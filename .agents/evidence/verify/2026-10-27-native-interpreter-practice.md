# Managed interpreter practical use and unresolved exception replay

Result: PARTIAL

Date: 2026-10-27. Published standalone CLI0.5.7; Python client0.4.0a6;
Express managed code-interpreter-v1 (Python3.13.13). Native creation does not build
or push an image, create a management API key, or start a project HTTP server.
Source docs were based on templates1627b69177263c47886ec8d9ebdb34951c2d3388.
The existing CLI/ProviderSandbox README code ran unchanged before additions.

- [Literal CLI/SDK](2026-10-27-native-interpreter/literal-cli-sdk-process.json):
  PASS; native create, pandas42, files, complete README program, uploaded CSV
  process and downloaded exact JSON, nonzero process exit7, independent deletion.
- [Persistent interpreter](2026-10-27-native-interpreter/persistent-context-data-chart.json):
  PASS for default variable persistence41→42; isolated context100→101 while
  default stays42; context list/remove/absence; actual numpy/pandas/matplotlib;
  JSON total51.30; downloaded PNG decoded as600×300; stdout/stderr/result/error
  callbacks; standard process/file use; independent own-instance absence.
- [Earlier assertion failure](2026-10-27-native-interpreter/first-error-name-assertion-failure.json):
  FAIL retained. The service reports generic ExecutionError, not ValueError as
  initially expected. Original exception text and callback are available. The
  corrected observation is not a fix to the managed runtime.
- [Exception replay](2026-10-27-native-interpreter/exception-replay-failure.json):
  FAIL; a file increment followed by ValueError executes twice (counter2 instead
  of1). Independent cleanup passed. Owner Issue251 contains a minimal reproduction.
  This unresolved behavior prevents full template/provider qualification; Beta
  must remain even though successful data tasks work. No acceptance-index update.
- [Complete expenses.py](2026-10-27-native-interpreter/downloadable-expenses-script.json):
  PASS, unchanged script with explicit ABX account options, downloaded JSON/PNG,
  independent Pillow11.3 decode and all own instances independently absent.
  Script SHA256 2e3e71bdc63e26a61a92a383f3d1422fdc99bbf01ff2b33a8da7c289c5ed109c.
- plt.show() yielded no PNG result; IPython magic was not supported in the actual
  execution. The documented path uses Agg/savefig/files.read(bytes) instead.
- [OpenCode OpenSandbox](2026-10-27-native-interpreter/opencode-opensandbox.json):
  PASS; actual default Docker build, all29 canonical assertions and10 fresh
  documented checks, zero skipped/not-run, second supported model, native serve
  lifecycle, independent downloaded output execution and complete owned cleanup.
  Original controller/adapter inputs remained unchanged. Provider1.1.1 server and
  plugin0.5.1, exact image/source/controller hashes are in the linked receipt.
  Registry provider-index follow-up remains separate.

Configured secret values, private endpoint/IDs and raw logs are excluded. Private
attempts01/02 failed before creation on an empty proxy option;03/04 exposed inline
plot assumptions. All created instances from the attempts above were independently
confirmed absent. Default model matrix tasks are not full documented acceptance.

Local checks: python scripts/check_docs.py PASS (224 documents, zero failures);
git diff --check PASS. Current-head CI and publication remain pending.
