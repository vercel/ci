#!/usr/bin/env python3

import argparse
import concurrent.futures
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
from typing import Any


EVALS_DIR = pathlib.Path(__file__).resolve().parent
SKILL_DIR = EVALS_DIR.parent
DEFAULT_MODELS = [
    "gpt-5.6-sol-medium",
    "claude-sonnet-5-5-high",
    "gemini-4-argon-medium",
]

PROMPT = """Use the vercel-ci-setup skill installed in this workspace.

This is an offline, read-only evaluation of task discovery and selection only.
Do not fetch current documentation, install dependencies, run Turborepo, edit
files, or call git, GitHub, or Vercel. Assume the team, private GitHub link,
remote identity, authentication, clean checkout, and current CI enablement have
already been verified. Evaluate the repository-structure preconditions that
can be determined from local files. Use 2.11.7 as the pinned minimum supported
Turborepo version.

Return exactly one JSON object between the markers below and no other text:

BEGIN_EVAL_JSON
{
  "outcome": "ready or stop",
  "stopReason": "unsupported_repository, no_safe_tasks, or null",
  "packageManager": "pnpm, npm, yarn, bun, or null",
  "turboVersion": "the declared dependency specifier or null",
  "requiresUpgrade": true,
  "selections": [
    {
      "configPath": "path to turbo.json or turbo.jsonc",
      "taskName": "full task name",
      "packageCount": 1,
      "reason": "concise evidence-based reason",
      "environmentRequirements": "concise evidence or uncertainty"
    }
  ]
}
END_EVAL_JSON

Set requiresUpgrade to null when there is no declared Turborepo dependency.
Select no more than five tasks. A task is identified by both configPath and
taskName.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Vercel CI setup skill against fixture repositories."
    )
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="Comma-separated Cursor model IDs.",
    )
    parser.add_argument(
        "--cases",
        help="Comma-separated case IDs. Runs every case when omitted.",
    )
    parser.add_argument("--runs", type=int, default=1, help="Runs per model and case.")
    parser.add_argument("--jobs", type=int, default=1, help="Concurrent agent runs.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout for each agent run in seconds.",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        help="Result directory. Defaults to .git/vercel-ci-evals/<timestamp>.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and list the matrix without invoking models.",
    )
    return parser.parse_args()


def load_cases(selected_ids: set[str] | None) -> list[dict[str, Any]]:
    cases = json.loads((EVALS_DIR / "cases.json").read_text())
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Case IDs must be unique")

    if selected_ids is None:
        return cases

    unknown = selected_ids.difference(ids)
    if unknown:
        raise ValueError(f"Unknown case IDs: {', '.join(sorted(unknown))}")
    return [case for case in cases if case["id"] in selected_ids]


def validate_case(case: dict[str, Any]) -> None:
    required = {"id", "description", "files", "expected"}
    missing = required.difference(case)
    if missing:
        raise ValueError(f"{case.get('id', '<unknown>')} is missing {sorted(missing)}")

    for relative_path in case["files"]:
        path = pathlib.PurePosixPath(relative_path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"{case['id']} has unsafe fixture path {relative_path}")

    expected = case["expected"]
    if len(expected["selections"]) > 5:
        raise ValueError(f"{case['id']} expects more than five selections")


def initialize_workspace(case: dict[str, Any], root: pathlib.Path) -> None:
    for relative_path, contents in case["files"].items():
        destination = root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents)

    skill_destination = root / ".cursor" / "skills" / "vercel-ci-setup"
    shutil.copytree(
        SKILL_DIR,
        skill_destination,
        ignore=shutil.ignore_patterns("evals"),
    )

    git_commands = [
        ["git", "init", "-b", "main"],
        ["git", "config", "user.name", "Vercel CI Eval"],
        ["git", "config", "user.email", "ci-eval@example.com"],
        ["git", "add", "."],
        ["git", "commit", "-m", "fixture"],
        [
            "git",
            "remote",
            "add",
            "origin",
            f"https://github.com/acme/{case['id']}.git",
        ],
    ]
    for command in git_commands:
        subprocess.run(
            command,
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )


def extract_payload(output: str) -> dict[str, Any]:
    start_marker = "BEGIN_EVAL_JSON"
    end_marker = "END_EVAL_JSON"
    start = output.rfind(start_marker)
    end = output.find(end_marker, start + len(start_marker))
    if start == -1 or end == -1:
        raise ValueError("Response did not contain eval JSON markers")

    payload = output[start + len(start_marker) : end].strip()
    return json.loads(payload)


def normalize_selections(selections: Any) -> set[tuple[str, str]]:
    if not isinstance(selections, list):
        return set()

    normalized = set()
    for selection in selections:
        if not isinstance(selection, dict):
            continue
        config_path = selection.get("configPath")
        task_name = selection.get("taskName")
        if isinstance(config_path, str) and isinstance(task_name, str):
            normalized.add((config_path, task_name))
    return normalized


def grade(case: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    actual_selections = normalize_selections(payload.get("selections"))
    expected_selections = {tuple(item) for item in expected["selections"]}
    forbidden = {tuple(item) for item in expected["forbiddenSelections"]}

    checks = {
        "outcome": payload.get("outcome") == expected["outcome"],
        "stopReason": payload.get("stopReason") == expected["stopReason"],
        "packageManager": payload.get("packageManager") == expected["packageManager"],
        "turboVersion": payload.get("turboVersion") == expected["turboVersion"],
        "requiresUpgrade": payload.get("requiresUpgrade")
        == expected["requiresUpgrade"],
        "selectionLimit": len(actual_selections) <= 5,
        "forbiddenSelections": not actual_selections.intersection(forbidden),
    }

    if expected_selections or actual_selections:
        true_positives = len(actual_selections.intersection(expected_selections))
        precision = true_positives / len(actual_selections) if actual_selections else 0
        recall = true_positives / len(expected_selections) if expected_selections else 0
        selection_score = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0
        )
    else:
        selection_score = 1

    score = (
        20 * checks["outcome"]
        + 10 * checks["stopReason"]
        + 10 * checks["packageManager"]
        + 10 * checks["turboVersion"]
        + 10 * checks["requiresUpgrade"]
        + 40 * selection_score
    )
    hard_failure = not checks["selectionLimit"] or not checks["forbiddenSelections"]
    if hard_failure:
        score = min(score, 49)

    return {
        "score": round(score, 1),
        "hardFailure": hard_failure,
        "checks": checks,
        "expectedSelections": sorted([list(item) for item in expected_selections]),
        "actualSelections": sorted([list(item) for item in actual_selections]),
        "forbiddenSelected": sorted(
            [list(item) for item in actual_selections.intersection(forbidden)]
        ),
    }


def run_one(
    case: dict[str, Any],
    model: str,
    run_number: int,
    timeout: int,
    output_dir: pathlib.Path,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "case": case["id"],
        "model": model,
        "run": run_number,
    }
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix=f"vercel-ci-{case['id']}-") as temp:
        workspace = pathlib.Path(temp)
        initialize_workspace(case, workspace)
        command = [
            "cursor-agent",
            "--print",
            "--mode",
            "plan",
            "--model",
            model,
            "--output-format",
            "text",
            "--sandbox",
            "enabled",
            "--trust",
            "--workspace",
            str(workspace),
            PROMPT,
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "NO_COLOR": "1"},
            )
            result["exitCode"] = completed.returncode
            result["response"] = completed.stdout
            result["stderr"] = completed.stderr
            if completed.returncode != 0:
                result["error"] = f"cursor-agent exited {completed.returncode}"
            else:
                payload = extract_payload(completed.stdout)
                result["payload"] = payload
                result["grade"] = grade(case, payload)
        except (subprocess.TimeoutExpired, ValueError, json.JSONDecodeError) as error:
            result["error"] = str(error)

    result["durationSeconds"] = round(time.monotonic() - started, 2)
    run_path = output_dir / "runs" / model / case["id"]
    run_path.mkdir(parents=True, exist_ok=True)
    (run_path / f"{run_number}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result


def write_summary(results: list[dict[str, Any]], output_dir: pathlib.Path) -> None:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault((result["model"], result["case"]), []).append(result)

    rows = []
    for (model, case_id), runs in sorted(grouped.items()):
        scored = [run["grade"]["score"] for run in runs if "grade" in run]
        hard_failures = sum(
            bool(run.get("grade", {}).get("hardFailure")) for run in runs
        )
        errors = sum("error" in run for run in runs)
        average = f"{sum(scored) / len(scored):.1f}" if scored else "0.0"
        rows.append(
            f"| `{model}` | `{case_id}` | {average} | {hard_failures} | {errors} |"
        )

    summary = "\n".join(
        [
            "# Vercel CI setup eval results",
            "",
            "| Model | Case | Average score | Hard failures | Errors |",
            "| --- | --- | ---: | ---: | ---: |",
            *rows,
            "",
            "A forbidden task selection or selection count above five is a hard failure "
            "and caps the run score at 49.",
            "",
        ]
    )
    (output_dir / "summary.md").write_text(summary)
    (output_dir / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n"
    )
    print(summary)
    print(f"Results: {output_dir}")


def main() -> int:
    args = parse_args()
    if args.runs < 1 or args.jobs < 1:
        raise ValueError("--runs and --jobs must be positive")

    selected_ids = set(args.cases.split(",")) if args.cases else None
    cases = load_cases(selected_ids)
    for case in cases:
        validate_case(case)

    models = [model.strip() for model in args.models.split(",") if model.strip()]
    if not models:
        raise ValueError("At least one model is required")

    matrix = [
        (case, model, run_number)
        for case in cases
        for model in models
        for run_number in range(1, args.runs + 1)
    ]
    print(
        f"{len(cases)} cases × {len(models)} models × {args.runs} runs "
        f"= {len(matrix)} evaluations"
    )
    if args.dry_run:
        for case, model, run_number in matrix:
            print(f"{model}\t{case['id']}\trun {run_number}")
        return 0

    if shutil.which("cursor-agent") is None:
        raise RuntimeError("cursor-agent is not installed or not on PATH")

    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output or (
        SKILL_DIR.parents[1] / ".git" / "vercel-ci-evals" / timestamp
    )
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = [
            executor.submit(
                run_one,
                case,
                model,
                run_number,
                args.timeout,
                output_dir,
            )
            for case, model, run_number in matrix
        ]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            status = (
                f"{result['grade']['score']:.1f}"
                if "grade" in result
                else f"ERROR: {result.get('error', 'unknown')}"
            )
            print(
                f"{result['model']} / {result['case']} / "
                f"run {result['run']}: {status}"
            )

    write_summary(results, output_dir)
    return 1 if any("error" in result for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
