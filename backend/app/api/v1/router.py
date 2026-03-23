"""Main API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.madden26.roster import router as madden_roster_router
from app.api.v1.endpoints.madden26.matchup import router as madden_matchup_router
from app.api.v1.endpoints.voiceforge import router as voiceforge_router
from app.api.v1.endpoints.fortnite.building import router as fn_building_router
from app.api.v1.endpoints.fortnite.strategy import router as fn_strategy_router

# Video Poker title endpoints
from app.api.v1.endpoints.video_poker.strategy import router as vp_strategy_router
from app.api.v1.endpoints.video_poker.pay_table import router as vp_pay_table_router
from app.api.v1.endpoints.video_poker.bankroll import router as vp_bankroll_router
from app.api.v1.endpoints.video_poker.variance import router as vp_variance_router
from app.api.v1.endpoints.video_poker.responsible_gambling import router as vp_responsible_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(madden_roster_router)
api_v1_router.include_router(madden_matchup_router)
api_v1_router.include_router(voiceforge_router)

# ── Title-specific: Fortnite ─────────────────────────────────────────────
api_v1_router.include_router(fn_building_router)
api_v1_router.include_router(fn_strategy_router)

# ── Title-specific: Video Poker ──────────────────────────────────────────
api_v1_router.include_router(vp_strategy_router)
api_v1_router.include_router(vp_pay_table_router)
api_v1_router.include_router(vp_bankroll_router)
api_v1_router.include_router(vp_variance_router)
api_v1_router.include_router(vp_responsible_router)
