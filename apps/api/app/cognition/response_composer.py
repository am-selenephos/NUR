from app.ai.schemas import NURTalkOutput


def compose_disabled_output(reason: str) -> NURTalkOutput:
    return NURTalkOutput(
        direct_response="I saved this turn, but live AI is disabled on this server.",
        observed=[],
        inferred=[],
        hypotheses=[],
        uncertainty=[reason],
        next_move="Keep one concrete next line, or enable the server-only AI provider locally.",
        memory_candidates=[],
        source_refs=[],
    )
