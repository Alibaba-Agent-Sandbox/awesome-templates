/** Original QM public harness/tool APIs and original SDK; only the owned target runs this. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { ServerClient } from '/opt/agent-sandbox-node-sdk/dist/index.js';
import { createToolContext } from '/opt/qm/src/tools/primitives.ts';
import { createPiHarness } from '/opt/qm/src/harness/pi-harness.ts';
import { createLocalWorkspaceStore } from '/opt/qm/src/workspace/workspace-store.ts';
import { createAclStore } from '/opt/qm/src/acl/acl-store.ts';
import { setCustomProviders, validateCustomProviderSpec } from '/opt/qm/src/model/custom-providers.ts';
import { createAgentSandboxBackend } from './adapter.mjs';

const metadata = JSON.parse(fs.readFileSync('/opt/qm-bootstrap/upstream.json', 'utf8'));
function identity() {
  if (process.version !== 'v24.16.0') throw new Error('original Node version differs');
  const binary = '/opt/node/current/bin/node';
  const digest = crypto.createHash('sha256'); const block = Buffer.allocUnsafe(1024 * 1024);
  const fd = fs.openSync(binary, 'r');
  try { let count; while ((count = fs.readSync(fd, block, 0, block.length, null)) > 0) digest.update(block.subarray(0, count)); }
  finally { fs.closeSync(fd); }
  if (fs.statSync(binary).size !== metadata.node.binary_size || digest.digest('hex') !== metadata.node.binary_sha256) throw new Error('original Node executable differs');
  for (const [key, directory] of [['qm', '/opt/qm'], ['agent-sandbox-node-sdk', '/opt/agent-sandbox-node-sdk']]) {
    for (const [name, expected] of Object.entries(metadata[key].identity_files)) {
      const bytes = fs.readFileSync(path.join(directory, name));
      if (crypto.createHash('sha256').update(bytes).digest('hex') !== expected) throw new Error('original native source identity differs');
    }
  }
  const qm = JSON.parse(fs.readFileSync('/opt/qm/package.json', 'utf8'));
  const sdk = JSON.parse(fs.readFileSync('/opt/agent-sandbox-node-sdk/package.json', 'utf8'));
  if (qm.name !== 'qm' || qm.version !== '0.1.0' || sdk.name !== '@agent-sandbox/sdk' || sdk.version !== '0.1.0') throw new Error('original package identity differs');
  return { qm_version: qm.version, node_version: process.versions.node, sdk_version: sdk.version };
}

function context(backend, handle, scope) {
  const unsupported = () => { throw new Error('deployment and external delivery are unavailable in this slice'); };
  return createToolContext({
    sandbox: backend, provision: async () => handle,
    layers: [{ scopeId: scope, mountPath: '', mode: 'rw' }],
    commandPolicy: () => ({ mode: 'denylist', rules: [] }), authorizeCommand: () => true,
    grantedHandles: [], workspace: createLocalWorkspaceStore(path.join(process.env.HOME, 'qm-workspace-state')),
    deploy: new Proxy({}, { get: () => unsupported }), acl: createAclStore(),
    createdBy: 'abx-owner', execTimeoutMs: 30000, execTimeoutCeilingMs: 120000,
    humanTurn: true, attach: async () => ({ ok: false, message: 'external delivery unavailable' }),
  });
}

async function useBackend(request, action) {
  const backend = createAgentSandboxBackend({ ServerClient, baseUrl: request.sdk_base, token: request.sdk_token, rootDir: request.root });
  let handle;
  try {
    const scope = 'personal:abx-' + crypto.randomUUID();
    handle = await backend.provision([{ scopeId: scope, mountPath: '', mode: 'rw' }]);
    return await action(backend, handle, context(backend, handle, scope), scope);
  } finally {
    if (handle) await backend.teardown(handle);
    await backend.close();
  }
}

async function sdkSmoke(request) {
  const folder = path.join(request.root, 'abx_qm_sdk_' + crypto.randomBytes(16).toString('hex'));
  fs.mkdirSync(folder, { mode: 0o700 });
  try {
    return await useBackend({ ...request, root: folder }, async (backend, handle, tools) => {
      const marker = 'ORIGINAL_QM_SDK_' + crypto.randomBytes(16).toString('hex');
      await tools.write('marker.txt', marker);
      const observed = await tools.read('marker.txt');
      if (observed.content !== marker) throw new Error('original QM SDK file round trip differs');
      const command = "python3 -I -c 'from pathlib import Path; print(Path(\"marker.txt\").read_text())'";
      const executed = await tools.execute(command, { timeoutSeconds: 30 });
      if (executed.code !== 0 || executed.stdout.trim() !== marker || executed.timedOut) throw new Error('original QM SDK execution differs');
      if (!(await backend.listDir(handle, '')).includes('marker.txt')) throw new Error('original backend listing differs');
      await backend.removeDir(handle, 'marker.txt');
      if ((await backend.readFile(handle, 'marker.txt')) !== null) throw new Error('owned backend target remains');
      const calls = backend.completedSdkCalls();
      if (!(calls.shell >= 6 && calls.upload === 1 && calls.download === 1)) throw new Error('actual SDK operations absent');
      return { original_qm_tools: true, actual_agent_sandbox_sdk: true, owned_cleanup: true, ...identity() };
    });
  } finally {
    fs.rmSync(folder, { recursive: true });
    if (fs.existsSync(folder)) throw new Error('owned SDK smoke directory remains');
  }
}

async function modelRun(request) {
  const settings = request.settings;
  const spec = { id: 'abx-approved', name: 'Approved compatible model', protocol: 'openai', baseUrl: settings.base,
    models: [{ id: settings.model, name: 'Approved model', reasoning: false, contextWindow: 65536, maxTokens: 8192 }] };
  validateCustomProviderSpec(spec); setCustomProviders([spec]);
  return useBackend(request, async (backend, handle, tools, scope) => {
    const harness = createPiHarness({ modelId: 'custom/abx-approved/' + settings.model,
      resolveProviderKeys: async () => ({ 'abx-approved': settings.key }), captureRequests: false,
      tempDirPrefix: 'abx-qm', scratchExec: false, ownerAuthExec: false, reachExec: false,
      controlTools: false, sandboxResources: false, turnWallClockMs: request.deadline * 1000,
      execTimeoutMs: 30000, execTimeoutCeilingMs: 120000 });
    let sequence = 0; let toolCalls = 0; let toolResults = 0; let modelRecords = 0;
    try {
      const result = await harness.turns.runTurn({
        session: { id: crypto.randomUUID(), type: 'dm', scopeId: scope, threadRef: 'owned-native', createdAt: Date.now() },
        input: request.prompt, history: [], scopeLabel: scope, orgScopeId: 'org:abx',
        systemPrompt: 'You are the original QM coding harness on an owned disposable computer. Use only execute and files read/write to inspect and repair the existing project. Preserve original tests. No delegation, subagents, external deliveries, provider changes or network services. The selected computer root is ' + JSON.stringify(handle.rootDir) + '.',
        tools, runtime: { harnessId: 'pi', modelId: 'custom/abx-approved/' + settings.model, effortLevel: 'off' },
        delegateWork: false, surfaceTools: false, turnWallClockMs: request.deadline * 1000,
        toolApprovalGate: name => ['execute', 'files:read', 'files:write'].includes(name),
        emit: async entry => { if (entry.type === 'tool_call') toolCalls++; if (entry.type === 'tool_result') toolResults++; return { ...entry, sessionId: 'owned-native', seq: ++sequence, parentSeq: null, createdAt: Date.now() }; },
        recordModelCall: () => { modelRecords++; },
      });
      const complete = typeof result.reply === 'string' && Boolean(result.reply.trim()) && result.modelCalls > 0 && !result.stopped && !result.stoppedByUser && !result.pausedOnApproval && !result.pendingApprovals?.length && !result.runtimeHandoff && !result.silent;
      return { ...identity(), source_commit: metadata.qm.source_commit, stdout: result.reply,
        native_completed: complete, model_calls: result.modelCalls ?? 0, model_records: modelRecords,
        native_tool_calls: toolCalls, native_tool_results: toolResults, sdk_calls: backend.completedSdkCalls(),
        stopped: result.stopped === true, pending_approvals: result.pendingApprovals?.length ?? 0 };
    } finally { await harness.turns.close?.(); }
  });
}

async function main() {
  const raw = fs.readFileSync(0, 'utf8');
  if (Buffer.byteLength(raw) > 131072) throw new Error('native request exceeds128KiB');
  const request = JSON.parse(raw); const operation = process.argv[2];
  const version = identity();
  if (operation === 'version') return version;
  if (operation === 'native_check') {
    if (typeof createToolContext !== 'function' || typeof createPiHarness !== 'function' || typeof ServerClient !== 'function') throw new Error('original native APIs absent');
    return { original_qm_harness: true, original_tool_context: true, actual_sdk_client: true };
  }
  if (operation === 'sdk_smoke') return sdkSmoke(request);
  if (operation === 'run') return modelRun(request);
  if (operation === 'exec') return useBackend(request, async (backend, handle, tools) => ({ ...await tools.execute(request.command, { timeoutSeconds: request.deadline }), sdk_calls: backend.completedSdkCalls(), original_qm_tools: true }));
  if (operation === 'file') return useBackend(request, async (backend, handle, tools) => {
    let result;
    if (request.action === 'read') result = await tools.read(request.path);
    else if (request.action === 'write') { await tools.write(request.path, request.text); result = true; }
    else if (request.action === 'list') result = await backend.listDir(handle, request.path);
    else if (request.action === 'remove') { await backend.removeDir(handle, request.path); result = true; }
    else throw new Error('unsupported original backend file operation');
    return { result, sdk_calls: backend.completedSdkCalls(), original_qm_tools: true };
  });
  throw new Error('unsupported native operation');
}

try {
  const result = await main();
  process.stdout.write(JSON.stringify(result) + '\n', () => process.exit(0));
} catch (error) {
  const kind = /^[A-Za-z_][A-Za-z0-9_]{0,63}$/.test(error?.name ?? '') ? error.name : 'NativeFailure';
  process.stdout.write(JSON.stringify({ error_type: kind }) + '\n', () => process.exit(1));
}
