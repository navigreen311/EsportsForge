"""Opponent model — scouted or encountered opponents."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class Opponent(UUIDPrimaryKeyMixin, Base):
    """
    An opponent encountered in competitive play.

    Stores scouting data, tendencies, and encounter history.
    """

    __tablename__ = "opponents"

    external_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True,
        comment="Platform-specific player ID"
    )
    gamertag: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Game title"
    )
    archetype: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Classified playstyle archetype"
    )
    tendencies: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Observed behavioral tendencies"
    )
    encounter_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Opponent {self.gamertag} ({self.archetype})>"
