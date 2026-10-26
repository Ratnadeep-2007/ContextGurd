import {authView, shell, reportView} from './views.js';
import {reviewWorkspace, sourceConnections, projectPicker} from './workspace.js';
import {processingPanel,activeProcessing,durationLabel} from './processing.js';

const defaults=()=>({project_id:'',source_id:'',start:'',end:'',status:'all'});
const state={data:null,project:'',page:'review',review:null,projectData:null,busy:false,findingId:null,
  findingFilter:'all',navOpen:false,filters:defaults(),filteredReviews:[],slackChannels:[],openWhenReady:null,meeting:null,captureType:'manual',pendingCapture:null,focusedIntake:null,progressError:false};
const app=document.querySelector('#app');
let pollTimer,whatsappTimer;
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=name=>`<svg class="icon" aria-hidden="true" focusable="false"><use href="/static/assets/icons.svg#${esc(name)}"></use></svg>`;
const hint=text=>`<p class="hint">${esc(text)}</p>`;
const projects=()=>state.data?.projects||[];
const userName=id=>{const user=state.data?.users.find(u=>u.id===id);return user?.display_name||user?.username||'Unassigned';};
const projectOptions=(empty=true)=>(empty?'<option value="">Match across my projects</option>':'')+projects().map(p=>`<option value="${esc(p.id)}" ${p.id===state.project?'selected':''}>${esc(p.name)}</option>`).join('');
const userOptions=(selected='',projectOnly=true)=>'<option value="">Unassigned</option>'+(state.data?.users||[]).filter(u=>!projectOnly||projects().find(p=>p.id===(state.project||projects()[0]?.id))?.members[u.id]).map(u=>`<option value="${esc(u.id)}" ${u.id===selected?'selected':''}>${esc(u.display_name||u.username)}</option>`).join('');
const multiUsers=selected=>(state.data?.users||[]).filter(u=>projects().find(p=>p.id===state.project)?.members[u.id]).map(u=>`<option value="${esc(u.id)}" ${(selected||[]).includes(u.id)?'selected':''}>${esc(u.display_name||u.username)}</option>`).join('');
const sourceOptions=()=>state.data.sources.map(s=>`<option value="${esc(s.id)}">${esc(s.label)}</option>`).join('');
const recent=()=>state.filteredReviews.slice(0,12).map(r=>`<button class="recent-review ${state.review?.id===r.id?'active':''}" data-review="${esc(r.id)}">${icon('file-text')}<span><strong>${esc(r.goal)}</strong><small>${r.test_mode?'Fictional sample':'Project review'} · ${esc(r.readiness)}</small></span><i></i></button>`).join('')||hint('Processed reviews appear here. Adjust the review filters to find earlier work.');
const context=()=>({state,esc,icon,hint,projectOptions,userOptions,multiUsers,sourceOptions,userName,recent:recent(),projectPicker:projectPicker({state,esc,icon})});

function toast(message){const node=document.querySelector('#notice');node.textContent=message;node.style.display='block';clearTimeout(toast.timer);toast.timer=setTimeout(()=>node.style.display='none',11000);}
async function api(path,body,method){const options={method:method||(body?'POST':'GET'),credentials:'same-origin'};if(body){options.body=JSON.stringify(body);options.headers={'Content-Type':'application/json'};}const response=await fetch('/api'+path,options);const result=await response.json();if(!response.ok)throw Error(result.detail||'Request failed.');return result;}
const command=(action,payload={})=>api('/command',{action,payload});
async function loadReviews(){state.filteredReviews=await api('/reviews?'+new URLSearchParams(state.filters));}
async function refresh(){
  state.data=await api('/state');
  if(state.project&&!projects().some(p=>p.id===state.project))state.project='';
  if(!state.project&&projects().length===1){state.project=projects()[0].id;state.filters.project_id=state.project;}
  state.projectData=state.project?await api('/projects/'+state.project+'/evidence'):null;
  await loadReviews();
}
function render(preserveCapture=false){
  if(!state.data)return;
  const previous=preserveCapture?document.querySelector('#capture-panel'):null;
  const projectDraft=preserveCapture?document.querySelector('.create-project[open]'):null;
  const meetingDraft=preserveCapture&&state.page==='sources'?document.querySelector('form[data-form=meeting]'):null;
  const processingHistoryOpen=document.querySelector('#processing-overview .processing-history')?.open;
  const focus=previous?.contains(document.activeElement)||projectDraft?.contains(document.activeElement)?document.activeElement:null;
  const ui=context();
  const body=state.page==='review'?(state.review?reportView(ui):reviewWorkspace(ui)):state.page==='sources'?sourceConnections(ui):state.page==='team'?teamPage():settingsPage();
  app.innerHTML=shell(ui,body);
  if(previous&&state.page==='review'&&!state.review){document.querySelector('#capture-panel')?.replaceWith(previous);focus?.focus({preventScroll:true});}
  if(projectDraft&&state.page==='review'){document.querySelector('.create-project')?.replaceWith(projectDraft);focus?.focus({preventScroll:true});}
  if(meetingDraft)document.querySelector('form[data-form=meeting]')?.replaceWith(meetingDraft);
  showProcessing();
  if(processingHistoryOpen&&document.querySelector('.processing-history'))document.querySelector('.processing-history').open=true;
}
function showProcessing(){
  const grid=document.querySelector('.review-intake-grid');
  if(state.page!=='review'||state.review||!grid)return;
  // Replace the old below-the-fold list rather than showing duplicate progress.
  document.querySelector('.processing-panel')?.remove();
  let region=document.querySelector('#processing-overview');
  if(!region){region=document.createElement('div');region.id='processing-overview';grid.before(region);}
  const expanded=region.querySelector('.processing-history')?.open;
  region.innerHTML=processingPanel(state,esc);
  if(expanded&&region.querySelector('.processing-history'))region.querySelector('.processing-history').open=true;
  updateCaptureButton();
}
function updateCaptureButton(){
  const button=document.querySelector('form[data-form=capture] button:not([type=button])');
  if(!button)return;
  const working=Boolean((state.pendingCapture&&!state.pendingCapture.error&&state.pendingCapture.projectId===state.project)||activeProcessing(state));
  button.disabled=!state.project||state.busy||working;
  button.innerHTML=working?'Processing…':`${icon('arrow-right')}Process content`;
}
setInterval(()=>{
  for(const node of document.querySelectorAll('[data-processing-start]'))
    node.textContent=durationLabel(node.dataset.processingStart,node.dataset.processingEnd||Date.now());
},1000);
async function openReview(id){state.review=await api('/reviews/'+id);state.project=state.review.project_id;state.projectData=await api('/projects/'+state.project+'/evidence');state.findingId=null;state.findingFilter='all';state.page='review';state.navOpen=false;render();}
function ensurePolling(){
  clearTimeout(pollTimer);
  if(!state.data||!state.data.intakes.some(j=>['queued','routing','analyzing'].includes(j.status)))return;
  pollTimer=setTimeout(async()=>{
    if(state.busy){ensurePolling();return;}
    try{
      await refresh();state.progressError=false;
      if(state.openWhenReady){
        const job=state.data.intakes.find(j=>j.id===state.openWhenReady);
        if(job?.status==='complete'&&job.review_ids.length===1){state.openWhenReady=null;await openReview(job.review_ids[0]);}
        else{if(job?.status==='failed')state.openWhenReady=null;render(true);}
      }else if(state.page==='review')render(true);
    }catch(error){state.progressError=true;showProcessing();}
    ensurePolling();
  },1200);
}
function pollWhatsApp(){
  clearTimeout(whatsappTimer);
  const status=state.data?.connection_details.whatsapp?.status;
  if(state.page!=='sources'||!['connecting','awaiting_scan','reconnecting'].includes(status))return;
  whatsappTimer=setTimeout(async()=>{
    if(!state.busy){try{state.data.connection_details.whatsapp=await api('/whatsapp/status');render(true);}catch(error){toast(error.message);}}
    pollWhatsApp();
  },1800);
}
function accepted(job,projectId=''){state.pendingCapture=null;state.focusedIntake=job.id;state.progressError=false;if(state.data)state.data.intakes=[job,...state.data.intakes.filter(j=>j.id!==job.id)];state.page='review';state.review=null;state.project=projectId;state.filters={...defaults(),project_id:projectId};showProcessing();if(job.status==='complete')toast('Open the saved review.');}

function teamPage(){
  const selected=projects().find(p=>p.id===state.project)||projects()[0];
  const labels={owner:'Project owner',decision_owner:'Decision owner',reviewer:'Reviewer'};
  const members=state.data.users.filter(u=>u.role==='owner'||selected?.members[u.id]);
  return `<div class="heading"><div><h1>Team</h1><p class="page-description">${esc(selected?.name||'Project')} members and decision roles.</p></div></div><section class="panel team-panel"><table class="team-table"><thead><tr><th>Member</th><th>Role</th><th>Responsibility</th></tr></thead><tbody>${members.map(u=>`<tr><td><strong>${esc(u.display_name||u.username)}</strong>${u.is_demo?'<span class="badge">Demo</span>':''}</td><td>${esc(u.role==='owner'?'Admin / project owner':labels[selected?.members[u.id]]||'Member')}</td><td>${esc(u.role==='owner'?'Project administration and final decisions':u.responsibility||'Review assigned findings')}</td></tr>`).join('')}</tbody></table>${hint('Reviewers answer assigned findings. Decision owners confirm resolutions.')}</section>`;
}

function settingsPage(){return `<h1>Settings & privacy</h1><section class="panel compact"><h2>Where your content goes</h2><p>Accounts, retained project evidence and versioned decisions are stored locally. Live processing sends the complete selected input and eligible project descriptions to the configured model; matched project decisions are used for analysis.</p><p>After successful processing, unmatched content is removed from active intake records. Relevant quoted evidence remains. Failed processing retains the input for an explicit retry. SQLite deletion does not guarantee secure erasure from disk journals or backups.</p><p>Keys and endpoints belong in this rebuild’s <code>.env</code>. Muse Wonder is primary; Groq and NVIDIA are fallbacks. Keys are never displayed here.</p><p>Connections are managed in Sources. Documents and selected conversation imports belong in Project Reviews. No meeting is joined silently and no message is sent.</p><button class="secondary" data-page="sources">Manage source connections</button><button class="secondary" data-click="logout">Sign out</button></section>`;}

document.addEventListener('change',async event=>{
  if(event.target.id==='project-select'){
    if(event.target.value===state.project)return;
    const main=document.querySelector('#main');state.busy=true;if(main)main.inert=true;
    try{state.project=event.target.value;state.filters.project_id=state.project;state.review=null;state.findingId=null;state.navOpen=false;await refresh();render();}catch(error){toast(error.message);}finally{state.busy=false;if(main)main.inert=false;updateCaptureButton();}
  }
  if(event.target.dataset.answer){const node=document.querySelector('#other-'+event.target.dataset.answer);node.hidden=event.target.value!=='other';node.querySelector('textarea').required=event.target.value==='other';}
  if(event.target.id==='meeting-link'){const form=event.target.closest('form');form.querySelector('[name=consent]').checked=false;form.querySelector('[name=model_consent]').checked=false;}
  if(event.target.name==='project_id'&&event.target.closest('form[data-form=responsibility]')){
    const members=projects().find(p=>p.id===event.target.value)?.members||{};
    event.target.closest('form').querySelector('[name=user_id]').innerHTML=state.data.users.filter(u=>members[u.id]).map(u=>`<option value="${esc(u.id)}">${esc(u.display_name||u.username)}</option>`).join('');
  }
});

document.addEventListener('click',async event=>{
  const target=event.target.closest('button');if(!target||target.disabled||state.busy)return;
  try{
    if(target.dataset.selectFinding){state.findingId=target.dataset.selectFinding;render();if(innerWidth<=900)document.querySelector('.finding-content')?.scrollIntoView({block:'start'});else document.querySelector('[data-select-finding="'+CSS.escape(state.findingId)+'"]')?.focus({preventScroll:true});}
    else if(target.dataset.findingFilter){state.findingFilter=target.dataset.findingFilter;state.findingId=null;render();document.querySelector('[data-finding-filter="'+state.findingFilter+'"]')?.focus({preventScroll:true});}
    else if(target.dataset.click==='menu'||target.dataset.click==='close-menu'){state.navOpen=target.dataset.click==='menu'?!state.navOpen:false;render();if(state.navOpen)document.querySelector('.sidebar .nav-item')?.focus();else document.querySelector('.mobile-menu')?.focus();}
    else if(target.dataset.page){state.busy=true;document.querySelector('#main')?.setAttribute('inert','');state.page=target.dataset.page;if(state.page==='review'){state.captureType='manual';state.review=null;state.project=state.filters.project_id||'';state.projectData=state.project?await api('/projects/'+state.project+'/evidence'):null;}else if(state.page==='team'||state.page==='sources')await refresh();state.navOpen=false;render();}
    else if(target.dataset.click==='whatsapp-status'){state.busy=true;state.data.connection_details.whatsapp=await api('/whatsapp/status');render(true);}
    else if(target.dataset.click==='whatsapp-chats'){state.busy=true;await api('/whatsapp/chats',{});await refresh();render(true);}
    else if(target.dataset.click==='whatsapp-disconnect'){state.busy=true;clearTimeout(whatsappTimer);const result=await api('/whatsapp/disconnect',{});await refresh();render();toast(result.note);}
    else if(target.dataset.click==='whatsapp-import'){state.busy=true;document.querySelector('#main')?.setAttribute('inert','');state.captureType='whatsapp';state.page='review';state.review=null;await refresh();render();document.querySelector('#capture-panel')?.scrollIntoView({block:'start'});}
    else if(target.dataset.review)await openReview(target.dataset.review);
    else if(target.dataset.click==='new-review'){state.review=null;state.page='review';state.findingId=null;render();document.querySelector('#capture-panel')?.scrollIntoView({block:'start'});}
    else if(target.dataset.click==='clear-filters'){state.filters={...defaults(),project_id:state.project};await loadReviews();render();}
    else if(target.dataset.click==='demo'){
      state.busy=true;
      const result=await command('demo');state.project=result.project.id;
      if(result.review_id){state.filters.project_id=result.project.id;await refresh();await openReview(result.review_id);return;}
      await command('project_settings',{project_id:result.project.id,description:'Orchid is a fictional v2 internal analytics pilot. Dates, security approval, vendor cost and credentials must be clarified.',goal:'Can the fictional Orchid v2 pilot proceed?'});
      const files=await api('/projects/'+result.project.id+'/evidence');
      const text=files.evidence.map(e=>e.text).join('\n\n');
      const job=await api('/intakes/text',{label:'Fictional Orchid conversation',text,project_ids:[result.project.id],test_mode:true,consent:true});
      state.openWhenReady=job.id;accepted(job);await refresh();
      const finished=state.data.intakes.find(j=>j.id===job.id);
      if(finished?.status==='complete'&&finished.review_ids.length===1){state.openWhenReady=null;await openReview(finished.review_ids[0]);}else render();
    }
    else if(target.dataset.retry){state.busy=true;const job=await api('/intakes/'+target.dataset.retry+'/retry',{});accepted(job,state.project);await refresh();render();}
    else if(target.dataset.connection){state.busy=true;let result;try{result=await api('/connections/'+target.dataset.connection+'/check',{});}finally{await refresh();render(true);}toast(result.status);}
    else if(target.dataset.click==='slack-connect'){const settings=state.data.connection_details.slack;const local=settings.local_token_ready&&!settings.oauth_ready;const result=await api(local?'/slack/local-connect':'/slack/connect',{});if(result.url)location.assign(result.url);else{await refresh();render();toast(result.note);}}
    else if(target.dataset.click==='slack-disconnect'){const result=await command('slack_disconnect');await refresh();render();toast(result.note);}
    else if(target.dataset.click==='slack-channels'){state.busy=true;const result=await api('/slack/channels');state.slackChannels=result.channels;render();document.querySelector('.slack-import').open=true;toast(result.complete?'Authorized channel list loaded.':'Channel list is bounded; some channels were not listed.');}
    else if(target.dataset.click==='logout'){clearTimeout(pollTimer);await api('/logout',{});state.data=null;state.review=null;state.project='';state.filters=defaults();state.filteredReviews=[];state.meeting=null;state.captureType='manual';state.pendingCapture=null;state.focusedIntake=null;state.progressError=false;app.innerHTML=authView(false,icon);}
    else if(target.dataset.original){const result=await api('/evidence/'+target.dataset.original+'/original');let node=target.parentElement.querySelector('pre');if(!node){node=document.createElement('pre');target.parentElement.append(node);}node.textContent=JSON.stringify(result.original,null,2);}
  }catch(error){toast(error.message);}finally{state.busy=false;document.querySelector('#main')?.removeAttribute('inert');updateCaptureButton();ensurePolling();pollWhatsApp();}
});

document.addEventListener('submit',async event=>{
  const form=event.target.closest('form[data-form]');if(!form)return;event.preventDefault();if(state.busy)return;
  state.busy=true;app.setAttribute('aria-busy','true');const buttons=[...form.querySelectorAll('button')];buttons.forEach(b=>b.disabled=true);
  const fd=new FormData(form),p=Object.fromEntries(fd),kind=form.dataset.form;
  const fields=form.querySelector('fieldset');if(fields)fields.disabled=true;
  try{
    if(kind==='login'||kind==='setup'){if(kind==='setup')await api('/setup',p);await api('/login',p);await refresh();render();return;}
    if(kind==='capture'){
      if(!state.project)throw Error('Select a project before adding context.');
      if(activeProcessing(state))throw Error('Wait for this project’s current processing to finish before submitting again.');
      const files=fd.getAll('files').filter(f=>f instanceof File&&f.name);
      const text=String(p.text||'').trim();
      if((files.length&&text)||(!files.length&&!text))throw Error('Choose documents or paste a conversation for this batch.');
      const chosen=[state.project];
      state.pendingCapture={started:new Date().toISOString(),files:files.length,projectId:state.project};showProcessing();
      let job;
      if(files.length){
        const upload=new FormData();files.forEach(file=>upload.append('files',file));
        upload.set('project_ids',chosen?JSON.stringify(chosen):'');upload.set('goal',p.goal||'');upload.set('source_type',p.source_type);
        for(const flag of ['consent','model_consent','test_mode','share'])upload.set(flag,String(fd.has(flag)));
        const response=await fetch('/api/intakes/upload',{method:'POST',body:upload});job=await response.json();if(!response.ok)throw Error(job.detail||'Upload failed.');
      }else job=await api('/intakes/text',{text,label:p.label,source_type:p.source_type,project_ids:chosen,goal:p.goal||'',consent:fd.has('consent'),model_consent:fd.has('model_consent'),test_mode:fd.has('test_mode'),share:fd.has('share')});
      accepted(job,chosen[0]);
    }else if(kind==='whatsapp-connect'){
      await api('/whatsapp/connect',{consent:fd.has('consent')});
    }else if(kind==='whatsapp-select'){
      const ids=fd.getAll('ids'),direct=String(p.direct||'').trim();
      if(direct)ids.push(direct.includes('@')?direct:direct.replace(/[^0-9]/g,'')+'@s.whatsapp.net');
      await api('/whatsapp/select',{ids:[...new Set(ids)],consent:fd.has('consent')});
    }else if(kind==='whatsapp-capture'){
      if(!state.project)throw Error('Select a project before processing WhatsApp text.');
      const job=await api('/whatsapp/capture',{project_ids:[state.project],consent:fd.has('consent'),model_consent:fd.has('model_consent'),share:fd.has('share')});
      accepted(job,state.project);
    }else if(kind==='meeting'){
      const result=await api('/meetings',{link:p.link,passcode:p.passcode||'',operation:event.submitter?.value||'join',consent:fd.has('consent'),model_consent:fd.has('model_consent'),share:fd.has('share')});
      const link=new URL(p.link);state.meeting={link:link.origin+link.pathname,consent:fd.has('consent'),model_consent:fd.has('model_consent'),share:fd.has('share')};
      if(result.job)accepted(result.job);else toast(result.note);
    }else if(kind==='slack-capture'){
      const job=await api('/slack/capture',{channel:p.channel,thread:p.thread||null,start:p.start||null,end:p.end||null,project_ids:p.project_id?[p.project_id]:null,consent:fd.has('consent'),model_consent:fd.has('model_consent'),share:fd.has('share')});accepted(job);
    }else if(kind==='review-filters'){
      state.filters={...state.filters,...p};await loadReviews();render();return;
    }else if(['assign','respond','confirm','dismiss'].includes(kind)){
      p.review_id=state.review.id;p.finding_id=form.dataset.fid;
      if(kind==='assign'){p.assignee_id=p.assignee_id||null;p.collaborators=fd.getAll('collaborators');p.watchers=fd.getAll('watchers');}
      if(kind==='confirm')p.supersedes=p.supersedes||null;
      if(kind==='respond'){const finding=state.review.findings.find(f=>f.id===p.finding_id);p.answer=p.choice==='other'?p.answer:finding.citations[Number(p.choice)].quote;p.citations=p.choice==='other'?[]:[finding.citations[Number(p.choice)]];p.answer_known=!fd.has('unknown');delete p.choice;delete p.unknown;}
      await command(kind,p);state.review=await api('/reviews/'+p.review_id);
    }else{
      if(kind==='source_grants')p.allowed_users=fd.getAll('allowed_users');
      const result=await command(kind,p);if(kind==='project'){state.project=result.id;state.filters.project_id=result.id;state.review=null;state.page='review';}
      toast('Saved.');
    }
    await refresh();render();
  }catch(error){if(state.pendingCapture&&!state.pendingCapture.error)state.pendingCapture={...state.pendingCapture,error:error.message,finished:new Date().toISOString()};showProcessing();toast(error.message);}finally{state.busy=false;app.setAttribute('aria-busy','false');buttons.forEach(b=>b.disabled=false);if(fields)fields.disabled=false;updateCaptureButton();ensurePolling();pollWhatsApp();}
});

document.addEventListener('keydown',event=>{if(event.key==='Escape'&&state.navOpen){state.navOpen=false;render();document.querySelector('.mobile-menu')?.focus();}});
async function boot(){try{const health=await api('/health');if(health.api_revision!=='conversation-v1'){app.innerHTML='<main id="main" class="auth"><section class="panel"><h1>Open the updated ContextGuard</h1><p>This address is still serving an older build. Run start.bat from contextguard-rebuild and open the address it prints. It preserves this process and your saved records.</p><p>The updated app may use the next available local port.</p></section></main>';return;}if(health.setup_required){app.innerHTML=authView(true,icon);return;}await refresh();render();ensurePolling();pollWhatsApp();}catch{app.innerHTML=authView(false,icon);}}
boot();
