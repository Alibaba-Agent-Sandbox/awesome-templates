# Bind a template API to an existing Sandbox

[中文](registry-api.zh-CN.md)

A template can ship `registry.yaml` and a package-local OpenAPI 3.1 file so the CLI can show its business operations and call them by name. Use the 0.6 CLI preview and inspect `abx sandbox --help` for the options in your installed version. Adding or binding API metadata does not install or start the server, and does not grant access. Service startup remains part of the template deployment.

`template.yaml` continues to select the template resources and startup. Adding `apis` does not convert an existing template to the proposed `specVersion: 1` resource format. The publication and initialization envelope in `registry-v1.schema.json` is separate; API-only metadata uses its `#/$defs/apiBindings` fragment and does not require publication fields.

## Package files

Put both files beside the template's existing `template.yaml`. This example describes the `hello` command of a service that is already listening on port 9000.

```yaml
# registry.yaml
apis:
  commands:
    resource: sandbox.agent
    port: 9000
    openapi: ./openapi.yaml
```

```yaml
# openapi.yaml
openapi: 3.1.0
info:
  title: Hello API
  version: '1.0'
paths:
  /commands/hello:
    post:
      operationId: hello
      security:
        - applicationToken: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              additionalProperties: false
              required: [name]
              properties:
                name:
                  type: string
      responses:
        '200':
          description: Command result
components:
  securitySchemes:
    applicationToken:
      type: http
      scheme: bearer
```

`resource` is a logical resource label for selecting bindings. The current CLI accepts `sandbox.NAME`; it does not accept a Serving Gateway in this field. `port` is the service's actual port, not a request to open a listener. Use `operationId` as the operation name. A local alias can give an operation a shorter name without changing its HTTP route or Server SDK decorator.

## Bind, inspect and call

Use an existing Sandbox ID (or a local deployment name which refers to that Sandbox) as `TARGET`:

```bash
abx sandbox "$TARGET" --bind ./registry.yaml --resource sandbox.agent \
  --credential commands.applicationToken=config:server_token \
  --alias greet=commands:hello
abx sandbox "$TARGET" --help
abx sandbox "$TARGET" hello --help
abx sandbox "$TARGET" greet --body '{"name":"Ada"}'
```

`config:server_token` reads the application's configured token. For a separately operated server, use `--credential commands.applicationToken=env:HELLO_API_TOKEN` after configuring that environment variable with the operator-provided token. Bindings store the source reference, not the token value. This credential is separate from a Provider API Key or cloud AK/SK.

Help is generated from the saved declaration and works offline. It does not prove that the server is running, that the caller has permission, or that every OpenAPI construct is supported for invocation. HTTP authentication, request validation and business errors remain visible when calling. Binding again replaces the target's saved API, credential references and aliases. API calls do not create a Sandbox or fall back to shell execution.

Keep `--body @request.json` for complete JSON input. Use the installed operation help for path, query, header and body options. Multiple APIs can share an operation name; select one with `--api NAME` or bind an explicit local alias.

## Authoring limits

| Field or behavior | Contract |
| --- | --- |
| `apis` | 1–32 named API bindings |
| API name | Starts with a letter; then letters, digits, `_` or `-`; at most 64 characters |
| Each binding | Exactly `resource`, `port`, `openapi` |
| `resource` | `sandbox.NAME`, where NAME starts with a letter and contains letters, digits, `_` or `-` |
| `port` | Integer from 1 through 65535 |
| `openapi` | Existing file inside the package after resolving symlinks; no URL |
| Files | Registry and OpenAPI files each at most 1 MiB; JSON-compatible YAML, no duplicate keys or YAML aliases |
| OpenAPI | Version 3.1.x; unique callable `operationId` within each API |
| References | Internal, nonrecursive JSON Pointers only; bundle external references first |
| Invocation extensions | `x-abx-*` extensions are not supported |

The checker verifies publication structure, local paths, references and operation identities. The CLI additionally validates its supported request and authentication subset. HTTP bearer and header API-key schemes can use explicitly configured credential sources. OpenAPI does not itself implement cloud AK/SK signing, OAuth login, uploads, shell scripts or automatic parameter discovery. An author must use an implemented operation/adapter for those behaviors; do not advertise them by inventing an extension.

Run `python scripts/check_template.py TEMPLATE_DIRECTORY` before publishing. Registry catalog metadata includes API and operation identities only; request examples, defaults, authentication values and server URLs are not exported in that summary. Keep credentials out of all published source files.
