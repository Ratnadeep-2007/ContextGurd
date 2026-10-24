// Full live flow using only the three public synthetic documents. Removes its own case.
import { createRequire } from 'node:module'
import { createHash } from 'node:crypto'
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const require = createRequire(resolve('frontend/package.json'))
const { chromium, expect } = require('@playwright/test')
const base = process.env.CONTEXTGUARD_URL || 'http://127.0.0.1:8017'
const folder = 'artifacts/release-verification'
await mkdir(folder, { recursive: true })
const result = { checked_at: new Date().toISOString(), checks: [], page_errors: [], live_status: 'not_run' }
const browser = await chromium.launch({ channel: 'msedge', headless: true })
let page, caseId
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, permissions: ['clipboard-read', 'clipboard-write'] })
  page = await context.newPage()
  page.on('pageerror', error => result.page_errors.push(error.message))
  const config = await (await page.request.get(`${base}/api/config`)).json()
  result.providers = config.providers
  await page.goto(base)
  await page.getByRole('button', { name: 'New review', exact: true }).click()
  await expect(page.getByLabel('Review name', { exact: true })).toBeVisible()
  caseId = await page.evaluate(() => localStorage.getItem('contextguard.active'))
  result.case_id = caseId
  await page.getByLabel('Review name', { exact: true }).fill('Release verification - three synthetic Synora documents')
  await page.getByLabel('What are you deciding?', { exact: true }).fill("What needs clarification before we commit to Synora's pilot scope, launch target, connector work, and operating budget?")
  await page.getByLabel('Scope', { exact: true }).fill('Assess timeline, security approval, connector dependencies, specification versions, acceptance wording, and budget assumptions. These three documents are synthetic. Distinguish dependent WhatsApp work from independent dashboard work.')
  const decisionSaved = page.waitForResponse(response => response.url().endsWith(`/api/cases/${caseId}`) && response.request().method() === 'PUT')
  await page.getByRole('button', { name: 'Save decision', exact: true }).click()
  expect((await decisionSaved).status()).toBe(200)
  await expect(page.locator('.upload-zone')).toBeEnabled()
  const files = (await readdir('samples/synora-three-docs')).filter(name => name.endsWith('.md')).sort()
  expect(files).toHaveLength(3)
  for (const [index, name] of files.entries()) {
    await page.getByLabel('Upload source file').setInputFiles(resolve('samples/synora-three-docs', name))
    await expect(page.getByText(`${index + 1} / 8 sources`, { exact: true })).toBeVisible({ timeout: 35000 })
  }
  const load = async () => (await page.request.get(`${base}/api/cases/${caseId}`)).json()
  let review = await load()
  for (const source of review.sources) {
    expect(source.status).toBe('ready')
    expect(source.content_hash).toBe(createHash('sha256').update(await readFile(resolve('samples/synora-three-docs', source.name))).digest('hex'))
  }
  const hashes = review.sources.map(source => source.content_hash)
  result.checks.push('Three actual files uploaded via browser; readable passages and exact file hashes verified')
  if (!config.live_available) throw new Error('No live provider is configured.')
  async function finishRun() {
    const until = Date.now() + 500000
    let stage
    do {
      review = await load()
      if (review.run?.stage !== stage) {
        stage = review.run?.stage
        console.log(JSON.stringify({ stage }))
      }
      if (review.run?.status !== 'running') return review
      await new Promise(resolve => setTimeout(resolve, 1200))
    } while (Date.now() < until)
    throw new Error('Review exceeded the verification deadline.')
  }
  const started = page.waitForResponse(response => response.url().endsWith('/analyze') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Review the evidence', exact: true }).click()
  expect((await started).status()).toBe(202)
  await finishRun()
  result.live_status = review.run?.status
  await writeFile(`${folder}/initial-live-case.json`, JSON.stringify(review, null, 2))
  if (review.run?.status !== 'completed') throw new Error(review.run?.error || 'Live review did not complete.')
  await expect(page.locator('.report-caption')).toBeVisible()
  result.traces = review.report.traces
  result.rejected_count = review.report.rejected_count
  const passages = new Map(review.sources.flatMap(source => source.passages.map(passage => [passage.id, passage.text])))
  const normalize = text => text.replace(/\s+/g, ' ').trim()
  for (const item of review.report.evidence) expect(normalize(passages.get(item.passage_id) || '')).toContain(normalize(item.quote))
  const findingText = f => [f.title, f.question, ...review.report.evidence.filter(e => f.evidence_ids.includes(e.id)).map(e => e.quote)].join('\n')
  const expected = {
    pilot_dates: text => /December 7, 2026/.test(text) && /January 18, 2027/.test(text),
    security_approval: text => /security/i.test(text) && /approv|sign.off/i.test(text),
    budget_assumption: text => /quota|budget/i.test(text) && /zero|free|cost/i.test(text),
    whatsapp_dependency: text => /WhatsApp/i.test(text) && /pending|not connected|authorization/i.test(text),
    outdated_specification: text => /live.caption|appendix v1/i.test(text) && /retired|v2|replac/i.test(text),
    ambiguous_acceptance: text => /fast|the team|processing delay|external client/i.test(text),
  }
  result.coarse_seed_coverage = Object.fromEntries(Object.entries(expected).map(([name, match]) => [name, review.report.findings.some(f => match(findingText(f)))]))
  result.coverage_note = 'Coarse topic checks of cited report content; manual review of meaning and negative controls is still required.'
  result.findings = review.report.findings
  const dateFinding = review.report.findings.find(f => expected.pilot_dates(findingText(f)))
  if (!dateFinding) throw new Error('The report missed the planted pilot-date disagreement.')
  await page.locator('.finding-item').filter({ hasText: dateFinding.title }).click()
  const answer = page.getByRole('combobox', { name: 'Choose an answer', exact: true })
  await expect(page.locator('.resolution-form select')).toHaveCount(1)
  await expect(answer.locator('option').last()).toHaveText('Other')
  await page.getByLabel('Who can clarify this?', { exact: true }).fill('Synthetic verification lead')
  const selectedChoice = dateFinding.clarification_choices.find(choice => choice.kind === 'source' && /January 18, 2027/.test(choice.answer))
  if (!selectedChoice) throw new Error('The date question did not offer the supplied January target as a source answer.')
  await answer.selectOption(selectedChoice.id)
  await page.locator('.resolution-form').screenshot({ path: `${folder}/live-answer.png` })
  const saved = page.waitForResponse(response => response.url().endsWith('/resolutions') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Save & recheck', exact: true }).click()
  expect((await saved).status()).toBe(202)
  await finishRun()
  result.recheck_status = review.run?.status
  await writeFile(`${folder}/clarified-live-case.json`, JSON.stringify(review, null, 2))
  if (review.run?.status !== 'completed') throw new Error(review.run?.error || 'Live clarification recheck did not complete.')
  const recorded = review.resolutions.at(-1)
  expect(recorded.answer).toBe(selectedChoice.answer)
  expect(recorded.owner).toBe('Synthetic verification lead')
  const resolved = review.report.findings.find(f => f.id === dateFinding.id)
  expect(resolved?.status, 'Selected finding must retain its identity and user decision after a real recheck').toBe('user_confirmed')
  expect(review.sources.map(source => source.content_hash)).toEqual(hashes)
  await page.reload()
  await expect(page.locator('.report-caption')).toBeVisible()
  await page.getByRole('button', { name: 'Prepare brief', exact: true }).click()
  await expect(page.getByLabel('Brief text', { exact: true })).toHaveValue(/Synthetic verification lead/)
  await page.getByRole('button', { name: 'Copy brief', exact: true }).click()
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download Markdown', exact: true }).click()
  await (await download).saveAs(`${folder}/live-kickoff-brief.md`)
  await page.getByRole('button', { name: 'Done', exact: true }).click()
  await page.screenshot({ path: `${folder}/live-report.png`, fullPage: true })
  result.checks.push('Live analysis, citation checks, source answer, recheck, persisted decision/owner, immutable sources, reload, real copy/download brief')
  expect(result.page_errors).toEqual([])
  result.passed = Object.values(result.coarse_seed_coverage).every(Boolean)
  if (!result.passed) throw new Error('One or more seeded topics were not represented; inspect the recorded report.')
} catch (error) {
  result.passed = false
  result.error = error.message
  process.exitCode = 1
  if (page) await page.screenshot({ path: `${folder}/live-attempt.png`, fullPage: true }).catch(() => {})
} finally {
  if (caseId && page) {
    try {
      let current = await (await page.request.get(`${base}/api/cases/${caseId}`)).json()
      if (current.run?.status === 'running') {
        await page.request.post(`${base}/api/cases/${caseId}/cancel`)
        current = await (await page.request.get(`${base}/api/cases/${caseId}`)).json()
      }
      const deleted = await page.request.delete(`${base}/api/cases/${caseId}`, { data: { version: current.version } })
      result.own_test_case_removed = deleted.ok()
    } catch { result.own_test_case_removed = false }
  }
  await writeFile(`${folder}/live-results.json`, JSON.stringify(result, null, 2))
  console.log(JSON.stringify(result, null, 2))
  await browser.close()
}
