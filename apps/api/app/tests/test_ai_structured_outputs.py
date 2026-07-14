from app.ai.structured_outputs import talk_json_schema


def test_talk_schema_is_openai_strict():
    wrapper = talk_json_schema()
    schema = wrapper["schema"]
    props = schema["properties"]
    assert wrapper["strict"] is True
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(props)
    assert "default" not in schema["properties"]["next_move"]
