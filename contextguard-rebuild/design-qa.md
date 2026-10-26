# Graphite & Cobalt design QA

## Visual truth and environment

- Selected source: docs/ui-concepts/01-graphite-cobalt.png, an exact copy of the user-selected generated image exec-81ef3b83-3816-4a80-ae7e-c336598d1a3b.png.
- Implementation: artifacts/graphite-cobalt/report-desktop.png.
- Viewport and pixel dimensions: source 1536 x 1024; implementation 1536 x 1024 CSS/pixels, deviceScaleFactor 1. No density normalization or browser chrome is included.
- State: fictional Synora, six sources, five unresolved findings, pilot date selected, opposing December 7 / January 18 passages, no approved decision. Initial desktop capture occurs before response mutation. Later tablet/mobile screenshots include one explicitly fictional response; the finding remains open.
- Full-view source and implementation were opened together for visual comparison. Focused evidence/resolution comparison uses artifacts/graphite-cobalt/source-detail.png and implementation-detail.png. Sidebar-detail.png and report-mobile.png were inspected separately. Tablet screenshot: report-tablet.png.
- Browser: local Edge through the existing project Playwright harness. No connected in-app Browser surface is exposed in this session. Existing FastAPI/native-module application was preserved; no prototype scaffold or deployment was introduced.

## Findings and iteration history

1. [P1, fixed] Opening a report inherited the review library scroll offset and clipped the heading/project selector. Fixed openReview to reset scroll to the top. The browser check now asserts scrollY is zero; final full-view evidence includes the complete header.
2. [P2, fixed] Repeated impact/type/citation metadata and an export toolbar pushed the source comparison and response controls down. Preserved full details but moved impact/type/next action into a supplemental disclosure, moved exports after the report, combined finding priority/provenance into a compact footer and put filters in a working heading menu. Final desktop capture shows all five issue rows and the main response action within the reference-height viewport.
3. [P2, fixed] Source blocks had redundant vertical padding and undersized source headings. Stacked full-width source blocks, enlarged quote/body text, added ruled filename headers, moved original-source actions into the headers and retained actual supplied author/time metadata. Focused source/detail comparison confirms readable exact quotes.
4. [P2, fixed] The mobile back button became visually blank because the previous icon name was unavailable and compact styling hides its text. Restored a bundled folder-open icon and a 44px mobile control. Mobile verification explicitly asserts that icon is visible.
5. [P2, fixed] Final desktop response button initially extended two pixels below the 1024px capture. Reduced repeated form margins without removing unknown-answer or assignment controls. The browser now asserts the response button bottom stays inside the reference viewport.

## Required fidelity surfaces

- Fonts/typography: native Segoe UI with clear sans-serif heading hierarchy. Report question, 18px source passages, 16px filenames and enlarged navigation are legible. Source raster uses slightly different glyph widths; this is a P3 precision difference, not an unavailable-font fallback. Long real text wraps, retains exact content and can extend the document naturally.
- Spacing/layout: 280px dark sidebar at full reference width, 32px workspace inset, approximately 35% findings index, ruled source headers and paired desktop resolution fields. Compact/mobile layouts stack without horizontal overflow. Persistent header, project control, evidence and primary response action remain visible in the reference-sized fixture.
- Colors/tokens: cobalt #2549a2, sidebar #20252d, paper #f3f4f7, white cards and pale blue selection. Native controls have visible focus. Computed checks found no rounded visible components or gradient fills. Flat CSS replaces the incidental shading in the generated reference, as explicitly required by the user.
- Image/asset quality: no photographic/decorative raster assets are present in the target. The text wordmark and closest matching bundled Lucide icon set remain sharp. No substitute illustrations, div art, handcrafted icons or placeholder imagery were added.
- Copy/content: real goal, source/finding counts and workflow status come from stored review data. Question-first detail, source filenames and exact passages remain linked. Explanations are available without repeated headings. No mockup theme caption, invented score or fabricated connection result appears in the app.

## Intentional production constraints

The reference omits separate assignee confirmation, unknown-answer state, authorized decision confirmation and detailed exports. Those working features are retained. Supplemental controls and longer real content can extend below the simplified reference. Recording a response still does not confirm a decision. Filters and original-source actions remain available through compact controls. Fixture speaker/source statements are explicitly fictional, and this preview does not certify live semantic detection.

## Verification

- Dedicated reference browser checks passed: same-viewport five-finding report, exact opposing quotes, palette/geometry, opening scroll, primary action geometry, finding/filter selection, Other input, persisted response and real report download.
- 768px tablet and 390px mobile layouts, overflow checks and actual Sources navigation passed.
- All 12 existing grouped browser journeys passed on a separate fresh database, including capture, roles, separate authorized confirmation, exports, source controls and retained-input retry.
- Six processing UI tests and JavaScript/Python syntax/whitespace checks passed. Browser console errors: zero.
- Existing user records, keys and normal source connections were not used or changed.

## Implementation checklist

- [x] Match selected palette, square geometry and report hierarchy.
- [x] Compare full view and focused evidence/resolution regions.
- [x] Fix all actionable P0/P1/P2 issues and capture again.
- [x] Exercise primary controls and responsive layouts.
- [x] Synchronize Devpost scope, PRD, spec and checklist.

## Follow-up polish

P3 only: native font rasterization and library icon glyphs differ slightly from the generated bitmap. This implementation follows the selected visual direction while preserving the actual application workflow; it is not claimed to be a pixel-identical raster recreation. Final learner preference remains open.

final result: passed
