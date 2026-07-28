"""Scoped, source-preserving dynamic translation API."""

import datetime as dt
import hashlib
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from app.api.deps import Identity, Scoped, require_csrf
from app.ai.errors import AIProviderError
from app.i18n.catalog import (
    QUALITY_STATES,
    SUPPORTED_LOCALES,
    locale_catalog,
    normalize_locale,
    resolve_variant,
)
from app.i18n.provider import (
    DisabledTranslationProvider,
    GLOSSARY_VERSION,
    PROTECTED_GLOSSARY_TERMS,
    TranslationProvider,
    TranslationProviderResult,
    get_translation_provider,
)
from app.models import (
    AMProject,
    AuditEvent,
    CognitiveEvent,
    CommunityComment,
    CommunityMembership,
    CommunityMessage,
    CommunityPost,
    Consultation,
    JournalEntry,
    Translation,
)
from app.models._mixins import now_utc


router = APIRouter(prefix="/translations", tags=["translations"])

TRANSLATION_SCOPES = {
    "EPHEMERAL",
    "PRIVATE_ORBIT",
    "SYSTEM_SHARED",
    "LEARNING_CANDIDATE",
    "COMMUNITY_ROOM",
}
MODERATION_CONTENT_TYPES = {
    "COMMUNITY_MESSAGE",
    "COMMUNITY_POST",
    "COMMUNITY_COMMENT",
    "MODERATION_REPORT",
}
COMMUNITY_SOURCE_TYPES = {
    "COMMUNITY_MESSAGE",
    "COMMUNITY_POST",
    "COMMUNITY_COMMENT",
}
SOURCE_OBJECTS = {
    "COGNITIVE_EVENT": (CognitiveEvent, "content_text", "PRIVATE_ORBIT"),
    "JOURNAL_ENTRY": (JournalEntry, "body", "PRIVATE_ORBIT"),
    "COMMUNITY_MESSAGE": (CommunityMessage, "body", "COMMUNITY_ROOM"),
    "COMMUNITY_POST": (CommunityPost, "body", "COMMUNITY_ROOM"),
    "COMMUNITY_COMMENT": (CommunityComment, "body", "COMMUNITY_ROOM"),
    "CONSULTATION": (Consultation, "question", "SYSTEM_SHARED"),
    "AM_PROJECT": (AMProject, "objective", "PRIVATE_ORBIT"),
}


class TranslationIn(BaseModel):
    source_text: str | None = Field(default=None, min_length=1, max_length=8000)
    source_object_type: str | None = Field(default=None, max_length=80)
    source_object_id: uuid.UUID | None = None
    source_locale: str | None = Field(default=None, max_length=16)
    source_writing_preference: str = Field(default="default", max_length=16)
    target_locale: str = Field(max_length=16)
    target_writing_preference: str = Field(default="default", max_length=16)
    content_type: str = Field(min_length=1, max_length=80)
    scope: str = Field(default="PRIVATE_ORBIT", max_length=32)
    allow_external_provider: bool = False

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "TranslationIn":
        has_text = self.source_text is not None
        has_object = self.source_object_type is not None or self.source_object_id is not None
        if has_text == has_object:
            raise ValueError("Provide bounded source_text or one source object, not both.")
        if has_object and (self.source_object_type is None or self.source_object_id is None):
            raise ValueError("source_object_type and source_object_id are required together.")
        return self


class TranslationOut(BaseModel):
    id: uuid.UUID
    source_locale: str | None
    detected_source_locale: str | None
    target_locale: str
    source_writing_preference: str
    target_writing_preference: str
    source_direction: str
    target_direction: str
    content_type: str
    scope: str
    source_object_type: str | None
    source_object_id: uuid.UUID | None
    source_link: str | None
    source_text: str
    translated_text: str | None
    status: str
    provider: str
    model: str | None
    provider_version: str | None
    cache_state: str
    quality_state: str
    translation_version: int
    moderation_context_preserved: bool
    feedback_count: int
    can_view_original: bool = True
    reason: str | None


class TranslationFeedbackIn(BaseModel):
    helpful: bool | None = None
    correction: str | None = Field(default=None, min_length=1, max_length=8000)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _has_feedback(self) -> "TranslationFeedbackIn":
        if self.helpful is None and self.correction is None and not (self.note or "").strip():
            raise ValueError("Feedback, a correction, or a note is required.")
        return self


def _out(row: Translation, *, cache_state: str) -> TranslationOut:
    return TranslationOut(
        id=row.id,
        source_locale=row.source_locale,
        detected_source_locale=row.detected_source_locale,
        target_locale=row.target_locale,
        source_writing_preference=row.source_writing_preference,
        target_writing_preference=row.target_writing_preference,
        source_direction=row.source_direction,
        target_direction=row.target_direction,
        content_type=row.content_type,
        scope=row.scope,
        source_object_type=row.source_object_type,
        source_object_id=row.source_object_id,
        source_link=row.source_ref,
        source_text=row.source_text,
        translated_text=row.translated_text,
        status=row.status,
        provider=row.provider,
        model=row.model,
        provider_version=row.provider_version,
        cache_state=cache_state,
        quality_state=row.quality_state,
        translation_version=row.translation_version,
        moderation_context_preserved=row.moderation_context_preserved,
        feedback_count=len(row.feedback or []),
        reason=row.reason,
    )


def _locale(value: str | None, *, required: bool) -> str | None:
    if value is None and not required:
        return None
    try:
        return normalize_locale(value)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


async def _source(
    db: Scoped,
    *,
    owner_user_id: uuid.UUID,
    payload: TranslationIn,
) -> tuple[str, str | None, str, str | None]:
    if payload.source_text is not None:
        source_text = payload.source_text.strip()
        if not source_text:
            raise HTTPException(422, "Translation source text cannot be blank.")
        return source_text, payload.source_locale, payload.scope.upper(), None
    object_type = (payload.source_object_type or "").upper()
    source_spec = SOURCE_OBJECTS.get(object_type)
    if source_spec is None:
        raise HTTPException(422, "Unsupported translation source object type.")
    model, text_field, scope = source_spec
    query = select(model).where(model.id == payload.source_object_id)
    if object_type not in COMMUNITY_SOURCE_TYPES:
        query = query.where(model.owner_user_id == owner_user_id)
    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Translation source not found.")
    if object_type in COMMUNITY_SOURCE_TYPES:
        membership = (await db.execute(select(CommunityMembership).where(
            CommunityMembership.room_id == row.room_id,
            CommunityMembership.user_id == owner_user_id,
        ))).scalar_one_or_none()
        if membership is None or row.status not in {"ACTIVE", "EDITED"}:
            raise HTTPException(404, "Translation source not found.")
    source_text = (getattr(row, text_field, None) or "").strip()
    if not source_text:
        raise HTTPException(409, "Translation source has no text.")
    if len(source_text) > 8000:
        raise HTTPException(413, "Translation source exceeds the 8000 character boundary.")
    source_locale = payload.source_locale or getattr(row, "language_tag", None)
    return source_text, source_locale, scope, f"{object_type}:{row.id}"


def _cache_key(
    *,
    source_hash: str,
    source_locale: str | None,
    target_locale: str,
    source_writing_preference: str,
    target_writing_preference: str,
    content_type: str,
    scope: str,
    source_ref: str | None,
    provider_version: str,
) -> str:
    canonical = json.dumps({
        "source_hash": source_hash,
        "source_locale": source_locale,
        "target_locale": target_locale,
        "source_writing_preference": source_writing_preference,
        "target_writing_preference": target_writing_preference,
        "content_type": content_type,
        "scope": scope,
        "source_ref": source_ref,
        "provider_version": provider_version,
    }, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@router.get("/catalog")
async def translation_catalog() -> dict:
    return {
        "catalog_version": "v5-35-locales-1",
        "glossary_version": GLOSSARY_VERSION,
        "protected_glossary_terms": list(PROTECTED_GLOSSARY_TERMS),
        "locale_count": len(SUPPORTED_LOCALES),
        "quality_states": sorted(QUALITY_STATES),
        "locales": locale_catalog(),
        "fallback_locale": "en",
        "quality_claim": (
            "Locale availability does not imply human review; each writing variant carries its own state."
        ),
    }


@router.post("", response_model=TranslationOut, dependencies=[Depends(require_csrf)])
async def translate(
    payload: TranslationIn,
    db: Scoped,
    identity: Identity,
    provider: TranslationProvider = Depends(get_translation_provider),
) -> TranslationOut:
    owner_user_id, _ = identity
    target_locale = _locale(payload.target_locale, required=True)
    source_text, source_locale_raw, scope, source_ref = await _source(
        db, owner_user_id=owner_user_id, payload=payload
    )
    source_locale = _locale(source_locale_raw, required=False)
    if scope not in TRANSLATION_SCOPES:
        raise HTTPException(422, "Unsupported translation privacy scope.")
    try:
        source_variant = resolve_variant(source_locale or "en", payload.source_writing_preference)
        target_variant = resolve_variant(target_locale or "en", payload.target_writing_preference)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    same_variant = (
        source_locale == target_locale
        and source_locale is not None
        and source_variant.preference == target_variant.preference
    )
    provider_version = "local-v1" if same_variant else provider.version
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    cache_key = _cache_key(
        source_hash=source_hash,
        source_locale=source_locale,
        target_locale=target_locale or "en",
        source_writing_preference=source_variant.preference,
        target_writing_preference=target_variant.preference,
        content_type=payload.content_type.upper(),
        scope=scope,
        source_ref=source_ref,
        provider_version=provider_version,
    )
    existing = (await db.execute(select(Translation).where(
        Translation.owner_user_id == owner_user_id,
        Translation.cache_key == cache_key,
    ))).scalar_one_or_none()
    if existing is not None:
        return _out(existing, cache_state="HIT")

    moderation_context = payload.content_type.upper() in MODERATION_CONTENT_TYPES
    if same_variant:
        result = TranslationProviderResult(
            available=True,
            provider="local",
            model=None,
            provider_version=provider_version,
            translated_text=source_text,
            detected_source_locale=source_locale,
            reason="Source and target locale/writing preference are the same.",
        )
    elif isinstance(provider, DisabledTranslationProvider):
        result = await provider.translate(
            source_text=source_text,
            source_locale=source_locale,
            target_locale=target_locale or "en",
            target_writing_preference=target_variant.preference,
            content_type=payload.content_type.upper(),
            preserve_moderation_context=moderation_context,
        )
    elif not payload.allow_external_provider:
        result = TranslationProviderResult(
            available=False,
            provider=provider.name,
            model=None,
            provider_version=provider_version,
            reason=(
                "External translation requires explicit owner consent; source text stayed inside NUR."
            ),
        )
    else:
        try:
            result = await provider.translate(
                source_text=source_text,
                source_locale=source_locale,
                target_locale=target_locale or "en",
                target_writing_preference=target_variant.preference,
                content_type=payload.content_type.upper(),
                preserve_moderation_context=moderation_context,
            )
        except AIProviderError as exc:
            result = TranslationProviderResult(
                available=False,
                provider=provider.name,
                model=None,
                provider_version=provider_version,
                reason=str(exc),
            )

    if result.available:
        status = "COMPLETE"
    elif isinstance(provider, DisabledTranslationProvider):
        status = "NOT_CONNECTED"
    elif not payload.allow_external_provider:
        status = "CONSENT_REQUIRED"
    else:
        status = "FAILED"
    row = Translation(
        owner_user_id=owner_user_id,
        source_hash=source_hash,
        source_locale=source_locale,
        detected_source_locale=result.detected_source_locale,
        target_locale=target_locale,
        source_writing_preference=source_variant.preference,
        target_writing_preference=target_variant.preference,
        source_direction=source_variant.direction,
        target_direction=target_variant.direction,
        content_type=payload.content_type.upper(),
        scope=scope,
        source_object_type=(payload.source_object_type or "").upper() or None,
        source_object_id=payload.source_object_id,
        source_ref=source_ref,
        source_text=source_text,
        translated_text=result.translated_text,
        status=status,
        provider=result.provider,
        model=result.model,
        provider_version=result.provider_version,
        cache_key=cache_key if result.available else None,
        quality_state=(
            "DRAFT_MACHINE_TRANSLATED"
            if result.available and result.provider not in {"local", "owner"}
            else "MISSING_REVIEW"
        ),
        moderation_context_preserved=moderation_context and result.available,
        reason=result.reason,
    )
    db.add(row)
    await db.commit()
    return _out(row, cache_state="MISS")


@router.get("", response_model=list[TranslationOut])
async def list_translations(
    db: Scoped, identity: Identity, limit: int = 50
) -> list[TranslationOut]:
    owner_user_id, _ = identity
    rows = (await db.execute(select(Translation).where(
        Translation.owner_user_id == owner_user_id,
    ).order_by(Translation.created_at.desc()).limit(min(limit, 200)))).scalars().all()
    return [_out(row, cache_state="PERSISTED") for row in rows]


@router.get("/{translation_id}", response_model=TranslationOut)
async def get_translation(
    translation_id: uuid.UUID, db: Scoped, identity: Identity
) -> TranslationOut:
    owner_user_id, _ = identity
    row = (await db.execute(select(Translation).where(
        Translation.id == translation_id,
        Translation.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Translation not found.")
    return _out(row, cache_state="PERSISTED")


@router.post(
    "/{translation_id}/feedback",
    response_model=TranslationOut,
    dependencies=[Depends(require_csrf)],
)
async def translation_feedback(
    translation_id: uuid.UUID,
    payload: TranslationFeedbackIn,
    db: Scoped,
    identity: Identity,
) -> TranslationOut:
    owner_user_id, _ = identity
    row = (await db.execute(select(Translation).where(
        Translation.id == translation_id,
        Translation.owner_user_id == owner_user_id,
    ))).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Translation not found.")
    correction = (payload.correction or "").strip() or None
    note = (payload.note or "").strip() or None
    feedback = list(row.feedback or [])
    feedback.append({
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "helpful": payload.helpful,
        "note": note,
        "correction_supplied": correction is not None,
        "previous_translation": row.translated_text if correction else None,
    })
    row.feedback = feedback[-50:]
    if correction is not None:
        row.translated_text = correction
        row.status = "COMPLETE"
        row.provider = "owner"
        row.model = None
        row.provider_version = "owner-correction-v1"
        row.quality_state = "BETA_REVIEWED"
        row.translation_version += 1
        row.reason = "Corrected explicitly by the owner; original source remains preserved."
    row.updated_at = now_utc()
    db.add(CognitiveEvent(
        owner_user_id=owner_user_id,
        event_kind="USER_CORRECTION",
        content_text=note or "Translation feedback recorded.",
        source_ref=f"translation:{row.id}",
        structured_payload={
            "translation_id": str(row.id),
            "helpful": payload.helpful,
            "correction_supplied": correction is not None,
            "translation_version": row.translation_version,
            "provenance_label": "OWNER_FEEDBACK",
        },
    ))
    db.add(AuditEvent(
        actor_user_id=owner_user_id,
        event_type="translation.feedback",
        object_type="translation",
        object_id=row.id,
        event_metadata={
            "helpful": payload.helpful,
            "correction_supplied": correction is not None,
            "translation_version": row.translation_version,
        },
    ))
    await db.commit()
    return _out(row, cache_state="UPDATED")
