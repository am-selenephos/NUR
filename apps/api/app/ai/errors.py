class AIProviderError(RuntimeError):
    """Base class for server-only AI provider errors."""

    code = "provider_error"
    public_message = "Live AI could not complete this request."
    http_status = 503
    retryable = False


class AIProviderDisabled(AIProviderError):
    """Raised when a caller asks for AI while the provider is disabled."""

    code = "provider_disabled"
    public_message = "Live AI is not enabled on this server."


class AIProviderMisconfigured(AIProviderError):
    """Raised when OpenAI mode is selected without a safe server config."""

    code = "provider_misconfigured"
    public_message = "Live AI is not configured correctly on this server."


class AIProviderAuthenticationError(AIProviderMisconfigured):
    """Raised when the provider rejects server-side credentials."""

    code = "provider_authentication_failed"
    public_message = "Live AI authentication failed on the server."


class AIProviderQuotaExceeded(AIProviderError):
    """Raised when provider billing or quota prevents a model run."""

    code = "provider_quota_exceeded"
    public_message = "Live AI quota is unavailable for this server."


class AIProviderRateLimited(AIProviderError):
    """Raised after the bounded retry for a provider rate limit fails."""

    code = "provider_rate_limited"
    public_message = "Live AI is temporarily rate limited."
    http_status = 429
    retryable = True


class AIProviderTimeout(AIProviderError):
    """Raised after the bounded retry for a provider timeout fails."""

    code = "provider_timeout"
    public_message = "Live AI timed out before a verified response was available."
    http_status = 504
    retryable = True


class AIProviderUnavailable(AIProviderError):
    """Raised for transient provider/network/server failures."""

    code = "provider_unavailable"
    public_message = "Live AI is temporarily unavailable."
    retryable = True


class AIProviderUnsupportedModel(AIProviderMisconfigured):
    """Raised when the configured model is unavailable to the project."""

    code = "provider_model_unsupported"
    public_message = "The configured Live AI model is unavailable."


class AIOutputValidationError(AIProviderError):
    """Raised when a provider response does not satisfy NUR's schema."""

    code = "provider_output_invalid"
    public_message = "Live AI returned an unverifiable response."
    http_status = 502


class AIRequestBudgetExceeded(AIProviderError):
    """Raised before a provider call when the owner budget is exhausted."""

    code = "ai_budget_exceeded"
    public_message = "The daily Live AI request limit has been reached."
    http_status = 429
