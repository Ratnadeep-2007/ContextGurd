import { useId } from 'react'
import type { ClarificationChoice, Review } from '../types'

export function ClarificationAnswer({ choices, selected, onSelect, answer, onAnswer, review, disabled }: {
  choices: ClarificationChoice[]
  selected: string
  onSelect: (value: string) => void
  answer: string
  onAnswer: (value: string) => void
  review: Review
  disabled: boolean
}) {
  const id = useId()
  const choice = choices.find(item => item.id === selected)
  const sourceChoices = choices.filter(item => item.kind === 'source')
  const decisions = choices.filter(item => item.kind === 'decision')
  const refs = review.report!.evidence.filter(e => choice?.evidence_ids.includes(e.id))
  const locations = refs.flatMap(e => review.sources.flatMap(source => source.passages.filter(p => p.id === e.passage_id).map(p => `${source.name} - ${p.location}`)))
  const guide = choice?.action === 'unknown' ? 'This saves your response and keeps the question open.'
    : choice?.action === 'dismiss' ? 'This records your relevance decision. It can be undone in History.'
    : choice?.action === 'accept_risk' ? 'This records your choice to proceed; the underlying gap stays visible.'
    : 'Choose an answer for the question above. Select Other to write a different answer.'
  return <div className="clarification-answer">
    <label className="field" htmlFor={id}>Choose an answer</label>
    <select id={id} aria-describedby={`${id}-guide`} value={selected} onChange={e => onSelect(e.target.value)} disabled={disabled} required>
      <option value="" disabled>Select an answer</option>
      {sourceChoices.length > 0 && <optgroup label="From the supplied sources">{sourceChoices.map(item => <option value={item.id} key={item.id}>{item.label}</option>)}</optgroup>}
      <optgroup label="How to handle this finding">{decisions.map(item => <option value={item.id} key={item.id}>{item.label}</option>)}</optgroup>
      <option value="other">Other</option>
    </select>
    <p className="guide" id={`${id}-guide`}>{guide}</p>
    {choice?.kind === 'source' && <div className="selected-source-context"><p>{choice.answer.replace(/\*\*|`/g, '')}</p><small>{[...new Set(locations)].join('; ')}</small></div>}
    {selected === 'other' && <label className="field custom-answer">Your answer<textarea aria-label="Your answer" value={answer} onChange={e => onAnswer(e.target.value)} disabled={disabled} required maxLength={3000} rows={3} placeholder="Write the answer or clarification the team should follow." /><small>Your answer is saved in this review. The original documents stay unchanged.</small></label>}
  </div>
}
