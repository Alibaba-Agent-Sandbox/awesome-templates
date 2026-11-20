# Verification: Agents API Qwen Code real model in the managed bridge

- Date: 2026-11-20
- Change: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/312
- Result: PARTIAL
- Runtime: source of the paired `0.4.0a8` candidate at [SDK commit 0585bdb](https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/0585bdb2b24d8efab215ad0965246820b50f8362)
- Environment: Node.js 22.22.2, CPython 3.13.13, native Qwen Code 0.23.0 (original) and 0.28.0 (fixed),
  configured `qwen3-coder-flash` Chat Completions service.

## What was verified

The existing configured model endpoint returned 200 for model discovery. An isolated
local ManagedBridge executed two actual model turns through `qwen-code`. The prompt
and input file were synthetic. The bridge used its ordinary native subprocess,
receipt, Session resume and artifact paths.

| Case | Result |
| --- | --- |
| Open the uploaded two-row CSV and save the sum | Turn completed and independently read `outputs/total.txt` containing `5`. |
| Continue the same native Session and double the previous result | Turn completed and independently read `outputs/double.txt` containing `10`. Native Session ID equality checked in memory. |
| Original Qwen Code 0.23.0, default Node trust store | A certificate trust error was rendered in output and the native CLI reported success. No artifact was produced. |
| New Qwen Code 0.28.0, same default Node trust store | The same failing connection produces a failed managed terminal receipt and no artifact. |
| New Qwen Code 0.28.0, system CA | Both model turns and artifact assertions passed. The CLI uses `NODE_EXTRA_CA_CERTS` for the local system CA, preserving TLS verification. |

The first and second reviews traced the type loss to the upstream
[0.23.0 non-interactive runner](https://github.com/QwenLM/qwen-code/blob/98a9c964158697dd5631d15a62174684ff7bbb53/packages/cli/src/nonInteractiveCli.ts#L2422).
The [0.28.0 runner](https://github.com/QwenLM/qwen-code/blob/895dfca8ff125ac0e16372edacd4653322c02147/packages/cli/src/nonInteractiveCli.ts#L3349)
emits a failed terminal result in structured output. The Qwen family recipe now
pins 0.28.0. The managed adapter keeps typed terminal status and never classifies
an error by matching assistant prose.

## Reproduction and cleanup

Install the pinned native CLI with `npm install --prefix <private-directory>
@qwen-code/qwen-code@0.28.0`. Use the paired SDK source and the selected model
endpoint. Run ManagedBridge with an isolated local working directory, a private
receipt database, the system certificate trust store and only the configured
model credential. Pass the first input with SHA-256 and base64 bytes and open the
second submission against the same Session. Verify both artifact bytes before
closing the Session.

The real run used a read-only package environment and a private writable project
under Bubblewrap user/PID separation. Model configuration was supplied in the
child environment. No cloud resources, cloud management keys, stored model
credentials, or application release were created. The owned Runtime Session
was deleted and its per-run native CLI home removed.

## Not verified

This result covers Qwen Code through the local managed runtime. It does not
exercise a published Guest or Serving image, real FC release, retained Sessions
during upgrade, or the other five Harnesses' real model accounts.
