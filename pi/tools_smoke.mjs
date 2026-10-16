/** Execute the actual pinned Pi tools offline; no model or protocol fixture. */
import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const [toolsDirectory, workspace] = process.argv.slice(2);
assert(toolsDirectory && workspace, 'tool module and disposable workspace paths required');
const factories = [
  ['read', 'createReadToolDefinition', { path: 'pi-probe.txt' }, 'pi-tool-needle'],
  ['find', 'createFindToolDefinition', { pattern: 'pi-probe.txt' }, 'pi-probe.txt'],
  ['grep', 'createGrepToolDefinition', { pattern: 'pi-tool-needle' }, 'pi-probe.txt:1: pi-tool-needle'],
  ['ls', 'createLsToolDefinition', {}, 'pi-probe.txt'],
];
await writeFile(join(workspace, 'pi-probe.txt'), 'pi-tool-needle\n');
for (const [name, factory, parameters, expected] of factories) {
  const module = await import(pathToFileURL(join(toolsDirectory, name + '.js')).href);
  const result = await module[factory](workspace).execute('offline-smoke-' + name, parameters);
  assert(!result.isError, name + ' reports tool failure');
  const text = result.content.filter(part => part.type === 'text').map(part => part.text).join('\n');
  assert(text.includes(expected), name + ' did not return the actual fixture result');
}
console.log('read/find/grep/ls OK');
