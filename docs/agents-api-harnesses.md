# Agents API Harness guide

[中文](agents-api-harnesses.zh-CN.md)

Use one Gateway for tasks, sessions, files and artifacts. Each recipe uses the
same [API contract](managed-agents-api.md); the native Harness and credentials differ.
These development candidates require the not-yet-published paired runtime0.4.0a8
and YAML v1 CLI. Older runtime releases cannot provide these adapters.

| Harness / recipe | Credential | Endpoint / model | Model protocol |
| --- | --- | --- | --- |
| [Codex](../agents-api-codex/README.md) | `OPENAI_API_KEY` | `OPENAI_BASE_URL`, `OPENAI_MODEL` | Responses |
| [Qwen Code](../agents-api-qwen-code/README.md) | `OPENAI_API_KEY` | `OPENAI_BASE_URL`, `OPENAI_MODEL` | Chat Completions |
| [Claude Code](../agents-api-claude-code/README.md) | `ANTHROPIC_API_KEY` | `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL` | Messages |
| [Qoder](../agents-api-qoder/README.md) | `QODER_PERSONAL_ACCESS_TOKEN` | `QODER_MODEL` (default `auto`) | Native Qoder service |
| [OpenCode](../agents-api-opencode/README.md) | `OPENAI_API_KEY` | `OPENAI_BASE_URL`, `OPENAI_MODEL` | Explicit compatible provider, v1 CLI |
| [DeepSeek Harness](../agents-api-deepseek-harness/README.md) | `DEEPSEEK_API_KEY` | `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` | Messages |

## Choose and configure

A model key is not automatically usable by every Harness. Codex needs actual
Responses tool rounds. Qoder uses a native PAT and an account-authorized model;
BYOK depends on the [official plan and account configuration](https://docs.qoder.com/cli/custom-models).
OpenCode pins its v1 CLI; its v2 CLI is a different product. The DeepSeek recipe
uses [official DSH](https://github.com/deepseek-ai/deepseek-harness), distinct from
this repository's older `deepseek-harness` tool loop. DSH uses a Messages endpoint
such as `https://api.deepseek.com/anthropic`.

Put credentials and the model in the selected project's private `.env`. Edit
region, budgets and native FC props in `template.yaml`. Initialization forms live
in `registry.yaml`; local execution does not depend on them. Use distinct application
names and private deployment records. Select the matching recipe instead of only
changing `vars.adapter`: its Guest installs that specific Harness.

## Shared protocol and limits

Discover allowed models at `GET /v1/models` and actual supported behavior at
`GET /v1/agent-sandbox/capabilities`. Session creation returns201; input returns202
and a Submission header. Ordinary input while busy returns409; an explicit
Submission queues a later turn. This differs from OpenAI mid-turn steering.
The shared entry does not provide function-result submission, remote MCP,
subagents or automatic review. Native tool progress varies; receiving final text
does not establish token streaming.

Close releases compute and retains committed results; DELETE removes public
resources. Poll cleanup Operations until successful. Remove an application with
its `python scripts/release.py destroy`. Existing databases, roles, networks and
user-supplied image tags remain user-managed.

Each recipe documents CLI deployment, Python `httpx` and curl. There is no
dedicated Gateway SDK. Business clients need neither a Sandbox SDK nor individual
Sandbox endpoints. This subset does not promise full OpenAI SDK compatibility.
