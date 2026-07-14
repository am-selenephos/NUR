import datetime as dt
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import Identity, Scoped, require_csrf
from app.models import Orbit, Profile
from app.models._mixins import now_utc

router = APIRouter(prefix="/profile", tags=["profile"])


class PreferencesOut(BaseModel):
    timezone: str | None
    locale: str | None
    writing_preference: str
    sound_enabled: bool
    reduced_effects: bool
    default_boundary: str
    active_orbit_id: uuid.UUID | None
    omega_enabled: bool
    updated_at: dt.datetime
    model_config = {"from_attributes": True}


class PreferencesPatch(BaseModel):
    timezone: str | None = Field(default=None, max_length=64)
    locale: str | None = Field(default=None, max_length=16)
    writing_preference: str | None = Field(default=None, max_length=32)
    sound_enabled: bool | None = None
    reduced_effects: bool | None = None
    default_boundary: str | None = Field(default=None, max_length=32)
    active_orbit_id: uuid.UUID | None = None
    omega_enabled: bool | None = None


@router.get("/preferences", response_model=PreferencesOut)
async def get_preferences(db: Scoped, identity: Identity) -> PreferencesOut:
    user_id, _ = identity
    profile = (await db.execute(select(Profile).where(Profile.user_id == user_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found.")
    return PreferencesOut.model_validate(profile)


@router.patch("/preferences", response_model=PreferencesOut, dependencies=[Depends(require_csrf)])
async def patch_preferences(payload: PreferencesPatch, db: Scoped, identity: Identity) -> PreferencesOut:
    user_id, _ = identity
    profile = (await db.execute(select(Profile).where(Profile.user_id == user_id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Profile not found.")
    if "timezone" in payload.model_fields_set:
        if payload.timezone is not None:
            try:
                ZoneInfo(payload.timezone)
            except ZoneInfoNotFoundError as exc:
                raise HTTPException(422, "Unknown IANA timezone.") from exc
        profile.timezone = payload.timezone
    if payload.locale is not None:
        profile.locale = payload.locale
    if payload.writing_preference is not None:
        if payload.writing_preference not in {"default", "roman", "script"}:
            raise HTTPException(422, "writing_preference must be default, roman, or script.")
        profile.writing_preference = payload.writing_preference
    if payload.sound_enabled is not None:
        profile.sound_enabled = payload.sound_enabled
    if payload.reduced_effects is not None:
        profile.reduced_effects = payload.reduced_effects
    if payload.default_boundary is not None:
        if payload.default_boundary not in {"EPHEMERAL", "PRIVATE_ORBIT", "SYSTEM_SHARED", "LEARNING_CANDIDATE"}:
            raise HTTPException(422, "Unknown boundary.")
        profile.default_boundary = payload.default_boundary
    if "active_orbit_id" in payload.model_fields_set:
        if payload.active_orbit_id is not None:
            owned = (await db.execute(select(Orbit.id).where(
                Orbit.id == payload.active_orbit_id,
                Orbit.owner_user_id == user_id,
            ))).scalar_one_or_none()
            if owned is None:
                raise HTTPException(404, "Orbit not found.")
        profile.active_orbit_id = payload.active_orbit_id
    if payload.omega_enabled is not None:
        profile.omega_enabled = payload.omega_enabled
    profile.updated_at = now_utc()
    await db.commit()
    return PreferencesOut.model_validate(profile)
