/* Headless goal-completion integration QA. Never loaded by World of Tanks. */
const fs=require('fs'),path=require('path'),assert=require('assert');
module.exports=async function qaCelebration(env){
    const {context,gamefaceHtml,nativeBootstrap,installQaArt,checks,errors,example}=env;
    const source=fs.readFileSync(path.join(__dirname,'..','ledger.js'),'utf8');
    const ACCOUNT='NA:123',ES='¡Meta alcanzada! ¡Buen trabajo!',EN='Goal reached! Well done!';
    const clone=value=>JSON.parse(JSON.stringify(value));
    function fixture(mode='widget',language='es'){
        const p=clone(example);p.account_context=ACCOUNT;p.view_mode=mode;p.language=language;
        p.completion_display={ready:true,generation:7,account_context:ACCOUNT};
        p.balance=22900000;p.goal=Object.assign({},p.goal,{active:true,target:1000000,baseline:22000000,
            final_balance:23000000,current:900000,remaining:100000,progress_percent:90,complete:false,reset_generation:0});
        p.goal_completion=null;return p;
    }
    function completion(number=1,target=1000000,generation=0){return {id:'00000000000040008000'+String(number).padStart(12,'0'),
        account_context:ACCOUNT,target,reset_generation:generation};}
    async function createSurface(payload,options={}){
        const surface=await context.newPage();surface.on('pageerror',e=>errors.push(String(e)));
        await surface.setViewportSize(options.viewport||{width:1100,height:1050});
        await surface.emulateMedia({reducedMotion:options.reducedMotion?'reduce':'no-preference'});
        await surface.evaluate(installQaArt);await surface.evaluate(nativeBootstrap,clone(payload));
        await surface.evaluate(options=>{
            window.isDomBuilt=true;window.__nativeReady=!options.nativePending;window.__acks=[];window.__mutations=[];window.__moves=[];
            window.__languageCalls=[];window.__celebrationTimers=[];window.__completionDelays=[];
            window.model.onAcknowledgeGoalCompletion=function(args){window.__acks.push(args);if(options.failAck){throw new Error('Fixture acknowledgement write failure');}const current=JSON.parse(window.model.payload);
                if(options.rejectFirstAckGeneration&&window.__acks.length===1){current.completion_display={ready:false,generation:8,account_context:current.account_context};}
                else{current.goal_completion=null;}
                window.model.payload=JSON.stringify(current);window.setTimeout(function(){if(window.__handlers['viewEnv.onDataChanged']){window.__handlers['viewEnv.onDataChanged']();}},0);};
            window.model.onSetLanguage=function(args){window.__languageCalls.push(args);const current=JSON.parse(window.model.payload);current.language=args.language;current.language_selection={request_id:args.request_id,requested_language:args.language,language:args.language,available:true,error:null};window.model.payload=JSON.stringify(current);window.setTimeout(function(){if(window.__handlers['viewEnv.onDataChanged']){window.__handlers['viewEnv.onDataChanged']();}},0);};
            window.viewEnv.handleViewEvent=function(args){window.__moves.push(args);};
            window.viewEnv.setTrackMouseOnStage=function(){};window.viewEnv.setEventHandled=function(){};
            for(const name of ['onSaveGoal','onResetGoal','onResetHistory','onSaveHistory','onRefresh']){
                window.model[name]=function(args){window.__mutations.push([name,args]);};
            }
            if(options.clientWidth){window.viewEnv.getClientSizePx=function(){return {width:options.clientWidth,height:1000};};}
            const schedule=window.setTimeout.bind(window),cancel=window.clearTimeout.bind(window),nativeNow=Date.now.bind(Date);
            let elapsed=0,nextId=-1;const epoch=nativeNow();
            if(!options.realTimers){Date.now=function(){return epoch+elapsed;};}
            window.__cancelRealTimeout=cancel;
            window.setTimeout=function(fn,delay){
                if(delay!==2800&&delay!==1500&&delay!==1000&&delay!==200){return schedule(fn,delay);}
                const timer={delay,due:elapsed+delay,fired:false,cancelled:false,fn};
                timer.id=options.realTimers?schedule(function(){timer.fired=true;fn();},delay):nextId--;
                window.__completionDelays.push(timer);if(delay===2800){window.__celebrationTimers.push(timer);}return timer.id;
            };
            window.clearTimeout=function(id){window.__completionDelays.forEach(t=>{if(t.id===id&&!t.fired){t.cancelled=true;}});if(id>=0){return cancel(id);}};
            window.__advanceCompletion=function(ms){
                const target=elapsed+ms;let calls=0;
                while(true){
                    const due=window.__completionDelays.filter(t=>!t.cancelled&&!t.fired&&t.due<=target).sort((a,b)=>a.due-b.due)[0];
                    if(!due){break;}if(++calls>25){throw new Error('Unbounded completion timer loop');}
                    elapsed=due.due;due.fired=true;due.fn();
                }
                elapsed=target;
            };
            window.__finishCelebration=function(){
                const active=window.__celebrationTimers.filter(t=>!t.cancelled&&!t.fired);
                if(active.length){window.__advanceCompletion(Math.max(...active.map(t=>t.due))-elapsed);}
            };
        },options);
        await surface.setContent(gamefaceHtml);await surface.addScriptTag({content:source});
        if(!options.nativePending){await surface.waitForFunction(()=>window.__nativeSize.width!==256);}
        return surface;
    }
    async function update(surface,patch){await surface.evaluate(patch=>{
        const p=JSON.parse(window.model.payload);Object.assign(p,patch);window.model.payload=JSON.stringify(p);
        window.__handlers['viewEnv.onDataChanged']();
    },patch);}
    async function advance(surface,ms){await surface.evaluate(ms=>window.__advanceCompletion(ms),ms);}
    async function achieve(surface,event=completion(),settle=true){
        await surface.evaluate(event=>{
            const p=JSON.parse(window.model.payload);p.balance=p.goal.baseline+event.target;
            p.goal=Object.assign({},p.goal,{active:true,target:event.target,current:event.target,remaining:0,progress_percent:100,
                final_balance:p.balance,complete:true,reset_generation:event.reset_generation});
            p.goal_completion=event;window.model.payload=JSON.stringify(p);window.__handlers['viewEnv.onDataChanged']();
        },event);
        if(settle){await advance(surface,1500);}
    }
    async function counts(surface){return surface.evaluate(()=>({acks:window.__acks.length,timers:window.__celebrationTimers.length,
        active:window.__celebrationTimers.filter(t=>!t.fired&&!t.cancelled).length}));}
    async function finish(surface){await surface.evaluate(()=>window.__finishCelebration());}
    async function noCelebration(surface){
        assert.strictEqual(await surface.locator('#lc-widget').evaluate(n=>n.classList.contains('lc-widget-celebrating')),false);
        assert.strictEqual(await surface.locator('.lc-goal-celebrating').count(),0);
    }
    async function assertWidgetBounds(surface,width){
        const bounds=await surface.evaluate(()=>{
            const outer=document.getElementById('lc-window').getBoundingClientRect();
            const ids=['lc-widget-status','lc-widget-progress','lc-widget-percent','lc-widget-details','lc-widget-close','lc-widget-chart'];
            const nodes=ids.map(id=>{const n=document.getElementById(id),r=n.getBoundingClientRect();
                const range=document.createRange();range.selectNodeContents(n);const text=range.getBoundingClientRect();
                return {id,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,
                    textLeft:text.left,textRight:text.right,textTop:text.top,textBottom:text.bottom};});
            return {outer:{width:outer.width,height:outer.height,left:outer.left,right:outer.right,top:outer.top,bottom:outer.bottom},nodes};
        });
        assert.strictEqual(bounds.outer.width,width);assert.strictEqual(bounds.outer.height,width<480?232:208);
        for(const n of bounds.nodes){assert(n.width>0&&n.height>0,n.id+' must remain visible');
            assert(n.left>=bounds.outer.left-1&&n.right<=bounds.outer.right+1&&n.top>=bounds.outer.top-1&&n.bottom<=bounds.outer.bottom+1,n.id+' must fit the widget');
            assert(n.textRight<=n.right+1&&n.textLeft>=n.left-1&&n.textBottom<=bounds.outer.bottom+1&&n.textTop>=bounds.outer.top-1,n.id+' text must not clip: '+JSON.stringify(n));}
    }
    // Backend only publishes an event for a new attainment: percentages alone never create one.
    const quiet=await createSurface(fixture());
    for(const patch of [
        {goal:Object.assign({},fixture().goal,{complete:true,current:1000000,remaining:0,progress_percent:100})},
        {goal:Object.assign({},fixture().goal,{target:0,active:false,complete:false,current:1000000,remaining:0,progress_percent:0})},
        {ready:false,balance:null,goal:Object.assign({},fixture().goal,{current:null,remaining:null,complete:false})},
        {ready:true,balance:22900000,goal:fixture().goal}
    ]){await update(quiet,patch);await noCelebration(quiet);}
    assert.deepStrictEqual(await counts(quiet),{acks:0,timers:0,active:0});
    checks.push('Goal percentages alone never trigger congratulations: an initially complete goal, disabled zero target, unknown balance and incomplete goal remain quiet without native acknowledgements or timers');
    await quiet.close();

    const widget=await createSurface(fixture());
    await achieve(widget);
    assert.strictEqual(await widget.locator('#lc-widget-status').textContent(),ES);
    assert.strictEqual(await widget.locator('#lc-widget-status').evaluate(n=>getComputedStyle(n).color),'rgb(141, 211, 106)');
    assert.strictEqual(await widget.locator('#lc-widget').evaluate(n=>n.classList.contains('lc-widget-celebrating')),true);
    assert.deepStrictEqual(await widget.evaluate(()=>window.__acks),[]);
    assert.deepStrictEqual(await counts(widget),{acks:0,timers:1,active:1});
    assert.strictEqual(await widget.locator('#lc-widget-percent').textContent(),'100,0 %');
    assert.strictEqual(await widget.locator('#lc-widget-progress').textContent(),'1.000.000 / 1.000.000 créditos');
    await assertWidgetBounds(widget,624);
    await widget.waitForTimeout(180);await widget.locator('#lc-window').screenshot({path:path.join(__dirname,'celebration-es-preview.png')});
    checks.push('A new confirmed attainment shows green Spanish congratulations in the existing624x208 widget after a stable visible garage, retains actual100-percent progress and earned/target credits, and stays unacknowledged until the full effect finishes');
    const particles=await widget.locator('#lc-celebration-sparks').evaluate(layer=>{
        const style=getComputedStyle(layer),r=layer.getBoundingClientRect(),parent=layer.parentNode.getBoundingClientRect();
        return {pointer:style.pointerEvents,hidden:layer.getAttribute('aria-hidden'),width:r.width,height:r.height,
            clipped:style.overflow,
            bounds:r.left>=parent.left&&r.right<=parent.right&&r.top>=parent.top&&r.bottom<=parent.bottom,
            particles:Array.from(layer.querySelectorAll('.lc-spark')).map(n=>({pointer:getComputedStyle(n).pointerEvents,
                duration:getComputedStyle(n).animationDuration,iterations:getComputedStyle(n).animationIterationCount}))};
    });
    assert.strictEqual(particles.pointer,'none');assert.strictEqual(particles.hidden,'true');
    assert(particles.bounds&&particles.width>0&&particles.height>0);assert.strictEqual(particles.clipped,'hidden');
    assert(particles.particles.length>0&&particles.particles.length<=24);
    particles.particles.forEach(p=>{assert.strictEqual(p.pointer,'none');assert(!p.iterations.includes('infinite'));assert(parseFloat(p.duration)<=1.5);});
    await widget.locator('#lc-widget-drag-bar').dispatchEvent('mousedown',{button:0,clientX:30,clientY:20});
    await widget.locator('#lc-widget-drag-bar').dispatchEvent('mouseup',{button:0});
    assert.deepStrictEqual(await widget.evaluate(()=>window.__moves.map(x=>x.on)),[true,false]);
    assert.strictEqual(await widget.locator('#credit-ledger-view').evaluate(n=>getComputedStyle(n).pointerEvents),'none');
    assert.strictEqual(await widget.locator('#lc-window').getAttribute('aria-modal'),'false');
    assert.deepStrictEqual(await widget.evaluate(()=>window.__mutations),[]);
    checks.push('Small finite spark bursts stay clipped inside the widget with at most24 decorative particles, no pointer capture or modal layer; native drag remains usable and the effect performs no finance/history/goal mutations');
    for(let i=0;i<3;i++){await update(widget,{message:'Datos de tu cuenta actual'});}
    assert.deepStrictEqual(await counts(widget),{acks:0,timers:1,active:1});
    await widget.locator('#lc-language-en').dispatchEvent('click');
    assert.strictEqual(await widget.locator('#lc-widget-status').textContent(),EN);await assertWidgetBounds(widget,624);
    assert.deepStrictEqual(await counts(widget),{acks:0,timers:1,active:1});
    await widget.locator('#lc-window').screenshot({path:path.join(__dirname,'celebration-en-preview.png')});
    await finish(widget);
    assert.deepStrictEqual(await widget.evaluate(()=>window.__acks),[{id:completion().id,account_context:ACCOUNT,presentation_generation:7}]);
    await noCelebration(widget);
    assert.strictEqual(await widget.locator('#lc-widget-status').textContent(),'Goal reached.');await assertWidgetBounds(widget,624);
    await update(widget,{goal_completion:completion()});await noCelebration(widget);
    assert.deepStrictEqual(await counts(widget),{acks:1,timers:1,active:0});
    await widget.locator('#lc-window').screenshot({path:path.join(__dirname,'celebration-restored-preview.png')});
    checks.push('Repeated payloads and a live Spanish/English language change reuse one2800ms celebration instead of restarting it; normal goal status returns afterward and the same attainment cannot replay');
    await widget.close();

    const narrow=await createSurface(fixture('widget','en'),{viewport:{width:450,height:1000},clientWidth:434});
    await narrow.waitForFunction(()=>window.__nativeSize.width===402);
    await achieve(narrow,completion(2));await assertWidgetBounds(narrow,402);
    await narrow.locator('#lc-window').screenshot({path:path.join(__dirname,'celebration-narrow-preview.png')});
    await finish(narrow);await noCelebration(narrow);
    await achieve(narrow,completion(200,999999999999999));await assertWidgetBounds(narrow,402);
    assert((await narrow.locator('#lc-widget-progress').textContent()).includes('999,999,999,999,999'));
    await finish(narrow);await noCelebration(narrow);await narrow.close();
    checks.push('English congratulations, earned credits, percentage, action buttons and progress scale remain legible and separated inside the native402px narrow widget without resizing or clipping');

    const details=await createSurface(fixture('details'));
    await details.locator('#lc-target').fill('2.500.000');
    await details.evaluate(()=>{const n=document.getElementById('lc-target');n.focus();n.setSelectionRange(5,5);});
    const detailsBefore=await details.evaluate(()=>({draft:document.getElementById('lc-target').value,caret:document.getElementById('lc-target').selectionStart,mode:JSON.parse(window.model.payload).view_mode}));
    await achieve(details,completion(3));
    assert.strictEqual(await details.locator('#lc-remaining').textContent(),ES);
    assert.strictEqual(await details.locator('.lc-goal-celebrating').count(),1);
    assert.strictEqual(await details.locator('#lc-widget').isVisible(),false);
    assert.deepStrictEqual(await details.evaluate(()=>({draft:document.getElementById('lc-target').value,caret:document.getElementById('lc-target').selectionStart,mode:JSON.parse(window.model.payload).view_mode})),detailsBefore);
    assert.strictEqual(await details.locator('#lc-window').getAttribute('aria-modal'),'false');
    const timersBefore=await counts(details);
    await details.locator('#lc-language-en').click();
    assert.strictEqual(await details.locator('#lc-remaining').textContent(),EN);
    assert.deepStrictEqual(await counts(details),timersBefore);
    await finish(details);await noCelebration(details);
    assert.strictEqual(await details.locator('#lc-remaining').textContent(),'Goal reached.');
    await details.close();
    checks.push('A goal completed while View details is open receives the same brief bilingual inline congratulations without forcing the widget, resizing, moving focus/caret or replacing an unsaved goal draft');

    const minimized=await createSurface(fixture('minimized'));
    await achieve(minimized,completion(4));await noCelebration(minimized);
    assert.deepStrictEqual(await counts(minimized),{acks:0,timers:0,active:0});
    assert.strictEqual(await minimized.locator('#lc-minimized-restore').isVisible(),true);
    await minimized.locator('#lc-minimized-restore').click();
    await advance(minimized,1500);
    await minimized.waitForFunction(()=>document.getElementById('lc-widget-status').textContent.includes('¡Buen trabajo!'));
    assert.deepStrictEqual(await counts(minimized),{acks:0,timers:1,active:1});
    await minimized.locator('#lc-widget-close').click();await noCelebration(minimized);
    assert.deepStrictEqual(await counts(minimized),{acks:0,timers:1,active:0});
    await minimized.locator('#lc-minimized-restore').click();await advance(minimized,1500);
    assert.deepStrictEqual(await counts(minimized),{acks:0,timers:2,active:1});
    await finish(minimized);await noCelebration(minimized);
    assert.deepStrictEqual(await counts(minimized),{acks:1,timers:2,active:0});
    await minimized.close();
    checks.push('A minimized widget retains a pending attainment without auto-expanding or acknowledging unseen feedback; minimizing an incomplete presentation preserves its event and restoring gives the full effect before acknowledging once');

    for(const kind of ['disabled','goal-reset','history-reset','account','unknown']){
        const surface=await createSurface(fixture());await achieve(surface,completion(10));
        const p=await surface.evaluate(()=>JSON.parse(window.model.payload));
        let patch={};
        if(kind==='disabled')patch={goal:Object.assign({},p.goal,{target:0,active:false}),goal_completion:null};
        if(kind==='goal-reset')patch={goal:Object.assign({},p.goal,{reset_generation:1,current:0,remaining:p.goal.target,complete:false}),goal_completion:null};
        if(kind==='history-reset')patch={history_control:Object.assign({},p.history_control,{generation:1}),goal:Object.assign({},p.goal,{target:0,active:false}),goal_completion:null};
        if(kind==='account')patch={account_context:'NA:456',goal_completion:null};
        if(kind==='unknown')patch={ready:false,balance:null,goal_completion:null};
        await update(surface,patch);await noCelebration(surface);
        assert.strictEqual((await counts(surface)).active,0,'Active timer cancelled on '+kind);
        await surface.close();
    }
    checks.push('Deactivating the goal, resetting its base, resetting history, switching accounts or losing ready balance data immediately clears the transient celebration and cancels its timer');

    const invalidPayload=fixture();invalidPayload.balance=23000000;invalidPayload.goal=Object.assign({},invalidPayload.goal,{current:1000000,remaining:0,progress_percent:100,complete:true});
    const invalid=await createSurface(invalidPayload);
    for(const event of [Object.assign({},completion(20),{account_context:'NA:other'}),Object.assign({},completion(21),{target:0}),
        Object.assign({},completion(22),{target:2000000}),Object.assign({},completion(23),{reset_generation:99})]){
        await update(invalid,{goal_completion:event});await noCelebration(invalid);
    }
    assert.deepStrictEqual(await counts(invalid),{acks:0,timers:0,active:0});
    await invalid.close();
    checks.push('Stale account, zero or mismatched target, and stale goal-generation notifications cannot start or acknowledge a celebration');

    const reduced=await createSurface(fixture('widget','en'),{reducedMotion:true});
    await achieve(reduced,completion(30));
    assert.strictEqual(await reduced.locator('#lc-widget-status').textContent(),EN);
    assert.strictEqual(await reduced.locator('#lc-celebration-sparks').isVisible(),false);
    assert.deepStrictEqual(await counts(reduced),{acks:0,timers:1,active:1});
    await finish(reduced);await noCelebration(reduced);await reduced.close();
    checks.push('Reduced-motion preference receives the same brief green success text with no animated spark layer and normal bounded restoration');

    const deferred=await createSurface(fixture('details'));
    await deferred.locator('#lc-content').evaluate(n=>{n.scrollTop=n.scrollHeight;n.dispatchEvent(new Event('scroll'));});
    const deferredScroll=await deferred.locator('#lc-content').evaluate(n=>n.scrollTop);
    await achieve(deferred,completion(31));await noCelebration(deferred);
    assert.deepStrictEqual(await counts(deferred),{acks:0,timers:0,active:0});
    assert.strictEqual(await deferred.locator('#lc-content').evaluate(n=>n.scrollTop),deferredScroll,'Do not force-scroll a hidden goal into sight');
    await deferred.locator('#lc-content').evaluate(n=>{n.scrollTop=0;n.dispatchEvent(new Event('scroll'));});
    await advance(deferred,1500);
    await deferred.waitForFunction(()=>document.getElementById('lc-remaining').textContent.includes('¡Buen trabajo!'));
    assert.deepStrictEqual(await counts(deferred),{acks:0,timers:1,active:1});await finish(deferred);await deferred.close();
    const nativePending=await createSurface(fixture(),{nativePending:true});
    await achieve(nativePending,completion(32));await noCelebration(nativePending);
    assert.deepStrictEqual(await counts(nativePending),{acks:0,timers:0,active:0});
    await nativePending.evaluate(()=>{
        window.viewEnv.resizeViewPx=function(w,h){if(window.__nativeReady){window.__nativeSize={width:w,height:h};}};
        const p=JSON.parse(window.model.payload);p.window={ready:true,width:624,height:208};
        window.model.payload=JSON.stringify(p);window.__handlers['viewEnv.onDataChanged']();
        const changed=window.__handlers['viewEnv.onDataChanged'];window.__lateFinanceEmits=0;
        window.__handlers['viewEnv.onDataChanged']=function(){window.__lateFinanceEmits+=1;changed();};
        window.__nativeReady=true;window.__handlers['self.onTextureReady']();
    });
    await nativePending.waitForFunction(()=>window.__nativeSize.width===624);
    await advance(nativePending,1500);
    await nativePending.waitForFunction(()=>document.getElementById('lc-widget-status').textContent.includes('¡Buen trabajo!'));
    assert.strictEqual(await nativePending.evaluate(()=>window.__lateFinanceEmits),0,'Native texture/bounds verification must start the grace without another finance/model emit');
    assert.deepStrictEqual(await counts(nativePending),{acks:0,timers:1,active:1});await finish(nativePending);await nativePending.close();
    checks.push('A goal out of sight in scrolled details or awaiting the actual native surface keeps its notification pending without forcing scroll or view changes; feedback starts once the goal is genuinely visible');

    const failedAck=await createSurface(fixture(),{failAck:true});await achieve(failedAck,completion(33));
    assert.deepStrictEqual(await counts(failedAck),{acks:0,timers:1,active:1});
    await finish(failedAck);await advance(failedAck,1000);
    assert.deepStrictEqual(await counts(failedAck),{acks:2,timers:1,active:0});
    await advance(failedAck,1000);
    assert.deepStrictEqual(await counts(failedAck),{acks:2,timers:1,active:0});
    assert.strictEqual(await failedAck.locator('#lc-backend-error').textContent(),'');
    assert.strictEqual(await failedAck.evaluate(()=>JSON.parse(window.model.payload).error),null);
    await finish(failedAck);await update(failedAck,{goal_completion:completion(33)});await noCelebration(failedAck);
    assert.deepStrictEqual(await counts(failedAck),{acks:2,timers:1,active:0});await failedAck.close();
    checks.push('Only after full visible presentation, a failed acknowledgement has one bounded retry at1000ms, never restarts the effect or overwrites finance errors, and a stillpending event cannot replay in the same view');
    const disposed=await createSurface(fixture());await achieve(disposed,completion(40));
    await disposed.evaluate(()=>window.dispatchEvent(new Event('unload')));
    assert.strictEqual((await counts(disposed)).active,0);await noCelebration(disposed);
    assert.strictEqual(await disposed.evaluate(()=>typeof window.__handlers['viewEnv.onDataChanged']),'undefined');
    await disposed.close();
    checks.push('Leaving or unloading the native view cancels an active celebration timer, clears the effect and removes model callbacks so no animation persists outside the garage view');

    // Regression: battle rewards can arrive while the lobby exists under its loading screen.
    const loadingPayload=fixture();loadingPayload.completion_display={ready:false,generation:7,account_context:ACCOUNT};
    const loading=await createSurface(loadingPayload);await achieve(loading,completion(60),false);
    for(const display of [null,{ready:false,generation:7,account_context:ACCOUNT},{ready:true,generation:7,account_context:'NA:other'}]){
        await update(loading,{completion_display:display});await advance(loading,6000);await noCelebration(loading);
        assert.deepStrictEqual(await counts(loading),{acks:0,timers:0,active:0});
        assert.strictEqual(await loading.evaluate(()=>JSON.parse(window.model.payload).goal_completion.id),completion(60).id);
    }
    await update(loading,{completion_display:{ready:true,generation:8,account_context:ACCOUNT}});
    await advance(loading,1499);await noCelebration(loading);
    for(let i=0;i<3;i++){await update(loading,{message:'Datos de tu cuenta actual'});}
    await advance(loading,1);
    assert.deepStrictEqual(await counts(loading),{acks:0,timers:1,active:1});
    await advance(loading,2799);assert.strictEqual(await loading.locator('#lc-widget-status').textContent(),ES);
    assert.strictEqual(await loading.evaluate(()=>window.__acks.length),0);
    await advance(loading,1);await noCelebration(loading);
    assert.deepStrictEqual(await loading.evaluate(()=>window.__acks),[{id:completion(60).id,account_context:ACCOUNT,presentation_generation:8}]);
    await loading.close();
    checks.push('Post-battle rewards arriving under a loading lobby remain durable: missing, false or foreign garage visibility cannot start or acknowledge them; a stable visible garage waits1500ms and presents the full2800ms before its sole acknowledgement');

    const flapping=await createSurface(fixture());await achieve(flapping,completion(61),false);await advance(flapping,1000);
    await update(flapping,{completion_display:{ready:false,generation:8,account_context:ACCOUNT}});await advance(flapping,5000);
    await noCelebration(flapping);assert.deepStrictEqual(await counts(flapping),{acks:0,timers:0,active:0});
    await update(flapping,{completion_display:{ready:true,generation:9,account_context:ACCOUNT}});await advance(flapping,1499);
    await update(flapping,{completion_display:{ready:true,generation:10,account_context:ACCOUNT}});await advance(flapping,1);await noCelebration(flapping);
    await advance(flapping,1499);assert.deepStrictEqual(await counts(flapping),{acks:0,timers:1,active:1});
    await advance(flapping,1000);await update(flapping,{completion_display:{ready:false,generation:11,account_context:ACCOUNT}});
    await noCelebration(flapping);assert.deepStrictEqual(await counts(flapping),{acks:0,timers:1,active:0});await advance(flapping,5000);
    await update(flapping,{completion_display:{ready:true,generation:12,account_context:ACCOUNT}});await advance(flapping,1500);
    assert.deepStrictEqual(await counts(flapping),{acks:0,timers:2,active:1});await advance(flapping,2799);
    assert.strictEqual(await flapping.evaluate(()=>window.__acks.length),0);await advance(flapping,1);
    assert.deepStrictEqual(await flapping.evaluate(()=>window.__acks),[{id:completion(61).id,account_context:ACCOUNT,presentation_generation:12}]);
    await flapping.close();
    checks.push('Lobby readiness flicker or a new garage generation restarts the stability margin; hiding halfway through the effect leaves it unacknowledged and the next stable garage receives a fresh full duration with its current generation');

    const hidden=await createSurface(fixture());
    async function setVisibility(surface,value){await surface.evaluate(value=>{
        Object.defineProperty(document,'visibilityState',{configurable:true,get:function(){return value;}});
        Object.defineProperty(document,'hidden',{configurable:true,get:function(){return value==='hidden';}});
        document.dispatchEvent(new Event('visibilitychange'));
    },value);}
    await setVisibility(hidden,'hidden');await achieve(hidden,completion(62),false);await advance(hidden,5000);await noCelebration(hidden);
    assert.deepStrictEqual(await counts(hidden),{acks:0,timers:0,active:0});
    await setVisibility(hidden,'visible');await advance(hidden,1500);assert.deepStrictEqual(await counts(hidden),{acks:0,timers:1,active:1});
    await advance(hidden,700);await setVisibility(hidden,'hidden');await noCelebration(hidden);await advance(hidden,5000);
    assert.deepStrictEqual(await counts(hidden),{acks:0,timers:1,active:0});
    await setVisibility(hidden,'visible');await advance(hidden,1500);assert.deepStrictEqual(await counts(hidden),{acks:0,timers:2,active:1});
    await finish(hidden);assert.deepStrictEqual(await counts(hidden),{acks:1,timers:2,active:0});await hidden.close();
    checks.push('A hidden browser/native document never consumes goal feedback, and hiding during the effect cancels it without acknowledgement so returning visibly restarts the complete presentation');

    const interruptedNative=await createSurface(fixture());await achieve(interruptedNative,completion(63));await advance(interruptedNative,600);
    await interruptedNative.evaluate(()=>{window.__nativeReady=false;window.__nativeSize={width:256,height:256};const p=JSON.parse(window.model.payload);
        p.window={ready:false,width:256,height:256};window.model.payload=JSON.stringify(p);window.__handlers['viewEnv.onDataChanged']();});
    await noCelebration(interruptedNative);await advance(interruptedNative,5000);
    assert.deepStrictEqual(await counts(interruptedNative),{acks:0,timers:1,active:0});
    await interruptedNative.evaluate(()=>window.__completeNativeLoad());await interruptedNative.waitForFunction(()=>window.__nativeSize.width===624);
    await advance(interruptedNative,1500);assert.deepStrictEqual(await counts(interruptedNative),{acks:0,timers:2,active:1});
    await finish(interruptedNative);assert.deepStrictEqual(await counts(interruptedNative),{acks:1,timers:2,active:0});await interruptedNative.close();
    checks.push('A native window reverting to its cropped256px bootstrap cancels the in-progress effect without consuming it; verified624x208 bounds must return and settle before the complete notification resumes');

    const interrupted=await createSurface(fixture());await achieve(interrupted,completion(64));await advance(interrupted,800);
    const durablePending=await interrupted.evaluate(()=>JSON.parse(window.model.payload));
    await interrupted.evaluate(()=>window.dispatchEvent(new Event('unload')));assert.strictEqual((await counts(interrupted)).acks,0);await interrupted.close();
    const recreated=await createSurface(durablePending);await noCelebration(recreated);await advance(recreated,1499);await noCelebration(recreated);
    await advance(recreated,1);assert.deepStrictEqual(await counts(recreated),{acks:0,timers:1,active:1});
    await finish(recreated);assert.deepStrictEqual(await counts(recreated),{acks:1,timers:1,active:0});await recreated.close();
    checks.push('Destroying and recreating the garage view midway through feedback preserves the pending token; the replacement view waits for stability and shows the full effect before acknowledging once');

    const lostBalance=await createSurface(fixture());await achieve(lostBalance,completion(65));await advance(lostBalance,900);
    const goodBalance=await lostBalance.evaluate(()=>JSON.parse(window.model.payload).balance);
    await update(lostBalance,{ready:false,balance:null});await noCelebration(lostBalance);await advance(lostBalance,5000);
    assert.deepStrictEqual(await counts(lostBalance),{acks:0,timers:1,active:0});
    await update(lostBalance,{ready:true,balance:goodBalance});await advance(lostBalance,1500);
    assert.deepStrictEqual(await counts(lostBalance),{acks:0,timers:2,active:1});await finish(lostBalance);
    assert.deepStrictEqual(await counts(lostBalance),{acks:1,timers:2,active:0});await lostBalance.close();
    checks.push('Temporarily unavailable synced balance data cancels visual feedback without acknowledging its stillpending event; resynchronization delivers a full visible presentation rather than losing the achievement');

    const rejectedGeneration=await createSurface(fixture(),{rejectFirstAckGeneration:true});await achieve(rejectedGeneration,completion(66));
    await finish(rejectedGeneration);
    await rejectedGeneration.waitForFunction(()=>JSON.parse(window.model.payload).completion_display.ready===false);
    assert.strictEqual(await rejectedGeneration.evaluate(()=>JSON.parse(window.model.payload).goal_completion.id),completion(66).id);
    await update(rejectedGeneration,{completion_display:{ready:true,generation:9,account_context:ACCOUNT}});await advance(rejectedGeneration,1499);await noCelebration(rejectedGeneration);
    await advance(rejectedGeneration,1);assert.deepStrictEqual(await counts(rejectedGeneration),{acks:1,timers:2,active:1});
    await finish(rejectedGeneration);assert.deepStrictEqual(await counts(rejectedGeneration),{acks:2,timers:2,active:0});
    assert.deepStrictEqual(await rejectedGeneration.evaluate(()=>window.__acks.map(x=>x.presentation_generation)),[7,9]);await rejectedGeneration.close();
    checks.push('If native visibility changes at acknowledgement and the old generation is rejected, the stillpending event is not locally suppressed forever: a new visible generation receives a full fresh presentation and a valid acknowledgement');

    const timed=await createSurface(fixture(),{realTimers:true});const realStart=Date.now();await achieve(timed,completion(50),false);
    await timed.waitForFunction(()=>document.getElementById('lc-widget').classList.contains('lc-widget-celebrating'),undefined,{timeout:2500});
    assert.strictEqual(await timed.evaluate(()=>window.__acks.length),0);
    await timed.waitForFunction(()=>!document.getElementById('lc-widget').classList.contains('lc-widget-celebrating'),undefined,{timeout:4000});
    assert(Date.now()-realStart>=4100,'The real stable grace plus full2800ms display must elapse before acknowledgement');
    assert.strictEqual(await timed.locator('#lc-widget-status').textContent(),'Meta alcanzada.');
    assert.deepStrictEqual(await counts(timed),{acks:1,timers:1,active:0});
    await timed.close();
    checks.push('The real1500ms stable-garage grace followed by the full2800ms effect restores the regular widget and only then acknowledges, without relying on repaint, interaction or another incoming payload');
};
