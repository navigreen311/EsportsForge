# The Canonical Forge Architecture Pattern

**Author:** Ivan Green, Green Companies LLC
**Status:** Authoritative — applies to every Forge in the portfolio
**Version:** 1.0
**Last Updated:** May 2026

---

## Purpose of this document

This document defines the canonical architecture pattern that EVERY Forge in the Green Companies portfolio must follow. It exists because the same architectural mistakes keep almost happening across different Forges, and the cost of getting them wrong compounds with every page, every title, and every consumer that gets built on top of a flawed foundation.

If you are building, reviewing, or extending any Forge — read this first. If a proposed design violates this pattern, push back until the design conforms.

---

## The pattern in one sentence

**One service in the middle, many adapters or profiles around it, downstream consumers subscribe to clean events instead of duplicating logic.**

That is it. Everything below is elaboration.

---

## Why the pattern exists

Every Forge in the platform faces the same temptation during initial build: scope it narrowly to one use case, one title, one page, one consumer. This feels efficient because it gets a working slice fast. It is a trap.

The trap manifests in five recurring forms:

**Form 1 — Per-page duplication.** The first version puts the integration logic directly inside the page that needs it. The second page that needs it copies the logic. The third page modifies it slightly. By page five, you have five subtly different implementations of the same feature, drifting out of sync with each release.

**Form 2 — Single-title hardcoding.** The first version targets one game (Madden 26, NBA 2K26, etc.). The vocabulary, timing assumptions, and HUD coordinates get baked into the main service code. When the second title is added, the architecture cannot accommodate it without a refactor.

**Form 3 — Single-consumer assumption.** The first version assumes one type of consumer (one page, one user role, one subscription tier). The service exposes APIs that work for that consumer and break for any other. Adding new consumer types requires rewriting the API contract.

**Form 4 — Frontend-side intelligence.** The first version puts business logic in the consuming page (the React component, the route handler) instead of the service. The page becomes "smart" and the service becomes a dumb passthrough. This means logic cannot be reused across consumers and cannot be tested independently of the UI.

**Form 5 — Direct external API calls from consumers.** The first version has consuming pages call external APIs (Claude vision, ElevenLabs, Stripe, etc.) directly. This bypasses the Forge entirely. The Forge becomes optional middleware that consumers route around when convenient.

Every one of these forms produces the same outcome: a refactor that should have been the original design, costing 2-4x the time it would have taken to build correctly the first time.

---

## The three layers every Forge must have

### Layer 1 — Core service

The Forge itself. Owns universal responsibilities that apply regardless of consumer or context. Owns the contract with external dependencies (third-party APIs, ML models, hardware integrations). Publishes structured events to a canonical event bus.

The core service knows nothing about specific consumers. It does not know that War Room exists. It does not know that the user is on the Drill Lab page. It produces clean, structured outputs that any consumer can subscribe to.

### Layer 2 — Adapters or profiles

The dimension along which the Forge varies. For VisionAudioForge, this is **title** (Madden 26, NBA 2K26, Warzone, etc.). For VoiceForge, this is **title × page × subscription tier × integrity mode**. For CapitalForge, this is **issuer** (Chase, Amex, Capital One). For AnimaForge, this is **content type** (play diagram, weapon animation, drill demo).

Adapters are self-contained modules that handle one specific case. They live under the core service and are routed to by the core service based on input characteristics (which title is detected, which page is active, which issuer is being queried, etc.).

### Layer 3 — Consumers

The pages, components, and downstream services that USE the Forge. Consumers subscribe to events from the core service or call clean APIs the core service exposes. Consumers do NOT call external APIs directly. Consumers do NOT duplicate logic that belongs in adapters.

A consumer's job is to render UI based on Forge events and to dispatch user intent back to the Forge. Nothing more.

---

## The five rules

Every Forge must satisfy these five rules. If a proposed design violates any of them, the design is wrong.

**Rule 1 — Multi-dimensional from day one.**
Even if the v1 build only supports one title, one page, or one consumer, the architecture must accommodate the full dimensional space of the platform. You build one adapter first, but the core service routes through an adapter pattern from the beginning. Adding the second adapter must not require modifying the core service.

**Rule 2 — Consumers never call external APIs directly.**
If a consumer needs Claude vision analysis, it goes through VisionAudioForge. If it needs voice synthesis, it goes through VoiceForge. If it needs a credit card application submitted, it goes through CapitalForge. The Forge owns the external dependency contract. Consumers own the user experience.

**Rule 3 — Logic lives in the Forge, not the consumer.**
Business rules, validation, prompt engineering, error handling, retry logic, caching — all of it belongs in the core service or its adapters. The consumer should be replaceable. Two different UIs should be able to consume the same Forge and get the same results.

**Rule 4 — Events are structured and canonical.**
The Forge publishes events in a documented schema. Every event has a stable shape. Every consumer reads from the same event bus. Adding a new consumer should not require changes to event production.

**Rule 5 — Adapters are added without core changes.**
When a new title, page, issuer, or content type is added, the work happens entirely inside a new adapter module. The core service does not change. The event bus does not change. The consumer pages may need to subscribe to new events, but they do not need to be rewritten.

---

## Recognized Forges in the portfolio

This pattern applies to every Forge below. Each entry includes the dimensional space the Forge must handle.

### EsportsForge ecosystem

**VisionAudioForge** — Vision and frame analysis service.
Dimensional space: **title**.
Adapters: madden26, cfb26, nba2k26, eafc26, mlb26, warzone, fortnite, ufc5, pga2k25, undisputed, video_poker.
Each adapter owns: HUD region coordinates, OCR pipeline, formation/stance/loadout detection, state assembler.

**VoiceForge** — Voice synthesis, recognition, and coaching cue dispatch.
Dimensional space: **title × page × subscription tier × integrity mode**.
Title profiles: same 11 titles as VisionAudioForge.
Page profiles: war_room, gameplan, arsenal, drills, simlab, tournament, analytics, dashboard, in_game.
Subscription gating: free (text only), competitive (voice on most pages), elite (premium voice plus in-game), team (shared profiles).
Integrity gating: tournament mode disables real-time AI cues, ranked allows some cues, offline lab fully unlocked.

**AnimaForge** — Animation generation for plays, weapons, drills, share cards.
Dimensional space: **content type × title**.
Content types: play_diagram, weapon_animation, drill_demo, scenario_preview, correct_call, share_your_win.
Title context: each content type renders differently per sport.

**Watching layer** — Global capture state and per-page adapters.
Dimensional space: **page**.
Single global toggle in header. Per-page adapters: drills, simlab, gameplan, arsenal, war_room.
Capture sources: TV via capture card, PC monitor, camera/NHJ19.

### Green Companies broader portfolio

**CapitalForge** — Credit card and capital application service.
Dimensional space: **issuer × product**.
Issuers: Chase, Amex, Capital One, Citi, Discover, Bank of America, Wells Fargo, US Bank, Navy Federal, Alliant, PenFed, BECU, First Tech FCU, Lake Michigan CU, plus business issuers.
Products per issuer: personal cards, business cards, lines of credit, term loans.
Issuer rules engine encodes per-issuer velocity rules (Chase 5/24, Amex once-per-lifetime, Capital One 6-month velocity).

**ChamberForge** — UHNW/HNW wealth-service operating system.
Dimensional space: **service module × client tier**.
109-module architecture. Client tiers: HNW, UHNW, family office.

**FunnelForge** — Conversion and funnel automation.
Dimensional space: **funnel type × industry vertical**.
Funnel types: lead generation, webinar, application, booking, e-commerce.
Includes integrated Visual Automation Builder, Unified Inbox, Sales Pipeline, Custom Report Builder, Agency/White-Label Mode.

**SelfPublisherForge** — Book production and publishing service.
Dimensional space: **book type**.
Types: standard, children's, coloring, puzzle, comic, cookbook, style clone, photo integration.

**StyleForge** — Personal stylist platform.
Dimensional space: **discipline × user identity profile**.
30 functional categories plus 8 accessory disciplines. 88 modules. Five Cross-Forge integrations (VoiceForge, VisionAudioForge, ChamberForge, SelfPublisherForge, AnimaForge).

**LegalForge** — Legal document and contract production (planned).
Dimensional space: **document type × jurisdiction**.
Hard UPL firewall required. Modules: Document Production Engine, Lifecycle Management, Compliance/Counsel layer, IP and Trademark Vault, Obligation/Calendar shared service.

**VideoEditForge** — AI video editing and production.
Dimensional space: **content type × style profile**.
12 curated pre-built style packs. CRDT collaboration. C2PA signing.

**DateForge AI** — AI dating assistant.
Dimensional space: **platform × user identity profile**.

**TrafficForge** — Traffic acquisition (now integrated into FunnelForge).
Dimensional space: **traffic source × campaign type**.

**MedLink Pro platform** — Healthcare staffing system of record.
Dimensional space: **clinician role × facility type × jurisdiction**.

**Greenstone CRE platform** — Commercial real estate wholesaling.
Dimensional space: **deal stage × property type**.

**Argus** — Cybersecurity vertical specialist.
Dimensional space: **vertical × threat model**.
Verticals: healthcare operators, CRE operators.

**Collingswood and Co.** — AI personal assistant SaaS.
Dimensional space: **assistant role × user identity profile**.
106 cognitively-architected agents with persistent episodic memory.

**Burkham Wickmont** — Corporate funding and growth capital architecture.
Dimensional space: **client stage × funding instrument**.
57-module Operations Console.

---

## How to apply this pattern to a new Forge

When designing a new Forge, work through this checklist before writing code.

**Step 1 — Identify the dimensional space.**
What dimensions does this Forge vary across? Title? Page? User tier? Geography? Issuer? Content type? Most Forges have 2-4 dimensions. Write them down explicitly.

**Step 2 — Identify the core responsibilities.**
What does this Forge do that is universal across all dimensions? Frame ingestion is universal. Voice queue management is universal. External API contract management is universal. List these.

**Step 3 — Identify the adapter responsibilities.**
What varies by dimension? HUD coordinates vary by title. Vocabulary varies by title and page. Issuer rules vary by issuer. Document templates vary by jurisdiction. List these.

**Step 4 — Identify the consumers.**
Who calls this Forge? Which pages, which downstream services, which user-facing flows? List them.

**Step 5 — Design the event contract.**
What structured events does the core service publish? What schemas? What priorities? Document this BEFORE writing any consumer code.

**Step 6 — Design the routing matrix.**
For multi-dimensional Forges (title × page × tier × mode), draw the matrix. Identify which combinations are allowed, which are restricted, which require special handling.

**Step 7 — Plan the build sequence.**
Build the core service plus ONE adapter first. Prove the architecture works end to end. Then expand to additional adapters in priority order. Never build all adapters in parallel.

**Step 8 — Plan the consumer wiring.**
Plan how existing consumers will subscribe to the new Forge. Plan how to deprecate any direct external API calls those consumers currently make.

If any of these steps cannot be completed at design time, the Forge is not ready to build. Push back until the design is complete.

---

## Anti-patterns to reject on sight

If you see any of these in a proposed design, the design is wrong.

**Anti-pattern 1 — "Just for v1."**
"We'll just hardcode Madden in v1 and refactor later." No. Build the adapter pattern from day one. Build only the Madden adapter for v1, but the architecture must accommodate the full set.

**Anti-pattern 2 — "The page will handle it."**
"The Drill Lab page will call the Claude vision API directly to detect formations." No. The page subscribes to VisionAudioForge events. The Forge owns the API contract.

**Anti-pattern 3 — "It's only one consumer."**
"Only the War Room uses voice briefings, so we can put the briefing logic in War Room." No. Voice briefing logic belongs in VoiceForge. Other consumers will need it later. The architecture should not assume singular consumption.

**Anti-pattern 4 — "We can copy the existing implementation."**
"This new feature is similar to the existing one in another page, so we can copy that code." No. If two pages need the same logic, the logic belongs in the Forge. Copying creates drift.

**Anti-pattern 5 — "The frontend will route to the right backend."**
"The frontend will detect which title is active and call the right backend endpoint." No. The frontend sends one event to the Forge. The Forge routes internally. The frontend must not know about adapter selection.

**Anti-pattern 6 — "We'll add a new field to the event."**
"This new consumer needs a slightly different event shape, so we'll add a field to the existing event." No. If the new consumer needs different data, design a new event type. Do not break the existing schema.

**Anti-pattern 7 — "Bypassing the Forge for performance."**
"Going through the Forge adds latency, so this consumer will call the external API directly." No. If the Forge is too slow, optimize the Forge. Do not let consumers bypass it.

---

## How to use this document with Claude Code

When prompting Claude Code on any Forge work, reference this document explicitly:

```
Reference: docs/FORGE_ARCHITECTURE_PATTERN.md

This task affects [name of Forge]. Before designing or modifying
this service, confirm the design satisfies all five rules in the
Canonical Forge Architecture Pattern document. Specifically:

- Identify the dimensional space.
- Confirm the core service knows nothing about specific consumers.
- Confirm logic lives in the Forge, not in consuming pages.
- Confirm consumers do not call external APIs directly.
- Confirm adapters can be added without core service changes.

If the proposed design violates any of these rules, stop and
propose a corrected design before writing implementation code.
```

This forces every prompt to pass through the architectural review. The pattern stays enforced even when the human prompting is moving fast.

---

## When this document should be updated

Update this document when:

- A new Forge is added to the portfolio. Add it to the "Recognized Forges" section with its dimensional space.
- A new anti-pattern is discovered. Add it to the "Anti-patterns to reject on sight" section.
- A new dimension is added to an existing Forge. Update that Forge's entry.
- A rule needs to be refined based on real-world experience. Update the rule with reasoning.

This document is the single source of truth for Forge architecture. If a decision in this document conflicts with code, the code is wrong, not the document. Fix the code to match the document. If the document is genuinely wrong, update the document FIRST, then update the code.

---

## Closing principle

The Forge pattern exists because every individual Forge looks deceptively simple at the start. "It's just a vision service." "It's just a voice service." "It's just a card application service." The simplicity is a mirage. By the time the Forge has 5 consumers, 11 titles, 9 pages, 3 subscription tiers, and 4 integrity modes, the dimensional space is enormous. Architectures that did not plan for that space collapse under it.

Every Forge in this portfolio will eventually be load-bearing for a real product with real users paying real money. The pattern is what makes that scaling possible. Follow it from day one.
