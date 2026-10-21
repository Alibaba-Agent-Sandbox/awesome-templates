#!/usr/bin/env python3
"""Validate managed metadata; NOT_VERIFIED is a valid catalog state, never a pass."""
import argparse,json,re
from pathlib import Path
import yaml
from check_template import README_EN,README_ZH,PROVIDERS
ROOT=Path(__file__).resolve().parents[1]
FIELDS={'name','provider','template_id','kind','documentation','evidence','verification_scope','native_interpreter_verified'}

def local_file(root,value):
    if not isinstance(value,str)or not value:return None
    path=root/value
    if Path(value).is_absolute()or path.is_symlink()or not path.resolve().is_relative_to(root.resolve())or not path.is_file():return None
    return path

def check(root=ROOT):
    problems=[]
    try:catalog=yaml.safe_load((root/'awesome-templates.yaml').read_text())
    except (OSError,ValueError,yaml.YAMLError):return ['invalid catalog YAML']
    if not isinstance(catalog,dict):return ['catalog must be a mapping']
    rows=catalog.get('managed_templates',[])
    if not isinstance(rows,list):return ['managed_templates must be a list']
    source_names={x.get('name')for x in catalog.get('templates',[])if isinstance(x,dict)and isinstance(x.get('name'),str)};seen=set()
    for index,row in enumerate(rows):
        label=str(row.get('name',index))if isinstance(row,dict)else str(index)
        def fail(message):problems.append(label+': '+message)
        if not isinstance(row,dict)or set(row)!=FIELDS:fail('managed fields must match the documented contract');continue
        name=row['name'];provider=row['provider']
        if not isinstance(name,str)or not re.fullmatch('[a-z0-9][a-z0-9-]*',name):fail('name must be kebab-case');continue
        if name in seen or name in source_names:fail('name duplicates a source/managed entry')
        seen.add(name)
        if not isinstance(provider,str)or provider not in PROVIDERS:fail('unknown provider')
        if row['kind']!='provider-managed'or not isinstance(row['template_id'],str)or not row['template_id'].strip():fail('managed kind/native template ID required')
        if not isinstance(row['verification_scope'],str)or not row['verification_scope'].strip():fail('verification_scope is required')
        if type(row['native_interpreter_verified'])is not bool:fail('native_interpreter_verified must be boolean')
        doc=local_file(root,row['documentation']);evidence=local_file(root,row['evidence'])
        if not doc:fail('documentation must be an existing local file')
        else:
            for file,headings in [(doc,README_EN),(doc.with_name('README.zh-CN.md'),README_ZH)]:
                if not file.is_file():fail('bilingual README missing');continue
                actual=[line[3:].strip()for line in file.read_text().splitlines()if line.startswith('## ')]
                if tuple(actual)!=headings:fail('managed README requires the ordered14sections')
        if not evidence:fail('evidence must be an existing local file');continue
        try:proof=json.loads(evidence.read_text())
        except (OSError,ValueError):fail('invalid evidence JSON');continue
        if not isinstance(proof,dict):fail('evidence must be an object');continue
        if proof.get('provider')!=provider or proof.get('template')!=name:fail('evidence provider/template differs')
        if proof.get('template_id',row['template_id'])!=row['template_id']:fail('native template ID differs')
        if proof.get('passed')is True:
            if proof.get('cleanup_verified')is not True or not isinstance(proof.get('checks'),list)or not proof['checks']or not all(isinstance(item,str)and item.strip()for item in proof['checks']):fail('runtime pass requires actual checks and independent cleanup')
            if row['verification_scope']=='catalog-only-unverified':fail('runtime pass contradicts unverified scope')
        elif proof.get('passed')is False:
            if proof.get('status')!='NOT_VERIFIED'or row['verification_scope']!='catalog-only-unverified'or row['native_interpreter_verified']is not False:fail('missing explicit unverified state/scope')
        else:fail('evidence passed must be boolean')
        if proof.get('native_interpreter_verified')is not row['native_interpreter_verified']:fail('native interpreter claim differs from evidence')
    return problems

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);args=parser.parse_args()
    problems=check(args.root)
    for problem in problems:print(problem)
    print(f'Managed catalog: {len(problems)} violations; unverified entries do not certify a backend')
    return int(bool(problems))
if __name__=='__main__':raise SystemExit(main())
