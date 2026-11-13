"""Actual schema execution and cross-language resource semantics fixtures."""
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator
from normalize import normalize_template_v1, normalize_registry_v1, compile_template_v1, schema_for_stage, parse_yaml_v1
ROOT = Path(__file__).parent
read = lambda p: json.loads((ROOT / p).read_text())
schema, registry_schema, fixtures = read('../../spec/template-v1.schema.json'), read('../../spec/registry-v1.schema.json'), read('fixtures.json')
validators = {stage: Draft202012Validator(schema_for_stage(schema, stage)).validate for stage in ['intent', 'resolved']}
registry_validator = Draft202012Validator(registry_schema).validate
valid = []
for fixture in fixtures['validTemplates']:
    options = {'stage': fixture['stage']}
    normalized = normalize_template_v1(fixture['manifest'], validators[fixture['stage']], **options)
    assert normalize_template_v1(normalized, validators[fixture['stage']], **options) == normalized
    row = {'id': fixture['id'], 'normalized': normalized}
    if fixture.get('compile'): row['compiled'] = compile_template_v1(fixture['manifest'], validators[fixture['stage']], **options)
    valid.append(row)
invalid = []
for fixture in fixtures['invalidTemplates']:
    try: normalize_template_v1(fixture['manifest'], validators[fixture['stage']], stage=fixture['stage'])
    except (ValueError, TypeError): invalid.append(fixture['id'])
    else: raise AssertionError(fixture['id'])
registry = normalize_registry_v1(fixtures['registry']['valid'], fixtures['registry']['template'], registry_validator, validators['intent'])
registry_invalid = []
for fixture in fixtures['registry']['invalid']:
    try: normalize_registry_v1(fixture['metadata'], fixtures['registry']['template'], registry_validator, validators['intent'])
    except (ValueError, TypeError): registry_invalid.append(fixture['id'])
    else: raise AssertionError(fixture['id'])
yaml_fixtures = read('yaml-fixtures.json')
yaml_valid, yaml_invalid = [], []
for fixture in yaml_fixtures['valid']:
    value = parse_yaml_v1(fixture['text']); assert value == fixture['expected'], fixture['id']
    yaml_valid.append({'id': fixture['id'], 'value': value})
for fixture in yaml_fixtures['invalid']:
    source = fixture.get('text')
    if source is None: source = bytes.fromhex(fixture['hex']) if 'hex' in fixture else fixture['repeat'] * fixture['count']
    try: parse_yaml_v1(source)
    except (ValueError, TypeError): yaml_invalid.append(fixture['id'])
    else: raise AssertionError(fixture['id'])
result = dict(valid=valid, invalid=invalid, registry=registry, registryInvalid=registry_invalid, yamlValid=yaml_valid, yamlInvalid=yaml_invalid)
print(json.dumps(result) if '--emit' in sys.argv else f'PASS: {len(valid)} valid, {len(invalid)} invalid; YAML source fixtures retained')
