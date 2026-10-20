"""Creation-route/ownership regressions only; fixtures are not cloud evidence."""
import json
from types import SimpleNamespace
from unittest.mock import patch

import express_e2e as h
from test_express_cleanup import case


def test_sdk_creation_uses_owned_ready_template_and_keeps_cli_smoke_cleanup():
    with case() as (project, options, intents):
        options=h.build_options([str(project),'--alias','e2e-cleanup-regression','--sandbox-create','sdk','--sandbox-timeout','600'])
        events=[]
        def runner(args,timeout):
            events.append(args)
            if '--official-api' in args:return h.Proc(0,'[]','')
            if 'deploy' in args:return h.Proc(0,'{"TemplateID":"owned-template","Status":"ready"}','')
            if args[:2]==['--json','create']:raise AssertionError('CLI creation selected despite explicit SDK route')
            if 'run' in args:return h.Proc(0,'{"result":"ok"}','')
            return h.Proc(0,'','')
        async def create(template, *, timeout):
            assert (template,timeout)==('owned-template',600)
            events.append('actual SDK create callback')
            async def close():events.append('local client closed')
            return SimpleNamespace(id='owned-sandbox',close=close)
        sdk=SimpleNamespace(Sandbox=SimpleNamespace(create=create))
        with patch.dict('sys.modules',{'agent_sandbox.api.sandbox':sdk}):
            assert h.execute(options,runner=runner,sdk=lambda *_:'ok',verify=lambda intent,_:intent['sandbox_ids']==['owned-sandbox'])==0
        assert 'actual SDK create callback' in events and 'local client closed' in events
        assert any(isinstance(x,list) and 'kill' in x for x in events)
        assert any(isinstance(x,list) and 'delete' in x for x in events)
        report=json.loads(next((project/'evidence').glob('express-*.json')).read_text())
        assert report['sandbox_create']=='python-sdk-Sandbox.create'


def test_sdk_create_failure_stays_ambiguous_without_acceptance():
    with case() as (project, options, intents):
        options=h.build_options([str(project),'--alias','e2e-cleanup-regression','--sandbox-create','sdk'])
        def runner(args,timeout):
            if '--official-api' in args:return h.Proc(0,'[]','')
            if 'deploy' in args:return h.Proc(0,'{"TemplateID":"owned-template","Status":"ready"}','')
            raise AssertionError('unknown creation must reconcile before mutation')
        with patch.object(h,'default_sdk_create',side_effect=TimeoutError('private upstream details')),patch.object(h,'recover_owned',return_value=False):
            assert h.execute(options,runner=runner,sdk=lambda *_:'ok',verify=lambda *_:True)==1
        assert not (project/'evidence').exists()
        intent=json.loads(intents[0].read_text())
        assert intent['create_attempted'] and not intent['sandbox_ids'] and not intent['recovery_complete']


def test_known_sdk_id_survives_local_client_close_failure():
    async def close():raise RuntimeError('local transport close failed')
    async def create(**kwargs):return SimpleNamespace(id='already-created-owned-id',close=close)
    with patch.dict('sys.modules',{'agent_sandbox.api.sandbox':SimpleNamespace(Sandbox=SimpleNamespace(create=create))}):
        assert h.default_sdk_create('owned-template',300)=='already-created-owned-id'
