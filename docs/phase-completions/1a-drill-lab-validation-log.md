# Phase 1a Drill Lab - Validation Log (§5.7 runnable criteria)

- **Scope:** in-process pipeline (file -> dispatcher -> OCR -> events), bounded per clip, OFFLINE_LAB.
- **Fixture classes (corrected):** OVERLAY = `playcall_*` + `practice_*` (both show the play-call overlay -> extraction); BROADCAST = `yt_*` only (no overlay -> transport + zero false-positive).
- **Deferred (recorded, not run):** #2 live page display (browser->core connect), #7 rollback-alarm wire (P2 CloudWatch), #8 webhook audit (:8002).
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
