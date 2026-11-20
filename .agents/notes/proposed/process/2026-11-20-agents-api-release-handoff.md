# Decision: Preserve Agents API release identity during deployment

Status: proposed

## Problem

Generated project `.env` values could be shadowed by process environment. The nested JSON values also failed to reach FC: native Devs rejected brace literals in `env()` defaults and its dotenv reader retained escaped quotes in structured values. The old Dispatcher timer update used a name without checking its recorded function ID. The example deployment's 600-second action limit expired before the candidate smoke process's 780-second task and 900-second process budgets.

## Decision

Reject explicit process values for release-generated variables before writing configuration. Use blank parser defaults before init, then write literal single-quoted values so the existing native parser receives actual JSON. Check the previously published Dispatcher's identity before candidate publication and again before handing off its timer. Use the CLI's `--build-timeout 1800` in the six recipes so the bounded business check can finish under the documented command.

## API Design

The release script creates generated state in the private project `.env`. `vars.policy` and the existing credential inputs control deployment. Generated values that could alter dotenv quoting or expansion are rejected. An empty exported optional token is rejected with a request to unset it for automatic generation. A stale Dispatcher receipt blocks publication without updating the replacement.

## Alternatives considered

Overriding the parent process environment would change native Devs precedence and hide stale input. Updating the previous Dispatcher by name would trust a replaceable identity. A new generic release timeout field would duplicate the existing CLI option.

## Dependencies

Tracks the existing [Agents API delivery Issue](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309) and [Harness recipes PR](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/312). The timeout parameter comes from the [named-resource CLI implementation](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/249).

## Test strategy

Reproduce process overrides, native parser rejection, literal JSON serialization and same-name Dispatcher replacement before applying the corrections. Exercise the actual built CLI parser before and after running init for each standalone template. Exercise existing matching-identity candidate behavior and the real local Gateway, Worker and Dispatcher processes. Check generator synchronization and bilingual quick starts.

## Acceptance criteria

All six standalone projects share the corrected release script and documented commands. Generated-only process values cannot change FC declarations. A known replacement cannot receive the previous Dispatcher timer mutation. Hosted and old-Session acceptance remain required for the parent delivery.

The Qwen Code recipe uses the native 0.28.0 error-terminal fix, checked with a real
failed provider connection and a real two-turn file task. See the
[model verification](../../../evidence/verify/2026-11-20-agents-api-qwen-model.md).
