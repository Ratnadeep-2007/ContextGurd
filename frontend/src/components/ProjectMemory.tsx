import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { ArrowUpRight, RefreshCw } from 'lucide-react'
import { api, date } from '../api'
import type { MemoryRecall, Project, Review } from '../types'

export function ProjectPicker({ value, onChange, disabled }: { value: string; onChange: (value: string) => void; disabled: boolean }) {
  const hint = useId()
  const [projects, setProjects] = useState<Project[]>([])
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    let cancelled = false
    void api<Project[]>('/projects').then(rows => {
      if (!cancelled) setProjects(existing => [...rows, ...existing.filter(p => !rows.some(row => row.id === p.id))])
    }).catch(e => { if (!cancelled) setError(e.message) })
    return () => { cancelled = true }
  }, [])
  async function create() {
    if (!name.trim()) return
    setBusy(true); setError('')
    try {
      const project = await api<Project>('/projects', 'POST', { name: name.trim() })
      setProjects(rows => [...rows, project]); onChange(project.id); setName('')
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return <div className="project-picker">
    <label className="field">Project<select aria-label="Project" aria-describedby={hint} value={value} onChange={e => onChange(e.target.value)} disabled={disabled || busy}>
      <option value="">Separate review · no project memory</option>
      {projects.map(project => <option key={project.id} value={project.id}>{project.name}</option>)}
    </select><small id={hint}>Choose the same project to recall decisions from earlier reviews. Save the decision below to apply your selection.</small></label>
    <details className="project-create"><summary>Create a project</summary><label className="field">New project name<input value={name} onChange={e => setName(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); void create() } }} maxLength={100} disabled={disabled || busy} placeholder="For example, Synora" /></label><button type="button" className="button secondary" disabled={disabled || busy || !name.trim()} onClick={() => void create()}>{busy ? 'Creating…' : 'Create project'}</button><p className="guide">Give related reviews a shared home for their recorded decisions.</p></details>
    {error && <p role="alert" className="inline-error">{error}</p>}
  </div>
}

export function ProjectMemoryPanel({ review, openReview }: { review: Review; openReview: (id: string) => void }) {
  const [memory, setMemory] = useState<MemoryRecall | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const request = useRef(0)
  const load = useCallback(async () => {
    const id = ++request.current
    setLoading(true); setError('')
    try {
      const next = await api<MemoryRecall>(`/cases/${review.id}/memory`)
      if (id === request.current) setMemory(next)
    } catch (e) { if (id === request.current) setError((e as Error).message) }
    finally { if (id === request.current) setLoading(false) }
  }, [review.id])
  useEffect(() => {
    void load()
    return () => { request.current += 1 }
  }, [load, review.project_id, review.resolutions.length, review.report?.created_at])
  return <section className="panel project-memory" aria-label="Earlier project decisions">
    <div className="row-between"><div><p className="eyebrow">PROJECT MEMORY</p><h2>Earlier project decisions <span>{memory?.decisions.length ?? 0}</span></h2></div><button className="text-button" disabled={loading} onClick={() => void load()}><RefreshCw size={14} />Refresh earlier decisions</button></div>
    <p className="guide">Review what was clarified before. A previous answer does not automatically settle a new disagreement.</p>
    {error && <p role="alert" className="inline-error">{error}</p>}
    {loading && !memory ? <p className="guide" role="status">Looking for earlier clarifications…</p> : memory?.decisions.length ? <div className="memory-decisions">{memory.decisions.map(decision => <article className="memory-decision" key={decision.id}>
      <div className="row-between"><h3>{decision.title}</h3><span className="tiny-badge">Earlier user clarification</span></div><p className="memory-answer">{decision.answer}</p><p className="guide">{decision.case_title} · {date(decision.created_at)} · {decision.owner || 'Owner unassigned'}</p>
      {decision.sources.length > 0 && <details><summary>Source references</summary>{decision.sources.map((source, index) => <div className="memory-source" key={`${source.passage_id}-${index}`}><strong>{source.name} · {source.location}</strong><blockquote>{source.quote}</blockquote></div>)}</details>}
      <button className="text-button" onClick={() => openReview(decision.case_id)}>Open earlier review <ArrowUpRight size={13} /></button><small className="guide">Inspect the answer, its history, and the original context.</small>
    </article>)}</div> : <p className="memory-empty">No earlier clarifications in this project yet. Answers recorded here can be recalled in its next review.</p>}
    {memory && <p className="guide memory-notice">{memory.notice} {!memory.index.configured && 'Recall is running locally; Mem0 search is not connected.'}</p>}
  </section>
}
