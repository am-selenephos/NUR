from collections.abc import Iterable
from typing import Any

from fastapi import Request

Label = tuple[str, str]


def record_counter(request: Request, name: str, labels: Iterable[Label] = (), amount: int = 1) -> None:
    counters = getattr(request.app.state, "domain_counters", None)
    if counters is None:
        return
    normalized = tuple(sorted((str(k), str(v)) for k, v in labels))
    counters[(name, normalized)] += amount


def format_labelset(labels: tuple[Label, ...]) -> str:
    if not labels:
        return ""
    return "{" + ",".join(f'{k}="{_escape(v)}"' for k, v in labels) + "}"


def _escape(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
