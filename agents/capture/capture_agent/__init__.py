"""EsportsForge Capture Agent — Phase 0 skeleton.

Reads frames from a configured source (capture-card / pc-monitor /
test-video) and forwards them to the VisionAudioForge core service.

Title-agnostic by construction. Title detection is server-side.

Phase 0 ships the test-video source + WS transport. Real capture-card
integration (DirectShow via cv2.CAP_DSHOW), system tray UI (pystray),
diagnostic window (Tk), and Credential Manager integration (pywin32) all
land in Phase 1 milestones M1 final + M8 hardening.
"""

__version__ = "0.0.1-phase-0"
