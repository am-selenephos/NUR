from typing import Protocol

from app.ai.schemas import AIProviderResult, AIStreamSink, NURTalkOutput, TalkProviderRequest
from app.core.config import get_settings


class AIProvider(Protocol):
    name: str

    async def complete_private_talk(
        self,
        request: TalkProviderRequest,
        event_sink: AIStreamSink | None = None,
    ) -> AIProviderResult: ...


class DisabledAIProvider:
    name = "disabled"
    REASON = "AI provider is disabled. Configure NUR_AI_PROVIDER=openai with a server-only key to generate model output."

    async def complete_private_talk(
        self,
        request: TalkProviderRequest,  # noqa: ARG002
        event_sink: AIStreamSink | None = None,
    ) -> AIProviderResult:
        result = AIProviderResult(
            provider=self.name,
            model=None,
            available=False,
            reason=self.REASON,
            output=NURTalkOutput(
                direct_response="I can hold this in your private Talk ledger, but live AI is not enabled on this server yet.",
                observed=[],
                inferred=[],
                hypotheses=[],
                uncertainty=["No model output was generated because the AI provider is disabled."],
                next_move="Keep one concrete line in the ledger, then enable the server-only provider when you are ready.",
                memory_candidates=[],
                source_refs=[],
            ),
        )
        if event_sink is not None:
            await event_sink("provider.disabled", {"reason": self.REASON})
        return result


def get_ai_provider() -> AIProvider:
    s = get_settings()
    if s.ai_provider == "disabled":
        return DisabledAIProvider()
    from app.ai.openai_provider import OpenAITalkProvider

    return OpenAITalkProvider()
