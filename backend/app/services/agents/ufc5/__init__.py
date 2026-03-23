"""UFC 5 AI agents — FightIQ, DamageForge, StaminaChain, GrappleGraph, RoundScore, OnlineCareer."""

from app.services.agents.ufc5.fight_iq import FightIQ
from app.services.agents.ufc5.damage_forge import DamageForge
from app.services.agents.ufc5.stamina_chain import StaminaChain
from app.services.agents.ufc5.grapple_graph import GrappleGraph
from app.services.agents.ufc5.round_score import RoundScoreAI
from app.services.agents.ufc5.online_career import OnlineCareerForge

__all__ = [
    "FightIQ",
    "DamageForge",
    "StaminaChain",
    "GrappleGraph",
    "RoundScoreAI",
    "OnlineCareerForge",
]
