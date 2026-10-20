// Explicit Stagehand4 ClientLLM transport. Browser actions remain upstream SDK work.
export function compatibleModel(config, fetchImpl = fetch) {
  let calls = 0;
  return {
    get calls() { return calls; },
    async generate(params) {
      if (++calls > 8) throw new RangeError('model call budget exhausted');
      if (params.responseFormat?.type !== 'json_schema') throw new TypeError('structured generation required');
      const messages = [];
      if (params.systemPrompt) messages.push({role:'system', content:params.systemPrompt});
      for (const message of params.messages) {
        const blocks = Array.isArray(message.content) ? message.content : [message.content];
        messages.push({role:message.role, content:blocks.map(block => {
          if (block.type === 'text') return {type:'text', text:block.text};
          if (block.type === 'image') return {type:'image_url', image_url:{url:`data:${block.mimeType};base64,${block.data}`}};
          throw new TypeError('unsupported generation content');
        })});
      }
      const body = JSON.stringify({model:config.model, messages, stream:false,
        response_format:{type:'json_schema', json_schema:{name:params.responseFormat.name,
          schema:params.responseFormat.schema, strict:true}},
        ...(params.temperature === undefined ? {} : {temperature:params.temperature})});
      if (Buffer.byteLength(body) > 2*1024*1024) throw new RangeError('model request too large');
      const response = await fetchImpl(config.base_url.replace(/\/+$/, '')+'/chat/completions', {
        method:'POST', redirect:'error', signal:AbortSignal.timeout(60000),
        headers:{'content-type':'application/json', authorization:'Bearer '+config.api_key}, body});
      if (!response.ok) { await response.body?.cancel(); throw new Error('model request failed: HTTP '+response.status); }
      let size = 0; const parts = [];
      try {
        for await (const part of response.body) {
          size += part.length;
          if (size > 1024*1024) throw new RangeError('model response too large');
          parts.push(part);
        }
      } catch (error) { await response.body?.cancel().catch(()=>{}); throw error; }
      const value = JSON.parse(Buffer.concat(parts).toString('utf8'));
      const text = value.choices?.[0]?.message?.content;
      if (value.choices?.[0]?.finish_reason !== 'stop' || typeof text !== 'string') throw new TypeError('model response incomplete');
      return {role:'assistant', content:{type:'text', text}, outputFormat:'json_schema', structuredContent:JSON.parse(text)};
    }
  };
}
