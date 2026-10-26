# Graphite & Cobalt implementation

The user selected the exact generated reference saved as [01-graphite-cobalt.png](ui-concepts/01-graphite-cobalt.png), superseding both Claude Amber variants. This applies to the existing ContextGuard rebuild, not a replacement application.

## Theme

| Surface | Color |
|---|---|
| Primary / actions | #2549a2 |
| Primary foreground | #ffffff |
| Background | #f3f4f7 |
| Card | #ffffff |
| Sidebar | #20252d |
| Foreground | #202735 |
| Muted foreground | #5d687a |
| Border | #d2d8e2 |
| Selection | #eaf0fc |

Native Segoe UI follows the reference's sans-serif typography without adding remote fonts. Solid colors and square corners remain mandatory. The wordmark is text, and standard icons reuse the bundled licensed Lucide sprite. There are no photographic or decorative image assets in the selected design, so no new raster assets or asset subagents were needed.

## Layout and behavior

- Desktop navigation is 280px wide at 1536px, with the account summary moved to the bottom.
- Project Reviews has a simple project selection row, followed by the actual goal and real source/finding/status summary.
- The findings index uses approximately 35% of the report width. One selected finding appears beside it. Filters remain available through a compact heading menu.
- The finding question is the main heading. Source blocks stack vertically with filenames in ruled headers; original-import controls remain accessible in each header.
- Resolution places accountable owner selection before the answer. Desktop fields align in two columns; mobile stacks them. Contextual Other still reveals the text field.
- Assignment confirmation, response, unknown-answer state, separate authorized decision confirmation and exports are retained. Extra production controls extend below the simplified visual reference where necessary.
- Supplemental impact, finding kind and next action move into an expandable Why this matters section.
- Opening a review now resets scroll to the top, preventing the previous library scroll position from hiding the report heading.

## Verification

`scripts/design_preview_server.py` creates a fresh ignored SQLite database and six fictional Synora sources with five controlled design findings; it never contacts model providers or connectors. Its fixture is for visual/workflow testing, not semantic detection certification. `scripts/browser-reference.mjs` checks the 1536x1024 report, actual source passages, selection/filter menu, Other/response persistence, report download, 768px/390px layout and mobile navigation. Results and screenshots live under artifacts/graphite-cobalt/.

All 12 existing grouped browser journeys passed on a separate fresh offline server, including real local document capture, assignment/decision authority and downloads. Six processing UI tests passed. Design QA and iteration evidence are recorded in [design-qa.md](../design-qa.md). No user records or credentials were used or changed.

The earlier light Claude Amber snapshot reached GitHub main at d65e3e0119a847d13378f065cf755636ccde7311. This Graphite & Cobalt revision is local until a subsequent publication request.
