# QM and SDK backend research

Status: PARTIAL. Date2026-10-21. Original source deef9b8b1e2b85bd4166dd833604bb31bcb8e255, Git tree2703entries/truncated=False. Read-only pinned original README/package/default Docker backend/original Sandbox interface/E2B client/router/exec base/native harness/tool context/custom provider wiring inspected. Core buildApp lacks a sandbox override; exported createPiHarness and createToolContext remain potential native embedding seams. PostgreSQL is optional for in-memory sessions; full durable multiplayer services are not being inferred.

Original selected harness supports delegateWork=False and disables optional control/scratch/owner-auth/reach tools; no sub-agent dispatch is authorized. Original custom provider registry explicitly supports openai→openai-completions with private keys resolved separately. Actual Node SDK public ServerClient.files.upload/download and process.shell can back execution/file methods; do not invent cloud Sandbox.create in this HTTP-only Node SDK. Outer creation remains actual Python SDK Sandbox.create. No implementation/native/kernel/model/cloud acceptance yet.

Original Node SDK0.1.0 npm metadata returned404; exact public source90b5187dca84fca78d75d3045896482540641c72 can be built through its own npm lock and build script. No unpublished package success claim. Original immutable archive provenance below; controller-measured hashes, not upstream-published digests.

```json
{
  "qm": {
    "url": "https://codeload.github.com/yc-software/qm/tar.gz/deef9b8b1e2b85bd4166dd833604bb31bcb8e255",
    "source_commit": "deef9b8b1e2b85bd4166dd833604bb31bcb8e255",
    "size": 10625243,
    "sha256": "40fb0d69319753a1cfab2dc8a1e8574d206e92589d26b264e768e94fa9109b4e",
    "digest_basis": "controller measured original immutable public source archive; not upstream-published checksum"
  },
  "agent-sandbox-node-sdk": {
    "url": "https://codeload.github.com/Alibaba-Agent-Sandbox/nodejs-sdk/tar.gz/90b5187dca84fca78d75d3045896482540641c72",
    "source_commit": "90b5187dca84fca78d75d3045896482540641c72",
    "size": 27746,
    "sha256": "6b51e849090656de448812dbc5b08bb0a7ac0a981241739e116597cd8383cfd6",
    "digest_basis": "controller measured original immutable public source archive; not upstream-published checksum"
  }
}
```

Public archives retained only while this integration is active. No cloud resource or model call created by this research; no model-generated code executed on operator. Full native/image/Express/SDK/model and independent cleanup gates remain NOT RUN.

Authored SDK backend prepared (not a completed template): real original compiled Node SDK ServerClient, literal-loopback/independent-Bearer guard, original-QM-compatible execution/files/provision/teardown, bounded path helper and per-tool nonce/pidfd-owned minimal-environment process runner.7actual SDK-over-authored-local-HTTP transport/boundary tests PASS,7authored filesystem/real fixed subprocess/timeout tests PASS1.10seconds. These are local fixtures, not native QM or Express/model acceptance. Compile checks pass. Read-file absence maps to null and actual exit124 is not falsely classified as a timeout. Returned tool streams64KiB each; file limit1MiB. More original interface/runtime coverage remains necessary.

Original SDK trusted build on operator Node22.22.2 (SDK minimum20; native QM requires24.15+ and was not run here): npm ci under default global npmmirror failedTLS; explicit official registry alone also failedTLS. Local Node help verifies --use-system-ca; retry with that system trust store and unchanged official source/lock, official registry and full TLS verification succeeds, then original npm run build succeeds. No certificate validation bypass, model call or QM-generated code execution.

Original Node24.16.0 Linuxx64 archive57023429bytes verified against official archiveSHA2562faf6a387e9b62b888e21c54f01249fb27537ffecf1842f29f4c919d0a59a0ff; original executable123438592bytes/controller-measured SHA256b2959781cc5a74c357ffa02367efa8a0330cbb1c9cb347732fdfaaaca381cbcd. QM source archive2704members/30042365expanded bytes includes four safe internal original symlinks; installer preserves bounded original links without allowing escape. Prepared source installer checks exact archive/source/native identities and keeps original notices. No install/image/cloud/native-model claim yet.

Installer traversal/symlink/hardlink rejection and safe internal notice-link preservation regressions now11PASS1.12seconds; actual original SDK HTTP unit controls7PASS after idempotent teardown refinement. Native worker adapter prepared to use unchanged original createPiHarness/createToolContext/createLocalWorkspaceStore/createAclStore/custom-provider registry. It is not executed on operator and remains unqualified pending native image/Express runs. Original sessionTools is False without sessionSyscalls; delegateWork=False, control/scratch/owner-auth/reach/sandbox-resources disabled, only execute/files read/write approval identities allowed. No sub-agent or external delivery started. Native worker stdout only returns final reply/fixed metadata; model transcripts are not emitted.

Completed source preparation: both standalone experimental templates now include full bilingual14section READMEs,7section designs, pinned original QM/SDK locks and notices, scalar APIs, source-bound three-archive steps profile and CI regressions. Native worker uses original noTools=builtin/customTools from unchanged createPiHarness; SessionEntry/session IDs preserve original API contract. Actual original SDK self data plane defaults9000 and WORKSPACE/home/user/app consistently with canonical harness; separately configured9010must use its matching SDK base/Bearer. Public file text/read32KiB, library files1MiB, directory1024names/32KiBJSON; per-tool64KiBstreams/deadline120seconds, separate native worker256KiBstreams/request. Archive installer supports exact original safe internal links and rejects escape/hardlinks. Safe native failure phases/classes/codes/module identifiers/numeric counts are exposed without raw stderr/task/key content.

Executed preparation checks:37wrapper/path/process/archive/anonymous-request/privacy controls PASS1.27seconds;14original-native completion-metadata controls PASS0.06seconds;7actual original SDK-over-authored-HTTP controls PASS145.534ms/0SKIP. Both source-only HTTP controllers7PASS0FAIL/nativeSKIP; qm model NOT_RUN.57spec-tool tests PASS13.700seconds; strict all-template0violations;195public Markdown documents0local-link failures, four actual SDK snippets compile. These are local/source controls only. Native image/SDK-created Express/fullHTTP/genuine original model/owned cloud cleanup NOT RUN. No benchmark/model-generated code ran on operator. Immutable preparation/wire regressions follow after committing exact COPY inputs.

First immutable-source steps/wire suite atdcfab391ed934297113546b42cc1449149f303a1:65controls PASS,2new QM wire checks FAIL129.30seconds; each prepared native recipe15199bytes exceeds unchanged15000guard. No cloud operation performed. Revised Docker profile combines the four reviewed package/lock files in one COPY, compares each byte-for-byte against its unchanged verified original source archive counterpart before npm ci, then removes only the owned review-lock staging directory. Original archive/native/package/source hashes and strict wire guard remain unchanged; revalidation required.
