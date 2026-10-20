"""One native DeepAgents invocation; private configuration enters file stdin only."""
import json,os,sys
from importlib.metadata import version

def main():
    if len(sys.argv)==2 and sys.argv[1]=='--version':
        print(version('deepagents'));return 0
    data=sys.stdin.buffer.read(512*1024+1)
    if len(data)>512*1024:raise ValueError('worker input limit')
    config=json.loads(data)
    from deepagents import create_deep_agent,HarnessProfile,GeneralPurposeSubagentProfile,register_harness_profile
    from deepagents.backends import LocalShellBackend
    from langchain_openai import ChatOpenAI
    tools=['ls','read_file','write_file','edit_file','glob','grep','execute','delete']
    register_harness_profile('openai:'+config['model'],HarnessProfile(general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),excluded_tools=frozenset([] if config['allow_tools'] else tools)))
    model=ChatOpenAI(model=config['model'],api_key=config['api_key'],base_url=config['base_url'],use_responses_api=False,max_retries=0,timeout=60,streaming=False,max_tokens=8192)
    backend=LocalShellBackend(root_dir=config['cwd'],virtual_mode=True,inherit_env=False,env={k:os.environ[k] for k in ['PATH','HOME','LANG','LC_ALL','ABX_DEEPAGENTS_OWNER'] if k in os.environ},timeout=min(config['command_timeout'],120),max_output_bytes=100000)
    agent=create_deep_agent(model=model,backend=backend,subagents=[],tools=[])
    result=agent.invoke({'messages':[{'role':'user','content':config['task']}]},config={'recursion_limit':40})
    text=result['messages'][-1].content
    if not isinstance(text,str):text=json.dumps(text,ensure_ascii=False)
    print(text,flush=True);return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:raise SystemExit(1) from None
