import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    chosen_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    consent: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class ProfileOut(BaseModel):
    chosen_name: str
    timezone: str | None = None
    locale: str | None = None
    writing_preference: str = "default"
    sound_enabled: bool
    reduced_effects: bool


class OrbitOut(BaseModel):
    title: str = "Personal Orbit"
    kind: str = "PERSONAL_BRIDGE"
    status: str = "ACTIVE"
    id: uuid.UUID
    current_arrival_state: str | None = None
    active_focus_area: str | None = None


class MeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    email_verified: bool
    profile: ProfileOut
    orbit: OrbitOut


class ErrorResponse(BaseModel):
    detail: str
