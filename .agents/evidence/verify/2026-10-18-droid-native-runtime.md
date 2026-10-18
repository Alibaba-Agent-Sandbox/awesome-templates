# Verification: Droid background installation on native SDK

- Date:2026-10-18
- Result:PASS for the source-runtime scope only.
- Controller SDK:76268024fb6e046b78ebc0f797ebcaf162ef2a55, accepted by
  https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/57.
- Command/runtime input hashes and source wheel hash are in the paired JSON.

The real Express base sandbox installed @factory/cli0.241.1 with short background
status polls, started the uploaded public command server, passed external SDK
health, exact Droid version/keyless setup and the external HTTP suite.
All nine recorded acceptance/cleanup checks passed, controller exit0.
No model key was forwarded or model call made. Owned sandbox cleanup passed;
independent readonly platform readback found zero source-runtime-droid resources.

This completes the missing Droid source-runtime reproduction from SDK Issue35:
https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/35.
It establishes current behavior after retiring held local sessions; it does not
prove the exact historical root cause. No Dockerfile image, canonical template
deploy L2 or model L3 pass follows. tested_on/provider badges remain unchanged.
Raw installation/server logs and temporary credentials are not published.
