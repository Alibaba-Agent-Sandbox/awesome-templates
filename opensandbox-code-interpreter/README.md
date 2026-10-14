# opensandbox-code-interpreter

OpenSandbox does not have a public template registry. Templates in its API are per-tenant golden images, and Docker runtime returns 501 for template create.

The image to pass is `opensandbox/code-interpreter`. The engine entrypoint for an image whose name contains `code-interpreter` is `/opt/code-interpreter/code-interpreter.sh`, not `python3 commands.py`.

```python
Sandbox.create(
    provider="opensandbox",
    template="opensandbox/code-interpreter",
)
```

`code.interpret` is still E8004 on this provider. Shell and files go through execd. Named commands (`sandbox.run`) are E8004 because the data plane URL is `abx-engine://`.

This image is not a substitute for E2B or Express `code-interpreter-v1`.
