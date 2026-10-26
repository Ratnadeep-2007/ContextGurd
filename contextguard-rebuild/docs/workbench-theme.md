# Workbench theme - October 26, 2026

The later user-selected [Claude Amber palette](claude-amber-theme.md) supersedes this earlier graphite/cobalt color direction. Layout and verification history below are retained.

User direction: change the theme and design; use solid colors, square components and concise functional text.

## Implemented

- Charcoal sidebar with a left rule for the selected page and divided recent reviews.
- Cool paper background, white work areas, cobalt primary actions and neutral secondary controls. Amber/red retain their status meaning.
- Consistent native Segoe UI Variable Text / Segoe UI for headings and body text; Tahoma/Arial/system sans-serif fallbacks on other devices. No external font requests or dependencies.
- Square buttons, panels, fields, badges, menus and notices. No gradients or decorative shadows.
- Project selection framed above capture, distinct section headings, divided review rows and compact filter areas.
- Responsive source/review layouts and keyboard focus indicators preserved. Existing reduced-motion support remains.
- Sign-in text describes the actual evidence checking task.

## Verification

Browser verification uses a fresh isolated SQLite database and fictional providers; no real connectors, model requests or user records are involved. Results and screenshots are stored under ignored artifacts/workbench-theme/. All 12 grouped browser journeys passed with zero page errors, including source controls, document upload, cited fixture review, resolution, exports, role restrictions, retry and 390px navigation/layout. Desktop Sources and mobile library screenshots were visually inspected. Additional computed-style checks on Project Reviews, Sources and Team found no visible elements with rounded corners or gradient backgrounds. This design work does not establish live processing success or learner approval.

## Try it

Refresh the running app to load the stylesheet and presentation module. If the old styling is cached, press Ctrl+F5. No backend restart or frontend build is required for these visual changes.
