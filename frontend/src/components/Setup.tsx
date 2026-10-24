import { useRef, useState } from 'react'
import { ArrowRight, Check, ChevronDown, FileText, Plus, Upload } from 'lucide-react'
import { api } from '../api'
import type { Config, Criterion, Review, Source } from '../types'
import { ProjectPicker } from './ProjectMemory'

export function CriteriaEditor({ review, onSave, disabled }: { review: Review; onSave: (criteria: Criterion[]) => Promise<void>; disabled: boolean }) {
  const [items, setItems] = useState(() => review.criteria.map(x => ({ ...x })))
  const [error, setError] = useState('')
  return <form onSubmit={e => { e.preventDefault(); setError(''); if (!items.some(x => !x.excluded)) { setError('Keep at least one check included.'); return } void onSave(items).catch(e => setError(e.message)) }}>
    <p className="guide">These are suggested checks, not mandatory project requirements. Exclude a check with a reason to keep the review relevant.</p>
    <div className="criteria-list">{items.map((c, i) => <div className="criterion" key={c.id}><label className="check-label"><input type="checkbox" checked={!c.excluded} onChange={e => setItems(xs => xs.map((x, j) => j === i ? { ...x, excluded: !e.target.checked } : x))} /><span><strong>{c.title}</strong><small>{c.description}</small></span><span className="tiny-badge">{c.origin}</span></label>{c.excluded && <label className="field exclusion">Reason for excluding<input required maxLength={500} value={c.exclusion_reason} onChange={e => setItems(xs => xs.map((x, j) => i === j ? { ...x, exclusion_reason: e.target.value } : x))} placeholder="For example, release planning is outside this review." /></label>}</div>)}</div>
    {error && <p role="alert" className="inline-error">{error}</p>}
    <div className="action-row"><button className="button primary" disabled={disabled}>Save checks <Check size={16} /></button><span className="guide">Save the scope of this review. Existing results will need a new run.</span></div>
  </form>
}

export function SourcePreview({ sources, selectedId }: { sources: Source[]; selectedId?: string }) {
  const [selected, setSelected] = useState(selectedId || sources[0]?.id || '')
  const source = sources.find(x => x.id === selected)
  return <><div className="source-tabs" aria-label="Choose a source to preview">{sources.map(s => <button key={s.id} className={s.id === selected ? 'selected' : ''} onClick={() => setSelected(s.id)} title={`Read the extracted text from ${s.name}.`}><FileText size={15} />{s.name}<span>{s.status === 'ready' ? 'Readable' : 'Failed'}</span></button>)}</div>
    {source ? <><div className="source-meta"><span className="tiny-badge">{source.kind.toUpperCase()}</span><span>{source.passages.length} passages · original extraction</span></div>{source.warnings.map(w => <p className="notice" key={w}>{w}</p>)}<div className="passages">{source.passages.map(p => <article key={p.id}><p className="eyebrow">{p.location}</p><p>{p.text}</p><code>{p.id}</code></article>)}</div></> : <p className="empty-small">No sources yet. Upload a file or paste your notes.</p>}</>
}

export function Setup({ review, config, onChange, run, busy, preview }: { review: Review; config: Config | null; onChange: (review: Review) => void; run: () => void; busy: boolean; preview: (id: string) => void }) {
  const [title, setTitle] = useState(review.title)
  const [goal, setGoal] = useState(review.goal)
  const [scope, setScope] = useState(review.scope)
  const [projectId, setProjectId] = useState(review.project_id || '')
  const [fallback, setFallback] = useState(review.allow_fallback)
  const [paste, setPaste] = useState(false)
  const [name, setName] = useState('Meeting notes')
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const sample = review.mode === 'sample'
  const liveEnabled = !!config?.providers.some(p => p.name === 'meta' || fallback)
  const dirty = title !== review.title || goal !== review.goal || scope !== review.scope || fallback !== review.allow_fallback || projectId !== (review.project_id || '')
  const locked = busy || saving
  async function perform(action: () => Promise<Review>) {
    setError(''); setSaving(true)
    try { onChange(await action()); return true } catch (e) { setError((e as Error).message); return false } finally { setSaving(false) }
  }
  async function saveGoal() { await perform(() => api(`/cases/${review.id}`, 'PUT', { version: review.version, title, goal, scope, project_id: projectId || null, allow_fallback: fallback })) }
  async function upload(file: File) {
    if (file.size > 8 * 1024 * 1024) { setError('Choose a file smaller than 8 MB.'); return }
    const form = new FormData(); form.append('file', file)
    await perform(() => api(`/cases/${review.id}/sources/upload?version=${review.version}`, 'POST', form))
  }
  return <div className="setup-grid"><section className="panel setup-main"><div className="section-title"><span className="step-number">01</span><div><h2>The decision</h2><p className="guide">Tell us what you need to decide. The goal determines which gaps matter.</p></div></div>
    <form onSubmit={e => { e.preventDefault(); void saveGoal() }}>
      <label className="field">Review name<input value={title} readOnly={sample} maxLength={120} required onChange={e => setTitle(e.target.value)} /></label>
      {!sample && <ProjectPicker value={projectId} onChange={setProjectId} disabled={locked} />}
      <label className="field">What are you deciding?<textarea aria-label="What are you deciding?" value={goal} readOnly={sample} required minLength={5} maxLength={1000} rows={2} onChange={e => setGoal(e.target.value)} /></label>
      <label className="field">Scope <span className="optional">optional</span><textarea aria-label="Scope" value={scope} readOnly={sample} maxLength={2000} rows={2} placeholder="For example, the first sprint only. Deployment is outside this review." onChange={e => setScope(e.target.value)} /><small>Include boundaries that should change which findings matter.</small></label>
      {!sample && <><label className="check-label fallback-check"><input type="checkbox" checked={fallback} onChange={e => setFallback(e.target.checked)} /><span>Allow configured fallback providers<small>Excerpts may go to Groq or NVIDIA if the primary provider fails.</small></span></label><div className="action-row"><button className="button secondary" disabled={locked || !dirty}>Save decision <Check size={15} /></button><span className="guide">Save any goal changes before running the review.</span></div></>}
      {sample && <p className="notice">This fictional sample has fixed inputs. Start a new review to use your own documents.</p>}
    </form>
    <div className="section-title sources-title"><span className="step-number">02</span><div><h2>The evidence</h2><p className="guide">Add the brief, requirements, or notes you already have.</p></div><span className="tiny-badge">{review.sources.length} / 8 sources</span></div>
    <div className="source-list">{review.sources.map((s, i) => <div className="source-row" key={s.id}><span className={`file-icon file-${i % 3}`}><FileText size={20} /></span><button className="source-name" onClick={() => preview(s.id)} title="Preview the exact extracted passages before analysis."><strong>{s.name}</strong><small>{s.status === 'ready' ? `${s.passages.length} passages · preview source` : 'Could not read · inspect the error'}</small></button><span className={`status-dot ${s.status}`} /><span className="source-state">{s.status === 'ready' ? 'Ready' : 'Failed'}</span>{!sample && <button className="text-button danger-text" disabled={locked} onClick={() => void perform(() => api(`/cases/${review.id}/sources/${s.id}`, 'DELETE', { version: review.version }))} title="Remove this source and invalidate its previous analysis.">Remove</button>}</div>)}</div>
    {!sample && <><input type="file" ref={fileInput} className="sr-only" accept=".pdf,.docx,.txt,.md" aria-label="Upload source file" onChange={e => { const file = e.target.files?.[0]; if (file) void upload(file); e.target.value = '' }} /><button className="upload-zone" disabled={locked || review.sources.length >= 8} onClick={() => fileInput.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); const file = e.dataTransfer.files[0]; if (file && !locked) void upload(file) }}><Upload size={22} /><strong>Choose a file or drop it here</strong><span>PDF, DOCX, TXT, or MD · up to 8 MB · 30 pages per PDF</span></button><div className="paste-toggle"><button className="text-button" onClick={() => setPaste(!paste)} aria-expanded={paste} disabled={locked}><Plus size={15} /> Paste notes instead <ChevronDown size={14} /></button><span className="guide">Use text when a file is unavailable or scanned.</span></div>
      {paste && <form className="paste-form" onSubmit={e => { e.preventDefault(); void perform(() => api(`/cases/${review.id}/sources/text`, 'POST', { version: review.version, name, text })).then(saved => { if (saved) setText('') }) }}><label className="field">Source name<input value={name} required maxLength={180} onChange={e => setName(e.target.value)} /></label><label className="field">Source text<textarea aria-label="Source text" rows={6} value={text} required maxLength={60000} onChange={e => setText(e.target.value)} placeholder="Paste the original notes, keeping dates and context intact." /></label><div className="action-row"><button className="button secondary" disabled={locked || !text.trim()}>Add notes</button><span className="guide">Preserve these notes as a separate source.</span></div></form>}
    </>}
    {error && <p role="alert" className="inline-error">{error}</p>}
  </section><aside className="setup-aside"><section className="panel review-outline"><p className="eyebrow">REVIEW OUTLINE</p><h3>A focused second look.</h3><p className="muted">We compare the evidence with your goal, then surface the decisions that need attention.</p><ol>{review.criteria.map(c => <li key={c.id}><span className={c.excluded ? 'muted strike' : ''}>{c.title}</span>{c.excluded ? <span className="tiny-badge">Excluded</span> : <Check size={15} />}</li>)}</ol><p className="guide">These checks are suggestions. You can change them from Review checks above.</p><div className="outline-bottom"><span className="eyebrow">THE OUTPUT</span><p>Source-linked findings.<br />Specific questions.<br />A brief for your kickoff.</p></div></section>
    <div className="run-box"><button className="button primary large" onClick={run} disabled={locked || dirty || !review.sources.some(s => s.status === 'ready') || (!sample && !liveEnabled)}>{sample ? 'Run sample review' : 'Review the evidence'}<ArrowRight size={18} /></button><p className="guide">{dirty ? 'Save the decision above before starting.' : sample ? 'Replay the fictional case. No documents are sent to an AI provider.' : liveEnabled ? 'Send readable source excerpts to your configured AI providers.' : 'Configure the Meta API key in .env, or enable a configured fallback, then restart the server.'}</p></div>
  </aside></div>
}
