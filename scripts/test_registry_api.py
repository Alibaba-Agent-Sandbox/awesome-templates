"""Current optional API publication contract, independent of resource spec migration."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import check_template
import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("registry_api_test", ROOT / "contracts/registry-api/validate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RegistryApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entry = {"resource": "sandbox.agent", "port": 9000, "openapi": "openapi.yaml"}
        self.api = {"openapi": "3.1.0", "info": {"title": "Report", "version": "1"},
                    "paths": {"/report": {"post": {"operationId": "report", "responses": {"200": {"description": "OK"}}}}}}
        self.write()

    def write(self):
        (self.root / "registry.yaml").write_text(yaml.safe_dump({"apis": {"reports": self.entry}}))
        (self.root / "openapi.yaml").write_text(yaml.safe_dump(self.api))

    def test_api_only_metadata_and_schema_fragment(self):
        schema = json.loads((ROOT / "spec/registry-v1.schema.json").read_text())
        jsonschema.Draft202012Validator(schema["$defs"]["apiBindings"]).validate({"reports": self.entry})
        self.api["servers"] = [{"url": "https://not-used.invalid"}]
        self.api["paths"]["/report"]["post"]["requestBody"] = {"content": {"application/json": {
            "schema": {"type": "object", "properties": {"key": {"type": "string", "default": "private-default"}}}}}}
        self.write()
        summary = module.read_api_bindings(self.root)
        self.assertEqual(summary[0]["operations"], [{"operationId": "report", "method": "POST", "path": "/report"}])
        self.assertNotIn("private-default", json.dumps(summary))
        self.assertNotIn("not-used.invalid", json.dumps(summary))
        self.assertFalse([v for v in check_template.check_directory(self.root) if v.code == "registry-api"])

    def test_bad_binding_reaches_checker(self):
        for field, value in [("port", True), ("port", 65536), ("resource", "serving.api"),
                             ("openapi", "https://example.invalid/openapi.yaml"), ("extra", "unknown")]:
            with self.subTest(field=field, value=value):
                saved = copy.deepcopy(self.entry)
                self.entry[field] = value
                self.write()
                with self.assertRaises(ValueError):
                    module.read_api_bindings(self.root)
                self.assertTrue(any(v.code == "registry-api" for v in check_template.check_directory(self.root)))
                self.entry = saved

    def test_symlink_escape_and_external_references(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "api.yaml"
            target.write_text(yaml.safe_dump(self.api))
            (self.root / "openapi.yaml").unlink()
            (self.root / "openapi.yaml").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "escapes"):
                module.read_api_bindings(self.root)
        (self.root / "openapi.yaml").unlink()
        self.api["paths"]["/report"] = {"$ref": "https://example.invalid/api.yaml#/report"}
        self.write()
        with self.assertRaisesRegex(ValueError, "external"):
            module.read_api_bindings(self.root)

    def test_duplicate_ids_aliases_and_unsupported_extensions(self):
        original = copy.deepcopy(self.api)
        self.api["paths"]["/second"] = copy.deepcopy(self.api["paths"]["/report"])
        self.write()
        with self.assertRaisesRegex(ValueError, "unique"):
            module.read_api_bindings(self.root)
        self.api = original
        self.api["paths"]["/report"]["post"]["x-abx-alias"] = "ask"
        self.write()
        with self.assertRaisesRegex(ValueError, "extensions"):
            module.read_api_bindings(self.root)
        (self.root / "registry.yaml").write_text("apis: &apis {}\ncopy: *apis\n")
        with self.assertRaises(ValueError):
            module.read_api_bindings(self.root)

    def test_internal_path_reference_and_recursive_reference(self):
        self.api["components"] = {"pathItems": {"report": self.api["paths"]["/report"]}}
        self.api["paths"]["/report"] = {"$ref": "#/components/pathItems/report"}
        self.write()
        self.assertEqual(module.read_api_bindings(self.root)[0]["operations"][0]["operationId"], "report")
        self.api["components"]["pathItems"]["report"] = {"$ref": "#/components/pathItems/report"}
        self.write()
        with self.assertRaisesRegex(ValueError, "Recursive"):
            module.read_api_bindings(self.root)

    def test_reference_in_schema_rejected_but_example_data_is_not_dereferenced(self):
        operation = self.api["paths"]["/report"]["post"]
        operation["parameters"] = [{"name": "mode", "in": "query", "schema": {
            "$ref": "./other.yaml#/Mode"}}]
        self.write()
        with self.assertRaisesRegex(ValueError, "external"):
            module.read_api_bindings(self.root)
        operation["parameters"][0]["schema"] = {"type": "string"}
        operation["responses"]["200"]["content"] = {"application/json": {
            "example": {"$ref": "literal business value", "x-abx-data": True}}}
        self.write()
        self.assertEqual(len(module.read_api_bindings(self.root)), 1)

    def test_oversized_file_is_rejected_before_parsing(self):
        (self.root / "openapi.yaml").write_bytes(b"#" * (1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, "1 MiB"):
            module.read_api_bindings(self.root)


if __name__ == "__main__":
    unittest.main()
