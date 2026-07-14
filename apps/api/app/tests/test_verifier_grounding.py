import json
from pathlib import Path

from app.ai.schemas import EvidenceRef, NURTalkOutput
from app.cognition.schemas import EvidencePacket
from app.cognition.verifier import verify_talk_output


def test_verifier_fixture_matrix():
    fixture = Path(__file__).with_name("fixtures") / "verifier_cases.jsonl"
    for line in fixture.read_text().splitlines():
        case = json.loads(line)
        output = NURTalkOutput.model_validate(case["output"])
        evidence = EvidencePacket(
            retrieval=[EvidenceRef.model_validate(row) for row in case["evidence"]],
        )

        result = verify_talk_output(output, evidence, provider_available=case["provider_available"])

        assert result.verdict == case["verdict"], case["name"]
        assert "repair" in result.checks
        assert "chain_of_thought" not in json.dumps(case["output"]).lower()
