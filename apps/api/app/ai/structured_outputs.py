from app.ai.schemas import NURTalkOutput


def talk_json_schema() -> dict:
    schema = NURTalkOutput.model_json_schema()
    _make_strict(schema)
    return {
        "type": "json_schema",
        "name": "nur_talk_output",
        "strict": True,
        "schema": schema,
    }


def _make_strict(node: dict) -> None:
    node.pop("default", None)
    if node.get("type") == "object" and "properties" in node:
        props = node["properties"]
        node["required"] = list(props)
        node["additionalProperties"] = False
        for child in props.values():
            if isinstance(child, dict):
                _make_strict(child)
    for key in ("items", "additionalProperties"):
        child = node.get(key)
        if isinstance(child, dict):
            _make_strict(child)
    for key in ("anyOf", "oneOf", "allOf"):
        for child in node.get(key, []) or []:
            if isinstance(child, dict):
                _make_strict(child)
    for child in node.get("$defs", {}).values():
        if isinstance(child, dict):
            _make_strict(child)
