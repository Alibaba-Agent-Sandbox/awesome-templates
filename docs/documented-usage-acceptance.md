# Complete a template's documented task

[中文](documented-usage-acceptance.zh-CN.md)

Building an image and creating a template prove preparation, not usable business
behavior. Follow the template README from a fresh published CLI/SDK installation:
configure the provider, separate application token and required account/model
credentials, launch, execute the documented task, inspect/download its results,
and release the owned resources.

The default public-launch runner deliberately removes blank manifest environment
variables and disables model calls. To run actual model/business controllers,
explicitly configure only the variables described by that template and use:

```bash
python scripts/public_launch_e2e.py opencode \
  --provider alicloud-express --source ./opencode \
  --application-controller --real-usage --build-timeout 3600 \
  --output opencode-real-usage-attempt-1.json
```

This mode retains explicitly configured manifest environment at runtime, enables
real model calls, requires the controller and rejects SKIP/NOT RUN even when the
controller exits zero. It may call paid APIs. Cloud management credentials are
not forwarded to the controller; model keys belong in runtime configuration,
never Dockerfiles, build arguments, receipts or logs. Existing package and source
identity checks, service authentication and owned resource cleanup still apply.
Cursor/Devin invalid-key or missing-account fixtures are disabled in this mode.
Configure genuine account credentials; a generic compatible-model key cannot
replace a vendor account where the tool requires one.

Passing this controller alone is not automatic complete qualification. Compare
live command discovery with every callable command (including hidden commands),
custom route and enabled SDK/native interface. Successfully exercise each method
and its results. Follow the README task literally, including file transfer and
configuration. For model tools, demonstrate selecting a second supported model,
endpoint/API key configuration and the documented login mechanism. Check an
actual response/artifact, not just the selected model string. For coding tasks,
require a source edit, a new artifact, unchanged original tests and independent
held-out assertions. Record any unsupported operation or account requirement.

Run OpenSandbox with its documented provider configuration and the template's
explicit portable build profile where required; do not silently change providers
or image recipes. Native managed entries require their owning provider.

Preserve each attempt as new dated sanitized engineering evidence. Record exact
inputs, installed packages, provider, full interface coverage, task outcome,
failures/skips and independently confirmed cleanup. A current complete pass on
at least one provider may be reviewed by Registry to remove Template Beta.
Historical or partial passes do not qualify. Delete only task-owned sandbox,
template and image resources; remove unused completed local image/cache data
sequentially when disk is limited.

Write each completed template experience as a practical case in the
[blogs repository](https://github.com/Alibaba-Agent-Sandbox/blogs): the reader's
problem, installation and configuration, runnable workflow, observed outcome,
extensions and limits. Keep the execution evidence in engineering records. Do
not publish unexecuted results or describe the article as a test report.
