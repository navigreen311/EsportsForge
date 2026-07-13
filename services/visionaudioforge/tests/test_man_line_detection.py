"""Man-line detector (`OCRPipeline._detect_man_lines`) — recovers the label-less Cover 0.

A real coach-cam MAN look (Cover 0 draws 0 zone labels) is confirmed by its diagonal
play-art line segments (defender->receiver man lines + blitz rushes); a plain field lacks
them (its edges are ~horizontal yard-lines). Measured on real frames: man/blitz coach-cam
16-22 diagonal segments, plain field <=12. These synthetic frames reproduce that contrast.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.adapters.madden26.ocr_pipeline import OCRPipeline

H, W = 1080, 1920


def _pipeline() -> OCRPipeline:
    return OCRPipeline()


def test_diagonal_play_art_lines_detected():
    # ~18 diagonal light lines in the LOS->receivers band -> man look.
    f = np.zeros((H, W, 3), np.uint8)
    y0 = int(H * 0.45)
    for i in range(18):
        x = 90 + i * 95
        cv2.line(f, (x, y0), (x + 190, y0 + 150), (220, 220, 220), 2)
    assert _pipeline()._detect_man_lines(f) is True


def test_plain_field_horizontal_lines_not_detected():
    # Field yard-lines are ~horizontal (not diagonal) -> not a coach-cam man look.
    f = np.zeros((H, W, 3), np.uint8)
    for i in range(10):
        y = int(H * 0.40) + i * 35
        cv2.line(f, (0, y), (W, y), (200, 200, 200), 2)
    assert _pipeline()._detect_man_lines(f) is False


def test_blank_frame_not_detected():
    assert _pipeline()._detect_man_lines(np.zeros((H, W, 3), np.uint8)) is False
