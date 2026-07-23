from app.ai.errors import AIProviderError
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
    if isinstance(exc, AIProviderError):
        return {
            "error": exc.__class__.__name__,
            "code": exc.code,
            "public_message": exc.public_message,
            "http_status": exc.http_status,
            "retryable": exc.retryable,
        }
    return {
        "error": exc.__class__.__name__,
        "code": "provider_error",
        "public_message": "Live AI could not complete this request.",
        "http_status": 503,
        "retryable": False,
        "detail": redact_for_audit(str(exc))[:500],
    }
