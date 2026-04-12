"""Notification model — user notifications and alerts."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, Base):
    """User-facing notifications triggered by AI agents or system events."""

    __tablename__ = "notifications"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
