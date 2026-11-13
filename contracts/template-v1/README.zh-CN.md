# Template v1 契约

[English](README.md)

本模块校验命名 `sandbox`、`serving` 资源和可选 Registry 上架元数据。公开结构由[资源 Schema](../../spec/template-v1.schema.json)与[Registry Schema](../../spec/registry-v1.schema.json)定义，用法见[模板规范](../../docs/template-spec.zh-CN.md)。

`parseYamlV1` / `parse_yaml_v1` 读取有界的 JSON 兼容 YAML 1.2 Core，不求值或读取凭据。`normalizeTemplateV1` / `normalize_template_v1` 校验并复制输入，唯一构建默认值为 `context = dirname(dockerfile)`。`compileTemplateV1` / `compile_template_v1` 保留命名资源集合并添加内部资源分类，不重建已移除的 application 或 instance 配置。

意图校验保留表达式。执行器求值后再执行已解析阶段及 Provider 校验。`registry.yaml.parameters` 使用 JSON Pointer 指向实际本地值。运行校验不读取 Registry 元数据。表达式求值和组件调用属于 CLI，目录工具不执行它们。

在本目录执行 `npm ci && npm test` 或 `python test_contract.py`。两种语言使用相同资源和源码读取用例并对比完整输出；这些检查不证明云部署通过。
