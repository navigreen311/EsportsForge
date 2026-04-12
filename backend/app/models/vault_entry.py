"""VaultEntry model — knowledge vault entries for AI context."""

from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class VaultEntry(UUIDPrimaryKeyMixin, Base):
    """Individual knowledge entries stored in a player's vault."""

    __tablename__ = "vault_entries"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    title_id: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
