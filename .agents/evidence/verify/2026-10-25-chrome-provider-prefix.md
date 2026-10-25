# Chrome provider-prefix correction

Date: 2026-10-25
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/217

Public Chrome 1.0.5 failed the full external controller at its native WebSocket handshake after 16 successful assertions; independently confirmed sandbox/prepared-resource absence is recorded in Actions run 40193575006. The 46-source follow-up 40193856040 retains another Chrome failure. Neither is overwritten by this candidate.

Local candidate: `python -m pytest chrome/test_protocol.py chrome/test_commands.py -q`: 26 passed. Before installing the template's existing hash-locked dependencies the first invocation failed due to missing aiohttp, Pillow and Crypto; after `uv pip install --require-hashes -r chrome/requirements.lock` the suite passed. No dependencies or lockfile changed.

Run the four new route regressions against the original `chrome/cdp.py`: 3 failed, 1 direct-path control passed. The failures cover both prefixed CDP paths and noVNC construction. Candidate tests use actual local HTTP and WebSocket transports, with synthetic application and gateway header values. They do not establish real browser/cloud acceptance.

Pending: candidate complete native controller, current-head CI, merged public-source rerun and independent cleanup receipts.

`python scripts/check_docs.py`: 222 documents, zero link failures. `python scripts/check_template.py chrome`: conformant. Candidate source and published workflow modes now install the same existing external-controller dependencies after package installation; no public option or dependency version changes.

Candidate cloud PASS: [Actions 40195245899](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40195245899), reviewed source 1d31a2acd62c524f76d47bd43f0c24ed389d6782. CLI and Python distributions were built from exact reviewed source commits (versions 0.5.1/0.4.0a1); this is not a fresh public-package pass. The actual OpenSandbox endpoints for app/CDP/noVNC each had a nonempty provider path prefix. Complete native controller: 30 passed, zero failed, zero skipped. This includes real headed browser navigation, original CDP version/WebSocket, authenticated RFB pixels, actual VNC pointer input, independent DOM state, screenshot byte/hash/PNG checks, post-return observation and owned desktop listener/private-state cleanup. The CLI, SDK and host HTTP smoke also passed. Owned sandbox and prepared artifacts were independently absent; zero cleanup failures/retained/uncertain resources. [Sanitized receipt](../../../chrome/evidence/public-opensandbox-prefix-candidate-2026-10-25.json) preserves artifact digest and exact inputs.

Current-head CI and merged public-package/source rerun remain pending. A candidate pass does not extend to Express or a later dependency revision.
