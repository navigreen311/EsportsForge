"""IdentityProfile model — player's competitive identity and philosophy."""

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class IdentityProfile(UUIDPrimaryKeyMixin, Base):
    """Captures a player's offensive/defensive identity and preferences."""

    __tablename__ = "identity_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    offensive_identity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    defensive_philosophy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_tolerance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pace_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comfort_zones: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    agent_directness: Mapped[str | None] = mapped_column(String(50), nullable=True)
    arsenal_voice_settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
