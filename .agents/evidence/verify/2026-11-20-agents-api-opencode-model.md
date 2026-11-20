# Verification: Agents API OpenCode real model in the managed bridge

- Date: 2026-11-20
- Change: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/312
- Result: PARTIAL
- Runtime: paired `0.4.0a8` source at [SDK 0585bdb](https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/0585bdb2b24d8efab215ad0965246820b50f8362)
- Native Harness: released OpenCode 1.19.5, the pin in the recipe's descriptor
- Model: `qwen3-coder-flash` through the configured OpenAI-compatible model endpoint

An isolated local ManagedBridge started the pinned OpenCode executable and sent a
synthetic two-row CSV through its normal SHA-256 and base64 input path. The first
real model turn read that CSV and wrote `outputs/total.txt` with value 5. The
second turn read that file and wrote `outputs/double.txt` with value 10. Both
turns reached completed receipts. The probe independently read both files and
checked equality of the nonempty native Session ID across turns.

The executable was invoked in a Bubblewrap user/PID namespace with its package
files read-only and an owned writable working directory. The system CA file
verified the configured endpoint over TLS. The Runtime Session was deleted and
temporary environment data was removed. No FC, Sandbox, RDS, or management key
was created.

This is a local real-model result, with published images, FC networking and
retained-Session upgrade still to verify. The OpenCode v1 limitation on live
tool-start observation remains.
