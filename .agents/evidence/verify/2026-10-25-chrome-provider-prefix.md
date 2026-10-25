# Chrome provider-prefix correction

Date: 2026-10-25
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/217

Public Chrome 1.0.5 failed the full external controller at its native WebSocket handshake after 16 successful assertions; independently confirmed sandbox/prepared-resource absence is recorded in Actions run 40193575006. The 46-source follow-up 40193856040 retains another Chrome failure. Neither is overwritten by this candidate.

Local candidate: `python -m pytest chrome/test_protocol.py chrome/test_commands.py -q`: 26 passed. Before installing the template's existing hash-locked dependencies the first invocation failed due to missing aiohttp, Pillow and Crypto; after `uv pip install --require-hashes -r chrome/requirements.lock` the suite passed. No dependencies or lockfile changed.

Run the four new route regressions against the original `chrome/cdp.py`: 3 failed, 1 direct-path control passed. The failures cover both prefixed CDP paths and noVNC construction. Candidate tests use actual local HTTP and WebSocket transports, with synthetic application and gateway header values. They do not establish real browser/cloud acceptance.

Pending: candidate complete native controller, current-head CI, merged public-source rerun and independent cleanup receipts.
