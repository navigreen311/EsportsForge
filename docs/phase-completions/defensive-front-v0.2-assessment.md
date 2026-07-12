# v0.2 defensive-front tier — approach + data assessment

- **What it is:** the pre-snap **defensive front** (`FootballPayload.defensive_formation`, "None until
  v0.2 ships") — the defensive personnel/alignment the offense reads pre-snap (4-3, 3-4, Nickel,
  Dime, Big Dime, 46, Bear, …). Distinct from v0.3 post-snap coverage.
- **Verdict:** the right approach is **OCR-of-play-call-overlay** — the *same proven pattern* that
  took the offensive formation classifier to 100% (ADR 0014). It is likely the **cheapest of the
  remaining tiers to ship** (read a NAME off an overlay, no hard vision problem), but it is
  **blocked on a capture that does not exist yet**: defensive play-call screens.

## Why OCR-of-overlay, not a visual classifier

When you pick a defensive play, Madden shows the defensive **front/formation on the play-call
screen** — exactly like the offensive play-call screen the v0.1 formation reader OCRs
(`OCRPipeline.read_formation_name` / `is_play_call_screen`). The hook already exists:
`formation_detector.detect_defensive_front()` returns None today. So v0.2 is "point the existing
overlay-OCR at the defensive play-call screen", not a from-scratch model. Reading a printed name
is trivially reliable once captured — unlike v0.3 coverage, which is a genuine post-snap vision
problem.

A *visual* pre-snap front classifier (CNN on the box alignment, like the coverage probes) is a
possible fallback, but it needs front-labeled frames (none exist) and is harder than reading the
name. Prefer the overlay.

## The data blocker (confirmed, not assumed)

- The 120 All-22 **coverage clips start AFTER the play-call** — pre-snap field view, no
  formation-picker screen. `is_play_call_screen` returns **False** on their early frames (f0/10/25/45),
  so there is no defensive formation-name overlay to OCR.
- The `madden26_playcall_*` captures are **all offensive** formations — there are **zero defensive
  play-call captures**, and no defensive-front labels anywhere.
- (The practice-mode "PLAY ZONE / ASSIGNMENTS" coaching panel visible ~f0–1s is *assignment text*,
  practice-only, and absent in real games — not the front name.)

## Path to ship (well-defined, low-risk)

1. **Capture defensive play-call screens**, one per front, labeled by construction — mirror the
   offensive set: `madden26_defcall_<front>.mp4` for `4-3 / 3-4 / nickel / dime / big_dime / 46 / …`
   (record the screen while selecting each defensive formation; a short burst like the offensive
   `--label ... --shots` captures suffices — this is a play-call *screen* grab, not a full play).
2. **Add/recalibrate the OCR region** for the defensive play-call layout (the offensive
   `formation_name` bbox is `[640,585,540,32]` in `hud_regions.json` v2.2.0; the defensive screen
   likely differs → add a `defensive_formation_name` region and validate by rendering it back).
3. **Wire `detect_defensive_front`** to read it (mirror `detect_offensive`), map the raw name to a
   canonical front set, and populate `defensive_formation`. `defensive_formation` is already a
   free-`str` in the schema (like `offensive_formation`), so no contract change.

## Recommendation

**Sequence after (or alongside) the v0.3 T0/T1 coverage captures** — it's the cheapest tier to
ship but needs its own (small) capture. Because it reuses the offensive OCR pipeline end-to-end,
once the defensive play-call screens exist it is a days-scale build, not a research arc — the
opposite of the coverage tiers. Cross-refs: `formation_detector.py` (the hook + the offensive
pattern to mirror), ADR 0014 (OCR-over-CNN), ADR 0017 (`defensive_formation` carrier).
