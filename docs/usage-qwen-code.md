# Qwen Code usage

This legacy documentation URL remains available. The canonical guide is now maintained with the template:

- [English guide](../qwen-code/README.md)
- [中文指南](../qwen-code/README.zh-CN.md)
- [Design and acceptance plan](design/qwen-code.md)

The template uses generation 2, a non-root Alibaba FC base and Qwen Code 0.23.0. The public `max_turns` argument maps to upstream `--max-session-turns`; the previous `--max-turns` invocation was invalid. Keys must reach the named-command server before it starts; see [runtime configuration](runtime-environment.md) for prewarmed services. Both `OPENAI_API_KEY` and a `DASHSCOPE_API_KEY` fallback are supported. Coding acceptance requires actual source edits, new artifacts and independent tests; a response marker alone is insufficient.

旧文档链接保留。使用方式、参数、HTTP/SDK 示例、认证说明、错误契约、验收限制和贡献步骤统一维护在上方双语模板指南中。旧的 Python 基础镜像、root 配置、`--max-turns` 和 marker-only 验收说明已不适用。
