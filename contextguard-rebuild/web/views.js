// Independent presentation layer. Network commands and authorization stay in app.js / the API.
export function authView(setup, icon) {
  return `<main id="main" class="auth">
    <a class="brand" href="/">${icon('shield-check')}<span>ContextGuard</span></a>
    <div class="auth-layout"><section class="auth-intro"><p class="eyebrow">Project evidence & decisions</p>
      <h1>Review the evidence.<br>Resolve the gaps.</h1><p>Check project documents and conversations for conflicts. Record answers with their supporting sources.</p>
      <div class="auth-note">${icon('shield-check')}<span>Your workspace runs on this computer. External source and model access are explicit choices.</span></div></section>
    <section class="panel auth-form"><p class="eyebrow">Your local workspace</p><h2>${setup?'Create your local workspace':'Welcome back'}</h2>
      <p class="muted">${setup?'Set up your owner account to begin.':'Sign in to continue your project reviews.'}</p>
      <form data-form="${setup?'setup':'login'}"><label for="username">Your name</label><input id="username" name="username" autocomplete="username" required minlength="2" maxlength="60">
      <label for="password">Password</label><input id="password" name="password" type="password" autocomplete="${setup?'new-password':'current-password'}" minlength="10" required>
      <p class="hint">Use at least 10 characters. Your password is never sent to a model.</p>
      <button class="full-width">${setup?'Create workspace':'Sign in'}${icon('arrow-right')}</button></form>
    </section></div></main>`;
}

export function shell(ui, body) {
  const {state,esc,icon,projectOptions,recent}=ui, d=state.data;
  const pages=[['review','folder-open','Project reviews',d.reviews.length],['sources','file-text','Sources',null],['team','users','Team',null]];
  const nav=pages.map(([key,svg,name,count])=>`<button class="nav-item" data-page="${key}" ${state.page===key?'aria-current="page"':''} aria-label="${name}">${icon(svg)}<span>${name}</span>${count!==null?`<small aria-hidden="true">${String(count).padStart(2,'0')}</small>`:''}</button>`).join('');
  const pageLabel={review:'Project reviews',sources:'Sources',team:'Team',settings:'Providers & privacy'}[state.page];
  return `<div class="shell">
    ${state.navOpen?'<button class="nav-scrim" data-click="close-menu" aria-label="Close workspace navigation"></button>':''}
    <aside id="workspace-navigation" class="sidebar ${state.navOpen?'mobile-open':''}" aria-label="Workspace navigation" ${state.navOpen?'role="dialog" aria-modal="true"':''}>
      <a href="/" class="brand">${icon('shield-check')}<span>ContextGuard</span></a>
      <div class="workspace-card"><span class="workspace-initial">${esc(d.actor.username.slice(0,1).toUpperCase())}</span><div><strong>${esc(d.actor.username)}</strong><small>Local workspace · on this device</small></div></div>
      <div class="side-section"><div class="side-heading"><span>Workspace</span><span>01</span></div><nav aria-label="Project workspace">${nav}</nav></div>
      <div class="recent"><div class="side-heading"><span>Recent reviews</span><button class="icon-button" data-click="new-review" aria-label="Start a new review">${icon('plus')}</button></div>${recent}</div>

    </aside>
    <div class="content" ${state.navOpen?'inert':''}><header class="topbar"><div class="breadcrumbs"><button class="icon-button mobile-menu" data-click="menu" aria-label="Open workspace navigation" aria-expanded="${Boolean(state.navOpen)}" aria-controls="workspace-navigation">${icon('menu')}</button>${icon('folder-open')}<span>Workspace</span>${icon('chevron-right')}<strong>${pageLabel}</strong></div>
      <div class="topbar-actions"><button class="secondary settings-button" data-page="settings">${icon('settings-2')}<span>Settings & privacy</span></button></div></header>
      <main id="main" class="workspace"><div id="busy" role="status"></div>${body}</main>
    </div></div>`;
}

export function reportView(ui) {
  const {state,esc,icon,hint}=ui, r=state.review;
  const unresolved=r.findings.filter(f=>f.state==='open'&&f.kind!=='verified_fact').length;
  const filter=state.findingFilter||'all';
  const visible=r.findings.filter(f=>filter==='all'||(filter==='open'?f.state==='open':f.state!=='open'));
  const selected=visible.find(f=>f.id===state.findingId)||visible[0];
  state.findingId=selected?.id||null;
  const index=visible.map((f,i)=>`<button class="finding-list-item ${f.id===selected?.id?'active':''}" data-select-finding="${esc(f.id)}" aria-pressed="${f.id===selected?.id}"><span class="finding-list-meta"><span class="priority-text ${f.state==='open'?f.priority:'recorded'}">${esc(f.state==='open'?f.priority:f.state)}</span><small>${String(i+1).padStart(2,'0')}</small></span><strong>${esc(f.title)}</strong><p>${esc(f.impact)}</p><span class="finding-list-foot">${icon('link')} ${f.citations.length} source passage${f.citations.length===1?'':'s'} ${icon('arrow-right')}</span></button>`).join('');
  const filters=[['all','All findings',r.findings.length],['open','Needs attention',r.findings.filter(f=>f.state==='open').length],['recorded','Recorded',r.findings.filter(f=>f.state!=='open').length]].map(([value,label,count])=>`<button data-finding-filter="${value}" aria-pressed="${filter===value}">${label}<span>${count}</span></button>`).join('');
  return `<div class="heading"><div><h1>${esc(r.goal)}</h1></div><div class="heading-action"><button class="secondary" data-click="new-review">${icon('plus')}Back to reviews</button></div></div>
    ${ui.projectPicker}<div class="review-toolbar"><div><span class="pill ${r.test_mode?'sample':''}"><i></i>${r.test_mode?'Fictional sample':'Your review'}</span><small>${r.test_mode?'Fixture analysis · no live AI':'Selected project evidence'}</small></div><div class="toolbar-links"><button class="text-button" data-page="team">${icon('users')}Team</button><a class="button secondary" href="/api/reviews/${esc(r.id)}/brief" download>${icon('download')}Download report</a><a class="button secondary" href="/api/reviews/${esc(r.id)}/document" download>${icon('file-text')}Download updated document</a></div></div>
    <div class="readiness-banner ${r.readiness==='Needs clarification'?'needs-attention':''}">${icon('shield-check')}<div><strong>${unresolved} ${unresolved===1?'decision needs':'decisions need'} attention</strong><small>${r.evidence.length} analyzed passages · ${esc(r.readiness)}</small></div></div>
    ${r.stale?'<div class="error-banner" role="alert">Sources changed. Start a new review before confirming or exporting decisions.</div>':''}
    <div class="report-workspace"><aside class="finding-index"><div class="finding-index-heading"><p class="eyebrow">Context Gap Report</p><h2>Findings <span>${r.findings.length}</span></h2></div><div class="finding-filters" aria-label="Filter findings">${filters}</div><div class="finding-list">${index||'<p class="empty">No findings in this view.</p>'}</div></aside>
      <div class="finding-content">${selected?findingView(ui,r,selected):'<section class="no-findings"><h2>No verified findings to display.</h2><p>Check source coverage and analysis limitations before drawing a conclusion.</p></section>'}</div></div>
    <details class="panel report-limits"><summary>Sources, failures and limitations <span>Read before acting on this report.</span></summary><p>Dates: ${esc(r.start||'all')} through ${esc(r.end||'all')}</p><p>Provider: ${esc(r.provider||'Analysis did not complete')}</p>${r.failures.map(x=>`<p class="danger">${esc(x)}</p>`).join('')}${r.limitations.map(x=>`<p>${esc(x)}</p>`).join('')}
      <p>Ready requires complete usable evidence and no open findings; Ready with actions allows low/medium open findings. High open findings, incomplete evidence, stale sources or failed analysis mean Needs clarification. This is not an accuracy score.</p>
      ${r.evidence.map(e=>`<p><strong>${esc(e.location)}</strong> · ${esc(e.extraction)}<small>${esc(e.author||'Unattributed')} · ${esc(e.timestamp||'Date unknown')}</small></p>`).join('')}</details>
    <details class="panel"><summary>Prior decisions considered <span>${r.memory.length} available for this review</span></summary>${r.memory.map(d=>`<p>${esc(d.text)}<small>${esc(ui.userName(d.confirmed_by))} · ${esc(d.confirmed_at)}</small></p>`).join('')||hint('No visible confirmed decisions for this project.')}</details>`;
}

function findingView(ui,r,f) {
  const {esc,icon,userOptions,multiUsers,userName,hint}=ui;
  const disabled=f.state!=='open'||r.stale||r.status!=='complete';
  const actor=ui.state.data.actor;
  const project=ui.state.data.projects.find(p=>p.id===r.project_id);
  const role=actor.role==='owner'?'owner':project?.members[actor.id];
  const canAssign=actor.id===r.owner_id;
  const canRespond=canAssign||actor.id===f.assignee_id;
  const canConfirm=['owner','decision_owner'].includes(role)&&f.responses.at(-1)?.answer_known===true;
  const citations=f.citations.map(c=>{const e=r.evidence.find(x=>x.id===c.evidence_id);return `<section class="quote-card"><div class="quote-source">${icon('file-text')}<div><strong>${esc(e?.location)}</strong><small>${esc(e?.author||'Unattributed')} · ${esc(e?.timestamp||'Date unknown')}</small></div></div><blockquote>${esc(c.quote)}</blockquote><div class="quote-actions">${e?.link&&/^https?:\/\//.test(e.link)?`<a href="${esc(e.link)}" target="_blank" rel="noopener noreferrer">Open source ${icon('arrow-right')}</a>`:''}<button class="text-button" data-original="${esc(c.evidence_id)}">View original import ${icon('arrow-right')}</button></div></section>`;}).join('');
  const responses=f.responses.map(x=>`<div class="recorded-response"><strong>${x.answer_known?'Recorded response':'Answer still unknown'}</strong><p>${esc(x.answer)}</p><small>${esc(userName(x.actor))} · ${esc(x.date)}</small></div>`).join('');
  return `<article data-finding="${esc(f.id)}" class="finding-detail"><div class="detail-meta"><span class="badge ${f.state==='open'&&f.priority==='high'?'warning':''}">${esc(f.state==='open'?f.priority:f.state)}</span><span class="eyebrow">${esc(f.kind.replaceAll('_',' '))}</span></div><h2>${esc(f.title)}</h2>
    <div class="finding-impact"><p class="eyebrow">Why it matters to your goal</p><p>${esc(f.impact)}</p></div>
    <div class="evidence-heading"><h3>${icon('link')}Evidence <span>${f.citations.length} ${f.citations.length===1?'passage':'passages'}</span></h3></div><div class="quote-grid">${citations}</div>
    <p class="uncertainty">${icon('circle-help')}<span><strong>What’s uncertain</strong> ${esc(f.uncertainty)}</span></p>${f.decision_ids.length?`<details><summary>Linked earlier decisions</summary><p>${esc(f.decision_ids.join(', '))}</p></details>`:''}
    <section class="clarification-section"><h3>${esc(f.question)}</h3><p class="muted">${esc(f.next_action)}</p>${f.related_questions?.length?`<details><summary>Related questions</summary><ul>${f.related_questions.map(q=>`<li>${esc(q)}</li>`).join('')}</ul></details>`:''}<hr>

      ${f.suggested_assignee_id?`<p class="suggestion">Suggested owner: ${esc(userName(f.suggested_assignee_id))}. </p>`:''}
      <form data-form="assign" data-fid="${esc(f.id)}"><label for="owner-${esc(f.id)}">Who can clarify this?</label><div class="owner-row"><select id="owner-${esc(f.id)}" name="assignee_id">${userOptions(f.assignee_id)}</select><button class="secondary" ${disabled||!canAssign?'disabled':''}>Confirm assignee</button></div>${hint('One assignee; no message is sent.')}<details class="optional-people"><summary>Add collaborators or watchers <span>optional</span></summary><div class="two"><label>Optional collaborators<select name="collaborators" multiple>${multiUsers(f.collaborators)}</select></label><label>Optional watchers<select name="watchers" multiple>${multiUsers(f.watchers)}</select></label></div><p class="hint">Save with Confirm assignee.</p></details></form>
      <form data-form="respond" data-fid="${esc(f.id)}"><label for="answer-${esc(f.id)}">Answer from the context</label><select id="answer-${esc(f.id)}" name="choice" data-answer="${esc(f.id)}" required><option value="">Select a source statement</option>${f.citations.map((c,i)=>`<option value="${i}">${esc(c.quote.length>200?c.quote.slice(0,197)+'...':c.quote)}</option>`).join('')}<option value="other">Other</option></select>${hint('Select Other to write an answer.')}
        <div id="other-${esc(f.id)}" hidden><label for="custom-${esc(f.id)}">Your answer or explanation</label><textarea id="custom-${esc(f.id)}" name="answer"></textarea></div><label class="check"><input type="checkbox" name="unknown">Answer unknown; keep this open.</label><div class="action-row"><button ${disabled||!canRespond?'disabled':''}>Record response ${icon('arrow-right')}</button></div></form>
      ${responses}
      <form data-form="confirm" data-fid="${esc(f.id)}" class="confirmation-form"><h4>Confirm the decision</h4><label for="supersedes-${esc(f.id)}">Prior decision to supersede (optional)</label><select id="supersedes-${esc(f.id)}" name="supersedes"><option value="">Create a new decision</option>${r.memory.map(d=>`<option value="${esc(d.id)}">${esc(d.text)}</option>`).join('')}</select>${hint('A project or decision owner must confirm.')}<button class="secondary" ${disabled||!canConfirm?'disabled':''}>${icon('check')}Confirm resolution</button></form>
      ${f.confirmed?'<p class="confirmation-note">'+icon('shield-check')+'Confirmed and saved to project history.</p>':''}
      <details class="dismiss-option"><summary>Dismiss a false positive</summary><form data-form="dismiss" data-fid="${esc(f.id)}"><label>Why does this finding not apply?<textarea name="reason" minlength="5" required></textarea></label><button class="secondary" ${disabled||!canAssign?'disabled':''}>Dismiss with reason</button></form></details>${f.dismissal?`<p>Dismissed by ${esc(userName(f.dismissal.actor))}: ${esc(f.dismissal.reason)}</p>`:''}
    </section></article>`;
}
