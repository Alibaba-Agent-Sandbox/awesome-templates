"""Original Rust NDJSON schema guards; synthetic fixtures are not native acceptance."""
import importlib.util
import json
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('prime_native_terminal_tests',Path(__file__).with_name('e2e_test.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def events():
    return [{'type':'agent_start'},{'type':'turn_end'},
            {'type':'tool_execution_end','toolName':'ipython','toolCallId':'fixture-call','result':{'content':[]}},
            {'type':'agent_end','messages':[
                {'role':'toolResult','toolName':'ipython','toolCallId':'fixture-call','isError':False,'content':[]},
                {'role':'assistant','stopReason':'stop','content':[{'type':'text','text':'fixture-final'}]}]}]


def render(rows):return '\n'.join(json.dumps(row)for row in rows)


def test_native_schema_uses_terminal_tool_result_status_not_missing_event_status():
    assert c.final_text(render(events()))=='fixture-final'


@pytest.mark.parametrize('change',['error','aborted','missing_tool','mismatched_tool','tool_error','missing_turn','partial_only'])
def test_incomplete_native_json_never_qualifies_coding(change):
    rows=events()
    if change=='error':rows.append({'type':'error','message':'authored failure'})
    elif change=='aborted':rows[-1]['messages'][-1]['stopReason']='aborted'
    elif change=='missing_tool':rows=[row for row in rows if row['type']!='tool_execution_end']
    elif change=='mismatched_tool':rows[-1]['messages'][0]['toolCallId']='unrelated-call'
    elif change=='tool_error':rows[-1]['messages'][0]['isError']=True
    elif change=='missing_turn':rows=[row for row in rows if row['type']!='turn_end']
    elif change=='partial_only':rows=[{'type':'message_update','message':rows[-1]['messages'][-1]}]
    assert c.final_text(render(rows))==''
