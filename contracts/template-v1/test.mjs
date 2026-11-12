/** Actual AJV fixture validation, semantic checks and Python/JS conformance. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import Ajv2020 from 'ajv/dist/2020.js';
import {normalizeTemplateV1, compileTemplateV1, normalizeRegistryV1, pointerValue, schemaForStage} from './normalize.mjs';
const read = relative => JSON.parse(readFileSync(new URL(relative, import.meta.url), 'utf8'));
const schema = read('../../spec/template-v1.schema.json'), registrySchema = read('../../spec/registry-v1.schema.json'), fixtures = read('./fixtures.json');
const validators = Object.fromEntries(['intent', 'resolved'].map(stage => [stage, new Ajv2020({strict: false, allErrors: true}).compile(schemaForStage(schema, stage))]));
const validateRegistry = new Ajv2020({strict: false, allErrors: true}).compile(registrySchema);
const validatePluginInput = new Ajv2020({strict: false}).compile({type: 'object', additionalProperties: false, properties: {timeout: {type: 'integer', minimum: 1}, envs: {type: 'object'}, metadata: {type: 'object'}}, required: ['timeout']});
function pluginDescriptor(stage, value, provider) {
  assert.equal(provider, 'third-party'); assert.equal(stage, 'sandbox.create');
  assert.equal(validatePluginInput(value), true);
}
const valid = [];
for (const fixture of fixtures.validTemplates) {
  const before = structuredClone(fixture.manifest);
  const options = {stage: fixture.stage, ...(fixture.provider ? {provider: fixture.provider} : {}), ...(fixture.descriptor ? {validateProvider: pluginDescriptor} : {})};
  let normalized;
  try { normalized = normalizeTemplateV1(fixture.manifest, validators[fixture.stage], options); }
  catch (error) { throw new Error(`${fixture.id}: ${error.message}`); }
  assert.deepEqual(fixture.manifest, before);
  assert.deepEqual(normalizeTemplateV1(normalized, validators[fixture.stage], options), normalized);
  const row = {id: fixture.id, normalized};
  if (fixture.compile) {
    row.compiled = compileTemplateV1(fixture.manifest, validators[fixture.stage], options);
    assert.equal(Object.hasOwn(row.compiled, 'spec_version'), false);
  }
  valid.push(row);
}
const invalid = [];
for (const fixture of fixtures.invalidTemplates) {
  assert.throws(() => normalizeTemplateV1(fixture.manifest, validators[fixture.stage], {stage: fixture.stage, provider: fixture.provider}), error => !error.message.includes('do-not-store-plaintext'), fixture.id);
  invalid.push(fixture.id);
}
const registry = normalizeRegistryV1(fixtures.registry.valid, fixtures.registry.template, validateRegistry, validators.intent);
const registryInvalid = [];
for (const fixture of fixtures.registry.invalid) {
  assert.throws(() => normalizeRegistryV1(fixture.metadata, fixtures.registry.template, validateRegistry, validators.intent), undefined, fixture.id);
  registryInvalid.push(fixture.id);
}
const rows = Object.fromEntries(valid.map(row => [row.id, row]));
assert.deepEqual(rows['independent-sandbox-and-native-serving'].compiled.deployment, rows['independent-sandbox-and-native-serving'].normalized.deployment);
assert.deepEqual(rows['independent-sandbox-and-native-serving'].compiled.sandbox, rows['independent-sandbox-and-native-serving'].normalized.sandbox);
assert.equal(Object.hasOwn(rows['independent-sandbox-and-native-serving'].compiled, 'application'), false);
assert.equal(rows['intent-descriptor-deferred'].normalized.sandbox.instance.timeout, "${env('LIFETIME')}");
assert.equal(rows['managed-resolved-native-memory'].compiled.roleProps.worker.memorySize, 4096);
assert.equal(rows['managed-resolved-native-memory'].compiled.sandbox.instance.timeout, 3600);
assert.equal(rows['managed-single-ttl'].compiled.application.sessions.maxLifetimeSeconds, 1800);
assert.equal(Object.hasOwn(rows['managed-intent'].normalized.application.sessions, 'maxLifetimeSeconds'), false);
assert.deepEqual(rows['managed-resolved-native-memory'].compiled.bindingValues.clientAuth, {generate: true, owner: 'default'});
assert.deepEqual(rows['source-context-opensandbox'].compiled.build_profiles.portable, {dockerfile: 'Dockerfile.portable', context: '.'});
assert.equal(Object.hasOwn(rows['unbound-source-portable'].normalized.sandbox, 'provider'), false);
assert.equal(Object.hasOwn(rows['managed-explicit-auth-preserved'].compiled.bindingValues.clientAuth, 'generate'), false);
assert.equal(Object.hasOwn(rows['managed-explicit-auth-preserved'].compiled.bindingValues.internalAuth, 'generate'), false);
assert.equal(rows['managed-native-role-authority'].compiled.bindingValues.internalAuth.roleArn, 'acs:ram::123456789:role/fixture');
assert.throws(() => normalizeTemplateV1(fixtures.validTemplates.find(row => row.id === 'third-party-descriptor').manifest, validators.resolved, {stage: 'resolved', validateProvider: () => false}));
assert.equal(rows['managed-intent'].normalized.application.bindings.model.apiKey, "${env('OPENAI_API_KEY')}");
assert.equal(pointerValue({'a/b': {'~': ['value']}}, '/a~1b/~0/0'), 'value');
assert.throws(() => pointerValue(['value'], '/01'));
assert.throws(() => pointerValue({}, ''));
for (const number of [NaN, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
  const fixture = structuredClone(fixtures.validTemplates[0].manifest); fixture.sandbox.instance.timeout = number;
  assert.throws(() => normalizeTemplateV1(fixture, validators.intent));
}
const result = {valid, invalid, registry, registryInvalid};
const python = spawnSync(process.env.PYTHON || 'python3', [fileURLToPath(new URL('./test_contract.py', import.meta.url)), '--emit'], {encoding: 'utf8'});
assert.equal(python.status, 0, 'Python fixture consumer failed: ' + python.stderr);
assert.deepEqual(JSON.parse(python.stdout), result, 'Python and JS resolved different resource meaning');
console.log(JSON.stringify({result: 'PASS', valid: valid.length, invalid: invalid.length, registryInvalid: registryInvalid.length, conformance: 'Python and JavaScript deep-equal', scope: 'inactive contract/actual schema and pure normalization; no Devs expression execution or cloud acceptance'}));
