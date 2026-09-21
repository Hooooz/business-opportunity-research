#!/usr/bin/env python3
"""Transparent first-purchase subscription arithmetic and Wilson intervals.

Standard library only. No network or forecasts. All inputs must be supplied.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist
import sys
from typing import Any


def number(data: dict[str, Any], key: str, *, rate: bool = False) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a supplied number")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{key} must be finite and non-negative")
    if rate and value > 1:
        raise ValueError(f"{key} must be between 0 and 1; use 0.03 for 3%")
    return value


def calculate_scenario(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Each scenario must be an object")
    for key in ("id", "currency", "revenue_period", "evidence_basis"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"{key} must be a non-empty string")
    days = data.get("conversion_window_days")
    if isinstance(days, bool) or not isinstance(days, int) or days <= 0:
        raise ValueError("conversion_window_days must be a positive integer")
    allowed_bases = {"measured", "external_reference", "estimate", "assumption", "mixed"}
    if data["evidence_basis"] not in allowed_bases:
        raise ValueError(f"evidence_basis must be one of {sorted(allowed_bases)}")

    price = number(data, "price")
    refund = number(data, "refund_rate", rate=True)
    fee = number(data, "store_fee_rate", rate=True)
    payer_cost = number(data, "variable_cost_per_payer")
    install_cost = number(data, "variable_cost_per_install")
    conversion = number(data, "install_to_paid_rate", rate=True)
    cpi = number(data, "cost_per_install")

    net_revenue = price * (1 - refund) * (1 - fee)
    base_contribution = net_revenue - payer_cost
    max_cpi = conversion * base_contribution - install_cost
    required_conversion = (cpi + install_cost) / base_contribution if base_contribution > 0 else None
    # Zero conversion has no paying customer denominator; use null, not zero or infinity.
    cac = cpi / conversion if conversion > 0 else None
    before_acquisition = base_contribution - install_cost / conversion if conversion > 0 else None
    after_acquisition = base_contribution - (cpi + install_cost) / conversion if conversion > 0 else None
    contribution_per_install = conversion * base_contribution - install_cost - cpi

    warnings = [
        "Contribution is not net profit: fixed costs, omitted taxes and other unmodeled costs are excluded.",
        "Fees are assumed to apply after refunded revenue is removed. Verify actual fee/refund treatment.",
        "No renewal, organic-acquisition subsidy, exchange-rate conversion or probability forecast is assumed.",
    ]
    if conversion == 0:
        warnings.append("No paying customers at zero conversion; per-payer metrics are undefined.")
    if base_contribution <= 0:
        warnings.append("Payer-level contribution is non-positive before acquisition/common install costs.")
    elif required_conversion is not None and required_conversion > 1:
        warnings.append("Required conversion exceeds 100%; the supplied scenario cannot break even.")
    if max_cpi < 0:
        warnings.append("Non-acquisition service costs exceed contribution even with zero paid CPI.")
    if data["evidence_basis"] != "measured":
        warnings.append("Inputs are not wholly measured. This is conditional arithmetic, not validated unit economics.")
    return {
        "id": data["id"],
        "currency": data["currency"],
        "revenue_period": data["revenue_period"],
        "conversion_window_days": days,
        "evidence_basis": data["evidence_basis"],
        "net_revenue_per_initial_payer": net_revenue,
        "payer_contribution_before_common_costs_and_acquisition": base_contribution,
        "contribution_per_payer_before_acquisition": before_acquisition,
        "paid_cac": cac,
        "contribution_per_payer_after_acquisition": after_acquisition,
        "contribution_per_install_after_acquisition": contribution_per_install,
        "break_even_cpi_ceiling": max_cpi,
        "break_even_conversion_at_given_cpi": required_conversion,
        "warnings": warnings,
    }


def calculate_model(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("model") != "first_purchase_subscription":
        raise ValueError("model must be first_purchase_subscription")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenarios must be a non-empty list; an empty template is not a model")
    results = [calculate_scenario(scenario) for scenario in scenarios]
    ids = [result["id"] for result in results]
    if len(ids) != len(set(ids)):
        raise ValueError("Scenario IDs must be unique")
    example = data.get("example_only", False)
    if not isinstance(example, bool):
        raise ValueError("example_only must be boolean")
    return {
        "model": data["model"],
        "example_only": example,
        "source_notes": data.get("notes"),
        "results": results,
        "interpretation": "Illustration only; not market evidence." if example else "Conditional calculations; verify all evidence and scope before use.",
    }


def wilson_interval(successes: int, total: int, confidence: float = 0.95) -> dict[str, Any]:
    if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
        raise ValueError("total must be a positive integer")
    if isinstance(successes, bool) or not isinstance(successes, int) or not 0 <= successes <= total:
        raise ValueError("successes must be an integer between zero and total")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one, exclusive")
    quantile = (1 + confidence) / 2
    if not 0 < quantile < 1:
        raise ValueError("confidence is too close to one for floating-point quantile calculation")
    z = NormalDist().inv_cdf(quantile)
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {
        "successes": successes,
        "total": total,
        "observed_rate": p,
        "confidence_level": confidence,
        "wilson_lower": max(0.0, center - radius),
        "wilson_upper": min(1.0, center + radius),
        "limitations": "Binomial interval only: does not correct selection bias, repeated users, sequential stopping, causal confounding or population mismatch.",
    }


def emit(data: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    model_parser = subparsers.add_parser("model", help="Calculate explicitly supplied scenarios")
    model_parser.add_argument("input", type=Path)
    model_parser.add_argument("--output", type=Path)
    wilson_parser = subparsers.add_parser("wilson", help="Calculate a Wilson binomial proportion interval")
    wilson_parser.add_argument("--successes", required=True, type=int)
    wilson_parser.add_argument("--total", required=True, type=int)
    wilson_parser.add_argument("--confidence", type=float, default=0.95)
    wilson_parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "model":
            if args.output and args.output.resolve() == args.input.resolve():
                raise ValueError("Output must not overwrite the model input file")
            data = json.loads(args.input.read_text(encoding="utf-8"))
            result = calculate_model(data)
        else:
            result = wilson_interval(args.successes, args.total, args.confidence)
        emit(result, args.output)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
