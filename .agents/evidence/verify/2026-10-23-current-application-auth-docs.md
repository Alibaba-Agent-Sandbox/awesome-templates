# Current application authentication documentation

Result: PASS (documentation scope).

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/194. Scope: bilingual specification, template usage and runtime-environment guides on top of bf410ec1b82febe0f668327d119683ebfdf69f9c.

The specification retained an obsolete claim that current CLI application requests retried HTTP 401 anonymously. The current workflow contract preserves gateway credentials, sends explicit application bearer tokens and returns authentication failures without anonymous retries. Both specification languages now describe that behavior. Current project Python examples use the asynchronous `application_client(port, token=...)` endpoint resolver instead of synchronous `server_at`, so EPP providers can preserve their actual endpoint descriptor. Diagnostic prose no longer presents older executable compatibility as supported acceptance.

`python scripts/check_docs.py`: PASS, 221 documents, zero relative link failures. `git diff --check`: PASS. This prose correction changes no runtime or manifest bytes and does not qualify a provider or certify a cloud run. Historical evidence remains unmodified.
