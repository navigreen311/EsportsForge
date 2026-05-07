# ADR 0009 — Core Service Platform-Neutral Clarification

- **Status:** Accepted
- **Date:** 2026-05-06
- **Reference:** [FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md) — Rule 1 (multi-dimensional from day one — including deployment platform; Forges should not be platform-locked) and Rule 5 (no platform assumptions baked in that block adapter additions later).
- **Modifies:** Clarifies [specs/01-capture-agent.md §1 "Out of scope for v1"](../specs/01-capture-agent.md) and [specs/02-visionaudioforge-core.md](../specs/02-visionaudioforge-core.md) (no assumption-leakage).

## Context

Spec #1 declares the **capture agent** Windows-only in v1 ("macOS / Linux support out of scope"). This is appropriate — capture-card driver maturity, OpenCV `cv2.CAP_DSHOW` access, and PyInstaller's native Windows packaging make Windows the deployment target.

Spec #2 doesn't explicitly state the **core service**'s platform target. By implication (FastAPI on AWS ECS), it's Linux. But "Windows-only capture agent" wasn't carefully separated from "Windows-only core" in the docs, and that ambiguity creates risk: if a developer assumes Windows for the core service, they may use Win32-specific paths, line endings, or registry calls that break Linux deployment.

## Decision

**Confirm the platform-target separation explicitly:**

- **Capture agent** is **Windows-only in v1**, per [Spec #1 §1](../specs/01-capture-agent.md). (Approved as-is.)
- **Core service** is **Linux ECS production target.** Cross-platform development (engineers on macOS / Windows can build and test locally), but **no Windows assumptions baked into core code paths.**

**Verification requirements before Phase 0 sign-off:**

1. **Path handling.** All file operations in the core use `pathlib.Path` or POSIX path separators. No raw `\\` Windows paths anywhere in the core's `backend/app/services/integrations/visionaudio/` tree.
2. **Line endings.** Files committed with LF. Repo `.gitattributes` enforces this for all `*.py`, `*.json`, `*.md` under the core's directories.
3. **Process spawning.** No `subprocess` calls to Windows-specific binaries. ML model inference is via cross-platform ONNX runtime; Tesseract is invoked via the Linux-compatible `pytesseract` package.
4. **Time-zone / locale.** Core runs in UTC. No `time.timezone` Windows-isms.
5. **CI matrix.** Core unit tests run on Linux + macOS in CI. Capture agent tests are Linux + Windows. Mismatch deliberately catches platform leakage.

The capture agent talks to the core over WebSocket, which is platform-neutral. There's no shared-filesystem dependency between the two.

## Consequences

- The core service can deploy to AWS ECS (Fargate Linux), GCP Cloud Run, Azure Container Apps, or self-hosted Docker without any platform-conditional code.
- A `.gitattributes` rule is added to the repo root to lock LF for the core's tree.
- A pre-commit lint hook flags Windows-isms (raw `\\`, `os.path.sep` mixed with literals, `time.timezone`) in core paths. The same hook does not run on the capture-agent tree.
- Phase 0 acceptance includes a "no Windows-isms" check as a Definition of Done item.

## Notes / followups

- The CI matrix change is small (one extra Linux + one macOS Python lane). Cost is single-digit dollars/month.
- The lint hook is a follow-up after Phase 0 once the core directory structure is solid; not a blocker for kickoff.
- The capture agent's Windows-only scope is **not changed** by this ADR. The decision is purely a clarification that the core has different rules.
