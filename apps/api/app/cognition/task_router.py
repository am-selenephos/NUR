from app.cognition.schemas import TaskMode


def route_task(raw: str, requested: str | None = None) -> TaskMode:
    if requested:
        try:
            return TaskMode(requested)
        except ValueError:
            return TaskMode.TALK
    lowered = raw.lower()
    if any(token in lowered for token in ("challenge me", "push back", "don't soothe")):
        return TaskMode.CHALLENGE
    if any(token in lowered for token in ("summarize", "summary")):
        return TaskMode.SUMMARIZE
    if any(token in lowered for token in ("reflect", "why am i", "what pattern")):
        return TaskMode.REFLECT
    return TaskMode.TALK
