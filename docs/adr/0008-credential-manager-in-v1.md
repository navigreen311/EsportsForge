# ADR 0008 — Windows Credential Manager Integration in v1

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 2 (consumers — including the capture agent — never expose secrets carelessly; the capture agent's API key is the credential the core trusts).
- **Modifies:** [specs/01-capture-agent.md §6 "Encryption at rest"](../specs/01-capture-agent.md). **Overrides** the spec's deferral of Credential Manager integration to v1.1.

## Context

Spec #1 proposed storing the capture agent's API key in plaintext in `config.toml`, with Windows ACL on `%LOCALAPPDATA%` as the protection. v1.1 was scheduled to integrate Windows Credential Manager (`CredWrite` / `CredRead`).

The deferral was justified by ~half-day of additional dev cost. After review:

- The capture agent runs on the **CLX PC**, which is plausibly shared (coaching room, family PC, public-event demo machines).
- The same credential is the entry point to the player's session in the core, which has access to game-state events including opponent-side data in Broadcast mode.
- The Forge platform spans many products (CapitalForge, ChamberForge, etc.) where credential hygiene precedent matters more than half a day of velocity.
- A leaked plaintext API key on a shared machine is a 90-day window of unauthorized access.

The half-day cost is justified by the platform-level security posture.

## Decision

**Ship Windows Credential Manager integration in v1, not v1.1.**

The capture agent uses `CredWrite` to store the API key under target name `EsportsForge.CaptureAgent.APIKey` per logged-in user. Stored secrets are encrypted by Windows DPAPI scoped to the user account.

**Plaintext fallback only if Credential Manager is unavailable** (e.g., older Windows builds, sandboxed environments where DPAPI is disabled). Fallback paths require a startup warning toast: *"Capture Agent could not access Windows Credential Manager — your API key is stored in a less-secure location."*

The `[auth]` section of `config.toml` retains `user_id` (non-sensitive) and a flag `credential_storage = "credman" | "plaintext"` indicating which storage path is active.

## Consequences

- v1 capture-agent installer ships with Credential Manager integration as a hard requirement on supported Windows 10 (build 19041+) / Windows 11 — both ship DPAPI by default.
- Phase 1 capture-agent build adds ~half-day to the M1 milestone for the Credential Manager wrapper. Acceptable within Phase 1's 12–14 day envelope.
- Windows Credential Manager is per-user — the capture agent installer must be a per-user install (already specified in Spec #1 §8) so each user has their own credential.
- Credential rotation (90-day cycle, [Spec #1 §6 "Auth token rotation"](../specs/01-capture-agent.md)) writes the new key via `CredWrite` and reads via `CredRead`. The agent never reads plaintext from disk for the api_key field.

## Notes / followups

- The `pywin32` dependency adds ~5 MB to the PyInstaller bundle. Acceptable.
- Test matrix for Phase 1 M8 (deploy validation) includes both happy path (Credential Manager works) and fallback path (Credential Manager simulated unavailable).
- Document the fallback-mode warning toast in the player-facing release notes so the appearance of the warning isn't surprising.
