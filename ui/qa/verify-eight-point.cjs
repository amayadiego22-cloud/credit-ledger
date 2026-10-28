/* Geometry regression checks on real rendered controls; QA only. */
const assert=require('assert'),fs=require('fs'),path=require('path');
module.exports=async function verifyEightPoint(env){
    const {context,gamefaceHtml,nativeBootstrap,installQaArt,checks,example}=env;
    const page=await context.newPage();
    await page.setViewportSize({width:1100,height:1050});
    await page.evaluate(installQaArt);
    await page.evaluate(nativeBootstrap,JSON.parse(JSON.stringify(example)));
    await page.evaluate(()=>{window.isDomBuilt=true;window.__nativeReady=true;});
    await page.setContent(gamefaceHtml);
    await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'..','ledger.js'),'utf8')});
    await page.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
    const financial=await page.evaluate(()=>{const p=JSON.parse(window.model.payload);return {balance:p.balance,goal:p.goal,summary:p.summary};});
    const metrics=await page.evaluate(()=>{
        const cards=Array.from(document.querySelectorAll('.lc-stat')).map(n=>n.getBoundingClientRect());
        const content=getComputedStyle(document.getElementById('lc-content'));
        const goal=getComputedStyle(document.querySelector('.lc-goal'));
        return {cardGaps:cards.slice(1).map((r,i)=>r.left-cards[i].right),
            aligned:cards.every(r=>r.top===cards[0].top&&r.height===cards[0].height),
            contentPadding:[content.paddingTop,content.paddingLeft,content.paddingRight],goalPadding:goal.paddingLeft,
            field:document.getElementById('lc-target').getBoundingClientRect().height,
            save:document.getElementById('lc-save-goal').getBoundingClientRect().height,
            reset:document.getElementById('lc-reset-goal').getBoundingClientRect().height};
    });
    assert(metrics.aligned);metrics.cardGaps.forEach(gap=>assert(Math.abs(gap-16)<0.1));
    assert.deepStrictEqual(metrics.contentPadding,['24px','24px','32px']);
    assert.strictEqual(metrics.goalPadding,'24px');assert.strictEqual(metrics.field,48);
    assert.strictEqual(metrics.save,40);assert.strictEqual(metrics.reset,40);
    await page.locator('#lc-window').screenshot({path:path.join(__dirname,'eight-point-details-es.png')});
    await page.setViewportSize({width:850,height:900});
    await page.evaluate(()=>{window.viewEnv.getClientSizePx=()=>({width:850,height:900});window.__handlers.clientResized();});
    await page.waitForFunction(()=>window.__nativeSize.width===802);
    const two=await page.locator('.lc-stat').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom};}));
    assert(Math.abs(two[1].x-two[0].right-16)<0.1&&two[0].y===two[1].y&&two[2].y>two[0].bottom);
    await page.setViewportSize({width:450,height:850});
    await page.evaluate(()=>{window.viewEnv.getClientSizePx=()=>({width:450,height:850});window.__handlers.clientResized();});
    await page.waitForFunction(()=>window.__nativeSize.width===402);
    assert(await page.locator('.lc-stat').evaluateAll(nodes=>nodes.every(n=>n.scrollWidth<=n.clientWidth+1)));
    assert.deepStrictEqual(await page.evaluate(()=>{const p=JSON.parse(window.model.payload);return {balance:p.balance,goal:p.goal,summary:p.summary};}),financial);
    await page.close();
    checks.push('8pt grid keeps four equal-height cards and16px gutters,24px content/card insets,48px inputs and40px actions; reflows to two and one columns without clipping amounts or changing financial values');
};
