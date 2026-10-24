import { useEffect, useId, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'

export function Dialog({ title, description, onClose, children, wide = false }: { title: string; description: string; onClose: () => void; children: ReactNode; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null)
  const id = useId()
  useEffect(() => {
    const dialog = ref.current!
    const previous = document.activeElement as HTMLElement | null
    dialog.showModal()
    return () => { dialog.close(); previous?.focus() }
  }, [])
  return <dialog ref={ref} className={`dialog ${wide ? 'wide' : ''}`} aria-labelledby={id} aria-describedby={`${id}-desc`} onCancel={onClose}>
    <div className="dialog-heading"><div><p className="eyebrow">CONTEXTGUARD / WORKSPACE</p><h2 id={id}>{title}</h2><p id={`${id}-desc`} className="muted">{description}</p></div><button className="icon-button" onClick={onClose} aria-label="Close dialog" title="Close this panel and return to your review."><X size={20} /></button></div>
    {children}
    <div className="dialog-footer"><span className="guide">Close this panel to return to the review.</span><button className="button secondary" onClick={onClose}>Done</button></div>
  </dialog>
}
