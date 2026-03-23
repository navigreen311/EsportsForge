"""EA FC 26 AI agents — SquadForge, TacticsForge, SkillForge, SetPieceForge, PlayerTwin."""

from app.services.agents.eafc26.squad_forge import SquadForge
from app.services.agents.eafc26.tactics_forge import TacticsForge
from app.services.agents.eafc26.skill_forge import SkillForge
from app.services.agents.eafc26.set_piece_forge import SetPieceForge
from app.services.agents.eafc26.eafc_player_twin import EAFCPlayerTwin

__all__ = ["SquadForge", "TacticsForge", "SkillForge", "SetPieceForge", "EAFCPlayerTwin"]
