from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import re

from .abstract import expected_milestones, milestones
from .actions import parse_action
from .goals import parse_goal


class ContractCompiler:
    def __init__(self, minimum_support: float = 0.8, minimum_order_support: float = 0.9):
        self.minimum_support = minimum_support
        self.minimum_order_support = minimum_order_support
        self._traces: dict[str, dict] = {}

    def add(self, trace: dict) -> None:
        if not trace.get("success") or trace.get("error"):
            raise ValueError("only successful, error-free traces can witness contracts")
        payload = {
            "environment": trace["environment"],
            "family": trace["family"],
            "task_id": trace["task_id"],
            "task_description": trace["task_description"],
            "executed_actions": trace["executed_actions"],
            "initial_observation": trace.get("observations", [trace.get("initial_observation", "")])[0],
        }
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        self._traces[key] = payload

    def compile(self) -> dict:
        groups: dict[tuple[str, str], list[tuple[str, dict, list[str], list[str]]]] = defaultdict(list)
        navigation_witnesses: dict[tuple[str, str], list[str]] = defaultdict(list)
        for trace_hash, trace in self._traces.items():
            goal = parse_goal(trace["family"], trace["task_description"])
            sequence, _ = milestones(trace["executed_actions"], goal)
            groups[(trace["environment"], trace["family"])].append(
                (
                    trace_hash,
                    trace,
                    [item.key() for item in sequence],
                    expected_milestones(goal),
                )
            )
            if trace["environment"] == "scienceworld":
                match = re.search(
                    r"This room is called the ([^.]+)", trace["initial_observation"], flags=re.I
                )
                current = match.group(1).strip().lower() if match else ""
                for action in trace["executed_actions"]:
                    event = parse_action(action)
                    if event.operator == "go" and current:
                        navigation_witnesses[(current, event.subject)].append(trace_hash)
                        current = event.subject
        contracts = {}
        for (environment, family), traces in sorted(groups.items()):
            total = len(traces)
            presence = Counter()
            precedence = Counter()
            witnesses: dict[str, list[str]] = defaultdict(list)
            branches = Counter()
            for trace_hash, _, sequence, expected_sequence in traces:
                branches[tuple(sequence)] += 1
                for item in set(sequence):
                    presence[item] += 1
                    witnesses[f"requires:{item}"].append(trace_hash)
                for left_index, left in enumerate(sequence):
                    for right in sequence[left_index + 1 :]:
                        if left != right:
                            precedence[(left, right)] += 1
                            witnesses[f"before:{left}>{right}"].append(trace_hash)
            required = sorted(
                item
                for item, count in presence.items()
                if count / total >= self.minimum_support
            )
            order = sorted(
                [left, right]
                for (left, right), count in precedence.items()
                if count / total >= self.minimum_order_support
                and left in required
                and right in required
                and precedence.get((right, left), 0) == 0
            )
            key = f"{environment}/{family}"
            contracts[key] = {
                "environment": environment,
                "family": family,
                "trace_count": total,
                "required_milestones": required,
                "precedence": order,
                "branches": [
                    {"sequence": list(sequence), "support": count}
                    for sequence, count in sorted(branches.items())
                ],
                "witnesses": {name: sorted(set(ids)) for name, ids in sorted(witnesses.items())},
            }
        result = {
            "method": "incremental_witnessed_contract_compilation",
            "minimum_support": self.minimum_support,
            "minimum_order_support": self.minimum_order_support,
            "trace_count": len(self._traces),
            "contracts": contracts,
            "navigation_edges": [
                {
                    "source": source,
                    "destination": destination,
                    "witnesses": sorted(set(witnesses)),
                }
                for (source, destination), witnesses in sorted(navigation_witnesses.items())
            ],
        }
        canonical = json.dumps(result, sort_keys=True, separators=(",", ":"))
        result["canonical_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
        return result
