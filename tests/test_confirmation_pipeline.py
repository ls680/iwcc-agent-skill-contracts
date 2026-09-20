from scripts.generate_confirmation_specs import role_substitution
from scripts.run_confirmation_mutations import mutate


def test_role_substitution_changes_alfworld_goal_action():
    record = {
        "environment": "alfworld",
        "executed_actions": ["go to cabinet 1", "move mug 1 to cabinet 1"],
    }
    index, replacement = role_substitution(record)
    assert index == 1
    assert replacement != record["executed_actions"][index]
    assert "cabinet" not in replacement


def test_role_substitution_changes_scienceworld_box_color():
    record = {
        "environment": "scienceworld",
        "executed_actions": ["go to bedroom", "move wolf in inventory to red box"],
    }
    index, replacement = role_substitution(record)
    assert index == 1
    assert replacement.endswith("green box")


def test_all_program_mutations_are_deterministic():
    actions = ["look", "go to desk 1", "take mug 1 from desk 1", "go to cabinet 1", "move mug 1 to cabinet 1"]
    specs = [
        {"operator": "delete_action", "program_index": 2, "replacement_action": None},
        {"operator": "adjacent_order_swap", "program_index": 2, "replacement_action": None},
        {"operator": "truncate_suffix", "program_index": 2, "replacement_action": None},
        {"operator": "role_substitution", "program_index": 4, "replacement_action": "move mug 1 to drawer 1"},
    ]
    expected = [
        ["look", "go to desk 1", "go to cabinet 1", "move mug 1 to cabinet 1"],
        ["look", "go to desk 1", "go to cabinet 1", "take mug 1 from desk 1", "move mug 1 to cabinet 1"],
        ["look", "go to desk 1"],
        ["look", "go to desk 1", "take mug 1 from desk 1", "go to cabinet 1", "move mug 1 to drawer 1"],
    ]
    assert [mutate(actions, spec) for spec in specs] == expected
