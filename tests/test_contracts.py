from iwcc.compiler import ContractCompiler
from iwcc.goals import parse_goal
from iwcc.validator import validate_program


def trace(task_id: str, actions: list[str]) -> dict:
    return {
        "environment": "alfworld",
        "family": "pick_clean_then_place_in_recep",
        "task_id": task_id,
        "task_description": "Your task is to: put a clean mug in cabinet.",
        "executed_actions": actions,
        "success": True,
        "error": None,
    }


HEALTHY = [
    "go to counter 1",
    "take mug 1 from counter 1",
    "go to sinkbasin 1",
    "clean mug 1 with sinkbasin 1",
    "go to cabinet 1",
    "move mug 1 to cabinet 1",
]


def compiled() -> dict:
    compiler = ContractCompiler()
    compiler.add(trace("a", HEALTHY))
    compiler.add(trace("b", ["look", *HEALTHY]))
    return compiler.compile()


def test_goal_parser_handles_transform_variant():
    goal = parse_goal(
        "pick_clean_then_place_in_recep",
        "Your task is to: clean some bowl and put it in cabinet.",
    )
    assert (goal.subject, goal.destination, goal.transform) == ("bowl", "cabinet", "clean")


def test_incremental_contract_is_order_invariant():
    first = ContractCompiler()
    second = ContractCompiler()
    for item in [trace("a", HEALTHY), trace("b", ["look", *HEALTHY])]:
        first.add(item)
    for item in [trace("b", ["look", *HEALTHY]), trace("a", HEALTHY)]:
        second.add(item)
    assert first.compile() == second.compile()


def test_healthy_program_has_witnessed_contract():
    result = validate_program(
        compiled(),
        environment="alfworld",
        family="pick_clean_then_place_in_recep",
        objective="Your task is to: put a clean mug in cabinet.",
        program=HEALTHY,
    )
    assert result["valid"]


def test_missing_acquisition_is_rejected():
    candidate = [action for action in HEALTHY if not action.startswith("take mug")]
    result = validate_program(
        compiled(),
        environment="alfworld",
        family="pick_clean_then_place_in_recep",
        objective="Your task is to: put a clean mug in cabinet.",
        program=candidate,
    )
    assert not result["valid"]
    assert any(row["clause"] == "holding_before_transform" for row in result["violations"])


def test_wrong_navigation_is_rejected_by_dataflow_not_endpoint_only():
    candidate = HEALTHY.copy()
    candidate[4] = "go to drawer 1"
    endpoint = validate_program(
        compiled(), environment="alfworld", family="pick_clean_then_place_in_recep",
        objective="Your task is to: put a clean mug in cabinet.", program=candidate,
        mode="endpoint_only",
    )
    witnessed = validate_program(
        compiled(), environment="alfworld", family="pick_clean_then_place_in_recep",
        objective="Your task is to: put a clean mug in cabinet.", program=candidate,
    )
    assert endpoint["valid"] and not witnessed["valid"]


def test_scienceworld_navigation_uses_trace_witnesses():
    compiler = ContractCompiler()
    compiler.add(
        {
            "environment": "scienceworld",
            "family": "find-living-thing",
            "task_id": "sw-a",
            "task_description": "Your task is to find a(n) living thing. First, focus on the thing. Then, move it to the red box in the bedroom.",
            "executed_actions": [
                "open door to hallway", "go to hallway", "open door to bedroom", "go to bedroom",
                "focus on wolf", "pick up wolf", "move wolf to red box",
            ],
            "observations": ["This room is called the kitchen."],
            "success": True,
            "error": None,
        }
    )
    contract = compiler.compile()
    broken = [
        "open door to hallway", "open door to bedroom", "go to bedroom",
        "focus on wolf", "pick up wolf", "move wolf to red box",
    ]
    result = validate_program(
        contract,
        environment="scienceworld",
        family="find-living-thing",
        objective="Your task is to find a(n) living thing. First, focus on the thing. Then, move it to the red box in the bedroom.",
        program=broken,
        initial_observation="This room is called the kitchen.",
    )
    assert not result["valid"]
    assert any(row["clause"] == "witnessed_navigation_edge" for row in result["violations"])
