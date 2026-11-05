# Managed template network, database trust and cleanup documentation

Date: 2026-11-05 UTC. Issue295 / Draft PR296:
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296

This is a documentation follow-up to the source verification record. Historical
source/image/package failures and pending public-release gates are not rewritten.

## Reviewed changes

Read the actual CLI command registration, private binding resolver, FC function
properties/readback, public summary and image cleanup implementation. The CLI
owner independently confirmed the parameter and cleanup boundaries before this
follow-up. The parent and runtime/CLI owners independently reviewed the need for
private-network and certificate-only trust inputs before implementation.

Updated both template README languages and both author references:

- State remains a string DSN or a private object with databaseUrl and optional
  vpcConfig/databaseCa. The YAML schema still stores only a binding reference;
  no duplicate YAML networking or general file-reference DSL is introduced.
- VPC references select existing same-region VPC/vSwitch/security-group resources
  for the three FC roles. The profile sets and reads back internetAccess:true;
  this setting does not independently prove connectivity. No network/NAT/routing
  resource creation is promised. Network access is borrowed and operator-owned.
- databaseCa accepts a PEM string, env reference or the narrowly scoped file leaf.
  Relative files use the binding JSON directory (CWD for environment-only inputs);
  examples recommend absolute host paths. Only regular non-symlink files, at most
  64KiB and1..8 valid certificate blocks are accepted; private keys/other content
  are rejected. It configures Server trust with DSN verify-full preserved, never
  guest/image/plan/receipt content. No vendor CA material is embedded in a recipe.
- The CLI handles the durable database identity. No user-facing expectedStateId
  field or manual identity preparation is documented.
- The full retire command uses current receipt, --revision, --bindings and --yes.
  clean-build takes a build receipt and --yes only; builds used by any Apply must
  use app Destroy/Retire. Borrowed Server images are preserved. Retained Sandbox
  image artifacts and historical receipts remain an explicit manual cleanup scope.

The minimal bindings.example.json is unchanged; optional configuration is shown
as a usable private State-object replacement in the README, not invalid JSON
comments or fake manifest fields.

## Actual verification

- Parsed the bilingual optional VPC JSON fenced examples successfully.
- `python scripts/check_docs.py`:232 current documents, zero local-link failures.
- `python scripts/check_template.py agents-api`: conformant.
- `git diff --check`: passed.

Only documentation and engineering records changed in this follow-up. No new
cloud/model run, database provisioning, TLS/CA connection or image build was
performed by these document checks. Shared-runtime and CLI execution evidence
belongs to their owning repositories and the parent integration controller.
Current public a6 recipe pins remain unchanged until a compatible SDK is
actually published; a source install is not that public-recipe gate.
