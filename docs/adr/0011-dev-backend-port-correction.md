# ADR 0011 — Dev Backend Port Correction (8001 → 8002)

- **Status:** Accepted
- **Date:** 2026-05-07
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 5 (adapters and infra wiring evolve without forcing core changes; port assignment is infra wiring).
- **Modifies:** [specs/01-capture-agent.md §"Local dev topology"](../specs/01-capture-agent.md), [specs/02-visionaudioforge-core.md §"Service ports"](../specs/02-visionaudioforge-core.md), and any local `.env.example` referencing `ESF_BACKEND_URL`.

## Context

Phase 0 specs assigned the EsportsForge backend dev server to **port 8001** so the VAF core could occupy the primary port (8100) and the capture agent could reach the backend at `http://127.0.0.1:8001`.

During Phase 0 smoke validation, port 8001 on the dev workstation showed a persistent `LISTEN` state held by **PID 19292**, which is not associated with any visible process. Reproduction:

```
> Get-NetTCPConnection -LocalPort 8001 -State Listen
LocalPort  State    OwningProcess
---------  -------  --------------
8001       Listen   19292

> Get-Process -Id 19292
Get-Process : Cannot find a process with the process ID 19292.
```

This is a Windows TCP zombie listener (orphaned socket whose owning process exited without releasing the bind). Resolution requires either:

1. A reboot, or
2. `netsh int ipv4 reset` from an elevated shell.

Neither is available without admin escalation, which the dev environment does not provide. Because Phase 0's acceptance criteria required a working end-to-end smoke, the backend was bound to **port 8002** as a working substitute.

## Decision

**Local dev backend runs on port 8002.** All references to `:8001` in specs, kickoff briefs, agent configs, and `.env.example` files are updated to `:8002`.

The change is dev-environment-only. Production / staging deployments continue on their normal port assignments (those are unaffected — production runs in containers with isolated network namespaces).

## Consequences

- Capture-agent default `config.dev.toml` sets `backend_url = "http://127.0.0.1:8002"`.
- VAF core's webhook publisher default target is `http://127.0.0.1:8002/api/v1/visionaudio/events`.
- Phase 1a kickoff brief's smoke checklist references `:8002` instead of `:8001`.
- A `.env.example` comment documents the rationale: "Port 8002 used instead of 8001 to avoid a Windows TCP zombie listener on the maintainer's dev box. See ADR 0011."
- If a future contributor runs into the inverse issue (zombie on 8002), the precedent is set: pick the next port up, document the deviation, ship.

## Followups

- Once dev-machine reboot lands (whenever convenient), validate that port 8001 is free, but **do not revert** unless every ADR-0011 reference is updated in the same PR. Half-reverts are worse than the deviation.
- Production port assignments are untouched. CI / staging environments deliberately don't use this fallback path; they rely on container-provided port isolation.
- If similar zombie-port issues recur, consider adding a `make doctor` target that probes each expected port and renders a friendly diagnostic with the `netsh` reset command.
