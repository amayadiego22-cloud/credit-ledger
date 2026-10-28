/* Minimized circle regressions: real rendered paths, native bridge and data. */
const assert=require('assert'),fs=require('fs'),path=require('path');
module.exports=async function verifyCircle(env){
 const {context,gamefaceHtml,nativeBootstrap,checks,errors,example}=env;
 const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
 await page.setViewportSize({width:1100,height:1050});
 const payload=JSON.parse(JSON.stringify(example));payload.view_mode='minimized';
 payload.balance=24357991;payload.goal={active:true,target:2500000,baseline:22329142,final_balance:24829142,current:2028849,remaining:471151,progress_percent:81.15396,complete:false};
 payload.summary.battle_count=19;payload.summary.net_credits=2028849;
 await page.evaluate(nativeBootstrap,payload);
 await page.evaluate(()=>{
  window.isDomBuilt=true;window.__nativeReady=true;window.__circleMoves=[];window.__circleFinancialWrites=[];
  window.viewEnv.handleViewEvent=event=>window.__circleMoves.push(event.on);
  window.model.onSaveGoal=()=>window.__circleFinancialWrites.push('goal');
  window.model.onResetGoal=()=>window.__circleFinancialWrites.push('reset');
  window.model.onResetHistory=()=>window.__circleFinancialWrites.push('history');
  window.model.onSetLanguage=request=>{
   const p=JSON.parse(window.model.payload);p.language=request.language;
   p.language_selection={request_id:request.request_id,requested_language:request.language,language:request.language,available:true};
   window.model.payload=JSON.stringify(p);window.__handlers['viewEnv.onDataChanged']();
  };
 });
 await page.setContent(gamefaceHtml);await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'..','ledger.js'),'utf8')});
 await page.waitForFunction(()=>window.__nativeSize.width===184&&window.__nativeSize.height===144);
 async function update(patch){await page.evaluate(p=>{const v=JSON.parse(window.model.payload);Object.assign(v,p);window.model.payload=JSON.stringify(v);window.__handlers['viewEnv.onDataChanged']();},patch);}
 async function circle(){return page.evaluate(()=>{
  const r=document.getElementById('lc-window').getBoundingClientRect(),button=document.getElementById('lc-minimized-restore'),b=button.getBoundingClientRect(),
    path=document.querySelector('#lc-minimized .lc-progress-ring-value'),s=getComputedStyle(document.getElementById('lc-window'));
  return {width:r.width,height:r.height,label:document.getElementById('lc-minimized-percent').textContent,aria:button.getAttribute('aria-label'),offset:Number(path.getAttribute('stroke-dashoffset')),
    painted:getComputedStyle(path).display!=='none',stroke:getComputedStyle(path).stroke,background:s.backgroundColor,border:s.borderTopWidth,
    contained:b.left>=r.left&&b.right<=r.right&&b.top>=r.top&&b.bottom<=r.bottom};
 });}
 let c=await circle();assert.strictEqual(c.label,'81,2%');assert.strictEqual(c.width,184);assert.strictEqual(c.height,144);assert(c.contained);
 assert.strictEqual(c.border,'0px');assert.strictEqual(c.background,'rgba(0, 0, 0, 0)');assert(c.aria.includes('81,2'));
 assert(Math.abs(c.offset-301.5929*(1-0.8115396))<0.01&&c.painted);
 assert.strictEqual(await page.locator('.lc-progress-ring circle').count(),0,'Dash strokes must use SVG paths in Gameface');
 assert.strictEqual(await page.locator('.lc-progress-ring [pathLength]').count(),0);
 await page.locator('#lc-window').screenshot({path:path.join(__dirname,'progress-circle-minimized.png'),omitBackground:true});
 const financial=await page.evaluate(()=>{const p=JSON.parse(window.model.payload);return {goal:p.goal,summary:p.summary,balance:p.balance,wallet:p.wallet};});
 const handle=page.locator('#lc-minimized-move');
 async function hidden(){await page.waitForFunction(()=>getComputedStyle(document.getElementById('lc-minimized-move')).opacity==='0');}
 await hidden();
 assert.strictEqual(await page.locator('#lc-minimized-target').textContent(),'2.500.000');
 assert.strictEqual(await page.locator('#lc-minimized-goal-label').textContent(),'Meta');
 assert.strictEqual(await page.locator('#lc-minimized .lc-progress-ring-value').evaluate(n=>getComputedStyle(n).strokeWidth),'8px');
 assert.strictEqual(c.stroke,'rgb(152, 213, 123)');
 const surface=page.locator('#lc-minimized-drag-bar');
 const restingSurface=await surface.evaluate(n=>({color:getComputedStyle(n).backgroundColor,shadow:getComputedStyle(n).boxShadow}));
 const disk=await page.locator('#lc-minimized-restore').boundingBox();
 assert.strictEqual(disk.width,112);assert.strictEqual(disk.height,112);
 assert.strictEqual(await page.locator('#lc-minimized-restore').evaluate(n=>getComputedStyle(n).borderRadius),'56px');
 await page.locator('#lc-minimized-restore').hover();
 await page.waitForFunction(()=>getComputedStyle(document.getElementById('lc-minimized-move')).opacity==='1');
 const selectedSurface=await surface.evaluate(n=>({color:getComputedStyle(n).backgroundColor,shadow:getComputedStyle(n).boxShadow}));
 assert.notStrictEqual(selectedSurface.color,restingSurface.color);
 assert.notStrictEqual(selectedSurface.shadow,'none');
 const circleEdges=[{x:56,y:2},{x:110,y:56},{x:56,y:110},{x:2,y:56}];
 for(const edge of circleEdges){
  const point={x:disk.x+edge.x,y:disk.y+edge.y};
  assert.strictEqual(await page.evaluate(p=>document.elementFromPoint(p.x,p.y).id,point),'lc-minimized-restore','The outer circle must be part of the active button');
  await page.mouse.move(point.x,point.y);
  assert.deepStrictEqual(await surface.evaluate(n=>({color:getComputedStyle(n).backgroundColor,shadow:getComputedStyle(n).boxShadow})),selectedSurface);
 }
 assert.strictEqual(await page.evaluate(p=>document.elementFromPoint(p.x+1,p.y+1).id, disk)==='lc-minimized-restore',false,'Transparent corners must not become part of the circle');
 await handle.hover();await page.waitForTimeout(200);
 assert.strictEqual(await handle.evaluate(n=>getComputedStyle(n).opacity),'1','Handle must survive crossing the short gap');
 await page.locator('#lc-window').screenshot({path:path.join(__dirname,'progress-circle-hover.png'),omitBackground:true});
 const box=await handle.boundingBox();
 await page.mouse.move(box.x+36,box.y+16);await page.mouse.down();await page.mouse.move(4,4);
 assert.strictEqual(await handle.evaluate(n=>getComputedStyle(n).opacity),'1','Keep handle visible while dragging');
 await page.mouse.up();await hidden();
 assert.deepStrictEqual(await surface.evaluate(n=>({color:getComputedStyle(n).backgroundColor,shadow:getComputedStyle(n).boxShadow})),restingSurface,'Hover must clear after leaving');
 assert.deepStrictEqual(await page.evaluate(()=>window.__circleMoves),[true,false]);
 assert.deepStrictEqual(await page.evaluate(()=>window.__modeCalls),[],'Dragging must not open the widget');
 await page.locator('#lc-minimized-restore').focus();await page.keyboard.press('Tab');
 assert.strictEqual(await handle.evaluate(n=>document.activeElement===n),true);
 assert.strictEqual(await handle.evaluate(n=>getComputedStyle(n).opacity),'1','Tab exposes the handle');
 await page.mouse.click(4,4);await hidden();
 await page.locator('#lc-minimized-restore').focus();await page.keyboard.press('Enter');
 await page.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208);
 assert.strictEqual(await page.locator('#lc-widget-close .lc-progress-circle-label').textContent(),'81,2%');
 await page.locator('#lc-window').screenshot({path:path.join(__dirname,'progress-circle-widget.png')});
 await page.locator('#lc-widget-close').click();await page.waitForFunction(()=>window.__nativeSize.width===184);
 assert.deepStrictEqual(await page.evaluate(()=>{const p=JSON.parse(window.model.payload);return {goal:p.goal,summary:p.summary,balance:p.balance,wallet:p.wallet};}),financial);
 for(const edge of circleEdges){
  const b=await page.locator('#lc-minimized-restore').boundingBox();
  await page.mouse.click(b.x+edge.x,b.y+edge.y);
  await page.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208);
  await page.locator('#lc-widget-close').click();
  await page.waitForFunction(()=>window.__nativeSize.width===184&&window.__nativeSize.height===144);
 }
 assert.deepStrictEqual(await page.evaluate(()=>{const p=JSON.parse(window.model.payload);return {goal:p.goal,summary:p.summary,balance:p.balance,wallet:p.wallet};}),financial);
 checks.push('The full112px circular hit area highlights on its center and all four edges, opens from each edge, preserves transparent corners and real progress, and clears its circular hover after leaving; move-handle dragging remains separate');
 const zero=Object.assign({},payload.goal,{current:0,remaining:2500000,progress_percent:0});await update({goal:zero});c=await circle();assert.strictEqual(c.label,'0,0%');assert(!c.painted);
 await update({goal:Object.assign({},zero,{current:-50000})});assert.strictEqual(await page.locator('#lc-minimized-percent').evaluate(n=>getComputedStyle(n).color),'rgb(240, 113, 113)');
 await update({goal:Object.assign({},zero,{current:2500000,remaining:0,progress_percent:100,complete:true})});c=await circle();assert.strictEqual(c.label,'100%');assert.strictEqual(c.offset,0);assert.strictEqual(c.stroke,'rgb(141, 211, 106)');
 await update({goal:Object.assign({},zero,{active:false,target:0})});c=await circle();assert.strictEqual(c.label,'—');assert(!c.painted&&c.aria.includes('Sin meta activa'));
 await page.locator('#lc-window').screenshot({path:path.join(__dirname,'progress-circle-inactive.png'),omitBackground:true});
 await update({goal:payload.goal,ready:false});c=await circle();assert.strictEqual(c.label,'—');assert(!c.painted&&c.aria.includes('pendiente'));
 await update({goal:payload.goal,ready:true});
 await page.locator('#lc-minimized-restore').click();await page.locator('#lc-widget-details').click();await page.locator('#lc-language-en').click();
 await page.locator('#lc-close').click();await page.waitForFunction(()=>window.__nativeSize.width===184);
 c=await circle();assert.strictEqual(c.label,'81.2%');assert(c.aria.startsWith('Show credit ledger'));
 assert.strictEqual(await page.locator('#lc-minimized-goal-label').textContent(),'Goal');
 assert.strictEqual(await page.locator('#lc-minimized-target').textContent(),'2,500,000');
 await update({goal:Object.assign({},payload.goal,{current:1500000,progress_percent:60,remaining:1000000})});c=await circle();assert.strictEqual(c.label,'60.0%');assert(Math.abs(c.offset-120.63716)<0.01);
 assert.deepStrictEqual(await page.evaluate(()=>window.__circleFinancialWrites),[]);
 const initialGoal=Object.assign({},payload.goal,{target:100000,current:25000,remaining:75000,progress_percent:25});
 await page.locator('#lc-minimized-restore').click();await page.locator('#lc-widget-details').click();await page.locator('#lc-language-es').click();
 await page.locator('#lc-close').click();await page.waitForFunction(()=>window.__nativeSize.width===184);
 await update({goal:initialGoal});
 assert.strictEqual(await page.locator('#lc-minimized-target').textContent(),'100.000');
 assert.strictEqual(await page.locator('#lc-minimized-percent').textContent(),'25,0%');
 await page.mouse.move(4,4);await hidden();
 await page.locator('#lc-window').screenshot({path:path.join(__dirname,'progress-circle-initial-goal.png'),omitBackground:true});
 await page.locator('#lc-minimized-restore').hover();
 await page.locator('#lc-window').screenshot({path:path.join(__dirname,'progress-circle-initial-hover.png'),omitBackground:true});
 await update({goal:Object.assign({},initialGoal,{target:9007199254740991})});
 const targetFit=await page.locator('#lc-minimized-target').evaluate(n=>({width:n.clientWidth,content:n.scrollWidth,text:n.textContent}));
 assert(targetFit.content<=targetFit.width,'Largest supported goal must fit in the circle');
 assert(targetFit.text.includes('B'));
 assert((await page.locator('#lc-minimized-restore').getAttribute('aria-label')).includes('9.007.199.254.740.991'));
 await page.close();
 checks.push('Approved112px green8px ring shows live percentage and exact goal, localized Meta/Goal, first-use100000 and compact large amounts; hover/keyboard move handle hides on exit, native dragging cannot open the widget, and no money, goals or history are changed');
};
