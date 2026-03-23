"""DamageForge — damage tracking, vulnerability windows, and cut targeting risk.

Tracks cumulative damage across leg/body/head/cuts/stamina drain, identifies
vulnerability windows after opponent actions, and calculates cut targeting risk.
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.ufc5.combat import (
    BodyRegion,
    CutSeverity,
    DamageEntry,
    DamageState,
    StrikeType,
    VulnerabilityWindow,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — damage values by strike type and target region
# ---------------------------------------------------------------------------

_BASE_DAMAGE: dict[StrikeType, float] = {
    StrikeType.JAB: 5.0,
    StrikeType.CROSS: 10.0,
    StrikeType.HOOK: 12.0,
    StrikeType.UPPERCUT: 14.0,
    StrikeType.OVERHAND: 15.0,
    StrikeType.BODY_HOOK: 10.0,
    StrikeType.BODY_STRAIGHT: 8.0,
    StrikeType.LEG_KICK: 8.0,
    StrikeType.CALF_KICK: 10.0,
    StrikeType.BODY_KICK: 12.0,
    StrikeType.HEAD_KICK: 20.0,
    StrikeType.SPINNING_BACK_KICK: 18.0,
    StrikeType.SPINNING_BACK_FIST: 16.0,
    StrikeType.FRONT_KICK: 9.0,
    StrikeType.KNEE: 14.0,
    StrikeType.ELBOW: 13.0,
    StrikeType.SUPERMAN_PUNCH: 13.0,
    StrikeType.FLYING_KNEE: 22.0,
}

_REGION_MULTIPLIERS: dict[BodyRegion, float] = {
    BodyRegion.HEAD: 1.5,
    BodyRegion.BODY: 1.0,
    BodyRegion.LEFT_LEG: 0.8,
    BodyRegion.RIGHT_LEG: 0.8,
    BodyRegion.LEFT_ARM: 0.5,
    BodyRegion.RIGHT_ARM: 0.5,
}

_STRIKE_TARGET_MAP: dict[StrikeType, BodyRegion] = {
    StrikeType.JAB: BodyRegion.HEAD,
    StrikeType.CROSS: BodyRegion.HEAD,
    StrikeType.HOOK: BodyRegion.HEAD,
    StrikeType.UPPERCUT: BodyRegion.HEAD,
    StrikeType.OVERHAND: BodyRegion.HEAD,
    StrikeType.BODY_HOOK: BodyRegion.BODY,
    StrikeType.BODY_STRAIGHT: BodyRegion.BODY,
    StrikeType.LEG_KICK: BodyRegion.LEFT_LEG,
    StrikeType.CALF_KICK: BodyRegion.LEFT_LEG,
    StrikeType.BODY_KICK: BodyRegion.BODY,
    StrikeType.HEAD_KICK: BodyRegion.HEAD,
    StrikeType.SPINNING_BACK_KICK: BodyRegion.BODY,
    StrikeType.SPINNING_BACK_FIST: BodyRegion.HEAD,
    StrikeType.FRONT_KICK: BodyRegion.BODY,
    StrikeType.KNEE: BodyRegion.BODY,
    StrikeType.ELBOW: BodyRegion.HEAD,
    StrikeType.SUPERMAN_PUNCH: BodyRegion.HEAD,
    StrikeType.FLYING_KNEE: BodyRegion.HEAD,
}

_CUT_SEVERITY_ORDER = [
    CutSeverity.NONE,
    CutSeverity.MINOR,
    CutSeverity.MODERATE,
    CutSeverity.SEVERE,
    CutSeverity.CRITICAL,
]

# Strikes with the highest cut probability
_CUT_STRIKES = {StrikeType.ELBOW, StrikeType.HOOK, StrikeType.UPPERCUT}

# Recovery frames after common whiffs (at 60fps)
_WHIFF_RECOVERY: dict[StrikeType, int] = {
    StrikeType.OVERHAND: 28,
    StrikeType.HOOK: 22,
    StrikeType.UPPERCUT: 24,
    StrikeType.HEAD_KICK: 35,
    StrikeType.SPINNING_BACK_KICK: 40,
    StrikeType.SPINNING_BACK_FIST: 38,
    StrikeType.FLYING_KNEE: 42,
    StrikeType.SUPERMAN_PUNCH: 30,
    StrikeType.KNEE: 20,
    StrikeType.CROSS: 18,
    StrikeType.JAB: 12,
    StrikeType.LEG_KICK: 16,
    StrikeType.CALF_KICK: 16,
    StrikeType.BODY_KICK: 25,
    StrikeType.BODY_HOOK: 20,
    StrikeType.BODY_STRAIGHT: 16,
    StrikeType.FRONT_KICK: 22,
    StrikeType.ELBOW: 18,
}


class DamageForge:
    """Damage accumulation tracker — leg/body/head/cuts/stamina drain.

    Maintains a running damage state and identifies vulnerability windows
    and cut targeting opportunities.
    """

    def __init__(self) -> None:
        self._state = DamageState()

    @property
    def state(self) -> DamageState:
        """Current cumulative damage state."""
        return self._state

    def reset(self) -> None:
        """Reset damage state for a new fight."""
        self._state = DamageState()

    def apply_damage(
        self,
        strike_type: StrikeType,
        region: BodyRegion | None = None,
        is_critical: bool = False,
        round_number: int = 1,
        timestamp: float = 0.0,
    ) -> DamageEntry:
        """
        Apply a single strike of damage and update cumulative state.

        Args:
            strike_type: Type of strike landed.
            region: Override target region (defaults to strike's natural target).
            is_critical: Whether the strike was a counter or critical hit.
            round_number: Current round number.
            timestamp: Time in round (seconds).

        Returns:
            The DamageEntry created.
        """
        target = region or _STRIKE_TARGET_MAP.get(strike_type, BodyRegion.HEAD)
        base = _BASE_DAMAGE.get(strike_type, 8.0)
        multiplier = _REGION_MULTIPLIERS.get(target, 1.0)
        damage = base * multiplier * (1.5 if is_critical else 1.0)

        entry = DamageEntry(
            region=target,
            strike_type=strike_type,
            damage_value=round(damage, 1),
            is_critical=is_critical,
            round_number=round_number,
            timestamp_seconds=timestamp,
        )

        self._state.damage_log.append(entry)
        self._update_region_damage(target, damage)
        self._update_cut_state(strike_type, target)
        self._update_ko_vulnerability()
        self._update_stamina_drain()

        return entry

    def get_vulnerability_windows(self) -> list[VulnerabilityWindow]:
        """
        Return all known vulnerability windows based on opponent whiff recovery.

        Each window describes what happens when an opponent misses a strike
        and the optimal punish response.
        """
        windows: list[VulnerabilityWindow] = []
        for strike, frames in sorted(
            _WHIFF_RECOVERY.items(), key=lambda x: x[1], reverse=True
        ):
            best_region = self._best_target_region()
            punish = self._optimal_punish_for_window(frames)
            expected = sum(
                _BASE_DAMAGE.get(p, 8.0) * _REGION_MULTIPLIERS.get(best_region, 1.0)
                for p in punish
            )
            windows.append(
                VulnerabilityWindow(
                    trigger=f"Opponent whiffs {strike.value}",
                    duration_frames=frames,
                    optimal_punish=punish,
                    expected_damage=round(expected, 1),
                    body_target=best_region,
                )
            )
        return windows

    def get_cut_risk_assessment(self) -> dict[str, Any]:
        """
        Assess current cut targeting viability.

        Returns dict with cut severity, stoppage risk, and recommended strategy.
        """
        severity = self._state.cut_severity
        idx = _CUT_SEVERITY_ORDER.index(severity)
        stoppage_risk = idx / (len(_CUT_SEVERITY_ORDER) - 1)

        should_target = severity in (CutSeverity.MODERATE, CutSeverity.SEVERE)
        recommended_strikes = (
            [StrikeType.ELBOW, StrikeType.HOOK, StrikeType.UPPERCUT]
            if should_target
            else []
        )

        return {
            "current_severity": severity.value,
            "stoppage_risk": round(stoppage_risk, 2),
            "should_target_cut": should_target,
            "recommended_strikes": [s.value for s in recommended_strikes],
            "cut_location": (
                self._state.cut_location.value if self._state.cut_location else None
            ),
        }

    def get_damage_summary(self) -> dict[str, Any]:
        """Return a human-readable summary of cumulative damage."""
        return {
            "head": round(self._state.head_damage, 1),
            "body": round(self._state.body_damage, 1),
            "left_leg": round(self._state.left_leg_damage, 1),
            "right_leg": round(self._state.right_leg_damage, 1),
            "cut": self._state.cut_severity.value,
            "ko_vulnerability": round(self._state.knockout_vulnerability, 2),
            "stamina_drain_factor": round(self._state.stamina_drain_factor, 2),
            "is_rocked": self._state.is_rocked,
            "total_strikes": len(self._state.damage_log),
            "most_damaged_region": self._best_target_region().value,
        }

    # --- private helpers ---

    def _update_region_damage(self, region: BodyRegion, damage: float) -> None:
        if region == BodyRegion.HEAD:
            self._state.head_damage = min(100.0, self._state.head_damage + damage)
        elif region == BodyRegion.BODY:
            self._state.body_damage = min(100.0, self._state.body_damage + damage)
        elif region == BodyRegion.LEFT_LEG:
            self._state.left_leg_damage = min(
                100.0, self._state.left_leg_damage + damage
            )
        elif region == BodyRegion.RIGHT_LEG:
            self._state.right_leg_damage = min(
                100.0, self._state.right_leg_damage + damage
            )

    def _update_cut_state(self, strike: StrikeType, region: BodyRegion) -> None:
        """Progress cut severity if an elbow/hook lands on the head."""
        if strike not in _CUT_STRIKES or region != BodyRegion.HEAD:
            return
        idx = _CUT_SEVERITY_ORDER.index(self._state.cut_severity)
        # ~25% chance to escalate per cut strike
        if idx < len(_CUT_SEVERITY_ORDER) - 1:
            self._state.cut_severity = _CUT_SEVERITY_ORDER[idx + 1]
            self._state.cut_location = BodyRegion.HEAD

    def _update_ko_vulnerability(self) -> None:
        """Recalculate KO vulnerability from head damage."""
        head = self._state.head_damage
        self._state.knockout_vulnerability = min(1.0, head / 100.0)
        self._state.is_rocked = head > 65.0

    def _update_stamina_drain(self) -> None:
        """Body damage increases stamina drain factor."""
        body = self._state.body_damage
        self._state.stamina_drain_factor = 1.0 + (body / 100.0) * 1.5

    def _best_target_region(self) -> BodyRegion:
        """Return the region with the most accumulated damage (easiest to finish)."""
        regions = {
            BodyRegion.HEAD: self._state.head_damage,
            BodyRegion.BODY: self._state.body_damage,
            BodyRegion.LEFT_LEG: self._state.left_leg_damage,
            BodyRegion.RIGHT_LEG: self._state.right_leg_damage,
        }
        return max(regions, key=regions.get)  # type: ignore[arg-type]

    def _optimal_punish_for_window(self, frames: int) -> list[StrikeType]:
        """Select the best punish strikes that fit within a vulnerability window."""
        # Rough frame costs for punish strikes
        fast = [(StrikeType.JAB, 8), (StrikeType.CROSS, 12)]
        medium = [(StrikeType.HOOK, 16), (StrikeType.BODY_HOOK, 16)]
        slow = [(StrikeType.UPPERCUT, 20), (StrikeType.OVERHAND, 22)]

        selected: list[StrikeType] = []
        remaining = frames

        for strike, cost in fast:
            if remaining >= cost:
                selected.append(strike)
                remaining -= cost

        for strike, cost in medium:
            if remaining >= cost:
                selected.append(strike)
                remaining -= cost
                break

        for strike, cost in slow:
            if remaining >= cost:
                selected.append(strike)
                break

        return selected or [StrikeType.JAB]
