import { createRequire } from 'node:module'
import { createHash } from 'node:crypto'
import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

// Runs the six real files through the browser and local API. No model mocks.
const require = createRequire(resolve('frontend/package.json'))
const { chromium, expect } = require('@playwright/test')
const base = process.env.CONTEXTGUARD_URL || 'http://127.0.0.1:8017'
const target = 'artifacts/synora-review'
await mkdir(target, { recursive: true })
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const results = { checked_at: new Date().toISOString(), checks: [], errors: [], live_detection: 'not_run' }
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } })
  page.on('pageerror', error => results.errors.push(error.message))
  await page.goto(base)
  await page.getByRole('button', { name: 'New review', exact: true }).click()
  await page.getByLabel('Review name', { exact: true }).fill('Synora · six-source review test')
  await page.getByLabel('What are you deciding?', { exact: true }).fill('What scope and decisions need clarification before the next Synora development phase?')
  await page.getByLabel('Scope', { exact: true }).fill('Review input channels, memory approval behavior, and rollout timing. These are synthetic draft documents; do not infer approval or a whole-project blocker.')
  const saved = page.waitForResponse(r => r.url().includes('/api/cases/') && r.request().method() === 'PUT')
  await page.getByRole('button', { name: 'Save decision', exact: true }).click()
  const initial = await (await saved).json()
  results.case_id = initial.id
  const files = (await readdir('synora-review-pack')).filter(name => /^0[1-6]-.*\.md$/.test(name)).sort()
  expect(files).toHaveLength(6)
  for (const [index, name] of files.entries()) {
    await page.getByLabel('Upload source file').setInputFiles(resolve('synora-review-pack', name))
    await expect(page.getByText(`${index + 1} / 8 sources`, { exact: true })).toBeVisible({ timeout: 35000 })
  }
  await page.reload()
  await expect(page.getByText('6 / 8 sources', { exact: true })).toBeVisible()
  const storedResponse = await page.request.get(`${base}/api/cases/${initial.id}`)
  const stored = await storedResponse.json()
  expect(stored.sources).toHaveLength(6)
  for (const source of stored.sources) {
    const raw = await readFile(resolve('synora-review-pack', source.name))
    expect(source.status).toBe('ready')
    expect(source.content_hash).toBe(createHash('sha256').update(raw).digest('hex'))
    const original = raw.toString('utf8').split(/\n\s*\n/).map(x => x.trim()).filter(Boolean)
    expect(source.passages.map(p => p.text)).toEqual(original)
  }
  results.checks.push('Six actual browser uploads, ready parser status, exact text and hashes, persisted after reload')
  await page.getByRole('button', { name: /^Sources 6$/ }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.locator('.passages article').first()).toBeVisible()
  await page.getByRole('button', { name: 'Done', exact: true }).click()
  results.checks.push('Extracted source passages render in the source dialog')
  const config = await (await page.request.get(`${base}/api/config`)).json()
  results.providers = config.providers
  const run = page.getByRole('button', { name: 'Review the evidence', exact: true })
  if (!config.live_available) {
    await expect(run).toBeDisabled()
    const response = await page.request.post(`${base}/api/cases/${stored.id}/analyze`, { data: { version: stored.version } })
    expect(response.status()).toBe(400)
    results.live_detection = 'blocked_no_provider'
    results.api_message = (await response.json()).detail
    results.checks.push('Missing provider disables live review; direct API request fails honestly with HTTP 400')
  } else {
    const started = page.waitForResponse(r => r.url().endsWith('/analyze'))
    await run.click()
    expect((await started).status()).toBe(202)
    let current
    const until = Date.now() + 500000
    do {
      current = await (await page.request.get(`${base}/api/cases/${stored.id}`)).json()
      if (current.run?.status !== 'running') break
      await new Promise(resolve => setTimeout(resolve, 1500))
    } while (Date.now() < until)
    results.live_detection = current.run?.status || 'unknown'
    results.run = current.run
    await writeFile(`${target}/case-output.json`, JSON.stringify(current, null, 2))
    if (current.run?.status === 'completed') {
      await expect(page.locator('.report-caption')).toBeVisible({ timeout: 10000 })
      results.findings = current.report.findings
      results.rejected_count = current.report.rejected_count
      results.traces = current.report.traces
      const topics = [
        ['pilot_timing', text => /December 7, 2026/.test(text) && /January 18, 2027/.test(text)],
        ['canvas_direction', text => /not ingested|do not flow back|read-only/i.test(text) && /Saved canvas edits will be imported|changes are an input too/i.test(text)],
        ['requirement_approval', text => /must remain pending|member approval is needed/i.test(text) && /updates to existing requirements/i.test(text)],
      ]
      results.seeded_disagreement_checks = Object.fromEntries(topics.map(([name, matches]) => [name,
        current.report.findings.some(f => ['potential_conflict', 'clarification_needed'].includes(f.type) && matches(
          current.report.evidence.filter(e => f.evidence_ids.includes(e.id)).map(e => e.quote).join('\n')
        ))
      ]))
      results.detection_check_note = 'Coarse checks of cited text for the three seeded topics; human review of meaning, draft status, and impact is still required.'
      if (Object.values(results.seeded_disagreement_checks).some(found => !found)) process.exitCode = 1
      const brief = await page.request.get(`${base}/api/cases/${stored.id}/brief`)
      expect(brief.status()).toBe(200)
      await writeFile(`${target}/kickoff-brief.md`, await brief.text())
      results.checks.push('Live workflow completed, report rendered, Markdown brief exported')
    } else {
      await expect(page.getByText('The review stopped.', { exact: true })).toBeVisible({ timeout: 10000 })
      const brief = await page.request.get(`${base}/api/cases/${stored.id}/brief`)
      expect(brief.status()).toBe(400)
      results.checks.push('Failed run is visible in the browser and cannot export a nonexistent report')
      process.exitCode = 1
    }
  }
  await page.screenshot({ path: `${target}/browser-output.png`, fullPage: true })
  if (results.live_detection === 'blocked_no_provider') await writeFile(`${target}/case-output.json`, JSON.stringify(stored, null, 2))
  expect(results.errors).toEqual([])
} catch (error) {
  results.failure = error.message
  process.exitCode = 1
} finally {
  await writeFile(`${target}/results.json`, JSON.stringify(results, null, 2))
  console.log(JSON.stringify(results, null, 2))
  await browser.close()
}
