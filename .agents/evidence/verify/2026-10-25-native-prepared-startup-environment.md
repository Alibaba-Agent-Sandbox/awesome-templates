# Prepared native startup environment verification

Date: 2026-10-25
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/227

## Why the previous correction was insufficient

The public4229 control using official CLI0.5.6 and SDK0.4.0a6 failed in14.378seconds at the first agents_version CLI call with E3000 / RuntimeError, codex is missing. Its generated manifest and launch manifest both contained the expected nonempty PATH and retained the original startup/readiness. No smoke success or guest-version readback is inferred from that control. Its [unaltered receipt](../../../agents-cli/evidence/verification-steps-2026-10-25T222455Z.json) records independent sandbox and prepared-template absence with no unresolved ownership.

PR229's local108PASS and earlier environment mapping assertions are preserved as historical local evidence; they did not prove successful native application startup. No merged evidence is rewritten.

## One bounded same-instance diagnostic

The [filtered diagnostic](2026-10-25-native-env-inheritance-diagnostic.json) and its [unaltered runner receipt](../../../agents-cli/evidence/verification-steps-2026-10-25T223809Z.json) used unchanged public4229 source, official CLI0.5.6 and public SDK a6. An operator-only in-memory overlay added one nonsecret marker to the temporary managed manifest. No public source file changed, and no application restarted.

Default SDK execution and the unique token-matched application were UID1000. Both inherited the creation marker and correct application token, but PATH omitted the installed Node prefix. Absolute Node/Codex/Qwen files existed, resolved to reviewed installation paths, were executable0755 and returned expected versions24.16.0/0.162.1/0.23.0. The runtime commands matched source and the independently read server package was a6.

Only the same sandbox's explicit process environment then changed PATH and a nonsecret marker. All binary lookups became correct. The original application stayed unchanged, and another default process returned to the original creation marker/base PATH, proving no global environment mutation. The /proc/environ observation is an initial exec snapshot, used together with the process observations and source trace; it is not claimed as an arbitrary live Python environment view. No permission/read error occurred.

The original CLI E3000 remained the primary failure. The diagnostic rethrew it and the existing finally path independently confirmed both owned resource absences. Raw environments, credentials, native identifiers, process IDs and private URLs are not included. This evidence isolates a PATH difference; it does not establish that all creation environment or authentication is broken.

## Local correction and remaining gates

The correction changes only the existing prepared-reference helper and its regression module: supplied runtime environment wraps original startup/readiness using the existing production native-steps mechanism. Empty secret declarations are omitted from the command; the inherited application token is not frozen or replaced. The image consumer with runtime_env=None is unchanged.

PASS: the new actual-shell regression fails against original4229 with exit127 and passes after correction. The integrated preparation/image/archive/public-launch/actual-installed-parser suites pass109 tests in5.73seconds with the official CLI0.5.6 binary. The regression also verifies startup/readiness, literal quote/dollar preservation, manifest priority, original source immutability and inherited empty-secret values. These are local checks, not cloud acceptance.

Independent candidate review, a new actual full agents control, latest-head CI and final native supplemental matrix remain pending here. No public CLI/SDK version or business template input is changed. Arbitrary public prepared-reference PATH inheritance remains a separate observed limitation rather than being claimed repaired by this adapter.
