"""College Football 26 specific models — schemes, recruiting, dynasty."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class CFBSchemeType(str, enum.Enum):
    """Offensive or defensive scheme classification."""

    OFFENSE = "offense"
    DEFENSE = "defense"


class CFBScheme(UUIDPrimaryKeyMixin, Base):
    """
    CFB 26 scheme — similar to Madden but with momentum impact tracking.

    College football has unique momentum and crowd mechanics.
    """

    __tablename__ = "cfb_schemes"

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    type: Mapped[CFBSchemeType] = mapped_column(
        Enum(CFBSchemeType, name="cfb_scheme_type", native_enum=True), nullable=False
    )
    concepts: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Core scheme concepts"
    )
    coverage_matrix: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Coverage matchup matrix"
    )
    momentum_impact: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="How momentum affects scheme effectiveness"
    )

    # Relationships
    plays: Mapped[list["CFBPlay"]] = relationship(
        back_populates="scheme", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CFBScheme {self.name} ({self.type.value})>"


class CFBPlay(UUIDPrimaryKeyMixin, Base):
    """CFB 26 play within a scheme."""

    __tablename__ = "cfb_plays"

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cfb_schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    formation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    play_type: Mapped[str] = mapped_column(String(50), nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    situation_tags: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    scheme: Mapped["CFBScheme"] = relationship(back_populates="plays")

    def __repr__(self) -> str:
        return f"<CFBPlay {self.name} ({self.formation})>"


class RecruitingPipeline(str, enum.Enum):
    """Recruiting pipeline stage."""

    SCOUTED = "scouted"
    CONTACTED = "contacted"
    VISITED = "visited"
    COMMITTED = "committed"
    SIGNED = "signed"


class CFBRecruitingTarget(UUIDPrimaryKeyMixin, Base):
    """
    CFB 26 recruiting target — dynasty mode recruit tracking.

    Stores recruit attributes, interest level, and pipeline stage.
    """

    __tablename__ = "cfb_recruiting_targets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    star_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    high_school: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    interest_level: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="0.0-1.0 interest in your program"
    )
    pipeline_stage: Mapped[RecruitingPipeline] = mapped_column(
        Enum(RecruitingPipeline, name="recruiting_pipeline", native_enum=True),
        default=RecruitingPipeline.SCOUTED,
        nullable=False,
        index=True,
    )
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Detailed recruit attributes"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )

    def __repr__(self) -> str:
        return f"<CFBRecruitingTarget {self.name} ({self.position}) {self.star_rating}*>"
