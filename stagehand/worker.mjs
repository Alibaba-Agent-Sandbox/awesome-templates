import fs from 'node:fs/promises';
import path from 'node:path';
import {localBrowser, Stagehand} from '@browserbasehq/stagehand';
import {z} from 'zod';
import {compatibleModel} from './transport.mjs';

let browser, stagehand;
try {
  const version = JSON.parse(await fs.readFile(new URL('./node_modules/@browserbasehq/stagehand/package.json', import.meta.url))).version;
  if (version !== '4.3.0') throw new Error('native version mismatch');
  if (process.argv[2] === '--version') { process.stdout.write(version); process.exit(0); }
  let size = 0; const input = [];
  for await (const part of process.stdin) { size += part.length; if (size > 128*1024) throw new RangeError('request too large'); input.push(part); }
  const request = JSON.parse(Buffer.concat(input).toString('utf8'));
  const selfTest = request.mode === 'self-test';
  const model = selfTest ? {generate:async()=>{throw new Error('offline self-test cannot infer');}} : compatibleModel(request);
  browser = await localBrowser.launch({headless:true, executablePath:request.browser_binary,
    userDataDir:path.join(process.cwd(), 'browser'), preserveUserDataDir:false,
    chromiumSandbox:false, args:['--disable-dev-shm-usage'], viewport:{width:1024,height:768}});
  stagehand = await Stagehand.create({browser, model:{generate:params=>model.generate(params)}, logging:{level:'off'}});
  const page = await browser.context.newPage();
  const target = selfTest ? 'data:text/html;charset=utf-8,'+encodeURIComponent('<title>STAGEHAND_NATIVE</title><h1>Native Stagehand 浏览器</h1>') : request.url;
  await page.goto(target, {waitUntil:'load', timeout:30000});
  let action, extracted;
  if (!selfTest) {
    action = await stagehand.act(request.task, {page, timeout:60000, cache:false});
    if (action.data.success !== true || action.data.actions.length < 1) throw new Error('native action failed');
    if (request.extract_instruction) {
      extracted = (await stagehand.extract(request.extract_instruction, z.object({text:z.string()}), {page, timeout:60000, cache:false})).data;
    }
  }
  const png = Buffer.from(await page.screenshot({type:'png'}));
  if (png.length < 100 || png.length > 8*1024*1024 || png.subarray(0,8).toString('hex') !== '89504e470d0a1a0a') throw new Error('invalid native PNG');
  const result = {version, title:await page.title(), final_url:await page.url(), png_bytes:png.length};
  if (selfTest) {
    if (result.title !== 'STAGEHAND_NATIVE') throw new Error('native navigation mismatch');
    result.self_test = 'STAGEHAND_NATIVE_OK';
  } else {
    await fs.writeFile(request.screenshot_path, png, {flag:'r+'});
    Object.assign(result, {action:action.data, extracted:extracted??null, model_calls:model.calls, screenshot_path:request.screenshot_path});
  }
  await stagehand.close(); stagehand = undefined;
  await browser.close(); browser = undefined;
  process.stdout.write(JSON.stringify(result));
} catch (error) {
  try { await stagehand?.close(); } catch {}
  try { await browser?.close(); } catch {}
  process.stdout.write(JSON.stringify({native_error_type:/^[A-Za-z][A-Za-z0-9_]{0,79}$/.test(error?.name??'')?error.name:'NativeError'}));
  process.exitCode = 1;
}
