import {test} from 'node:test';
import assert from 'node:assert/strict';
import {processingPanel,activeProcessing} from '../web/processing.js';
const escape=s=>String(s).replaceAll('<','&lt;').replaceAll('>','&gt;');
const state=(jobs=[],extra={})=>({project:'p1',data:{intakes:jobs},...extra});
const job=(extra={})=>({id:'j1',project_ids:['p1'],status:'routing',created:'2026-10-26T10:00:00Z',
  updated:'2026-10-26T10:01:00Z',units_total:325,units_processed:135,review_ids:[],...extra});
test('upload has immediate indeterminate progress, not a fabricated percentage',()=>{
  const html=processingPanel(state([],{pendingCapture:{started:new Date().toISOString(),files:6,projectId:'p1'}}),escape);
  assert.match(html,/Uploading and preparing documents/);assert.match(html,/6 documents selected/);
  assert.match(html,/<progress aria-label="Upload in progress"><\/progress>/);assert.doesNotMatch(html,/100%/);
});
test('routing counts explain their scope; completed matching does not claim a completed review',()=>{
  const html=processingPanel(state([job({status:'analyzing',units_processed:325,analysis_total:4,analysis_done:1})]),escape);
  assert.match(html,/325\/325 passages checked for project relevance/);assert.match(html,/1\/4 evidence-analysis batches/);
  assert.match(html,/review is still running/);assert.doesNotMatch(html,/Open review/);
});
test('failed partial results show retry, never a completed review link',()=>{
  const html=processingPanel(state([job({status:'failed',error:'Service <unavailable>',review_ids:['partial']})]),escape);
  assert.match(html,/Processing needs attention/);assert.match(html,/Retry retained input/);
  assert.match(html,/Service &lt;unavailable&gt;/);assert.doesNotMatch(html,/data-review=/);
});
test('project scope excludes other jobs and complete jobs expose their result',()=>{
  const jobs=[job({id:'other',project_ids:['p2']}),job({status:'complete',review_ids:['r1']})];
  assert.equal(activeProcessing(state(jobs)),undefined);
  const html=processingPanel(state(jobs),escape);
  assert.match(html,/Review complete/);assert.match(html,/data-review="r1"/);assert.doesNotMatch(html,/data-processing-job="other"/);
});
test('retry duration uses the attempt start and legacy timing has an honest label',()=>{
  const retried=job({status:'failed',created:'2026-10-26T06:46:00Z',attempt_started:'2026-10-26T10:31:00Z',updated:'2026-10-26T10:32:00Z'});
  const html=processingPanel(state([retried]),escape);
  assert.match(html,/Attempt duration/);assert.match(html,/>1:00<\/span>/);assert.doesNotMatch(html,/>226:00<\/span>/);
  delete retried.attempt_started;
  const legacy=processingPanel(state([retried]),escape);
  assert.match(legacy,/Since original upload/);assert.doesNotMatch(legacy,/Attempt duration/);
});
test('local network denial offers a normal-user restart rather than a credential reset',()=>{
  const html=processingPanel(state([job({status:'failed',error:'Muse Wonder: outbound connection denied by local Windows/network permissions'})]),escape);
  assert.match(html,/AI requests were blocked on this computer/);assert.match(html,/File Explorer/);
  assert.match(html,/normal Windows account/);assert.match(html,/Retry retained input/);
});
