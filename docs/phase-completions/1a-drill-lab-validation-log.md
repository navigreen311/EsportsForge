# Phase 1a Drill Lab - Validation Log (§5.7 runnable criteria)

- **Scope:** in-process pipeline (file -> dispatcher -> OCR -> events), bounded per clip, OFFLINE_LAB.
- **Fixture classes (corrected):** OVERLAY = `playcall_*` + `practice_*` (both show the play-call overlay -> extraction); BROADCAST = `yt_*` only (no overlay -> transport + zero false-positive).
- **Deferred (recorded, not run):** ~~#2 live page display (browser->core connect)~~ **PROVEN 2026-07-09 — see "Stage D" below**; #7 rollback-alarm wire (P2 CloudWatch), #8 webhook audit (:8002).
- **Tracked robustness finding (not fixed here):** broadcast/null-HUD frames trigger a caught `Madden26Payload` ValidationError (score/clock required non-null) -> event logged+dropped, non-fatal. Payload-schema fix is separate work.

## Overlay clips - FORMATION extraction

| clip | formation | family | expected | status | frames | fps |
|---|---|---|---|---|---|---|
| madden26_playcall_human_exhibition.mp4 | None | None | (any) | no-overlay-in-window | 900 | 15.3 |
| madden26_playcall_i_form_pro.mp4 | 'Pro' | 'i_form_pro' | i_form_pro | match | 3 | 2.7 |
| madden26_playcall_pistol_strong.mp4 | 'Strong ed' | 'pistol_strong' | pistol_strong | match | 3 | 2.5 |
| madden26_playcall_shotgun_bunch.mp4 | 'Bunch' | 'shotgun_bunch' | shotgun_bunch | match | 3 | 2.6 |
| madden26_playcall_shotgun_doubles.mp4 | 'Doubles' | 'shotgun_doubles' | shotgun_doubles | match | 3 | 2.4 |
| madden26_playcall_shotgun_empty.mp4 | 'Empty Base' | 'shotgun_empty' | shotgun_empty | match | 3 | 2.6 |
| madden26_playcall_shotgun_trips.mp4 | 'Trips' | 'shotgun_trips' | shotgun_trips | match | 3 | 2.7 |
| madden26_playcall_singleback_ace.mp4 | 'Ace' | 'singleback_ace' | singleback_ace | match | 3 | 2.7 |
| madden26_playcall_singleback_wing.mp4 | 'Wing Slot' | 'singleback_wing' | singleback_wing | match | 3 | 2.6 |
| madden26_practice_i-form_pro.mp4 | 'Pro' | 'i_form_pro' | i_form_pro | match | 3 | 2.7 |
| madden26_practice_pistol_strong.mp4 | 'Strong' | 'pistol_strong' | pistol_strong | match | 3 | 2.5 |
| madden26_practice_shotgun_bunch.mp4 | None | None | shotgun_bunch | no-overlay-in-window | 900 | 26.0 |
| madden26_practice_shotgun_doubles.mp4 | None | None | shotgun_doubles | no-overlay-in-window | 900 | 26.8 |
| madden26_practice_shotgun_empty.mp4 | None | None | shotgun_empty | no-overlay-in-window | 900 | 25.2 |
| madden26_practice_shotgun_tight.mp4 | None | None | shotgun_tight | no-overlay-in-window | 900 | 26.9 |
| madden26_practice_shotgun_trips.mp4 | None | None | shotgun_trips | no-overlay-in-window | 900 | 26.9 |
| madden26_practice_singleback_ace.mp4 | 'Ace Slot' | 'singleback_ace' | singleback_ace | match | 3 | 2.6 |
| madden26_practice_singleback_wing.mp4 | 'Wing Flex Close' | 'singleback_wing' | singleback_wing | match | 3 | 2.6 |

## Broadcast clips (yt_ only) - transport + zero false-positive FORMATION_LOCKED (#3)

| clip | events by type | false-positive FORMATION | errors | frames | fps |
|---|---|---|---|---|---|
| madden26_yt_baseline_cpuvscpu_1.mp4 | {} | 0 | 0 | 150 | 23.1 |
| madden26_yt_baseline_franchise_1.mp4 | {} | 0 | 0 | 150 | 15.9 |
| madden26_yt_baseline_h2h_online.mp4 | {'SNAPSHOT': 1} | 0 | 0 | 150 | 25.4 |
| madden26_yt_baseline_mut_1.mp4 | {} | 0 | 0 | 150 | 9.6 |
| madden26_yt_baseline_playnow_kc_buf.mp4 | {} | 0 | 0 | 150 | 25.4 |
| madden26_yt_capture_4k_downscaled.mp4 | {} | 0 | 0 | 150 | 14.6 |
| madden26_yt_capture_compressed.mp4 | {'SNAPSHOT': 6} | 0 | 0 | 150 | 10.4 |
| madden26_yt_capture_streamer_overlay.mp4 | {'SNAPSHOT': 3} | 0 | 0 | 150 | 11.8 |
| madden26_yt_edge_2min_drill.mp4 | {} | 0 | 0 | 150 | 52.5 |
| madden26_yt_ocr_bengals.mp4 | {} | 0 | 0 | 150 | 24.4 |
| madden26_yt_ocr_ravens.mp4 | {} | 0 | 0 | 150 | 24.4 |
| madden26_yt_ocr_sf.mp4 | {} | 0 | 0 | 150 | 17.1 |
| madden26_yt_ocr_texans.mp4 | {} | 0 | 0 | 150 | 22.6 |

## Summary

- Overlay extraction: **12 matched**, 6 no-overlay-in-window (absence != failure), **0 mismatch**.
- Mismatches (wrong formation): none.
- Broadcast false-positive FORMATION_LOCKED: none (criterion #3 holds).
- Pipeline throughput (with OCR): 2.4-52.5 fps. (File-input/capture-path throughput is ~319 fps source-level, Day 1 - #4's actual subject.)

## Stage D - Live browser render (criterion #2) - PROVEN 2026-07-09

Criterion #2 (live page display: browser <- core over the events WebSocket) was
deferred through Day 1-3 and never proven until now. Proven live off a real PS5
capture-card feed, on `ai-feature/hud-recal-live`, with the WS-URL fix applied.

**Full chain, each link instrumented (not narrated):**

`PS5 -> HDMI capture card ("USB3.0 Video") -> ffmpeg (dshow) -> capture agent
(source=capture-card) -> VAF core /ws/ingest -> dispatcher -> OCR -> FORMATION_LOCKED
-> event_hub -> /ws/events/{session_id} -> browser (useVisionEvents) -> render + auto-rep`

| Link | Evidence |
|---|---|
| agent -> core ingest (session-scoped) | core: `WebSocket /ws/ingest?session_id=ses_...8Q3 [accepted]` |
| browser -> core subscribe (same session) | core: `events_subscriber_connected` on `ses_...8Q3` |
| broker returns usable ws_url | `POST /visionaudio/sessions/start` -> 200, `ws_url":"ws://127.0.0.1:8100"` |
| core emits real events | probe on `/ws/events/{sid}` captured a real envelope (below) |
| browser renders | Vision line showed the formation; rep counter advanced (auto-rep driven by live feed) |

**Real captured envelope (probe subscriber on the browser's exact WS surface):**

```json
{ "event_type": "FORMATION_LOCKED",
  "confidence": 0.615,
  "payload": { "offensive_formation": "IForm Pro", "offensive_formation_family": "i_form_pro",
               "down": 1, "distance": 10, "clock": "0:26", "quarter": 1,
               "score_home": null, "score_away": null,  // correct per ADR 0019, not broken
               "defensive_formation": null, "title": "madden26" } }
```

**The fix (commit `25318c8`):** the frontend discarded the broker's `ws_url` and
read an unset `NEXT_PUBLIC_VAF_WS_URL`, so the WS had no base URL. Now `page.tsx`
threads `data.ws_url` into `useVisionEvents`, which prefers it (env var kept as a
harmless fallback). Source-only change; `.env.local` / `config.live.toml` are local
and uncommitted.

**Dev-environment gotchas (cost real time, will recur):**
- `backend/app` has **no `load_dotenv`** -> `VAF_DRILL_LAB_ENABLED` and `VAF_CORE_URL`
  must be **shell-exported**, not placed in a `.env`, or `/sessions/start` returns
  403 `drill_lab_disabled`.
- Dev backend port is **:8002 per ADR 0011** (NOT the :8000 repo default, NOT the
  stale :8001 in the main-tree `.env.local`). Wrong port -> `page.tsx` silently
  swallows the session-start error -> "page loads, no events, no error."

**Incidental (NOT a Stage-D defect):** the worktree dev sqlite was schema-drifted on
the auth path (no `alembic_version`; `create_all()`-built; missing
`recommendations.feedback_at`), which 500'd every authed request. Unblocked by
swapping in the current main-tree sqlite (backup: `backend/esportsforge.db.bak-staged`).
Real remediation is `feat/alembic-remediation` (43842fe, unmerged).

**Open, deliberately not chased here:**
- `adapter_budget_breach` on hot-tier frames under CPU-only OCR (no accelerator) -
  harmless; OCR-tier frames still emit. Sparse cadence is by design (ADR 0015).
- The hook currently surfaces only `FORMATION_LOCKED`; the `SNAPSHOT` delivery path
  is identical (same hub fan-out), just not filtered-in by the display.
- Banked from ADR 0019: digit-OCR pass (scores, clock-seconds 1<->7, single-digit
  distance) and the canonical-family mapping gap.
