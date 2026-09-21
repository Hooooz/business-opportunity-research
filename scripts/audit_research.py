#!/usr/bin/env python3
"""Audit research records for structure and traceability, NOT source truth.

Does not browse, alter evidence, score opportunities, or verify citation semantics.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime
import json
import math
from pathlib import Path
import sys
from typing import Any

DIMENSIONS = {f"D{i}" for i in range(1, 7)}
KINDS = {"observed_fact", "attributed_fact", "estimate", "assumption", "inference", "unknown"}
CONFIDENCE = {"high", "medium", "low", "unassessed"}
REVIEWED = {"reviewed_text", "reviewed_visual"}
REVIEW_STATUSES = REVIEWED | {"lead_only", "metadata_only", "failed"}
ACCESS_STATUSES = {"full", "partial", "paywalled", "blocked", "missing", "error"}
SOURCE_KINDS = {"official_record", "company_statement", "original_research", "third_party_estimate", "firsthand_review", "internal_data", "secondary_report", "other"}


def is_choice(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def audit_workspace(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    def finite_values(value: Any, label: str) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f"{label}: non-finite numeric value")
        elif isinstance(value, dict):
            for key, child in value.items():
                finite_values(child, f"{label}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                finite_values(child, f"{label}[{index}]")

    def load_json(filename: str, fallback: Any) -> Any:
        try:
            data = json.loads((root / filename).read_text(encoding="utf-8"))
            finite_values(data, filename)
            return data
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{filename}: {exc}")
            return fallback

    def load_jsonl(filename: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        try:
            lines = (root / filename).read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"{filename}: {exc}")
            return records
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            label = f"{filename}:{line_number}"
            try:
                item = json.loads(line)
                if not isinstance(item, dict):
                    raise ValueError("record must be a JSON object")
                finite_values(item, label)
                records.append(item)
            except (ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{label}: {exc}")
        return records

    def required_text(record: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
        for field in fields:
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{label}: {field} must be a non-empty string")

    def valid_date(value: Any, label: str) -> None:
        try:
            if not isinstance(value, str):
                raise ValueError("not a date string")
            if len(value) == 10:
                date.fromisoformat(value)
            else:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{label}: expected an actual ISO date or timestamp")

    def index_by(records: list[dict[str, Any]], field: str, label: str) -> dict[str, dict[str, Any]]:
        indexed: dict[str, dict[str, Any]] = {}
        for row in records:
            key = row.get(field)
            if not isinstance(key, str) or not key.strip():
                errors.append(f"{label}: missing/invalid {field}")
            elif key in indexed:
                errors.append(f"{label}: duplicate {field} {key}")
            else:
                indexed[key] = row
        return indexed

    brief = load_json("brief.json", {})
    if not isinstance(brief, dict):
        errors.append("brief.json must be an object")
        brief = {}
    required_text(brief, ("category", "core_question"), "brief")
    valid_date(brief.get("as_of"), "brief.as_of")
    if not isinstance(brief.get("markets"), list) or not brief.get("markets"):
        warnings.append("Research market is not specified")
    if brief.get("company_context_status") == "unknown":
        warnings.append("Company context is unknown; final D4 and decision must remain conditional")

    sources = load_jsonl("sources.jsonl")
    claims = load_jsonl("claims.jsonl")
    actions = load_jsonl("actions.jsonl")
    competitors = load_jsonl("competitors.jsonl")
    source_index = index_by(sources, "source_id", "sources")
    claim_index = index_by(claims, "claim_id", "claims")
    index_by(actions, "action_id", "actions")

    for source_id, source in source_index.items():
        required_text(source, ("title", "locator", "origin_group", "quality_note"), source_id)
        valid_date(source.get("accessed_at"), f"{source_id}.accessed_at")
        if not is_choice(source.get("review_status"), REVIEW_STATUSES):
            errors.append(f"{source_id}: invalid review_status")
        if not is_choice(source.get("access_status"), ACCESS_STATUSES):
            errors.append(f"{source_id}: invalid access_status")
        if not is_choice(source.get("source_kind"), SOURCE_KINDS):
            errors.append(f"{source_id}: invalid source_kind")
        if is_choice(source.get("review_status"), REVIEWED) and not is_choice(source.get("access_status"), {"full", "partial"}):
            errors.append(f"{source_id}: reviewed source must have full or partial readable access")

    duplicate_locators = Counter(s.get("locator") for s in sources if isinstance(s.get("locator"), str))
    for locator, count in duplicate_locators.items():
        if count > 1:
            warnings.append(f"Exact source locator appears {count} times; review deduplication: {locator}")

    cited_sources: set[str] = set()
    decisive_count = 0
    decisive_supported_count = 0
    for claim_id, claim in claim_index.items():
        required_text(claim, ("statement", "confidence_reason"), claim_id)
        kind = claim.get("kind")
        if not is_choice(kind, KINDS):
            errors.append(f"{claim_id}: invalid kind")
        if not is_choice(claim.get("dimension"), DIMENSIONS | {"CROSS"}):
            errors.append(f"{claim_id}: invalid dimension")
        if not is_choice(claim.get("confidence"), CONFIDENCE):
            errors.append(f"{claim_id}: invalid confidence")
        if not is_choice(claim.get("decision_role"), {"decisive", "supporting", "background"}):
            errors.append(f"{claim_id}: invalid decision_role")
        if not isinstance(claim.get("included_in_report"), bool):
            errors.append(f"{claim_id}: included_in_report must be boolean")
        evidence = claim.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{claim_id}: evidence must be a list")
            evidence = []
        valid_support = False
        for item in evidence:
            if not isinstance(item, dict):
                errors.append(f"{claim_id}: evidence entries must be objects")
                continue
            sid = item.get("source_id")
            if not isinstance(sid, str) or sid not in source_index:
                errors.append(f"{claim_id}: references missing source {sid}")
                continue
            if not is_choice(item.get("role"), {"supports", "contradicts", "context"}):
                errors.append(f"{claim_id}: invalid evidence role for {sid}")
            required_text(item, ("precise_locator",), f"{claim_id}/{sid}")
            reviewed = is_choice(source_index[sid].get("review_status"), REVIEWED)
            if item.get("role") == "supports" and reviewed:
                valid_support = True
            if claim.get("included_in_report"):
                cited_sources.add(sid)
                if not reviewed:
                    warnings.append(f"{claim_id}: report cites an unreviewed source {sid}")
        if is_choice(kind, {"observed_fact", "attributed_fact"}) and not valid_support:
            errors.append(f"{claim_id}: factual claim lacks a reviewed supporting source")
        dependencies = claim.get("depends_on", [])
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies):
            errors.append(f"{claim_id}: depends_on must be a list of claim IDs")
            dependencies = []
        for dependency in dependencies:
            if dependency not in claim_index:
                errors.append(f"{claim_id}: missing dependency {dependency}")
        if is_choice(kind, {"estimate", "inference"}) and not dependencies:
            errors.append(f"{claim_id}: {kind} requires premise/input claim IDs")
        if kind == "estimate" and (not isinstance(claim.get("formula"), str) or not claim["formula"].strip()):
            errors.append(f"{claim_id}: estimate requires a formula")
        metric = claim.get("metric")
        if metric is not None:
            if not isinstance(metric, dict):
                errors.append(f"{claim_id}: metric must be an object or null")
            else:
                for key in ("name", "value", "unit", "geography", "population", "period", "platform", "definition"):
                    if key not in metric:
                        errors.append(f"{claim_id}: metric missing scope field {key}")
                    elif metric[key] is None:
                        warnings.append(f"{claim_id}: metric {key} is unknown; limit comparison/aggregation")
        if claim.get("decision_role") == "decisive":
            decisive_count += 1
            if valid_support:
                decisive_supported_count += 1
            if is_choice(claim.get("confidence"), {"low", "unassessed"}) or is_choice(kind, {"unknown", "assumption"}):
                warnings.append(f"{claim_id}: material uncertainty must be reflected in the final decision")

    # Detect dependency cycles with an iterative topological pass.
    graph: dict[str, set[str]] = {}
    for cid, claim in claim_index.items():
        deps = claim.get("depends_on", [])
        graph[cid] = {dep for dep in deps if isinstance(dep, str) and dep in claim_index} if isinstance(deps, list) else set()
    pending = {cid: set(deps) for cid, deps in graph.items()}
    while pending:
        ready = {cid for cid, deps in pending.items() if not deps}
        if not ready:
            errors.append("Claim dependency cycle detected: " + ", ".join(sorted(pending)))
            break
        pending = {cid: deps - ready for cid, deps in pending.items() if cid not in ready}

    assessments = load_json("dimension_assessments.json", [])
    if not isinstance(assessments, list):
        errors.append("dimension_assessments.json must be a list")
        assessments = []
    assessment_ids: list[str] = []
    for assessment in assessments:
        if not isinstance(assessment, dict):
            errors.append("Dimension assessment must be an object")
            continue
        dimension = assessment.get("dimension")
        if isinstance(dimension, str):
            assessment_ids.append(dimension)
        required_text(assessment, ("conclusion", "confidence_reason", "decision_impact", "limitation"), str(dimension))
        if not is_choice(assessment.get("status"), {"complete", "provisional", "unknown", "not_applicable"}):
            errors.append(f"{dimension}: invalid assessment status")
        if not is_choice(assessment.get("confidence"), CONFIDENCE):
            errors.append(f"{dimension}: invalid assessment confidence")
        ids = assessment.get("claim_ids")
        if not isinstance(ids, list):
            errors.append(f"{dimension}: claim_ids must be a list")
            ids = []
        for cid in ids:
            if not isinstance(cid, str) or cid not in claim_index:
                errors.append(f"{dimension}: unknown claim reference {cid}")
        if is_choice(assessment.get("status"), {"complete", "provisional"}) and not ids:
            warnings.append(f"{dimension}: assessment has no linked claims")
        if assessment.get("status") == "unknown":
            warnings.append(f"{dimension}: explicitly unknown; propagate limitation to the decision")
    if len(assessment_ids) != 6 or set(assessment_ids) != DIMENSIONS:
        errors.append("Dimension assessments must cover D1-D6 exactly once")

    for action in actions:
        aid = str(action.get("action_id", "action"))
        required_text(action, ("phase", "tool", "operation", "target", "result_status"), aid)
        valid_date(action.get("timestamp"), f"{aid}.timestamp")
        if not isinstance(action.get("executed"), bool):
            errors.append(f"{aid}: executed must be boolean")
        elif not action["executed"]:
            warnings.append(f"{aid}: planned/non-executed actions belong in the plan, not execution history")

    for filename in ("research_plan.md", "report.md", "validation_package.md", "handoff.md"):
        try:
            text = (root / filename).read_text(encoding="utf-8")
            if "<FILL:" in text:
                errors.append(f"{filename}: unresolved template placeholders")
            elif not text.strip():
                errors.append(f"{filename}: empty document")
        except OSError as exc:
            errors.append(f"{filename}: {exc}")

    model = load_json("unit_economics.json", {})
    if not isinstance(model, dict):
        errors.append("unit_economics.json must be an object")
    elif model.get("example_only") is True:
        warnings.append("Economics model is labeled example_only: do not treat it as market evidence")
    elif model.get("model") == "first_purchase_subscription" and not model.get("scenarios"):
        warnings.append("Economics scenarios are empty; explain the gap or use an appropriate alternative model")

    reviewed = [source for source in sources if is_choice(source.get("review_status"), REVIEWED)]
    if not reviewed:
        warnings.append("No reviewed sources recorded; do not claim current market verification")
    if not actions:
        warnings.append("No tool actions logged; actual historical work counts cannot be reconstructed")
    if not claims:
        warnings.append("No atomic claims recorded; no decision evidence chain is available")
    stats = {
        "logged_tool_calls": sum(action.get("executed") is True for action in actions),
        "search_hits": None,
        "registered_source_records": len(sources),
        "reviewed_source_records": len(reviewed),
        "unique_reviewed_locators": len({source.get("locator") for source in reviewed if isinstance(source.get("locator"), str)}),
        "reviewed_origin_groups": len({source.get("origin_group") for source in reviewed if isinstance(source.get("origin_group"), str)}),
        "cited_source_records": len(cited_sources),
        "failed_source_records": sum(source.get("review_status") == "failed" for source in sources),
        "atomic_claims": len(claims),
        "decisive_claims": decisive_count,
        "decisive_claims_with_direct_reviewed_support": decisive_supported_count,
        "competitor_records": len(competitors),
    }
    return {
        "status": "fail" if errors else ("pass_with_warnings" if warnings else "pass"),
        "scope": "Structural and traceability checks only; source truth, independence, citation entailment, cost completeness and commercial judgment require human/agent review.",
        "stats_basis": "Self-recorded ledgers only. Not host telemetry. Origin-group counts are not automatic proof of independent corroboration. search_hits is unavailable from this schema.",
        "stats": stats,
        "errors": errors,
        "warnings": warnings,
        "semantic_review_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_workspace(args.workspace)
    text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        protected = {"brief.json", "sources.jsonl", "claims.jsonl", "actions.jsonl", "competitors.jsonl", "dimension_assessments.json", "unit_economics.json", "research_plan.md", "report.md", "validation_package.md", "handoff.md"}
        if args.output.resolve() in {(args.workspace / name).resolve() for name in protected}:
            parser.exit(2, "Error: audit output must not overwrite a research input file\n")
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        except OSError as exc:
            parser.exit(2, f"Error writing audit output: {exc}\n")
    print(text, end="")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
