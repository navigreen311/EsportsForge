"""Video Poker models — session tracking, responsible gambling, and analytics."""

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VideoPokerVariant(str, enum.Enum):
    """Supported video poker game variants."""
    JACKS_OR_BETTER = "jacks_or_better"
    DEUCES_WILD = "deuces_wild"
    DOUBLE_BONUS = "double_bonus"
    DOUBLE_DOUBLE_BONUS = "double_double_bonus"
    JOKER_POKER = "joker_poker"


class SelfExclusionType(str, enum.Enum):
    """Self-exclusion duration types."""
    TEMPORARY = "temporary"
    PERMANENT = "permanent"


class ComplianceAction(str, enum.Enum):
    """Actions taken by compliance system."""
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    TIME_LIMIT_WARNING = "time_limit_warning"
    TIME_LIMIT_ENFORCED = "time_limit_enforced"
    LOSS_LIMIT_WARNING = "loss_limit_warning"
    LOSS_LIMIT_ENFORCED = "loss_limit_enforced"
    COOLING_OFF_ACTIVATED = "cooling_off_activated"
    SELF_EXCLUSION_ACTIVATED = "self_exclusion_activated"
    PROBLEM_SIGNAL_DETECTED = "problem_signal_detected"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class VideoPokerSession(UUIDPrimaryKeyMixin, Base):
    """Tracks a video poker play session for analytics and compliance."""

    __tablename__ = "video_poker_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
    )
    variant: Mapped[VideoPokerVariant] = mapped_column(
        Enum(VideoPokerVariant, name="video_poker_variant", native_enum=True),
        nullable=False,
    )
    bet_size: Mapped[float] = mapped_column(Float, nullable=False)
    session_bankroll: Mapped[float] = mapped_column(Float, nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    hands_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_plays: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_result: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    peak_balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    end_reason: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="voluntary | stop_loss | win_goal | time_limit | loss_limit",
    )

    def __repr__(self) -> str:
        return f"<VideoPokerSession {self.id} {self.variant.value}>"


class ResponsibleGamblingConfig(UUIDPrimaryKeyMixin, Base):
    """User's responsible gambling configuration — persistent settings."""

    __tablename__ = "responsible_gambling_configs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True,
    )
    session_time_limit_minutes: Mapped[int] = mapped_column(
        Integer, default=240, nullable=False,
    )
    daily_loss_limit: Mapped[float] = mapped_column(
        Float, default=200.0, nullable=False,
    )
    weekly_loss_limit: Mapped[float] = mapped_column(
        Float, default=500.0, nullable=False,
    )
    monthly_loss_limit: Mapped[float] = mapped_column(
        Float, default=1500.0, nullable=False,
    )

    # Self-exclusion
    self_excluded: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    self_exclusion_type: Mapped[Optional[SelfExclusionType]] = mapped_column(
        Enum(SelfExclusionType, name="self_exclusion_type", native_enum=True),
        nullable=True,
    )
    self_exclusion_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    self_exclusion_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    self_exclusion_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    # Cooling-off
    cooling_off_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    def __repr__(self) -> str:
        return f"<ResponsibleGamblingConfig user={self.user_id}>"


class ComplianceAuditLog(UUIDPrimaryKeyMixin, Base):
    """Immutable audit trail for all compliance actions — legally required."""

    __tablename__ = "compliance_audit_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
    )
    action: Mapped[ComplianceAction] = mapped_column(
        Enum(ComplianceAction, name="compliance_action", native_enum=True),
        nullable=False,
    )
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True,
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )

    def __repr__(self) -> str:
        return f"<ComplianceAuditLog {self.action.value} user={self.user_id}>"
