# Decision: Run real documented template usage before qualification

Status: proposed

## Problem
Default public-launch smoke intentionally disables model calls and strips blank
manifest configuration. It cannot establish usable model tasks, complete public
interfaces or literal newcomer documentation. Every template also needs its own
practical article after actual use.

## Decision
Add explicit --real-usage mode: preserve configured manifest runtime values,
require the application controller, enable real models/business prerequisites
and reject SKIP/NOT RUN. Keep the existing isolated non-model mode. Disable
Cursor/Devin invalid-key/missing-account fixtures in real mode. Use the actual
manifest WORKSPACE for controllers and identify explicitly owned remote runs.
Record full documented cases separately from basic matrix success. Start with
python-hello and opencode; the catalog-wide request remains open.

## API Design
The public runner gains --real-usage, requiring --application-controller. Helper
functions take keyword real_usage=False for compatibility. Only declared runtime
configuration reaches the application; cloud/model keys do not reach the HTTP
controller. Non-secret task/model/deadline selectors are explicitly allowlisted.
A passing controller is not automatic complete-method qualification.

## Alternatives considered
Enabling models globally would change baseline scope and borrow unrelated keys.
Treating build/create, invalid-account errors or zero-exit skips as usable tasks
would misstate acceptance. Keep historical results immutable.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244,
https://github.com/Alibaba-Agent-Sandbox/registry/issues/68 and
https://github.com/Alibaba-Agent-Sandbox/blogs/issues/16.
Use published CLI0.5.7 and Python client/server0.4.0a6; current shared installation
instructions are updated to CLI0.5.7, whose public npm version was read back.

## Test Strategy
Regress real-mode environment isolation, required flags, skip rejection, account
fixture removal and manifest workspace selection. Follow literal CLI, complete
Python and HTTP README tasks on owned Express sandboxes, inspect/download their
artifacts and confirm all owned resource deletion. Coding tasks require actual
source changes, artifacts, preserved tests and held-out independent assertions.

## Acceptance criteria
The mode and scoped regressions pass. Dated reports distinguish complete use,
failures, skipped models and missing accounts. Each fully used template gets a
practical blogs article; Registry removes Beta after >=1 reviewed provider.
The overall issue stays open until all template/provider/article criteria land.
