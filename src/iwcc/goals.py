from __future__ import annotations

from dataclasses import dataclass
import re

from .actions import norm


@dataclass(frozen=True)
class Goal:
    family: str
    subject: str
    destination: str
    transform: str = ""
    subject_kind: str = "named"
    required_count: int = 1
    destination_location: str = ""


def _match(pattern: str, text: str) -> tuple[str, ...] | None:
    found = re.search(pattern, text, flags=re.I)
    return tuple(norm(value) if value is not None else "" for value in found.groups()) if found else None


def parse_goal(family: str, objective: str) -> Goal:
    text = re.sub(r"\s+", " ", objective.strip())
    if family == "look_at_obj_in_light":
        values = _match(r"(?:look at|examine) (.+?) (?:under|with) the (.+?)[.]?$", text)
        if not values:
            raise ValueError(f"unsupported look objective: {objective}")
        return Goal(family, values[0], values[1], "illuminate")
    if family == "pick_and_place_simple":
        values = _match(r"put (?:a |some )?(.+?) (?:in|on) (.+?)[.]?$", text)
        if not values:
            raise ValueError(f"unsupported place objective: {objective}")
        return Goal(family, values[0], values[1])
    if family.startswith("pick_") and "then_place" in family:
        transform = {"pick_clean": "clean", "pick_cool": "cool", "pick_heat": "heat"}
        kind = next(value for prefix, value in transform.items() if family.startswith(prefix))
        values = _match(
            rf"(?:{kind} (?:some )?(.+?) and put it|put a (?:clean|cool|hot) (.+?)) (?:in|on) (.+?)[.]?$",
            text,
        )
        if not values:
            raise ValueError(f"unsupported transform objective: {objective}")
        subject = values[0] or values[1]
        return Goal(family, subject, values[2], kind)
    if family == "pick_two_obj_and_place":
        values = _match(r"put two (.+?) (?:in|on) (.+?)[.]?$", text)
        if not values:
            raise ValueError(f"unsupported two-object objective: {objective}")
        return Goal(family, values[0], values[1], required_count=2)
    if family in {"find-living-thing", "find-non-living-thing"}:
        values = _match(r"move it to the (.+?) box in the (.+?)[.]?$", text)
        if not values:
            raise ValueError(f"unsupported find objective: {objective}")
        category = "living" if family == "find-living-thing" else "nonliving"
        return Goal(
            family,
            "",
            f"{values[0]} box",
            subject_kind=category,
            destination_location=values[1],
        )
    if family == "use-thermometer":
        values = _match(r"measure the temperature of (.+?), which", text)
        if not values:
            raise ValueError(f"unsupported thermometer objective: {objective}")
        destinations = re.findall(r"place it in the (.+?) box", text, flags=re.I)
        location = _match(r"boxes are located around the (.+?)[.]?$", text)
        return Goal(
            family,
            values[0],
            "|".join(f"{norm(v)} box" for v in destinations),
            "measure",
            destination_location=location[0] if location else "",
        )
    raise ValueError(f"unsupported family: {family}")
