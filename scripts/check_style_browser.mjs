/** Check the offline learned-style proof. Run through devrun. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createServer} from 'node:http';
import {chromium, firefox} from 'playwright-core';

const root=path.resolve(import.meta.dirname,'../build/style-transfer/proof');
const screenshots=path.join(root,'screenshots');fs.mkdirSync(screenshots,{recursive:true});
const server=createServer(async(req,res)=>{
 try{
  const name=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname).replace(/^\//,'')||'index.html';
  const file=path.resolve(root,name);if(!file.startsWith(root+path.sep))throw Error('Outside proof');
  const bytes=await fs.promises.readFile(file);
  const mime={'.html':'text/html; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.json':'application/json','.txt':'text/plain'}[path.extname(file)]||'application/octet-stream';
  res.writeHead(200,{'Content-Type':mime});res.end(bytes);
 }catch{res.writeHead(404);res.end('Not found')}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const reports=[];
try{
 for(const engine of [chromium,firefox]){
  const executablePath=process.env[engine.name().toUpperCase()+'_EXECUTABLE_PATH'];
  const browser=await engine.launch({headless:true,...(executablePath?{executablePath}:{})});
  try{
   const page=await browser.newPage({viewport:{width:1200,height:1250},deviceScaleFactor:2});
   const errors=[];page.on('pageerror',error=>errors.push(error.message));
   await page.goto(`http://127.0.0.1:${server.address().port}/`);
   const loaded=()=>page.evaluate(async()=>{await Promise.all([...document.images].map(im=>im.decode()));});
   await loaded();assert.equal(await page.locator('.row').count(),18);
   assert.match(await page.locator('#position').innerText(),/of 140$/);
   if(engine===chromium){await page.screenshot({path:path.join(screenshots,'tangut-light.png')});await page.locator('#theme').click();await page.screenshot({path:path.join(screenshots,'tangut-dark.png')});await page.locator('#theme').click();}
   await page.locator('#view').selectOption('methods');await page.locator('#group').selectOption('counters');assert.equal(await page.locator('.row').count(),4);await loaded();if(engine===chromium)await page.screenshot({path:path.join(screenshots,'counter-closures.png')});await page.locator('#model').selectOption('no-latent');assert.equal(await page.locator('.row').count(),5);await page.locator('#model').selectOption('dual-style');await page.locator('#group').selectOption('tangut');await page.locator('#search').fill('U+16FE0');assert.equal(await page.locator('.missing').innerText(),'Absent');
   await page.locator('#search').fill('');await page.locator('#group').selectOption('stress');await page.locator('#view').selectOption('cleanup');await loaded();assert.match(await page.locator('#position').innerText(),/of 80$/);
   if(engine===chromium){await page.screenshot({path:path.join(screenshots,'cjk-light.png')});await page.locator('#theme').click();await page.screenshot({path:path.join(screenshots,'cjk-dark.png')});await page.locator('#theme').click();}
   await page.locator('#search').fill('永');assert.equal(await page.locator('.row').count(),1);
   await page.locator('#model').selectOption('no-latent');assert.match(await page.locator('.cell img').nth(2).getAttribute('src'),/no-latent/);
   await page.locator('#overlay').check();assert.equal(await page.locator('.overlay-box img').count(),2);
   await page.locator('#size').selectOption('24');assert((await page.locator('.overlay-box').boundingBox()).width<28);
   await page.locator('#overlay').uncheck();await page.locator('#search').fill('');await page.locator('#group').selectOption('test');await page.locator('#order').selectOption('worst');assert.match(await page.locator('#position').innerText(),/of 256$/);
   await page.locator('#next').click();assert.match(await page.locator('#position').innerText(),/^19/);await page.locator('#previous').click();
   const vector=await page.evaluate(async()=>{
    const groups={};
    const canvas=document.createElement('canvas');canvas.width=canvas.height=256;const ctx=canvas.getContext('2d',{willReadFrequently:true});
    async function mask(src){const im=new Image();im.src=src;await im.decode();ctx.clearRect(0,0,256,256);ctx.drawImage(im,0,0);const d=ctx.getImageData(0,0,256,256).data;return Array.from({length:256*256},(_,i)=>d[i*4+3]>=128)}
    for(const file of ['vector-checks.json','font-checks.json','cleanup-checks.json']){const cases=await(await fetch(file)).json(),values=[],misses=[];for(const c of cases){const a=await mask(c.svg),b=await mask(c.mask);let intersection=0,union=0;for(let i=0;i<a.length;i++){intersection+=a[i]&&b[i];union+=a[i]||b[i]}values.push(intersection/union);let miss=0;for(let y=0;y<256;y++)for(let x=0;x<256;x++){const i=y*256+x;if(a[i]===b[i])continue;const other=a[i]?b:a;let near=false;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const yy=y+dy,xx=x+dx;if(yy>=0&&yy<256&&xx>=0&&xx<256&&other[yy*256+xx])near=true}if(!near)miss++}misses.push(miss/union)}
    groups[file]={cases:values.length,min_iou:Math.min(...values),mean_iou:values.reduce((a,b)=>a+b,0)/values.length,max_difference_beyond_one_pixel:Math.max(...misses),worst_pair:cases[values.indexOf(Math.min(...values))].svg};}return groups;
   });
   assert.equal(vector['cleanup-checks.json'].cases,48);assert(vector['cleanup-checks.json'].min_iou>.97,JSON.stringify(vector));assert.equal(vector['vector-checks.json'].cases,48);assert(vector['vector-checks.json'].min_iou>.97,JSON.stringify(vector));assert.equal(vector['font-checks.json'].cases,72);assert(vector['font-checks.json'].min_iou>.9&&vector['font-checks.json'].max_difference_beyond_one_pixel<.005,JSON.stringify(vector));
   await page.setViewportSize({width:390,height:900});await page.locator('#group').selectOption('tangut');await page.locator('#size').selectOption('96');await loaded();
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.evaluate(()=>scrollTo(0,0));if(engine===chromium)await page.screenshot({path:path.join(screenshots,'mobile.png')});
   assert.deepEqual(errors,[]);reports.push({browser:engine.name(),controls:'pass',mobile:'no overflow',page_errors:errors,vector});
  }finally{await browser.close()}
 }
}finally{await new Promise(resolve=>server.close(resolve))}
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const report={results:reports,html_sha256:hash(path.join(root,'index.html')),script_sha256:hash(import.meta.filename)};
fs.writeFileSync(path.join(root,'../browser-checks.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
