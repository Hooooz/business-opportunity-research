#!/usr/bin/env python3
"""Create a new research workspace. No network, no overwriting existing work."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shutil
import sys

SKILL_ROOT = Path(__file__).resolve().parents[1]


def initialize(category: str, markets: str, as_of: str, out: Path) -> dict:
    if not category.strip():
        raise ValueError("category must be a non-empty string")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of):
        raise ValueError("as-of must be an actual date in YYYY-MM-DD format")
    date.fromisoformat(as_of)
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite an existing path: {out}")

    assets = SKILL_ROOT / "assets"
    brief = json.loads((assets / "brief.template.json").read_text(encoding="utf-8"))
    brief.update({
        "category": category.strip(),
        "markets": [item.strip() for item in markets.split(",") if item.strip()],
        "as_of": as_of,
    })
    out.mkdir(parents=True, exist_ok=False)
    (out / "brief.json").write_text(
        json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    copies = {
        "research-plan.template.md": "research_plan.md",
        "report.template.md": "report.md",
        "validation-package.template.md": "validation_package.md",
        "handoff.template.md": "handoff.md",
        "unit_economics.template.json": "unit_economics.json",
    }
    for source, target in copies.items():
        shutil.copyfile(assets / source, out / target)
    for filename in ("actions.jsonl", "sources.jsonl", "claims.jsonl", "competitors.jsonl"):
        (out / filename).write_text("", encoding="utf-8")
    assessments = [
        {
            "dimension": f"D{index}",
            "status": "unknown",
            "conclusion": "",
            "claim_ids": [],
            "confidence": "unassessed",
            "confidence_reason": "尚未研究",
            "decision_impact": "待判断",
            "limitation": "尚未研究",
        }
        for index in range(1, 7)
    ]
    (out / "dimension_assessments.json").write_text(
        json.dumps(assessments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "workspace": str(out.resolve()),
        "created_files": sorted(path.name for path in out.iterdir()),
        "status": "initialized_not_researched",
        "note": "Empty ledgers and placeholders are intentional. No research actions have been executed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", required=True)
    parser.add_argument("--markets", default="待确认", help="Comma-separated target markets")
    parser.add_argument("--as-of", required=True, help="Actual YYYY-MM-DD date")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = initialize(args.category, args.markets, args.as_of, args.out)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
