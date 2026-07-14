import asyncio
import json
from types import SimpleNamespace

import pytest

from app.ai.errors import AIOutputValidationError, AIProviderError, AIProviderMisconfigured
from app.ai.openai_provider import OpenAITalkProvider
from app.ai.schemas import TalkProviderRequest


def _valid_payload() -> str:
    return json.dumps({
        "direct_response": "Held.",
        "observed": [],
        "inferred": [],
        "hypotheses": [],
        "uncertainty": [],
        "next_move": "Write one next line.",
        "memory_candidates": [],
        "source_refs": [],
    })


class FakeStatus(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class FakeResponses:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    async def create(self, **_payload):
        self.calls += 1
        item = self.outcomes.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _provider(outcomes) -> tuple[OpenAITalkProvider, FakeResponses]:
    provider = object.__new__(OpenAITalkProvider)
    provider._settings = SimpleNamespace(openai_model="gpt-readiness", openai_reasoning_effort="high")
    responses = FakeResponses(outcomes)
    provider._client = SimpleNamespace(responses=responses)
    return provider, responses


def _request() -> TalkProviderRequest:
    return TalkProviderRequest(user_line="hold this", locale="en", mode="talk")


@pytest.mark.parametrize("failure", [FakeStatus(429), asyncio.TimeoutError("slow")], ids=["rate_limit_429", "timeout"])
async def test_openai_provider_retries_transient_failure_once(failure):
    response = SimpleNamespace(output_text=_valid_payload(), usage=None, id="resp-ok")
    provider, responses = _provider([failure, response])

    result = await provider.complete_private_talk(_request())

    assert responses.calls == 2
    assert result.available is True
    assert result.raw_response_id == "resp-ok"


async def test_openai_provider_does_not_retry_auth_failures():
    provider, responses = _provider([FakeStatus(401)])

    with pytest.raises(AIProviderMisconfigured):
        await provider.complete_private_talk(_request())

    assert responses.calls == 1


async def test_openai_provider_retries_at_most_once():
    provider, responses = _provider([FakeStatus(503), FakeStatus(503)])

    with pytest.raises(AIProviderError):
        await provider.complete_private_talk(_request())

    assert responses.calls == 2


async def test_openai_provider_rejects_malformed_output_without_retry():
    response = SimpleNamespace(output_text="{not-json", usage=None, id="bad")
    provider, responses = _provider([response])

    with pytest.raises(AIOutputValidationError):
        await provider.complete_private_talk(_request())

    assert responses.calls == 1
