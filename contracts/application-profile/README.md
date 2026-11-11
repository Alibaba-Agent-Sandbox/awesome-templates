# Application profile defaults

[中文](README.zh-CN.md)

`profiles.json` owns the fixed fields supplied by each explicit
`application.deployment.profile`. `spec_version` remains the schema version and
does not select a profile. `normalize.mjs` and `normalize.py` copy a manifest and
fill missing fields only. They do not validate budgets, build images, resolve
credentials or deploy resources. Consumers must validate the expanded result
against the supported template schema and semantic rules before using it.

Keep explicit nulls and conflicting values: validation must reject them. Default
binding targets apply only to existing bindings and follow `state.bindingRef` and
`deployment.ingressBindingRef`. References, provider choice and configurable
budgets are never synthesized. Additional bindings require explicit targets.

Run `node contracts/application-profile/test.mjs` and
`python scripts/test_spec_tools.py` for the shared fixtures and schema regressions.
Consumer copies must preserve these source bytes and record their source revision
and content hashes; do not fork the default table in a consumer.
