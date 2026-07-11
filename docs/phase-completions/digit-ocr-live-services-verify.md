# Digit-OCR — Live-Services Verify + EasyOCR-Throughput Follow-up

Live-services run of the wired clock-seconds + single-digit-distance readers
([digit-ocr-integration.md](digit-ocr-integration.md)), through the **full real
path** — HDMI capture → capture-agent WS transport → VAF core (`:8100`) OCR →
`/ws/events` SNAPSHOTs — not saved crops. Records the result and banks the one real
finding it surfaced.

## Live verify — the wired readers emit correctly end-to-end

Streamed the live PS5 feed through the running services with the merged pipeline and
subscribed to SNAPSHOT events:

```
SNAPSHOT  q=4  clock 3:39 -> 3:38 -> 3:36 -> 3:34 -> 3:33 -> 3:32 -> 3:31 -> 3:30 -> 3:29   down=1 dist=10
```

- **Clock seconds run correctly** (the reader is in the live path): `:39 :38 :36 :34 :33 :32 :31 :30 :29`, incl. a `:X1` (`:31`). Running clock, live.
- **down/distance emit**: `1 & 10`. The `10` is **multi-digit → correctly handled by the EasyOCR path** (the distance reader is single-digit only), exactly as the gate designs it.
- The integration produces valid SNAPSHOTs through the real dispatcher/adapter/event-hub.
- **Reader cost is negligible**: +10 ms/frame (patch-NCC on 68×40 / 33×44 crops).

(The single-digit `1<->7` distance path wasn't exercised in this run — the drive stayed
on `1st & 10` — but it is already proven on saved + held-out live captures: `& 1`
EasyOCR `7` → gated `1`; clock `:37`→`37`.)

## THE FINDING — EasyOCR wide-cluster read blows the ocr-tier budget

Measured on this box (VAF venv, CPU-only EasyOCR):

| | ms/frame |
|---|---|
| `read_fields` with the digit readers | **703** |
| `read_fields` EasyOCR-only (the wide `right_cluster` read) | **694** |
| the digit readers' added cost | **10** |
| ocr-tier budget (`max_ocr_tier_ms`, ADR 0015) | **500** |

So every OCR-tier frame breaches the 500 ms budget by ~200 ms, and the dispatcher
**drops the frame** (`dispatcher.py` `return []` on breach). At the default budget,
**0 SNAPSHOTs flowed live** — all dropped. Raising the budget to 1500 ms (verify-only,
reverted) let them through, but with **heavy lag**: SNAPSHOTs buffered and arrived
~40 s late in a burst, and the ingest WebSocket dropped under the backlog.

**This is a PRE-EXISTING EasyOCR CPU-throughput ceiling**, exposed by running
core + EasyOCR + capture on one machine. It is **not** caused by the digit readers
(they add 10 ms). It's ADR-0006/0015 budget territory, orthogonal to the digit-reader
accuracy work.

## The path forward — migrate EasyOCR reads to patch-NCC

The patch-NCC readers are **~70× faster** than the EasyOCR cluster read (10 ms vs
694 ms). The same technique that fixed the `1<->7` *accuracy* is also the *throughput*
fix:

- **Replace the EasyOCR wide-cluster read with per-field patch-NCC readers.** clock-
  seconds and single-digit distance are already done. Remaining cluster fields —
  clock-minutes, play-clock, and the down/quarter **ordinals** (a different glyph style:
  `1ST/2ND/3RD/4TH` — needs its own template set) — each a small calibration +
  template-build like the two shipped readers. As fields migrate off EasyOCR, per-frame
  time falls toward the readers' ~ms and the ocr-tier budget is met → real-time SNAPSHOTs.
- **Alternatives:** GPU EasyOCR (if a GPU is available), or a sparser OCR cadence
  (trades freshness for latency headroom).

## Status

- **Digit-reader accuracy work** (clock-seconds + single-digit distance `1<->7`):
  DONE, shipped to `main`, and live-emission verified.
- **EasyOCR throughput:** pre-existing; banked here as the next performance workstream
  (patch-NCC migration is the natural continuation). Not a regression from this work.
