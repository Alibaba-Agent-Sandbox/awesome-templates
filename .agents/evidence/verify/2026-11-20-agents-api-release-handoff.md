# Verification: Agents API release identity and candidate timeout

Result: PARTIAL. Release controller regressions and bounded local role checks passed. The FC deployment, retained Session upgrade and cloud cleanup gates remain open.

Scope: base `048db39f5a865b07343ede2a93393ceab7f2df31`, canonical `agents-api-codex` release script, its tests, and generated copies with bilingual quick starts in the five peer templates. CLI timeout checked against `dcc3dd265c38ebf179cb7ea063cac0a335232cc3`.

## Reproduced defects

- Before the fix, the new regression produced seven failed subtests for generated process overrides, including empty explicit auth overrides. The script previously admitted the values and wrote private release state despite native Devs giving the process values precedence.
- A fresh Codex template failed in the actual compiled `loadResourceProject` with E2004 after `release.py init`. Direct `devs-compile` independently demonstrated `${env('NAME', '{}')}` fails with either a defined or missing environment value, while the blank default parses in both cases. The native dotenv reader preserved `\"` inside double-quoted JSON. The same structured value in a single-quoted assignment arrived intact. Both changes were required for native input to reach the FC environment as valid JSON.
- Two replacement-identity subtests reached the candidate version step after the fixture recorded a timer operation against the previous Dispatcher's name. During replay, one fixture has the replacement before publication and the other changes identity before the old timer update.
- Named-resource deploy passed its default `600` seconds to the gateway success action. Candidate `release.py publish` can use a 900-second child budget, with a 780-second smoke default, plus its FC operations. The supported `--build-timeout 1800` stays below the executor's 3600-second limit and applies to each action.

## Executed checks

- Installed candidate client and server packages as editable source, alongside the checked-in template requirements. No public a8 installation was used.
- Ran `python -m pytest -q scripts/test_agents_api_family.py agents-api-codex/scripts/test_release.py agents-api-codex/test_smoke.py` on Python 3.11.15 and 3.13.13. Both produced 37 passes and one `RemoteProtocolError` in the normal local role HTTP test. Original assertions remain intact.
- An independent standard-library HTTP/1.1 server sent `Connection: close`; the client observed that header removed in this environment. With `httpx` pooling it reproduced the second-request disconnect. With zero keepalive connections the same fixture returned all five expected 200/401 responses. The full unchanged family assertions first passed with an external `httpx.Client` zero-keepalive shim, then passed again without a shim in a dedicated PID/network namespace with loopback enabled. Both runs passed 38 tests and 34 subtests.
- A clean user, PID and network namespace with only loopback enabled also ran the
  unchanged family tests on Python 3.13.13, passing 38 tests and 34 subtests without
  the HTTP client shim.
- `python scripts/sync_agents_api_templates.py --check`, `python scripts/check_template.py --all` and `python scripts/check_docs.py` passed in this scoped run. The catalog checker reported zero claimed spec failures. All six English and Chinese quick starts use the same confirmed timeout flag.
- `python .agents/evidence/verify/2026-11-20-agents-api-release-handoff/check-native-release-env.py --cli <built-cli-checkout>` verified the actual CLI resource parser before and after local release init for all six templates, with both documented input sources (12 cases). Each prepared Worker, Dispatcher and Gateway received the saved function/revision identity, plain JSON policy and Worker routing, and matching private runtime token. All roles used the same region as the prepared template; Worker and Dispatcher received the matching Sandbox runtime region without a separate input. The initial parser saw empty generated values. The probe used synthetic deployment inputs and did not call FC or the model service.
- `alibabacloud-fc20230330==4.8.3` method signatures were checked locally for function read/update, trigger read/create/update/delete, alias read/create/update, and version publish. The pinned API types support the script's current invocation shapes.

## Hosted evidence and cleanup

Tracked by [Issue 309](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309) and [PR 312](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/312). The release-controller probe performed no real FC mutation, credential creation,
model task or database allocation. See the [separate Qwen model verification](2026-11-20-agents-api-qwen-model.md). Test-created project directories, loopback processes and SQLite state were cleaned up. The previous Dispatcher regression checks the controller's preflight and immediate readback boundary. It does not establish a remote compare-and-set operation or retained-Session acceptance.
