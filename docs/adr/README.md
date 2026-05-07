# Architectural Decision Records

Each ADR records a single, binding architectural decision. ADRs are written when a decision overrides, refines, or resolves an open question in a spec under [docs/specs/](../specs/) or [docs/integrations/](../integrations/).

## Format

Every ADR has these sections:

- **Title** (short, descriptive).
- **Status** (`Accepted` once signed off, `Superseded` if replaced by a later ADR).
- **Date** of acceptance.
- **Reference** to the [Forge architecture pattern](../FORGE_ARCHITECTURE_PATTERN.md) rule(s) the decision satisfies.
- **Modifies / supersedes** — the spec section the ADR amends, or prior ADRs it replaces.
- **Context** — why we're deciding this now.
- **Decision** — what we decided.
- **Consequences** — what changes downstream.
- **Notes / followups** — anything to revisit later.

## Conventions

- File names: `NNNN-short-slug.md` (zero-padded sequence number).
- Sequence is monotonically increasing in date order; never reused even if an ADR is superseded.
- ADRs are immutable once `Accepted`. To change a decision, write a new ADR that supersedes the old one and update the old ADR's status.
- The spec a decision modifies stays as written. The ADR overrides; future readers cross-reference both.

## Index

| # | Title | Status | Modifies |
|---|---|---|---|
| 0001 | [Feature flag infrastructure](0001-feature-flag-infrastructure.md) | Accepted | [specs/03 §5 Q1](../specs/03-mock-removal-and-page-wiring.md) |
| 0002 | [Film Room frame cache cap](0002-film-room-frame-cache-cap.md) | Accepted | [specs/03 §5 Q2](../specs/03-mock-removal-and-page-wiring.md) |
| 0003 | [Webhook delivery durability v1](0003-webhook-delivery-durability-v1.md) | Accepted | [specs/03 §5 Q3](../specs/03-mock-removal-and-page-wiring.md), [specs/02 §8](../specs/02-visionaudioforge-core.md) |
| 0004 | [Mock deletion bar](0004-mock-deletion-bar.md) | Accepted | [specs/03 §5 Q4](../specs/03-mock-removal-and-page-wiring.md) |
| 0005 | [Per-adapter frame-rate override](0005-per-adapter-frame-rate-override.md) | Accepted | [specs/01 §2](../specs/01-capture-agent.md) |
| 0006 | [Tiered per-frame budget](0006-tiered-per-frame-budget.md) | Accepted | [specs/02 §1, §4](../specs/02-visionaudioforge-core.md) |
| 0007 | [Title detection fallback strategy](0007-title-detection-fallback.md) | Accepted | [specs/02 §1](../specs/02-visionaudioforge-core.md) |
| 0008 | [Credential Manager in v1](0008-credential-manager-in-v1.md) | Accepted | [specs/01 §6](../specs/01-capture-agent.md) |
| 0009 | [Core service platform-neutral](0009-core-service-platform-neutral.md) | Accepted | [specs/01 §1](../specs/01-capture-agent.md), [specs/02](../specs/02-visionaudioforge-core.md) |
| 0010 | [Phase 1c gated on adapter v0.3](0010-phase-1c-gated-on-adapter-v0-3.md) | Accepted | [specs/03 §3](../specs/03-mock-removal-and-page-wiring.md) |
