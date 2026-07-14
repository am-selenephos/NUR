"""Legacy cognitive-cycle gateway.

The Talk path now uses app.ai.provider directly and persists a model_run. This
gateway remains only for the older `/cognition/events` cycle route; it reports
the currently configured provider honestly and never fabricates proposals.
"""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class GatewayResult:
    available: bool
    reason: str
    proposals: list[dict] = field(default_factory=list)


class CognitionModelGateway(Protocol):
    name: str

    async def generate_hypotheses(
        self, *, question: str, context_snippets: list[dict]
    ) -> GatewayResult: ...

    async def summarize(self, *, text: str, purpose: str) -> GatewayResult: ...


class ProviderStatusGateway:
    """Status-only gateway for the legacy cycle route."""

    @property
    def name(self) -> str:
        from app.ai.provider import get_ai_provider

        return get_ai_provider().name

    async def generate_hypotheses(self, *, question: str, context_snippets: list[dict]) -> GatewayResult:  # noqa: ARG002
        from app.ai.provider import DisabledAIProvider, get_ai_provider

        provider = get_ai_provider()
        if isinstance(provider, DisabledAIProvider):
            return GatewayResult(available=False, reason=provider.REASON)
        return GatewayResult(
            available=False,
            reason="Legacy hypothesis generation is not wired; use /api/v1/cognition/talk for model output.",
        )

    async def summarize(self, *, text: str, purpose: str) -> GatewayResult:  # noqa: ARG002
        return await self.generate_hypotheses(question=text, context_snippets=[])


_gateway: CognitionModelGateway = ProviderStatusGateway()


def get_gateway() -> CognitionModelGateway:
    return _gateway
