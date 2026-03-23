"""Agent performance model — Truth Engine accuracy tracking."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class AgentPerformance(UUIDPrimaryKeyMixin, Base):
    """
    Truth Engine — tracks prediction accuracy per AI agent.

    Used to calibrate agent confidence and surface unreliable agents.
    """

    __tablename__ = "agent_performances"

    agent_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="Agent identifier"
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Game title scope"
    )
    total_recommendations: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    correct_predictions: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    accuracy_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="correct / total ratio"
    )
    last_audit_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AgentPerformance {self.agent_name} acc={self.accuracy_rate:.2%}>"
