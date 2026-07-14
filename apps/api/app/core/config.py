from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_MARKERS = ("change_me", "dev_only")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.local"), extra="ignore")

    app_env: str = "development"
    web_origin: str = "http://localhost:5173"
    web_extra_origins: str = Field(default="", validation_alias="WEB_EXTRA_ORIGINS")
    api_origin: str = "http://localhost:8000"

    database_url: str = "postgresql+asyncpg://nur_app:change_me@localhost:5432/nur"
    alembic_database_url: str | None = None  # schema-owner role; migrations only
    redis_url: str = "redis://localhost:6379/0"

    session_secret: str = "dev_only_change_me"
    csrf_secret: str = "dev_only_change_me"

    session_cookie_name: str = "nur_session"
    csrf_cookie_name: str = "nur_csrf"
    session_ttl_seconds: int = 60 * 60 * 24 * 14  # 14 days

    login_rate_limit_max: int = 10
    login_rate_limit_window_seconds: int = 300
    register_rate_limit_max: int = 10
    register_rate_limit_window_seconds: int = 300

    # AI gateway: server-side only. Keys never cross to the web client.
    ai_provider: str = Field(default="disabled", validation_alias=AliasChoices("NUR_AI_PROVIDER", "AI_PROVIDER"))
    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="", validation_alias=AliasChoices("NUR_OPENAI_MODEL", "OPENAI_MODEL"))
    openai_embedding_model: str = Field(default="", validation_alias=AliasChoices("NUR_OPENAI_EMBEDDING_MODEL", "OPENAI_EMBEDDING_MODEL"))
    openai_reasoning_effort: str = Field(default="high", validation_alias="NUR_OPENAI_REASONING_EFFORT")
    openai_critical_reasoning_effort: str = Field(default="high", validation_alias="NUR_OPENAI_CRITICAL_REASONING_EFFORT")
    openai_request_timeout_seconds: int = Field(default=45, validation_alias="NUR_OPENAI_REQUEST_TIMEOUT_SECONDS")
    ai_per_user_daily_limit: int = Field(default=50, validation_alias="NUR_AI_PER_USER_DAILY_LIMIT")
    ai_daily_budget_cents: int = Field(default=500, validation_alias="NUR_AI_DAILY_BUDGET_CENTS")
    ai_allow_external_web_research: bool = Field(default=False, validation_alias="NUR_AI_ALLOW_EXTERNAL_WEB_RESEARCH")
    ai_log_prompts: bool = Field(default=False, validation_alias="NUR_AI_LOG_PROMPTS")
    demo_mode: bool = Field(default=False, validation_alias="DEMO_MODE")

    # Omega research layer: owner-only, disabled for public UI unless the web
    # bundle flag is also enabled. The scheduler carries owner IDs only.
    omega_enabled: bool = Field(default=True, validation_alias="NUR_OMEGA_ENABLED")
    omega_scheduled_consolidation: bool = Field(default=True, validation_alias="NUR_OMEGA_SCHEDULED_CONSOLIDATION")
    omega_consolidation_interval_hours: int = Field(default=24, validation_alias="NUR_OMEGA_CONSOLIDATION_INTERVAL_HOURS")
    omega_max_experiences_per_run: int = Field(default=100, validation_alias="NUR_OMEGA_MAX_EXPERIENCES_PER_RUN")

    @field_validator("ai_provider")
    @classmethod
    def _known_provider(cls, value: str) -> str:
        v = value.lower().strip()
        if v not in {"disabled", "openai"}:
            raise ValueError("NUR_AI_PROVIDER must be 'disabled' or 'openai'.")
        return v

    @model_validator(mode="after")
    def _no_decorative_secrets_in_production(self) -> "Settings":
        """SESSION_SECRET keys session-token HMACs; CSRF_SECRET keys CSRF tokens.
        They are load-bearing, so production refuses placeholders outright."""
        if self.app_env == "production":
            for name in ("session_secret", "csrf_secret"):
                value = getattr(self, name)
                if len(value) < 32 or any(m in value for m in _PLACEHOLDER_MARKERS):
                    raise ValueError(
                        f"{name.upper()} must be a real secret (>=32 chars, no placeholder text) "
                        "when APP_ENV=production."
                    )
        if self.ai_provider == "openai":
            if self.openai_api_key is None or not self.openai_api_key.get_secret_value().strip():
                raise ValueError("NUR_AI_PROVIDER=openai requires OPENAI_API_KEY in the server environment.")
            if not self.openai_model.strip():
                raise ValueError("NUR_AI_PROVIDER=openai requires NUR_OPENAI_MODEL in the server environment.")
        if self.ai_allow_external_web_research:
            raise ValueError("NUR_AI_ALLOW_EXTERNAL_WEB_RESEARCH must remain false for this readiness gate.")
        return self

    @property
    def cookies_secure(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        origins = {self.web_origin.rstrip("/")}
        for value in self.web_extra_origins.split(","):
            origin = value.strip().rstrip("/")
            if origin:
                origins.add(origin)
        if self.app_env != "production":
            origins.update({"http://localhost:4173", "http://127.0.0.1:4173"})
        return sorted(origins)


@lru_cache
def get_settings() -> Settings:
    return Settings()
