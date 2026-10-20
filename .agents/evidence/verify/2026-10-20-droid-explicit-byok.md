# Droid compatible BYOK preparation — 2026-10-20

Status: PARTIAL; [Issue19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19).

Official npm0.241.1 metadata and native archive SHA512 verified. Unmodified native
binary292,157,408bytes, SHA256 matching [upstream.json](../../../droid/upstream.json).
Actual keyless version0.241.1 and exec help confirm custom models, JSON output,
low autonomy, disabled builtin skills and stdin prompt input. Proprietary
UNLICENSED metadata is retained; no native binary committed.

An initial synthetic local non-streaming fixture failed because native requested
streaming; retain this failure. Corrected owned SSE fixed-response fixture:
actual native exit0, terminal success, positive1turn, exactly one owned
`/v1/chat/completions` request with the exact synthetic model/Bearer. No Factory
credential or real model key was provided; no generated code or tool call ran.
Temporary HOME was removed. This establishes a supported native account-free
BYOK route; it does not establish cloud or real-model acceptance. It supersedes
the earlier assumption that Factory credentials are the only route, without
rewriting historical blocked evidence.

Authored regressions:59PASS in9.45s across existing process/Factory protocol and
new BYOK/controller suites. Both README languages conform;171public Markdown
documents have0local link failures. Current source image, Express SDK-created
canonical steps/full HTTP, actual approved model coding, independently preserved
original tests/held-outs, and owned cloud cleanup: NOT RUN. `tested_on: []` and
experimental status remain. Legacy Factory real-model acceptance is unverified.

Current wrapper genuine-native probe also passed: [wire proof](2026-10-20-droid-native-synthetic-wire.json).
It executes the unchanged verified native binary with this wrapper's anonymous
stdin, private model profile and low-autonomy argv. The research fixture supplies
the binary path only; this is not image-path/cloud qualification. Native exit0,
terminal success,1turn, exact fixed response and one exact owned model/Bearer
request; private HOME/process state absent. An intermediate probe returned native
success but mismatched synthetic auth because project-level settings influenced
model selection. No real key was provided. Fixed by pinned native `--settings`
runtime priority, then reverified against the same conflicting project fixture.
BYOK file tools are restricted to original Read/Edit/Create/Grep/Glob/LS; native
Execute/subagent/MCP tools are excluded. Required cloud repeat before real key.

Final local strict all-template check:0violations. Full spec regressions:57PASS
in13.082s. Source-only actual HTTP server:7PASS/0FAIL,1explicit missing-native
SKIP, model NOT_RUN. First local server launch omitted the task venv PATH and
failed missing `agent_sandbox`; corrected PATH launch is the result above.
Both languages' two Python snippets compile; no cloud claim from these checks.

Repeated collision probe showed runtime settings alone were insufficient when
selecting a duplicated raw-model alias from an existing project's custom models.
Again only a synthetic key was used. Final wrapper starts native Droid in its
own private temporary Git root, passes private runtime settings, and identifies
the selected project by an absolute path in anonymous task context. Target native
project settings are not loaded automatically. This avoids that configuration
collision without rewriting caller files. Actual native tool-bound probe and
[independent repeat](2026-10-20-droid-native-synthetic-tools-repeat.json) both PASS:
[current tools/wire proof](2026-10-20-droid-native-synthetic-tools.json), exactly one
correct model/Bearer request, terminal positive-turn success, and exactly the six
permitted native file tools. Current wrapper SHA is recorded in those proofs;
the earlier wire proof retains the superseded wrapper's narrower historical scope.
