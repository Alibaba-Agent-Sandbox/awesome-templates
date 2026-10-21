/** Authored local HTTP fixtures; genuine pinned SDK transport, no native/model claim. */
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { pathToFileURL } from 'node:url';
import test from 'node:test';
import { createAgentSandboxBackend } from './adapter.mjs';
const sdk = process.env.ABX_QM_TEST_SDK_ENTRY ? await import(pathToFileURL(process.env.ABX_QM_TEST_SDK_ENTRY)) : null;

async function fixture() {
  const seen = []; const files = new Map(); const root = '/home/user/workspace/fixed-fixture';
  const server = createServer(async (request, response) => {
    let text = ''; for await (const block of request) text += block;
    const body = text ? JSON.parse(text) : {};
    seen.push({ path: request.url, method: request.method, body, auth: request.headers.authorization });
    let value;
    if (request.url === '/shell') {
      if (body.command.includes('sdk_exec.py')) value = { exit_code: 0, stdout: JSON.stringify({ result: { stdout: 'fixed synthetic output', stderr: '', code: 124, timedOut: false } }), stderr: '' };
      else {
        const action = body.command.includes("'provision'") ? 'provision' : body.command.includes("'write'") ? 'write' : body.command.includes("'read'") ? 'read' : 'list';
        value = { exit_code: 0, stdout: JSON.stringify({ result: action === 'provision' ? root : action === 'list' ? ['hello.txt'] : root + '/hello.txt' }), stderr: '' };
      }
    } else if (request.url === '/files/upload-stream') {
      files.set(body.path, Buffer.from(body.content_base64, 'base64')); value = { path: body.path, bytes: files.get(body.path).length };
    } else if (request.url.startsWith('/files/download-stream?')) {
      const path = new URL(request.url, 'http://127.0.0.1').searchParams.get('path'); value = { content_base64: files.get(path).toString('base64') };
    } else { response.writeHead(404); response.end('{}'); return; }
    response.writeHead(200, { 'Content-Type': 'application/json' }); response.end(JSON.stringify(value));
  });
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  return { root, seen, files, baseUrl: 'http://127.0.0.1:' + server.address().port, close: async () => { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); } };
}

test('actual original SDK HTTP round trips preserve files, Bearer and actual command exit', { skip: !sdk }, async () => {
  const f = await fixture(); const backend = createAgentSandboxBackend({ ServerClient: sdk.ServerClient, baseUrl: f.baseUrl, token: 'synthetic-owned-token', rootDir: f.root });
  try {
    const handle = await backend.provision([{ mode: 'rw', mountPath: '', scopeId: 'personal:unit' }]);
    await backend.writeFile(handle, 'hello.txt', 'fixed authored UTF8: 云');
    assert.equal(await backend.readFile(handle, 'hello.txt'), 'fixed authored UTF8: 云');
    assert.deepEqual(await backend.listDir(handle), ['hello.txt']);
    const result = await backend.run(handle, 'exit 124', { timeoutMs: 1000 });
    assert.equal(result.code, 124); assert.equal(result.timedOut, false);
    assert.equal(result.stdout, 'fixed synthetic output');
    assert.ok(f.seen.every(request => request.auth === 'Bearer synthetic-owned-token'));
    assert.deepEqual(backend.completedSdkCalls(), { shell: 5, upload: 1, download: 1 });
    await backend.teardown(handle);
    await backend.teardown(handle);
  } finally { await backend.close(); await f.close(); }
});

test('scope, deadline, data and unrelated handles fail before actual SDK network', { skip: !sdk }, async () => {
  const f = await fixture(); const backend = createAgentSandboxBackend({ ServerClient: sdk.ServerClient, baseUrl: f.baseUrl, rootDir: f.root });
  try {
    const handle = await backend.provision(); const before = f.seen.length;
    await assert.rejects(backend.writeFile(handle, '../escape.txt', 'fixed'), /outside selected/);
    await assert.rejects(backend.readFile({ ...handle, id: 'other' }, 'hello.txt'), /unrelated/);
    await assert.rejects(backend.run(handle, 'fixed', { timeoutMs: 0 }), /deadline/);
    await assert.rejects(backend.writeFileBytes(handle, 'hello.txt', new Uint8Array(1024 * 1024 + 1)), /1MiB/);
    await assert.rejects(backend.provision([{ mode: 'ro', mountPath: 'other' }]), /one existing writable/);
    assert.equal(f.seen.length, before);
  } finally { await backend.close(); await f.close(); }
});

for (const baseUrl of ['https://example.invalid', 'http://localhost:9000', 'http://user@127.0.0.1:9000', 'http://127.0.0.1:9000?token=x', 'http://127.0.0.1:9000/path']) {
  test('reject unsafe SDK base ' + baseUrl, () => {
    class MustNotConstruct { constructor() { assert.fail('unsafe route constructed actual SDK'); } }
    assert.throws(() => createAgentSandboxBackend({ ServerClient: MustNotConstruct, baseUrl, rootDir: '/home/user/workspace/project' }));
  });
}
