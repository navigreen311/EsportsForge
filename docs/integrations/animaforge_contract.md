# AnimaForge Integration — Shared Contract

> **Read this before writing any code.** Every agent working on `ai-feature/animaforge-*` branches must follow this contract. It locks the public surfaces (DB schema, API endpoints, component props, env vars, file paths) so 10 parallel branches merge cleanly.

Source blueprint: `EsportsForge_AnimaForge_Integration.docx` (see Section references below).
External repo: `navigreen311/animaforge` (treat as remote service via REST — do not vendor the SDK).

---

## 1. Architecture decisions

**Stack translation.** The blueprint is written in Next.js + Prisma terms. EsportsForge's backend is **FastAPI + SQLAlchemy (async)**, frontend is **Next.js 14 + TypeScript**. We translate as follows:

| Blueprint says | We implement as |
|---|---|
| `lib/services/animaforge.ts` (Next.js server) | `backend/app/services/animaforge/client.py` (httpx async, on FastAPI) |
| `app/api/animaforge/*/route.ts` | `backend/app/api/v1/endpoints/animaforge_*.py` |
| Prisma `AnimaForgeJob` model | SQLAlchemy `AnimaForgeJob` model in `backend/app/models/animaforge.py` |
| `prisma migrate dev` | Alembic migration under `backend/alembic/versions/` |
| `redis.setex(...)` cache | Skip (Redis is empty in dev). Read direct from DB; pre-generation handles the rest. |
| Direct frontend → AnimaForge call | **Never.** Frontend → FastAPI → AnimaForge. Secret stays on backend. |

**Frontend never talks to AnimaForge directly.** All calls go through `/api/v1/animaforge/*` on the FastAPI backend. The `ANIMAFORGE_API_KEY` is server-side only.

**Async render-job pattern (verbatim from blueprint Section 1):**
1. Frontend POSTs to `/api/v1/animaforge/<feature>` → backend creates job row → calls AnimaForge `/api/v1/render` → returns `{job_id, estimated_seconds}` or `{video_url}` (cached).
2. AnimaForge calls webhook `POST /api/v1/animaforge/webhook` on completion.
3. Webhook updates row, creates Notification, fires push.
4. Frontend either polls `/api/v1/animaforge/jobs/{job_id}` every 5s, or relies on the notification.

**Graceful degradation.** If `AnimaForgeService.is_available()` returns `False`, all UI hides silently — no disabled buttons, no error toasts. Call this at component mount via `GET /api/v1/animaforge/status`.

---

## 2. Canonical data model

**File:** `backend/app/models/animaforge.py` (owned by Agent #1).

```python
"""AnimaForge integration — render-job tracking."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


# Job types
JOB_TYPE_WEAPON = "weapon-diagram"
JOB_TYPE_DRILL = "drill-demo"
JOB_TYPE_PLAY = "play-diagram"
JOB_TYPE_SHARE = "share-win"
JOB_TYPES: tuple[str, ...] = (
    JOB_TYPE_WEAPON,
    JOB_TYPE_DRILL,
    JOB_TYPE_PLAY,
    JOB_TYPE_SHARE,
)

# Job status
STATUS_PENDING = "pending"
STATUS_RENDERING = "rendering"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"


class AnimaForgeJob(UUIDPrimaryKeyMixin, Base):
    """Tracks every render job submitted to AnimaForge.

    A row exists for every render request, including failed ones (so the
    UI can show retry state). Successful jobs hold the videoUrl/thumbnailUrl
    that completed renders are served from.
    """

    __tablename__ = "animaforge_jobs"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )  # AnimaForge's external id
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # weapon: source_id = weapon_id (uuid)
    # drill:  source_id = f"{title_id}:{drill_type}"  (shared across users; user_id="system")
    # play:   source_id = f"{play_id}:{coverage}"     (per-coverage variant)
    # share:  source_id = f"{trigger_type}:{session_id_or_milestone_key}"
    title_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=STATUS_PENDING, index=True
    )
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    spec: Mapped[dict | None] = mapped_column(
        # Use sqlalchemy.JSON for portability; sqlite stores as TEXT.
        # Imported in real file as: from sqlalchemy import JSON
        # The animation spec sent to AnimaForge — kept for retry/debug.
        Text, nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

> **Note:** `spec` should use `sqlalchemy.JSON` not `Text` — the snippet above is illustrative. Agent #1 must use proper `JSON` typing as the codebase does in `secret_weapon.py`.

**Special user_id values:**
- `"system"` — drill demos (shared across all users, not personalized).

**Migration:** Alembic file `backend/alembic/versions/XXXX_add_animaforge_jobs.py` created by Agent #1. Use `alembic revision --autogenerate -m "add animaforge jobs"`.

---

## 3. Backend service wrapper

**File:** `backend/app/services/animaforge/client.py` (owned by Agent #1).

Public class surface — agents 4, 6, 8, 9 will import and call these:

```python
class AnimaForgeService:
    @staticmethod
    async def is_available() -> bool: ...

    @staticmethod
    async def request_render(
        *,
        type: str,           # one of JOB_TYPES
        title_id: str,
        spec: dict,          # animation spec (template + style + sequence)
        user_id: str,        # or "system" for shared
        webhook_url: str | None = None,
    ) -> dict:               # returns {"job_id": str, "estimated_seconds": int}
        ...

    @staticmethod
    async def get_job_status(job_id: str) -> dict:
        # returns {"status": str, "video_url"?: str, "thumbnail_url"?: str, "progress"?: int}
        ...
```

**Implementation notes:**
- Use `httpx.AsyncClient` with timeouts (5s for `is_available`, 30s for `request_render`).
- Read `settings.animaforge_api_url` and `settings.animaforge_api_key` from `app.core.config.settings` (Agent #1 adds these fields).
- `is_available()` swallows all errors and returns `False`.
- Default `webhook_url` is `f"{settings.animaforge_webhook_base_url}/api/v1/animaforge/webhook"`.
- All other methods raise `AnimaForgeUnavailable` on network/5xx errors.

```python
class AnimaForgeUnavailable(Exception):
    """Raised when AnimaForge is unreachable or returns 5xx."""
```

---

## 4. FastAPI endpoint contract

All endpoints under prefix `/api/v1/animaforge`. Mount in `backend/app/api/v1/router.py` after the existing `_mount(...)` calls (Agent #1 adds the mount lines; the rest of the routes plug into individual modules each agent owns).

**Endpoints by owner:**

| Method | Path | Owner | Purpose |
|---|---|---|---|
| GET | `/api/v1/animaforge/status` | Agent #1 | `{available: bool}` for frontend availability check |
| GET | `/api/v1/animaforge/jobs/{job_id}` | Agent #1 | Returns row + AnimaForge live status if pending |
| GET | `/api/v1/animaforge/jobs` | Agent #1 | List authenticated user's jobs (for library page) |
| DELETE | `/api/v1/animaforge/jobs/{job_id}` | Agent #1 | Soft-delete user's job (library page) |
| POST | `/api/v1/animaforge/webhook` | Agent #2 | Webhook receiver (no auth, signature verify) |
| POST | `/api/v1/animaforge/arsenal` | Agent #4 | Render weapon diagram |
| GET | `/api/v1/animaforge/arsenal/status` | Agent #4 | Cached job for `?weapon_id=...` |
| POST | `/api/v1/animaforge/drill` | Agent #6 | Render drill demo |
| GET | `/api/v1/animaforge/drill/status` | Agent #6 | Cached job for `?title_id=&drill_type=` |
| POST | `/api/v1/animaforge/play` | Agent #8 | Render play diagram |
| GET | `/api/v1/animaforge/play/status` | Agent #8 | Cached job for `?play_id=&coverage=` |
| POST | `/api/v1/animaforge/share-win` | Agent #9 | Render share card |
| GET | `/api/v1/animaforge/pending-wins` | Agent #9 | Pending share-win triggers for current user |

**Response shapes (all JSON):**

```jsonc
// POST /animaforge/<feature> → either of:
{ "video_url": "https://...", "thumbnail_url": "https://...", "cached": true }
// or
{ "job_id": "af_abc123", "estimated_seconds": 45, "status": "pending" }

// GET /animaforge/jobs/{job_id} →
{
  "job_id": "af_abc123",
  "type": "weapon-diagram",
  "status": "complete",
  "video_url": "https://...",
  "thumbnail_url": "https://...",
  "progress": 100,
  "completed_at": "2026-05-04T12:34:56Z"
}

// GET /animaforge/status →
{ "available": true }
```

**Auth:** All endpoints except `/webhook` require the standard `Depends(get_current_user)` from `backend/app/api/v1/deps.py`. The webhook verifies an HMAC header (`X-AnimaForge-Signature`).

**Pydantic schemas:** Each agent puts request/response schemas under `backend/app/schemas/animaforge.py` (shared file — see file-ownership below for write rules).

---

## 5. Frontend AnimaPlayer component

**File:** `frontend/src/components/animaforge/AnimaPlayer.tsx` (owned by Agent #3).

```ts
export type AnimaPlayerType =
  | "weapon-diagram"
  | "drill-demo"
  | "play-diagram"
  | "share-win";

export interface AnimaPlayerProps {
  /** Job to poll. Either jobId OR videoUrl must be provided. */
  jobId?: string;
  /** Direct video URL — skips polling. */
  videoUrl?: string;
  thumbnailUrl?: string;
  type: AnimaPlayerType;
  /** Auto-play muted on mount (default: true for short diagrams) */
  autoPlay?: boolean;
  /** Loop short diagrams (default: true for diagrams, false for share-win) */
  loop?: boolean;
  /** Fired once when video is ready to play. Receives the resolved videoUrl. */
  onReady?: (videoUrl: string) => void;
  /** Fired when render fails permanently (after max retries). */
  onError?: (message: string) => void;
  /** Override polling interval ms — default 5000 */
  pollIntervalMs?: number;
}
```

**States** (per blueprint Section 1):
1. **PENDING** — spinner with "Generating animation… ~Xs". Polls `/api/v1/animaforge/jobs/{job_id}` every 5s.
2. **COMPLETE** — HTML5 `<video>` with thumbnail poster, controls, autoplay-muted, loop based on prop.
3. **FAILED** — "Animation unavailable — [Try Again]" → calls `onError` after 3 retries.
4. **UNAVAILABLE** — render `null` (parent should also gate via `useAnimaForgeAvailable()`).

**Companion files (also owned by Agent #3):**
- `frontend/src/hooks/useAnimaForge.ts` — exports `useAnimaForgeAvailable()` (cached SWR query of `/animaforge/status`) and `useAnimaForgeJob(jobId)`.
- `frontend/src/lib/animaforge/types.ts` — shared TypeScript types for all consumers (job, status, trigger types, etc.).
- `frontend/src/lib/animaforge/api.ts` — typed wrappers around `/api/v1/animaforge/*` using the existing `lib/api.ts` axios instance.

Other agents (5, 7, 8, 9, 10) **import** from these paths but **never edit** them.

---

## 6. Environment variables

Agent #1 owns the canonical addition; everyone else just reads them.

**Backend (`backend/app/core/config.py` — Agent #1 adds fields):**
```python
animaforge_api_url: str = "http://localhost:3001"
animaforge_api_key: str = ""
animaforge_webhook_secret: str = ""           # HMAC for webhook verification
animaforge_webhook_base_url: str = "http://localhost:8001"  # the URL AnimaForge calls back
animaforge_default_quality: str = "standard"  # standard|high|low
```

**Root `.env` (Agent #1 appends — do not duplicate keys):**
```
# AnimaForge integration
ANIMAFORGE_API_URL=http://localhost:3001
ANIMAFORGE_API_KEY=
ANIMAFORGE_WEBHOOK_SECRET=
ANIMAFORGE_WEBHOOK_BASE_URL=http://127.0.0.1:8001
ANIMAFORGE_DEFAULT_QUALITY=standard
```

**`.env.example` (Agent #1 mirrors with placeholders):**
```
ANIMAFORGE_API_URL=http://localhost:3001
ANIMAFORGE_API_KEY=YOUR_ANIMAFORGE_API_KEY_HERE
ANIMAFORGE_WEBHOOK_SECRET=YOUR_ANIMAFORGE_WEBHOOK_SECRET_HERE
ANIMAFORGE_WEBHOOK_BASE_URL=http://127.0.0.1:8001
ANIMAFORGE_DEFAULT_QUALITY=standard
```

**Frontend (`frontend/.env.local` — already exists; do not modify here):** none required. Frontend talks to FastAPI; no animaforge envs on the Next side.

---

## 7. File-ownership matrix

**Strict rule:** Each path is owned by one agent and only that agent writes to it. If you need a path another agent owns, **import** from it (assume the contract surface above) — do not modify.

Shared/append-only files have explicit append rules so agents don't overwrite each other.

| Path | Owner |
|---|---|
| `backend/app/models/animaforge.py` | #1 |
| `backend/app/services/animaforge/__init__.py` | #1 |
| `backend/app/services/animaforge/client.py` | #1 |
| `backend/app/services/animaforge/exceptions.py` | #1 |
| `backend/app/api/v1/endpoints/animaforge_core.py` | #1 |
| `backend/alembic/versions/<ts>_add_animaforge_jobs.py` | #1 |
| `backend/app/api/v1/endpoints/animaforge_webhook.py` | #2 |
| `backend/app/services/animaforge/notifications.py` | #2 |
| `frontend/src/components/animaforge/AnimaPlayer.tsx` | #3 |
| `frontend/src/components/animaforge/AnimaPendingState.tsx` | #3 |
| `frontend/src/components/animaforge/AnimaErrorState.tsx` | #3 |
| `frontend/src/hooks/useAnimaForge.ts` | #3 |
| `frontend/src/lib/animaforge/types.ts` | #3 |
| `frontend/src/lib/animaforge/api.ts` | #3 |
| `backend/app/api/v1/endpoints/animaforge_arsenal.py` | #4 |
| `backend/app/services/animaforge/weapon_spec.py` | #4 |
| `frontend/src/components/arsenal/WeaponDetail.tsx` | #5 (edits) |
| `frontend/src/components/arsenal/WeaponCard.tsx` | #5 (edits) |
| `backend/app/api/v1/endpoints/animaforge_drill.py` | #6 |
| `backend/app/services/animaforge/drill_spec.py` | #6 |
| `backend/scripts/pre_generate_drill_animations.py` | #6 |
| `frontend/src/components/drills/DrillRunner.tsx` | #7 (edits) |
| `frontend/src/components/drills/PostDrillDebrief.tsx` | #7 (edits) |
| `frontend/src/components/drills/DrillQueue.tsx` | #7 (edits) |
| `backend/app/api/v1/endpoints/animaforge_play.py` | #8 |
| `backend/app/services/animaforge/play_spec.py` | #8 |
| `frontend/src/components/gameplan/PlayDetail.tsx` | #8 (edits) |
| `backend/app/api/v1/endpoints/animaforge_share.py` | #9 |
| `backend/app/services/animaforge/share_spec.py` | #9 |
| `backend/app/services/animaforge/share_triggers.py` | #9 |
| `frontend/src/components/animaforge/ShareWinModal.tsx` | #9 |
| `backend/app/api/v1/endpoints/animaforge_settings.py` | #10 |
| `frontend/src/app/(dashboard)/settings/animations/page.tsx` | #10 |
| `frontend/src/components/settings/AnimaForgeSettingsPanel.tsx` | #10 |
| `frontend/src/app/admin/.../animaforge/page.tsx` | #10 (place under whatever existing admin layout uses) |

**Shared file rules (multiple agents touch — append-only):**

| Path | Rule |
|---|---|
| `backend/app/api/v1/router.py` | Append `_mount(...)` lines under a new `# AnimaForge` section. Each agent appends ONLY their own line. Owner of section header: Agent #1. |
| `backend/app/schemas/animaforge.py` | One file with all Pydantic schemas. Agents append their own block under a `# === <feature> ===` section header. Agent #1 creates the file with imports and the core schemas (Job, JobStatusResponse). |
| `backend/app/services/animaforge/__init__.py` | Re-exports. Agent #1 owns. Other agents do not touch. |
| `.env` | Agent #1 appends. No one else writes. |
| `.env.example` | Agent #1 mirrors. No one else writes. |
| `requirements.txt` | Agent #1 adds `httpx>=0.27` if not already present. Verify before adding. |
| `package.json` (frontend) | Agent #3 adds `swr` if not present. Verify before adding. No other adds. |
| `frontend/src/app/(dashboard)/layout.tsx` (or shell) | Agent #9 may add a `<ShareWinModalHost />` mount once. |
| `CHANGELOG.md` | Each agent appends one bullet under `## [Unreleased] - AnimaForge integration` (a section that Agent #1 creates). |

If two agents must touch the same line, **one of them stops and leaves a TODO comment** rather than guessing — surface it in the PR summary at handoff. This is rare given the matrix.

---

## 8. Branch & commit conventions

Per repo `CLAUDE.md`:
- Branch: `ai-feature/animaforge-<scope>` (kebab-case). Each agent creates exactly one branch.
- Commits: Conventional Commits. Examples in blueprint:
  - `feat(animaforge): add AnimaForge service wrapper, AnimaForgeJob schema, webhook handler, AnimaPlayer component`
  - `feat(arsenal): add AnimaForge animated play diagrams for all 11 titles`
  - `feat(drills): add AnimaForge drill demonstration videos`
  - etc.
- Commit early, commit often. End with one final commit per branch summarizing the slice.
- Do **not** push. Do **not** open PRs. Do **not** merge to `main`. Coordinator (the human's primary session) handles merge.

---

## 9. Title coverage (11 titles)

All spec builders must handle every title in `TITLE_IDS` (see `backend/app/models/secret_weapon.py`):
`madden-26, cfb-26, nba-2k26, eafc-26, mlb-26, warzone, fortnite, ufc-5, pga-2k25, undisputed, video-poker`.

Use the per-title style/template config from blueprint Sections 2/3/4. If a title is not in the blueprint's per-title config (e.g. `cfb-26` reuses madden), fall back gracefully (`cfb-26` → reuse `madden-26` template).

---

## 10. Acceptance criteria (verbatim from blueprint Section 7 — apply to your slice)

Every agent self-checks their slice against the relevant rows in the blueprint's "Final Verification Checklist" before declaring done.

Tests:
- Backend: `pytest backend/tests` should still pass; add at least one test per new endpoint or service module under `backend/tests/unit/test_animaforge_<scope>.py`.
- Frontend: `cd frontend && npx tsc --noEmit` (type-check) should pass; `npm run build` is a stretch goal but type-check is required.

---

## 11. Mocking AnimaForge in dev/tests

AnimaForge will not be running. Tests should monkeypatch `AnimaForgeService` to return canned responses. For dev:
- `is_available()` → returns `False` if env var unset → frontend hides UI silently → matches blueprint.
- This is **correct** behavior, not a bug.

---

## 12. Handoff format

Every agent ends with a 5-line summary on its branch (in commit message body or PR description-style text in the final response):
```
WHAT: <one-line scope>
FILES: <count> created, <count> edited
TESTS: pytest result / type-check result
RISKS: <anything the merge coordinator needs to know>
NEXT: <follow-ups or "none">
```

End of contract.
