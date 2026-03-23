"""TransferAI — Measures practice-to-competition transfer and flags false confidence.

Prevents theoretical plays from entering the gameplan by comparing
performance across lab, ranked, and tournament modes.
"""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game_session import GameSession
from app.models.game_session import GameMode as DBGameMode

from app.schemas.transfer_ai import (
    CompetitionPackage,
    FalseConfidence,
    GameMode,
    ModeComparison,
    ModeStats,
    ProvenPlay,
    TransferRate,
)

# Map schema GameMode to DB GameMode
_MODE_MAP: dict[GameMode, DBGameMode] = {
    GameMode.RANKED: DBGameMode.RANKED,
    GameMode.TOURNAMENT: DBGameMode.TOURNAMENT,
    GameMode.LAB: DBGameMode.TRAINING,
    GameMode.PRACTICE: DBGameMode.TRAINING,
}

# Minimum sample sizes for statistical reliability
_MIN_SAMPLES = 20
_TRANSFER_THRESHOLDS = {
    "elite": 0.90,
    "solid": 0.75,
    "leaking": 0.55,
    # Below 0.55 → false-confidence
}
_GRADE_THRESHOLDS = [
    (0.95, "A+"), (0.90, "A"), (0.85, "A-"),
    (0.80, "B+"), (0.75, "B"), (0.70, "B-"),
    (0.65, "C+"), (0.60, "C"), (0.55, "C-"),
    (0.50, "D+"), (0.45, "D"), (0.40, "D-"),
    (0.0, "F"),
]


class TransferAI:
    """Core engine for measuring skill transfer across game modes."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Data access helpers (backed by DB)
    # ------------------------------------------------------------------

    async def _get_skill_stats(
        self,
        user_id: str,
        skill: str,
        mode: GameMode,
    ) -> dict:
        """Fetch aggregated stats for a skill in a specific mode from DB."""
        try:
            uid = _uuid.UUID(user_id)
            db_mode = _MODE_MAP.get(mode)
            if db_mode is None:
                return {"attempts": 0, "successes": 0, "avg_exec_time_ms": None}

            result = await self.db.execute(
                select(GameSession)
                .where(
                    GameSession.user_id == uid,
                    GameSession.mode == db_mode,
                )
            )
            sessions = result.scalars().all()

            attempts = 0
            successes = 0
            exec_times: list[float] = []
            for sess in sessions:
                stats = sess.stats or {}
                skill_data = stats.get("skills", {}).get(skill, {})
                attempts += skill_data.get("attempts", 0)
                successes += skill_data.get("successes", 0)
                if skill_data.get("avg_exec_time_ms"):
                    exec_times.append(skill_data["avg_exec_time_ms"])

            avg_exec = sum(exec_times) / len(exec_times) if exec_times else None
            return {
                "attempts": attempts,
                "successes": successes,
                "avg_exec_time_ms": avg_exec,
            }
        except (ValueError, Exception):
            return {"attempts": 0, "successes": 0, "avg_exec_time_ms": None}

    async def _get_all_skills(self, user_id: str, title: str) -> list[str]:
        """Return all skills tracked for a user in a given title from DB."""
        try:
            uid = _uuid.UUID(user_id)
            result = await self.db.execute(
                select(GameSession)
                .where(
                    GameSession.user_id == uid,
                    GameSession.title == title,
                )
                .limit(100)
            )
            sessions = result.scalars().all()
            skills: set[str] = set()
            for sess in sessions:
                stats = sess.stats or {}
                skill_keys = stats.get("skills", {}).keys()
                skills.update(skill_keys)
            return list(skills)
        except (ValueError, Exception):
            return []

    async def _get_tournament_plays(
        self, user_id: str, title: str
    ) -> list[dict]:
        """Return plays executed in tournament mode with outcomes from DB."""
        try:
            uid = _uuid.UUID(user_id)
            result = await self.db.execute(
                select(GameSession)
                .where(
                    GameSession.user_id == uid,
                    GameSession.title == title,
                    GameSession.mode == DBGameMode.TOURNAMENT,
                )
                .order_by(GameSession.played_at.desc())
            )
            sessions = result.scalars().all()
            plays: list[dict] = []
            for sess in sessions:
                stats = sess.stats or {}
                for play in stats.get("plays", []):
                    plays.append(play)
            return plays
        except (ValueError, Exception):
            return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def measure_transfer_rate(
        self,
        user_id: str,
        skill: str,
        from_mode: GameMode,
        to_mode: GameMode,
    ) -> TransferRate:
        """Calculate how well *skill* transfers from *from_mode* to *to_mode*."""
        from_stats = await self._get_skill_stats(user_id, skill, from_mode)
        to_stats = await self._get_skill_stats(user_id, skill, to_mode)

        from_attempts = from_stats["attempts"]
        to_attempts = to_stats["attempts"]
        from_rate = (
            from_stats["successes"] / from_attempts if from_attempts > 0 else 0.0
        )
        to_rate = (
            to_stats["successes"] / to_attempts if to_attempts > 0 else 0.0
        )
        transfer = to_rate / from_rate if from_rate > 0 else 0.0
        reliable = from_attempts >= _MIN_SAMPLES and to_attempts >= _MIN_SAMPLES

        verdict = self._verdict(transfer)

        return TransferRate(
            user_id=user_id,
            skill=skill,
            from_mode=from_mode,
            to_mode=to_mode,
            from_mode_success_rate=from_rate,
            to_mode_success_rate=to_rate,
            transfer_rate=min(transfer, 1.0),
            sample_size_from=from_attempts,
            sample_size_to=to_attempts,
            is_reliable=reliable,
            verdict=verdict,
        )

    async def flag_false_confidence(
        self, user_id: str, title: str
    ) -> list[FalseConfidence]:
        """Identify skills that succeed in lab but fall apart under pressure."""
        skills = await self._get_all_skills(user_id, title)
        flags: list[FalseConfidence] = []

        for skill in skills:
            lab = await self._get_skill_stats(user_id, skill, GameMode.LAB)
            ranked = await self._get_skill_stats(user_id, skill, GameMode.RANKED)
            tourney = await self._get_skill_stats(user_id, skill, GameMode.TOURNAMENT)

            lab_rate = lab["successes"] / lab["attempts"] if lab["attempts"] > 0 else 0.0
            ranked_rate = ranked["successes"] / ranked["attempts"] if ranked["attempts"] > 0 else 0.0
            tourney_rate = tourney["successes"] / tourney["attempts"] if tourney["attempts"] > 0 else 0.0

            worst_live = min(ranked_rate, tourney_rate)
            if lab_rate > 0 and worst_live < lab_rate * 0.55:
                drop = ((lab_rate - worst_live) / lab_rate) * 100
                risk = self._risk_level(drop)
                flags.append(
                    FalseConfidence(
                        skill=skill,
                        lab_success_rate=lab_rate,
                        ranked_success_rate=ranked_rate,
                        tournament_success_rate=tourney_rate,
                        drop_off_pct=round(drop, 1),
                        risk_level=risk,
                        recommendation=self._recommendation(skill, risk),
                    )
                )

        return flags

    async def build_competition_ready_package(
        self, user_id: str, title: str
    ) -> CompetitionPackage:
        """Build a gameplan containing ONLY tournament-proven plays."""
        all_skills = await self._get_all_skills(user_id, title)
        tournament_plays = await self._get_tournament_plays(user_id, title)

        # Index tournament play data by skill
        tourney_by_skill: dict[str, list[dict]] = {}
        for play in tournament_plays:
            tourney_by_skill.setdefault(play.get("skill", ""), []).append(play)

        proven: list[ProvenPlay] = []
        excluded: list[str] = []

        for skill in all_skills:
            plays = tourney_by_skill.get(skill, [])
            if len(plays) < 5:
                excluded.append(skill)
                continue

            successes = sum(1 for p in plays if p.get("success", False))
            rate = successes / len(plays)
            if rate < 0.50:
                excluded.append(skill)
                continue

            avg_pressure = sum(p.get("pressure_index", 0.5) for p in plays) / len(plays)
            last_tourney = max((p.get("tournament_name") for p in plays), default=None)

            proven.append(
                ProvenPlay(
                    skill=skill,
                    tournament_uses=len(plays),
                    tournament_success_rate=round(rate, 3),
                    avg_pressure_index=round(avg_pressure, 3),
                    last_used_tournament=last_tourney,
                )
            )

        total_lab = len(all_skills)
        total_proven = len(proven)
        readiness = total_proven / total_lab if total_lab > 0 else 0.0

        return CompetitionPackage(
            user_id=user_id,
            title=title,
            proven_plays=proven,
            excluded_plays=excluded,
            total_lab_plays=total_lab,
            total_proven=total_proven,
            readiness_score=round(readiness, 3),
        )

    async def get_mode_comparison(
        self, user_id: str, title: str
    ) -> ModeComparison:
        """Compare performance across all game modes for a title."""
        modes = [GameMode.LAB, GameMode.PRACTICE, GameMode.RANKED, GameMode.TOURNAMENT]
        skills = await self._get_all_skills(user_id, title)

        mode_stats_list: list[ModeStats] = []
        mode_rates: dict[GameMode, float] = {}

        for mode in modes:
            total_attempts = 0
            total_successes = 0
            exec_times: list[float] = []
            consistency_scores: list[float] = []

            for skill in skills:
                stats = await self._get_skill_stats(user_id, skill, mode)
                total_attempts += stats["attempts"]
                total_successes += stats["successes"]
                if stats["avg_exec_time_ms"] is not None:
                    exec_times.append(stats["avg_exec_time_ms"])

                if stats["attempts"] > 0:
                    consistency_scores.append(
                        stats["successes"] / stats["attempts"]
                    )

            rate = total_successes / total_attempts if total_attempts > 0 else 0.0
            avg_exec = sum(exec_times) / len(exec_times) if exec_times else None
            consistency = (
                sum(consistency_scores) / len(consistency_scores)
                if consistency_scores
                else 0.0
            )

            mode_rates[mode] = rate
            mode_stats_list.append(
                ModeStats(
                    mode=mode,
                    total_attempts=total_attempts,
                    success_rate=round(rate, 3),
                    avg_execution_time_ms=round(avg_exec, 1) if avg_exec else None,
                    consistency_score=round(consistency, 3),
                )
            )

        # Find biggest gap
        biggest_gap = self._find_biggest_gap(mode_rates)

        # Compute false-confidence flags
        fc_flags = await self.flag_false_confidence(user_id, title)

        # Overall transfer grade: average of (ranked/lab) and (tournament/lab)
        lab_rate = mode_rates.get(GameMode.LAB, 0.0)
        ranked_rate = mode_rates.get(GameMode.RANKED, 0.0)
        tourney_rate = mode_rates.get(GameMode.TOURNAMENT, 0.0)
        if lab_rate > 0:
            avg_transfer = ((ranked_rate / lab_rate) + (tourney_rate / lab_rate)) / 2
        else:
            avg_transfer = 0.0
        grade = self._letter_grade(min(avg_transfer, 1.0))

        return ModeComparison(
            user_id=user_id,
            title=title,
            mode_stats=mode_stats_list,
            biggest_gap=biggest_gap,
            false_confidence_flags=fc_flags,
            overall_transfer_grade=grade,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _verdict(transfer_rate: float) -> str:
        if transfer_rate >= _TRANSFER_THRESHOLDS["elite"]:
            return "elite-transfer"
        if transfer_rate >= _TRANSFER_THRESHOLDS["solid"]:
            return "solid"
        if transfer_rate >= _TRANSFER_THRESHOLDS["leaking"]:
            return "leaking"
        return "false-confidence"

    @staticmethod
    def _risk_level(drop_pct: float) -> str:
        if drop_pct >= 70:
            return "critical"
        if drop_pct >= 50:
            return "high"
        if drop_pct >= 30:
            return "medium"
        return "low"

    @staticmethod
    def _recommendation(skill: str, risk: str) -> str:
        if risk == "critical":
            return f"Remove '{skill}' from gameplan immediately — lab-only skill"
        if risk == "high":
            return f"Demote '{skill}' to practice-only until ranked success rate improves"
        if risk == "medium":
            return f"Increase ranked reps for '{skill}' before using in tournament"
        return f"Monitor '{skill}' — slight lab-to-live drop detected"

    @staticmethod
    def _find_biggest_gap(mode_rates: dict[GameMode, float]) -> str:
        if not mode_rates:
            return "No data available"
        modes = list(mode_rates.keys())
        max_gap = 0.0
        gap_desc = "No significant gaps detected"
        for i, m1 in enumerate(modes):
            for m2 in modes[i + 1:]:
                gap = abs(mode_rates[m1] - mode_rates[m2])
                if gap > max_gap:
                    max_gap = gap
                    higher = m1 if mode_rates[m1] > mode_rates[m2] else m2
                    lower = m2 if higher == m1 else m1
                    gap_desc = (
                        f"{higher.value} -> {lower.value}: "
                        f"{max_gap * 100:.1f}% drop"
                    )
        return gap_desc

    @staticmethod
    def _letter_grade(score: float) -> str:
        for threshold, grade in _GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"
