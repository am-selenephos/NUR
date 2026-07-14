import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import Identity, Scoped, require_csrf
from app.core.config import get_settings
from app.models import Translation


router = APIRouter(prefix="/translations", tags=["translations"])

SUPPORTED_LOCALES = {
    "en", "ur", "hi", "bn", "pa", "ar", "fa", "tr", "id", "ms",
    "zh-Hans", "zh-Hant", "ja", "ko", "vi", "th", "fil", "ta", "te",
    "mr", "gu", "kn", "ml", "ru", "uk", "pl", "de", "fr", "es", "pt",
    "it", "nl", "sv", "ro", "sw",
}


class TranslationIn(BaseModel):
    source_text: str = Field(min_length=1, max_length=8000)
    source_locale: str | None = Field(default=None, max_length=16)
    target_locale: str = Field(max_length=16)
    content_type: str = Field(min_length=1, max_length=80)


class TranslationOut(BaseModel):
    id: uuid.UUID
    source_locale: str | None
    target_locale: str
    content_type: str
    translated_text: str | None
    status: str
    provider: str
    model: str | None
    reason: str | None
    model_config = {"from_attributes": True}


def _validate_locale(value: str | None, *, required: bool) -> None:
    if value is None and not required:
        return
    if value not in SUPPORTED_LOCALES:
        raise HTTPException(422, "Unsupported NUR locale.")


@router.post("", response_model=TranslationOut, dependencies=[Depends(require_csrf)])
async def translate(payload: TranslationIn, db: Scoped, identity: Identity) -> TranslationOut:
    owner_user_id, _ = identity
    _validate_locale(payload.source_locale, required=False)
    _validate_locale(payload.target_locale, required=True)
    source_hash = hashlib.sha256(payload.source_text.encode("utf-8")).hexdigest()
    existing = (await db.execute(select(Translation).where(
        Translation.owner_user_id == owner_user_id,
        Translation.source_hash == source_hash,
        Translation.source_locale == payload.source_locale,
        Translation.target_locale == payload.target_locale,
        Translation.content_type == payload.content_type,
    ).order_by(Translation.created_at.desc()).limit(1))).scalar_one_or_none()
    if existing is not None:
        return TranslationOut.model_validate(existing)

    settings = get_settings()
    if payload.source_locale == payload.target_locale:
        row = Translation(
            owner_user_id=owner_user_id,
            source_hash=source_hash,
            source_locale=payload.source_locale,
            target_locale=payload.target_locale,
            content_type=payload.content_type,
            source_text=payload.source_text,
            translated_text=payload.source_text,
            status="COMPLETE",
            provider="local",
            reason="Source and target locale are the same.",
        )
    else:
        row = Translation(
            owner_user_id=owner_user_id,
            source_hash=source_hash,
            source_locale=payload.source_locale,
            target_locale=payload.target_locale,
            content_type=payload.content_type,
            source_text=payload.source_text,
            translated_text=None,
            status="NOT_CONNECTED",
            provider=settings.ai_provider,
            model=settings.openai_model or None,
            reason="Dynamic translation provider is not connected in this runtime mode.",
        )
    db.add(row)
    await db.commit()
    return TranslationOut.model_validate(row)


@router.get("", response_model=list[TranslationOut])
async def list_translations(db: Scoped, identity: Identity, limit: int = 50) -> list[TranslationOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(Translation).where(
        Translation.owner_user_id == owner_user_id,
    ).order_by(Translation.created_at.desc()).limit(min(limit, 200)))).scalars().all()
    return [TranslationOut.model_validate(row) for row in rows]
