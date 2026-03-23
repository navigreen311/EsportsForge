"""Initial schema — Phase 1 MVP models for EsportsForge.

Revision ID: 001
Revises: None
Create Date: 2026-03-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enums ---
    user_role = postgresql.ENUM(
        "free", "competitive", "elite", "team",
        name="user_role", create_type=False,
    )
    input_type = postgresql.ENUM(
        "controller", "kbm", "fightstick",
        name="input_type", create_type=False,
    )
    game_mode = postgresql.ENUM(
        "ranked", "tournament", "training",
        name="game_mode", create_type=False,
    )
    game_result = postgresql.ENUM(
        "win", "loss", "draw",
        name="game_result", create_type=False,
    )
    impact_status = postgresql.ENUM(
        "active", "resolved", "deferred",
        name="impact_status", create_type=False,
    )
    game_environment = postgresql.ENUM(
        "offline_lab", "ranked", "tournament", "broadcast",
        name="game_environment", create_type=False,
    )
    anti_cheat_status = postgresql.ENUM(
        "compliant", "warning", "restricted",
        name="anti_cheat_status", create_type=False,
    )
    scheme_type = postgresql.ENUM(
        "offense", "defense",
        name="scheme_type", create_type=False,
    )
    cfb_scheme_type = postgresql.ENUM(
        "offense", "defense",
        name="cfb_scheme_type", create_type=False,
    )
    recruiting_pipeline = postgresql.ENUM(
        "scouted", "contacted", "visited", "committed", "signed",
        name="recruiting_pipeline", create_type=False,
    )

    # Create all enum types
    user_role.create(op.get_bind(), checkfirst=True)
    input_type.create(op.get_bind(), checkfirst=True)
    game_mode.create(op.get_bind(), checkfirst=True)
    game_result.create(op.get_bind(), checkfirst=True)
    impact_status.create(op.get_bind(), checkfirst=True)
    game_environment.create(op.get_bind(), checkfirst=True)
    anti_cheat_status.create(op.get_bind(), checkfirst=True)
    scheme_type.create(op.get_bind(), checkfirst=True)
    cfb_scheme_type.create(op.get_bind(), checkfirst=True)
    recruiting_pipeline.create(op.get_bind(), checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="free"),
        sa.Column("active_title", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # --- opponents ---
    op.create_table(
        "opponents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(255), unique=True, nullable=True),
        sa.Column("gamertag", sa.String(100), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("archetype", sa.String(100), nullable=True),
        sa.Column("tendencies", postgresql.JSON, nullable=True),
        sa.Column("encounter_count", sa.Integer, default=0, nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_opponents_external_id", "opponents", ["external_id"])
    op.create_index("ix_opponents_gamertag", "opponents", ["gamertag"])

    # --- player_profiles ---
    op.create_table(
        "player_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("tendencies", postgresql.JSON, nullable=True),
        sa.Column("execution_ceiling", postgresql.JSON, nullable=True),
        sa.Column("panic_patterns", postgresql.JSON, nullable=True),
        sa.Column("identity", postgresql.JSON, nullable=True),
        sa.Column("input_type", input_type, nullable=False, server_default="controller"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_player_profiles_user_id", "player_profiles", ["user_id"])

    # --- game_sessions ---
    op.create_table(
        "game_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("mode", game_mode, nullable=False),
        sa.Column("opponent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opponents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("result", game_result, nullable=False),
        sa.Column("stats", postgresql.JSON, nullable=True),
        sa.Column("recommendations_followed", postgresql.JSON, nullable=True),
        sa.Column("session_duration", sa.Integer, nullable=True),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_game_sessions_user_id", "game_sessions", ["user_id"])
    op.create_index("ix_game_sessions_opponent_id", "game_sessions", ["opponent_id"])

    # --- recommendations ---
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("game_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_source", sa.String(100), nullable=False),
        sa.Column("recommendation_type", sa.String(100), nullable=False),
        sa.Column("content", postgresql.JSON, nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False),
        sa.Column("impact_score", sa.Float, nullable=True),
        sa.Column("was_followed", sa.Boolean, nullable=True),
        sa.Column("outcome_correct", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])
    op.create_index("ix_recommendations_session_id", "recommendations", ["session_id"])

    # --- gameplans ---
    op.create_table(
        "gameplans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("opponent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opponents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("plays", postgresql.JSON, nullable=True),
        sa.Column("kill_sheet", postgresql.JSON, nullable=True),
        sa.Column("meta_snapshot", sa.Text, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gameplans_user_id", "gameplans", ["user_id"])
    op.create_index("ix_gameplans_opponent_id", "gameplans", ["opponent_id"])

    # --- agent_performances ---
    op.create_table(
        "agent_performances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("total_recommendations", sa.Integer, default=0, nullable=False),
        sa.Column("correct_predictions", sa.Integer, default=0, nullable=False),
        sa.Column("accuracy_rate", sa.Float, default=0.0, nullable=False),
        sa.Column("last_audit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_performances_agent_name", "agent_performances", ["agent_name"])

    # --- impact_rankings ---
    op.create_table(
        "impact_rankings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("weakness_id", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("win_rate_damage", sa.Float, nullable=False),
        sa.Column("fix_priority", sa.Integer, nullable=False),
        sa.Column("expected_lift", sa.Float, nullable=False),
        sa.Column("time_to_master", sa.String(50), nullable=True),
        sa.Column("status", impact_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_impact_rankings_user_id", "impact_rankings", ["user_id"])
    op.create_index("ix_impact_rankings_status", "impact_rankings", ["status"])

    # --- drills ---
    op.create_table(
        "drills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("skill_target", sa.String(200), nullable=False),
        sa.Column("difficulty_level", sa.String(50), nullable=False),
        sa.Column("drill_config", postgresql.JSON, nullable=True),
        sa.Column("completion_count", sa.Integer, default=0, nullable=False),
        sa.Column("success_rate", sa.Float, default=0.0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_drills_user_id", "drills", ["user_id"])

    # --- integrity_modes ---
    op.create_table(
        "integrity_modes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("environment", game_environment, nullable=False, server_default="offline_lab"),
        sa.Column("restricted_features", postgresql.JSON, nullable=True),
        sa.Column("anti_cheat_status", anti_cheat_status, nullable=False, server_default="compliant"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_integrity_modes_user_id", "integrity_modes", ["user_id"])

    # --- madden_schemes ---
    op.create_table(
        "madden_schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", scheme_type, nullable=False),
        sa.Column("concepts", postgresql.JSON, nullable=True),
        sa.Column("coverage_matrix", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_madden_schemes_name", "madden_schemes", ["name"])

    # --- madden_plays ---
    op.create_table(
        "madden_plays",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("madden_schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("formation", sa.String(100), nullable=False),
        sa.Column("play_type", sa.String(50), nullable=False),
        sa.Column("success_rate", sa.Float, default=0.0, nullable=False),
        sa.Column("situation_tags", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_madden_plays_scheme_id", "madden_plays", ["scheme_id"])
    op.create_index("ix_madden_plays_formation", "madden_plays", ["formation"])

    # --- cfb_schemes ---
    op.create_table(
        "cfb_schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", cfb_scheme_type, nullable=False),
        sa.Column("concepts", postgresql.JSON, nullable=True),
        sa.Column("coverage_matrix", postgresql.JSON, nullable=True),
        sa.Column("momentum_impact", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cfb_schemes_name", "cfb_schemes", ["name"])

    # --- cfb_plays ---
    op.create_table(
        "cfb_plays",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cfb_schemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("formation", sa.String(100), nullable=False),
        sa.Column("play_type", sa.String(50), nullable=False),
        sa.Column("success_rate", sa.Float, default=0.0, nullable=False),
        sa.Column("situation_tags", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cfb_plays_scheme_id", "cfb_plays", ["scheme_id"])
    op.create_index("ix_cfb_plays_formation", "cfb_plays", ["formation"])

    # --- cfb_recruiting_targets ---
    op.create_table(
        "cfb_recruiting_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("position", sa.String(10), nullable=False),
        sa.Column("star_rating", sa.Integer, nullable=False),
        sa.Column("overall_rating", sa.Integer, nullable=False),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("high_school", sa.String(200), nullable=True),
        sa.Column("interest_level", sa.Float, default=0.0, nullable=False),
        sa.Column("pipeline_stage", recruiting_pipeline, nullable=False, server_default="scouted"),
        sa.Column("attributes", postgresql.JSON, nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_cfb_recruiting_targets_user_id", "cfb_recruiting_targets", ["user_id"])
    op.create_index("ix_cfb_recruiting_targets_position", "cfb_recruiting_targets", ["position"])
    op.create_index("ix_cfb_recruiting_targets_pipeline_stage", "cfb_recruiting_targets", ["pipeline_stage"])


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("cfb_recruiting_targets")
    op.drop_table("cfb_plays")
    op.drop_table("cfb_schemes")
    op.drop_table("madden_plays")
    op.drop_table("madden_schemes")
    op.drop_table("integrity_modes")
    op.drop_table("drills")
    op.drop_table("impact_rankings")
    op.drop_table("agent_performances")
    op.drop_table("gameplans")
    op.drop_table("recommendations")
    op.drop_table("game_sessions")
    op.drop_table("player_profiles")
    op.drop_table("opponents")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS recruiting_pipeline")
    op.execute("DROP TYPE IF EXISTS cfb_scheme_type")
    op.execute("DROP TYPE IF EXISTS scheme_type")
    op.execute("DROP TYPE IF EXISTS anti_cheat_status")
    op.execute("DROP TYPE IF EXISTS game_environment")
    op.execute("DROP TYPE IF EXISTS impact_status")
    op.execute("DROP TYPE IF EXISTS game_result")
    op.execute("DROP TYPE IF EXISTS game_mode")
    op.execute("DROP TYPE IF EXISTS input_type")
    op.execute("DROP TYPE IF EXISTS user_role")
