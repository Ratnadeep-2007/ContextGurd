export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api' + path, {
    method,
    headers: body instanceof FormData || body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: 'The server did not respond. Check that it is running, then retry.' }))
    const detail = Array.isArray(data.detail) ? data.detail.map((x: { msg: string }) => x.msg).join('; ') : data.detail
    throw new Error(typeof detail === 'string' ? detail : 'The request could not be completed.')
  }
  return response.json() as Promise<T>
}

export async function getBrief(id: string) {
  const response = await fetch(`/api/cases/${id}/brief`)
  if (!response.ok) throw new Error('The brief is unavailable. Finish a review first.')
  return response.text()
}

export function label(text: string) { return text.replaceAll('_', ' ').replace(/^./, c => c.toUpperCase()) }
export function date(text: string) { return new Date(text).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) }
