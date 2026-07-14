class AIProviderError(RuntimeError):
    """Base class for server-only AI provider errors."""


class AIProviderDisabled(AIProviderError):
    """Raised when a caller asks for AI while the provider is disabled."""


class AIProviderMisconfigured(AIProviderError):
    """Raised when OpenAI mode is selected without a safe server config."""


class AIOutputValidationError(AIProviderError):
    """Raised when a provider response does not satisfy NUR's schema."""
