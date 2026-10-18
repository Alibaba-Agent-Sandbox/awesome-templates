# Template acceptance review: 2026-10-18

This is a dated snapshot, not a release or provider certification. Main and existing drafts contain **23 product templates** in total. This documentation branch builds on the 16 directories in PR #82; other templates live in their linked owner PRs. Each row applies only to its exact revision.

| Template | Source PR / revision | Image and normal CI | Current canonical L2 |
|---|---|---|---|
| agents-cli | [#101](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/101) `d7e74574` | Corresponding image/local jobs passed; see PR | Pending |
| amp | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| browser-automation | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| claude-code | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| codex | [#97](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/97) `2f4d33be` | Corresponding image/local jobs passed; see PR | Pending |
| codex-agent-api | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| deepseek-harness | [#100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100) `ff0106c6` | Corresponding image/local jobs passed; see PR | Pending |
| droid | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| gemini | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| hermes-agent | [#100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100) `ff0106c6` | Corresponding image/local jobs passed; see PR | Pending |
| node-web | [#105](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/105) `7689edae` | Corresponding image/local jobs passed; see PR | Pending |
| openclaw | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| opencode | [#104](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/104) `8bb61cfe` | Corresponding image/local jobs passed; see PR | Pending |
| python-hello | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| qoder | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | Corresponding image/local jobs passed; see PR | Pending |
| qwen-code | [#100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100) `ff0106c6` | Corresponding image/local jobs passed; see PR | Pending |
| pi | [#100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100) `ff0106c6` | Corresponding image/local jobs passed; see PR | Pending |
| aider | [#102](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/102) `50c11425` | Corresponding image/local jobs passed; see PR | Pending |
| swe | [#96](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/96) `70ac5a6e` | Corresponding image/local jobs passed; see PR | Pending |
| osworld | [#94](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/94) `9a53b56c` | Corresponding image/local jobs passed; see PR | Pending |
| ocr | [#103](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/103) `a4a18b0d` | Corresponding image/local jobs passed; see PR | Pending |
| media-tools | [#106](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/106) `a7b8bdca` | Corresponding image/local jobs passed; see PR | Pending |
| document-tools | [#107](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/107) `b06359f3` | Corresponding image/local jobs passed; see PR | Pending |

Image builds remain separate from source-runtime HTTP/model evidence. All templates have CLI, Python SDK and HTTP POST documentation; use each owner PR's bilingual README for new templates and exact arguments. Source-runtime diagnostics do not prove that revision's Dockerfile passed the canonical deploy. Unrun native providers cannot receive a pass, and historical tested_on cannot transfer to changed versions.

The [PR #92 canonical controller](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/92) remains default-disabled. Its current selector covers its fixed 17 inputs, **not all 23 templates**. This machine lacks Docker; temporary cloud configuration storage in GitHub Actions also needs explicit separate approval. Until authorization, reviewed revision and template inputs are resolved, `all` cannot mean every current template, and these draft PRs cannot all be declared merge-ready.

Other providers (native E2B, Cube, OpenSandbox and container edition) require their own actual environment, image adaptation and credentials. Express credentials must not be forwarded to E2B. Existing image-URI support is not native template-deploy acceptance.

Development tiers are defined by the [specification](template-spec.md); calling and ownership guidance is in [Using templates](using-templates.md).

[中文](verification-2026-10-18.zh-CN.md)
