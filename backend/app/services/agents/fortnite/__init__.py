"""Fortnite title intelligence module — 5 specialized agents.

Agents:
    BuildForge FN — build sequence training and analysis
    EditForge — edit speed and pressure training
    ZoneForge FN — storm rotation and zone discipline
    FortniteMeta AI — loot pool, augments, mobility optimization
    FortniteTwin — player digital twin profile
"""

from app.services.agents.fortnite.build_forge import BuildForgeFN
from app.services.agents.fortnite.edit_forge import EditForge
from app.services.agents.fortnite.zone_forge_fn import ZoneForgeFN
from app.services.agents.fortnite.fortnite_meta import FortniteMetaAI
from app.services.agents.fortnite.fortnite_twin import FortniteTwin

__all__ = [
    "BuildForgeFN",
    "EditForge",
    "ZoneForgeFN",
    "FortniteMetaAI",
    "FortniteTwin",
]
