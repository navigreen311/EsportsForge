# Spec — Capture Agent (CLX PC Local Application)

> **Reference:** [docs/FORGE_ARCHITECTURE_PATTERN.md](../FORGE_ARCHITECTURE_PATTERN.md). The Capture Agent is a consumer in the Forge sense — it sends frames to the VisionAudioForge core. It owns no game logic and no title-specific behaviour.
> **Companion specs:** [docs/specs/02-visionaudioforge-core.md](02-visionaudioforge-core.md), [docs/specs/03-mock-removal-and-page-wiring.md](03-mock-removal-and-page-wiring.md). Deeper architectural context and Phase 1 milestones live in [docs/integrations/visionaudioforge/](../integrations/visionaudioforge/).
> **Status:** Specification only. No implementation code in this PR.

## Purpose

A small native binary that runs on the CLX PC, reads HDMI frames from a capture card, and forwards them to the VisionAudioForge ingestion endpoint. Title-agnostic by design — the agent never knows whether the player is running Madden 26, Warzone, or PGA TOUR 2K25. Title detection happens server-side.

The agent runs as a system tray application on Windows. Players install it once, configure their capture source via Settings → Game Settings → Capture Source, and otherwise forget it exists.

---

## 1. Tech stack recommendation

**Recommendation: Python 3.12 + OpenCV + websockets + PyInstaller, packaged as a signed Windows installer.**

### Comparison with alternatives

| Stack | Distributable size | Capture-card access | Backend reuse | Verdict |
|---|---|---|---|---|
| **Python + OpenCV + PyInstaller** | ~30 MB exe | `cv2.VideoCapture(idx, cv2.CAP_DSHOW)` — one line via DirectShow | Backend is already Python; logging/Pydantic patterns reusable | **Recommended.** Ship sooner, one fewer language to maintain. |
| Node + Electron + ffmpeg | ~150 MB exe (Chromium bundled) | Requires native module (`node-mediasource` or shelling out to ffmpeg) | Frontend stack but separate runtime; no backend reuse | Heavier, slower startup, no clear win. UI framework is overkill — agent's UI is one tray icon + menu + small diagnostic window. |
| Native C++ / Rust | ~5 MB exe | Direct Media Foundation API access | None | Faster runtime perf, ~3× development cost. The bottleneck for the agent is network throughput, not capture overhead. We'll port to Rust later if frame rate becomes the limit. |
| Native C# (WPF) | ~50 MB framework-dependent | Built-in DirectShow | Some interop with the wider .NET ecosystem | Adds a third language to the stack with no offsetting advantage. |

### Rationale

Three forces pick Python:
1. **Capture-card driver maturity in OpenCV.** Windows DirectShow access via `cv2.VideoCapture(device_index, cv2.CAP_DSHOW)` works for every capture card we plan to support (Elgato HD60 X, Elgato Game Capture 4K X, AVerMedia Live Gamer 4K, generic MS2109-based UVC). One backend, one bug surface.
2. **Stack monoculture.** The EsportsForge backend is Python. Reusing Pydantic schemas, structlog conventions, and pytest tooling cuts onboarding cost and bug-fix time.
3. **PyInstaller produces a single signed `.exe`.** No system Python required; player downloads, installs, runs. This is the only deployment target that matters for v1 (Windows-only).

### What's not in this stack

- No GUI framework beyond Win32 tray and a minimal Tkinter status window.
- No web server (the agent is a client, not a server).
- No ML libraries (all CV work happens server-side).

### Out of scope for v1

- macOS / Linux support.
- Audio capture ("VisionAudioForge" is forward-looking; v1 is video only).
- Multi-monitor / dual-source capture (one source per session).

---

## 2. Frame sampling strategy

### Base cadence

- **Internal capture rate:** 30 fps.
- **Default send rate:** 12 fps to the core (configurable 1–24 fps).
- **Adaptive ramp-up:** to 24 fps for ~2 s when motion is detected (see "Motion gating" below).

### Format and compression

- **Encoding:** JPEG, quality 75. Roughly 150 KB per 1080p frame; well under the WS message size budget.
- **Color space:** BGR → RGB conversion happens server-side; agent ships native BGR.
- **Resolution:** capture at the device's native rate (typically 1080p for HDMI capture cards). Server adapters assume 1080p; if the device delivers a different resolution, server resizes upstream of adapter dispatch.

### Motion gating (adaptive ramp)

To minimise bandwidth during menus and idle screens, the agent uses a cheap frame-difference heuristic:

```
Captured at 30 fps internally.
Default cadence:   send every Nth frame (N = 30 / target_fps).
Motion gate:       compute frame-difference vs previous queued frame.
                   diff < low_threshold  → drop to 2 fps   (static menu, paused game)
                   diff > high_threshold → bump to 24 fps for 2 s (snap, kill, animation)
```

Computed on a downscaled (320×180) version of the frame for cost — typically <2 ms.

### Batching

- **Batch size:** 4 frames per WebSocket message (configurable).
- **Per-message size budget:** 2 MB; 4 × 1080p JPEG q=75 ≈ 600 KB. Plenty of headroom.
- **Latency cost:** 333 ms at 12 fps (4 frames × 83 ms each). Acceptable for the use case — formation reads tolerate ~1 s lag.

### Local ring buffer

The last 30 s of compressed frames stays in memory while the WS is connected. On a brief disconnect, captures continue queuing into the ring; on reconnect, the buffer drains in order before live capture resumes. Buffer cap: 30 s × 24 fps × 200 KB ≈ 144 MB max — acceptable on a gaming PC.

If a disconnect exceeds the buffer window, oldest frames drop and the agent reports `frames_dropped` in its next heartbeat.

---

## 3. Ingestion endpoint contract

### Decision: **WebSocket** for frame stream, HTTP for control.

#### Comparison

| Transport | Pros | Cons | Verdict |
|---|---|---|---|
| **WebSocket** | Single connection, low overhead per frame, bidirectional control channel (server → agent: pause, throttle, close), framing is built in | Requires WS-aware load balancer; reconnection logic on agent side | **Recommended.** Right tool — frames are a continuous stream, the server needs to send control messages back. |
| Plain HTTP POST per batch | Simple, stateless, every standard LB handles it | TCP/TLS handshake per batch; no native channel for server → agent control; polling pattern needed for control messages | Rejected — overhead at 3 batches/sec is non-trivial, and we lose the control channel. |
| WebRTC | Lowest latency, P2P-capable, native ducking-grade audio support for v2 | Complex setup (STUN/TURN, signalling), heavier client dependency, overkill for ~12 fps batched JPEG | Rejected for v1 — reconsider for v2 when audio enters scope. |
| gRPC streaming | Strongly typed, bidirectional | Needs HTTP/2 ALB config; no clear advantage over WS for this payload shape | Rejected — typing benefit is small (frames are bytes), config overhead is real. |

### Wire protocol

**Endpoint:** `wss://vision.esportsforge.gg/ws/ingest` (prod) / `ws://localhost:8100/ws/ingest` (dev).

**Auth:** `Authorization: Bearer <api_key>` on the upgrade request. Keys are short-lived (90 days), bound to a `user_id`, issued and rotated by the EsportsForge backend.

**Server → Agent (handshake on connect):**

```json
{
  "type": "session_open",
  "session_id": "ses_01HXXX",
  "integrity_mode": "ranked",
  "active_title": "madden26",
  "capture_allowed": true,
  "frame_format": "jpeg",
  "max_fps": 24
}
```

`capture_allowed: false` means the agent stays connected, sends heartbeats, but does not send frames. Used when the user is in Tournament mode.

**Agent → Server (frame batches, ~3/sec):**

```json
{
  "type": "frame_batch",
  "session_id": "ses_01HXXX",
  "batch_seq": 42,
  "frames": [
    {
      "frame_id": 1247,
      "captured_at": "2026-05-06T22:30:01.123Z",
      "width": 1920,
      "height": 1080,
      "format": "jpeg",
      "data_b64": "..."
    },
    ...
  ]
}
```

**Agent → Server (heartbeat, every 5 s):**

```json
{
  "type": "heartbeat",
  "session_id": "ses_01HXXX",
  "stats": {
    "frames_captured": 4382,
    "frames_sent": 4380,
    "frames_dropped": 2,
    "current_fps": 12.1,
    "capture_device_status": "ok",
    "uptime_sec": 364
  }
}
```

**Server → Agent (control messages):**

```json
{ "type": "capture_pause", "reason": "integrity_mode_switch" }
{ "type": "capture_resume" }
{ "type": "set_target_fps", "fps": 18 }
{ "type": "session_close", "reason": "user_logout" }
```

---

## 4. System tray app shell design

### Tray icon states

| State | Icon | Tooltip text |
|---|---|---|
| Idle / disconnected | grey forge anvil | "EsportsForge — disconnected" |
| Connecting | amber pulsing | "EsportsForge — connecting…" |
| Capturing | green | "EsportsForge — capturing (12 fps)" |
| Paused (integrity mode) | amber | "EsportsForge — paused (Tournament mode)" |
| Error | red | "EsportsForge — capture device missing" |

The icon updates on state transitions. Pulsing animations are throttled to 2 fps to avoid distraction.

### Tray right-click context menu

```
┌────────────────────────────────┐
│ ⚪ Status: Capturing (12 fps)   │   ← live status line, updates every second
├────────────────────────────────┤
│ Open EsportsForge              │   → opens the dashboard in the default browser
│ Open Diagnostic Window         │   → opens the local status window
├────────────────────────────────┤
│ Pause Capture                  │   → temporary local pause; resumes on next start
│ Resume Capture            ⌘⇧P  │
├────────────────────────────────┤
│ Capture Source: HDMI (HD60 X)  │   → submenu: select source device
│   ▸ HDMI capture card           │
│   ▸ PC monitor                  │
│   ▸ Test video file             │
├────────────────────────────────┤
│ View Logs                      │   → opens %LOCALAPPDATA%\EsportsForge\CaptureAgent\logs in Explorer
│ Open Settings (in-app)         │   → opens browser to /settings?tab=game
├────────────────────────────────┤
│ About / Version                │   → version, build hash, EV-cert status
│ Quit                            │   → tears down session, exits agent
└────────────────────────────────┘
```

### Diagnostic window (single Tk window)

Opens on left-click of tray icon, or via the context menu. Closes back to tray on the X button (does not exit the agent — only "Quit" does).

```
┌─ EsportsForge Capture Agent ───────────────────────┐
│                                                     │
│  Connection:  ● Connected    [vision.esportsforge.gg] │
│  Session:     ses_01HXXX                            │
│  Active title (server-detected): Madden 26          │
│  Integrity mode: Ranked                             │
│                                                     │
│  ┌─ Capture Device ─────────────────────────────┐  │
│  │ Elgato HD60 X (USB 3.0)                      │  │
│  │ 1920 × 1080 @ 60 fps                          │  │
│  │ Status: ● OK                                 │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Frames captured: 4,382                            │
│  Frames sent:     4,380                            │
│  Frames dropped:  2                                 │
│  Current send FPS: 12.1                             │
│  Uptime: 6m 04s                                    │
│                                                     │
│  [ Test Capture (save 1 frame) ]  [ View Log ]     │
│  [ Reconnect ]  [ Pause ]                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

Window minimises back to the tray icon. The diagnostic window is purely informational — all state transitions also surface as Windows toast notifications when the window is hidden.

### Toast notifications (Windows balloon / Action Center)

Shown only on state changes the player should know about:
- Capture device disconnected.
- Re-connecting after extended outage (>30 s).
- Auth failure.
- Integrity mode switched to Tournament (capture paused).
- Crash recovery on agent restart.

Suppressed in rapid succession (max 1 toast per 30 s).

---

## 5. Start/stop controls and error states

### Lifecycle

1. **Launch:** auto-start on Windows boot (configurable). Reads `config.toml`, validates capture device exists, opens WS to core service, transitions to "Connecting".
2. **Connect:** server returns `session_open`. If `capture_allowed: true`, transitions to "Capturing".
3. **Capturing:** sends frame batches. Heartbeat every 5 s. Listens for control messages.
4. **Pause (server-initiated):** server sends `capture_pause` (e.g., on Tournament mode entry). Agent stops sending frames; stays connected; heartbeats continue.
5. **Pause (user-initiated):** user clicks "Pause Capture" in tray menu. Same as above but the agent additionally suppresses the resume signal until the user clicks "Resume Capture".
6. **Reconnect:** WS drops. Agent enters exponential backoff (1 → 2 → 4 → 8 → 16 → 30 s, capped). Frames queue in ring buffer.
7. **Quit:** tray "Quit" menu, or system shutdown. Agent closes the WS gracefully (`{"type": "session_close", "reason": "agent_quit"}`), drains the in-flight batch, exits.

### Error states

| Error | Detection | Behaviour |
|---|---|---|
| **Capture device missing** | `cv2.VideoCapture` fails to open OR returns a black frame for >5 s | Tray icon → red. Diagnostic window shows "Capture device disconnected — check USB connection." Heartbeat reports `capture_device_status: "missing"`. Frames stop sending; auto-recovers when device returns. |
| **WS disconnect** | `websockets` client raises `ConnectionClosed` | Tray icon → amber pulsing. Reconnect with exponential backoff (1, 2, 4, 8, 16, 30 s). Frames queue in ring buffer. |
| **Auth failure (401 on upgrade)** | Server rejects connection during handshake | Tray icon → red. Stop reconnect attempts. Toast: "Capture Agent needs to re-authenticate — open EsportsForge to refresh keys." Diagnostic window shows the same. |
| **Frame encode failure** | `cv2.imencode` exception or returns failure | Drop the single frame, increment dropped counter, continue. Logged at WARN level. |
| **Config file missing** | `config.toml` absent at expected path | Refuse to start. Toast: "EsportsForge needs to set up the Capture Agent — open Settings → Game Settings → Capture Source." |
| **Config file corrupted** | TOML parse error | Refuse to start. Same toast, with "(config invalid)" appended. |
| **Disk full (ring buffer overflow)** | Heap usage breach | Drop oldest 30 s of buffer. Heartbeat reports `frames_dropped` count. |
| **Server returns malformed message** | JSON parse error or unknown `type` | Log at ERROR level, ignore the message, continue. |
| **OS audio API unavailable for ducking** | Win32 IAudioSessionControl call fails | Capture continues (audio ducking is a separate concern). VoiceForge falls back to in-app ducking. |

### Hotkeys (configurable, defaults shown)

- `Ctrl+Shift+P` — Pause/Resume capture (toggle).
- `Ctrl+Shift+R` — Reconnect (force).
- `Ctrl+Shift+L` — Open log file.

Hotkeys are global (handled via Win32 `RegisterHotKey`). Disabled while the player has a fullscreen game in foreground only if the player explicitly opts in via config.

---

## 6. Local config storage

### File location

`%LOCALAPPDATA%\EsportsForge\CaptureAgent\config.toml`

Written by the EsportsForge desktop installer and by the in-app Settings → Game Settings → Capture Source flow. Human-readable, hand-editable when needed.

### Schema

```toml
# config.toml

[auth]
api_key      = "esf-cap-..."           # short-lived, bound to user, rotates every 90 days
user_id      = "5041bbe7-..."

[core]
endpoint          = "wss://vision.esportsforge.gg/ws/ingest"
fallback_endpoint = "ws://localhost:8100/ws/ingest"     # for dev environments

[capture]
source        = "capture-card"         # capture-card | pc-monitor | test-video
device_index  = 0                       # for capture-card
monitor_index = 0                       # for pc-monitor
crop          = [0, 0, 1920, 1080]      # for pc-monitor
test_video    = ""                       # for test-video

[transport]
target_fps          = 12
adaptive            = true
adaptive_max_fps    = 24
jpeg_quality        = 75
batch_size          = 4
ring_buffer_seconds = 30

[diagnostics]
log_level   = "INFO"
log_path    = "%LOCALAPPDATA%/EsportsForge/CaptureAgent/logs/agent.log"
auto_start  = true                       # launch on Windows boot

[hotkeys]
pause_resume = "Ctrl+Shift+P"
reconnect    = "Ctrl+Shift+R"
view_log     = "Ctrl+Shift+L"
```

### Auth token rotation

- Tokens have a 90-day TTL.
- The EsportsForge backend exposes `POST /api/v1/auth/capture-key/rotate` which the agent calls when its token has <14 days remaining.
- Rotation is gated on the player being authenticated in the dashboard (the agent surfaces a toast: "Sign in to EsportsForge to refresh capture keys").
- Old token remains valid for 7 days after rotation to prevent in-flight session breakage.

### Hot-reload

**Not in v1.** Changes to `config.toml` require an agent restart to take effect. Documented in the diagnostic window's "Settings" page so the player understands.

### Encryption at rest

`api_key` is the only sensitive field. Stored in plaintext in v1 (Windows ACL on `%LOCALAPPDATA%` is the protection). v1.1 will integrate with Windows Credential Manager (`CredWrite` / `CredRead`) for the api_key field; other fields stay in TOML.

---

## 7. Failure modes and graceful degradation

| Failure | Severity | Behaviour | Recovery |
|---|---|---|---|
| Capture device unplugged mid-session | High | Frames stop. Heartbeat reports `capture_device_status: "missing"`. UI surfaces banner. | Auto-recovers within 2 s when device reconnects. No agent restart needed. |
| WS disconnect (transient, <30 s) | Low | Frames queue in ring buffer. Tray amber. | Auto-reconnect, drain buffer in order, transparent to user. |
| WS disconnect (extended, >30 s) | Medium | Buffer fills, oldest frames drop. Reconnect attempts continue. | Auto-recovers. Heartbeat once reconnected reports total dropped count. |
| Auth token expired | Medium | Server rejects upgrade with 401. | Agent stops reconnecting; surfaces toast. Player re-auths in dashboard → backend issues new key → installer/Settings flow updates config.toml → agent restart picks up new key. |
| ElevenLabs / VAF core service down (server-side) | High | Agent stays connected. Server emits no events. UI banner: "Vision service degraded." | Auto-recovers when core service returns. |
| Player's network drops entirely | Medium | WS disconnect; reconnect-with-backoff loop. Capture continues into ring buffer until buffer caps. | Auto-recovers when network returns. Player loses 0–30 s of analysis (whatever wasn't in the buffer). |
| Capture card driver crash | High | OS reports device removal. Same as "unplugged." | Player must reset the capture card (USB unplug/replug or driver restart). Documented in the diagnostic window's error state. |
| Agent process crash | Critical | Tray icon disappears. No frames sent. | v1: manual restart from Start Menu. v1.1: auto-restart via a watchdog service. |
| OS upgrade pending reboot | Low | Agent continues; OS interrupts on shutdown. | Agent re-launches on next boot from auto-start. |
| Disk full (logs filled drive) | Low | Log rotation kicks in (10 MB × 5 generations cap = 50 MB max). | Auto-managed; not a long-term concern. |

### Graceful degradation principle

The agent's job is to keep frames flowing or, when it can't, to make that fact visible without forcing the player to think about it. Any failure that prevents frames from reaching the core results in:
1. Tray icon transitions to amber or red.
2. Diagnostic window shows the specific problem.
3. Toast notification (rate-limited).
4. Heartbeat continues (so the server knows the agent is alive but blocked).
5. Logs are written.

The agent never silently drops frames without surfacing it.

---

## 8. Dev environment requirements

### Player-side (production)

- **OS:** Windows 10 (build 19041+) or Windows 11.
- **Hardware:** USB 3.0+ port for capture card, 8 GB RAM minimum, no GPU requirement.
- **Capture card:** one of:
  - Elgato HD60 X
  - Elgato Game Capture 4K X
  - AVerMedia Live Gamer 4K
  - Generic MS2109-based UVC USB capture
- **Network:** any broadband connection capable of ~5 Mbps sustained upstream.
- **Permissions:** standard user account is sufficient. The agent does not require admin to install (per-user install path).

### Engineer-side (dev)

- **Python 3.12** (matches the EsportsForge backend's pin).
- **OpenCV 4.x** with `cv2.CAP_DSHOW` support (default Windows wheel works).
- **Dependencies:** `websockets`, `pillow`, `pystray` (for tray UI), `mss` (for pc-monitor source), `tomli` / `tomllib`. All pure Python or wheel-available; no compile chain needed.
- **Testing capture:** at least one supported capture card, OR a `test-video` MP4 file for development without hardware.
- **Local backend:** EsportsForge backend running on `:8001` and the VAF core skeleton running on `:8100`. The agent's `config.toml` `[core] fallback_endpoint` points there during dev.
- **Code signing (release builds only):** EV code-signing certificate. The cert is sensitive; only release engineers have access. Dev builds are unsigned (Windows shows the "unrecognized publisher" warning — acceptable for dev).

### Build pipeline

- `pyinstaller --onefile --windowed --icon=assets/forge.ico capture_agent.py` produces the `.exe`.
- NSIS or Inno Setup wraps it in a signed installer.
- CI builds on every tag; release builds get signed and uploaded to S3 (download URL referenced from the EsportsForge desktop landing page).

### Test matrix (CI)

- Unit tests on Linux + Windows for everything except the Win32 tray code (mocked).
- Integration test on Windows with a `test-video` source pointing at a fixture MP4.
- Manual integration test against a real capture card before each release.

---

## Compliance with FORGE_ARCHITECTURE_PATTERN.md

This spec satisfies the five rules:

| Rule | How this spec satisfies it |
|---|---|
| **1. Multi-dimensional from day one.** | The agent is title-agnostic by construction. Title detection happens server-side. Adding a new title (CFB 26, NBA 2K26, etc.) requires zero changes to the agent — only a new server-side adapter and that title's HUD signature. The capture card / pc-monitor / test-video source dimensions are also accommodated from day one via the config schema. |
| **2. Consumers never call external APIs directly.** | The agent does not call ElevenLabs, OpenAI, AnimaForge, or any other external service. It speaks only to the EsportsForge ecosystem — a single WS endpoint to the VAF core, plus a single HTTP endpoint (`auth/capture-key/rotate`) on the EsportsForge backend. All ML and analysis are server-side. |
| **3. Logic lives in the Forge, not the consumer.** | The agent has minimal logic: capture frames → encode → batch → send → handle reconnect. No OCR, no formation detection, no game-state interpretation. Everything intelligent is in the VAF core's adapters. |
| **4. Events are structured and canonical.** | The wire protocol is documented above with explicit JSON schemas (frame_batch, heartbeat, control messages). Both directions (agent → server, server → agent) are typed. The server-to-agent channel uses a `type` discriminator so future control messages are additive without breaking existing handlers. |
| **5. Adapters are added without core changes.** | Adding a new title is purely a server-side change. The agent ships once and does not need a release to support new titles. The agent ships once and does not need a release to support new capture-source types either — `[capture] source` is an open enum the agent dispatches via a small handler registry. |

This spec is ready for engineering kickoff once the architectural decisions in [docs/integrations/visionaudioforge/00-overview.md](../integrations/visionaudioforge/00-overview.md) are signed off.
