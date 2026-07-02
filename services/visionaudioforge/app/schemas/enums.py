"""Enums shared across schemas — title, integrity mode, event type."""

from __future__ import annotations

from enum import Enum


class TitleEnum(str, Enum):
    """The 11 EsportsForge titles. Adapters register against this enum."""

    MADDEN26 = "madden26"
    CFB26 = "cfb26"
    NBA2K26 = "nba2k26"
    EAFC26 = "eafc26"
    MLB26 = "mlb26"
    WARZONE = "warzone"
    FORTNITE = "fortnite"
    UFC5 = "ufc5"
    UNDISPUTED = "undisputed"
    PGA2K25 = "pga2k25"
    VIDEO_POKER = "video_poker"


class IntegrityMode(str, Enum):
    """Per-session anti-cheat / competitive-integrity gating mode."""

    OFFLINE_LAB = "offline_lab"
    RANKED = "ranked"
    TOURNAMENT = "tournament"
    BROADCAST = "broadcast"


class EventType(str, Enum):
    """Universal event taxonomy. Adapters emit a subset; new entries
    require a contract version bump per the event-bus contract spec."""

    # Lifecycle
    SESSION_STARTED = "SESSION_STARTED"
    MATCH_STARTED = "MATCH_STARTED"
    MATCH_ENDED = "MATCH_ENDED"
    SNAPSHOT = "SNAPSHOT"

    # Football / basketball / soccer / baseball
    SCORE_CHANGE = "SCORE_CHANGE"
    POSSESSION_CHANGE = "POSSESSION_CHANGE"
    DOWN_AND_DISTANCE = "DOWN_AND_DISTANCE"
    PLAY_STARTED = "PLAY_STARTED"
    PLAY_ENDED = "PLAY_ENDED"
    FORMATION_LOCKED = "FORMATION_LOCKED"
    COVERAGE_LOCKED = "COVERAGE_LOCKED"

    # FPS / BR
    KILL_CONFIRMED = "KILL_CONFIRMED"
    DOWN_CONFIRMED = "DOWN_CONFIRMED"
    DEATH_CONFIRMED = "DEATH_CONFIRMED"
    LOOT_PICKED_UP = "LOOT_PICKED_UP"
    ZONE_PHASE_CHANGE = "ZONE_PHASE_CHANGE"
    LOADOUT_CHANGE = "LOADOUT_CHANGE"

    # Combat
    ROUND_STARTED = "ROUND_STARTED"
    ROUND_ENDED = "ROUND_ENDED"
    DAMAGE_DEALT = "DAMAGE_DEALT"
    DAMAGE_TAKEN = "DAMAGE_TAKEN"
    STANCE_CHANGE = "STANCE_CHANGE"

    # Golf / card
    STROKE_TAKEN = "STROKE_TAKEN"
    HOLE_COMPLETED = "HOLE_COMPLETED"
    HAND_COMPLETED = "HAND_COMPLETED"

    # Misc / debug
    MENU_DETECTED = "MENU_DETECTED"
    INTEGRITY_DROP = "INTEGRITY_DROP"
