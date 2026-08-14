#!/usr/bin/env python3
"""Validate the retained GearDrop visibility panel and metric denominators."""

import argparse
import json
from pathlib import Path


VALID_RESULTS = {"observed", "not_observed"}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=Path("geo/audits/2026-08-14-gemini-exploratory"),
    )
    args = parser.parse_args()
    root = args.audit_dir
    panel = [
        json.loads(line)
        for line in (root / "query-panel.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    runs = [load_json(root / row["run_file"]) for row in panel]
    metrics = load_json(root / "metrics.json")

    run_ids = [row["run_id"] for row in panel]
    errors = []
    if len(panel) != 72:
        errors.append("planned run count must remain 72")
    if len(set(run_ids)) != len(run_ids):
        errors.append("query panel contains duplicate run IDs")
    if len(runs) != len(panel):
        errors.append("every panel row must have a retained run")
    for row, run in zip(panel, runs):
        if run.get("run_id") != row.get("run_id"):
            errors.append("run identity mismatch: %s" % row.get("run_id"))
        planned = run.get("planned", {})
        if planned.get("query") != row.get("query"):
            errors.append("query drift: %s" % row.get("run_id"))

    valid = [run for run in runs if run["observation"]["result"] in VALID_RESULTS]
    blocked = [run for run in runs if run["observation"]["result"] == "blocked"]
    unaided = [
        run for run in valid
        if run["planned"]["eligible_for_geo"] and not run["planned"]["branded"]
    ]
    mentioned = [run for run in unaided if run["observation"]["brand_mentioned"]]
    expected = {
        "completed_runs": len(runs),
        "valid_runs": len(valid),
        "unaided_numerator": len(mentioned),
        "unaided_denominator": len(unaided),
    }
    overall = metrics.get("overall", {})
    observed_metric = overall.get("unaided_mention_rate", {})
    if overall.get("completed_runs") != expected["completed_runs"]:
        errors.append("metrics completed_runs drift")
    if overall.get("valid_runs") != expected["valid_runs"]:
        errors.append("metrics valid_runs drift")
    if observed_metric.get("numerator") != expected["unaided_numerator"]:
        errors.append("unaided numerator drift")
    if observed_metric.get("denominator") != expected["unaided_denominator"]:
        errors.append("unaided denominator drift")

    result = {
        "valid": not errors,
        "audit_dir": str(root),
        "planned_runs": len(panel),
        "retained_runs": len(runs),
        "valid_runs": len(valid),
        "blocked_runs": len(blocked),
        "unaided_mentions": "%d/%d" % (len(mentioned), len(unaided)),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
