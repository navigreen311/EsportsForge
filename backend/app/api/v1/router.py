"""Main API v1 router — aggregates all endpoint routers.

Every endpoint file in backend/app/api/v1/endpoints/ is imported and mounted
here. Each import is wrapped in try/except so a broken module won't take down
the entire application.
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

api_router = APIRouter()

# ---------------------------------------------------------------------------
# Helper — safe import + mount
# ---------------------------------------------------------------------------

def _mount(module_path: str, prefix: str, tags: list[str]) -> None:
    """Import *module_path*, pull its ``router`` attribute, and include it."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        api_router.include_router(mod.router, prefix=prefix, tags=tags)
    except ImportError as exc:
        logger.warning("Could not import %s: %s", module_path, exc)
    except AttributeError:
        logger.warning("Module %s has no 'router' attribute — skipped", module_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unexpected error importing %s: %s", module_path, exc)


# ═══════════════════════════════════════════════════════════════════════════
# Core
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.health",          prefix="/health",          tags=["Health"])
_mount("app.api.v1.endpoints.backbone",        prefix="/backbone",        tags=["Backbone"])
_mount("app.api.v1.endpoints.auth",            prefix="/auth",            tags=["Auth"])
_mount("app.api.v1.endpoints.users",           prefix="/users",           tags=["Users"])
_mount("app.api.v1.endpoints.onboarding",      prefix="/onboarding",      tags=["Onboarding"])
_mount("app.api.v1.endpoints.sessions",        prefix="/sessions",        tags=["Sessions"])
_mount("app.api.v1.endpoints.titles",          prefix="/titles",          tags=["Titles"])

# ═══════════════════════════════════════════════════════════════════════════
# Backbone Services
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.forgecore",       prefix="/forgecore",       tags=["ForgeCore"])
_mount("app.api.v1.endpoints.player_twin",     prefix="/player-twin",     tags=["PlayerTwin"])
_mount("app.api.v1.endpoints.impact_rank",     prefix="/impact-rank",     tags=["ImpactRank"])
_mount("app.api.v1.endpoints.truth_engine",    prefix="/truth-engine",    tags=["TruthEngine"])
_mount("app.api.v1.endpoints.loop_ai",         prefix="/loop-ai",         tags=["LoopAI"])
_mount("app.api.v1.endpoints.adapt",           prefix="/adapt",           tags=["Adapt"])
_mount("app.api.v1.endpoints.calibration",     prefix="/calibration",     tags=["Calibration"])
_mount("app.api.v1.endpoints.confidence",      prefix="/confidence",      tags=["Confidence"])
_mount("app.api.v1.endpoints.integrity",       prefix="/integrity",       tags=["Integrity"])
_mount("app.api.v1.endpoints.trust",           prefix="/trust",           tags=["Trust"])
_mount("app.api.v1.endpoints.proof",           prefix="/proof",           tags=["Proof"])
_mount("app.api.v1.endpoints.meta_version",    prefix="/meta-version",    tags=["MetaVersion"])
_mount("app.api.v1.endpoints.install",         prefix="/install",         tags=["Install"])
_mount("app.api.v1.endpoints.extensions",      prefix="/extensions",      tags=["Extensions"])
_mount("app.api.v1.endpoints.vault",           prefix="/vault",           tags=["Vault"])
_mount("app.api.v1.endpoints.transfer_ai",     prefix="/transfer-ai",     tags=["TransferAI"])
_mount("app.api.v1.endpoints.cross_title",     prefix="/cross-title",     tags=["CrossTitle"])

# ═══════════════════════════════════════════════════════════════════════════
# Game Data & Training
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.data",            prefix="/data",            tags=["Data"])
_mount("app.api.v1.endpoints.drills",          prefix="/drills",          tags=["Drills"])
_mount("app.api.v1.endpoints.film",            prefix="/film",            tags=["Film"])
_mount("app.api.v1.endpoints.input_lab",       prefix="/input-lab",       tags=["InputLab"])
_mount("app.api.v1.endpoints.mental",          prefix="/mental",          tags=["Mental"])
_mount("app.api.v1.endpoints.opponents",       prefix="/opponents",       tags=["Opponents"])
_mount("app.api.v1.endpoints.progression",     prefix="/progression",     tags=["Progression"])
_mount("app.api.v1.endpoints.ratings",         prefix="/ratings",         tags=["Ratings"])
_mount("app.api.v1.endpoints.sim",             prefix="/sim",             tags=["Sim"])
_mount("app.api.v1.endpoints.simulation",      prefix="/simulation",      tags=["Simulation"])
_mount("app.api.v1.endpoints.tournament",      prefix="/tournament",      tags=["Tournament"])
_mount("app.api.v1.endpoints.streamer",        prefix="/streamer",        tags=["Streamer"])
_mount("app.api.v1.endpoints.gameplans",       prefix="/gameplans",       tags=["Gameplans"])
_mount("app.api.v1.endpoints.recommendations", prefix="/recommendations", tags=["Recommendations"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — Madden 26
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.madden26.roster",    prefix="/madden26/roster",    tags=["Madden 26"])
_mount("app.api.v1.endpoints.madden26.matchup",   prefix="/madden26/matchup",   tags=["Madden 26"])
_mount("app.api.v1.endpoints.madden26.scheme",    prefix="/madden26/scheme",    tags=["Madden 26"])
_mount("app.api.v1.endpoints.madden26.gameplan",  prefix="/madden26/gameplan",  tags=["Madden 26"])
_mount("app.api.v1.endpoints.madden26.killsheet", prefix="/madden26/killsheet", tags=["Madden 26"])
_mount("app.api.v1.endpoints.madden26.clock",     prefix="/madden26/clock",     tags=["Madden 26"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — CFB 26
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.cfb26.scheme",       prefix="/cfb26/scheme",       tags=["CFB 26"])
_mount("app.api.v1.endpoints.cfb26.recruiting",   prefix="/cfb26/recruiting",   tags=["CFB 26"])
_mount("app.api.v1.endpoints.cfb26.momentum",     prefix="/cfb26/momentum",     tags=["CFB 26"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — NBA 2K26
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.nba2k26.builds",     prefix="/nba2k26/builds",     tags=["NBA 2K26"])
_mount("app.api.v1.endpoints.nba2k26.gameplay",   prefix="/nba2k26/gameplay",   tags=["NBA 2K26"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — EA FC 26
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.eafc26.squad",       prefix="/eafc26/squad",       tags=["EA FC 26"])
_mount("app.api.v1.endpoints.eafc26.tactics",     prefix="/eafc26/tactics",     tags=["EA FC 26"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — MLB 26
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.mlb26.hitting",      prefix="/mlb26/hitting",      tags=["MLB 26"])
_mount("app.api.v1.endpoints.mlb26.pitching",     prefix="/mlb26/pitching",     tags=["MLB 26"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — UFC 5
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.ufc5.combat",        prefix="/ufc5/combat",        tags=["UFC 5"])
_mount("app.api.v1.endpoints.ufc5.career",        prefix="/ufc5/career",        tags=["UFC 5"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — Undisputed
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.undisputed.boxing",   prefix="/undisputed/boxing",  tags=["Undisputed"])
_mount("app.api.v1.endpoints.undisputed.career",   prefix="/undisputed/career",  tags=["Undisputed"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — Warzone
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.warzone.loadout",     prefix="/warzone/loadout",    tags=["Warzone"])
_mount("app.api.v1.endpoints.warzone.combat",      prefix="/warzone/combat",     tags=["Warzone"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — Fortnite
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.fortnite.building",   prefix="/fortnite/building",  tags=["Fortnite"])
_mount("app.api.v1.endpoints.fortnite.strategy",   prefix="/fortnite/strategy",  tags=["Fortnite"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — PGA 2K25
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.pga2k25.course",     prefix="/pga2k25/course",     tags=["PGA 2K25"])
_mount("app.api.v1.endpoints.pga2k25.green",      prefix="/pga2k25/green",      tags=["PGA 2K25"])
_mount("app.api.v1.endpoints.pga2k25.ranked",     prefix="/pga2k25/ranked",     tags=["PGA 2K25"])
_mount("app.api.v1.endpoints.pga2k25.swing",      prefix="/pga2k25/swing",      tags=["PGA 2K25"])

# ═══════════════════════════════════════════════════════════════════════════
# Title Modules — Video Poker
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.video_poker.strategy",             prefix="/video-poker/strategy",             tags=["Video Poker"])
_mount("app.api.v1.endpoints.video_poker.pay_table",            prefix="/video-poker/pay-table",            tags=["Video Poker"])
_mount("app.api.v1.endpoints.video_poker.bankroll",             prefix="/video-poker/bankroll",             tags=["Video Poker"])
_mount("app.api.v1.endpoints.video_poker.variance",             prefix="/video-poker/variance",             tags=["Video Poker"])
_mount("app.api.v1.endpoints.video_poker.responsible_gambling",  prefix="/video-poker/responsible-gambling", tags=["Video Poker"])

# ═══════════════════════════════════════════════════════════════════════════
# Integrations
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.voiceforge",      prefix="/voiceforge",      tags=["VoiceForge"])
_mount("app.api.v1.endpoints.visionaudio",     prefix="/visionaudio",     tags=["VisionAudioForge"])

# ═══════════════════════════════════════════════════════════════════════════
# Ecosystem
# ═══════════════════════════════════════════════════════════════════════════
_mount("app.api.v1.endpoints.community",       prefix="/community",       tags=["Community"])
_mount("app.api.v1.endpoints.coach",           prefix="/coach",           tags=["Coach Portal"])
_mount("app.api.v1.endpoints.mobile",          prefix="/mobile",          tags=["Mobile"])
