import { useEffect, useState } from 'react'
import { ArrowDownToLine, ArrowRight, Check, CircleAlert, Copy, FileText, GitBranch, History, Link2, List, Quote, RotateCcw } from 'lucide-react'
import { api, date, getBrief, label } from '../api'
import type { Finding, Review } from '../types'
import { Dialog } from './Dialog'
import { ClarificationAnswer } from './ClarificationAnswer'

export function BriefDialog({ review, close }: { review: Review; close: () => void }) {
  const [text, setText] = useState('')
  const [message, setMessage] = useState('')
  useEffect(() => {
    let cancelled = false
    void getBrief(review.id).then(value => { if (!cancelled) setText(value) }).catch(e => { if (!cancelled) setMessage(e.message) })
    return () => { cancelled = true }
  }, [review.id])
  async function copy() {
    try { await navigator.clipboard.writeText(text); setMessage('Brief copied. Paste it into your kickoff notes or team channel.') }
    catch { setMessage('Clipboard access was unavailable. Select and copy the text below, or download it.') }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' }))
    const a = document.createElement('a'); a.href = url; a.download = 'contextguard-kickoff-brief.md'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
    setMessage('Brief downloaded. It includes source names, quotations, and review limitations.')
  }
  return <Dialog title="Your kickoff brief" description="Your recorded decisions, remaining questions, owners, and source references. Review this copy before sharing." onClose={close} wide><div className="brief-actions"><div><button className="button primary" disabled={!text} onClick={() => void copy()}><Copy size={16} /> Copy brief</button><p className="guide">Copy this text for your existing team workflow.</p></div><div><button className="button secondary" disabled={!text} onClick={download}><ArrowDownToLine size={16} /> Download Markdown</button><p className="guide">Save a portable copy with its source references.</p></div></div>{message && <p role="status" className="notice">{message}</p>}<label className="field">Brief text<textarea aria-label="Brief text" className="brief-text" rows={19} value={text} onChange={e => setText(e.target.value)} /><small>Edits here affect only this copy; they do not change your saved report.</small></label></Dialog>
}

export function HistoryDialog({ review, close, onChange, busy }: { review: Review; close: () => void; onChange: (r: Review) => void; busy: boolean }) {
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  async function undo(id: string) {
    setSaving(true); setError('')
    try { onChange(await api<Review>(`/cases/${review.id}/resolutions/${id}/undo`, 'POST', { version: review.version })); close() } catch (e) { setError((e as Error).message) } finally { setSaving(false) }
  }
  return <Dialog title="Decision history" description="Answers stay separate from the source documents. Undo a choice to recheck it." onClose={close}><div className="history-list">{review.resolutions.length === 0 ? <p className="empty-small">No decisions recorded yet. Add an answer from a finding to start the history.</p> : [...review.resolutions].reverse().map(r => <article key={r.id}><div className="row-between"><span className="tiny-badge">{r.revoked ? 'Undone' : label(r.action)}</span><time>{date(r.created_at)}</time></div><p>{r.answer || 'Left unanswered.'}</p><small>Owner: {r.owner || 'Unassigned'} · User statement</small>{!r.revoked && <div className="action-row"><button className="text-button" disabled={busy || saving} onClick={() => void undo(r.id)}><RotateCcw size={14} /> Undo this choice</button><span className="guide">Reopen this issue and any newer answers to it.</span></div>}</article>)}</div>{error && <p role="alert" className="inline-error">{error}</p>}</Dialog>
}

function EvidenceMap({ finding, review, preview }: { finding: Finding; review: Review; preview: (id: string) => void }) {
  const evidence = review.report!.evidence.filter(x => finding.evidence_ids.includes(x.id))
  return <div className="evidence-map"><div className="map-node map-goal"><span className="eyebrow">YOUR DECISION</span><p>{review.goal}</p></div><span className="map-line" aria-hidden="true" /><div className="map-node map-issue"><span className="eyebrow">{label(finding.type)}</span><p>{finding.title}</p></div><div className="map-branches">{evidence.map(e => { const source = review.sources.find(s => s.passages.some(p => p.id === e.passage_id))!; const passage = source.passages.find(p => p.id === e.passage_id)!; return <button key={e.id} className="map-node" onClick={() => preview(source.id)}><FileText size={17} /><strong>{source.name}</strong><span>{passage.location} · source context</span><small>Open the original extracted passage.</small></button> })}</div><p className="guide">Lines link this finding to its source context. They do not establish causation or prove a claim.</p></div>
}

function FindingDetail({ finding: f, review, onChange, busy, preview }: { finding: Finding; review: Review; onChange: (r: Review) => void; busy: boolean; preview: (id: string) => void }) {
  const choices = f.clarification_choices || []
  const [view, setView] = useState('passages')
  const [answer, setAnswer] = useState(f.option_text ? '' : f.answer)
  const [selected, setSelected] = useState(() => {
    const saved = choices.find(choice => choice.id === f.choice_id) || choices.find(choice => choice.kind === 'source' && choice.answer === f.option_text)
    return saved?.id || (f.answer ? 'other' : '')
  })
  const [owner, setOwner] = useState(f.owner)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  async function save() {
    if (!selected) { setError('Choose an answer or select Other.'); return }
    setSaving(true); setError('')
    const choice = choices.find(item => item.id === selected)
    try { onChange(await api<Review>(`/cases/${review.id}/resolutions`, 'POST', { version: review.version, finding_id: f.id, action: choice?.action || 'confirm', answer: choice ? '' : answer, choice_id: choice?.id || '', owner })) } catch (e) { setError((e as Error).message) } finally { setSaving(false) }
  }
  const items = review.report!.evidence.filter(e => f.evidence_ids.includes(e.id))
  return <article className="finding-detail" aria-label="Selected finding"><div className="row-between"><span className={`badge ${f.priority}`}><span className="status-dot" />{label(f.priority)}</span><span className="eyebrow">{label(f.type)}</span></div><h2>{f.title}</h2><p className="explanation">{f.explanation}</p><div className="impact"><span className="eyebrow">WHY IT MATTERS</span><p>{f.impact}</p></div>
    <div className="evidence-heading"><h3><Link2 size={16} /> The evidence <span>{items.length} passages</span></h3><div className="view-switch" aria-label="Evidence view"><button className={view === 'passages' ? 'active' : ''} onClick={() => setView('passages')} aria-pressed={view === 'passages'} title="Compare the exact source quotations."><List size={15} /> Passages</button><button className={view === 'map' ? 'active' : ''} onClick={() => setView('map')} aria-pressed={view === 'map'} title="Trace this issue to its sources."><GitBranch size={15} /> Map</button></div></div>
    {view === 'map' ? <EvidenceMap finding={f} review={review} preview={preview} /> : <div className="quote-grid">{items.map((e, i) => { const source = review.sources.find(s => s.passages.some(p => p.id === e.passage_id))!; const passage = source.passages.find(p => p.id === e.passage_id)!; return <div className="quote-card" key={e.id}><div className="quote-source"><span className={`file-icon file-${i % 3}`}><FileText size={15} /></span><span><strong>{source.name.replace(/^0\d_/, '')}</strong><small>{passage.location}</small></span><Quote size={16} /></div><blockquote>{e.quote}</blockquote><button className="text-button" onClick={() => preview(source.id)} title="Read the full source text and its extraction limitations.">View source <ArrowRight size={13} /></button><p className="guide">Read this quote in its original context.</p></div> })}</div>}
    <p className="uncertainty"><CircleAlert size={15} /><span><strong>What’s uncertain</strong> {f.uncertainty}</span></p><div className="next-question"><p className="eyebrow">THE QUESTION TO RESOLVE</p><h3>{f.question}</h3><p>{f.recommended_action}</p></div>
    {f.status !== 'open' && <div className="recorded"><Check size={18} /><div><strong>{label(f.status)}</strong><p>{f.answer}</p><small>This records your choice. It is not independent verification.</small></div></div>}
    <form className="resolution-form" onSubmit={e => { e.preventDefault(); void save() }}>
      <h3>Clarify this finding</h3><p className="guide">Name the person who can clarify it, then choose the answer to record.</p>
      <label className="field">Who can clarify this? <span className="optional">optional</span><input aria-label="Who can clarify this?" value={owner} onChange={e => setOwner(e.target.value)} disabled={busy || saving} maxLength={120} placeholder="Name or role" /><small>Record an owner for the brief. No message is sent.</small></label>
      <ClarificationAnswer choices={choices} selected={selected} onSelect={value => { setSelected(value); setError('') }} answer={answer} onAnswer={setAnswer} review={review} disabled={busy || saving} />
      {error && <p className="inline-error" role="alert">{error}</p>}
      <div className="action-row"><button className="button primary" disabled={busy || saving}>{saving ? 'Saving...' : 'Save & recheck'}<ArrowRight size={16} /></button><span className="guide">Save this response and rerun the checks. You can undo it in History.</span></div>
    </form>
  </article>
}

export function ReportView({ review, onChange, busy, preview }: { review: Review; onChange: (r: Review) => void; busy: boolean; preview: (id: string) => void }) {
  const [selected, setSelected] = useState(review.report?.findings[0]?.id || '')
  const [filter, setFilter] = useState('all')
  const report = review.report!
  const open = report.findings.filter(f => f.status === 'open' || f.status === 'risk_accepted')
  const findings = report.findings.filter(f => filter === 'all' || (filter === 'open' ? f.status === 'open' || f.status === 'risk_accepted' : f.status !== 'open' && f.status !== 'risk_accepted'))
  const current = findings.find(f => f.id === selected) || findings[0]
  return <><div className="report-caption"><div><span className="report-mark"><Check size={16} /></span><span><strong>{open.length ? `${open.length} decisions need attention` : 'No open decisions in assessed checks'}</strong><small>{report.checks.filter(c => !c.excluded).length} checks included · {review.sources.filter(s => s.status === 'ready').length} readable sources · {date(report.created_at)}</small></span></div><p className="guide">This review supports your decision.<br />It does not approve the project.</p></div>
    {review.changes.length > 0 && <div className="change-note" role="status"><History size={17} /><div><strong>Updated after your review</strong>{review.changes.map(c => <p key={c}>{c}</p>)}</div></div>}
    <div className="report-grid"><section className="findings-panel"><div className="findings-heading"><p className="eyebrow">CONTEXT GAP REPORT</p><h2>What needs a second look<span>{report.findings.length.toString().padStart(2, '0')}</span></h2></div><div className="filter-tabs" aria-label="Filter findings">{[['all', 'All findings'], ['open', 'Needs attention'], ['closed', 'Recorded']].map(([value, title]) => <button key={value} onClick={() => setFilter(value)} className={filter === value ? 'active' : ''} aria-pressed={filter === value} title={`Show ${title.toLowerCase()} in this report.`}>{title}</button>)}</div>
      <div className="finding-list">{findings.length ? findings.map((f, i) => <button className={`finding-item ${current?.id === f.id ? 'selected' : ''}`} key={f.id} onClick={() => setSelected(f.id)} aria-pressed={current?.id === f.id} title="Read the evidence, impact, and next action for this finding."><div className="row-between"><span className={`text-tag ${f.priority}`}>{f.status === 'open' ? label(f.priority) : label(f.status)}</span><span className="finding-index">{(i + 1).toString().padStart(2, '0')}</span></div><h3>{f.title}</h3><p>{f.explanation}</p><div className="finding-footer"><span><Link2 size={13} />{f.evidence_ids.length} source passages</span><ArrowRight size={16} /></div></button>) : <div className="empty-small"><Check size={24} /><p>No findings in this view. Review coverage below before making a decision.</p></div>}</div>
      <details className="coverage"><summary>Check coverage <span>See what was assessed</span></summary>{report.checks.map(c => <div key={c.id}><strong>{c.title}</strong><small>{c.excluded ? `Excluded: ${c.exclusion_reason}` : report.evidence.some(e => e.check_id === c.id) ? 'Source evidence reviewed; inspect findings for uncertainty.' : 'Insufficient evidence; no conclusion.'}</small></div>)}</details>
    </section><section className="detail-panel">{current ? <FindingDetail key={`${current.id}-${report.created_at}`} finding={current} review={review} onChange={onChange} busy={busy} preview={preview} /> : <div className="empty-detail"><Check size={30} /><h2>No finding selected</h2><p>Choose a different filter or inspect the review coverage. No detected issue is not proof of readiness.</p></div>}</section></div>
    <details className="limitations"><summary>Review limits & provenance <span>Read before acting on the report.</span></summary><ul>{report.limitations.map(x => <li key={x}>{x}</li>)}</ul><div className="trace-grid">{report.traces.map((t, i) => <div key={`${t.role}-${i}`}><span className="eyebrow">{t.role}</span><strong>{t.provider === 'fixture' ? 'Fixture replay' : t.provider}</strong><small>{t.model}</small>{t.provider !== 'fixture' && <small>{(t.duration_ms / 1000).toFixed(1)}s · {t.input_tokens + t.output_tokens} tokens</small>}</div>)}</div></details>
  </>
}
