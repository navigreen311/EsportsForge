"""PlayerTwin model — AI digital twin of a player's tendencies and patterns."""

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class PlayerTwin(UUIDPrimaryKeyMixin, Base):
    """Stores the AI-generated player twin data per title."""

    __tablename__ = "player_twins"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    title_id: Mapped[str] = mapped_column(String(50), nullable=False)
    tendencies: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    execution_ceiling: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    panic_patterns: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    coverage_accuracy: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_updated: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
