"""Synthetic, local tests. Fixtures are not evidence for any actual market."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_research import audit_workspace
from calculate_economics import calculate_model, calculate_scenario, wilson_interval
from init_research import initialize


def example_scenario() -> dict:
    data = json.loads((ROOT / "assets/unit_economics.example.json").read_text(encoding="utf-8"))
    return copy.deepcopy(data["scenarios"][1])


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


def fixture(root: Path) -> None:
    """Create an explicitly synthetic fixture, never real research history."""
    initialize("SYNTHETIC_TEST_NOT_MARKET_EVIDENCE", "TEST_ONLY", "2026-09-21", root)
    source = {
        "source_id": "S001", "title": "SYNTHETIC FIXTURE",
        "locator": "https://example.invalid/synthetic-fixture",
        "accessed_at": "2026-09-21", "origin_group": "O001",
        "source_kind": "official_record", "review_status": "reviewed_text",
        "access_status": "full", "quality_note": "Synthetic test record, not real evidence",
    }
    claim = {
        "claim_id": "C001", "dimension": "D1", "statement": "Synthetic assertion for tests only",
        "kind": "observed_fact", "confidence": "high", "confidence_reason": "Fixture only",
        "decision_role": "decisive", "included_in_report": True,
        "evidence": [{"source_id": "S001", "role": "supports", "precise_locator": "Synthetic section 1"}],
        "depends_on": [], "formula": None, "metric": None,
    }
    write_jsonl(root / "sources.jsonl", [source])
    write_jsonl(root / "claims.jsonl", [claim])
    write_jsonl(root / "actions.jsonl", [{
        "action_id": "T001", "timestamp": "2026-09-21T00:00:00+00:00",
        "phase": "synthetic_fixture", "tool": "synthetic", "operation": "synthetic",
        "target": "synthetic", "result_status": "synthetic", "executed": True,
    }])
    dims = json.loads((root / "dimension_assessments.json").read_text(encoding="utf-8"))
    for row in dims:
        row["conclusion"] = "Explicitly unknown in this synthetic fixture"
    dims[0].update({
        "status": "complete", "conclusion": "Synthetic conclusion", "claim_ids": ["C001"],
        "confidence": "high", "confidence_reason": "Fixture only", "decision_impact": "Fixture only",
    })
    (root / "dimension_assessments.json").write_text(json.dumps(dims), encoding="utf-8")
    for filename in ("research_plan.md", "report.md", "validation_package.md", "handoff.md"):
        (root / filename).write_text("# Synthetic test fixture; not a real research result.\n", encoding="utf-8")


class EconomicsTests(unittest.TestCase):
    def test_base_arithmetic(self):
        result = calculate_scenario(example_scenario())
        self.assertAlmostEqual(result["net_revenue_per_initial_payer"], 32.291925)
        self.assertAlmostEqual(result["paid_cac"], 50)
        self.assertAlmostEqual(result["contribution_per_payer_after_acquisition"], -22.708075)

    def test_higher_conversion(self):
        scenario = example_scenario()
        scenario["install_to_paid_rate"] = 0.06
        result = calculate_scenario(scenario)
        self.assertAlmostEqual(result["paid_cac"], 25)
        self.assertAlmostEqual(result["contribution_per_payer_after_acquisition"], 2.291925)

    def test_install_service_cost(self):
        scenario = example_scenario()
        scenario["variable_cost_per_install"] = 0.1
        result = calculate_scenario(scenario)
        self.assertAlmostEqual(result["break_even_cpi_ceiling"], 0.03 * 27.291925 - 0.1)
        self.assertAlmostEqual(result["contribution_per_payer_after_acquisition"], 27.291925 - 1.6 / 0.03)

    def test_zero_conversion(self):
        scenario = example_scenario()
        scenario["install_to_paid_rate"] = 0
        result = calculate_scenario(scenario)
        self.assertIsNone(result["paid_cac"])
        self.assertIsNone(result["contribution_per_payer_after_acquisition"])
        self.assertEqual(result["contribution_per_install_after_acquisition"], -1.5)

    def test_non_positive_base(self):
        scenario = example_scenario()
        scenario["store_fee_rate"] = 1
        result = calculate_scenario(scenario)
        self.assertIsNone(result["break_even_conversion_at_given_cpi"])
        self.assertLess(result["break_even_cpi_ceiling"], 0)

    def test_invalid_ratio(self):
        scenario = example_scenario()
        scenario["install_to_paid_rate"] = 3
        with self.assertRaises(ValueError):
            calculate_scenario(scenario)

    def test_negative_cost(self):
        scenario = example_scenario()
        scenario["cost_per_install"] = -1
        with self.assertRaises(ValueError):
            calculate_scenario(scenario)

    def test_missing_and_non_finite_number(self):
        for bad_value in (None, True, float("nan"), float("inf")):
            with self.subTest(bad_value=bad_value):
                scenario = example_scenario()
                scenario["price"] = bad_value
                with self.assertRaises(ValueError):
                    calculate_scenario(scenario)

    def test_model_requires_unique_ids(self):
        scenario = example_scenario()
        with self.assertRaises(ValueError):
            calculate_model({"model": "first_purchase_subscription", "scenarios": [scenario, scenario]})

    def test_empty_model_rejected(self):
        with self.assertRaises(ValueError):
            calculate_model({"model": "first_purchase_subscription", "scenarios": []})

    def test_example_flag_preserved(self):
        model = json.loads((ROOT / "assets/unit_economics.example.json").read_text(encoding="utf-8"))
        result = calculate_model(model)
        self.assertTrue(result["example_only"])
        self.assertEqual(len(result["results"]), 3)

    def test_wilson_small_sample(self):
        result = wilson_interval(3, 100)
        self.assertAlmostEqual(result["observed_rate"], 0.03)
        self.assertTrue(0.010 < result["wilson_lower"] < 0.011)
        self.assertTrue(0.084 < result["wilson_upper"] < 0.085)

    def test_wilson_edge_counts(self):
        zero = wilson_interval(0, 100)
        full = wilson_interval(100, 100)
        self.assertAlmostEqual(zero["wilson_lower"], 0)
        self.assertGreater(zero["wilson_upper"], 0)
        self.assertLess(full["wilson_lower"], 1)
        self.assertAlmostEqual(full["wilson_upper"], 1)

    def test_wilson_invalid_inputs(self):
        for successes, total, confidence in ((0, 0, .95), (101, 100, .95), (-1, 100, .95), (3, 100, 1), (True, 100, .95)):
            with self.subTest(values=(successes, total, confidence)):
                with self.assertRaises(ValueError):
                    wilson_interval(successes, total, confidence)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "research"

    def tearDown(self):
        self.temp.cleanup()

    def test_initialize(self):
        result = initialize("测试品类", "中国大陆,美国", "2026-09-21", self.root)
        self.assertEqual(result["status"], "initialized_not_researched")
        self.assertEqual(len(result["created_files"]), 11)
        self.assertEqual((self.root / "actions.jsonl").read_text(), "")

    def test_refuses_overwrite(self):
        initialize("test", "test", "2026-09-21", self.root)
        with self.assertRaises(FileExistsError):
            initialize("test", "test", "2026-09-21", self.root)

    def test_invalid_date(self):
        for bad_date in ("YYYY-MM-DD", "2026-02-30", "20260921"):
            with self.subTest(date=bad_date):
                with self.assertRaises(ValueError):
                    initialize("test", "test", bad_date, self.root)

    def test_blank_workspace_not_ready(self):
        initialize("test", "test", "2026-09-21", self.root)
        result = audit_workspace(self.root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("placeholders" in error for error in result["errors"]))

    def test_valid_fixture(self):
        fixture(self.root)
        result = audit_workspace(self.root)
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["semantic_review_required"])
        self.assertEqual(result["stats"]["reviewed_source_records"], 1)
        self.assertEqual(result["stats"]["logged_tool_calls"], 1)
        self.assertIsNone(result["stats"]["search_hits"])

    def test_lead_does_not_support_fact(self):
        fixture(self.root)
        source = json.loads((self.root / "sources.jsonl").read_text())
        source["review_status"] = "lead_only"
        write_jsonl(self.root / "sources.jsonl", [source])
        result = audit_workspace(self.root)
        self.assertTrue(any("lacks a reviewed supporting source" in error for error in result["errors"]))

    def test_missing_source(self):
        fixture(self.root)
        (self.root / "sources.jsonl").write_text("")
        result = audit_workspace(self.root)
        self.assertTrue(any("missing source" in error for error in result["errors"]))

    def test_duplicate_claim_id(self):
        fixture(self.root)
        claim = json.loads((self.root / "claims.jsonl").read_text())
        write_jsonl(self.root / "claims.jsonl", [claim, claim])
        result = audit_workspace(self.root)
        self.assertTrue(any("duplicate claim_id" in error for error in result["errors"]))

    def test_estimate_needs_formula(self):
        fixture(self.root)
        claim = json.loads((self.root / "claims.jsonl").read_text())
        estimate = copy.deepcopy(claim)
        estimate.update({"claim_id": "C002", "kind": "estimate", "depends_on": ["C001"], "formula": None})
        write_jsonl(self.root / "claims.jsonl", [claim, estimate])
        result = audit_workspace(self.root)
        self.assertTrue(any("estimate requires a formula" in error for error in result["errors"]))

    def test_dependency_cycle(self):
        fixture(self.root)
        claim = json.loads((self.root / "claims.jsonl").read_text())
        other = copy.deepcopy(claim)
        claim.update({"kind": "inference", "depends_on": ["C002"]})
        other.update({"claim_id": "C002", "kind": "inference", "depends_on": ["C001"]})
        write_jsonl(self.root / "claims.jsonl", [claim, other])
        result = audit_workspace(self.root)
        self.assertTrue(any("dependency cycle" in error for error in result["errors"]))

    def test_exact_locator_and_origin_counts(self):
        fixture(self.root)
        source = json.loads((self.root / "sources.jsonl").read_text())
        other = copy.deepcopy(source)
        other["source_id"] = "S002"
        write_jsonl(self.root / "sources.jsonl", [source, other])
        result = audit_workspace(self.root)
        self.assertEqual(result["stats"]["reviewed_source_records"], 2)
        self.assertEqual(result["stats"]["unique_reviewed_locators"], 1)
        self.assertEqual(result["stats"]["reviewed_origin_groups"], 1)
        self.assertTrue(any("deduplication" in warning for warning in result["warnings"]))

    def test_dimension_coverage(self):
        fixture(self.root)
        dims = json.loads((self.root / "dimension_assessments.json").read_text())
        (self.root / "dimension_assessments.json").write_text(json.dumps(dims[:-1]))
        result = audit_workspace(self.root)
        self.assertTrue(any("D1-D6 exactly once" in error for error in result["errors"]))

    def test_malformed_enum_does_not_crash(self):
        fixture(self.root)
        source = json.loads((self.root / "sources.jsonl").read_text())
        source["review_status"] = ["reviewed_text"]
        source["source_kind"] = {"bad": "type"}
        write_jsonl(self.root / "sources.jsonl", [source])
        result = audit_workspace(self.root)
        self.assertTrue(any("invalid review_status" in error for error in result["errors"]))
        self.assertTrue(any("invalid source_kind" in error for error in result["errors"]))

    def test_invalid_action_timestamp(self):
        fixture(self.root)
        action = json.loads((self.root / "actions.jsonl").read_text())
        action["timestamp"] = "2026-09-21-not-a-timestamp"
        write_jsonl(self.root / "actions.jsonl", [action])
        result = audit_workspace(self.root)
        self.assertTrue(any("actual ISO date or timestamp" in error for error in result["errors"]))

    def test_metric_scope_required(self):
        fixture(self.root)
        claim = json.loads((self.root / "claims.jsonl").read_text())
        claim["metric"] = {"name": "test", "value": 1}
        write_jsonl(self.root / "claims.jsonl", [claim])
        result = audit_workspace(self.root)
        self.assertTrue(any("metric missing scope field" in error for error in result["errors"]))


class PackageTests(unittest.TestCase):
    def test_skill_name_and_length(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: business-opportunity-research\n", text)
        self.assertLess(len(text.splitlines()), 500)
        self.assertTrue(re.search(r"^description: .+", text, flags=re.M))

    def test_markdown_local_links(self):
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target = target.split("#", 1)[0]
                with self.subTest(file=path.name, target=target):
                    self.assertTrue((path.parent / target).exists(), f"Broken link: {path} -> {target}")


if __name__ == "__main__":
    unittest.main()
