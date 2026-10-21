"""Validate original Muse run correlation/usage/terminal records; return no transcript."""
import json


def completed(stdout,code,model):
    rows=[]
    for line in stdout.splitlines():
        if not line.strip():continue
        value=json.loads(line)
        if not isinstance(value,dict)or value.get('schema_version')!=1:raise ValueError('original Muse event protocol differs')
        rows.append(value)
    terminal=[v for v in rows if v.get('payload_type')=='run.terminal.completed']
    if len(terminal)!=1:return {'native_completed':False,'model_calls':0,'native_tool_results':0,'stdout':''}
    final=terminal[0].get('payload',{});command=final.get('command_id');stream=final.get('run_stream')
    if not isinstance(command,str)or not command or stream!={'id':command,'kind':'run'}:raise ValueError('original Muse terminal run identity differs')
    def correlated(row):
        payload=row.get('payload',{})
        return isinstance(payload,dict)and payload.get('command_id')==command and payload.get('run_stream')==stream
    usages=[v['payload']for v in rows if v.get('payload_type')=='run.usage'and correlated(v)]
    configs=[v['payload']for v in rows if v.get('payload_type')=='run.model.configured'and correlated(v)]
    tools=[v for v in rows if v.get('payload_type')=='tool.result'and correlated(v)]
    failed=any(v.get('payload_type')in ['run.terminal.failed','run.terminal.cancelled']and correlated(v)for v in rows)
    usage=usages[-1]if len(usages)==1 else{}
    calls=usage.get('completed_calls')
    numeric=type(calls)is int and calls>0 and usage.get('calls')==calls and type(usage.get('calls'))is int
    native_ok=code==0 and not failed and final.get('terminal')=='completed'and final.get('reason')is None and numeric and usage.get('children_included')is False and type(usage.get('cancelled_calls'))is int and usage['cancelled_calls']==0 and type(usage.get('failed_calls'))is int and usage['failed_calls']==0
    text=final.get('text');native_ok=native_ok and isinstance(text,str)and bool(text.strip())and len(configs)==1 and configs[0].get('model_id')==model and configs[0].get('provider_id')=='meta'
    return {'native_completed':bool(native_ok),'model_calls':calls if numeric else 0,'native_tool_results':len(tools),'stdout':text if isinstance(text,str)else''}
