# Claude Amber light theme

The current selected design is [Graphite & Cobalt](graphite-cobalt-theme.md); this file retains earlier theme history.

The user selected the Claude Amber accent and then explicitly requested a white theme. The original screenshot supplied the terracotta primary and destructive red; surfaces and text were adapted to light mode. This supersedes the earlier dark implementation.

| Token | Hex |
|---|---|
| Primary | #d97757 |
| Secondary | #f2f0eb |
| Accent | #f5eee8 |
| Muted | #f6f5f1 |
| Destructive | #ef4444 |
| Border | #dedbd4 |
| Card | #ffffff |
| Background | #faf9f5 |

`web/theme.css` owns semantic color tokens and component color states. `web/style.css` retains typography, geometry and responsive layout. The screenshot's rounded-radius examples were not adopted: the user's square-corner requirement remains in force. Native Segoe UI typography remains; the request selects the palette rather than introducing an Outfit dependency. Flat fills only, no gradients or decorative shadows.

Warm-white backgrounds, white cards, dark text and warm-gray secondary text provide the light theme. Terracotta buttons retain dark text for contrast; error messages use darker red on pale red. Native form controls use the light color scheme. WhatsApp QR codes retain their necessary white background for scanning.

## Verification

Earlier checks below describe the dark version; the light follow-up is recorded separately after verification.

Browser checks use a fresh isolated database and controlled fictional providers. All 12 grouped browser journeys passed with zero page errors. Desktop Sources/report and mobile Sources screenshots were inspected. Computed-style checks on Project Reviews, Sources and Team confirmed the selected tokens load and visible elements have square corners with no gradient backgrounds. Results and desktop/mobile screenshots are saved under artifacts/claude-amber-theme/. This theme change does not claim live processing or connector success. Refresh the running app with Ctrl+F5 to load the new stylesheet; no backend restart is needed for CSS changes.


## Light-theme follow-up

Computed-style checks passed for Project Reviews, Sources and Team: light palette loaded, square corners and no gradients. Targeted 390px navigation and overflow checks passed for all three screens; desktop Sources and mobile Project Reviews were visually inspected. The full browser run reached its final mobile navigation step but timed out locating Sources, so it is not recorded as a complete 12-journey pass for this light revision. Separate mobile navigation rechecks passed without an implementation change. Whitespace validation passed. These checks used isolated fictional data; the user database was not changed.
