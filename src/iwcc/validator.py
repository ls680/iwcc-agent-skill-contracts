from __future__ import annotations

from .abstract import milestones
from .actions import parse_action
from .goals import parse_goal


def _location_violations(
    program: list[str], environment: str, contract: dict, initial_observation: str
) -> list[dict]:
    current = ""
    if environment == "scienceworld":
        import re

        match = re.search(r"This room is called the ([^.]+)", initial_observation, flags=re.I)
        current = match.group(1).strip().lower() if match else ""
    navigation_edges = {
        (row["source"], row["destination"]) for row in contract.get("navigation_edges", [])
    }
    held: set[str] = set()
    problems = []
    for index, action in enumerate(program):
        event = parse_action(action)
        if event.operator == "go":
            if environment == "scienceworld" and current and (current, event.subject) not in navigation_edges:
                problems.append({"index": index, "clause": "witnessed_navigation_edge", "action": action})
            current = event.subject
        elif event.operator == "acquire":
            if environment == "alfworld" and event.target and current and current != event.target:
                problems.append({"index": index, "clause": "at_source_before_acquire", "action": action})
            held.add(event.subject)
        elif event.operator in {"clean", "cool", "heat"}:
            if environment == "alfworld" and event.subject not in held:
                problems.append({"index": index, "clause": "holding_before_transform", "action": action})
            if environment == "alfworld" and event.target and current and current != event.target:
                problems.append({"index": index, "clause": "at_device_before_transform", "action": action})
        elif event.operator == "place":
            if environment == "alfworld" and event.subject not in held:
                problems.append({"index": index, "clause": "holding_before_place", "action": action})
            if environment == "alfworld" and event.target and current and current != event.target:
                problems.append({"index": index, "clause": "at_destination_before_place", "action": action})
            held.discard(event.subject)
    return problems


def validate_program(
    contract: dict,
    *,
    environment: str,
    family: str,
    objective: str,
    program: list[str],
    mode: str = "iwcc",
    initial_observation: str = "",
) -> dict:
    goal = parse_goal(family, objective)
    observed, _ = milestones(program, goal)
    sequence = [item.key() for item in observed]
    expected = contract["contracts"][f"{environment}/{family}"]
    violations = []
    for required in expected["required_milestones"]:
        if required not in sequence:
            violations.append({"index": len(program), "clause": f"missing:{required}"})
    if mode != "endpoint_only":
        positions = {item: sequence.index(item) for item in sequence}
        for left, right in expected["precedence"]:
            if left in positions and right in positions and positions[left] >= positions[right]:
                violations.append({"index": positions[right], "clause": f"order:{left}>{right}"})
    if mode == "iwcc":
        violations.extend(_location_violations(program, environment, contract, initial_observation))
    return {
        "valid": not violations,
        "violations": violations,
        "observed_milestones": sequence,
        "mode": mode,
    }
