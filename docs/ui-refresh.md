# UI refresh — original ContextGuard as visual reference

The user requested that the fresh `contextguard-rebuild` UI be inspired by the original ContextGuard in the outer directory. This is visual inspiration, not a code migration. The original app remains unchanged.

## Evidence captured and inspected

The local Edge harness captured the current outer app at 1440×1050 and the rebuild's authentication, review setup and report. All rebuild operations used fictional data in an isolated artifact database at port 8037. The normal project database was not touched. No live provider/source operation ran during UI checks.

Accepted before captures: `artifacts/ui-refresh/00-original-reference.png`, `01-auth-before.png`, `02-home-before.png`, `03-report-before.png`.

Accepted after captures: `04-auth-after.png`, `05-home-after.png`, `06-report-after.png`, `06-report-after-full.png`, `07-home-mobile-after.png`. `comparison.png` places the original and rebuild welcome screens together at matching source viewports; it was visually inspected. The comparison HTML is local/ignored. Artifact filenames are relative to `artifacts/ui-refresh/`.

## Observations and resulting changes

1. **Sign-in — healthy after refresh.** A readable account form remains, with local privacy guidance; an editorial heading and restrained two-column composition introduce the product. No authentication behavior changed.
2. **Review setup — healthy after refresh.** The former form-first view lacked the original's hierarchy and welcome context. The new ivory/sage shell, serif heading, fictional evidence illustration and three-step guide lead into the existing goal/source form. Source permissions and transfer consent remain explicit.
3. **Report — healthy after refresh.** The former report repeated six large forms in one very long page. A findings index now sits beside one selected detail, with All/Needs attention/Recorded filters, priority/state, exact passages, uncertainty, owner-first clarification, Other answer and separate authorized confirmation. Optional collaborators/watchers are collapsed; context and responsibilities are retained.
4. **Mobile — healthy in tested journey.** Navigation is available through a labeled drawer, supports Escape/focus restoration, and the report stacks into list/detail. Checks include 390px horizontal overflow, keyboard finding selection and the complete answer/confirmation/export path.

## Implementation and resources

`web/views.js` is the independent presentation layer. `web/app.js` retains network commands/state and adds selected-finding/filter/mobile-navigation state. `web/style.css` is freshly written. DM Sans and Lucide are standard library resources with bundled upstream licenses; no old application source or asset bundle is copied. Every component uses solid colors; no gradient or external CDN is introduced.

The underlying schemas, permissions, route/memory gates, provider behavior and resolution authority are unchanged. User content still passes through the existing escaping function, external links still require HTTP(S), and no source content enters an SVG/icon definition.

## Verification and limits

The revised browser journey passed nine grouped checks with zero page errors: account setup, six fixture findings/selected detail, click/keyboard selection, Other/response/confirmation, filters, download, reload, unknown routing and mobile layout. This is functional and visual evidence, not a complete screen-reader/accessibility audit. Real model/source integrations remain separately unverified. Screenshots and fictional test data remain ignored; no remote publication is implied by this local UI change.
