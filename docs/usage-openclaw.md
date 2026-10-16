# OpenClaw gateway usage

The current bilingual usage and full command contract live with the template:
[English](../openclaw/README.md) · [简体中文](../openclaw/README.zh-CN.md).

`gateway_start`, `gateway_status`, `gateway_health`, and `gateway_stop` manage an
owned background `openclaw gateway run` process. The legacy `gateway` command is
an explicit `action=start|status|health|stop` alias; it no longer executes
`openclaw <action>`. A gateway token is required for start; model keys are not
required for gateway readiness. Local gateway success is not coding/model L3.

See [design](design/openclaw.md), [template spec](template-spec.md), and
[Issue #20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20).
