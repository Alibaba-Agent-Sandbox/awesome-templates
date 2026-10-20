import test from 'node:test';
import assert from 'node:assert/strict';
import {compatibleModel} from './transport.mjs';

const config = {base_url:'https://model.example.invalid/v1/', api_key:'synthetic-test-key', model:'fixture'};
const params = {systemPrompt:'fixed authored instructions', messages:[{role:'user',content:[{type:'text',text:'fixture'},{type:'image',mimeType:'image/png',data:'aGk='}]}],
  responseFormat:{type:'json_schema',name:'result',schema:{type:'object',properties:{value:{type:'string'}},required:['value'],additionalProperties:false}}};
const reply = () => Response.json({choices:[{finish_reason:'stop',message:{content:'{"value":"fixed"}'}}]});

test('actual callback maps structured schema, system, text, image and approved endpoint; no redirect', async()=>{
  const seen=[];
  const model=compatibleModel(config, async(url,options)=>{seen.push({url,options});return reply();});
  const result=await model.generate(params);
  assert.equal(model.calls,1); assert.equal(result.outputFormat,'json_schema');assert.deepEqual(result.structuredContent,{value:'fixed'});
  const {url,options}=seen[0];assert.equal(url,'https://model.example.invalid/v1/chat/completions');assert.equal(options.redirect,'error');
  assert.equal(options.headers.authorization,'Bearer synthetic-test-key');const body=JSON.parse(options.body);
  assert.equal(body.model,'fixture');assert.equal(body.stream,false);assert.equal(body.messages[0].role,'system');
  assert.equal(body.messages[1].content[1].image_url.url,'data:image/png;base64,aGk=');assert.deepEqual(body.response_format.json_schema.schema,params.responseFormat.schema);
});
test('invalid content and schema reject before network',async()=>{
  let calls=0;const model=compatibleModel(config,async()=>{calls++;return reply();});
  await assert.rejects(model.generate({...params,responseFormat:{type:'text'}}));
  await assert.rejects(model.generate({...params,messages:[{role:'user',content:{type:'tool_use'}}]}));assert.equal(calls,0);
});
test('nonzero HTTP, incomplete/invalid JSON and oversize response cannot pass',async()=>{
  for(const response of [new Response('private upstream detail',{status:401}),Response.json({choices:[{finish_reason:'length',message:{content:'{}'}}]}),Response.json({choices:[{finish_reason:'stop',message:{content:'not-json'}}]}),new Response('x'.repeat(1024*1024+1))]) {
    const model=compatibleModel(config,async()=>response);await assert.rejects(model.generate(params));
  }
});
test('bounded model budget prevents ninth upstream request',async()=>{
  let calls=0;const model=compatibleModel(config,async()=>{calls++;return reply();});
  for(let i=0;i<8;i++)await model.generate(params);await assert.rejects(model.generate(params),/budget/);assert.equal(calls,8);
});
