from __future__ import annotations

from collections import Counter

from .actions import role_name, parse_action
from .goals import Goal
from .model import Event, Milestone


def _same(value: str, role: str) -> bool:
    left, right = role_name(value), role_name(role)
    if left.startswith("egg ") and right != "egg":
        left = left.removeprefix("egg ")
    return bool(right) and (left == right or right in left)


def expected_milestones(goal: Goal) -> list[str]:
    if goal.subject_kind in {"living", "nonliving"}:
        return ["focus_subject#1", "acquire_subject#1", "place_subject#1"]
    if goal.family == "use-thermometer":
        return [
            "acquire_tool#1",
            "focus_tool#1",
            "acquire_subject#1",
            "focus_subject#1",
            "measure_subject#1",
            "place_subject#1",
        ]
    required = [f"acquire_subject#{index}" for index in range(1, goal.required_count + 1)]
    if goal.transform and goal.transform != "illuminate":
        required.append(f"{goal.transform}_subject#1")
    if goal.transform == "illuminate":
        required.append("illuminate_subject#1")
    else:
        required.extend(f"place_subject#{index}" for index in range(1, goal.required_count + 1))
    return required


def milestones(program: list[str], goal: Goal) -> tuple[list[Milestone], list[Event]]:
    events = [parse_action(action) for action in program]
    result: list[Milestone] = []
    counts: Counter[str] = Counter()
    bound_subject = goal.subject
    for event in events:
        kind = ""
        if goal.family == "use-thermometer" and event.operator == "acquire" and _same(event.subject, "thermometer"):
            kind = "acquire_tool"
        elif goal.family == "use-thermometer" and event.operator == "focus" and _same(event.subject, "thermometer"):
            kind = "focus_tool"
        if goal.subject_kind in {"living", "nonliving"}:
            if event.operator == "focus" and "box" not in event.subject and not bound_subject:
                bound_subject = event.subject
                kind = "focus_subject"
            elif event.operator == "focus" and _same(event.subject, bound_subject):
                kind = "focus_subject"
            elif event.operator == "acquire" and _same(event.subject, bound_subject):
                kind = "acquire_subject"
            elif event.operator == "place" and _same(event.subject, bound_subject) and _same(event.target, goal.destination):
                kind = "place_subject"
            elif event.operator == "place" and not bound_subject and _same(event.target, goal.destination):
                bound_subject = event.subject
                kind = "place_subject"
        elif not kind:
            if event.operator == "acquire" and _same(event.subject, goal.subject):
                kind = "acquire_subject"
            elif event.operator in {"clean", "cool", "heat"} and event.operator == goal.transform and _same(event.subject, goal.subject):
                kind = f"{event.operator}_subject"
            elif event.operator == "focus" and _same(event.subject, goal.subject):
                kind = "focus_subject"
            elif event.operator == "measure" and _same(event.subject, goal.subject):
                kind = "measure_subject"
            elif event.operator == "place" and _same(event.subject, goal.subject) and any(
                _same(event.target, option) for option in goal.destination.split("|")
            ):
                kind = "place_subject"
            elif goal.transform == "illuminate" and event.operator == "use" and _same(event.subject, goal.destination):
                kind = "illuminate_subject"
        if kind:
            counts[kind] += 1
            result.append(Milestone(kind, counts[kind]))
    return result, events
