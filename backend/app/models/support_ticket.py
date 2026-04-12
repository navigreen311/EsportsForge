"""Support ticket model for customer support system."""

from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class SupportTicket(UUIDPrimaryKeyMixin, Base):
    """Customer support ticket."""

    __tablename__ = "support_tickets"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), default="other", nullable=False,
        comment="billing, bug, account, feature, feedback, other",
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="normal", nullable=False,
        comment="low, normal, high",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False,
        comment="open, in_progress, resolved",
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SupportTicket {self.id} [{self.status}] {self.subject[:40]}>"
