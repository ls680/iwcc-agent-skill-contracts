#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import time

PROJECT = Path(__file__).resolve().parents[1]

SYSTEM = """You are a pre-execution validator for a complete executable agent skill program.
Inspect only the public task objective, initial observation, and numbered program.
Return BROKEN only when there is a clear missing objective step, wrong object or destination,
invalid ordering, or unsatisfied navigation/data dependency. Return VALID when the program is
internally sufficient for the objective. Return UNCERTAIN when the visible evidence is insufficient.
Do not assume access to a healthy reference or execution outcome.
Return one JSON object: {"verdict":"VALID|BROKEN|UNCERTAIN","violation_index":integer_or_null,"reason":"at most 20 words"}."""


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def append(path: Path, row: dict) -> None:
    with path.open("a") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prompt(row: dict) -> str:
    program = "\n".join(f"{index}: {action}" for index, action in enumerate(row["program"]))
    return (
        f"Environment: {row['environment']}\nSkill family: {row['family']}\n"
        f"Objective:\n{row['objective']}\n\nInitial observation:\n{row['initial_observation']}\n\n"
        f"Candidate program:\n{program}"
    )


def parse(text: str) -> tuple[str, int | None]:
    verdict = re.search(r'"?verdict"?\s*:\s*"?(VALID|BROKEN|UNCERTAIN)', text, re.I)
    index = re.search(r'"?violation_index"?\s*:\s*(\d+|null)', text, re.I)
    return (
        verdict.group(1).upper() if verdict else "INVALID_OUTPUT",
        int(index.group(1)) if index and index.group(1).lower() != "null" else None,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-label", required=True)
    parser.add_argument("--split", choices=("development", "confirmation"), default="development")
    arguments = parser.parse_args()
    config_path = PROJECT / "configs/models.json"
    config = json.loads(config_path.read_text())
    model_config = next(row for row in config["models"] if row["label"] == arguments.model_label)
    if arguments.split == "confirmation":
        confirmation = json.loads((PROJECT / "configs/confirmation.json").read_text())
        public_path = PROJECT / confirmation["outputs"]["candidates"] / "public_candidates.jsonl"
    else:
        public_path = PROJECT / "data/development/public_candidates.jsonl"
    candidates = rows(public_path)
    output = PROJECT / f"results/{arguments.split}/llm_judges" / arguments.model_label
    output.mkdir(parents=True, exist_ok=True)
    response_path = output / "responses.jsonl"
    run_spec = {
        "status": f"{arguments.split}_llm_program_judge",
        "split": arguments.split,
        "model": model_config,
        "seed": config["seed"],
        "maximum_generation_tokens": config["maximum_generation_tokens"],
        "public_candidates_sha256": digest(public_path),
        "system_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
        "private_labels_opened": False,
    }
    spec_path = output / "run_spec.json"
    if spec_path.exists() and json.loads(spec_path.read_text()) != run_spec:
        raise RuntimeError("judge inputs changed")
    if not spec_path.exists():
        if response_path.exists():
            raise RuntimeError("unowned cold outputs")
        spec_path.write_text(json.dumps(run_spec, indent=2) + "\n")
    completed = {row["candidate_id"] for row in rows(response_path)}

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        model_config["id"], revision=model_config["revision"], local_files_only=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_config["id"], revision=model_config["revision"], local_files_only=True,
        dtype="auto", device_map="cuda:0"
    ).eval()
    started_all = time.perf_counter()
    for row in candidates:
        if row["candidate_id"] in completed:
            continue
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt(row)}]
        try:
            rendered = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
            )
        except TypeError:
            rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(rendered, return_tensors="pt").to(model.device)
        tick = time.perf_counter()
        with torch.inference_mode():
            generated = model.generate(
                **inputs, do_sample=False, max_new_tokens=config["maximum_generation_tokens"],
                pad_token_id=tokenizer.eos_token_id
            )
        generated_ids = generated[0, inputs["input_ids"].shape[1] :]
        text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        verdict, violation_index = parse(text)
        result = {
            "candidate_id": row["candidate_id"],
            "verdict": verdict,
            "violation_index": violation_index,
            "response": text,
            "input_tokens": int(inputs["input_ids"].shape[1]),
            "output_tokens": int(generated_ids.shape[0]),
            "elapsed_seconds": time.perf_counter() - tick,
        }
        append(response_path, result)
        completed.add(row["candidate_id"])
        print(json.dumps({k: v for k, v in result.items() if k != "response"}), flush=True)
    final = rows(response_path)
    completion = {
        "status": "completed",
        "model": model_config,
        "candidates": len(final),
        "invalid_outputs": sum(row["verdict"] == "INVALID_OUTPUT" for row in final),
        "peak_cuda_memory_gib": torch.cuda.max_memory_reserved() / 1024**3,
        "elapsed_seconds_this_process": time.perf_counter() - started_all,
        "responses_sha256": digest(response_path),
    }
    (output / "completion.json").write_text(json.dumps(completion, indent=2) + "\n")
    print(json.dumps(completion, indent=2))


if __name__ == "__main__":
    main()
