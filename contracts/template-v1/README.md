# Template v1 contract

[中文](README.zh-CN.md)

This owner module validates named `sandbox` and `serving` resources and optional Registry publication metadata. The public shape is defined by [the resource schema](../../spec/template-v1.schema.json) and [the Registry schema](../../spec/registry-v1.schema.json). Usage is documented in [the template specification](../../docs/template-spec.md).

`parseYamlV1` / `parse_yaml_v1` reads bounded JSON-compatible YAML 1.2 Core without expressions or credentials. `normalizeTemplateV1` / `normalize_template_v1` validates and clones input. Its only build default is `context = dirname(dockerfile)`. `compileTemplateV1` / `compile_template_v1` preserves the named maps and adds an internal resource kind; it does not recreate retired application or instance declarations.

Intent validation preserves expressions. Execution resolves them before resolved-stage validation and selected Provider validation. `registry.yaml.parameters` targets existing local values by JSON Pointer. Runtime validation never reads Registry metadata. Expression execution and component invocation belong to the CLI, and catalog tools must not execute either.

Run `npm ci && npm test` here, or `python test_contract.py`. Both language implementations run the same resource and source-reader fixtures and compare their complete outputs. These checks do not prove cloud deployment.
