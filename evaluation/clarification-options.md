# Clarification choices and final output

## Implemented behavior

- The form starts with Who can clarify this?, followed by one Choose an answer dropdown. It includes available source answers and context-specific decisions; Other is the final option and opens a required custom-answer field. The separate action dropdown and radio cards were removed.
- Choice text must occur in each referenced verified quote, and option references must belong to the finding. Generated text without that support is discarded. Existing conflict reports can use their exact verified statements as fallback choices. Missing information does not produce invented people, approvals, or dates.
- No answer is preselected for a new response. The native select supports keyboard selection. A saved choice is restored when the finding is reopened. The selected source statement and its location appear below the dropdown when applicable.
- Contextual choices have server-defined IDs, actions, and response text. Keeping missing information or a dependency pending leaves it open; accepting risk keeps the gap visible. A client cannot forge a choice ID or change its action to confirm something else.
- The API validates that a submitted option is currently available, ignores conflicting custom text when a valid option is selected, and records the selected text, evidence IDs, stable passage IDs, owner, time, and source fingerprint in local SQLite history.
- Custom answers use the same history and user-assertion boundary. The source files remain unchanged. Memory applies to this review and matching inputs, rather than all projects automatically.
- The exported brief separates recorded clarifications from open decisions and accepted risks. It includes counts, answers, owners, selected source statements/locations, evidence, coverage, and limitations.

## Checks executed

**80 backend tests passed** after the form revision. Regressions cover invalid generated options, selection persistence/provenance, forged options and inappropriate actions, context-specific handling for all six finding types, keeping missing information open, accepted-risk status, and an all-clarified brief.

**TypeScript and production build passed.** The React changes were checked for stable state initialization, native form semantics, disabled behavior, and source text escaping.

**Nine existing browser checks passed** after the dropdown revision. The custom-answer path now selects Other explicitly.

The dedicated browser journey (`node scripts/browser-clarification-check.mjs`) passed with no page errors:

1. Open the fictional sample, check the owner field appears first, and verify the form has exactly one dropdown, no radios, no initial selection, and Other last.
2. Select by keyboard, switch to Other, enter custom text, then choose a source option; the custom textbox disappears and its text is not submitted.
3. Save/recheck/reload and confirm the choice, owner, and passage provenance persist.
4. Clarify the remaining three findings using Other and verify source hashes stay unchanged.
5. Prepare and download a brief showing four user-confirmed clarifications and zero unanswered findings, while retaining evidence and limits.
6. Check the options at 390px with no horizontal overflow.
7. Reopen history and undo the source choice.

Evidence: `artifacts/clarification-options/results.json`, `source-options-desktop.png`, `source-options-mobile.png`, `all-clarified-brief.png`, and `all-clarified-brief.md`. Screenshots and exported brief were inspected.

The revised form is also captured in `owner-first-dropdown.png` and `other-custom-answer.png`. The three new documents in `samples/synora-three-docs/` all passed the actual isolated parser. The generated reviews were then removed through the API at the user's request; the workspace was checked empty, with the Synora project retained for the user's fresh review. Cleanup counts are recorded in `artifacts/review-cleanup.json`.

## Limit of verification

The browser journey uses explicitly labeled fictional fixture replay and tests the actual API, verifier, database, UI, and export. It is not a live model detection or option-quality score. Real-provider generation of the newly requested concise options remains unverified because outbound provider calls from this session are denied by local network permissions.
