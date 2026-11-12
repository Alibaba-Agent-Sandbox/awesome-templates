"""Cross-language v1 fixture consumption, with real JSON Schema validation."""

from __future__ import annotations

import importlib.util
import json
import sys
import traceback
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "template_v1_normalizer", ROOT / "normalize.py"
)
assert spec and spec.loader
normalizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalizer)
SCHEMA = json.loads((ROOT.parents[1] / "spec/template-v1.schema.json").read_text())
REGISTRY_SCHEMA = json.loads(
    (ROOT.parents[1] / "spec/registry-v1.schema.json").read_text()
)
FIXTURES = json.loads((ROOT / "fixtures.json").read_text())
VALIDATORS = {
    stage: Draft202012Validator(normalizer.schema_for_stage(SCHEMA, stage)).validate
    for stage in ("intent", "resolved")
}
REGISTRY_VALIDATOR = Draft202012Validator(REGISTRY_SCHEMA).validate


def plugin_descriptor(stage: str, value: Any, provider: str) -> None:
    """Fixture plugin descriptor proves selection/validation, not backend support."""
    assert provider == "third-party"
    assert stage == "sandbox.create"
    Draft202012Validator(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "timeout": {"type": "integer", "minimum": 1},
                "envs": {"type": "object"},
                "metadata": {"type": "object"},
            },
            "required": ["timeout"],
        }
    ).validate(value)


def outcomes() -> dict[str, Any]:
    """Consume all valid and invalid actual fixtures without evaluating expressions."""
    results: list[dict[str, Any]] = []
    for case in FIXTURES["validTemplates"]:
        before = deepcopy(case["manifest"])
        kwargs: dict[str, Any] = {"stage": case["stage"]}
        if case.get("provider"):
            kwargs["provider"] = case["provider"]
        if case.get("descriptor"):
            kwargs["validate_provider"] = plugin_descriptor
        normalized = normalizer.normalize_template_v1(
            case["manifest"], VALIDATORS[case["stage"]], **kwargs
        )
        assert case["manifest"] == before, case["id"]
        assert normalized == normalizer.normalize_template_v1(
            normalized, VALIDATORS[case["stage"]], **kwargs
        ), case["id"]
        row = {"id": case["id"], "normalized": normalized}
        if case.get("compile"):
            row["compiled"] = normalizer.compile_template_v1(
                case["manifest"], VALIDATORS[case["stage"]], **kwargs
            )
            assert "spec_version" not in row["compiled"]
        results.append(row)
    invalid: list[str] = []
    for case in FIXTURES["invalidTemplates"]:
        try:
            normalizer.normalize_template_v1(
                case["manifest"],
                VALIDATORS[case["stage"]],
                stage=case["stage"],
                provider=case.get("provider"),
            )
        except (TypeError, ValueError) as error:
            assert "do-not-store-plaintext" not in str(error)
            invalid.append(case["id"])
        else:
            raise AssertionError("Accepted invalid fixture " + case["id"])
    registry = FIXTURES["registry"]
    publication = normalizer.normalize_registry_v1(
        registry["valid"],
        registry["template"],
        REGISTRY_VALIDATOR,
        VALIDATORS["intent"],
    )
    registry_invalid = []
    for case in registry["invalid"]:
        try:
            normalizer.normalize_registry_v1(
                case["metadata"],
                registry["template"],
                REGISTRY_VALIDATOR,
                VALIDATORS["intent"],
            )
        except (TypeError, ValueError):
            registry_invalid.append(case["id"])
        else:
            raise AssertionError("Accepted invalid registry fixture " + case["id"])
    return {
        "valid": results,
        "invalid": invalid,
        "registry": publication,
        "registryInvalid": registry_invalid,
    }


class ContractTest(unittest.TestCase):
    """Observable contract and semantic consumption regressions."""

    def test_real_schema_and_shared_fixture_consumption(self) -> None:
        Draft202012Validator.check_schema(SCHEMA)
        Draft202012Validator.check_schema(REGISTRY_SCHEMA)
        result = outcomes()
        self.assertEqual(len(result["valid"]), len(FIXTURES["validTemplates"]))

    def test_resource_names_are_strict_without_limiting_native_references(self) -> None:
        manifest = deepcopy(FIXTURES["validTemplates"][0]["manifest"])
        manifest["name"] = "a" * 63
        self.assertEqual(
            normalizer.normalize_template_v1(manifest, VALIDATORS["intent"])["name"],
            "a" * 63,
        )
        for name in ["a" * 64, "name\n", "name\r\n"]:
            manifest["name"] = name
            with self.assertRaises(ValueError):
                normalizer.normalize_template_v1(manifest, VALIDATORS["intent"])
        row = next(
            row
            for row in outcomes()["valid"]
            if row["id"] == "long-native-reference-unrestricted"
        )
        self.assertGreater(len(row["compiled"]["template_id"]), 128)

    def test_additional_ports_do_not_fabricate_services(self) -> None:
        rows = {row["id"]: row for row in outcomes()["valid"]}
        self.assertEqual(
            rows["additional-access-ports-only"]["compiled"]["ports"], [6080, 9222]
        )
        self.assertEqual(
            rows["additional-access-ports-only"]["compiled"]["provides"], {}
        )
        self.assertEqual(
            rows["service-and-additional-port-union"]["compiled"]["ports"], [9000, 9222]
        )

    def test_provider_validation_is_deferred_until_resolved_stage(self) -> None:
        intent = deepcopy(FIXTURES["validTemplates"][0]["manifest"])
        intent["sandbox"]["instance"]["timeout"] = "${env('LIFETIME')}"
        calls = []

        def reject(stage: str, value: Any, provider: str) -> bool:
            calls.append((stage, value, provider))
            return False

        normalized = normalizer.normalize_template_v1(
            intent, VALIDATORS["intent"], validate_provider=reject
        )
        self.assertEqual(
            normalized["sandbox"]["instance"]["timeout"], "${env('LIFETIME')}"
        )
        self.assertEqual(calls, [])
        intent["sandbox"]["instance"]["timeout"] = 300
        with self.assertRaisesRegex(ValueError, "selected Provider validation failed"):
            normalizer.normalize_template_v1(
                intent,
                VALIDATORS["resolved"],
                stage="resolved",
                validate_provider=reject,
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "sandbox.create")

    def test_independent_resource_declarations_are_preserved(self) -> None:
        row = next(
            row
            for row in outcomes()["valid"]
            if row["id"] == "independent-sandbox-and-native-serving"
        )
        self.assertEqual(row["compiled"]["sandbox"], row["normalized"]["sandbox"])
        self.assertEqual(row["compiled"]["deployment"], row["normalized"]["deployment"])
        self.assertNotIn("application", row["compiled"])

    def test_managed_props_and_generated_bindings(self) -> None:
        rows = {row["id"]: row for row in outcomes()["valid"]}
        compiled = rows["managed-resolved-native-memory"]["compiled"]
        self.assertEqual(compiled["roleProps"]["worker"]["memorySize"], 4096)
        self.assertEqual(compiled["sandbox"]["instance"]["timeout"], 3600)
        self.assertEqual(
            compiled["application"]["sessions"]["maxLifetimeSeconds"], 3600
        )
        self.assertEqual(
            rows["managed-single-ttl"]["compiled"]["application"]["sessions"][
                "maxLifetimeSeconds"
            ],
            1800,
        )
        self.assertNotIn(
            "maxLifetimeSeconds",
            rows["managed-intent"]["normalized"]["application"]["sessions"],
        )
        self.assertEqual(
            compiled["bindingValues"]["clientAuth"],
            {"generate": True, "owner": "default"},
        )
        self.assertEqual(compiled["application"]["deployment"]["region"], "cn-hangzhou")
        self.assertEqual(
            compiled["application"]["deployment"]["serverBuildRecipe"]["dockerfile"],
            "server/Dockerfile",
        )
        self.assertEqual(
            compiled["application"]["bindings"]["model"]["targets"],
            ["sandbox-creation"],
        )
        custom = rows["managed-explicit-auth-preserved"]["compiled"]["bindingValues"]
        self.assertNotIn("generate", custom["clientAuth"])
        self.assertNotIn("generate", custom["internalAuth"])
        self.assertEqual(custom["clientAuth"]["tokens"][0]["owner"], "custom")
        self.assertEqual(
            rows["managed-native-role-authority"]["compiled"]["bindingValues"][
                "internalAuth"
            ]["roleArn"],
            "acs:ram::123456789:role/fixture",
        )

    def test_source_and_instances_preserve_different_meanings(self) -> None:
        rows = {row["id"]: row for row in outcomes()["valid"]}
        unbound = rows["unbound-source-portable"]["normalized"]
        self.assertNotIn("provider", unbound["sandbox"])
        compiled = rows["source-context-opensandbox"]["compiled"]
        self.assertEqual(
            compiled["build_profiles"]["portable"],
            {"dockerfile": "Dockerfile.portable", "context": "."},
        )
        self.assertEqual(compiled["aliases"], ["hello"])
        self.assertEqual(compiled["env"]["ABX_SERVER_TOKEN"], "")
        self.assertNotIn("cpu", compiled["sandbox"]["instance"])

    def test_native_expressions_are_preserved_and_registry_is_optional(self) -> None:
        case = next(
            row for row in FIXTURES["validTemplates"] if row["id"] == "managed-intent"
        )
        before = normalizer.normalize_template_v1(
            case["manifest"], VALIDATORS["intent"]
        )
        self.assertEqual(
            before["application"]["bindings"]["model"]["apiKey"],
            "${env('OPENAI_API_KEY')}",
        )
        self.assertEqual(
            normalizer.normalize_template_v1(case["manifest"], VALIDATORS["intent"]),
            before,
        )
        self.assertNotIn("parameters", before)

    def test_json_pointer_escaping_and_array_indexes(self) -> None:
        self.assertEqual(
            normalizer.pointer_value({"a/b": {"~": ["value"]}}, "/a~1b/~0/0"), "value"
        )
        with self.assertRaises(ValueError):
            normalizer.pointer_value(["value"], "/01")
        with self.assertRaises(ValueError):
            normalizer.pointer_value({}, "")

    def test_validation_tracebacks_do_not_disclose_secret_values(self) -> None:
        case = next(
            row
            for row in FIXTURES["invalidTemplates"]
            if row["id"] == "managed-plaintext-secret"
        )
        try:
            normalizer.normalize_template_v1(case["manifest"], VALIDATORS["intent"])
        except ValueError as error:
            rendered = "".join(traceback.format_exception(error))
            self.assertNotIn("do-not-store-plaintext", rendered)
        else:
            self.fail("Expected secret input rejection")

    def test_selected_plugin_must_actually_validate(self) -> None:
        case = next(
            row
            for row in FIXTURES["validTemplates"]
            if row["id"] == "third-party-descriptor"
        )
        with self.assertRaises(ValueError):
            normalizer.normalize_template_v1(
                case["manifest"],
                VALIDATORS["resolved"],
                stage="resolved",
                validate_provider=lambda *_: False,
            )

    def test_nonfinite_values_do_not_cross_language_boundary(self) -> None:
        for number in (float("nan"), float("inf"), 10**200):
            case = deepcopy(FIXTURES["validTemplates"][0]["manifest"])
            case["sandbox"]["instance"]["timeout"] = number
            with self.assertRaises(ValueError):
                normalizer.normalize_template_v1(case, VALIDATORS["intent"])


if __name__ == "__main__":
    if "--emit" in sys.argv:
        print(
            json.dumps(
                outcomes(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
    else:
        unittest.main()
