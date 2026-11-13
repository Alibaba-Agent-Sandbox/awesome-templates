# Deploy templates and run applications

[中文](workflows.zh-CN.md)

Resource configuration lives in `template.yaml`. Named `sandbox` entries prepare reusable templates and static volumes. Named `serving` entries deploy external services through native component `props`. Either collection can be used independently or together; see the [resource specification](template-spec.md).

For ordinary source templates: download the directory, edit `template.yaml`, run `abx deploy .`, then create an instance and start the application with the included `run.py --template <template-id>`. Each README documents its runtime environment and APIs. Deployment itself does not create a dynamic Sandbox.

`template.startCommand` and `readyCommand` retain their Provider-native template preparation semantics. They do not replace application startup for each dynamic instance. Process listening, Provider network access, application protocol and authentication belong to the image/program, Provider and business code respectively.

Use `template.reference` to borrow a prepared template from its Provider; borrowed resources are not updated or deleted. A static volume reference similarly does not mount it. Business code or the SDK chooses dynamic mounts and instance lifetimes.

To choose another Dockerfile, edit `template.buildConfig.dockerfile`; omitted `context` uses that file's directory. Alternate recipe files can remain, without a public build-profile layer. A recipe alone does not establish another Provider's resource, image or network support.

Export results before deleting owned instances. Templates, volumes and Serving resources have separate lifetimes. Keep private session files until instance cleanup completes. Follow the [usage guide](using-templates.md).
