/* Headless visual/bridge verification only. This file is not a game asset. */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const {chromium} = require('playwright');
const ui = path.resolve(__dirname, '..');
const example = {
    schema: 1, ready: true, view_mode: 'details', message: 'Datos de prueba para verificar la interfaz', balance: 22000000,
    summary: {battle_count: 1, gross_credits: 56028,
        expenses: {repair: 33136, ammo: 106400, consumables: 30000, other: 0},
        net_credits: -113508, average_net_credits: -113508, pending_battles: 0},
    goal: {mode: 'balance_growth', target: 3000000, baseline: 22000000, final_balance: 25000000, since_utc: '2026-10-17T18:00:00Z',
        since_label:'17/10/2026 23:30 (hora local, UTC+05:30)',
        current: 0, remaining: 3000000, progress_percent: 0,
        complete: false, estimated_battles: null},
    history: [{battle_id: '999000111', occurred_at: '2026-10-17T19:57:00Z',
        time_label: '17 oct, 14:57', gross_credits: 56028,
        expenses: {repair: 33136, ammo: 106400, consumables: 30000, other: 0},
        net_credits: -113508, vehicles:[{vehicle_type_id:'321',name:'XM57',tier:8,icon:'coui://gui/maps/icons/vehicle/usa-A01_T1_Cunningham.png'}],
        battle_mode:{bonus_type:1,gui_type:1,label:'Batalla aleatoria'},
        rewards: [{title:'Crisol: misión de prueba',credits:50000}]}],
    wallet: {ready: true, baseline:22000000, balance:22000000, started_at:'2026-10-18T06:00:00Z',
        started_at_label:'18/10/2026 11:30 (hora local, UTC+05:30)',battle_net:0,external_credits:0,unclassified:0},
    rewards: [{time_label:'18/10 01:15', included_in_battle:true, credits:50000,parts:[{title:'Crisol: misión de prueba',credits:50000}]}], error: null,
    history_control: {mode:'manual',hour:6,preserve_goal:false,since_utc:'2026-10-18T02:30:00Z',generation:0,next_reset_utc:null,can_reset:true,
        since_label:'18/10/2026 08:00 (hora local, UTC+05:30)',next_reset_label:'',timezone_label:'Hora local del equipo (UTC+05:30)'}
};
function installQaArt(nativePreviewArt){
    // Original fixture drawings represent native-only local PNGs in Chrome QA.
    const source=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');
    const tank='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="144" height="76"><path d="M12 55h108l12-10-10-12H80l-9-17H45l-9 17H15z" fill="#929b79"/><path d="M63 22h68v6H63z" fill="#c0b581"/><rect x="9" y="52" width="116" height="17" rx="8" fill="#545c4a"/><path d="M21 60h92" stroke="#a3ac8c" stroke-width="4"/></svg>');
    const mode='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="29" fill="#323c3e" stroke="#adb0a2" stroke-width="3"/><circle cx="32" cy="32" r="22" fill="#6b3432"/><path d="m32 14 5 12 13 1-10 9 3 14-11-8-11 8 3-14-10-9 13-1z" fill="#cdb577"/></svg>');
    Object.defineProperty(HTMLImageElement.prototype,'src',{get:source.get,set:function(value){
        this.setAttribute('data-native-src',value);
        if(nativePreviewArt&&Object.prototype.hasOwnProperty.call(nativePreviewArt,value)){
            source.set.call(this,nativePreviewArt[value]);
        }else if(value.indexOf('coui://')===0){
            if(value.indexOf('missing')>=0){source.set.call(this,'data:image/png;base64,AA==');}
            else{source.set.call(this,value.indexOf('battleTypes/')>=0||value.indexOf('mode_selector/')>=0?mode:tank);}
        }else{source.set.call(this,value);}
    }});
}
(async function () {
    const context = await chromium.launchPersistentContext(process.env.CREDIT_LEDGER_QA_PROFILE || path.join(__dirname, 'chrome-profile'), {
        ...(process.env.CREDIT_LEDGER_CHROME ? {executablePath: process.env.CREDIT_LEDGER_CHROME} : {}),
        headless: true, viewport: {width: 1100, height: 850}, timezoneId:'Pacific/Honolulu',
        args: ['--disable-extensions', '--disable-background-networking', '--disable-component-update']
    });
    const page = await context.newPage();
    const errors = [];
    const checks = [];
    page.on('pageerror', error => errors.push(String(error)));
    try {
        await page.evaluate(installQaArt);
        await page.evaluate(function (payload) {
            window.__calls = [];
            window.__modeCalls = [];
            window.__handlers = {};
            window.isDomBuilt = true;
            window.engine = {
                whenReady: Promise.resolve(),
                enableImmediateLayout: function () {},
                on: function (name, handler) { window.__handlers[name] = handler; },
                off: function (name) { delete window.__handlers[name]; }
            };
            window.viewEnv = {
                addDataChangedCallback: function (name, id, sub) { window.__callback = [name, id, sub]; return 77; },
                removeDataChangedCallback: function (id, res) { window.__removed = [id, res]; }
            };
            window.model = {
                payload: JSON.stringify(payload),
                onSaveGoal: function (value) { window.__calls.push(['save', value]); },
                onResetGoal: function (value) { window.__calls.push(['goal-reset', value]); },
                onSetVehicleFilter: function (value) { window.__calls.push(['vehicle-filter', value]); },
                onSelectHistoryDay: function (value) { window.__calls.push(['archive', value]); },
                onClose: function (value) { window.__calls.push(['close', value]); },
                onRefresh: function (value) { window.__calls.push(['refresh', value]); },
                onSaveHistory: function (value) { window.__calls.push(['history-save', value]); },
                onResetHistory: function (value) { window.__calls.push(['history-reset', value]); },
                onSetViewMode: function (value) {
                    window.__modeCalls.push(value);
                    const current=JSON.parse(window.model.payload);
                    current.view_mode=value.mode;
                    window.model.payload=JSON.stringify(current);
                    window.setTimeout(function(){window.__handlers['viewEnv.onDataChanged']();},0);
                }
            };
        }, example);
        let html = fs.readFileSync(path.join(ui, 'LedgerView.html'), 'utf8');
        html = html.replace('<link rel="stylesheet" href="ledger.css">', '<style>' + fs.readFileSync(path.join(ui, 'ledger.css'), 'utf8') + '</style>');
        html = html.replace('<script src="ledger.js"></script>', '');
        const gamefaceHtml=html.replace('<style>','<style>div { display:flex; flex-direction:column; flex-shrink:0; } span { display:flex; flex-direction:row; flex-shrink:0; }</style><style>');
        await page.setContent(html);
        await page.addScriptTag({content: fs.readFileSync(path.join(ui, 'ledger.js'), 'utf8')});
        await page.waitForFunction(() => document.getElementById('lc-net-total').textContent === '-113.508');
        assert.strictEqual(await page.locator('#lc-repair').textContent(), '-33.136');
        assert.strictEqual(await page.locator('#lc-ammo').textContent(), '-106.400');
        assert.strictEqual(await page.locator('#lc-consumables').textContent(), '-30.000');
        assert.strictEqual(await page.locator('#lc-balance').textContent(), '22.000.000');
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(), '22.000.000');
        assert.strictEqual(await page.locator('#lc-goal-base-status').textContent(), 'Base de tu meta actual');
        assert.strictEqual(await page.locator('#lc-wallet-period').textContent(),'Seguimiento desde '+example.wallet.started_at_label);
        assert.strictEqual(await page.locator('#lc-goal-since').textContent(),'Meta iniciada: '+example.goal.since_label);
        assert.strictEqual(await page.locator('#lc-percent').textContent(), '0,0 %');
        assert((await page.locator('#lc-base-note').textContent()).includes('25.000.000'));
        assert.deepStrictEqual(await page.evaluate(() => window.__callback), ['model', 0, true]);
        checks.push('Actual observed battle amounts, native model subscription, negative color');
        const color = await page.locator('#lc-detail-net').evaluate(node => getComputedStyle(node).color);
        assert.strictEqual(color, 'rgb(240, 113, 113)');
        const signColors={positive:'rgb(141, 211, 106)',negative:'rgb(240, 113, 113)'};
        async function assertProgressScale(surface,meterSelector,fillSelector,marksSelector){
            assert.deepStrictEqual((await surface.locator(marksSelector).allTextContents()).map(text=>text.replace(/\s/g,'')),
                Array.from({length:10},(_,index)=>String((index+1)*10)+'%'));
            const scale=await surface.evaluate(function(selectors){
                const meter=document.querySelector(selectors.meter).getBoundingClientRect();
                const fill=document.querySelector(selectors.fill).getBoundingClientRect();
                const outer=document.getElementById('lc-window').getBoundingClientRect();
                const marks=Array.from(document.querySelectorAll(selectors.marks)).map(node=>{
                    const rect=node.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(node);
                    const label=range.getBoundingClientRect();
                    return {position:(rect.right-meter.left)/meter.width,
                        visible:rect.left>=outer.left&&rect.right<=outer.right+1&&rect.top>=meter.bottom-1&&rect.bottom<=outer.bottom+1,
                        labelFits:label.width>0&&label.left>=rect.left-1&&label.right<=rect.right+1&&label.top>=rect.top-1&&label.bottom<=rect.bottom+1};
                });
                return {meterHeight:meter.height,fillHeight:fill.height,marks};
            },{meter:meterSelector,fill:fillSelector,marks:marksSelector});
            assert.strictEqual(scale.meterHeight,12);
            assert.strictEqual(scale.fillHeight,12);
            scale.marks.forEach((mark,index)=>{
                assert(Math.abs(mark.position-(index+1)/10)<0.015,'Percentage mark must match its tenth of the bar');
                assert(mark.visible&&mark.labelFits,'Percentage label '+((index+1)*10)+' must fit without clipping');
            });
        }
        async function assertSignColor(locator, sign){
            const actual=await locator.evaluate(node=>({color:getComputedStyle(node).color,
                positive:node.classList.contains('lc-positive'),negative:node.classList.contains('lc-negative')}));
            if(sign==='zero'){
                assert.strictEqual(actual.positive,false);
                assert.strictEqual(actual.negative,false);
                assert.notStrictEqual(actual.color,signColors.positive);
                assert.notStrictEqual(actual.color,signColors.negative);
            }else{
                assert.strictEqual(actual.color,signColors[sign]);
                assert.strictEqual(actual[sign],true);
                assert.strictEqual(actual[sign==='positive'?'negative':'positive'],false);
            }
        }
        await assertSignColor(page.locator('#lc-gross'),'positive');
        for(const selector of ['#lc-repair','#lc-ammo','#lc-consumables']){
            await assertSignColor(page.locator(selector),'negative');
        }
        await assertSignColor(page.locator('#lc-balance'),'positive');
        await assertSignColor(page.locator('#lc-goal-base'),'positive');
        checks.push('Income is green and displayed deductions are red even when underlying expense fields are positive; positive balance and starting balance use the same color rule');
        await page.screenshot({path: path.join(__dirname, 'ledger-desktop.png')});
        async function updateReservePayload(payload){
            await page.evaluate(function(value){window.model.payload=JSON.stringify(value);window.__handlers['viewEnv.onDataChanged']();},payload);
        }
        function reservePayload(reserves,known,total){
            const payload=JSON.parse(JSON.stringify(example));
            payload.history[0].reserves=reserves;
            payload.summary.battle_count=total;
            payload.summary.reserves={personal:reserves?reserves.personal:0,clan:reserves?reserves.clan:0,known_battles:known,total_battles:total};
            return payload;
        }
        const reserveExample=reservePayload({personal:20000,clan:10000},1,1);
        reserveExample.history[0].rewards=[];
        reserveExample.rewards=[];
        await updateReservePayload(reserveExample);
        assert.strictEqual(await page.locator('#lc-reserve-personal').textContent(),'+20.000');
        assert.strictEqual(await page.locator('#lc-reserve-clan').textContent(),'+10.000');
        assert.strictEqual(await page.locator('#lc-reserve-note').textContent(),'Ya incluidas en los ingresos brutos.');
        await updateReservePayload(reservePayload({personal:20000,clan:10000},1,3));
        assert((await page.locator('#lc-reserve-note').textContent()).includes('1 de 3 partidas'));
        assert.strictEqual(await page.locator('#lc-reserve-personal').textContent(),'+20.000');
        await updateReservePayload(reservePayload(null,0,3));
        assert.strictEqual(await page.locator('#lc-reserve-personal').textContent(),'—');
        assert.strictEqual(await page.locator('#lc-reserve-clan').textContent(),'—');
        assert((await page.locator('#lc-reserve-note').textContent()).includes('ya están incluidos'));
        checks.push('Period reserve totals distinguish complete, partial and missing historical coverage without presenting unknown bonuses as zero');
        await updateReservePayload(reserveExample);
        await page.locator('#lc-history-toggle').click();
        await page.locator('.lc-history-battle').first().click();
        for(let repeat=0;repeat<3;repeat++) await updateReservePayload(reserveExample);
        assert.strictEqual(await page.locator('#lc-reserve-personal').count(),1);
        assert.strictEqual(await page.locator('#lc-reserve-clan').count(),1);
        await assertSignColor(page.locator('#lc-reserve-personal'),'positive');
        await assertSignColor(page.locator('#lc-reserve-clan'),'positive');
        assert.strictEqual(await page.locator('#lc-gross').textContent(),'+56.028');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-113.508');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'-113.508');
        assert.strictEqual(await page.locator('#lc-balance').textContent(),'22.000.000');
        assert.strictEqual(await page.locator('#lc-reserve-note').textContent(),'Ya incluidas en los ingresos brutos.');
        await page.locator('.lc-battle-panel').scrollIntoViewIfNeeded();
        await page.locator('.lc-battle-panel').screenshot({path:path.join(__dirname,'reserve-breakdown-preview.png')});
        checks.push('Selected battle itemizes positive personal and clan bonuses in green as already included; repeated native model updates do not duplicate rows or change gross, net, period total or account balance');
        await updateReservePayload(reservePayload({personal:0,clan:0},1,1));
        for(const selector of ['#lc-reserve-personal','#lc-reserve-clan']){
            assert.strictEqual(await page.locator(selector).textContent(),'0');
            await assertSignColor(page.locator(selector),'zero');
        }
        await updateReservePayload(reservePayload(null,0,1));
        assert.strictEqual(await page.locator('#lc-reserve-personal').textContent(),'—');
        assert.strictEqual(await page.locator('#lc-reserve-clan').textContent(),'—');
        assert((await page.locator('#lc-reserve-note').textContent()).includes('ya están incluidos'));
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-113.508');
        assert((await page.locator('#lc-history-label').textContent()).includes('XM57'));
        checks.push('Selected known-zero bonuses remain neutral while legacy unknown bonuses show dashes; updates preserve battle selection and real financial amounts');
        await page.locator('#lc-history-toggle').click();
        await page.locator('.lc-history-option').first().click();
        await updateReservePayload(example);
        await page.locator('#lc-content').evaluate(node=>node.scrollTop=0);
        const originalColorPayload=await page.evaluate(()=>JSON.parse(window.model.payload));
        for(const scenario of [
            {sign:'positive',net:10000,gross:12000,repair:1000,ammo:1000},
            {sign:'negative',net:-10000,gross:12000,repair:11000,ammo:11000},
            {sign:'zero',net:0,gross:0,repair:0,ammo:0}
        ]){
            await page.evaluate(function(test){
                const payload=JSON.parse(window.model.payload);
                const expenses={repair:test.repair,ammo:test.ammo,consumables:0,other:0};
                Object.assign(payload.summary,{gross_credits:test.gross,expenses,net_credits:test.net,average_net_credits:test.net});
                Object.assign(payload.history[0],{gross_credits:test.gross,expenses,net_credits:test.net});
                payload.balance=22000000+test.net;
                Object.assign(payload.wallet,{balance:payload.balance,battle_net:test.net,external_credits:0,unclassified:0});
                Object.assign(payload.goal,{active:true,current:test.net,remaining:3000000-test.net,progress_percent:Math.max(0,test.net/3000000*100)});
                window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
            },scenario);
            for(const selector of ['#lc-net-total','#lc-detail-net','#lc-wallet-battles',
                '#lc-history-list .lc-history-net','#lc-widget-period .lc-amount',
                '#lc-widget-progress .lc-amount','#lc-progress-text .lc-amount']){
                await assertSignColor(page.locator(selector).first(),scenario.sign);
            }
            if(scenario.sign==='zero'){
                for(const selector of ['#lc-gross','#lc-repair','#lc-ammo','#lc-consumables']){
                    await assertSignColor(page.locator(selector),'zero');
                }
            }
            assert.strictEqual(await page.locator('#lc-net-total').textContent(),scenario.net<0?'-10.000':scenario.net>0?'+10.000':'+0');
        }
        await page.evaluate(function(payload){window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();},originalColorPayload);
        checks.push('Native updates replace positive, negative and zero colors across summary, breakdown, history, wallet and inline widget/goal amounts without changing their displayed values');
        await page.setViewportSize({width:1100,height:1050});
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            payload.message='Datos de prueba para verificar el diseño';payload.balance=24052083;
            Object.assign(payload.summary,{battle_count:17,gross_credits:2084522,
                expenses:{repair:79561,ammo:149020,consumables:133000,other:0},net_credits:1722941,average_net_credits:101349});
            Object.assign(payload.goal,{active:true,target:2000000,baseline:22329142,final_balance:24329142,
                current:1722941,remaining:277059,progress_percent:86.14705,complete:false,
                since_utc:'2026-10-19T00:24:00Z',since_label:'18/10/2026 19:24 (hora local, UTC-05:00)'});
            Object.assign(payload.wallet,{baseline:22329142,balance:24052083,battle_net:1722941,external_credits:0,unclassified:0,
                started_at:'2026-10-19T00:24:00Z',started_at_label:'18/10/2026 19:24 (hora local, UTC-05:00)'});
            Object.assign(payload.history_control,{since_utc:'2026-10-19T00:24:00Z',
                since_label:'18/10/2026 19:24 (hora local, UTC-05:00)',timezone_label:'Hora local del equipo (UTC-05:00)'});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        await page.locator('#lc-content').evaluate(n=>n.scrollTop=0);
        await page.waitForFunction(()=>document.getElementById('lc-window').getBoundingClientRect().height===976);
        await assertProgressScale(page,'#lc-meter','#lc-fill','.lc-detail-marks .lc-widget-mark');
        await page.locator('#lc-window').screenshot({path:path.join(__dirname,'details-redesign-preview.png')});
        await page.locator('#lc-window').screenshot({path:path.join(__dirname,'four-cards-preview.png')});
        const fourCardsPayload=await page.evaluate(()=>JSON.parse(window.model.payload));
        await page.evaluate(function(payload){window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();},originalColorPayload);
        await page.setViewportSize({width:1100,height:850});
        const target = page.locator('#lc-target');
        await page.evaluate(function () {
            const value = JSON.parse(window.model.payload);
            value.goal = {target:0,current:0,progress_percent:0,baseline:null,active:false};
            window.model.payload = JSON.stringify(value);
            window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await target.inputValue(), '0');
        assert.strictEqual(await page.locator('#lc-save-goal').textContent(),'Guardar sin meta');
        assert.strictEqual(await page.locator('#lc-save-goal').isDisabled(), false);
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'\u2014');
        await page.locator('#lc-target-up').click();
        assert.strictEqual(await target.inputValue(), '100.000');
        await page.locator('#lc-target-up').click();
        assert.strictEqual(await target.inputValue(), '200.000');
        await page.locator('#lc-target-down').click();
        assert.strictEqual(await target.inputValue(), '100.000');
        await target.fill('50000');
        await target.press('ArrowDown');
        assert.strictEqual(await target.inputValue(), '0');
        await target.press('ArrowUp');
        assert.strictEqual(await target.inputValue(), '100.000');
        assert.strictEqual(await page.locator('#lc-percent').textContent(), '0,0 %');
        checks.push('Zero initial goal stays inactive; buttons and keyboard change 100,000 with minimum zero');
        await target.fill('');
        await target.pressSequentially('1000000');
        assert.strictEqual(await target.inputValue(), '1.000.000');
        assert.strictEqual(await page.evaluate(() => window.__calls.length), 0);
        await target.evaluate(node => node.setSelectionRange(3, 3));
        await target.press('9');
        assert.strictEqual(await target.inputValue(), '10.900.000');
        const draft = await target.inputValue();
        const caret = await target.evaluate(node => node.selectionStart);
        await page.evaluate(function () { window.__handlers['viewEnv.onDataChanged'](); });
        assert.strictEqual(await target.inputValue(), draft);
        assert.strictEqual(await target.evaluate(node => node.selectionStart), caret);
        checks.push('Digit grouping and middle caret; unsaved draft preserved on native update');
        await page.locator('#lc-save-goal').click();
        assert.deepStrictEqual(await page.evaluate(() => window.__calls[0]), ['save', {value: '10900000', mode: 'balance_growth'}]);
        assert.strictEqual(await page.locator('#lc-reset-goal').isDisabled(),true);
        const normalSaveCalls=await page.evaluate(()=>window.__calls.length);
        await page.locator('#lc-reset-goal').dispatchEvent('click');
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),normalSaveCalls);
        assert.strictEqual(await target.isDisabled(), true);
        await page.evaluate(function () {
            const value = JSON.parse(window.model.payload);
            value.goal.target = 10900000;
            value.goal.active = true;
            value.goal.baseline = 22000000;
            value.goal.remaining = 10900000;
            value.goal.final_balance = 32900000;
            value.goal.progress_percent = 0;
            window.model.payload = JSON.stringify(value);
            window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await target.isDisabled(), false);
        assert.strictEqual(await page.locator('#lc-draft-status').textContent(), 'Meta guardada.');
        checks.push('Save sends digits once and waits for backend acknowledgement');
        assert.strictEqual(await page.locator('#lc-save-goal').textContent(),'Actualizar meta');
        await page.evaluate(function(){
            const value=JSON.parse(window.model.payload);
            value.balance=22426000;
            Object.assign(value.goal,{current:426000,remaining:10474000,progress_percent:100*426000/10900000,
                since_utc:'2026-10-18T06:00:00Z',since_label:'18/10/2026 11:30 (hora local, UTC+05:30)'});
            window.model.payload=JSON.stringify(value);window.__handlers['viewEnv.onDataChanged']();
        });
        await target.fill('20000000');
        await page.locator('#lc-save-goal').click();
        assert.deepStrictEqual(await page.evaluate(()=>window.__calls[window.__calls.length-1]),['save',{value:'20000000',mode:'balance_growth'}]);
        assert.strictEqual(await target.isDisabled(),true);
        assert((await page.locator('#lc-progress-text').textContent()).includes('426.000'));
        await page.evaluate(function(){
            const value=JSON.parse(window.model.payload);
            Object.assign(value.goal,{target:20000000,final_balance:42000000,remaining:19574000,progress_percent:2.13});
            window.model.payload=JSON.stringify(value);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await target.isDisabled(),false);
        assert.strictEqual(await target.inputValue(),'20.000.000');
        assert.strictEqual(await page.locator('#lc-save-goal').textContent(),'Actualizar meta');
        assert((await page.locator('#lc-progress-text').textContent()).includes('426.000 / 20.000.000'));
        assert((await page.locator('#lc-base-note').textContent()).includes('22.000.000'));
        assert.strictEqual(await page.locator('#lc-goal-since').textContent(),'Meta iniciada: 18/10/2026 11:30 (hora local, UTC+05:30)');
        checks.push('Active goal updates keep accumulated credits, original base and start date; first goals use the start action and subsequent saves use update');
        await page.locator('#lc-history-toggle').click();
        await page.locator('.lc-history-option').nth(1).click();
        assert((await page.locator('#lc-history-label').textContent()).includes('17 oct, 14:57'));
        await page.locator('#lc-history-toggle').click();
        await page.keyboard.press('Escape');
        assert.strictEqual(await page.locator('#lc-history-toggle').getAttribute('aria-expanded'), 'false');
        await page.keyboard.press('Escape');
        assert.deepStrictEqual(await page.evaluate(() => window.__modeCalls[window.__modeCalls.length-1]),{mode:'widget'});
        assert.strictEqual(await page.locator('#lc-widget').isVisible(),true);
        assert.strictEqual(await page.evaluate(()=>window.__calls.filter(call=>call[0]==='close').length),0);
        await page.locator('#lc-widget-details').click();
        await page.waitForFunction(()=>document.getElementById('lc-details').className.indexOf('lc-hidden')<0);
        checks.push('History picker selection, Escape dismisses the picker first and then returns details to the widget without closing the view');
        assert((await page.locator('#lc-detail-rewards').textContent()).includes('Crisol'));
        await assertSignColor(page.locator('#lc-detail-rewards .lc-amount').first(),'positive');
        await assertSignColor(page.locator('#lc-rewards-list .lc-reward-amount').first(),'positive');
        checks.push('Battle mission annotation names the reward as already included');
        assert.strictEqual(await page.locator('#lc-detail-vehicles .lc-tank-name').textContent(),'XM57');
        assert.strictEqual(await page.locator('#lc-detail-vehicles .lc-tank-tier').textContent(),'Nivel VIII');
        await page.waitForFunction(()=>document.querySelector('#lc-detail-vehicles img').naturalWidth>0);
        assert.strictEqual(await page.locator('#lc-detail-vehicles img').getAttribute('data-native-src'),example.history[0].vehicles[0].icon);
        await page.locator('#lc-content').evaluate(n=>{n.scrollTop += document.querySelector('.lc-detail-header').getBoundingClientRect().top - n.getBoundingClientRect().top - 20;});
        await page.screenshot({path:path.join(__dirname,'tank-detail-preview.png')});
        await page.screenshot({path:path.join(__dirname,'colors-preview.png')});
        await page.locator('#lc-window').screenshot({path:path.join(__dirname,'details-redesign-battle.png')});
        checks.push('Included mission rewards and receipt amounts remain green while the selected battle loss and its deductions remain red');
        checks.push('Selected battle displays its own name, local tank art and Roman tier VIII above unchanged financial amounts');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            payload.history[0].vehicles.push({vehicle_type_id:'654',name:'Pz. Neu',tier:11,icon:'coui://gui/maps/icons/vehicle/missing.png'});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.deepStrictEqual(await page.locator('#lc-detail-vehicles .lc-tank-name').allTextContents(),['XM57','Pz. Neu']);
        assert.deepStrictEqual(await page.locator('#lc-detail-vehicles .lc-tank-tier').allTextContents(),['Nivel VIII','Nivel XI']);
        await page.waitForFunction(()=>document.querySelectorAll('#lc-detail-vehicles .lc-tank-placeholder')[1].className.indexOf('lc-hidden')<0);
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-113.508');
        await page.locator('#lc-history-toggle').click();
        await page.waitForTimeout(60);
        assert.strictEqual(await page.locator('#lc-history-menu').evaluate(n=>n.offsetHeight),122);
        assert.strictEqual(await page.locator('#lc-history-track').isVisible(),false);
        assert(await page.locator('#lc-history-menu').evaluate(n=>n.getBoundingClientRect().top>=document.getElementById('lc-history-toggle').getBoundingClientRect().bottom));
        checks.push('A short history expands below the selector without empty rows or an unnecessary scroll bar');
        assert((await page.locator('.lc-history-battle').first().textContent()).includes('Pz. Neu (Nivel XI)'));
        assert.strictEqual(await page.locator('.lc-history-battle img').count(),1);
        await page.locator('.lc-history-option').first().click();
        assert.strictEqual(await page.locator('#lc-detail-vehicles').isVisible(),false);
        checks.push('Multiple own vehicles and tier XI retain one financial aggregate; history identifies them and All battles has no invented tank');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);delete payload.history[0].vehicles;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        await page.locator('#lc-history-toggle').click();
        await page.locator('.lc-history-battle').first().click();
        assert.strictEqual(await page.locator('#lc-detail-vehicles .lc-tank-name').textContent(),'Vehículo sin identificar');
        assert.strictEqual(await page.locator('#lc-detail-vehicles img').count(),0);
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-113.508');
        checks.push('Legacy history without identity keeps real amounts and explicitly shows missing vehicle without guessed art');
        const modePayload=await page.evaluate(()=>JSON.parse(window.model.payload));
        const modeFixtures=[{bonus_type:1,gui_type:1,label:'Batalla aleatoria'},
            {bonus_type:20,gui_type:15,label:'Escaramuza'},{bonus_type:43,gui_type:30,label:'Asedio'}];
        const modeLabels=modeFixtures.map(mode=>mode.label);
        modePayload.history=modeFixtures.map((battle_mode,index)=>Object.assign({},example.history[0],{
            battle_id:'mode-'+index,time_label:'17 oct, 14:5'+index,battle_mode}));
        modePayload.history.push(Object.assign({},example.history[0],{battle_id:'mode-legacy',battle_mode:null}));
        modePayload.history.push(Object.assign({},example.history[0],{battle_id:'mode-text',battle_mode:{bonus_type:999,label:'<img src=x onerror=alert(1)> Evento'}}));
        await updateReservePayload(modePayload);
        await page.locator('#lc-history-toggle').click();
        assert.deepStrictEqual((await page.locator('.lc-history-stamp').allTextContents()).slice(0,3),modeLabels.map((label,index)=>'17 oct, 14:5'+index+' · '+label));
        assert((await page.locator('.lc-history-stamp').nth(3).textContent()).includes('Modo no identificado'));
        assert((await page.locator('.lc-history-stamp').nth(4).textContent()).includes('<img src=x onerror=alert(1)> Evento'));
        assert.strictEqual(await page.locator('.lc-history-stamp img').count(),0);
        for(let index=0;index<3;index++){
            await page.locator('.lc-history-battle').nth(index).click();
            assert.strictEqual(await page.locator('#lc-detail-mode').textContent(),'Modo de juego: '+modeLabels[index]);
            assert.strictEqual(await page.locator('#lc-detail-vehicles .lc-tank-name').textContent(),'XM57');
            assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-113.508');
            await page.locator('#lc-history-toggle').click();
        }
        await page.locator('.lc-history-battle').nth(3).click();
        assert.strictEqual(await page.locator('#lc-detail-mode').textContent(),'Modo de juego: Modo no identificado');
        await page.locator('#lc-history-toggle').click();
        await page.locator('.lc-history-battle').nth(4).click();
        assert.strictEqual(await page.locator('#lc-detail-mode img').count(),0);
        assert((await page.locator('#lc-detail-mode').textContent()).includes('<img src=x onerror=alert(1)> Evento'));
        checks.push('Same-vehicle random, skirmish and onslaught battles have distinct mode labels in history and details; unknown legacy modes stay unidentified and labels are rendered as text');
        await page.locator('#lc-history-toggle').click();
        await page.locator('.lc-history-battle').nth(1).click();
        const modeFinancialSnapshot=await page.evaluate(function(){const payload=JSON.parse(window.model.payload);return {summary:payload.summary,goal:payload.goal,wallet:payload.wallet,gross:payload.history[1].gross_credits,expenses:payload.history[1].expenses,net:payload.history[1].net_credits};});
        await page.locator('.lc-battle-panel').scrollIntoViewIfNeeded();
        await page.locator('.lc-battle-panel').screenshot({path:path.join(__dirname,'battle-mode-preview.png')});
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.history[1].battle_mode.label='Avance de fortaleza';
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert((await page.locator('#lc-history-label').textContent()).includes('14:51'));
        assert.strictEqual(await page.locator('#lc-detail-mode').textContent(),'Modo de juego: Avance de fortaleza');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-113.508');
        assert.deepStrictEqual(await page.evaluate(function(){const payload=JSON.parse(window.model.payload);return {summary:payload.summary,goal:payload.goal,wallet:payload.wallet,gross:payload.history[1].gross_credits,expenses:payload.history[1].expenses,net:payload.history[1].net_credits};}),modeFinancialSnapshot);
        await page.locator('#lc-history-toggle').click();
        await page.locator('.lc-history-option').first().click();
        assert.strictEqual(await page.locator('#lc-detail-mode').isVisible(),false);
        checks.push('Mode metadata updates preserve the selected battle and financial/goal/wallet values; All battles does not claim a single combined mode');
        const filterBasePayload=await page.evaluate(()=>JSON.parse(window.model.payload));
        const filterPayload=JSON.parse(JSON.stringify(filterBasePayload));
        filterPayload.account_context='NA:qa-mode-account';
        const randomRow=Object.assign({},example.history[0],{battle_id:'random-0',net_credits:3000,battle_mode:{bonus_type:1,gui_type:1,label:'Batalla aleatoria'}});
        const skirmishRow=Object.assign({},example.history[0],{battle_id:'skirmish-old-0',gross_credits:2000,
            expenses:{repair:2200,ammo:300,consumables:0,other:0},net_credits:-500,reserves:{personal:5,clan:10},
            battle_mode:{bonus_type:20,gui_type:15,label:'Escaramuza'}});
        filterPayload.history=Array.from({length:100},(_,index)=>Object.assign({},randomRow,{battle_id:'random-'+index}));
        filterPayload.summary={battle_count:256,gross_credits:710000,expenses:{repair:400000,ammo:50000,consumables:0,other:0},net_credits:260000,average_net_credits:null,pending_battles:2,
            reserves:{personal:30000,clan:20000,known_battles:255,total_battles:256}};
        const emptyModeSummary={battle_count:0,gross_credits:0,expenses:{repair:0,ammo:0,consumables:0,other:0},net_credits:0,average_net_credits:null,pending_battles:0,
            reserves:{personal:0,clan:0,known_battles:0,total_battles:0}};
        filterPayload.mode_groups=[
            {key:'mode:1',label:'Batalla aleatoria',history_total:150,history:filterPayload.history,
                summary:{battle_count:150,gross_credits:500000,expenses:{repair:180000,ammo:20000,consumables:0,other:0},net_credits:300000,pending_battles:0,reserves:{personal:15000,clan:10000,known_battles:150,total_battles:150}}},
            {key:'mode:20',label:'Escaramuza',history_total:105,history:Array.from({length:100},(_,index)=>Object.assign({},skirmishRow,{battle_id:'skirmish-old-'+index})),
                summary:{battle_count:105,gross_credits:200000,expenses:{repair:220000,ammo:30000,consumables:0,other:0},net_credits:-50000,pending_battles:0,reserves:{personal:15000,clan:10000,known_battles:105,total_battles:105}}},
            {key:'mode:43',label:'Asedio',history_total:0,history:[],summary:emptyModeSummary},
            {key:'unknown',label:'Modo no identificado',history_total:1,history:[Object.assign({},example.history[0],{battle_id:'unknown-old',battle_mode:null,net_credits:10000})],
                summary:{battle_count:1,gross_credits:10000,expenses:{repair:0,ammo:0,consumables:0,other:0},net_credits:10000,pending_battles:0,reserves:{personal:0,clan:0,known_battles:0,total_battles:1}}}
        ];
        for(let index=50;index<62;index++) filterPayload.mode_groups.push({key:'mode:'+index,label:'Modo '+index,history_total:0,history:[],summary:emptyModeSummary});
        async function chooseFilter(surface,key){await surface.locator('#lc-mode-toggle').click();await surface.locator('[data-mode-key="'+key+'"]').click();}
        await updateReservePayload(filterPayload);
        const beforeFilterCommands=await page.evaluate(()=>window.__calls.length);
        const globalWidgetBefore=await page.locator('#lc-widget-period').textContent();
        const globalWalletBefore=await page.locator('#lc-wallet-total').textContent();
        const goalBeforeFilter=await page.locator('#lc-goal-base').textContent();
        await chooseFilter(page,'mode:20');
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Escaramuza');
        assert.strictEqual(await page.locator('#lc-net-label').textContent(),'Ganancia o pérdida del modo');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'-50.000');
        assert((await page.locator('#lc-battle-count').textContent()).includes('105 partidas registradas · Escaramuza'));
        assert.strictEqual(await page.locator('#lc-gross').textContent(),'+200.000');
        assert.strictEqual(await page.locator('#lc-repair').textContent(),'-220.000');
        assert.strictEqual(await page.locator('#lc-ammo').textContent(),'-30.000');
        assert.strictEqual(await page.locator('#lc-reserve-personal').textContent(),'+15.000');
        assert.strictEqual(await page.locator('#lc-reserve-clan').textContent(),'+10.000');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-50.000');
        await assertSignColor(page.locator('#lc-net-total'),'negative');
        assert.strictEqual(await page.locator('.lc-history-battle').count(),100);
        assert.strictEqual(await page.locator('#lc-widget-period').textContent(),globalWidgetBefore);
        assert.strictEqual(await page.locator('#lc-wallet-total').textContent(),globalWalletBefore);
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),goalBeforeFilter);
        assert((await page.locator('#lc-message').textContent()).includes('2 resultados pendientes'));
        await page.locator('#lc-history-toggle').click();
        await page.locator('.lc-history-battle').first().click();
        assert.strictEqual(await page.locator('#lc-detail-mode').textContent(),'Modo de juego: Escaramuza');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-500');
        await page.locator('#lc-mode-toggle').click();await page.keyboard.press('Escape');
        assert.strictEqual(await page.locator('#lc-mode-toggle').getAttribute('aria-expanded'),'false');
        assert.strictEqual(await page.locator('#lc-details').isVisible(),true);
        await updateReservePayload(filterPayload);
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Escaramuza');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-500');
        assert((await page.locator('#lc-history-label').textContent()).includes('XM57'));
        await page.locator('#lc-back-widget').click();await page.locator('#lc-widget-details').click();
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Escaramuza');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-500');
        checks.push('Mode filter uses complete backend mode totals and its own 100-row history even when every global recent row belongs to another mode; preserves selection over updates/view switches while widget, wallet, goal and pending notice stay global');
        await chooseFilter(page,'mode:1');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+300.000');
        await assertSignColor(page.locator('#lc-net-total'),'positive');
        assert.strictEqual(await page.locator('#lc-detail-mode').isVisible(),false);
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'+300.000');
        await chooseFilter(page,'mode:43');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+0');
        await assertSignColor(page.locator('#lc-net-total'),'zero');
        assert.strictEqual(await page.locator('.lc-history-battle').count(),0);
        assert.strictEqual(await page.locator('#lc-history-empty').isVisible(),true);
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'+0');
        await chooseFilter(page,'unknown');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+10.000');
        assert.strictEqual(await page.locator('#lc-reserve-personal').textContent(),'—');
        await page.locator('#lc-history-toggle').click();await page.locator('.lc-history-battle').first().click();
        assert.strictEqual(await page.locator('#lc-detail-mode').textContent(),'Modo de juego: Modo no identificado');
        await chooseFilter(page,'all');
        assert.strictEqual(await page.locator('#lc-net-label').textContent(),'Ganancia o pérdida total');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+260.000');
        assert.strictEqual(await page.locator('#lc-detail-mode').isVisible(),false);
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),beforeFilterCommands);
        checks.push('Random, skirmish, empty Asedio, unknown and All filters show their own counts, signed totals, reserve coverage and aggregate breakdown; changing filter clears individual selection and sends no native mutation');
        await page.locator('#lc-mode-toggle').click();await page.waitForTimeout(60);
        assert.strictEqual(await page.locator('#lc-mode-track').isVisible(),true);
        await page.locator('#lc-mode-options').hover();
        await page.mouse.wheel(0,240);
        assert((await page.locator('#lc-mode-options').evaluate(node=>node.scrollTop))>0);
        await page.locator('[data-mode-key="mode:61"]').click();
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Modo 61');
        await chooseFilter(page,'mode:20');
        await page.locator('#lc-content').evaluate(node=>{node.scrollTop=document.querySelector('.lc-battle-panel').offsetTop-40;});
        await page.locator('#lc-window').screenshot({path:path.join(__dirname,'mode-filter-preview.png')});
        const removedGroup=JSON.parse(JSON.stringify(filterPayload));removedGroup.mode_groups=removedGroup.mode_groups.filter(group=>group.key!=='mode:20');
        await updateReservePayload(removedGroup);
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Todos los modos');
        assert.strictEqual(await page.locator('#lc-detail-mode').isVisible(),false);
        await updateReservePayload(filterPayload);await chooseFilter(page,'mode:20');
        const otherAccount=JSON.parse(JSON.stringify(filterPayload));otherAccount.account_context='NA:qa-other-account';otherAccount.ready=false;
        await updateReservePayload(otherAccount);
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Todos los modos');
        await updateReservePayload(filterPayload);await chooseFilter(page,'mode:20');
        const newHistoryPeriod=JSON.parse(JSON.stringify(filterPayload));newHistoryPeriod.history_control.generation+=1;
        await updateReservePayload(newHistoryPeriod);
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Todos los modos');
        assert.strictEqual(await page.locator('#lc-detail-mode').isVisible(),false);
        await updateReservePayload(filterBasePayload);
        checks.push('Mode picker scrolls through additional modes and safely returns to All when a group disappears, account context changes while loading or history generation resets');
        const vehiclePayload=JSON.parse(JSON.stringify(filterPayload));
        const xmVehicle=example.history[0].vehicles[0];
        const pzVehicle={vehicle_type_id:'654',name:'Pz. Neu',tier:11,icon:'coui://gui/maps/icons/vehicle/germany-G01_PzIII_A.png'};
        const xmSummary={battle_count:110,gross_credits:600000,expenses:{repair:100000,ammo:30000,consumables:20000,other:0},net_credits:450000,average_net_credits:4091,pending_battles:0,reserves:{personal:20000,clan:15000,known_battles:110,total_battles:110}};
        const pzSummary={battle_count:2,gross_credits:300000,expenses:{repair:100000,ammo:0,consumables:0,other:0},net_credits:200000,average_net_credits:100000,pending_battles:0,reserves:{personal:0,clan:0,known_battles:2,total_battles:2}};
        const xmGroup={key:'vehicle:321',label:'XM57',vehicle:xmVehicle,rankable:true,summary:xmSummary,history_total:110};
        const pzGroup={key:'vehicle:654',label:'Pz. Neu',vehicle:pzVehicle,rankable:true,summary:pzSummary,history_total:2};
        vehiclePayload.vehicle_groups=[pzGroup,xmGroup,
            {key:'unknown',label:'Vehículo sin identificar',vehicle:null,rankable:false,summary:Object.assign({},pzSummary,{battle_count:5,net_credits:900000}),history_total:5},
            {key:'multiple',label:'Varios vehículos en una partida',vehicle:null,rankable:false,summary:Object.assign({},pzSummary,{battle_count:1,net_credits:800000}),history_total:1}];
        for(let index=0;index<6;index++) vehiclePayload.vehicle_groups.push({key:'vehicle:'+(700+index),label:'Tanque '+index,
            vehicle:Object.assign({},xmVehicle,{vehicle_type_id:String(700+index),name:'Tanque '+index}),rankable:true,
            summary:Object.assign({},emptyModeSummary,{battle_count:1,net_credits:-1000*(index+1),average_net_credits:-1000*(index+1)}),history_total:1});
        vehiclePayload.vehicle_groups.push({key:'vehicle:9999',label:'Pendiente',vehicle:Object.assign({},xmVehicle,{vehicle_type_id:'9999',name:'Pendiente'}),rankable:false,summary:emptyModeSummary,history_total:0});
        const modeXmGroup=Object.assign({},xmGroup,{summary:Object.assign({},xmSummary,{battle_count:10,net_credits:-25000,average_net_credits:-2500}),history_total:10});
        vehiclePayload.mode_groups.forEach(group=>{group.vehicle_groups=group.key==='mode:20'?[modeXmGroup]:group.key==='mode:1'?[xmGroup,pzGroup]:[];});
        vehiclePayload.vehicle_selection=null;
        async function chooseVehicle(surface,key){await surface.locator('#lc-vehicle-toggle').click();await surface.locator('[data-vehicle-key="'+key+'"]').click();}
        async function lastVehicleRequest(){return page.evaluate(()=>window.__calls.filter(call=>call[0]==='vehicle-filter').slice(-1)[0][1]);}
        async function vehicleResponse(surface,request,group,rows,patch){
            await surface.evaluate(function(args){
                const payload=JSON.parse(window.model.payload);payload.error=null;
                payload.vehicle_selection=Object.assign({mode_key:args.request.mode_key,vehicle_key:args.request.vehicle_key,request_id:args.request.request_id,
                    available:true,summary:args.group.summary,history:args.rows,history_total:args.group.history_total},args.patch||{});
                window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
            },{request,group,rows,patch});
        }
        await updateReservePayload(vehiclePayload);
        assert.strictEqual(await page.locator('[id^=lc-ranking],.lc-vehicle-comparison').count(),0);
        checks.push('Vehicle comparison and both total/average sorting controls are removed from production DOM while mode/tank filters remain available');
        const globalVehicleWidget=await page.locator('#lc-widget-period').textContent();
        const globalVehicleWallet=await page.locator('#lc-wallet-total').textContent();
        await chooseVehicle(page,'vehicle:321');
        const requestXm=await lastVehicleRequest();
        assert.deepStrictEqual(requestXm,{mode_key:'all',vehicle_key:'vehicle:321',request_id:requestXm.request_id,account_context:vehiclePayload.account_context});
        assert(Number.isInteger(requestXm.request_id)&&requestXm.request_id>0);
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+450.000');
        assert.strictEqual(await page.locator('.lc-history-battle').count(),0);
        assert.strictEqual(await page.locator('#lc-history-toggle').isDisabled(),true);
        assert((await page.locator('#lc-vehicle-status').textContent()).includes('Cargando'));
        assert.strictEqual(await page.locator('#lc-gross').textContent(),'+600.000');
        assert.strictEqual(await page.locator('#lc-repair').textContent(),'-100.000');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'+450.000');
        await chooseVehicle(page,'vehicle:654');
        const requestPz=await lastVehicleRequest();assert(requestPz.request_id>requestXm.request_id);
        await vehicleResponse(page,requestXm,xmGroup,[Object.assign({},example.history[0],{battle_id:'old-xm'})]);
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+200.000');
        assert((await page.locator('#lc-vehicle-label').textContent()).includes('Pz. Neu'));
        await vehicleResponse(page,requestPz,pzGroup,[Object.assign({},example.history[0],{battle_id:'pz-0',vehicles:[pzVehicle],net_credits:200000})]);
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+200.000');
        assert.strictEqual(await page.locator('#lc-net-label').textContent(),'Ganancia o pérdida del vehículo');
        assert((await page.locator('#lc-battle-count').textContent()).includes('2 partidas registradas'));
        assert.strictEqual(await page.locator('#lc-gross').textContent(),'+300.000');
        assert.strictEqual(await page.locator('#lc-widget-period').textContent(),globalVehicleWidget);
        assert.strictEqual(await page.locator('#lc-wallet-total').textContent(),globalVehicleWallet);
        await chooseVehicle(page,'all');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+260.000');
        await vehicleResponse(page,requestPz,pzGroup,[]);
        assert.strictEqual(await page.locator('#lc-vehicle-label').textContent(),'Todos los vehículos');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+260.000');
        checks.push('Vehicle selection keeps full known gross/expenses/net visible while only history waits; account-bound IDs ignore old tank responses and returning to All changes neither widget nor wallet');
        await chooseVehicle(page,'vehicle:321');const requestXmAll=await lastVehicleRequest();
        const xmRows=Array.from({length:100},(_,index)=>Object.assign({},example.history[0],{battle_id:'xm-filter-'+index}));
        await vehicleResponse(page,requestXmAll,xmGroup,xmRows);
        assert((await page.locator('#lc-battle-count').textContent()).includes('110 partidas registradas'));
        assert.strictEqual(await page.locator('.lc-history-battle').count(),100);
        await chooseFilter(page,'mode:20');const requestXmMode=await lastVehicleRequest();
        assert.strictEqual(requestXmMode.mode_key,'mode:20');assert.strictEqual(requestXmMode.vehicle_key,'vehicle:321');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'-25.000');
        await vehicleResponse(page,requestXmAll,xmGroup,xmRows);assert.strictEqual(await page.locator('#lc-net-total').textContent(),'-25.000');
        await vehicleResponse(page,requestXmMode,modeXmGroup,[Object.assign({},skirmishRow,{battle_id:'xm-skirmish'})]);
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'-25.000');
        assert((await page.locator('#lc-battle-count').textContent()).includes('Escaramuza'));
        assert((await page.locator('#lc-battle-count').textContent()).includes('XM57'));
        await chooseFilter(page,'mode:43');
        assert.strictEqual(await page.locator('#lc-vehicle-label').textContent(),'Todos los vehículos');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+0');
        await chooseFilter(page,'all');await chooseVehicle(page,'unknown');const requestUnknown=await lastVehicleRequest();
        const unknownGroup=vehiclePayload.vehicle_groups.find(group=>group.key==='unknown');
        await vehicleResponse(page,requestUnknown,unknownGroup,[Object.assign({},example.history[0],{battle_id:'unknown-vehicle',vehicles:[]})]);
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+900.000');
        await chooseVehicle(page,'multiple');const requestMultiple=await lastVehicleRequest();
        const multipleGroup=vehiclePayload.vehicle_groups.find(group=>group.key==='multiple');
        await vehicleResponse(page,requestMultiple,multipleGroup,[Object.assign({},example.history[0],{battle_id:'multiple-vehicle',vehicles:[xmVehicle,pzVehicle]})]);
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+800.000');
        await page.locator('#lc-history-toggle').click();await page.locator('.lc-history-battle').first().click();
        assert.deepStrictEqual(await page.locator('#lc-detail-vehicles .lc-tank-name').allTextContents(),['XM57','Pz. Neu']);
        checks.push('Combined mode and tank filters retain only a tank available in the new scope, request fresh mode-specific history, use complete totals beyond100 rows and keep unknown/multiple aggregates separate from individual tanks');
        await chooseVehicle(page,'vehicle:321');const failedVehicleRequest=await lastVehicleRequest();
        await page.evaluate(function(){const payload=JSON.parse(window.model.payload);payload.error='No se pudo filtrar.';window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        assert.strictEqual(await page.locator('#lc-vehicle-retry').isVisible(),true);
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+450.000');
        await page.locator('#lc-vehicle-retry').click();const retryVehicleRequest=await lastVehicleRequest();
        assert(retryVehicleRequest.request_id>failedVehicleRequest.request_id);
        await vehicleResponse(page,retryVehicleRequest,xmGroup,xmRows);
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+450.000');
        await page.locator('#lc-window').screenshot({path:path.join(__dirname,'vehicle-filter-preview.png')});
        await chooseVehicle(page,'vehicle:654');const unavailableRequest=await lastVehicleRequest();
        await vehicleResponse(page,unavailableRequest,pzGroup,[],{available:false});
        assert.strictEqual(await page.locator('#lc-vehicle-label').textContent(),'Todos los vehículos');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+260.000');
        await chooseVehicle(page,'vehicle:321');
        const vehicleOtherAccount=JSON.parse(JSON.stringify(vehiclePayload));vehicleOtherAccount.account_context='NA:different-vehicle-account';vehicleOtherAccount.ready=false;
        await updateReservePayload(vehicleOtherAccount);
        assert.strictEqual(await page.locator('#lc-vehicle-label').textContent(),'Todos los vehículos');
        await updateReservePayload(vehiclePayload);await chooseVehicle(page,'vehicle:321');
        const vehicleResetPeriod=JSON.parse(JSON.stringify(vehiclePayload));vehicleResetPeriod.history_control.generation+=1;
        await updateReservePayload(vehicleResetPeriod);
        assert.strictEqual(await page.locator('#lc-vehicle-label').textContent(),'Todos los vehículos');
        await updateReservePayload(filterBasePayload);
        checks.push('Vehicle filter errors unlock retry with a new request ID; unavailable selection, account changes and history resets safely restore All without showing another tank under the selected label');
        const modeIcons={
            random:'coui://gui/maps/icons/battleTypes/64x64/random.png',
            skirmish:'coui://gui/maps/icons/battleTypes/64x64/strongholdsBattlesList.png',
            onslaught:'coui://gui/maps/icons/battleTypes/64x64/comp7.png',
            light:'coui://comp7_light/gui/maps/icons/battleTypes/64x64/comp7_light.png',
            tower:'coui://halloween/gui/maps/icons/battleTypes/64x64/halloween.extend.png',
            global:'coui://gui/maps/icons/battleTypes/136x136/clan.png'
        };
        const artPayload=JSON.parse(JSON.stringify(filterBasePayload));
        artPayload.account_context='NA:qa-native-art';
        const artSummary=JSON.parse(JSON.stringify(example.summary));
        artPayload.mode_groups=[
            {key:'mode:1',label:'Batalla aleatoria',icon:modeIcons.random},
            {key:'mode:20',label:'Escaramuza',icon:modeIcons.skirmish},
            {key:'mode:43',label:'Asedio',icon:modeIcons.onslaught},
            {key:'mode:102',label:'Torre oscura · Difícil',icon:modeIcons.tower},
            {key:'mode:49',label:'Asedio ligero',icon:modeIcons.light},
            {key:'mode:13',label:'Mapa global',icon:modeIcons.global},
            {key:'unknown',label:'Modo no identificado',icon:null}
        ].map(group=>Object.assign(group,{summary:artSummary,history:[],history_total:0,vehicle_groups:[]}));
        const eventArtTypes=['france-F17_AMX_13_90_Halloween_event','uk-GB24_Centurion_Mk3_Halloween_event',
            'ussr-R171_IS_3_II_hw21','usa-A100_T49_Halloween_event',
            'ussr-R40_T-54_Halloween_event','italy-It19_Progetto_C50_mod_66_hw21',
            'uk-GB123_GSOR_1006_v7_Halloween_event'];
        const eventArtNames=['Avispa','Cerbero','Doble','Granadero','Malaquita','Legio Ferrata','Devastador'];
        artPayload.history=eventArtNames.map((name,index)=>Object.assign({},example.history[0],{
            battle_id:'event-art-'+index,time_label:'19/10 06:'+String(10+index),
            vehicles:[{vehicle_type_id:String(8000+index),name,tier:9,
                icon:'coui://halloween/gui/maps/icons/vehicle/'+eventArtTypes[index]+'.extend.png'}],
            battle_mode:{bonus_type:102,label:'Torre oscura · Difícil',icon:modeIcons.tower}
        }));
        artPayload.vehicle_groups=artPayload.history.map(row=>({key:'vehicle:'+row.vehicles[0].vehicle_type_id,label:row.vehicles[0].name,
            vehicle:row.vehicles[0],rankable:true,summary:artSummary,history_total:1}));
        artPayload.mode_groups.forEach(group=>{
            if(group.key==='mode:102'){group.history=artPayload.history;group.history_total=7;group.vehicle_groups=artPayload.vehicle_groups;}
        });
        await updateReservePayload(artPayload);
        const artFinancialBefore=await page.evaluate(()=>({net:document.getElementById('lc-net-total').textContent,
            balance:document.getElementById('lc-balance').textContent,goal:document.getElementById('lc-progress-text').textContent,
            calls:window.__calls.length}));
        await page.locator('#lc-mode-toggle').click();
        await page.waitForFunction(()=>Array.from(document.querySelectorAll('#lc-mode-list img')).every(img=>img.complete));
        assert.strictEqual(await page.locator('[data-mode-key="mode:1"] img').getAttribute('data-native-src'),modeIcons.random);
        assert.strictEqual(await page.locator('[data-mode-key="mode:20"] img').getAttribute('data-native-src'),modeIcons.skirmish);
        assert.strictEqual(await page.locator('[data-mode-key="mode:43"] img').getAttribute('data-native-src'),modeIcons.onslaught);
        assert.strictEqual(await page.locator('[data-mode-key="mode:102"] img').getAttribute('data-native-src'),modeIcons.tower);
        assert.strictEqual(await page.locator('[data-mode-key="mode:49"] img').getAttribute('data-native-src'),modeIcons.light);
        assert.strictEqual(await page.locator('[data-mode-key="mode:13"] img').getAttribute('data-native-src'),modeIcons.global);
        assert.strictEqual(await page.locator('[data-mode-key="all"] img').count(),0);
        assert.strictEqual(await page.locator('[data-mode-key="unknown"] img').count(),0);
        assert(await page.locator('#lc-mode-list .lc-mode-option').evaluateAll(rows=>rows.every(row=>{
            const box=row.getBoundingClientRect(),art=row.querySelector('.lc-mode-art').getBoundingClientRect(),label=row.querySelector('.lc-filter-option-label').getBoundingClientRect();
            return box.height===56&&art.width===40&&art.height===40&&art.right<=label.left&&label.right<=box.right;
        })));
        await page.locator('#lc-window').screenshot({path:path.join(__dirname,'mode-icons-preview.png')});
        await page.locator('[data-mode-key="mode:102"]').click();
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Torre oscura · Difícil');
        assert.strictEqual(await page.locator('#lc-mode-icon img').getAttribute('data-native-src'),modeIcons.tower);
        await page.locator('#lc-history-toggle').click();
        assert.strictEqual(await page.locator('.lc-history-stamp img').first().getAttribute('data-native-src'),modeIcons.tower);
        await page.locator('.lc-history-battle').first().click();
        assert.strictEqual(await page.locator('#lc-detail-mode img').getAttribute('data-native-src'),modeIcons.tower);
        assert.strictEqual(await page.locator('#lc-detail-mode').textContent(),'Modo de juego: Torre oscura · Difícil');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'-113.508');
        await updateReservePayload(artPayload);
        await page.locator('#lc-back-widget').click();await page.locator('#lc-widget-details').click();
        assert.strictEqual(await page.locator('#lc-mode-icon img').getAttribute('data-native-src'),modeIcons.tower);
        assert.deepStrictEqual(await page.evaluate(()=>({net:document.getElementById('lc-net-total').textContent,
            balance:document.getElementById('lc-balance').textContent,goal:document.getElementById('lc-progress-text').textContent,
            calls:window.__calls.length})),artFinancialBefore);
        checks.push('Official local mode image identities follow each group and selected battle, including mounted current Tower and light Onslaught assets plus136px global map; All/unknown have no unrelated emblem and image rendering preserves accounting and selection');
        await page.locator('#lc-vehicle-toggle').click();
        assert.strictEqual(await page.locator('#lc-vehicle-list img').count(),7);
        for(let index=0;index<4;index++){
            const option=page.locator('[data-vehicle-key="vehicle:'+(8000+index)+'"]');
            assert.strictEqual(await option.locator('img').getAttribute('data-native-src'),artPayload.history[index].vehicles[0].icon);
            assert((await option.textContent()).includes('Nivel IX'));
        }
        assert(await page.locator('#lc-vehicle-list .lc-vehicle-option').evaluateAll(rows=>rows.every(row=>row.getBoundingClientRect().height===56)));
        await page.locator('#lc-window').screenshot({path:path.join(__dirname,'event-vehicles-preview.png')});
        await page.locator('[data-vehicle-key="vehicle:8000"]').click();
        const artRequest=await lastVehicleRequest();
        assert.strictEqual(await page.locator('#lc-vehicle-icon img').getAttribute('data-native-src'),artPayload.history[0].vehicles[0].icon);
        assert.strictEqual(await page.locator('#lc-vehicle-label').textContent(),'Avispa (Nivel IX)');
        await vehicleResponse(page,artRequest,artPayload.vehicle_groups[0],[artPayload.history[0]]);
        await page.locator('#lc-history-toggle').click();await page.locator('.lc-history-battle').first().click();
        assert.strictEqual(await page.locator('#lc-detail-vehicles img').getAttribute('data-native-src'),artPayload.history[0].vehicles[0].icon);
        assert.strictEqual(await page.locator('#lc-detail-vehicles .lc-tank-tier').textContent(),'Nivel IX');
        checks.push('Seven current mounted event tank images and their actual native level IX appear in vehicle filter options, selected closed control, history and individual detail without assigning a selected garage vehicle or changing native filtered amounts');
        await chooseVehicle(page,'all');await chooseFilter(page,'all');
        for(const bad of ['https://example.invalid/logo.png','javascript:alert(1)','coui://halloween/gui/maps/icons/battleTypes/64x64/../../vehicle/fake.png',
            'coui://untrusted/gui/maps/icons/battleTypes/64x64/random.png','coui://gui/maps/icons/other/random.png']){
            const badPayload=JSON.parse(JSON.stringify(artPayload));badPayload.mode_groups[0].icon=bad;
            await updateReservePayload(badPayload);await page.locator('#lc-mode-toggle').click();
            assert.strictEqual(await page.locator('[data-mode-key="mode:1"] img').count(),0);
            await page.keyboard.press('Escape');
        }
        const missingArt=JSON.parse(JSON.stringify(artPayload));
        missingArt.mode_groups[0].icon='coui://gui/maps/icons/battleTypes/64x64/missing.png';
        missingArt.vehicle_groups[0].vehicle.icon='coui://halloween/gui/maps/icons/vehicle/missing.extend.png';
        await updateReservePayload(missingArt);await chooseFilter(page,'mode:1');
        await page.waitForFunction(()=>document.querySelector('#lc-mode-icon img').className.indexOf('lc-hidden')>=0);
        assert.strictEqual(await page.locator('#lc-mode-label').textContent(),'Batalla aleatoria');
        assert.strictEqual(await page.locator('#lc-mode-icon').evaluate(node=>node.getBoundingClientRect().width),40);
        await chooseFilter(page,'all');await page.locator('#lc-vehicle-toggle').click();
        await page.waitForFunction(()=>document.querySelector('[data-vehicle-key="vehicle:8000"] img').className.indexOf('lc-hidden')>=0);
        assert.strictEqual(await page.locator('[data-vehicle-key="vehicle:8000"] .lc-tank-placeholder').isVisible(),true);
        assert((await page.locator('[data-vehicle-key="vehicle:8000"]').textContent()).includes('Avispa (Nivel IX)'));
        await page.keyboard.press('Escape');
        for(const bad of ['https://example.invalid/tank.png','javascript:alert(1)',
            'coui://halloween/gui/maps/icons/vehicle/../other.png','coui://untrusted/gui/maps/icons/vehicle/tank.png']){
            const badPayload=JSON.parse(JSON.stringify(artPayload));badPayload.vehicle_groups[0].vehicle.icon=bad;
            await updateReservePayload(badPayload);await page.locator('#lc-vehicle-toggle').click();
            assert.strictEqual(await page.locator('[data-vehicle-key="vehicle:8000"] img').count(),0);
            assert((await page.locator('[data-vehicle-key="vehicle:8000"]').textContent()).includes('Avispa (Nivel IX)'));
            await page.keyboard.press('Escape');
        }
        checks.push('Image allowlists reject remote URLs, script URLs, traversal and unverified mounts; missing mode art leaves stable blank spacing and readable names while missing vehicle art keeps its explicit placeholder and tier');
        await updateReservePayload(filterBasePayload);
        await page.evaluate(function () {
            const value = JSON.parse(window.model.payload);
            const first = value.history[0];
            value.history = Array.from({length:100}, (_, i) => Object.assign({}, first, {battle_id:String(9000+i),time_label:'Partida '+i,
                vehicles:[{vehicle_type_id:'321',name:'XM57',tier:8,icon:'coui://gui/maps/icons/vehicle/usa-A01_T1_Cunningham.png'}],
                battle_mode:{bonus_type:999,label:'Evento de prueba con nombre de modo muy largo para comprobar el límite de la segunda línea'}}));
            value.rewards = Array.from({length:30}, (_, i) => ({time_label:'18/10 01:15',included_in_battle:false,credits:10000,parts:[{title:'Misión de campaña '+i,credits:10000}]}));
            window.model.payload = JSON.stringify(value);
            window.__handlers['viewEnv.onDataChanged']();
        });
        await page.locator('#lc-history-toggle').click();
        await page.waitForTimeout(60);
        assert.strictEqual(await page.locator('#lc-history-track').isVisible(), true);
        const fiveRows = await page.evaluate(function(){
            const viewport=document.getElementById('lc-history-options').getBoundingClientRect();
            const rows=Array.from(document.querySelectorAll('.lc-history-battle')).map(n=>n.getBoundingClientRect());
            const menu=document.getElementById('lc-history-menu').getBoundingClientRect();
            const content=document.getElementById('lc-content').getBoundingClientRect();
            return {visible:rows.filter(r=>r.top>=viewport.top && r.bottom<=viewport.bottom).length,
                sixthBelow:rows[5].top>=viewport.bottom-5,
                below:menu.top>=document.getElementById('lc-history-toggle').getBoundingClientRect().bottom,
                contained:menu.top>=content.top && menu.bottom<=content.bottom,
                costsBelow:document.querySelector('.lc-costs').getBoundingClientRect().top>=menu.bottom};
        });
        assert.deepStrictEqual(fiveRows,{visible:5,sixthBelow:true,below:true,contained:true,costsBelow:true});
        assert(await page.locator('.lc-history-battle').evaluateAll(rows=>rows.every(row=>{
            const outer=row.getBoundingClientRect(),stamp=row.querySelector('.lc-history-stamp').getBoundingClientRect();
            const name=row.querySelector('.lc-history-tank').getBoundingClientRect(),net=row.querySelector('.lc-history-net').getBoundingClientRect();
            return outer.height===72&&stamp.height===24&&name.bottom<=stamp.top&&stamp.bottom<=outer.bottom&&stamp.right<=net.left+1;
        })));
        await page.screenshot({path:path.join(__dirname,'five-battles-preview.png')});
        checks.push('Expanded history shows five complete battles below the selector, reveals them within the panel and pushes the breakdown down without covering the goal');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);window.__qaFullHistory=payload.history;
            payload.history=payload.history.slice(0,5);
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        await page.waitForTimeout(60);
        assert.strictEqual(await page.locator('#lc-history-track').isVisible(),false);
        assert.strictEqual(await page.locator('#lc-history-options').evaluate(n=>n.scrollHeight-n.clientHeight),0);
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.history=window.__qaFullHistory;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        await page.waitForTimeout(60);
        assert.strictEqual(await page.locator('#lc-history-track').isVisible(),true);
        checks.push('Exactly five battles fit without scrolling; additional battles activate the bar while the picker remains open');
        const parentScroll = await page.locator('#lc-content').evaluate(n=>n.scrollTop);
        await page.locator('#lc-history-options').hover();
        await page.mouse.wheel(0, 600);
        await page.waitForTimeout(60);
        assert((await page.locator('#lc-history-options').evaluate(n=>n.scrollTop)) > 0);
        assert.strictEqual(await page.locator('#lc-content').evaluate(n=>n.scrollTop), parentScroll);
        let thumb = await page.locator('#lc-history-thumb').boundingBox();
        let track = await page.locator('#lc-history-track').boundingBox();
        await page.mouse.move(thumb.x+4,thumb.y+4);
        await page.mouse.down();
        await page.mouse.move(track.x+4,track.y+track.height-3,{steps:5});
        await page.mouse.up();
        const extent = await page.locator('#lc-history-options').evaluate(n=>({top:n.scrollTop,max:n.scrollHeight-n.clientHeight}));
        assert(extent.top >= extent.max-5);
        await page.locator('.lc-history-option').last().click();
        assert((await page.locator('#lc-history-label').textContent()).includes('Partida 99'));
        checks.push('100-row history: mouse wheel, drag bar, last row selectable, parent scroll isolated');
        await page.locator('#lc-rewards-list').scrollIntoViewIfNeeded();
        await page.locator('#lc-rewards-viewport').hover();
        await page.mouse.wheel(0,600);
        await page.waitForTimeout(60);
        assert((await page.locator('#lc-rewards-viewport').evaluate(n=>n.scrollTop)) > 0);
        assert.strictEqual(await page.locator('#lc-rewards-track').isVisible(), true);
        checks.push('Reward receipts have their own wheel and visible scroll bar');
        await page.locator('#lc-content').evaluate(n=>n.scrollTop=0);
        const field = await target.boundingBox();
        const save = await page.locator('#lc-save-goal').boundingBox();
        assert(field.y+field.height<=save.y || save.y+save.height<=field.y ||
            field.x+field.width<=save.x || save.x+save.width<=field.x,
            'Goal input and save action must have separate selectable rectangles');
        checks.push('Goal input and save button have separate selectable areas');
        await page.locator('#lc-content').evaluate(n=>n.scrollTop=0);
        const beforeMove = await page.locator('#lc-window').boundingBox();
        let header = await page.locator('#lc-drag-bar').boundingBox();
        await page.mouse.move(header.x+80,header.y+30);
        await page.mouse.down();
        await page.mouse.move(header.x+180,header.y+65,{steps:4});
        await page.mouse.up();
        const moved = await page.locator('#lc-window').boundingBox();
        assert(moved.x > beforeMove.x && moved.y > beforeMove.y);
        await page.evaluate(function(){
            const background = document.createElement('button');
            background.id='qa-garage-button';
            background.style.cssText='position:fixed;left:4px;top:4px;width:90px;height:28px;z-index:0;pointer-events:auto';
            background.textContent='Garaje';
            background.onclick=function(){window.__garageClicked=true;};
            document.body.insertBefore(background,document.body.firstChild);
        });
        await page.locator('#qa-garage-button').click();
        assert.strictEqual(await page.evaluate(()=>window.__garageClicked),true);
        checks.push('Preview header drag stays on screen and empty overlay space passes clicks to background');
        // Verify the real Wulf bridge calls separately from preview DOM movement.
        await page.evaluate(function(){
            window.__nativeOps=[];
            window.__nativeSize={width:256,height:256};
            window.viewEnv.getClientSizePx=function(){return {width:1100,height:850};};
            window.viewEnv.getViewSizePx=function(){return window.__nativeSize;};
            window.viewEnv.resizeViewPx=function(w,h){
                window.__nativeOps.push(['size',w,h]);
                const changed=window.__nativeSize.width!==w||window.__nativeSize.height!==h;
                window.__nativeSize={width:w,height:h};
                if(changed){
                    const payload=JSON.parse(window.model.payload);
                    payload.window={ready:true,width:w,height:h};
                    window.model.payload=JSON.stringify(payload);
                    window.setTimeout(function(){window.__handlers['viewEnv.onDataChanged']();},0);
                }
            };
            window.viewEnv.handleViewEvent=function(data){window.__nativeOps.push(['move',data]);};
            window.viewEnv.setTrackMouseOnStage=function(on){window.__nativeOps.push(['track',on]);};
            window.viewEnv.setEventHandled=function(){window.__nativeOps.push(['handled']);};
            window.model.onLayoutReady=function(args){window.__nativeOps.push(['layout',args]);};
            const payload=JSON.parse(window.model.payload);
            payload.window={ready:true,width:256,height:256};
            window.model.payload=JSON.stringify(payload);
            window.__handlers['viewEnv.onDataChanged']();
            window.dispatchEvent(new Event('resize'));
        });
        await page.waitForFunction(()=>window.__nativeOps.some(x=>x[0]==='layout'&&x[1].phase==='verified'));
        const nativeOps = await page.evaluate(()=>window.__nativeOps);
        assert.deepStrictEqual(nativeOps.find(x=>x[0]==='size'),['size',1040,802]);
        const verifiedLayout=nativeOps.filter(x=>x[0]==='layout'&&x[1].phase==='verified').pop()[1];
        assert.deepStrictEqual([verifiedLayout.clientWidth,verifiedLayout.clientHeight,verifiedLayout.width,verifiedLayout.height], [1100,850,1040,802]);
        assert.deepStrictEqual([verifiedLayout.nativeWidth,verifiedLayout.nativeHeight], [1040,802]);
        header = await page.locator('#lc-drag-bar').boundingBox();
        await page.mouse.move(header.x+80,header.y+30);
        await page.mouse.down();
        await page.mouse.move(header.x+120,header.y+40,{steps:3});
        await page.mouse.up();
        const moves = await page.evaluate(()=>window.__nativeOps.filter(x=>x[0]==='move'));
        assert.deepStrictEqual(moves.map(x=>x[1]),[
            {__Type:'GFViewEventProxy',type:16,isMouseEvent:true,on:true},
            {__Type:'GFViewEventProxy',type:16,isMouseEvent:true,on:false}]);
        assert.strictEqual(await page.evaluate(()=>window.__nativeOps.filter(x=>x[0]==='track').pop()[1]),false);
        checks.push('Native bridge requests bounded view size and Wulf MOVE start/stop; outside tracking is released');
        await page.evaluate(function(){
            delete window.viewEnv.resizeViewPx;delete window.viewEnv.getClientSizePx;delete window.viewEnv.getViewSizePx;
            delete window.viewEnv.handleViewEvent;
        });
        await page.setViewportSize({width: 720, height: 720});
        await page.screenshot({path: path.join(__dirname, 'ledger-narrow.png')});
        await page.setViewportSize({width: 500, height: 720});
        const scroll = await page.locator('.lc-content').evaluate(node => ({height: node.clientHeight, total: node.scrollHeight}));
        assert(scroll.total >= scroll.height);
        const bounds = await page.locator('.lc-window').boundingBox();
        assert(bounds.x >= 0 && bounds.y >= 0 && bounds.x + bounds.width <= 501 && bounds.y + bounds.height <= 721);
        await page.screenshot({path: path.join(__dirname, 'ledger-compact.png')});
        checks.push('Desktop/narrow/compact bounds and internal scroll');
        await page.setViewportSize({width:1100,height:850});
        await target.fill('1234567');
        await target.evaluate(n=>n.setSelectionRange(3,3));
        const preservedGoalDraft=await target.inputValue();
        const preservedGoalCaret=await target.evaluate(n=>n.selectionStart);
        const beforeHistoryCalls=await page.evaluate(()=>window.__calls.length);
        await page.locator('#lc-history-control').scrollIntoViewIfNeeded();
        assert.strictEqual(await page.locator('#lc-history-manual,#lc-history-daily,#lc-history-server,#lc-history-hour,#lc-history-preserve,#lc-history-save,#lc-history-next').count(),0);
        assert.strictEqual(await page.locator('#lc-archive-panel').isVisible(),false);
        assert.strictEqual(await page.locator('#lc-history-reset').isDisabled(),false);
        assert.strictEqual(await target.inputValue(),preservedGoalDraft);
        assert.strictEqual(await target.evaluate(n=>n.selectionStart),preservedGoalCaret);
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),beforeHistoryCalls);
        checks.push('History settings expose only the explicit reset action, with no schedule/local-hour/preserve controls; previous days are collapsed and no hidden save command mutates a goal draft');
        const beforeResetCalls=await page.evaluate(()=>window.__calls.length);
        const manualResetBalance=await page.evaluate(()=>JSON.parse(window.model.payload).balance);
        const manualResetBalanceText=manualResetBalance.toLocaleString('de-DE');
        await page.locator('#lc-history-reset').click();
        assert.strictEqual(await page.locator('#lc-history-confirmation').isVisible(),true);
        assert((await page.locator('#lc-history-confirm-note').textContent()).includes('100.000 créditos'));
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),beforeResetCalls);
        await page.keyboard.press('Escape');
        assert.strictEqual(await page.locator('#lc-history-confirmation').isVisible(),false);
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),beforeResetCalls);
        await page.locator('#lc-history-reset').click();
        await page.locator('#lc-history-cancel').click();
        assert.strictEqual(await page.locator('#lc-history-confirmation').isVisible(),false);
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),beforeResetCalls);
        await page.locator('#lc-history-reset').click();
        await page.locator('#lc-history-confirm').click();
        assert.deepStrictEqual(await page.evaluate(()=>window.__calls[window.__calls.length-1]),['history-reset',{confirm:true}]);
        assert.strictEqual(await page.locator('#lc-history-confirm').isDisabled(),true);
        assert.strictEqual(await page.locator('#lc-history-reset').isDisabled(),true);
        await page.locator('#lc-history-toggle').click();
        assert.strictEqual(await page.locator('#lc-history-toggle').getAttribute('aria-expanded'),'true');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            payload.summary={battle_count:0,gross_credits:0,expenses:{repair:0,ammo:0,consumables:0,other:0},net_credits:0,average_net_credits:null,pending_battles:0};
            payload.history=[];payload.rewards=[];
            payload.goal={mode:'balance_growth',target:100000,active:true,baseline:payload.balance,final_balance:payload.balance+100000,since_utc:'2026-10-18T12:00:00Z',since_label:'18/10/2026 17:30 (hora local, UTC+05:30)',current:0,remaining:100000,progress_percent:0,complete:false,reset_generation:1};
            Object.assign(payload.history_control,{generation:1,since_utc:'2026-10-18T12:00:00Z',since_label:'18/10/2026 17:30 (hora local, UTC+05:30)'});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await page.locator('#lc-history-confirmation').isVisible(),false);
        assert.strictEqual(await page.locator('#lc-history-toggle').getAttribute('aria-expanded'),'false');
        assert.strictEqual(await page.locator('#lc-history-label').textContent(),'Todas las partidas');
        assert.strictEqual(await page.locator('#lc-battle-count').textContent(),'0 partidas registradas');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+0');
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),manualResetBalanceText);
        assert.strictEqual(await page.locator('#lc-gross').textContent(),'+0');
        assert.strictEqual(await page.locator('#lc-repair').textContent(),'0');
        assert.strictEqual(await page.locator('#lc-ammo').textContent(),'0');
        assert.strictEqual(await page.locator('#lc-consumables').textContent(),'0');
        assert.strictEqual(await page.locator('#lc-detail-net').textContent(),'+0');
        assert.strictEqual(await page.locator('#lc-history-settings-status').textContent(),'Historial reiniciado.');
        assert.strictEqual(await target.inputValue(),'100.000');
        assert.strictEqual(await page.locator('#lc-progress-text').textContent(),'0 / 100.000');
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),beforeResetCalls+1);
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.ready=false;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'\u2014');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.ready=true;payload.summary.battle_count=null;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),manualResetBalanceText);
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.summary.battle_count=0;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),manualResetBalanceText);
        checks.push('Manual reset requires confirmation, replaces the old goal draft with the editable100000-credit goal and current balance; Cancel/Escape send no reset, duplicate guards hold and generation acknowledgement clears counts, selection and picker');
        const beforeServerPayload=await page.evaluate(()=>JSON.parse(window.model.payload));
        const beforeServerCalls=await page.evaluate(()=>window.__calls.length);
        await target.fill('7654321');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            payload.balance=25901536;
            payload.goal={mode:'balance_growth',target:100000,active:true,baseline:payload.balance,final_balance:payload.balance+100000,since_utc:'2026-10-20T10:00:00Z',since_label:'20/10/2026 05:00 (hora local, UTC-05:00)',current:0,remaining:100000,progress_percent:0,complete:false,reset_generation:2};
            payload.summary={battle_count:0,gross_credits:0,expenses:{repair:0,ammo:0,consumables:0,other:0},net_credits:0,average_net_credits:null,pending_battles:0};
            payload.history=[];payload.rewards=[];
            Object.assign(payload.history_control,{generation:2,since_label:'20/10/2026 05:00 (hora local, UTC-05:00)',server_cycle:'2026-10-20T10:00:00Z',next_reset_label:'21/10/2026 05:00 (hora local, UTC-05:00)'});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await target.inputValue(),'100.000');
        assert.strictEqual(await page.locator('#lc-save-goal').isVisible(),true);
        assert.strictEqual(await page.locator('#lc-progress-text').textContent(),'0 / 100.000');
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'25.901.536');
        assert.strictEqual(await page.locator('#lc-balance').textContent(),'25.901.536');
        assert.strictEqual(await page.locator('#lc-net-total').textContent(),'+0');
        assert.strictEqual(await page.locator('#lc-battle-count').textContent(),'0 partidas registradas');
        assert.strictEqual(await page.locator('.lc-history-battle').count(),0);
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),beforeServerCalls,'Server-day rollover must not send a client reset command');
        checks.push('Acknowledged new server day replaces stale unsaved goal text with100000 credits at0percent and zero period results while preserving current account balance without issuing a native mutation');
        await target.fill('9876543');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            payload.goal={mode:'balance_growth',target:0,active:false,baseline:null,since_utc:null,since_label:'',current:0,remaining:0,progress_percent:0,complete:false,reset_generation:3};
            payload.history_control.generation=3;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await target.inputValue(),'0');
        assert.strictEqual(await page.locator('#lc-progress-text').textContent(),'Sin meta activa');
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),beforeServerCalls);
        checks.push('A legacy zero-target period acknowledgement still clears a stale draft without inventing a positive goal or sending a mutation');
        await page.evaluate(function(payload){window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();},beforeServerPayload);
        await page.setViewportSize({width:1100,height:850});
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            payload.ready=true;payload.balance=23549047;payload.message='Datos de prueba para verificar la interfaz';
            payload.goal={mode:'balance_growth',active:true,target:100000,baseline:22329142,final_balance:22429142,
                current:1219905,remaining:0,progress_percent:100,complete:true,since_utc:'2026-10-19T00:24:00Z',since_label:'18/10/2026 19:24 (hora local, UTC-05:00)'};
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        await target.fill('0');
        assert.strictEqual(await page.locator('#lc-save-goal').isDisabled(),false);
        assert.strictEqual(await page.locator('#lc-save-goal').textContent(),'Desactivar meta');
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'22.329.142');
        await page.locator('#lc-save-goal').click();
        assert.deepStrictEqual(await page.evaluate(()=>window.__calls[window.__calls.length-1]),['save',{value:'0',mode:'balance_growth'}]);
        assert.strictEqual(await target.isDisabled(),true);
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            Object.assign(payload.goal,{active:false,target:0,final_balance:null,current:1219905,remaining:0,progress_percent:0,complete:false,reset_generation:0});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await target.isDisabled(),false);
        assert.strictEqual(await target.inputValue(),'0');
        assert.strictEqual(await page.locator('#lc-progress-text').textContent(),'Sin meta activa');
        assert.strictEqual(await page.locator('#lc-percent').textContent(),'0,0 %');
        assert.strictEqual(await page.locator('#lc-fill').evaluate(n=>n.style.width),'0%');
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'22.329.142');
        assert.strictEqual(await page.locator('#lc-goal-base-status').textContent(),'Última meta · sin meta activa');
        assert(!(await page.locator('#lc-base-note').textContent()).includes('Saldo al completar'));
        assert((await page.locator('#lc-goal-accumulated').textContent()).includes('+1.219.905'));
        assert((await page.locator('#lc-goal-since').textContent()).includes('18/10/2026 19:24'));
        assert(!(await page.locator('#credit-ledger-view').textContent()).includes('Ganancia o pérdida por partida'));
        await page.locator('#lc-content').evaluate(n=>n.scrollTop=0);
        await page.screenshot({path:path.join(__dirname,'optional-goal-preview.png')});
        checks.push('Saving zero deactivates a reached goal through the native bridge and acknowledgement, removes completion and keeps its historical starting balance instead of the average');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.balance=23649047;payload.goal.current=1319905;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert((await page.locator('#lc-goal-accumulated').textContent()).includes('+1.319.905'));
        assert.strictEqual(await page.locator('#lc-fill').evaluate(n=>n.style.width),'0%');
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'22.329.142');
        assert((await page.locator('#lc-goal-since').textContent()).includes('18/10/2026 19:24'));
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.balance=null;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await page.locator('#lc-save-goal').isDisabled(),false);
        await page.locator('#lc-save-goal').click();
        assert.deepStrictEqual(await page.evaluate(()=>window.__calls[window.__calls.length-1]),['save',{value:'0',mode:'balance_growth'}]);
        await page.evaluate(()=>window.__handlers['viewEnv.onDataChanged']());
        await target.fill('500000');
        assert.strictEqual(await page.locator('#lc-save-goal').isDisabled(),true);
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.balance=23649047;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await page.locator('#lc-save-goal').textContent(),'Reactivar meta');
        await page.locator('#lc-save-goal').click();
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            Object.assign(payload.goal,{active:true,target:500000,baseline:22329142,final_balance:22829142,
                current:1319905,remaining:0,progress_percent:100,complete:true});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'22.329.142');
        assert.strictEqual(await page.locator('#lc-goal-base-status').textContent(),'Base de tu meta actual');
        assert.strictEqual(await page.locator('#lc-progress-text').textContent(),'1.319.905 / 500.000');
        assert((await page.locator('#lc-goal-since').textContent()).includes('18/10/2026 19:24'));
        checks.push('Zero can be saved while balance is pending; reactivation waits for balance and retains its original base, date and accumulated credits');
        const beforeGoalReset=await page.evaluate(function(){const payload=JSON.parse(window.model.payload);return {history:payload.history,summary:payload.summary,wallet:payload.wallet,history_control:payload.history_control};});
        await target.fill('750000');
        assert.strictEqual(await page.locator('#lc-reset-goal').isDisabled(),false);
        await page.locator('#lc-reset-goal').click();
        assert.deepStrictEqual(await page.evaluate(()=>window.__calls[window.__calls.length-1]),['goal-reset',{value:'750000',mode:'balance_growth'}]);
        assert.strictEqual(await target.inputValue(),'750.000');
        assert.strictEqual(await target.isDisabled(),true);
        assert.strictEqual(await page.locator('#lc-save-goal').isDisabled(),true);
        assert.strictEqual(await page.locator('#lc-history-reset').isDisabled(),true);
        const resetCallCount=await page.evaluate(()=>window.__calls.length);
        await page.locator('#lc-reset-goal').dispatchEvent('click');
        await page.locator('#lc-save-goal').dispatchEvent('click');
        await page.locator('#lc-history-reset').dispatchEvent('click');
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),resetCallCount);
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);payload.goal.target=750000;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await target.isDisabled(),true,'Matching target without a new reset generation is a stale update, not acknowledgement');
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'22.329.142');
        await page.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            Object.assign(payload.goal,{target:750000,baseline:23649047,final_balance:24399047,current:0,remaining:750000,
                progress_percent:0,complete:false,reset_generation:1,since_utc:'2026-10-19T05:00:00Z',since_label:'19/10/2026 00:00 (hora local, UTC-05:00)'});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await target.isDisabled(),false);
        assert.strictEqual(await target.inputValue(),'750.000');
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'23.649.047');
        assert.strictEqual(await page.locator('#lc-progress-text').textContent(),'0 / 750.000');
        assert.strictEqual(await page.locator('#lc-percent').textContent(),'0,0 %');
        assert((await page.locator('#lc-goal-since').textContent()).includes('19/10/2026 00:00'));
        assert.deepStrictEqual(await page.evaluate(function(){const payload=JSON.parse(window.model.payload);return {history:payload.history,summary:payload.summary,wallet:payload.wallet,history_control:payload.history_control};}),beforeGoalReset);
        await page.locator('.lc-goal').scrollIntoViewIfNeeded();
        await page.locator('.lc-goal').screenshot({path:path.join(__dirname,'goal-reset-preview.png')});
        checks.push('Dedicated goal reset sends the written positive target once, blocks concurrent goal/history mutations, waits for a new generation and starts at zero without erasing history, period totals or wallet');
        await target.fill('0');
        assert.strictEqual(await page.locator('#lc-reset-goal').isDisabled(),true);
        await page.locator('#lc-reset-goal').dispatchEvent('click');
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),resetCallCount);
        await target.fill('900000');
        await page.evaluate(function(){const payload=JSON.parse(window.model.payload);payload.balance=null;window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        assert.strictEqual(await page.locator('#lc-reset-goal').isDisabled(),true);
        await page.locator('#lc-reset-goal').dispatchEvent('click');
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),resetCallCount);
        await page.evaluate(function(){const payload=JSON.parse(window.model.payload);payload.balance=23649047;payload.ready=false;window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        assert.strictEqual(await page.locator('#lc-reset-goal').isDisabled(),true);
        await page.locator('#lc-reset-goal').dispatchEvent('click');
        assert.strictEqual(await page.evaluate(()=>window.__calls.length),resetCallCount);
        await page.evaluate(function(){const payload=JSON.parse(window.model.payload);payload.ready=true;window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        await page.locator('#lc-reset-goal').click();
        await page.evaluate(function(){const payload=JSON.parse(window.model.payload);payload.error='No se pudo reiniciar la meta.';window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        assert.strictEqual(await target.isDisabled(),false);
        assert.strictEqual(await target.inputValue(),'900.000');
        assert((await page.locator('#lc-draft-status').textContent()).includes('No se reinició'));
        assert.strictEqual(await page.locator('#lc-goal-base').textContent(),'23.649.047');
        await page.evaluate(function(){const payload=JSON.parse(window.model.payload);payload.error=null;window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        await page.locator('#lc-reset-goal').click();
        await page.evaluate(function(){const payload=JSON.parse(window.model.payload);Object.assign(payload.goal,{target:900000,final_balance:24549047,remaining:900000,reset_generation:2});window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        assert.strictEqual(await target.isDisabled(),false);
        checks.push('Goal reset rejects zero and unsynchronized balance, preserves the written target on backend errors and allows retry acknowledged by generation even when the balance and start time are unchanged');
        async function renderFourthCard(goalPatch,payloadPatch){
            const payload=JSON.parse(JSON.stringify(fourCardsPayload));
            Object.assign(payload,payloadPatch||{});
            Object.assign(payload.goal,goalPatch||{});
            await page.evaluate(function(value){window.model.payload=JSON.stringify(value);window.__handlers['viewEnv.onDataChanged']();},payload);
        }
        const remainingCard=page.locator('#lc-goal-remaining');
        const remainingStatus=page.locator('#lc-goal-remaining-status');
        await renderFourthCard();
        assert.strictEqual(await remainingCard.textContent(),'277.059');
        await renderFourthCard({}, {balance:null});
        assert.strictEqual(await remainingCard.textContent(),'\u2014');
        assert.strictEqual(await remainingStatus.textContent(),'Saldo pendiente');
        await renderFourthCard({remaining:null});
        assert.strictEqual(await remainingCard.textContent(),'\u2014');
        assert.strictEqual(await remainingStatus.textContent(),'Saldo pendiente');
        await renderFourthCard({current:2000000,remaining:0,progress_percent:100,complete:true}, {balance:24329142});
        assert.strictEqual(await remainingCard.textContent(),'0');
        assert.strictEqual(await remainingStatus.textContent(),'Meta alcanzada');
        await renderFourthCard({remaining:-1});
        assert.strictEqual(await remainingCard.textContent(),'0');
        await renderFourthCard({active:false,target:0,current:0,remaining:0,progress_percent:0,complete:false,final_balance:null});
        assert.strictEqual(await remainingCard.textContent(),'\u2014');
        assert.strictEqual(await remainingStatus.textContent(),'Sin meta activa');
        await renderFourthCard();
        await target.fill('2500000');
        assert.strictEqual(await remainingCard.textContent(),'277.059','An unsaved target must not replace the backend remaining amount');
        await page.locator('#lc-save-goal').click();
        assert.deepStrictEqual(await page.evaluate(()=>window.__calls[window.__calls.length-1]),['save',{value:'2500000',mode:'balance_growth'}]);
        assert.strictEqual(await remainingCard.textContent(),'277.059');
        await renderFourthCard({target:2500000,final_balance:24829142,remaining:777059,progress_percent:68.91764});
        assert.strictEqual(await remainingCard.textContent(),'777.059');
        assert.strictEqual(await target.inputValue(),'2.500.000');
        await renderFourthCard({remaining:9007199254740991});
        assert.strictEqual(await remainingCard.textContent(),'9.007.199.254.740.991');
        for(const geometry of [{width:1040,rows:1},{width:700,rows:2},{width:500,rows:4}]){
            await page.setViewportSize({width:geometry.width+48,height:1050});
            await page.locator('#lc-content').evaluate(n=>n.scrollTop=0);
            await page.waitForFunction(width=>Math.abs(document.getElementById('lc-window').getBoundingClientRect().width-width)<1,geometry.width);
            const cards=await page.evaluate(function(){
                const windowRect=document.getElementById('lc-window').getBoundingClientRect();
                const ids=['lc-net-total','lc-goal-base','lc-balance','lc-goal-remaining'];
                const rectangles=ids.map(id=>{
                    const amount=document.getElementById(id),card=amount.closest('.lc-stat');
                    const outer=card.getBoundingClientRect(),inner=amount.getBoundingClientRect();
                    return {top:Math.round(outer.top),contained:outer.left>=windowRect.left&&outer.right<=windowRect.right&&outer.top>=windowRect.top&&outer.bottom<=windowRect.bottom,
                        amountFits:inner.left>=outer.left&&inner.right<=outer.right&&inner.top>=outer.top&&inner.bottom<=outer.bottom&&amount.scrollWidth<=amount.clientWidth+1};
                });
                const status=document.getElementById('lc-goal-remaining-status').getBoundingClientRect();
                const last=document.getElementById('lc-goal-remaining').closest('.lc-stat').getBoundingClientRect();
                return {rows:new Set(rectangles.map(r=>r.top)).size,count:rectangles.length,
                    contained:rectangles.every(r=>r.contained&&r.amountFits),statusFits:status.left>=last.left&&status.right<=last.right&&status.top>=last.top&&status.bottom<=last.bottom};
            });
            assert.deepStrictEqual(cards,{rows:geometry.rows,count:4,contained:true,statusFits:true},'Four summary cards must fit at window width '+geometry.width);
            await page.locator('.lc-detail-marks').scrollIntoViewIfNeeded();
            await assertProgressScale(page,'#lc-meter','#lc-fill','.lc-detail-marks .lc-widget-mark');
        }
        await page.setViewportSize({width:1100,height:850});
        checks.push('Fourth summary card shows backend remaining credits, distinguishes pending/reached/inactive goals, ignores unsaved targets, updates after acknowledgement and fits four/two/one columns including maximum-length amounts');
        await page.evaluate(() => window.dispatchEvent(new Event('unload')));
        assert.deepStrictEqual(await page.evaluate(() => window.__removed), [77, 0]);
        // Reproduce the actual failure: JS can request a large size during
        // loading, yet C++ ignores it and assigns its 256px fallback later.
        // DOM-built is independent of resize requests. Only the native-ready
        // update allows a subsequent request to change the actual surface.
        const nativePage = await context.newPage();
        nativePage.on('pageerror', error => errors.push(String(error)));
        await nativePage.setViewportSize({width:256,height:256});
        const nativeBootstrap=function(payload) {
            window.isDomBuilt=false;window.__ops=[];window.__handlers={};window.__nativeReady=false;
            window.__nativeSize={width:256,height:256};
            window.engine={whenReady:Promise.resolve(),
                enableImmediateLayout:function(on){window.__ops.push(['immediate',on]);},
                on:function(n,f){window.__handlers[n]=f;},off:function(n){delete window.__handlers[n];}};
            window.viewEnv={getClientSizePx:function(){return {width:2560,height:1440};},
                getViewSizePx:function(){return {width:window.__nativeSize.width,height:window.__nativeSize.height};},
                resizeViewPx:function(w,h){
                    window.__ops.push(['size',w,h,window.isDomBuilt,window.__nativeReady]);
                    if(window.__nativeReady){
                        const changed=window.__nativeSize.width!==w||window.__nativeSize.height!==h;
                        window.__nativeSize={width:w,height:h};
                        const current=JSON.parse(window.model.payload);
                        current.window={ready:true,width:w,height:h};
                        window.model.payload=JSON.stringify(current);
                        if(changed){window.setTimeout(function(){window.__handlers['viewEnv.onDataChanged']();},0);}
                    }
                },
                addDataChangedCallback:function(){return 1;},removeDataChangedCallback:function(){}};
            payload.window={ready:false,width:0,height:0};
            window.__modeCalls=[];window.__closeCalls=[];window.__goalResetCalls=[];window.__vehicleFilterCalls=[];
            window.model={payload:JSON.stringify(payload),onLayoutReady:function(a){window.__ops.push(['layout',a]);},onClose:function(a){window.__closeCalls.push(a);},onSaveGoal:function(){},onRefresh:function(){},
                onResetGoal:function(value){window.__goalResetCalls.push(value);},
                onSetVehicleFilter:function(value){window.__vehicleFilterCalls.push(value);},
                onSetViewMode:function(value){
                    window.__modeCalls.push(value);
                    const current=JSON.parse(window.model.payload);
                    if(window.__rejectNextMode){window.__rejectNextMode=false;current.error='No se pudo guardar la vista.';}
                    else{current.view_mode=value.mode;current.error=null;}
                    window.model.payload=JSON.stringify(current);
                    window.setTimeout(function(){window.__handlers['viewEnv.onDataChanged']();},0);
                }};
            window.__completeNativeLoad=function(){
                window.__nativeReady=true;
                window.__nativeSize={width:256,height:256};
                window.__ops.push(['fallback',256,256]);
                const current=JSON.parse(window.model.payload);
                current.window={ready:true,width:256,height:256};
                window.model.payload=JSON.stringify(current);
                window.__handlers['viewEnv.onDataChanged']();
            };
        };
        await nativePage.evaluate(nativeBootstrap,example);
        await nativePage.setContent(html);
        await nativePage.addScriptTag({content:fs.readFileSync(path.join(ui,'ledger.js'),'utf8')});
        await nativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='size'),{timeout:5000});
        const startup=await nativePage.evaluate(()=>window.__ops);
        const firstResize=startup.findIndex(x=>x[0]==='size');
        const immediate=startup.findIndex(x=>x[0]==='immediate'&&x[1]===true);
        assert(immediate>=0&&immediate<firstResize,'Immediate layout must be enabled before requesting a native surface size');
        assert([[624,208],[1040,976]].some(size=>size[0]===startup[firstResize][1]&&size[1]===startup[firstResize][2]));
        assert.deepStrictEqual(startup[firstResize].slice(3),[false,false]);
        assert.deepStrictEqual(await nativePage.evaluate(()=>window.__nativeSize),{width:256,height:256});
        assert.strictEqual(await nativePage.evaluate(()=>window.isDomBuilt),false);
        await nativePage.evaluate(function(){window.isDomBuilt=true;window.__handlers['self.onDomBuilt']();});
        await nativePage.waitForFunction(()=>document.getElementById('lc-net-total').textContent==='-113.508');
        await nativePage.waitForFunction(()=>window.__ops.filter(x=>x[0]==='size'&&x[3]===true&&!x[4]).length>=3);
        assert.deepStrictEqual(await nativePage.evaluate(()=>window.__nativeSize),{width:256,height:256});
        await nativePage.evaluate(()=>window.__completeNativeLoad());
        await nativePage.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
        await nativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='layout'&&x[1].phase==='verified'&&x[1].nativeWidth===1040&&x[1].nativeHeight===976));
        const recovered=await nativePage.evaluate(()=>({ops:window.__ops,payload:JSON.parse(window.model.payload)}));
        const fallbackIndex=recovered.ops.findIndex(x=>x[0]==='fallback');
        assert(recovered.ops.some((x,i)=>i>fallbackIndex&&x[0]==='size'&&x[4]===true),'A native-ready update must retry the unchanged requested geometry');
        assert.deepStrictEqual(recovered.payload.window,{ready:true,width:1040,height:976});
        assert.strictEqual(recovered.ops.filter(x=>x[0]==='layout'&&x[1].phase==='verified').pop()[1].viewMode,'details');
        assert.strictEqual(await nativePage.locator('#lc-window').evaluate(n=>n.getBoundingClientRect().width),1040);
        await nativePage.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            payload.summary.reserves={personal:20000,clan:10000,known_battles:1,total_battles:1};
            payload.history[0].reserves={personal:20000,clan:10000};
            for(let repeat=0;repeat<3;repeat++){
                window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
            }
        });
        assert.strictEqual(await nativePage.locator('#lc-reserve-personal').textContent(),'+20.000');
        assert.strictEqual(await nativePage.locator('#lc-reserve-clan').textContent(),'+10.000');
        assert.strictEqual(await nativePage.locator('#lc-reserve-note').count(),1);
        assert.strictEqual(await nativePage.locator('#lc-gross').textContent(),'+56.028');
        assert.strictEqual(await nativePage.locator('#lc-detail-net').textContent(),'-113.508');
        assert.deepStrictEqual(await nativePage.evaluate(()=>window.__nativeSize),{width:1040,height:976});
        checks.push('Personal and clan reserve updates use the actual native model bridge without duplicate components, financial recalculation or changing the verified 1040x976 details surface');
        await nativePage.locator('#lc-target').fill('4000000');
        await nativePage.locator('#lc-reset-goal').click();
        assert.deepStrictEqual(await nativePage.evaluate(()=>window.__goalResetCalls),[{value:'4000000',mode:'balance_growth'}]);
        await nativePage.evaluate(()=>window.__handlers['viewEnv.onDataChanged']());
        assert.strictEqual(await nativePage.locator('#lc-target').isDisabled(),true);
        await nativePage.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            Object.assign(payload.goal,{target:4000000,reset_generation:1,baseline:22000000,current:0,
                final_balance:26000000,remaining:4000000,progress_percent:0,complete:false});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        assert.strictEqual(await nativePage.locator('#lc-target').isDisabled(),false);
        assert.strictEqual(await nativePage.locator('#lc-target').inputValue(),'4.000.000');
        assert.strictEqual(await nativePage.locator('#lc-progress-text').textContent(),'0 / 4.000.000');
        assert.strictEqual(await nativePage.locator('#lc-detail-net').textContent(),'-113.508');
        assert.deepStrictEqual(await nativePage.evaluate(()=>window.__nativeSize),{width:1040,height:976});
        checks.push('Native onResetGoal command carries the written amount and waits for generation acknowledgement even at unchanged baseline and date, retaining the battle loss and verified window dimensions');
        await nativePage.setViewportSize({width:1040,height:976});
        await nativePage.locator('#lc-content').evaluate(n=>n.scrollTop=0);
        await nativePage.locator('#lc-content').dispatchEvent('wheel',{deltaY:-3,deltaMode:0,bubbles:true,cancelable:true});
        const down = await nativePage.locator('#lc-content').evaluate(n=>n.scrollTop);
        assert(down>0);
        await nativePage.locator('#lc-content').dispatchEvent('wheel',{deltaY:3,deltaMode:0,bubbles:true,cancelable:true});
        assert((await nativePage.locator('#lc-content').evaluate(n=>n.scrollTop))<down);
        await nativePage.screenshot({path:path.join(__dirname,'ledger-native-bootstrap.png')});
        await nativePage.locator('#lc-back-widget').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208);
        await nativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='layout'&&x[1].phase==='verified'&&x[1].viewMode==='widget'&&x[1].nativeWidth===624&&x[1].nativeHeight===208));
        assert.deepStrictEqual(await nativePage.evaluate(()=>window.__modeCalls),[{mode:'widget'}]);
        assert.strictEqual(await nativePage.locator('#lc-widget').isVisible(),true);
        assert.strictEqual(await nativePage.locator('#lc-details').isVisible(),false);
        await nativePage.locator('#lc-widget-details').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
        await nativePage.waitForFunction(()=>window.__ops.filter(x=>x[0]==='layout'&&x[1].phase==='verified'&&x[1].viewMode==='details').length>=2);
        assert.deepStrictEqual(await nativePage.evaluate(()=>window.__modeCalls),[{mode:'widget'},{mode:'details'}]);
        await nativePage.evaluate(()=>window.__rejectNextMode=true);
        await nativePage.locator('#lc-back-widget').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976&&document.getElementById('lc-details').className.indexOf('lc-hidden')<0&&JSON.parse(window.model.payload).error);
        assert.strictEqual(await nativePage.locator('#lc-widget').isVisible(),false);
        assert.strictEqual(await nativePage.locator('#lc-details').isVisible(),true);
        assert.strictEqual(await nativePage.evaluate(()=>JSON.parse(window.model.payload).view_mode),'details');
        await nativePage.locator('#lc-back-widget').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208&&JSON.parse(window.model.payload).view_mode==='widget'&&!JSON.parse(window.model.payload).error);
        assert.deepStrictEqual((await nativePage.evaluate(()=>window.__modeCalls)).slice(-2),[{mode:'widget'},{mode:'widget'}]);
        checks.push('Widget/details commands resize and verify the actual native surface in both directions, including viewMode acknowledgements');
        await nativePage.locator('#lc-widget-close').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===184&&window.__nativeSize.height===144);
        await nativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='layout'&&x[1].phase==='verified'&&x[1].viewMode==='minimized'&&x[1].nativeWidth===184&&x[1].nativeHeight===144));
        assert.strictEqual(await nativePage.locator('#lc-minimized').isVisible(),true);
        assert.deepStrictEqual(await nativePage.locator('#lc-window').evaluate(n=>[n.getBoundingClientRect().width,n.getBoundingClientRect().height]),[184,144]);
        assert.strictEqual(await nativePage.evaluate(()=>window.__closeCalls.length),0);
        await nativePage.evaluate(()=>window.__rejectNextMode=true);
        await nativePage.locator('#lc-minimized-restore').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===184&&window.__nativeSize.height===144&&JSON.parse(window.model.payload).view_mode==='minimized'&&JSON.parse(window.model.payload).error);
        assert.strictEqual(await nativePage.locator('#lc-minimized').isVisible(),true);
        assert((await nativePage.locator('#lc-minimized-restore').getAttribute('title')).includes('No se pudo cambiar la vista'));
        await nativePage.locator('#lc-minimized-restore').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208&&JSON.parse(window.model.payload).view_mode==='widget'&&!JSON.parse(window.model.payload).error);
        await nativePage.locator('#lc-widget-details').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
        await nativePage.locator('#lc-close').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===184&&window.__nativeSize.height===144);
        assert.strictEqual(await nativePage.locator('#lc-details').isVisible(),false);
        assert.strictEqual(await nativePage.locator('#lc-minimized').isVisible(),true);
        await nativePage.locator('#lc-minimized-restore').click();
        await nativePage.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208);
        checks.push('Native minimize from both views acknowledges a real 184x144 surface; plus restores 624x208 and failed restoration rolls back safely without destroying the view');
        await nativePage.close();
        checks.push('Native loading ignores early sizes, retries after DOM and recovers from 256px C++ fallback after native-ready; reports verified actual surface dimensions');
        checks.push('Immediate layout precedes native resize; raw wheel down/up follow content direction');
        const nativeModePage=await context.newPage();
        nativeModePage.on('pageerror',error=>errors.push(String(error)));
        await nativeModePage.evaluate(installQaArt);
        await nativeModePage.setViewportSize({width:1100,height:1050});
        const nativeModePayload=JSON.parse(JSON.stringify(modePayload));
        nativeModePayload.history.forEach((row,index)=>{row.battle_mode={bonus_type:999,label:'Evento de prueba con nombre muy largo del modo de juego '+index+' para verificar la segunda línea'};});
        await nativeModePage.evaluate(nativeBootstrap,nativeModePayload);
        await nativeModePage.evaluate(function(){window.isDomBuilt=true;window.__nativeReady=true;});
        await nativeModePage.setContent(gamefaceHtml);
        await nativeModePage.addScriptTag({content:fs.readFileSync(path.join(ui,'ledger.js'),'utf8')});
        await nativeModePage.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
        await nativeModePage.locator('#lc-history-toggle').click();
        await nativeModePage.waitForTimeout(60);
        const nativeModeRows=await nativeModePage.locator('.lc-history-battle').evaluateAll(rows=>rows.map(row=>{
            const outer=row.getBoundingClientRect(),name=row.querySelector('.lc-history-tank').getBoundingClientRect();
            const stamp=row.querySelector('.lc-history-stamp').getBoundingClientRect(),net=row.querySelector('.lc-history-net').getBoundingClientRect();
            const viewport=document.getElementById('lc-history-options').getBoundingClientRect();
            return {height:outer.height,stampHeight:stamp.height,visible:outer.top>=viewport.top&&outer.bottom<=viewport.bottom,
                noOverlap:name.bottom<=stamp.top&&stamp.bottom<=outer.bottom&&stamp.right<=net.left+1};
        }));
        assert.strictEqual(nativeModeRows.length,5);
        assert(nativeModeRows.every(row=>row.height===72&&row.stampHeight===24&&row.visible&&row.noOverlap));
        assert.strictEqual(await nativeModePage.locator('#lc-history-track').isVisible(),false);
        await nativeModePage.locator('.lc-history-battle').nth(2).click();
        assert((await nativeModePage.locator('#lc-detail-mode').textContent()).includes('nombre muy largo del modo de juego 2'));
        assert.strictEqual(await nativeModePage.locator('#lc-detail-net').textContent(),'-113.508');
        assert.deepStrictEqual(await nativeModePage.evaluate(()=>window.__nativeSize),{width:1040,height:976});
        await nativeModePage.evaluate(function(source){
            const payload=JSON.parse(JSON.stringify(source));payload.window=JSON.parse(window.model.payload).window;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        },filterPayload);
        await chooseFilter(nativeModePage,'mode:20');
        assert.strictEqual(await nativeModePage.locator('#lc-net-total').textContent(),'-50.000');
        assert((await nativeModePage.locator('#lc-battle-count').textContent()).includes('105 partidas registradas'));
        await nativeModePage.locator('#lc-history-toggle').click();await nativeModePage.waitForTimeout(60);
        assert.strictEqual(await nativeModePage.locator('.lc-history-battle').count(),100);
        assert(await nativeModePage.locator('.lc-history-battle').evaluateAll(rows=>{
            const viewport=document.getElementById('lc-history-options').getBoundingClientRect();
            const complete=rows.filter(row=>{const rect=row.getBoundingClientRect();return rect.top>=viewport.top&&rect.bottom<=viewport.bottom;});
            return complete.length===5&&complete.every(row=>row.getBoundingClientRect().height===72);
        }));
        await nativeModePage.locator('.lc-history-battle').first().click();
        assert.strictEqual(await nativeModePage.locator('#lc-detail-net').textContent(),'-500');
        assert.strictEqual(await nativeModePage.locator('#lc-detail-mode').textContent(),'Modo de juego: Escaramuza');
        assert.deepStrictEqual(await nativeModePage.evaluate(()=>window.__nativeSize),{width:1040,height:976});
        assert.deepStrictEqual(await nativeModePage.evaluate(()=>window.__modeCalls),[]);
        checks.push('Gameface mode filter remains a local view operation at 1040x976, shows the complete filtered count and five whole 66px battle rows, then selects the real mode-specific financial record');
        await nativeModePage.evaluate(function(source){
            const payload=JSON.parse(JSON.stringify(source));payload.window=JSON.parse(window.model.payload).window;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        },vehiclePayload);
        await chooseFilter(nativeModePage,'all');
        await chooseVehicle(nativeModePage,'vehicle:321');
        const nativeVehicleRequest=await nativeModePage.evaluate(()=>window.__vehicleFilterCalls.slice(-1)[0]);
        assert.strictEqual(nativeVehicleRequest.account_context,vehiclePayload.account_context);
        assert.strictEqual(await nativeModePage.locator('#lc-net-total').textContent(),'+450.000');
        await vehicleResponse(nativeModePage,nativeVehicleRequest,xmGroup,xmRows);
        assert.strictEqual(await nativeModePage.locator('#lc-net-total').textContent(),'+450.000');
        assert((await nativeModePage.locator('#lc-battle-count').textContent()).includes('110 partidas registradas'));
        assert.deepStrictEqual(await nativeModePage.evaluate(()=>window.__nativeSize),{width:1040,height:976});
        checks.push('Gameface tank selection immediately shows full known totals while querying history and retains verified1040x976 geometry after acknowledgement');
        await nativeModePage.evaluate(function(source){
            const payload=JSON.parse(JSON.stringify(source));payload.window=JSON.parse(window.model.payload).window;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        },artPayload);
        await nativeModePage.locator('#lc-mode-toggle').click();
        assert(await nativeModePage.locator('#lc-mode-list .lc-mode-option').evaluateAll(rows=>rows.every(row=>{
            const box=row.getBoundingClientRect(),art=row.querySelector('.lc-mode-art').getBoundingClientRect(),label=row.querySelector('.lc-filter-option-label').getBoundingClientRect();
            return box.height===56&&art.right<=label.left&&label.right<=box.right&&art.top>=box.top&&art.bottom<=box.bottom;
        })));
        await nativeModePage.locator('[data-mode-key="mode:102"]').click();
        assert.strictEqual(await nativeModePage.locator('#lc-mode-icon img').getAttribute('data-native-src'),modeIcons.tower);
        await nativeModePage.locator('#lc-history-toggle').click();await nativeModePage.waitForTimeout(60);
        assert(await nativeModePage.locator('.lc-history-battle').evaluateAll(rows=>{
            const viewport=document.getElementById('lc-history-options').getBoundingClientRect();
            return rows.filter(row=>{const box=row.getBoundingClientRect();return box.top>=viewport.top&&box.bottom<=viewport.bottom;}).length===5&&rows.every(row=>{
                const box=row.getBoundingClientRect(),stamp=row.querySelector('.lc-history-stamp').getBoundingClientRect(),logo=row.querySelector('.lc-history-stamp .lc-mode-art').getBoundingClientRect();
                return box.height===72&&stamp.height===24&&logo.width===24&&logo.height===24&&logo.top>=stamp.top&&logo.bottom<=stamp.bottom;
            });
        }));
        await nativeModePage.locator('.lc-history-battle').first().click();
        assert.strictEqual(await nativeModePage.locator('#lc-detail-vehicles .lc-tank-tier').textContent(),'Nivel IX');
        assert.strictEqual(await nativeModePage.locator('#lc-detail-vehicles img').getAttribute('data-native-src'),artPayload.history[0].vehicles[0].icon);
        assert.strictEqual(await nativeModePage.locator('#lc-detail-mode img').getAttribute('data-native-src'),modeIcons.tower);
        await nativeModePage.locator('#lc-vehicle-toggle').click();
        assert(await nativeModePage.locator('#lc-vehicle-list .lc-vehicle-option').evaluateAll(rows=>rows.every(row=>{
            const box=row.getBoundingClientRect(),label=row.querySelector('.lc-filter-option-label').getBoundingClientRect(),art=row.querySelector('.lc-tank-art')||row.querySelector('.lc-filter-tank-space');
            const image=art.getBoundingClientRect();
            return box.height===56&&image.right<=label.left&&label.right<=box.right&&image.top>=box.top&&image.bottom<=box.bottom;
        })));
        await nativeModePage.locator('#lc-window').screenshot({path:path.join(__dirname,'native-art-preview.png')});
        await nativeModePage.keyboard.press('Escape');
        await nativeModePage.evaluate(function(){window.viewEnv.getClientSizePx=function(){return {width:450,height:800};};window.dispatchEvent(new Event('resize'));});
        await nativeModePage.setViewportSize({width:450,height:800});
        await nativeModePage.waitForFunction(()=>window.__nativeSize.width===402);
        await nativeModePage.locator('#lc-mode-toggle').click();
        assert(await nativeModePage.locator('#lc-mode-list .lc-mode-option').evaluateAll(rows=>rows.every(row=>{
            const box=row.getBoundingClientRect(),label=row.querySelector('.lc-filter-option-label').getBoundingClientRect(),art=row.querySelector('.lc-mode-art').getBoundingClientRect();
            return label.width>65&&art.width===40&&art.right<=label.left&&label.right<=box.right;
        })));
        await nativeModePage.keyboard.press('Escape');
        await nativeModePage.locator('#lc-vehicle-toggle').click();
        assert(await nativeModePage.locator('#lc-vehicle-list .lc-vehicle-option').evaluateAll(rows=>rows.every(row=>{
            const box=row.getBoundingClientRect(),label=row.querySelector('.lc-filter-option-label').getBoundingClientRect();
            return label.width>60&&label.right<=box.right&&label.left>=box.left;
        })));
        await nativeModePage.locator('#lc-window').screenshot({path:path.join(__dirname,'native-art-narrow-preview.png')});
        await nativeModePage.keyboard.press('Escape');
        await nativeModePage.locator('#lc-history-toggle').click();
        assert(await nativeModePage.locator('#lc-history-list .lc-history-battle').evaluateAll(rows=>rows.every(row=>{
            const r=row.getBoundingClientRect(),stamp=row.querySelector('.lc-history-stamp').getBoundingClientRect(),
                logo=row.querySelector('.lc-history-stamp .lc-mode-art').getBoundingClientRect(),net=row.querySelector('.lc-history-net').getBoundingClientRect();
            return r.height===72&&stamp.height===24&&logo.width===24&&logo.height===24&&logo.top>=stamp.top&&logo.bottom<=stamp.bottom&&stamp.right<=net.left+1;
        })));
        await nativeModePage.keyboard.press('Escape');
        await nativeModePage.evaluate(function(){window.viewEnv.getClientSizePx=function(){return {width:2560,height:1440};};window.dispatchEvent(new Event('resize'));});
        await nativeModePage.setViewportSize({width:1100,height:1050});
        await nativeModePage.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
        checks.push('Gameface mode emblems, current event tank thumbnails and Roman tiers fit opened/closed controls at native1040x976 and narrow402px surfaces; tiny mode logos preserve five complete66px battle rows with scroll and no label overlap');
        await nativeModePage.evaluate(function(){
            const payload=JSON.parse(window.model.payload);
            Object.assign(payload.history_control,{mode:'server',preserve_goal:false,server_clock_ready:true,
                since_label:'19/10/2026 05:00 (hora local, UTC-05:00)',next_reset_label:'20/10/2026 05:00 (hora local, UTC-05:00)',
                timezone_label:'Horario comunicado por el servidor. Hora local del equipo (UTC-05:00)'});
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
        });
        await nativeModePage.locator('#lc-history-control').scrollIntoViewIfNeeded();
        assert.strictEqual(await nativeModePage.locator('#lc-history-server,#lc-history-hour,#lc-history-preserve,.lc-history-mode-button').count(),0);
        assert.strictEqual(await nativeModePage.locator('#lc-history-reset').isVisible(),true);
        assert.strictEqual(await nativeModePage.locator('#lc-archive-panel').isVisible(),false);
        assert.deepStrictEqual(await nativeModePage.evaluate(()=>window.__nativeSize),{width:1040,height:976});
        await nativeModePage.locator('#lc-window').screenshot({path:path.join(__dirname,'server-history-preview.png')});
        checks.push('Gameface history panel has one manual reset action and a collapsed previous-days entry without any visible schedule configuration at native1040x976 bounds');
        await nativeModePage.close();
        checks.push('Gameface-style default flex layout keeps five complete 66px history rows with long mode names, fixed one-line time/mode stamps and no overlap with tank names, net values or native bounds');
        const widgetPage=await context.newPage();
        widgetPage.on('pageerror',error=>errors.push(String(error)));
        await widgetPage.setViewportSize({width:1100,height:850});
        const widgetPayload=JSON.parse(JSON.stringify(example));
        delete widgetPayload.view_mode;
        delete widgetPayload.window;
        widgetPayload.message='';
        widgetPayload.history=[];widgetPayload.rewards=[];
        widgetPayload.balance=22000000;
        widgetPayload.summary={battle_count:0,gross_credits:0,expenses:{repair:0,ammo:0,consumables:0,other:0},net_credits:0,average_net_credits:null,pending_battles:0};
        widgetPayload.goal={mode:'balance_growth',active:true,target:1000000,baseline:22000000,final_balance:23000000,current:0,remaining:1000000,progress_percent:0,complete:false};
        widgetPayload.wallet={ready:true,baseline:22000000,balance:22000000,battle_net:0,external_credits:0,unclassified:0};
        await widgetPage.evaluate(function(payload){
            window.__modeCalls=[];window.__calls=[];window.__handlers={};window.isDomBuilt=true;
            window.engine={whenReady:Promise.resolve(),enableImmediateLayout:function(){},on:function(n,f){window.__handlers[n]=f;},off:function(n){delete window.__handlers[n];}};
            window.viewEnv={addDataChangedCallback:function(){return 10;},removeDataChangedCallback:function(){}};
            window.model={payload:JSON.stringify(payload),onSaveGoal:function(v){window.__calls.push(['save',v]);},onClose:function(v){window.__calls.push(['close',v]);},
                onRefresh:function(){},onSaveHistory:function(){},onResetHistory:function(){},onSetViewMode:function(value){window.__modeCalls.push(value);}};
        },widgetPayload);
        await widgetPage.setContent(gamefaceHtml);
        await widgetPage.addScriptTag({content:fs.readFileSync(path.join(ui,'ledger.js'),'utf8')});
        await widgetPage.waitForFunction(()=>document.getElementById('lc-widget-percent').textContent==='0,0 %');
        const widgetBounds=await widgetPage.locator('#lc-window').boundingBox();
        assert.deepStrictEqual([widgetBounds.width,widgetBounds.height],[624,208]);
        assert.strictEqual(await widgetPage.locator('#lc-widget').isVisible(),true);
        assert.strictEqual(await widgetPage.locator('#lc-details').isVisible(),false);
        assert.strictEqual(await widgetPage.locator('#lc-widget-meter').getAttribute('aria-valuenow'),'0');
        assert.strictEqual(await widgetPage.locator('#lc-widget-fill').evaluate(n=>n.style.width),'0%');
        const compactElements=['#lc-widget-percent','#lc-widget-progress','#lc-widget-status','#lc-widget-meter','#lc-widget-period','#lc-widget-balance','#lc-widget-details','#lc-widget-close'];
        async function assertWidgetContentsFit(){
            const outer=await widgetPage.locator('#lc-window').boundingBox();
            for(const selector of compactElements){
                const box=await widgetPage.locator(selector).boundingBox();
                assert(box&&box.x>=outer.x-1&&box.y>=outer.y-1&&box.x+box.width<=outer.x+outer.width+1&&box.y+box.height<=outer.y+outer.height+1,selector+' must fit inside the compact window');
            }
        }
        async function assertWidgetRowsAligned(allowWrappedProgress=false){
            const result=await widgetPage.evaluate(function(allowWrap){
                const box=node=>node.getBoundingClientRect();
                const progress=document.getElementById('lc-widget-progress');
                const parts=Array.from(progress.children);
                const rows=['lc-widget-progress','lc-widget-status','lc-widget-period','lc-widget-balance'].map(id=>{
                    const node=document.getElementById(id),outer=box(node);
                    const children=Array.from(node.children).filter(child=>getComputedStyle(child).display!=='none');
                    const bounds=children.map(box);
                    return {id,flex:!children.length||(getComputedStyle(node).display==='flex'&&getComputedStyle(node).flexDirection==='row'),
                        noMixedText:!children.length||!Array.from(node.childNodes).some(child=>child.nodeType===3&&child.textContent.trim()),
                        fit:bounds.every(child=>child.left>=outer.left-1&&child.right<=outer.right+1&&child.top>=outer.top-1&&child.bottom<=outer.bottom+1),
                        sameLine:(id==='lc-widget-progress'&&allowWrap)||bounds.every(child=>!bounds.length||Math.min(child.bottom,bounds[0].bottom)-Math.max(child.top,bounds[0].top)>Math.min(child.height,bounds[0].height)/2)};
                });
                const current=box(parts[0]),separator=box(parts[1]),target=box(parts[2]);
                const percent=box(document.getElementById('lc-widget-percent'));
                const status=box(document.getElementById('lc-widget-status'));
                const meter=box(document.getElementById('lc-widget-meter'));
                const chart=box(document.getElementById('lc-widget-chart'));
                const footer=box(document.querySelector('.lc-widget-footer'));
                return {partClasses:parts.map(node=>node.classList.contains('lc-amount')?'amount':node.classList.contains('lc-text-part')?'text':'other'),
                    rowsValid:rows.every(row=>row.flex&&row.noMixedText&&row.fit&&row.sameLine),
                    amountOrder:allowWrap||(current.right<=separator.left+1&&separator.right<=target.left+1&&Math.abs(current.top-target.top)<=1),
                    percentSeparate:box(progress).left>=percent.right-1,
                    statusBelow:status.top>=box(progress).bottom-1,
                    meterBelow:meter.top>=status.bottom-1,
                    footerBelow:footer.top>=chart.bottom-1,debugRows:rows};
            },allowWrappedProgress);
            const debugRows=result.debugRows;delete result.debugRows;
            assert.deepStrictEqual(result,{partClasses:['amount','text','amount','text'],rowsValid:true,amountOrder:true,percentSeparate:true,statusBelow:true,meterBelow:true,footerBelow:true},'Gameface-style row geometry: '+JSON.stringify(debugRows));
        }
        await assertWidgetContentsFit();
        await assertWidgetRowsAligned();
        assert((await widgetPage.locator('#lc-widget-progress').textContent()).includes('0 / 1.000.000'));
        assert((await widgetPage.locator('#lc-widget-balance').textContent()).includes('22.000.000'));
        checks.push('Default widget is a bounded 624x208 window with readable contents and genuine zero progress');
        async function updateWidget(patch){
            await widgetPage.evaluate(function(value){
                const payload=JSON.parse(window.model.payload);
                Object.keys(value).forEach(key=>payload[key]=value[key]);
                window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();
            },patch);
        }
        await updateWidget({ready:false,balance:null,goal:{active:true,target:1000000,baseline:22000000,current:null,remaining:null,progress_percent:null,complete:false}});
        assert((await widgetPage.locator('#lc-widget-percent').textContent()).includes('\u2014'));
        assert.strictEqual(await widgetPage.locator('#lc-widget-fill').evaluate(n=>n.style.width),'0%');
        assert(!/100[,\.]0/.test(await widgetPage.locator('#lc-widget-percent').textContent()));
        assert(/sincron|esper/i.test(await widgetPage.locator('#lc-widget-status').textContent()));
        await updateWidget({ready:true,balance:22000000,goal:{active:false,target:0,baseline:null,current:0,remaining:0,progress_percent:0,complete:false}});
        assert(!/100[,\.]0/.test(await widgetPage.locator('#lc-widget-percent').textContent()));
        assert.strictEqual(await widgetPage.locator('#lc-widget-fill').evaluate(n=>n.style.width),'0%');
        assert(/meta/i.test(await widgetPage.locator('#lc-widget-status').textContent()));
        checks.push('Unknown balance and inactive goals never show false completion; pending values remain visibly unsynchronized');
        const progressGoal={mode:'balance_growth',active:true,target:1000000,baseline:22000000,final_balance:23000000,current:426000,remaining:574000,progress_percent:42.6,complete:false};
        const progressWallet={ready:true,baseline:22000000,balance:22426000,battle_net:300000,external_credits:126000,unclassified:0};
        await updateWidget({balance:22426000,goal:progressGoal,wallet:progressWallet,
            summary:{battle_count:12,gross_credits:1200000,expenses:{repair:250000,ammo:500000,consumables:150000,other:0},net_credits:300000,average_net_credits:25000,pending_battles:0}});
        assert.strictEqual(await widgetPage.locator('#lc-widget-percent').textContent(),'42,6 %');
        assert.strictEqual(await widgetPage.locator('#lc-widget-meter').getAttribute('aria-valuenow'),'42.6');
        assert.strictEqual(await widgetPage.locator('#lc-widget-fill').evaluate(n=>n.style.width),'42.6%');
        assert((await widgetPage.locator('#lc-widget-progress').textContent()).includes('426.000 / 1.000.000'));
        assert((await widgetPage.locator('#lc-widget-status').textContent()).includes('574.000'));
        assert((await widgetPage.locator('#lc-widget-balance').textContent()).includes('22.426.000'));
        assert((await widgetPage.locator('#lc-widget-period').textContent()).includes('Batallas del período +300.000'));
        assert((await widgetPage.locator('#lc-widget-period').textContent()).includes('12 partidas'));
        const fillRatio=await widgetPage.locator('#lc-widget-meter').evaluate(n=>n.querySelector('#lc-widget-fill').getBoundingClientRect().width/n.getBoundingClientRect().width);
        assert(Math.abs(fillRatio-0.426)<0.015);
        await assertProgressScale(widgetPage,'#lc-widget-meter','#lc-widget-fill','#lc-widget .lc-widget-mark');
        await assertWidgetContentsFit();
        await widgetPage.locator('#lc-window').screenshot({path:path.join(__dirname,'ledger-widget.png')});
        checks.push('Widget fractional progress follows the native payload continuously; the 8px bar and ten proportional percentage labels fit in widget/details while the battle-only period result stays distinct');
        await updateWidget({balance:24357991,goal:{mode:'balance_growth',active:true,target:2500000,baseline:22329142,final_balance:24829142,
            current:2028849,remaining:471151,progress_percent:81.15396,complete:false},
            wallet:{ready:true,baseline:22329142,balance:24357991,battle_net:2028849,external_credits:0,unclassified:0},
            summary:{battle_count:19,gross_credits:2928849,expenses:{repair:250000,ammo:500000,consumables:150000,other:0},net_credits:2028849,average_net_credits:106782,pending_battles:0}});
        assert.strictEqual(await widgetPage.locator('#lc-widget-percent').textContent(),'81,2 %');
        assert((await widgetPage.locator('#lc-widget-progress').textContent()).includes('2.028.849 / 2.500.000'));
        assert((await widgetPage.locator('#lc-widget-status').textContent()).includes('471.151'));
        assert((await widgetPage.locator('#lc-widget-balance').textContent()).includes('24.357.991'));
        assert((await widgetPage.locator('#lc-widget-period').textContent()).includes('19 partidas'));
        assert(Math.abs(parseFloat(await widgetPage.locator('#lc-widget-fill').evaluate(n=>n.style.width))-81.15396)<0.001,'Ten labels must not snap the continuous progress to a tenth of the bar');
        const continuousFillRatio=await widgetPage.locator('#lc-widget-meter').evaluate(n=>document.getElementById('lc-widget-fill').getBoundingClientRect().width/n.getBoundingClientRect().width);
        assert(Math.abs(continuousFillRatio-0.8115396)<0.001);
        await assertWidgetContentsFit();
        await assertWidgetRowsAligned();
        await widgetPage.locator('#lc-window').screenshot({path:path.join(__dirname,'widget-layout-preview.png')});
        await updateWidget({balance:9007199254740990,goal:{mode:'balance_growth',active:true,target:9007199254740991,baseline:0,final_balance:9007199254740991,
            current:9007199254740990,remaining:1,progress_percent:99.99999,complete:false},
            wallet:{ready:true,baseline:0,balance:9007199254740990,battle_net:9007199254740990,external_credits:0,unclassified:0},
            summary:{battle_count:19,gross_credits:9007199254740990,expenses:{repair:0,ammo:0,consumables:0,other:0},net_credits:9007199254740990,average_net_credits:null,pending_battles:0}});
        await assertWidgetContentsFit();
        await assertWidgetRowsAligned();
        await widgetPage.setViewportSize({width:400,height:720});
        await assertWidgetContentsFit();
        await assertWidgetRowsAligned(true);
        await assertProgressScale(widgetPage,'#lc-widget-meter','#lc-widget-fill','#lc-widget .lc-widget-mark');
        await widgetPage.setViewportSize({width:1100,height:850});
        checks.push('Gameface-style default column divs and flex spans keep current/target, status, meter and footer aligned without mixed text nodes, including the reported 81.2-percent state and long amounts');
        await updateWidget({balance:21920000,goal:Object.assign({},progressGoal,{current:-80000,remaining:1080000,progress_percent:0}),
            wallet:Object.assign({},progressWallet,{balance:21920000,battle_net:-80000,external_credits:0}),
            summary:{battle_count:2,net_credits:-80000,average_net_credits:-40000,pending_battles:0}});
        assert.strictEqual(await widgetPage.locator('#lc-widget-percent').textContent(),'0,0 %');
        assert.strictEqual(await widgetPage.locator('#lc-widget-fill').evaluate(n=>n.style.width),'0%');
        assert((await widgetPage.locator('#lc-widget-progress').textContent()).includes('-80.000'));
        assert((await widgetPage.locator('#lc-widget-status').textContent()).includes('por debajo de la base'));
        await updateWidget({balance:22999999,goal:Object.assign({},progressGoal,{current:999999,remaining:1,progress_percent:99.9999,complete:false})});
        assert.notStrictEqual(await widgetPage.locator('#lc-widget-percent').textContent(),'100,0 %','Rounding must not report completion before the target is reached');
        assert((await widgetPage.locator('#lc-widget-status').textContent()).includes('1'));
        assert(parseFloat(await widgetPage.locator('#lc-widget-fill').evaluate(n=>n.style.width))<100);
        await updateWidget({balance:23100000,goal:Object.assign({},progressGoal,{current:1100000,remaining:0,progress_percent:100,complete:true}),
            wallet:Object.assign({},progressWallet,{balance:23100000,battle_net:1000000,external_credits:100000}),
            summary:{battle_count:12,gross_credits:1800000,expenses:{repair:200000,ammo:500000,consumables:100000,other:0},net_credits:1000000,average_net_credits:83333,pending_battles:0}});
        assert.strictEqual(await widgetPage.locator('#lc-widget-percent').textContent(),'100,0 %');
        assert.strictEqual(await widgetPage.locator('#lc-widget-fill').evaluate(n=>n.style.width),'100%');
        assert(/alcanz|complet/i.test(await widgetPage.locator('#lc-widget-status').textContent()));
        checks.push('Losses keep progress at zero with the real deficit; reached goals cap the bar at 100 percent');
        await widgetPage.locator('#lc-widget-details').click();
        assert.deepStrictEqual(await widgetPage.evaluate(()=>window.__modeCalls),[{mode:'details'}]);
        await updateWidget({view_mode:'widget'});
        assert.strictEqual(await widgetPage.locator('#lc-details').isVisible(),true,'A stale mode payload must not undo the requested detail view');
        await updateWidget({view_mode:'details'});
        assert.strictEqual(await widgetPage.locator('#lc-details').isVisible(),true);
        await updateWidget({view_mode:'widget'});
        assert.strictEqual(await widgetPage.locator('#lc-details').isVisible(),true,'A late stale mode update must not undo the user choice after its acknowledgement');
        const widgetTarget=widgetPage.locator('#lc-target');
        await widgetTarget.fill('2345678');
        await widgetTarget.evaluate(n=>n.setSelectionRange(3,3));
        const switchedDraft=await widgetTarget.inputValue();
        const switchedCaret=await widgetTarget.evaluate(n=>n.selectionStart);
        await widgetPage.locator('#lc-back-widget').click();
        await updateWidget({view_mode:'widget'});
        await widgetPage.locator('#lc-widget-details').click();
        await updateWidget({view_mode:'details'});
        assert.strictEqual(await widgetTarget.inputValue(),switchedDraft);
        assert.strictEqual(await widgetTarget.evaluate(n=>n.selectionStart),switchedCaret);
        assert.deepStrictEqual(await widgetPage.evaluate(()=>window.__modeCalls),[{mode:'details'},{mode:'widget'},{mode:'details'}]);
        checks.push('View-mode commands resist stale payloads and preserve an unsaved goal draft and caret across widget/detail switches');
        await widgetPage.locator('#lc-back-widget').click();
        await updateWidget({view_mode:'widget'});
        await widgetPage.locator('#lc-widget-details').click();
        await updateWidget({view_mode:'widget',error:'No se pudo guardar la vista.'});
        assert.strictEqual(await widgetPage.locator('#lc-widget').isVisible(),true);
        assert.strictEqual(await widgetPage.locator('#lc-details').isVisible(),false);
        assert.deepStrictEqual(await widgetPage.locator('#lc-window').evaluate(n=>[n.getBoundingClientRect().width,n.getBoundingClientRect().height]),[624,208]);
        assert.strictEqual(await widgetTarget.inputValue(),switchedDraft);
        await widgetPage.locator('#lc-widget-details').click();
        await updateWidget({view_mode:'details',error:null});
        assert.strictEqual(await widgetPage.locator('#lc-details').isVisible(),true);
        assert.strictEqual(await widgetTarget.inputValue(),switchedDraft);
        assert.strictEqual(await widgetTarget.evaluate(n=>n.selectionStart),switchedCaret);
        assert.deepStrictEqual((await widgetPage.evaluate(()=>window.__modeCalls)).slice(-2),[{mode:'details'},{mode:'details'}]);
        await widgetPage.locator('#lc-back-widget').click();
        await updateWidget({view_mode:'widget'});
        checks.push('Rejected view-mode saves roll back to authoritative mode and geometry, preserve goal drafts and allow successful retry in preview and native bridges');
        assert.strictEqual(await widgetPage.locator('#lc-widget-close .lc-progress-ring').count(),1);
        assert((await widgetPage.locator('#lc-widget-close').getAttribute('aria-label')).startsWith('Minimizar'));
        assert((await widgetPage.locator('#lc-close').getAttribute('aria-label')).startsWith('Minimizar'));
        await widgetPage.locator('#lc-widget-close').click();
        await updateWidget({view_mode:'widget'});
        assert.strictEqual(await widgetPage.locator('#lc-minimized').isVisible(),true,'Stale widget updates must not undo pending minimization');
        await updateWidget({view_mode:'minimized'});
        assert.strictEqual(await widgetPage.locator('#lc-widget').isVisible(),false);
        assert.strictEqual(await widgetPage.locator('#lc-details').isVisible(),false);
        assert.deepStrictEqual(await widgetPage.locator('#lc-window').evaluate(n=>[n.getBoundingClientRect().width,n.getBoundingClientRect().height]),[184,144]);
        const minBounds=await widgetPage.locator('#lc-window').boundingBox();
        const restoreBounds=await widgetPage.locator('#lc-minimized-restore').boundingBox();
        assert(restoreBounds&&restoreBounds.x>=minBounds.x&&restoreBounds.y>=minBounds.y&&restoreBounds.x+restoreBounds.width<=minBounds.x+184&&restoreBounds.y+restoreBounds.height<=minBounds.y+144);
        assert((await widgetPage.locator('#lc-minimized-restore').getAttribute('aria-label')).startsWith('Mostrar contabilidad de créditos'));
        assert(!(await widgetPage.locator('#lc-minimized-restore').textContent()).includes('+'));
        await widgetPage.locator('#lc-window').screenshot({path:path.join(__dirname,'ledger-minimized.png')});
        const beforeMinEscape=await widgetPage.evaluate(()=>window.__modeCalls.length);
        await widgetPage.keyboard.press('Escape');
        assert.strictEqual(await widgetPage.evaluate(()=>window.__modeCalls.length),beforeMinEscape);
        assert.strictEqual(await widgetPage.locator('#lc-minimized').isVisible(),true);
        assert.strictEqual(await widgetPage.evaluate(()=>window.__calls.filter(call=>call[0]==='close').length),0);
        assert.strictEqual(await widgetTarget.inputValue(),switchedDraft);
        assert.strictEqual(await widgetTarget.evaluate(n=>n.selectionStart),switchedCaret);
        await widgetPage.locator('#lc-minimized-restore').click();
        await updateWidget({view_mode:'widget'});
        await widgetPage.locator('#lc-widget-details').click();
        await updateWidget({view_mode:'details'});
        assert.strictEqual(await widgetTarget.inputValue(),switchedDraft);
        assert.strictEqual(await widgetTarget.evaluate(n=>n.selectionStart),switchedCaret);
        await widgetPage.locator('#lc-close').click();
        await updateWidget({view_mode:'minimized'});
        assert.strictEqual(await widgetPage.locator('#lc-minimized').isVisible(),true);
        await widgetPage.locator('#lc-minimized-restore').click();
        await updateWidget({view_mode:'widget'});
        await widgetPage.locator('#lc-widget-details').click();
        await updateWidget({view_mode:'details'});
        await widgetPage.keyboard.press('Escape');
        assert.strictEqual(await widgetPage.locator('#lc-widget').isVisible(),true);
        await updateWidget({view_mode:'widget'});
        await widgetPage.keyboard.press('Escape');
        assert.strictEqual(await widgetPage.locator('#lc-minimized').isVisible(),true);
        await updateWidget({view_mode:'minimized'});
        const afterMinimized=await widgetPage.evaluate(()=>window.__modeCalls.length);
        await widgetPage.keyboard.press('Escape');
        assert.strictEqual(await widgetPage.evaluate(()=>window.__modeCalls.length),afterMinimized);
        assert.strictEqual(await widgetPage.evaluate(()=>window.__calls.filter(call=>call[0]==='close').length),0);
        assert.strictEqual(await widgetTarget.inputValue(),switchedDraft);
        assert.strictEqual(await widgetTarget.evaluate(n=>n.selectionStart),switchedCaret);
        await widgetPage.locator('#lc-minimized-restore').click();
        await updateWidget({view_mode:'widget'});
        checks.push('Minus buttons and staged Escape keep a bounded visible plus shortcut; all three modes retain unsaved goal text and caret without sending a close command');
        await widgetPage.evaluate(function(){
            const background=document.createElement('button');background.id='qa-widget-garage';
            background.style.cssText='position:fixed;left:4px;top:4px;width:90px;height:28px;z-index:0;pointer-events:auto';
            background.onclick=function(){window.__garageClicked=true;};document.body.insertBefore(background,document.body.firstChild);
        });
        await widgetPage.locator('#qa-widget-garage').click();
        assert.strictEqual(await widgetPage.evaluate(()=>window.__garageClicked),true);
        let widgetHeader=await widgetPage.locator('#lc-widget-drag-bar').boundingBox();
        await widgetPage.mouse.move(widgetHeader.x+40,widgetHeader.y+15);await widgetPage.mouse.down();
        await widgetPage.mouse.move(2000,1500,{steps:5});await widgetPage.mouse.up();
        let draggedWidget=await widgetPage.locator('#lc-window').boundingBox();
        assert(draggedWidget.x>=0&&draggedWidget.y>=0&&draggedWidget.x+draggedWidget.width<=1101&&draggedWidget.y+draggedWidget.height<=851);
        widgetHeader=await widgetPage.locator('#lc-widget-drag-bar').boundingBox();
        await widgetPage.mouse.move(widgetHeader.x+40,widgetHeader.y+15);await widgetPage.mouse.down();
        await widgetPage.mouse.move(-200,-200,{steps:5});await widgetPage.mouse.up();
        draggedWidget=await widgetPage.locator('#lc-window').boundingBox();
        assert(draggedWidget.x>=0&&draggedWidget.y>=0);
        await widgetPage.setViewportSize({width:400,height:720});
        const narrowWidget=await widgetPage.locator('#lc-window').boundingBox();
        assert.deepStrictEqual([narrowWidget.width,narrowWidget.height],[368,232]);
        await assertWidgetContentsFit();
        await widgetPage.locator('#qa-widget-garage').evaluate(n=>n.remove());
        await widgetPage.locator('#lc-window').screenshot({path:path.join(__dirname,'ledger-widget-narrow.png')});
        checks.push('Compact widget leaves garage clicks available, clamps header dragging to screen bounds and stays readable at narrow width');
        await widgetPage.close();
        const widgetNativePage=await context.newPage();
        widgetNativePage.on('pageerror',error=>errors.push(String(error)));
        await widgetNativePage.setViewportSize({width:256,height:256});
        await widgetNativePage.evaluate(nativeBootstrap,widgetPayload);
        await widgetNativePage.setContent(gamefaceHtml);
        await widgetNativePage.addScriptTag({content:fs.readFileSync(path.join(ui,'ledger.js'),'utf8')});
        await widgetNativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='size'));
        assert.deepStrictEqual((await widgetNativePage.evaluate(()=>window.__ops)).find(x=>x[0]==='size').slice(0,3),['size',624,208]);
        await widgetNativePage.evaluate(function(){window.isDomBuilt=true;window.__handlers['self.onDomBuilt']();});
        await widgetNativePage.waitForFunction(()=>document.getElementById('lc-widget-percent').textContent==='0,0 %');
        assert.deepStrictEqual(await widgetNativePage.evaluate(()=>window.__nativeSize),{width:256,height:256});
        assert.strictEqual(await widgetNativePage.evaluate(()=>window.__ops.some(x=>x[0]==='layout'&&x[1].phase==='verified')),false,'Requested CSS dimensions are not proof that the native widget surface resized');
        await widgetNativePage.evaluate(()=>window.__completeNativeLoad());
        await widgetNativePage.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208);
        await widgetNativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='layout'&&x[1].phase==='verified'&&x[1].viewMode==='widget'&&x[1].nativeWidth===624&&x[1].nativeHeight===208));
        assert.strictEqual(await widgetNativePage.locator('#lc-widget').isVisible(),true);
        assert.strictEqual(await widgetNativePage.locator('#lc-details').isVisible(),false);
        await widgetNativePage.close();
        checks.push('Default native widget also recovers from the ignored-size 256px bootstrap and only verifies once the actual surface acknowledges 624x208');
        const minimizedNativePage=await context.newPage();
        minimizedNativePage.on('pageerror',error=>errors.push(String(error)));
        await minimizedNativePage.setViewportSize({width:256,height:256});
        const minimizedPayload=JSON.parse(JSON.stringify(widgetPayload));
        minimizedPayload.view_mode='minimized';
        await minimizedNativePage.evaluate(nativeBootstrap,minimizedPayload);
        await minimizedNativePage.setContent(gamefaceHtml);
        await minimizedNativePage.addScriptTag({content:fs.readFileSync(path.join(ui,'ledger.js'),'utf8')});
        await minimizedNativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='size'));
        await minimizedNativePage.evaluate(function(){window.isDomBuilt=true;window.__handlers['self.onDomBuilt']();});
        await minimizedNativePage.waitForFunction(()=>document.getElementById('lc-minimized').className.indexOf('lc-hidden')<0);
        await minimizedNativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='size'&&x[1]===184&&x[2]===144));
        assert.deepStrictEqual(await minimizedNativePage.evaluate(()=>window.__nativeSize),{width:256,height:256});
        assert.strictEqual(await minimizedNativePage.evaluate(()=>window.__ops.some(x=>x[0]==='layout'&&x[1].phase==='verified')),false);
        assert.deepStrictEqual(await minimizedNativePage.evaluate(()=>window.__modeCalls),[],'Opening an existing minimized preference must not send a replacement mode');
        await minimizedNativePage.evaluate(()=>window.__completeNativeLoad());
        await minimizedNativePage.waitForFunction(()=>window.__nativeSize.width===184&&window.__nativeSize.height===144);
        await minimizedNativePage.waitForFunction(()=>window.__ops.some(x=>x[0]==='layout'&&x[1].phase==='verified'&&x[1].viewMode==='minimized'&&x[1].nativeWidth===184&&x[1].nativeHeight===144));
        assert.deepStrictEqual(await minimizedNativePage.locator('#lc-window').evaluate(n=>[n.getBoundingClientRect().width,n.getBoundingClientRect().height]),[184,144]);
        await minimizedNativePage.locator('#lc-minimized-restore').click();
        await minimizedNativePage.waitForFunction(()=>window.__nativeSize.width===624&&window.__nativeSize.height===208);
        assert.deepStrictEqual(await minimizedNativePage.evaluate(()=>window.__modeCalls),[{mode:'widget'}]);
        assert.strictEqual(await minimizedNativePage.evaluate(()=>window.__closeCalls.length),0);
        await minimizedNativePage.close();
        checks.push('Persisted minimized mode loads without overrides, survives the unready 256px native fallback and verifies actual 184x144 bounds before plus restores the widget');
        async function assertArchiveDisclosure(surface,expanded,language){
            const action=language==='en'?(expanded?'Hide daily battle history':'Show daily battle history'):
                (expanded?'Ocultar historial por día':'Mostrar historial por día');
            assert.strictEqual(await surface.locator('#lc-archive-toggle').getAttribute('aria-expanded'),String(expanded));
            assert.strictEqual(await surface.locator('#lc-archive-toggle').getAttribute('aria-controls'),'lc-archive-panel');
            assert.strictEqual(await surface.locator('#lc-archive-toggle').getAttribute('aria-label'),action);
            assert.strictEqual(await surface.locator('#lc-archive-toggle').getAttribute('title'),action);
            assert.strictEqual(await surface.locator('#lc-archive-chevron').textContent(),expanded?'−':'+');
            assert.strictEqual(await surface.locator('#lc-archive-chevron').getAttribute('aria-hidden'),'true');
            const geometry=await surface.locator('#lc-archive-toggle').evaluate(button=>{
                const r=button.getBoundingClientRect(),badge=button.querySelector('#lc-archive-chevron'),b=badge.getBoundingClientRect(),
                    label=button.querySelector('.lc-archive-heading-label').getBoundingClientRect(),s=getComputedStyle(badge);
                return {height:r.height,width:b.width,badgeHeight:b.height,inside:b.left>=r.left&&b.right<=r.right&&b.top>=r.top&&b.bottom<=r.bottom,
                    noOverlap:label.right<=b.left,decorationOnly:s.pointerEvents==='none',border:s.borderTopWidth,
                    wholeHeaderCursor:getComputedStyle(button).cursor};
            });
            assert.deepStrictEqual(geometry,{height:56,width:32,badgeHeight:32,inside:true,noOverlap:true,
                decorationOnly:true,border:'1px',wholeHeaderCursor:'pointer'});
        }
        async function clickArchiveBadge(surface){
            await surface.locator('#lc-archive-toggle').scrollIntoViewIfNeeded();
            const rect=await surface.locator('#lc-archive-chevron').boundingBox();
            await surface.mouse.click(rect.x+rect.width/2,rect.y+rect.height/2);
        }
        const archivePage=await context.newPage();
        archivePage.on('pageerror',error=>errors.push(String(error)));
        await archivePage.setViewportSize({width:1100,height:1050});
        await archivePage.evaluate(installQaArt);
        const archivePayload=JSON.parse(JSON.stringify(vehiclePayload));
        archivePayload.history_control.mode='server';archivePayload.history_control.generation=4;
        archivePayload.history_archive={ready:true,selection:null,days:Array.from({length:45},(_,index)=>{
            const day=new Date(Date.UTC(2026,9,18-index,10)),label=String(day.getUTCDate()).padStart(2,'0')+'/'+String(day.getUTCMonth()+1).padStart(2,'0')+'/'+day.getUTCFullYear();
            return {key:day.toISOString().replace('.000Z','Z'),label,battle_count:110,net_credits:450000,summary:xmSummary,history_total:110,external_credits:20000};
        })};
        await archivePage.evaluate(nativeBootstrap,archivePayload);
        await archivePage.evaluate(()=>{
            window.isDomBuilt=true;window.__nativeReady=true;window.__archiveCalls=[];
            window.model.onSelectHistoryDay=function(value){window.__archiveCalls.push(value);};
            window.model.onSetLanguage=function(args){const payload=JSON.parse(window.model.payload);payload.language=args.language;
                payload.language_selection={request_id:String(args.request_id),requested_language:args.language,language:args.language,available:true,error:null};
                window.model.payload=JSON.stringify(payload);window.setTimeout(function(){window.__handlers['viewEnv.onDataChanged']();},0);};
        });
        await archivePage.setContent(gamefaceHtml);
        await archivePage.addScriptTag({content:fs.readFileSync(path.join(ui,'ledger.js'),'utf8')});
        await archivePage.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
        assert.strictEqual(await archivePage.locator('#lc-archive-panel').isVisible(),false);
        assert.deepStrictEqual(await archivePage.evaluate(()=>window.__archiveCalls),[]);
        await assertArchiveDisclosure(archivePage,false,'es');
        await archivePage.locator('#lc-archive-toggle').scrollIntoViewIfNeeded();
        await archivePage.locator('#lc-archive-toggle').screenshot({path:path.join(__dirname,'archive-toggle-closed-preview.png')});
        checks.push('Daily battle history starts collapsed with a discoverable32x28 bordered plus badge inside the full44px header, with matching aria-expanded, aria-controls, Spanish accessible action and decorative-only symbol');
        await archivePage.locator('#lc-target').fill('7654321');
        await archivePage.locator('#lc-target').evaluate(node=>node.setSelectionRange(3,3));
        const archiveLiveSnapshot=await archivePage.evaluate(()=>({target:document.getElementById('lc-target').value,caret:document.getElementById('lc-target').selectionStart,
            net:document.getElementById('lc-net-total').textContent,wallet:document.getElementById('lc-wallet-total').textContent,
            widget:document.getElementById('lc-widget-period').textContent,balance:document.getElementById('lc-balance').textContent}));
        await clickArchiveBadge(archivePage);
        await assertArchiveDisclosure(archivePage,true,'es');
        const archiveFirstRequest=await archivePage.evaluate(()=>window.__archiveCalls.slice(-1)[0]);
        assert.deepStrictEqual(archiveFirstRequest,{day_key:archivePayload.history_archive.days[0].key,mode_key:'all',vehicle_key:'all',
            request_id:archiveFirstRequest.request_id,account_context:archivePayload.account_context});
        assert.strictEqual(await archivePage.locator('#lc-archive-net').textContent(),'+450.000','Known complete day summary remains visible while history loads');
        const archiveModes=[{key:'mode:1',label:'Batalla aleatoria',icon:modeIcons.random,summary:xmSummary},
            {key:'mode:20',label:'Escaramuza',icon:modeIcons.skirmish,summary:modeXmGroup.summary},
            {key:'mode:102',label:'Torre oscura · Difícil',icon:modeIcons.tower,summary:emptyModeSummary}];
        async function archiveResponse(request,patch){
            const response=Object.assign({day_key:request.day_key,label:archivePayload.history_archive.days.find(day=>day.key===request.day_key).label,
                mode_key:request.mode_key,vehicle_key:request.vehicle_key,request_id:String(request.request_id),available:true,
                summary:xmSummary,mode_groups:archiveModes,vehicle_groups:[xmGroup,pzGroup],history:xmRows,history_total:110,external_credits:20000,
                account_context:request.account_context},patch||{});
            await archivePage.evaluate(value=>{const payload=JSON.parse(window.model.payload);payload.error=null;payload.history_archive.selection=value;
                window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();},response);
        }
        await archiveResponse(archiveFirstRequest);
        assert.strictEqual(await archivePage.locator('#lc-archive-status').textContent(),'');
        const archiveDisclosureCalls=await archivePage.evaluate(()=>window.__archiveCalls.length);
        await clickArchiveBadge(archivePage);await assertArchiveDisclosure(archivePage,false,'es');
        assert.strictEqual(await archivePage.locator('#lc-archive-panel').isVisible(),false);
        await archivePage.locator('#lc-archive-toggle').click({position:{x:18,y:22}});await assertArchiveDisclosure(archivePage,true,'es');
        await archivePage.locator('#lc-language-en').click();await assertArchiveDisclosure(archivePage,true,'en');
        await archivePage.locator('#lc-archive-toggle').focus();await archivePage.keyboard.press('Enter');
        await assertArchiveDisclosure(archivePage,false,'en');
        await clickArchiveBadge(archivePage);await assertArchiveDisclosure(archivePage,true,'en');
        await archivePage.locator('#lc-language-es').click();await assertArchiveDisclosure(archivePage,true,'es');
        assert.strictEqual(await archivePage.evaluate(()=>window.__archiveCalls.length),archiveDisclosureCalls);
        assert.deepStrictEqual(await archivePage.evaluate(()=>({target:document.getElementById('lc-target').value,caret:document.getElementById('lc-target').selectionStart,
            net:document.getElementById('lc-net-total').textContent,wallet:document.getElementById('lc-wallet-total').textContent,
            widget:document.getElementById('lc-widget-period').textContent,balance:document.getElementById('lc-balance').textContent})),archiveLiveSnapshot);
        await archivePage.locator('#lc-content').evaluate(n=>{n.scrollTop+=document.getElementById('lc-archive-toggle').getBoundingClientRect().top-n.getBoundingClientRect().top-12;});
        const archivePreviewBounds=await archivePage.locator('#lc-archive').boundingBox();
        await archivePage.screenshot({path:path.join(__dirname,'archive-toggle-preview.png'),clip:{x:archivePreviewBounds.x,y:archivePreviewBounds.y,width:archivePreviewBounds.width,height:440}});
        checks.push('Clicking the plus/minus badge, either side of the whole header or pressing Enter toggles the archive once with live bilingual Show/Hide accessibility labels, preserves cached results and performs no extra archive query or change to today’s wallet, goal draft/caret or totals');
        assert.strictEqual(await archivePage.locator('#lc-archive-battle-list .lc-history-battle').count(),100);
        assert((await archivePage.locator('#lc-archive-count').textContent()).includes('110 partidas'));
        assert((await archivePage.locator('#lc-archive-count').textContent()).includes('últimas 100'));
        assert.strictEqual(await archivePage.locator('#lc-archive-gross').textContent(),'+600.000');
        assert.strictEqual(await archivePage.locator('#lc-archive-clan').textContent(),'+15.000');
        assert.strictEqual(await archivePage.locator('#lc-archive-repair').textContent(),'-100.000');
        await assertSignColor(archivePage.locator('#lc-archive-repair'),'negative');
        await assertSignColor(archivePage.locator('#lc-archive-net'),'positive');
        assert((await archivePage.locator('#lc-archive-extra').textContent()).includes('+20.000'));
        assert((await archivePage.locator('#lc-archive-extra').textContent()).includes('toda la jornada'));
        await archivePage.locator('#lc-archive-battles').scrollIntoViewIfNeeded();
        assert(await archivePage.locator('#lc-archive-battle-list .lc-history-battle').evaluateAll(rows=>{
            const bounds=document.getElementById('lc-archive-battle-options').getBoundingClientRect();
            const complete=rows.filter(row=>{const r=row.getBoundingClientRect();return r.top>=bounds.top&&r.bottom<=bounds.bottom;});
            return complete.length===5&&complete.every(row=>{
                const r=row.getBoundingClientRect(),name=row.querySelector('.lc-history-time').getBoundingClientRect(),value=row.querySelector('.lc-history-net').getBoundingClientRect();
                return r.height===72&&name.right<=value.left+1&&value.right<=r.right;
            });
        }));
        await archivePage.locator('#lc-archive-battle-options').dispatchEvent('wheel',{deltaY:-240,bubbles:true});
        assert((await archivePage.locator('#lc-archive-battle-options').evaluate(node=>node.scrollTop))>0);
        const archiveOuter=await archivePage.locator('#lc-content').evaluate(node=>node.scrollTop);
        await archivePage.locator('#lc-archive-battle-options').dispatchEvent('wheel',{deltaY:-240,bubbles:true});
        assert.strictEqual(await archivePage.locator('#lc-content').evaluate(node=>node.scrollTop),archiveOuter);
        await archivePage.locator('#lc-archive-battle-options').evaluate(node=>node.scrollTop=0);
        await archivePage.locator('#lc-window').screenshot({path:path.join(__dirname,'daily-history-preview.png')});
        checks.push('Previous server days remain collapsed until requested; opening queries newest day once with account/context ID, accepts native string acknowledgement and uses complete110-battle totals with latest100 history, signed costs/reserves and five72px rows with isolated wheel scroll');
        await archivePage.locator('#lc-archive-mode-toggle').click();
        assert.strictEqual(await archivePage.locator('#lc-archive-mode-toggle').evaluate(n=>n.getBoundingClientRect().height),56);
        assert(await archivePage.locator('#lc-archive-mode-list .lc-mode-option').evaluateAll(rows=>rows.every(row=>{
            const box=row.getBoundingClientRect(),art=row.querySelector('.lc-mode-art').getBoundingClientRect(),label=row.querySelector('.lc-filter-option-label').getBoundingClientRect();
            return box.height===56&&art.width===40&&art.height===40&&art.top>=box.top&&art.bottom<=box.bottom&&art.right<=label.left&&label.right<=box.right;
        })));
        assert.strictEqual(await archivePage.locator('[data-archive-mode="mode:20"] .lc-mode-art img').getAttribute('data-native-src'),modeIcons.skirmish);
        await archivePage.locator('[data-archive-mode="mode:20"]').click();
        const archiveModeRequest=await archivePage.evaluate(()=>window.__archiveCalls.slice(-1)[0]);
        assert.strictEqual(archiveModeRequest.mode_key,'mode:20');
        assert.strictEqual(await archivePage.locator('#lc-archive-net').textContent(),'-25.000');
        await archiveResponse(archiveFirstRequest);
        assert((await archivePage.locator('#lc-archive-status').textContent()).includes('Cargando'));
        await archiveResponse(archiveModeRequest,{summary:modeXmGroup.summary,vehicle_groups:[modeXmGroup],history:[skirmishRow],history_total:10});
        assert.strictEqual(await archivePage.locator('#lc-archive-net').textContent(),'-25.000');
        await archivePage.locator('#lc-archive-vehicle-toggle').click();
        assert((await archivePage.locator('[data-archive-vehicle="vehicle:321"]').textContent()).includes('Nivel VIII'));
        await archivePage.locator('[data-archive-vehicle="vehicle:321"]').click();
        const archiveTankRequest=await archivePage.evaluate(()=>window.__archiveCalls.slice(-1)[0]);
        assert.strictEqual(archiveTankRequest.vehicle_key,'vehicle:321');assert.strictEqual(archiveTankRequest.mode_key,'mode:20');
        await archiveResponse(archiveTankRequest,{summary:Object.assign({},modeXmGroup.summary,{reserves:{personal:100,clan:200,known_battles:1,total_battles:10}}),vehicle_groups:[modeXmGroup],history:[Object.assign({},skirmishRow,{reserves:null})],history_total:10});
        assert((await archivePage.locator('#lc-archive-reserve-note').textContent()).includes('1 de 10 partidas'));
        await archivePage.locator('#lc-archive-battle-list .lc-history-battle').first().click();
        assert.strictEqual(await archivePage.locator('#lc-archive-net').textContent(),'-500');
        assert((await archivePage.locator('#lc-archive-detail-title').textContent()).includes('Escaramuza'));
        assert((await archivePage.locator('#lc-archive-detail-title').textContent()).includes('Nivel VIII'));
        assert((await archivePage.locator('#lc-archive-reserve-note').textContent()).includes('ya forman parte'));
        assert.deepStrictEqual(await archivePage.evaluate(()=>({target:document.getElementById('lc-target').value,caret:document.getElementById('lc-target').selectionStart,
            net:document.getElementById('lc-net-total').textContent,wallet:document.getElementById('lc-wallet-total').textContent,
            widget:document.getElementById('lc-widget-period').textContent,balance:document.getElementById('lc-balance').textContent})),archiveLiveSnapshot);
        assert.deepStrictEqual(await archivePage.evaluate(()=>window.__vehicleFilterCalls),[]);
        assert.deepStrictEqual(await archivePage.evaluate(()=>window.__goalResetCalls),[]);
        checks.push('Archive mode and tank filters carry only archive commands, ignore stale response IDs, retain native logos/images/Roman tiers and select individual financial records without changing live totals, wallet, goal draft/caret, balance or widget');
        await archivePage.locator('#lc-archive-day-toggle').click();
        assert.strictEqual(await archivePage.locator('[data-archive-day]').count(),45);
        assert(await archivePage.locator('#lc-archive-day-list .lc-mode-option').evaluateAll(rows=>rows.every(row=>row.getBoundingClientRect().height===48)));
        await archivePage.locator('[data-archive-day]').nth(35).click();
        const archiveOldRequest=await archivePage.evaluate(()=>window.__archiveCalls.slice(-1)[0]);
        assert.strictEqual(archiveOldRequest.day_key,archivePayload.history_archive.days[35].key);
        assert.strictEqual(archiveOldRequest.mode_key,'all');assert.strictEqual(archiveOldRequest.vehicle_key,'all');
        await archiveResponse(archiveOldRequest,{history:[],history_total:0,summary:emptyModeSummary});
        assert.strictEqual(await archivePage.locator('#lc-archive-net').textContent(),'+0');
        assert.strictEqual(await archivePage.locator('#lc-archive-battles').isVisible(),false);
        assert.strictEqual(await archivePage.locator('#lc-archive-vehicle-label').textContent(),'Todos los vehículos');
        checks.push('Archive day list scrolls beyond30 retained days, switching days resets only archive mode/tank/individual record and shows honest zero-empty results without disturbing today');
        // Accelerate only bounded query deadlines, leaving animation/native sizing clocks unchanged.
        await archivePage.evaluate(()=>{window.__originalSetTimeout=window.setTimeout;window.setTimeout=function(fn,delay){return window.__originalSetTimeout(fn,delay===6000?30:delay);};});
        await archivePage.locator('#lc-archive-day-toggle').click();await archivePage.locator('[data-archive-day]').first().click();
        const beforeTimeoutCount=await archivePage.evaluate(()=>window.__archiveCalls.length);
        await archivePage.waitForFunction(()=>!document.getElementById('lc-archive-retry').classList.contains('lc-hidden'));
        assert.strictEqual(await archivePage.evaluate(()=>window.__archiveCalls.length),beforeTimeoutCount+1,'Only one automatic retry is allowed');
        assert.strictEqual(await archivePage.locator('#lc-archive-net').textContent(),'+450.000');
        const staleTimeoutRequest=await archivePage.evaluate(()=>window.__archiveCalls[window.__archiveCalls.length-2]);
        await archivePage.evaluate(()=>{window.setTimeout=window.__originalSetTimeout;});
        await archivePage.locator('#lc-archive-retry').click();
        const retriedArchive=await archivePage.evaluate(()=>window.__archiveCalls.slice(-1)[0]);
        assert(retriedArchive.request_id>staleTimeoutRequest.request_id);
        await archiveResponse(staleTimeoutRequest);
        await archiveResponse(retriedArchive,{history:xmRows.slice(0,5),history_total:110});
        await archivePage.evaluate(()=>{window.setTimeout=window.__originalSetTimeout;});
        assert.strictEqual(await archivePage.locator('#lc-archive-retry').isVisible(),false);
        assert.strictEqual(await archivePage.locator('#lc-archive-gross').textContent(),'+600.000');
        assert.strictEqual(await archivePage.locator('#lc-archive-battle-list .lc-history-battle').count(),5);
        assert.strictEqual(await archivePage.locator('#lc-archive-status').textContent(),'');
        checks.push('Archive queries have two bounded automatic attempts then a visible retry; retries increase request IDs, reject late timed-out replies and preserve alreadyknown whole-day totals rather than indefinitely blanking income');
        // Test the originally reported vehicle filter path using native numeric strings and no optional reserve detail.
        await archivePage.evaluate(()=>{window.__originalSetTimeout=window.setTimeout;window.setTimeout=function(fn,delay){return window.__originalSetTimeout(fn,delay===6000?30:delay);};});
        await chooseVehicle(archivePage,'vehicle:654');
        assert.strictEqual(await archivePage.locator('#lc-gross').textContent(),'+300.000');
        assert.strictEqual(await archivePage.locator('#lc-detail-net').textContent(),'+200.000');
        await archivePage.waitForFunction(()=>!document.getElementById('lc-vehicle-retry').classList.contains('lc-hidden'));
        assert.strictEqual(await archivePage.evaluate(()=>window.__vehicleFilterCalls.length),2);
        const lastTimedRequest=await archivePage.evaluate(()=>window.__vehicleFilterCalls.slice(-1)[0]);
        await vehicleResponse(archivePage,Object.assign({},lastTimedRequest,{request_id:String(lastTimedRequest.request_id)}),pzGroup,[],{summary:Object.assign({},pzSummary,{reserves:null})});
        await archivePage.evaluate(()=>{window.setTimeout=window.__originalSetTimeout;});
        assert.strictEqual(await archivePage.locator('#lc-vehicle-status').textContent(),'');
        assert.strictEqual(await archivePage.locator('#lc-gross').textContent(),'+300.000');
        assert.strictEqual(await archivePage.locator('#lc-detail-net').textContent(),'+200.000');
        assert.strictEqual(await archivePage.locator('#lc-reserve-personal').textContent(),'—');
        assert((await archivePage.locator('#lc-reserve-note').textContent()).includes('ya están incluidos'));
        checks.push('Reported Pz.Neu native filter keeps known gross/net visible through two bounded attempts, accepts marshalled string response IDs, updates history and never gates income on missing optional reserves');
        await archivePage.locator('#lc-archive-toggle').click();
        assert.strictEqual(await archivePage.locator('#lc-archive-panel').isVisible(),false);
        await archivePage.locator('#lc-history-control').scrollIntoViewIfNeeded();
        await archivePage.locator('#lc-window').screenshot({path:path.join(__dirname,'history-simplified-preview.png')});
        await archivePage.locator('#lc-archive-toggle').click();
        await archivePage.evaluate(()=>{window.viewEnv.getClientSizePx=function(){return {width:450,height:1000};};window.dispatchEvent(new Event('resize'));});
        await archivePage.setViewportSize({width:450,height:1000});
        await archivePage.waitForFunction(()=>window.__nativeSize.width===402);
        await assertArchiveDisclosure(archivePage,true,'es');
        await archivePage.locator('#lc-language-en').click();await assertArchiveDisclosure(archivePage,true,'en');
        await clickArchiveBadge(archivePage);await assertArchiveDisclosure(archivePage,false,'en');
        await archivePage.locator('#lc-archive-toggle').click({position:{x:18,y:22}});await assertArchiveDisclosure(archivePage,true,'en');
        await archivePage.locator('#lc-language-es').click();await assertArchiveDisclosure(archivePage,true,'es');
        await archivePage.locator('#lc-archive-battles').scrollIntoViewIfNeeded();
        assert(await archivePage.locator('#lc-archive .lc-history-battle').evaluateAll(rows=>rows.every(row=>{
            const r=row.getBoundingClientRect(),name=row.querySelector('.lc-history-time').getBoundingClientRect(),value=row.querySelector('.lc-history-net').getBoundingClientRect();
            return r.height===72&&name.right<=value.left+1&&value.right<=r.right;
        })));
        for(const kind of ['day','mode','vehicle']){
            await archivePage.locator('#lc-archive-'+kind+'-toggle').click();
            assert(await archivePage.locator('#lc-archive-'+kind+'-list .lc-mode-option').evaluateAll(rows=>rows.every(row=>{
                const r=row.getBoundingClientRect(),name=row.querySelector('.lc-filter-option-label').getBoundingClientRect();
                return r.width>0&&name.left>=r.left&&name.right<=r.right+1&&name.bottom<=r.bottom+1;
            })));
            await archivePage.keyboard.press('Escape');
        }
        await archivePage.locator('#lc-window').screenshot({path:path.join(__dirname,'daily-history-narrow-preview.png')});
        checks.push('Gameface previous-day controls, art/tier/history rows and amounts stay separated at native1040x976 and402px narrow bounds; collapsed entry is discreet below the sole manual reset action');
        await archivePage.evaluate(()=>{const payload=JSON.parse(window.model.payload);payload.history_control.generation+=1;payload.history_archive.selection=null;
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        assert.strictEqual(await archivePage.locator('#lc-archive-panel').isVisible(),false);
        await archivePage.locator('#lc-archive-toggle').click();
        const generationRequest=await archivePage.evaluate(()=>window.__archiveCalls.slice(-1)[0]);
        assert(generationRequest.request_id>retriedArchive.request_id);
        checks.push('History-generation changes discard the archived response/expected request and collapsed selection, preventing old archive data from lingering after the runtime clears its filter');
        const accountChanged=JSON.parse(JSON.stringify(archivePayload));accountChanged.account_context='NA:another-account';
        await archivePage.evaluate(value=>{window.model.payload=JSON.stringify(value);window.__handlers['viewEnv.onDataChanged']();},accountChanged);
        assert.strictEqual(await archivePage.locator('#lc-archive-panel').isVisible(),false);
        await archivePage.locator('#lc-archive-toggle').click();
        const newAccountRequest=await archivePage.evaluate(()=>window.__archiveCalls.slice(-1)[0]);
        assert.strictEqual(newAccountRequest.account_context,'NA:another-account');
        await archivePage.evaluate(()=>{const payload=JSON.parse(window.model.payload);payload.history_archive={ready:false,days:[],selection:null};
            window.model.payload=JSON.stringify(payload);window.__handlers['viewEnv.onDataChanged']();});
        assert((await archivePage.locator('#lc-archive-status').textContent()).includes('sincronizar'));
        assert.strictEqual(await archivePage.locator('#lc-archive-filters').isVisible(),false);
        checks.push('Account changes collapse and discard previous archive selections; unknown server-day catalog remains honest and does not reuse another account or invent a local reset schedule');
        await archivePage.close();
        // Installed ARENA_BONUS_TYPE14/15 are tournament modes, independent of GUI type.
        {
            const tournamentIcon='coui://gui/maps/icons/battleTypes/64x64/specBattlesList.png';
            const tournamentMode={bonus_type:14,gui_type:1,label:'Batalla de torneo',icon:tournamentIcon};
            const clanTournamentMode={bonus_type:15,gui_type:1,label:'Torneo de clanes',icon:tournamentIcon};
            const tournamentRow=Object.assign({},example.history[0],{battle_id:'native-tournament14',
                time_label:'19/10 21:05',vehicles:[pzVehicle],battle_mode:tournamentMode,rewards:[]});
            const clanTournamentRow=Object.assign({},tournamentRow,{battle_id:'native-tournament15',vehicles:[xmVehicle],battle_mode:clanTournamentMode,
                gross_credits:30000,expenses:{repair:10000,ammo:0,consumables:0,other:0},net_credits:20000});
            const futureModeRow=Object.assign({},tournamentRow,{battle_id:'native-unknown999',
                battle_mode:{bonus_type:999,gui_type:14,label:'Modo no identificado (código 999)',icon:null},
                gross_credits:10000,expenses:{repair:0,ammo:0,consumables:0,other:0},net_credits:10000});
            const tournamentSummary=JSON.parse(JSON.stringify(example.summary));
            const clanTournamentSummary=Object.assign({},emptyModeSummary,{battle_count:1,gross_credits:30000,
                expenses:{repair:10000,ammo:0,consumables:0,other:0},net_credits:20000});
            const futureModeSummary=Object.assign({},emptyModeSummary,{battle_count:1,gross_credits:10000,net_credits:10000});
            const tournamentGroup={key:'mode:14',label:tournamentMode.label,icon:tournamentIcon,
                summary:tournamentSummary,history:[tournamentRow],history_total:1,vehicle_groups:[Object.assign({},pzGroup,{summary:tournamentSummary,history_total:1})]};
            const clanTournamentGroup={key:'mode:15',label:clanTournamentMode.label,icon:tournamentIcon,
                summary:clanTournamentSummary,history:[clanTournamentRow],history_total:1,vehicle_groups:[Object.assign({},xmGroup,{summary:clanTournamentSummary,history_total:1})]};
            const futureModeGroup={key:'mode:999',label:futureModeRow.battle_mode.label,icon:null,
                summary:futureModeSummary,history:[futureModeRow],history_total:1,vehicle_groups:[]};
            const tournamentPayload=JSON.parse(JSON.stringify(example));
            tournamentPayload.account_context='NA:qa-tournament14';tournamentPayload.language='es';
            tournamentPayload.history=[tournamentRow,clanTournamentRow,futureModeRow];
            tournamentPayload.mode_groups=[tournamentGroup,clanTournamentGroup,futureModeGroup];
            tournamentPayload.vehicle_groups=[pzGroup,xmGroup];tournamentPayload.vehicle_selection=null;
            tournamentPayload.summary={battle_count:3,gross_credits:96028,
                expenses:{repair:43136,ammo:106400,consumables:30000,other:0},net_credits:-83508,pending_battles:0};
            tournamentPayload.history_archive={ready:true,selection:null,days:[{key:'2026-10-18T10:00:00Z',label:'18/10/2026',
                battle_count:3,net_credits:-83508,summary:tournamentPayload.summary,history_total:3,external_credits:0}]};
            const tournamentPage=await context.newPage();tournamentPage.on('pageerror',error=>errors.push(String(error)));
            await tournamentPage.setViewportSize({width:1100,height:1050});await tournamentPage.evaluate(installQaArt);
            await tournamentPage.evaluate(nativeBootstrap,tournamentPayload);
            await tournamentPage.evaluate(()=>{
                window.isDomBuilt=true;window.__nativeReady=true;window.__tournamentArchiveCalls=[];window.__tournamentMutations=[];
                window.model.onSelectHistoryDay=function(args){window.__tournamentArchiveCalls.push(args);};
                for(const name of ['onSaveGoal','onResetGoal','onResetHistory','onSaveHistory','onRefresh']){
                    window.model[name]=function(args){window.__tournamentMutations.push([name,args]);};
                }
                window.model.onSetLanguage=function(args){
                    const payload=JSON.parse(window.model.payload);payload.language=args.language;
                    payload.language_selection={request_id:String(args.request_id),requested_language:args.language,language:args.language,available:true,error:null};
                    window.model.payload=JSON.stringify(payload);window.setTimeout(function(){window.__handlers['viewEnv.onDataChanged']();},0);
                };
            });
            await tournamentPage.setContent(gamefaceHtml);await tournamentPage.addScriptTag({content:fs.readFileSync(path.join(ui,'ledger.js'),'utf8')});
            await tournamentPage.waitForFunction(()=>window.__nativeSize.width===1040&&window.__nativeSize.height===976);
            const tournamentFinanceBefore=await tournamentPage.evaluate(()=>{const p=JSON.parse(window.model.payload);
                return {balance:p.balance,goal:p.goal,wallet:p.wallet,summary:p.summary,history:p.history};});
            await tournamentPage.locator('#lc-mode-toggle').click();
            assert.strictEqual(await tournamentPage.locator('[data-mode-key="mode:14"] .lc-filter-option-label').textContent(),'Batalla de torneo');
            assert.strictEqual(await tournamentPage.locator('[data-mode-key="mode:14"] img').getAttribute('data-native-src'),tournamentIcon);
            await tournamentPage.locator('[data-mode-key="mode:14"]').click();
            assert.strictEqual(await tournamentPage.locator('#lc-mode-label').textContent(),'Batalla de torneo');
            assert.strictEqual(await tournamentPage.locator('#lc-gross').textContent(),'+56.028');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-net').textContent(),'-113.508');
            await tournamentPage.locator('#lc-history-toggle').click();
            assert((await tournamentPage.locator('#lc-history-list .lc-history-stamp').first().textContent()).includes('Batalla de torneo'));
            assert.strictEqual(await tournamentPage.locator('#lc-history-list .lc-history-stamp img').first().getAttribute('data-native-src'),tournamentIcon);
            await tournamentPage.locator('#lc-history-list .lc-history-battle').first().click();
            assert.strictEqual(await tournamentPage.locator('#lc-detail-mode').textContent(),'Modo de juego: Batalla de torneo');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-mode img').getAttribute('data-native-src'),tournamentIcon);
            assert.strictEqual(await tournamentPage.locator('#lc-detail-vehicles .lc-tank-name').textContent(),'Pz. Neu');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-vehicles .lc-tank-tier').textContent(),'Nivel XI');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-vehicles img').getAttribute('data-native-src'),pzVehicle.icon);
            await tournamentPage.locator('.lc-battle-panel').scrollIntoViewIfNeeded();
            await tournamentPage.locator('#lc-window').screenshot({path:path.join(__dirname,'tournament-mode-es-preview.png')});
            checks.push('Native bonus14 displays Batalla de torneo with the actual special-battle family logo in the live mode filter, history stamp and selected battle, preserving known gross/net values and the Pz.Neu image with tierXI');

            await tournamentPage.locator('#lc-language-en').click();
            assert.strictEqual(await tournamentPage.locator('#lc-mode-label').textContent(),'Tournament Battle');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-mode').textContent(),'Game mode: Tournament Battle');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-vehicles .lc-tank-tier').textContent(),'Tier XI');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-net').textContent(),'-113,508');
            assert((await tournamentPage.locator('#lc-history-label').textContent()).includes('Pz. Neu'));
            assert.strictEqual(await tournamentPage.locator('#lc-detail-mode img').getAttribute('data-native-src'),tournamentIcon);
            await tournamentPage.locator('#lc-window').screenshot({path:path.join(__dirname,'tournament-mode-en-preview.png')});
            await chooseFilter(tournamentPage,'mode:15');
            assert.strictEqual(await tournamentPage.locator('#lc-mode-label').textContent(),'Clan Tournament');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-net').textContent(),'+20,000');
            await tournamentPage.locator('#lc-history-toggle').click();await tournamentPage.locator('#lc-history-list .lc-history-battle').first().click();
            assert.strictEqual(await tournamentPage.locator('#lc-detail-mode').textContent(),'Game mode: Clan Tournament');
            await tournamentPage.locator('#lc-language-es').click();
            assert.strictEqual(await tournamentPage.locator('#lc-mode-label').textContent(),'Torneo de clanes');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-mode').textContent(),'Modo de juego: Torneo de clanes');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-net').textContent(),'+20.000');
            checks.push('Tournament bonus14 and clan tournament bonus15 switch immediately between Spanish and English without restarting, refetching or losing the selected battle, native logo, vehicle tier or signed financial results');

            await tournamentPage.locator('#lc-archive-toggle').click();
            async function tournamentArchiveResponse(request){
                const selected=request.mode_key==='mode:14'?tournamentGroup:request.mode_key==='mode:15'?clanTournamentGroup:null;
                await tournamentPage.evaluate(value=>{const p=JSON.parse(window.model.payload);p.history_archive.selection=value;
                    window.model.payload=JSON.stringify(p);window.__handlers['viewEnv.onDataChanged']();},
                    {day_key:request.day_key,label:'18/10/2026',mode_key:request.mode_key,vehicle_key:'all',request_id:String(request.request_id),
                        account_context:request.account_context,available:true,summary:selected?selected.summary:tournamentPayload.summary,
                        history:selected?selected.history:tournamentPayload.history,history_total:selected?1:3,
                        mode_groups:[tournamentGroup,clanTournamentGroup,futureModeGroup],vehicle_groups:[pzGroup,xmGroup],external_credits:0});
            }
            await tournamentArchiveResponse(await tournamentPage.evaluate(()=>window.__tournamentArchiveCalls.slice(-1)[0]));
            await tournamentPage.locator('#lc-archive-mode-toggle').click();
            assert.strictEqual(await tournamentPage.locator('[data-archive-mode="mode:14"] .lc-filter-option-label').textContent(),'Batalla de torneo');
            assert.strictEqual(await tournamentPage.locator('[data-archive-mode="mode:14"] img').getAttribute('data-native-src'),tournamentIcon);
            await tournamentPage.locator('[data-archive-mode="mode:14"]').click();
            const tournamentArchiveRequest=await tournamentPage.evaluate(()=>window.__tournamentArchiveCalls.slice(-1)[0]);
            assert.strictEqual(tournamentArchiveRequest.mode_key,'mode:14');await tournamentArchiveResponse(tournamentArchiveRequest);
            await tournamentPage.locator('#lc-archive-battle-list .lc-history-battle').first().click();
            assert((await tournamentPage.locator('#lc-archive-detail-title').textContent()).includes('Batalla de torneo'));
            assert((await tournamentPage.locator('#lc-archive-detail-title').textContent()).includes('Nivel XI'));
            assert.strictEqual(await tournamentPage.locator('#lc-archive-battle-list .lc-history-stamp img').first().getAttribute('data-native-src'),tournamentIcon);
            assert.strictEqual(await tournamentPage.locator('#lc-archive-battle-list .lc-tank-art img').first().getAttribute('data-native-src'),pzVehicle.icon);
            assert.strictEqual(await tournamentPage.locator('#lc-archive-gross').textContent(),'+56.028');
            assert.strictEqual(await tournamentPage.locator('#lc-archive-net').textContent(),'-113.508');
            const tournamentArchiveCallsBefore=await tournamentPage.evaluate(()=>window.__tournamentArchiveCalls.length);
            await tournamentPage.locator('#lc-language-en').click();
            assert.strictEqual(await tournamentPage.locator('#lc-archive-mode-label').textContent(),'Tournament Battle');
            assert((await tournamentPage.locator('#lc-archive-detail-title').textContent()).includes('Tournament Battle'));
            assert((await tournamentPage.locator('#lc-archive-detail-title').textContent()).includes('Tier XI'));
            assert.strictEqual(await tournamentPage.locator('#lc-archive-net').textContent(),'-113,508');
            assert.strictEqual(await tournamentPage.evaluate(()=>window.__tournamentArchiveCalls.length),tournamentArchiveCallsBefore);
            await tournamentPage.locator('#lc-archive-battles').scrollIntoViewIfNeeded();
            await tournamentPage.locator('#lc-window').screenshot({path:path.join(__dirname,'tournament-history-preview.png')});
            checks.push('Daily archived tournament battles use the same bilingual mode filter and native logo/image/tier, send exactmode14 archive requests and preserve selected historical financial values across a live language change without fetching again');

            await tournamentPage.locator('#lc-language-es').click();await chooseFilter(tournamentPage,'mode:999');
            assert.strictEqual(await tournamentPage.locator('#lc-mode-label').textContent(),'Modo no identificado (código 999)');
            assert.strictEqual(await tournamentPage.locator('#lc-mode-icon img').count(),0);
            await tournamentPage.locator('#lc-history-toggle').click();await tournamentPage.locator('#lc-history-list .lc-history-battle').first().click();
            assert.strictEqual(await tournamentPage.locator('#lc-detail-mode').textContent(),'Modo de juego: Modo no identificado (código 999)');
            assert.strictEqual(await tournamentPage.locator('#lc-detail-mode img').count(),0);
            assert.strictEqual(await tournamentPage.locator('#lc-detail-net').textContent(),'+10.000');
            assert.deepStrictEqual(await tournamentPage.evaluate(()=>{const p=JSON.parse(window.model.payload);
                return {balance:p.balance,goal:p.goal,wallet:p.wallet,summary:p.summary,history:p.history};}),tournamentFinanceBefore);
            assert.deepStrictEqual(await tournamentPage.evaluate(()=>window.__tournamentMutations),[]);
            checks.push('A genuinely unknown native bonus999 stays unidentified with no borrowed tournament icon even when gui_type is14; correcting tournament labels changes no stored battle money, wallet, balance, goal or history');
            await tournamentPage.close();
        }
        await require('./verify-bilingual.cjs')({context,gamefaceHtml,nativeBootstrap,installQaArt,checks,errors,
            example,vehiclePayload,xmGroup,pzGroup,modeXmGroup,archiveModes,archivePayload,skirmishRow,modeIcons,
            chooseVehicle,chooseFilter,vehicleResponse,assertSignColor});
        await require('./verify-eight-point.cjs')({context,gamefaceHtml,nativeBootstrap,installQaArt,checks,example});
        await require('./verify-progress-circle.cjs')({context,gamefaceHtml,nativeBootstrap,checks,errors,example});
        await require('./verify-celebration.cjs')({context,gamefaceHtml,nativeBootstrap,installQaArt,checks,errors,example});
        assert.strictEqual(errors.length, 0, errors.join('\n'));
        checks.push('Native observers removed on unload, no page errors');
        fs.writeFileSync(path.join(__dirname, 'qa-report.json'), JSON.stringify({passed: checks.length, checks, pageErrors: errors}, null, 2));
        process.stdout.write(JSON.stringify({passed: checks.length, checks, pageErrors: errors}, null, 2) + '\n');
    } finally {
        await context.close();
    }
}()).catch(function (error) { process.stderr.write(String(error.stack || error) + '\n'); process.exitCode = 1; });
