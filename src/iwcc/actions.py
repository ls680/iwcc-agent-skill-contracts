from __future__ import annotations

import re

from .model import Event


def norm(value: str) -> str:
    value = re.sub(r"\s+", " ", value.lower().strip().rstrip("."))
    value = re.sub(r"^(?:the|a|an|some) ", "", value)
    value = re.sub(r"\s+in inventory$", "", value)
    return value


def role_name(value: str) -> str:
    """Drop simulator instance suffixes while retaining them in state fluents."""
    return re.sub(r"\s+\d+$", "", norm(value))


def parse_action(action: str) -> Event:
    text = re.sub(r"\s+", " ", action.lower().strip())
    patterns = (
        (r"go to (.+)", "go"),
        (r"teleport to (.+)", "go"),
        (r"open (.+)", "open"),
        (r"close (.+)", "close"),
        (r"take (.+) from (.+)", "acquire"),
        (r"pick up (.+)", "acquire"),
        (r"move (.+?) (?:to|into) (.+)", "place"),
        (r"clean (.+) with (.+)", "clean"),
        (r"cool (.+) with (.+)", "cool"),
        (r"heat (.+) with (.+)", "heat"),
        (r"focus on (.+)", "focus"),
        (r"use thermometer(?: in inventory)? on (.+)", "measure"),
        (r"use (.+)", "use"),
    )
    for pattern, operator in patterns:
        match = re.fullmatch(pattern, text)
        if match:
            parts = [norm(value) for value in match.groups()]
            return Event(operator, parts[0], parts[1] if len(parts) > 1 else "")
    return Event("other", norm(text), "")
