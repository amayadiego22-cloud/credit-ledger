/* Headless bilingual integration QA only. Never loaded by World of Tanks. */
const fs=require('fs'),path=require('path'),assert=require('assert');
module.exports=async function qaBilingual(env){
    const {context,gamefaceHtml,nativeBootstrap,installQaArt,checks,errors,example,vehiclePayload,
        xmGroup,pzGroup,modeXmGroup,archiveModes,archivePayload,skirmishRow,chooseVehicle,chooseFilter,
        vehicleResponse,assertSignColor}=env;
    const source=fs.readFileSync(path.join(__dirname,'..','ledger.js'),'utf8');
    async function createSurface(payload,viewport){
        const surface=await context.newPage();surface.on('pageerror',e=>errors.push(String(e)));
        await surface.setViewportSize(viewport||{width:1100,height:1050});
        await surface.evaluate(installQaArt);await surface.evaluate(nativeBootstrap,JSON.parse(JSON.stringify(payload)));
        await surface.evaluate(()=>{
            window.isDomBuilt=true;window.__nativeReady=true;window.__languageCalls=[];window.__archiveCalls=[];window.__otherMutations=[];
            window.model.onSetLanguage=function(args){window.__languageCalls.push(args);};
            window.model.onSelectHistoryDay=function(args){window.__archiveCalls.push(args);};
            for(const name of ['onSaveGoal','onResetGoal','onResetHistory','onSaveHistory','onRefresh']){
                window.model[name]=function(args){window.__otherMutations.push([name,args]);};
            }
        });
        await surface.setContent(gamefaceHtml);await surface.addScriptTag({content:source});
        await surface.waitForFunction(()=>document.getElementById('lc-language-en'));
        return surface;
    }
    async function update(surface,patch){await surface.evaluate(patch=>{
        const payload=JSON.parse(window.model.payload);Object.assign(payload,patch);
        window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
    },patch);}
    async function clickLanguage(surface,language){
        await surface.locator('#lc-language-'+language).click();
        return surface.evaluate(()=>window.__languageCalls.slice(-1)[0]);
    }
    async function acknowledge(surface,request,available=true,saved=request.language){
        await update(surface,{language:saved,language_selection:{request_id:String(request.request_id),
            requested_language:request.language,language:saved,available,error:available?null:'Language could not be saved.'}});
    }
    async function assertNoMutations(surface){assert.deepStrictEqual(await surface.evaluate(()=>window.__otherMutations),[]);}
    async function financeSnapshot(surface){return surface.evaluate(()=>{
        const p=JSON.parse(window.model.payload);return {balance:p.balance,summary:p.summary,goal:p.goal,wallet:p.wallet,
            history:p.history,rewards:p.rewards,history_control:p.history_control,
            vehicle_selection:p.vehicle_selection,history_archive:p.history_archive};
    });}
    async function displaySnapshot(surface){return surface.evaluate(()=>{
        const target=document.getElementById('lc-target');
        return {digits:target.value.replace(/\D/g,''),caretDigits:target.value.slice(0,target.selectionStart).replace(/\D/g,'').length,
            mainNet:document.getElementById('lc-detail-net').textContent.replace(/[.,]/g,''),
            archiveNet:document.getElementById('lc-archive-net').textContent.replace(/[.,]/g,''),
            contentScroll:document.getElementById('lc-content').scrollTop,
            archiveScroll:document.getElementById('lc-archive-battle-options').scrollTop,
            historyExpanded:document.getElementById('lc-history-toggle').getAttribute('aria-expanded'),
            archiveExpanded:document.getElementById('lc-archive-toggle').getAttribute('aria-expanded'),
            vehicleArt:document.querySelector('#lc-vehicle-icon img')?.getAttribute('data-native-src'),
            selectedBattle:Array.from(document.querySelectorAll('#lc-history-list .lc-history-battle')).findIndex(n=>n.classList.contains('lc-history-option-selected')),
            selectedArchiveBattle:Array.from(document.querySelectorAll('#lc-archive-battle-list .lc-history-battle')).findIndex(n=>n.classList.contains('lc-history-option-selected'))};
    });}
    async function assertHeaderBounds(surface){
        const result=await surface.evaluate(()=>{
            const outer=document.getElementById('lc-window').getBoundingClientRect();
            const nodes=['lc-language-es','lc-language-en','lc-back-widget','lc-close'].map(id=>{
                const r=document.getElementById(id).getBoundingClientRect();return {id,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};
            });
            return {width:outer.width,outer:{left:outer.left,right:outer.right,top:outer.top,bottom:outer.bottom},nodes};
        });
        for(const n of result.nodes){assert(n.width>0&&n.height>0,'Language/header control must be selectable: '+n.id);
            assert(n.left>=result.outer.left-1&&n.right<=result.outer.right+1&&n.top>=result.outer.top-1&&n.bottom<=result.outer.bottom+1,
                'Language/header control must fit native surface: '+JSON.stringify(n));}
        for(let i=0;i<result.nodes.length;i++)for(let j=i+1;j<result.nodes.length;j++){
            const a=result.nodes[i],b=result.nodes[j];assert(a.right<=b.left+1||b.right<=a.left+1||a.bottom<=b.top+1||b.bottom<=a.top+1,
                'Language/header controls overlap: '+a.id+' and '+b.id);
        }
        return result;
    }
    const payload=JSON.parse(JSON.stringify(vehiclePayload));
    payload.view_mode='details';delete payload.language;delete payload.language_selection;
    payload.message='Datos de tu cuenta actual';
    payload.goal=Object.assign({},example.goal,{current:450000,remaining:2550000,progress_percent:15});
    payload.history_archive=JSON.parse(JSON.stringify(archivePayload.history_archive));
    const surface=await createSurface(payload);
    await surface.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'es');
    assert.strictEqual(await surface.locator('#lc-title').textContent(),'Economía de tu cuenta');
    assert((await surface.locator('#lc-archive-toggle').textContent()).includes('Historial por día'));
    assert.strictEqual(await surface.locator('#lc-language-es').textContent(),'Español');
    assert.strictEqual(await surface.locator('#lc-language-en').textContent(),'English');
    assert.deepStrictEqual(await surface.evaluate(()=>window.__languageCalls),[]);
    await assertHeaderBounds(surface);
    await surface.locator('#lc-window').screenshot({path:path.join(__dirname,'bilingual-es-preview.png')});
    checks.push('Spanish is the default without a saved preference, Historial por día replaces Previous days and both language controls fit the actual1040x976 Gameface header without sending a command on load');

    await surface.locator('#lc-target').fill('7654321');
    await surface.locator('#lc-target').evaluate(n=>n.setSelectionRange(3,3));
    await chooseFilter(surface,'mode:20');await chooseVehicle(surface,'vehicle:321');
    const request=await surface.evaluate(()=>window.__vehicleFilterCalls.slice(-1)[0]);
    const rows=Array.from({length:8},(_,i)=>Object.assign({},skirmishRow,{battle_id:'language-skirmish-'+i}));
    await vehicleResponse(surface,request,modeXmGroup,rows);
    await surface.locator('#lc-history-toggle').click();await surface.locator('#lc-history-list .lc-history-battle').nth(3).click();
    await surface.locator('#lc-archive-toggle').click();
    const archiveRequest=await surface.evaluate(()=>window.__archiveCalls.slice(-1)[0]);
    const selection={day_key:archiveRequest.day_key,label:payload.history_archive.days[0].label,
        account_context:archiveRequest.account_context,mode_key:'all',vehicle_key:'all',request_id:String(archiveRequest.request_id),available:true,
        summary:xmGroup.summary,history_total:110,history:rows,mode_groups:archiveModes,vehicle_groups:[xmGroup,pzGroup],external_credits:20000};
    await surface.evaluate(selection=>{const p=JSON.parse(window.model.payload);p.history_archive.selection=selection;
        window.model.payload=JSON.stringify(p);window.__handlers['viewEnv.onDataChanged']();},selection);
    await surface.locator('#lc-archive-battle-list .lc-history-battle').nth(2).click();
    await surface.locator('#lc-archive-battle-options').evaluate(n=>n.scrollTop=66);
    await surface.locator('#lc-content').evaluate(n=>n.scrollTop=180);
    const beforeSwitch=await displaySnapshot(surface),financeBefore=await financeSnapshot(surface);
    const callCounts=await surface.evaluate(()=>({vehicle:window.__vehicleFilterCalls.length,archive:window.__archiveCalls.length}));
    const english=await clickLanguage(surface,'en');
    assert.deepStrictEqual(english,{language:'en',request_id:english.request_id});
    assert(Number.isInteger(english.request_id)&&english.request_id>0);
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'en');
    assert.strictEqual(await surface.locator('#lc-title').textContent(),'Your credit overview');
    assert.strictEqual(await surface.locator('#lc-target').inputValue(),'7,654,321');
    await acknowledge(surface,english);
    assert.deepStrictEqual(await displaySnapshot(surface),beforeSwitch);
    assert.deepStrictEqual(await financeSnapshot(surface),financeBefore);
    assert.deepStrictEqual(await surface.evaluate(()=>({vehicle:window.__vehicleFilterCalls.length,archive:window.__archiveCalls.length})),callCounts);
    await assertNoMutations(surface);
    checks.push('Switching immediately to English and accepting a native string-ID acknowledgement preserves financial payload, active goal progress, unsaved digits and digit caret, mode/tank/current battle, archive battle and scroll positions without refetching filters or resetting anything');
    assert.strictEqual(await surface.locator('#lc-detail-net').textContent(),'-500');
    assert.strictEqual(await surface.locator('#lc-percent').textContent(),'15.0 %');
    assert((await surface.locator('#lc-vehicle-label').textContent()).includes('XM57'));
    assert((await surface.locator('#lc-vehicle-label').textContent()).includes('Tier VIII'));
    assert((await surface.locator('#lc-goal-since').textContent()).includes('local time'));
    assert((await surface.locator('#lc-wallet-period').textContent()).includes('local time'));
    assert((await surface.locator('#lc-archive-toggle').textContent()).includes('Daily battle history'));
    const englishStatic=await surface.locator('#lc-details').textContent();
    for(const text of ['Gross earnings','Repairs','Ammunition','Consumables','Personal reserve','Clan reserve','Reset battle history'])assert(englishStatic.includes(text),'English UI is missing '+text);
    for(const text of ['Ganancia o pérdida','Tu meta','Ingresos brutos','Reparaciones','Conciliación','Reiniciar historial','Todas las partidas','Modo de juego:'])assert(!englishStatic.includes(text),'English interface retains a Spanish UI phrase: '+text);
    for(const attribute of ['title','aria-label']){
        const values=await surface.locator('#lc-details ['+attribute+']').evaluateAll((nodes,attribute)=>nodes.map(n=>n.getAttribute(attribute)),attribute);
        assert(!values.some(text=>/Arrastra|Desplazar|Reiniciar|créditos|Minimizar/.test(text)),'English tooltips and accessibility labels must be translated: '+values.join('|'));
    }
    await assertHeaderBounds(surface);await surface.locator('#lc-content').evaluate(n=>n.scrollTop=0);
    await surface.locator('#lc-window').screenshot({path:path.join(__dirname,'bilingual-en-preview.png')});
    checks.push('English static labels, dynamic tier/progress and accessibility/tooltips use clear accounting terms and English number separators while native vehicle identity and negative red accounting remain unchanged');

    const languageCalls=await surface.evaluate(()=>window.__languageCalls.length);
    await surface.locator('#lc-language-en').click();
    for(let i=0;i<4;i++)await surface.evaluate(()=>window.__handlers['viewEnv.onDataChanged']());
    assert.strictEqual(await surface.evaluate(()=>window.__languageCalls.length),languageCalls);
    const spanish=await clickLanguage(surface,'es');assert(spanish.request_id>english.request_id);
    await acknowledge(surface,english,true,'en');
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'es','Old English acknowledgement cannot override the newer Spanish choice');
    await acknowledge(surface,spanish,false,'en');
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'en');
    assert.strictEqual(await surface.locator('#lc-language-retry').isVisible(),true);
    assert((await surface.locator('#lc-language-status').textContent()).length>0);
    await surface.locator('#lc-language-retry').click();
    const retried=await surface.evaluate(()=>window.__languageCalls.slice(-1)[0]);
    assert.strictEqual(retried.language,'es');assert(retried.request_id>spanish.request_id);
    await acknowledge(surface,retried);
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'es');
    assert.strictEqual(await surface.locator('#lc-language-retry').isVisible(),false);
    assert.strictEqual(await surface.locator('#lc-target').inputValue(),'7.654.321');
    await assertNoMutations(surface);
    checks.push('Repeated same-language clicks and model updates do not resend settings; stale acknowledgements cannot undo a newer choice, storage failures roll back visibly and Retry persists the requested language with a fresh request ID');

    await surface.evaluate(()=>{window.__savedSetTimeout=window.setTimeout;window.setTimeout=function(fn,delay){return window.__savedSetTimeout(fn,delay===6000?40:delay);};});
    const timedOut=await clickLanguage(surface,'en');
    await surface.waitForFunction(()=>!document.getElementById('lc-language-retry').classList.contains('lc-hidden'),{timeout:10000});
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'es');
    await surface.evaluate(()=>{window.setTimeout=window.__savedSetTimeout;});
    await surface.locator('#lc-language-retry').click();
    const afterTimeout=await surface.evaluate(()=>window.__languageCalls.slice(-1)[0]);
    assert(afterTimeout.request_id>timedOut.request_id);
    await acknowledge(surface,timedOut);
    await acknowledge(surface,afterTimeout);
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'en');
    await assertNoMutations(surface);
    checks.push('An unacknowledged language change times out to the last saved language with a visible retry, ignores the obsolete late response after retry and recovers without a game restart or financial mutation');
    const rapidSpanish=await clickLanguage(surface,'es');
    const rapidEnglish=await clickLanguage(surface,'en');
    assert(rapidEnglish.request_id>rapidSpanish.request_id);
    await acknowledge(surface,rapidSpanish);
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'en');
    await acknowledge(surface,rapidEnglish);
    assert.strictEqual(await surface.locator('#lc-language-en').getAttribute('aria-pressed'),'true');
    assert.strictEqual(await surface.locator('#lc-language-es').getAttribute('aria-pressed'),'false');
    assert.strictEqual(await surface.locator('#lc-language-controls').getAttribute('aria-busy'),'false');
    await assertNoMutations(surface);
    checks.push('Rapid Spanish then English choices keep only the latest in-flight request authoritative, ignore the older successful response and settle the correct pressed/busy accessibility state');

    // Narrow Gameface layout must keep the language selection usable with the native window controls.
    await surface.setViewportSize({width:450,height:1000});
    await surface.evaluate(()=>{window.viewEnv.getClientSizePx=function(){return {width:450,height:1000};};window.dispatchEvent(new Event('resize'));});
    await surface.waitForFunction(()=>window.__nativeSize.width===402);
    assert.strictEqual((await assertHeaderBounds(surface)).width,402);
    await surface.locator('#lc-content').evaluate(n=>n.scrollTop=0);
    await surface.locator('#lc-window').screenshot({path:path.join(__dirname,'bilingual-en-narrow-preview.png')});
    const narrowSpanish=await clickLanguage(surface,'es');await acknowledge(surface,narrowSpanish);
    assert.strictEqual(await surface.locator('html').getAttribute('lang'),'es');
    const narrowEnglish=await clickLanguage(surface,'en');await acknowledge(surface,narrowEnglish);
    assert.strictEqual((await assertHeaderBounds(surface)).width,402);
    checks.push('Spanish and English language buttons remain separate selectable targets with Back to widget and Minimize at the actual402px Gameface width; switching keeps the same bounded surface');

    const widgetPayload=JSON.parse(JSON.stringify(example));widgetPayload.language='en';widgetPayload.view_mode='widget';
    widgetPayload.goal=Object.assign({},widgetPayload.goal,{target:2500000,current:2028849,remaining:471151,progress_percent:81.15396});
    widgetPayload.summary.net_credits=2028849;widgetPayload.summary.battle_count=19;widgetPayload.balance=24357991;
    const widget=await createSurface(widgetPayload,{width:700,height:300});
    await widget.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208);
    assert.strictEqual(await widget.locator('html').getAttribute('lang'),'en');
    assert.strictEqual(await widget.locator('#lc-widget-title').textContent(),'CREDIT GOAL');
    assert.strictEqual(await widget.locator('#lc-widget-percent').textContent(),'81.2 %');
    assert((await widget.locator('#lc-widget-progress').textContent()).includes('2,028,849'));
    assert((await widget.locator('#lc-widget-status').textContent()).includes('471,151'));
    const bounds=await widget.locator('#lc-widget').evaluate(n=>{const r=n.getBoundingClientRect();return {width:r.width,height:r.height,scrollWidth:n.scrollWidth,scrollHeight:n.scrollHeight};});
    assert(bounds.width<=624&&bounds.height<=208&&bounds.scrollWidth<=625&&bounds.scrollHeight<=209);
    assert.deepStrictEqual(await widget.evaluate(()=>window.__languageCalls),[]);
    await widget.locator('#lc-window').screenshot({path:path.join(__dirname,'bilingual-en-widget-preview.png')});
    checks.push('Saved English loads directly without sending another command and the624x208 widget shows English titles/status and comma-grouped81.2-percent progress without clipping or altered goal amounts');
    await widget.locator('#lc-widget-details').click();
    await widget.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
    assert.strictEqual(await widget.locator('#lc-title').textContent(),'Your credit overview');
    await widget.locator('#lc-close').click();
    await widget.waitForFunction(()=>window.__nativeSize.width===184&&window.__nativeSize.height===144);
    assert((await widget.locator('#lc-minimized-restore').getAttribute('aria-label')).startsWith('Show credit ledger'));
    await widget.locator('#lc-minimized-restore').click();
    await widget.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208);
    assert.strictEqual(await widget.locator('#lc-widget-title').textContent(),'CREDIT GOAL');
    assert.deepStrictEqual(await widget.evaluate(()=>window.__languageCalls),[]);
    await assertNoMutations(widget);
    checks.push('Saved English survives native details, minimized184x144 shortcut and restored widget transitions with localized accessibility names, unchanged goal data and no redundant language command');

    const states=[
        {name:'unknown',balance:null,goal:{target:0,baseline:null,current:null,remaining:null,progress_percent:0},summary:{net_credits:0},expected:'Pending'},
        {name:'zero',balance:0,goal:{target:0,baseline:0,current:0,remaining:0,progress_percent:0},summary:{net_credits:0},expected:'0'},
        {name:'negative',balance:-12,goal:{target:1000000,baseline:0,current:-12,remaining:1000012,progress_percent:0},summary:{net_credits:-12},expected:'-12'},
        {name:'large',balance:999999999999999,goal:{target:999999999999999,baseline:0,current:123456789012345,remaining:876543210987654,progress_percent:12.34567},summary:{net_credits:123456789012345},expected:'999,999,999,999,999'}
    ];
    await chooseFilter(surface,'all');await chooseVehicle(surface,'all');
    for(const state of states){
        await update(surface,{balance:state.balance,goal:Object.assign({},example.goal,state.goal),summary:Object.assign({},example.summary,state.summary)});
        assert.strictEqual(await surface.locator('#lc-balance').textContent(),state.expected,'English balance '+state.name);
        if(state.goal.target===0)assert.strictEqual(await surface.locator('#lc-percent').textContent(),'0.0 %','Inactive English goal uses the locale decimal point');
        await assertSignColor(surface.locator('#lc-net-total'),state.name==='negative'?'negative':state.name==='large'?'positive':'zero');
        assert(!/(NaN|undefined|Infinity)/.test(await surface.locator('#lc-details').textContent()),'English dynamic '+state.name+' must remain well formed');
    }
    checks.push('English unknown, zero, negative and fifteen-digit amounts stay honest and well formed with localized grouping, unchanged red/green/neutral rules and no NaN, undefined or false goal completion');

    const inputPayload=JSON.parse(JSON.stringify(example));inputPayload.language='en';inputPayload.view_mode='details';
    const inputSurface=await createSurface(inputPayload);
    await inputSurface.evaluate(()=>{window.__goalSaves=[];window.model.onSaveGoal=function(args){window.__goalSaves.push(args);};});
    await inputSurface.locator('#lc-target').fill('1,234,567');
    assert.strictEqual(await inputSurface.locator('#lc-target').inputValue(),'1,234,567');
    await inputSurface.locator('#lc-target').press('ArrowUp');
    assert.strictEqual(await inputSurface.locator('#lc-target').inputValue(),'1,334,567');
    await inputSurface.locator('#lc-target').press('ArrowDown');
    assert.strictEqual(await inputSurface.locator('#lc-target').inputValue(),'1,234,567');
    await inputSurface.locator('#lc-save-goal').click();
    assert.deepStrictEqual(await inputSurface.evaluate(()=>window.__goalSaves),[{value:'1234567',mode:'balance_growth'}]);
    assert.strictEqual(await inputSurface.locator('#lc-target').isDisabled(),true);
    await update(inputSurface,{goal:Object.assign({},example.goal,{target:1234567,active:true,remaining:1234567,final_balance:23234567})});
    assert.strictEqual(await inputSurface.locator('#lc-target').isDisabled(),false);
    await inputSurface.locator('#lc-target').fill('0');await inputSurface.locator('#lc-save-goal').click();
    assert.deepStrictEqual(await inputSurface.evaluate(()=>window.__goalSaves.slice(-1)[0]),{value:'0',mode:'balance_growth'});
    assert.deepStrictEqual(await inputSurface.evaluate(()=>window.__goalResetCalls),[]);
    checks.push('English grouped goal input and100000-credit keyboard steps send only canonical integer digits to the native save command; saving zero deactivates via the existing goal action and never invokes reset');

    const namedPayload=JSON.parse(JSON.stringify(example));namedPayload.language='en';namedPayload.view_mode='details';
    namedPayload.history[0].vehicles[0].name='Avance';
    namedPayload.rewards[0].parts[0].title='Escaramuza';
    namedPayload.rewards[0].parts.push({quest_id:'q-42',title:'Misión q-42',name_resolved:false,credits:5000});
    namedPayload.rewards[0].parts.push({quest_id:'crisol-01',title:'Crisol: Del día | Misión 01',name_resolved:true,credits:1000});
    namedPayload.rewards.push({kind:'battlePassReward',title:'Recompensa del pase de batalla',credits:10000,parts:[]});
    namedPayload.history.push(Object.assign({},namedPayload.history[0],{battle_id:'fallback-id',vehicles:[{vehicle_type_id:'654',name:'Vehículo 654',tier:11,icon:null}]}));
    const named=await createSurface(namedPayload);
    await named.locator('#lc-history-toggle').click();await named.locator('#lc-history-list .lc-history-battle').first().click();
    assert.strictEqual(await named.locator('#lc-detail-vehicles .lc-tank-name').textContent(),'Avance');
    assert.deepStrictEqual(await named.locator('#lc-rewards-list .lc-reward-title').allTextContents(),['Escaramuza','Mission q-42','Crucible: Del día | Mission 01','Battle Pass reward']);
    assert((await named.locator('#lc-detail-mode').textContent()).includes('Random Battle'));
    assert((await named.locator('#lc-detail-vehicles .lc-tank-tier').textContent()).includes('Tier VIII'));
    await named.locator('#lc-history-toggle').click();await named.locator('#lc-history-list .lc-history-battle').nth(1).click();
    assert.strictEqual(await named.locator('#lc-detail-vehicles .lc-tank-name').textContent(),'Vehicle 654');
    assert((await named.locator('#lc-detail-vehicles .lc-tank-tier').textContent()).includes('Tier XI'));
    checks.push('Native tank and mission names remain literal even when identical to catalog phrases; tiers, modes, unresolved vehicle/mission placeholders and mod-generated Battle Pass/Crucible wrappers translate independently');

    const invalidPayload=JSON.parse(JSON.stringify(example));invalidPayload.language='fr';invalidPayload.view_mode='details';
    const invalid=await createSurface(invalidPayload);
    assert.strictEqual(await invalid.locator('html').getAttribute('lang'),'es');
    assert.strictEqual(await invalid.locator('#lc-title').textContent(),'Economía de tu cuenta');
    assert.deepStrictEqual(await invalid.evaluate(()=>window.__languageCalls),[]);
    await invalid.evaluate(()=>window.dispatchEvent(new Event('unload')));
    assert.strictEqual(await invalid.evaluate(()=>Object.prototype.hasOwnProperty.call(window.__handlers,'viewEnv.onDataChanged')),false);
    await assertNoMutations(invalid);
    await surface.evaluate(()=>window.dispatchEvent(new Event('unload')));
    assert.strictEqual(await surface.evaluate(()=>Object.prototype.hasOwnProperty.call(window.__handlers,'viewEnv.onDataChanged')),false);
    checks.push('Unsupported saved locales fall back safely to Spanish without overwriting preferences; native unload removes language/model observers and leaves finances, history and goals untouched');
    await Promise.all([surface.close(),widget.close(),invalid.close(),inputSurface.close(),named.close()]);
};
