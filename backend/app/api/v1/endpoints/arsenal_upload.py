"""ArsenalAI upload endpoints — text / URL / document. Video is stubbed
(returns a soft error) until ffmpeg integration lands."""

from __future__ import annotations

import io
from pathlib import Path

import httpx
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.secret_weapon import SecretWeapon
from app.models.user import User
from app.schemas.secret_weapon import WeaponResponse
from app.services.arsenal_ai import (
    build_extract_system,
    call_claude,
    parse_json_object,
)

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[4] / "uploads" / "arsenal"
MAX_DOC_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_BYTES = 500 * 1024 * 1024


# ---------------------------------------------------------------------------
# Common: extract -> persist
# ---------------------------------------------------------------------------

async def _extract_and_save(
    *,
    db: AsyncSession,
    user_id: str,
    title_id: str,
    content: str,
    source_url: str | None = None,
) -> SecretWeapon:
    if not content.strip():
        raise HTTPException(status_code=422, detail="Empty content — nothing to analyze")

    system = build_extract_system(title_id)
    raw = await call_claude(
        system=system,
        user_content=content[:30_000],
        max_tokens=2000,
    )
    if not raw:
        raise HTTPException(
            status_code=503,
            detail="ArsenalAI is unavailable — ANTHROPIC_API_KEY not configured",
        )

    parsed = parse_json_object(raw)
    if not parsed:
        raise HTTPException(
            status_code=502, detail="ArsenalAI did not return valid JSON"
        )

    weapon = SecretWeapon(
        user_id=user_id,
        title_id=title_id,
        name=str(parsed.get("name", "Untitled weapon"))[:200],
        category=str(parsed.get("category", "Situational")),
        formation=parsed.get("formation"),
        play_name=parsed.get("play_name") or parsed.get("playName"),
        description=str(parsed.get("description", "")),
        instructions=list(parsed.get("instructions", []) or []),
        setup_steps=list(
            parsed.get("setup_steps", []) or parsed.get("setupSteps", []) or []
        ),
        when_to_use=str(parsed.get("when_to_use") or parsed.get("whenToUse") or ""),
        trigger_conditions=parsed.get("trigger_conditions")
        or parsed.get("triggerConditions")
        or {},
        difficulty=parsed.get("difficulty", "medium"),
        source_type="user-upload",
        source_url=source_url,
        tags=list(parsed.get("tags", []) or []),
        verified=False,
    )
    db.add(weapon)
    await db.commit()
    await db.refresh(weapon)
    return weapon


def _to_response(w: SecretWeapon) -> WeaponResponse:
    return WeaponResponse(
        id=w.id,
        user_id=w.user_id,
        title_id=w.title_id,
        name=w.name,
        category=w.category,
        sub_category=w.sub_category,
        formation=w.formation,
        play_name=w.play_name,
        description=w.description,
        instructions=w.instructions or [],
        setup_steps=w.setup_steps or [],
        when_to_use=w.when_to_use,
        trigger_conditions=w.trigger_conditions or {},
        difficulty=w.difficulty,  # type: ignore[arg-type]
        title_specific_data=w.title_specific_data or {},
        patch_version=w.patch_version,
        source_type=w.source_type,  # type: ignore[arg-type]
        source_url=w.source_url,
        video_url=w.video_url,
        thumbnail_url=w.thumbnail_url,
        tags=w.tags or [],
        verified=w.verified,
        success_rate=w.success_rate,
        times_used=w.times_used,
        community_rating=w.community_rating,
        community_votes=w.community_votes,
        saved=False,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

class TextBody(BaseModel):
    content: str
    title_id: str
    patch_version: str | None = None


@router.post("/upload/text", response_model=WeaponResponse)
async def upload_text(
    body: TextBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    weapon = await _extract_and_save(
        db=db,
        user_id=current_user.id,
        title_id=body.title_id,
        content=body.content,
    )
    return _to_response(weapon)


# ---------------------------------------------------------------------------
# URL (YouTube transcript or generic page text)
# ---------------------------------------------------------------------------

class UrlBody(BaseModel):
    url: str
    title_id: str
    patch_version: str | None = None


def _looks_like_youtube(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url


def _youtube_id(url: str) -> str | None:
    import re

    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{6,})", url)
    return m.group(1) if m else None


async def _fetch_youtube_transcript(url: str) -> str:
    """Fetch transcript via youtube-transcript-api if installed; otherwise fall
    back to fetching the page metadata."""
    vid = _youtube_id(url)
    if not vid:
        return ""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        chunks = YouTubeTranscriptApi.get_transcript(vid)
        return "\n".join(c["text"] for c in chunks if c.get("text"))
    except Exception:
        return ""


async def _fetch_url_text(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": "ArsenalAI/1.0"})
            resp.raise_for_status()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"URL fetch failed: {exc}")
    text = resp.text
    # Crude HTML stripping — keep it dependency-light.
    import re

    text = re.sub(r"<script.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:30_000]


@router.post("/upload/url", response_model=WeaponResponse)
async def upload_url(
    body: UrlBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    text = ""
    if _looks_like_youtube(body.url):
        text = await _fetch_youtube_transcript(body.url)
    if not text:
        text = await _fetch_url_text(body.url)
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract any text from the URL")

    weapon = await _extract_and_save(
        db=db,
        user_id=current_user.id,
        title_id=body.title_id,
        content=text,
        source_url=body.url,
    )
    return _to_response(weapon)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

def _read_pdf(buf: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="PDF parsing requires `pypdf` — install via `pip install pypdf`",
        )
    reader = PdfReader(io.BytesIO(buf))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _read_docx(buf: bytes) -> str:
    try:
        from docx import Document  # python-docx
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="DOCX parsing requires `python-docx` — install via `pip install python-docx`",
        )
    doc = Document(io.BytesIO(buf))
    return "\n".join(p.text for p in doc.paragraphs)


@router.post("/upload/document", response_model=WeaponResponse)
async def upload_document(
    title_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    buf = await file.read()
    if len(buf) > MAX_DOC_BYTES:
        raise HTTPException(status_code=413, detail="Document too large (>10 MB)")

    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        text = _read_pdf(buf)
    elif name.endswith((".docx",)):
        text = _read_docx(buf)
    elif name.endswith((".txt",)):
        text = buf.decode("utf-8", errors="replace")
    else:
        raise HTTPException(
            status_code=415, detail="Unsupported document type — use PDF, DOCX, or TXT"
        )

    weapon = await _extract_and_save(
        db=db,
        user_id=current_user.id,
        title_id=title_id,
        content=text,
        source_url=f"upload://{file.filename}",
    )
    return _to_response(weapon)


# ---------------------------------------------------------------------------
# Video (placeholder — vision pipeline lands later)
# ---------------------------------------------------------------------------

@router.post("/upload/video", response_model=WeaponResponse)
async def upload_video(
    title_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WeaponResponse:
    """For now: persist the video and use the filename as a hint for Claude.
    Full ffmpeg frame extraction + vision prompt is queued for a later patch."""
    buf = await file.read()
    if len(buf) > MAX_VIDEO_BYTES:
        raise HTTPException(status_code=413, detail="Video too large (>500 MB)")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    user_dir = UPLOAD_DIR / current_user.id
    user_dir.mkdir(parents=True, exist_ok=True)
    target = user_dir / f"{int(__import__('time').time())}_{file.filename}"
    target.write_bytes(buf)

    hint = (
        f"Video file uploaded: {file.filename}. Treat the filename and any "
        "embedded keywords as a hint for the play type. Generate a best-effort "
        "structured weapon based on common conventions in this title."
    )
    weapon = await _extract_and_save(
        db=db,
        user_id=current_user.id,
        title_id=title_id,
        content=hint,
        source_url=f"upload://{file.filename}",
    )
    weapon.video_url = f"file://{target}"
    await db.commit()
    await db.refresh(weapon)
    return _to_response(weapon)
