// Progress reflects server stages. Routing progress is not overall review completion.
export const isProcessing=job=>['queued','routing','analyzing'].includes(job.status);
export function projectJobs(state){
  return [...(state.data?.intakes||[])].filter(j=>!state.project||(j.project_ids||[]).includes(state.project))
    .sort((a,b)=>String(b.updated||b.created).localeCompare(String(a.updated||a.created)));
}
export const activeProcessing=state=>projectJobs(state).find(isProcessing);
export function durationLabel(start,end=Date.now()){
  const began=Date.parse(start),finished=typeof end==='number'?end:Date.parse(end);
  if(!Number.isFinite(began)||!Number.isFinite(finished))return '—';
  const seconds=Math.max(0,Math.floor((finished-began)/1000));
  return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
}
export function processingPanel(state,esc){
  const jobs=projectJobs(state),pending=state.pendingCapture&&(!state.project||state.pendingCapture.projectId===state.project)?state.pendingCapture:null;
  const current=jobs.find(isProcessing)||jobs.find(j=>j.id===state.focusedIntake)||jobs[0];
  if(!pending&&!current)return '';
  const clock=(start,end)=>`<span class="processing-clock" data-processing-start="${esc(start)}" ${end?`data-processing-end="${esc(end)}"`:''} aria-live="off">${durationLabel(start,end||Date.now())}</span>`;
  const summary=job=>{
    const count=Number(job.units_total)||0,done=Number(job.units_processed)||0;
    const total=Number(job.analysis_total)||0,analyzed=Number(job.analysis_done)||0;
    const titles={queued:'Preparing your review',routing:'Matching passages to projects',analyzing:'Analyzing findings',
      complete:job.review_ids?.length?'Review complete':'No matching project content',failed:'Processing needs attention'};
    const hint=job.status==='queued'?'Your content was received. Waiting for processing to start.':job.status==='routing'?
      'Checking which passages belong to the selected project.':job.status==='analyzing'?
      'Comparing evidence and prior decisions. Passage matching is complete; the review is still running.':job.status==='complete'?
      'Processing has finished. Inspect the findings and their source passages.':'This review did not finish. Input is retained for retry.';
    const meter=job.status==='routing'&&count?`<progress max="${count}" value="${Math.min(done,count)}" aria-label="Project matching progress"></progress>`:
      job.status==='analyzing'&&total?`<progress max="${total}" value="${Math.min(analyzed,total)}" aria-label="Evidence analysis progress"></progress>`:
      isProcessing(job)?'<progress aria-label="Processing in progress"></progress>':'';
    const counters=[count?`${done}/${count} passages checked for project relevance`:'',total?`${analyzed}/${total} evidence-analysis batches`:''].filter(Boolean).join(' · ');
    const complete=job.status==='complete';
    const timing=job.attempt_started?(complete||job.status==='failed'?'Attempt duration':'Elapsed'):'Since original upload';
    const blocked=job.status==='failed'&&/outbound connection denied by local Windows\/network permissions/.test(job.error||'');
    const recovery=blocked?'<p class="processing-recovery"><strong>AI requests were blocked on this computer.</strong> This can happen when the server is started inside a restricted agent terminal. Close that server, double-click start.bat in File Explorer under your normal Windows account, then retry. If it persists there, check local network policy.</p>':'';
    return `<div class="processing-record" data-processing-job="${esc(job.id)}"><div class="processing-copy"><strong>${esc(titles[job.status]||job.status)}</strong><p class="hint">${esc(hint)}</p>${meter}<p class="processing-meta">${counters?`${esc(counters)} · `:''}${timing} ${clock(job.attempt_started||job.created,complete||job.status==='failed'?job.updated:null)}</p>${job.error?`<p class="danger" role="alert">${esc(job.error)}</p>`:''}${recovery}</div><div class="processing-actions">${job.status==='failed'?`<button class="secondary" data-retry="${esc(job.id)}">Retry retained input</button>`:''}${complete?(job.review_ids||[]).map((id,i)=>`<button class="secondary" data-review="${esc(id)}">Open review${job.review_ids.length>1?' '+(i+1):''}</button>`).join(''):''}</div></div>`;
  };
  const uploading=pending?`<div class="processing-record"><div class="processing-copy"><strong>${esc(pending.error?'Upload needs attention':pending.files?'Uploading and preparing documents':'Submitting your content')}</strong><p class="hint">${pending.error?'Your selected content is still in the form. Correct the issue and submit again.':pending.files?`${pending.files} document${pending.files===1?'':'s'} selected. Uploading and extracting text before analysis.`:'Sending your content for processing.'}</p>${pending.error?`<p class="danger" role="alert">${esc(pending.error)}</p>`:'<progress aria-label="Upload in progress"></progress>'}<p class="processing-meta">${pending.error?'Duration':'Elapsed'} ${clock(pending.started,pending.finished)}</p></div></div>`:'';
  const history=jobs.filter(j=>pending||j.id!==current?.id).slice(0,5);
  return `<section class="panel processing-overview" aria-label="Processing status"><div role="status" aria-live="polite" aria-atomic="false">${uploading||summary(current)}${state.progressError?'<p class="hint">Status updates are temporarily unavailable. Reconnecting automatically…</p>':''}</div>${history.length?`<details class="processing-history"><summary>Earlier processing (${history.length})</summary>${history.map(summary).join('')}</details>`:''}</section>`;
}
