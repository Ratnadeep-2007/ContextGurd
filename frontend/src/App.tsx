import { useCallback, useEffect, useRef, useState } from 'react'
import { ArrowRight, BookOpen, Check, ChevronRight, CircleHelp, FileCheck2, FileText, FolderOpen, History, LoaderCircle, Menu, Plus, RefreshCw, Settings2, ShieldCheck, SlidersHorizontal, Trash2, X } from 'lucide-react'
import { api, date } from './api'
import type { Config, Review, Summary } from './types'
import { Dialog } from './components/Dialog'
import { ProjectMemoryPanel } from './components/ProjectMemory'
import { CriteriaEditor, Setup, SourcePreview } from './components/Setup'
import { BriefDialog, HistoryDialog, ReportView } from './components/Report'

type Panel = 'sources' | 'criteria' | 'settings' | 'history' | 'brief' | 'delete' | null
const stages = ['Planning checks', 'Finding source evidence', 'Challenging assumptions', 'Verifying source references']

export default function App() {
  const [reviews, setReviews] = useState<Summary[]>([])
  const [review, setReview] = useState<Review | null>(null)
  const [config, setConfig] = useState<Config | null>(null)
  const [panel, setPanel] = useState<Panel>(null)
  const [sourceId, setSourceId] = useState<string>()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [initializing, setInitializing] = useState(true)
  const [edit, setEdit] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)
  const activeId = useRef<string | null>(null)
  const requestId = useRef(0)
  const refreshList = useCallback(() => api<Summary[]>('/cases').then(setReviews), [])
  const apply = useCallback((r: Review) => { activeId.current = r.id; setReview(r); localStorage.setItem('contextguard.active', r.id); void refreshList().catch(() => {}) }, [refreshList])

  const receive = useCallback((r: Review) => {
    if (activeId.current === r.id) apply(r)
    else void refreshList().catch(() => {})
  }, [apply, refreshList])

  useEffect(() => {
    let cancelled = false
    async function initialize() {
      try {
        const [cfg, list] = await Promise.all([api<Config>('/config'), api<Summary[]>('/cases')])
        if (cancelled) return
        setConfig(cfg); setReviews(list)
        const id = localStorage.getItem('contextguard.active')
        if (id && list.some(x => x.id === id)) {
          const r = await api<Review>(`/cases/${id}`)
          if (!cancelled) { activeId.current = id; setReview(r) }
        }
      } catch (e) { if (!cancelled) setError((e as Error).message) } finally { if (!cancelled) setInitializing(false) }
    }
    void initialize()
    return () => { cancelled = true }
  }, [])

  const running = review?.run?.status === 'running'
  useEffect(() => {
    if (!running || !review) return
    const id = review.id
    let cancelled = false
    const timer = setInterval(() => {
      void api<Review>(`/cases/${id}`).then(r => { if (!cancelled && activeId.current === id) { setReview(r); if (r.run?.status !== 'running') void refreshList().catch(() => {}) } }).catch(e => { if (!cancelled) setError(e.message) })
    }, 700)
    return () => { cancelled = true; clearInterval(timer) }
  }, [running, review?.id, refreshList])

  async function attempt(action: () => Promise<void>) {
    setBusy(true); setError('')
    try { await action() } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  function create(sample = false) {
    void attempt(async () => { const r = await api<Review>(sample ? '/cases/sample' : '/cases', 'POST', sample ? undefined : { title: 'Untitled review', goal: 'Are we ready to start development?', scope: '' }); apply(r); setEdit(false); setMobileNav(false); if (sample) apply(await api<Review>(`/cases/${r.id}/analyze`, 'POST', { version: r.version })) })
  }
  function open(id: string) {
    const request = ++requestId.current
    void attempt(async () => { const r = await api<Review>(`/cases/${id}`); if (request === requestId.current) { apply(r); setEdit(false); setMobileNav(false) } })
  }
  function run() {
    if (review) void attempt(async () => { apply(await api<Review>(`/cases/${review.id}/analyze`, 'POST', { version: review.version })); setEdit(false) })
  }
  function preview(id: string) { setSourceId(id); setPanel('sources') }
  const locked = busy || !!running
  const hasReport = !!review?.report
  const showSetup = review && (!hasReport || edit)

  return <div className="app-shell"><a className="skip-link" href="#main-content">Skip to review</a>
    <aside className={`sidebar ${mobileNav ? 'mobile-open' : ''}`} aria-label="Workspace navigation"><div className="brand"><span className="brand-mark"><ShieldCheck size={24} strokeWidth={1.6} /></span><span>ContextGuard<span className="brand-sub">Project evidence, in context.</span></span><button className="mobile-close icon-button" aria-label="Close navigation" onClick={() => setMobileNav(false)}><X size={18} /></button></div><div className="workspace-label"><span className="workspace-icon">P</span><div><strong>Personal workspace</strong><small>Local · only on this device</small></div></div><div className="nav-heading"><span>WORKSPACE</span><span className="version-label">01</span></div><button className="nav-active" disabled={busy} onClick={() => { requestId.current += 1; setReview(null); activeId.current = null; localStorage.removeItem('contextguard.active'); setMobileNav(false) }} title="Return to the review overview."><FolderOpen size={18} />Project reviews<span>{reviews.length.toString().padStart(2, '0')}</span></button><p className="nav-guide">Review the evidence behind your next decision.</p>
      <div className="saved-heading"><span>RECENT REVIEWS</span><button aria-label="Create a new review" className="icon-button" disabled={busy} onClick={() => create()} title="Start a separate case with its own goal and sources."><Plus size={16} /></button></div><div className="saved-reviews">{reviews.length ? reviews.map(r => <button key={r.id} className={review?.id === r.id ? 'active' : ''} onClick={() => open(r.id)} disabled={busy} title="Reopen this review with its sources, findings, and saved answers."><FileCheck2 size={16} /><span><strong>{r.title}</strong><small>{r.mode === 'sample' ? 'Fictional sample' : `${r.source_count} sources`} · {date(r.updated_at)}</small></span>{review?.id === r.id && <span className="active-dot" />}</button>) : <p className="guide saved-empty">Your saved reviews will appear here. Start with the sample or your own sources.</p>}</div>
    </aside>
    <div className="workspace"><header className="topbar"><div className="breadcrumb"><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setMobileNav(true)}><Menu size={20} /></button><FolderOpen size={15} /><span>Workspace</span><ChevronRight size={13} /><strong>Project reviews</strong></div><div className="topbar-actions"><span className="local-indicator"><span />Local workspace</span><button className="topbar-settings" aria-label="Providers & privacy" onClick={() => setPanel('settings')} title="See provider configuration and privacy details."><Settings2 size={16} /><span>Providers &amp; privacy</span></button></div></header>
      <main id="main-content" tabIndex={-1}><div className="page-top"><div><p className="eyebrow">MAKE ROOM FOR CLEARER DECISIONS</p><h1>{review ? review.title === 'Untitled review' ? 'A new perspective.' : review.title : 'Before the work begins.'}</h1><p className="page-description">{review ? 'Check the evidence. Clarify what matters. Leave with a plan for the conversation.' : 'Turn scattered project documents into the questions worth asking.'}</p></div><div className="new-review-action"><button className="button secondary" disabled={busy} onClick={() => create()}><Plus size={16} />New review</button><span className="guide">Start a separate decision check.</span></div></div>
        {error && <div className="error-banner" role="alert"><CircleHelp size={19} /><p>{error}</p><button className="text-button" onClick={() => setError('')} title="Dismiss this message. Saved inputs are not affected.">Dismiss</button></div>}
        {initializing ? <div className="loading-state" role="status"><LoaderCircle className="spin" />Opening your workspace…</div> : !review ? <><section className="welcome"><div className="welcome-copy"><span className="pill"><span />EVIDENCE BEFORE ASSUMPTIONS</span><h2>Know what needs<br />clarifying before kickoff.</h2><p>A proposal says one thing. The meeting notes say another. Find the gaps before they become work.</p><div className="welcome-actions"><div><button className="button primary" disabled={busy} onClick={() => create(true)}>Try a sample review <ArrowRight size={17} /></button><p className="guide">See a fictional case. No API key needed.</p></div><div><button className="text-button" disabled={busy} onClick={() => create()}>Use my own sources <ChevronRight size={15} /></button><p className="guide">Add your goal, documents, and notes.</p></div></div></div><div className="welcome-example"><div className="example-heading"><span className="eyebrow">A TYPICAL KICKOFF QUESTION</span><FileText size={18} /></div><p className="example-question">“Are we ready to<br />start development?”</p><div className="example-quote"><span>PROPOSAL · PAGE 2</span><p>“The final release is November 15.”</p></div><div className="example-quote"><span>MEETING NOTES · PARAGRAPH 3</span><p>“Release is discussed for November 20.”</p></div><div className="example-answer"><span className="status-dot important" /><p>One milestone, two dates.<br /><strong>Which one is authoritative?</strong></p></div><small>Illustration only. Context and versions may explain the difference.</small></div></section><section className="how-it-works"><div><span>01</span><h3>Bring the context</h3><p>A goal and the documents you already use.</p></div><div><span>02</span><h3>Find the open decisions</h3><p>See specific findings beside their evidence.</p></div><div><span>03</span><h3>Prepare the conversation</h3><p>Clarify a gap and copy your kickoff brief.</p></div></section><div className="welcome-foot"><ShieldCheck size={17} /><p>A second look at your evidence. The final decision is always yours.</p><span>BUILT FOR THE MOMENT BEFORE KICKOFF</span></div></> : <>
          <section className="review-toolbar"><div className="review-mode"><span className={`pill ${review.mode === 'sample' ? 'sample' : ''}`}><span />{review.mode === 'sample' ? 'FICTIONAL SAMPLE' : 'YOUR REVIEW'}</span><span>{review.mode === 'sample' ? 'Fixture replay · no live AI' : 'Sources saved on this device'}</span></div><div className="toolbar-actions"><button onClick={() => { setSourceId(undefined); setPanel('sources') }} disabled={!review.sources.length} title="Read the extracted passages and parsing warnings."><FileText size={15} />Sources <span>{review.sources.length}</span></button><button onClick={() => setPanel('criteria')} disabled={locked} title="Include or exclude suggested checks with a reason."><SlidersHorizontal size={15} />Review checks</button><button onClick={() => setPanel('history')} title="Read saved user choices and undo them."><History size={15} />History</button></div></section><p className="toolbar-guide guide">Open Sources to inspect the extracted text, Review checks to refine the scope, or History to revisit saved choices.</p>
          {running && <section className="progress-panel" role="status" aria-live="polite"><div><LoaderCircle size={21} className="spin" /><div><strong>{review.run?.stage}</strong><p>{review.mode === 'sample' ? 'Replaying the sample and verifying its source references.' : 'Checking your supplied sources. You can keep this page open or return later.'}</p></div></div><ol>{stages.map((s, i) => { const at = stages.indexOf(review.run!.stage); return <li key={s} className={i <= at ? 'done' : ''}><span>{i < at ? <Check size={12} /> : i + 1}</span>{s}</li> })}</ol><div className="action-row"><button className="text-button" disabled={busy} onClick={() => void attempt(async () => apply(await api<Review>(`/cases/${review.id}/cancel`, 'POST')))}>Cancel review</button><span className="guide">Stop applying this run. A provider request already sent may still finish.</span></div></section>}
          {(review.run?.status === 'failed' || review.run?.status === 'cancelled') && <div role="alert" className="error-banner"><CircleHelp size={20} /><p><strong>The review stopped.</strong> {review.run.error} {review.report && 'The report below is from the previous successful run.'}</p></div>}
          {review.project_id && review.mode === 'live' && <ProjectMemoryPanel key={`${review.id}-${review.project_id}`} review={review} openReview={open} />}
          {showSetup && <Setup key={review.id} review={review} config={config} onChange={receive} run={run} busy={locked} preview={preview} />}
          {hasReport && !edit && <><div className="decision-strip"><div><p className="eyebrow">THE DECISION</p><h2>{review.goal}</h2>{review.scope && <p>{review.scope}</p>}</div><div className="report-controls"><div><button className="button secondary" disabled={locked} onClick={run}><RefreshCw size={15} />Recheck</button><small className="guide">Run the checks again.</small></div><div><button className="button primary" disabled={locked || (review.run?.status === 'failed' || review.run?.status === 'cancelled')} onClick={() => setPanel('brief')}><BookOpen size={16} />Prepare brief</button><small className="guide">Copy questions for kickoff.</small></div></div></div><ReportView review={review} onChange={receive} busy={locked} preview={preview} /><div className="review-footer"><button className="text-button" disabled={locked} onClick={() => setEdit(true)} title="Return to source and goal setup. Changes require a new review."><Settings2 size={15} />{review.mode === 'sample' ? 'Inspect sample setup' : 'Edit goal & sources'}</button><span className="guide">Inspect the inputs behind this report.</span><button className="text-button danger-text" disabled={locked} onClick={() => setPanel('delete')}><Trash2 size={14} />Delete review</button><span className="guide">Permanently remove this local case.</span></div></>}
        </>}
        <footer className="page-footer"><span>ContextGuard</span><p>Evidence you can inspect. Decisions you control.</p><button onClick={() => setPanel('settings')} title="Read provider configuration, retention, and review limitations.">About this workspace <ChevronRight size={12} /></button></footer>
      </main>
    </div>
    {panel === 'sources' && review && <Dialog title="Source documents" description="These are the extracted passages used by the review. Parsing limitations remain visible." onClose={() => setPanel(null)} wide><SourcePreview key={sourceId || 'all'} sources={review.sources} selectedId={sourceId} /></Dialog>}
    {panel === 'criteria' && review && <Dialog title="Review checks" description="Keep the analysis relevant to your goal. Suggestions are not project obligations." onClose={() => setPanel(null)}><CriteriaEditor review={review} disabled={locked} onSave={async criteria => { apply(await api<Review>(`/cases/${review.id}/criteria`, 'PUT', { version: review.version, criteria })); setPanel(null) }} /></Dialog>}
    {panel === 'history' && review && <HistoryDialog review={review} onChange={receive} busy={locked} close={() => setPanel(null)} />}
    {panel === 'brief' && review && <BriefDialog review={review} close={() => setPanel(null)} />}
    {panel === 'settings' && <Dialog title="Providers & privacy" description="This is a local, single-user workspace. You control which providers are configured." onClose={() => setPanel(null)}><section className="settings-section"><h3>AI connection</h3>{config?.providers.length ? config.providers.map(p => <div className="provider-row" key={p.name}><span className="status-dot ready" /><strong>{p.name}</strong><code>{p.model}</code><span className="tiny-badge">Key configured</span></div>) : <p className="notice">No API keys configured. The fictional sample is available; your own sources need a live provider.</p>}<p className="guide">A configured key has not necessarily been validated against its provider.</p><p>Create a root <code>.env</code> from <code>.env.example</code>, add <code>MODEL_API_KEY</code> for Meta, and restart the server. Optional fallbacks use <code>GROQ_API_KEY</code> and <code>NVIDIA_API_KEY</code>.</p></section><section className="settings-section"><h3>Project memory</h3><p>Clarified answers can be recalled by later reviews assigned to the same project. They remain user statements with their original source references. Undo, input changes, and deletion remove them from active recall.</p><p>{config?.project_memory?.configured ? 'Mem0 indexing is configured. Recorded answers and project metadata may be sent to that service; current local records validate every recalled result.' : 'Earlier decisions can be recalled locally. To connect a Mem0 OSS service, configure MEM0_BASE_URL and its optional MEM0_API_KEY in .env, then restart.'}</p><h3>What leaves this device</h3><p>The sample makes no AI calls. A live review sends your goal and extracted excerpts to configured providers. Meta is tried first, followed by enabled fallbacks. You can disable fallbacks in your review setup.</p><h3>What stays saved</h3><p>Extracted text, reports, and answers stay in the local SQLite database. Original uploaded file bytes are not retained. Delete a review to remove its saved case; deleting it does not erase any provider logs or external backups.</p><h3>What a review can establish</h3><p>It can identify evidence gaps in readable sources. It cannot certify truth, approve a project, or assess documents that failed to parse. User answers remain user assertions.</p></section><div className="notice">Use fictional or non-sensitive data until you have reviewed your providers’ data policies. This app has no multi-user account system and should stay on localhost.</div></Dialog>}
    {panel === 'delete' && review && <Dialog title="Delete this review?" description="This permanently removes the saved case, extracted sources, report, and decision history from this workspace." onClose={() => setPanel(null)}><div className="action-row"><button className="button destructive" disabled={locked} onClick={() => void attempt(async () => { await api(`/cases/${review.id}`, 'DELETE', { version: review.version }); setReview(null); activeId.current = null; localStorage.removeItem('contextguard.active'); setPanel(null); await refreshList() })}><Trash2 size={16} />Delete permanently</button><span className="guide">This cannot be undone. Close this panel to keep the review.</span></div></Dialog>}
  </div>
}
