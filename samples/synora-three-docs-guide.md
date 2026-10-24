# How to try the three-document Synora sample

Upload only the three Markdown files in `samples/synora-three-docs/` into one new review. They are a fictional scenario, not approved real Synora decisions. Do not upload this guide as evidence.

Project: **Synora**.

Goal: **What needs clarification before we commit to Synora's pilot scope, launch target, connector work, and operating budget?**

Scope: **Review timeline, security approval, connector dependencies, current specification versions, acceptance wording, and budget assumptions. Distinguish dependent connector work from the independent dashboard and source-preview work.**

## Cases intentionally represented

| Case | Evidence to compare | Intended next question |
|---|---|---|
| Potential conflict | December 7 baseline versus January 18 meeting target | Which pilot launch date is authoritative? |
| Missing information | Security approval is required; no approver or completed record is supplied | Who approves it, and where is the approval record? |
| Unsupported assumption | Zero AI budget/free quotas versus a requirement to assess volume, quotas, and cost | Is the zero-cost assumption supported, or should it be removed? |
| Unresolved dependency | WhatsApp task ready to start while connection and authorization are pending | What must be completed before WhatsApp work starts? |
| Possibly outdated | Current task cites retired v1 live-caption behavior despite v2 replacement | Should the task be updated to the completed-transcript path? |
| Clarification needed | “Fast updates” and “the team” have no agreed meaning | What delay and user audience should acceptance tests use? |

## Controls

- All three documents consistently keep Excalidraw read-only. There should be no invented canvas-direction conflict.
- The current v2 spec explicitly supersedes v1. The old task is an outdated-reference issue, not proof that two equally current specifications conflict.
- Only WhatsApp ingestion is dependent on its connection/authorization. The whole project, dashboard, and source preview should not be called blocked.
- Missing approval means not found in these supplied documents; it does not prove no approval exists elsewhere.

The model may combine related issues or choose another appropriate finding label. These are intended coverage checks, not a guarantee that six separate labels will appear. Inspect the cited passages and uncertainty.
