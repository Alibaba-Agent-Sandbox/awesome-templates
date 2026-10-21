/** Actual Agent Sandbox Node HTTP SDK backend for the original QM Sandbox interface. */
import { posix } from 'node:path';
import { randomUUID } from 'node:crypto';

const quote = (value) => "'" + value.replaceAll("'", "'\"'\"'") + "'";
const bounded = (value, limit, label) => {
  if (typeof value !== 'string' || Buffer.byteLength(value) > limit || value.includes('\0')) throw new TypeError('invalid bounded ' + label);
  return value;
};

export function createAgentSandboxBackend({ ServerClient, baseUrl, token = '', rootDir }) {
  const url = new URL(baseUrl);
  if (url.protocol !== 'http:' || !['127.0.0.1', '[::1]'].includes(url.hostname) || url.username || url.password || url.search || url.hash || url.pathname !== '/') throw new TypeError('explicit literal-loopback SDK base required');
  bounded(token, 8192, 'SDK token');
  if (/[\r\n]/.test(token)) throw new TypeError('invalid SDK token');
  bounded(rootDir, 4096, 'root');
  if (!posix.isAbsolute(rootDir) || rootDir === '/') throw new TypeError('existing absolute project root required');
  const client = new ServerClient(baseUrl, { token, timeout: 150 });
  const id = 'abx-qm-' + randomUUID();
  let root = posix.resolve(rootDir);
  let closed = false;
  let provisioned = false;
  const completed = { shell: 0, upload: 0, download: 0 };
  const profile = Object.freeze({ backend: 'agent-sandbox-http-sdk', writablePersistence: 'resident_disk', processSessions: false, egressEnforcement: 'none' });
  function active(handle) {
    if (closed || !provisioned || handle?.id !== id || handle.rootDir !== root) throw new Error('inactive or unrelated SDK backend handle');
  }
  function relative(path) {
    bounded(path, 4096, 'path');
    const value = posix.resolve(root, path);
    if (value !== root && !value.startsWith(root + '/')) throw new Error('path outside selected backend root');
    return path;
  }
  async function guard(action, path = '') {
    const command = ['python3', '-I', '/home/user/app/sdk_path.py', action, root, relative(path)].map(quote).join(' ');
    const result = await client.process.shell(command, { timeout: 30 });
    completed.shell++;
    const value = JSON.parse(result.stdout);
    if (result.exitCode !== 0) { const error = new Error('SDK backend path operation rejected'); if (value.error_type === 'FileNotFoundError') error.name = 'FileNotFoundError'; throw error; }
    if (!Object.hasOwn(value, 'result')) throw new Error('SDK backend path protocol invalid');
    return value.result;
  }
  const backend = {
    profile,
    async provision(layers = [], options = {}) {
      if (closed) throw new Error('SDK backend closed');
      if (layers.length > 1 || layers.some(layer => layer.mode !== 'rw' || layer.mountPath !== '')) throw new Error('only one existing writable project is supported');
      if (options.scratch || options.sandboxId || options.egress || options.env && Object.keys(options.env).length) throw new Error('unsupported backend provisioning capability');
      root = await guard('provision');
      provisioned = true;
      return { id, rootDir: root, backend: profile.backend, coldStart: false };
    },
    async run(handle, command, options = {}) {
      active(handle); bounded(command, 32768, 'command');
      const timeout = Math.ceil((options.timeoutMs ?? 60000) / 1000);
      if (!Number.isFinite(timeout) || timeout < 1 || timeout > 120) throw new RangeError('backend execution deadline must be1..120seconds');
      if (options.signal?.aborted) throw new Error('backend operation aborted before execution');
      const body = JSON.stringify({ root, command, deadline: timeout });
      const commandLine = 'python3 -I /home/user/app/sdk_exec.py ' + quote(body);
      const response = await client.process.shell(commandLine, { timeout: timeout + 30 });
      completed.shell++;
      const value = JSON.parse(response.stdout);
      if (response.exitCode !== 0 || !value.result || !Number.isInteger(value.result.code) || typeof value.result.timedOut !== 'boolean') throw new Error('owned native tool execution failed');
      if (typeof value.result.stdout !== 'string' || typeof value.result.stderr !== 'string' || Buffer.byteLength(value.result.stdout) > 64 * 1024 || Buffer.byteLength(value.result.stderr) > 64 * 1024) throw new Error('backend output exceeds64KiB per stream');
      return value.result;
    },
    async writeFileBytes(handle, path, data) {
      active(handle);
      if (!(data instanceof Uint8Array) || data.byteLength > 1024 * 1024) throw new TypeError('backend write requires at most1MiB bytes');
      const target = await guard('write', path);
      await client.files.upload(target, data); completed.upload++;
    },
    async writeFile(handle, path, text) {
      bounded(text, 1024 * 1024, 'text');
      return backend.writeFileBytes(handle, path, Buffer.from(text));
    },
    async readFileBytes(handle, path) {
      active(handle);
      let target;
      try { target = await guard('read', path); } catch (error) { if (error.name === 'FileNotFoundError') return null; throw error; }
      const data = await client.files.download(target); completed.download++;
      if (data.byteLength > 1024 * 1024) throw new Error('backend file exceeds1MiB');
      return data;
    },
    async readFile(handle, path) { const data = await backend.readFileBytes(handle, path); if (data === null) return null; return new TextDecoder('utf-8', { fatal: true }).decode(data); },
    async listDir(handle, path = '') { active(handle); return guard('list', path); },
    async removeDir(handle, path) { active(handle); await guard('remove', path); },
    async teardown(handle, options = {}) {
      if (handle?.id !== id || handle.rootDir !== root) throw new Error('unrelated SDK backend handle');
      if (options.destroy) throw new Error('outer sandbox/caller project deletion belongs to its controller');
      provisioned = false;
    },
    async close() { closed = true; provisioned = false; await client.close(); },
    completedSdkCalls() { return { ...completed }; },
  };
  return backend;
}
