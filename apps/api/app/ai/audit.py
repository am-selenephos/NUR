from app.ai.redaction import redact_for_audit


def model_run_metadata(*, provider: str, model: str | None, mode: str, locale: str, prompt_logging: bool) -> dict:
    return {
        "provider": provider,
        "model": model,
        "mode": mode,
        "locale": locale,
        "prompt_logged": bool(prompt_logging),
    }


def safe_error_metadata(exc: Exception) -> dict:
    return {"error": exc.__class__.__name__, "detail": redact_for_audit(str(exc))[:500]}
