# ContextGuard --- Complete Project Context & Build Blueprint

> **Implementation update ? 23 October 2026:** A new local application now exists in this workspace. See `README.md`, `devpost/checklist.md`, and `evaluation/results.md` for startup, verified behavior, and remaining live-AI checks. The original planning snapshot is preserved below; concept-stage status statements are historical. The evidence map uses native HTML/CSS rather than React Flow.

> **Purpose of this document:** This is the single source of context for
> a fresh ChatGPT conversation, teammate, or coding agent. It defines
> ContextGuard's problem, target users, final product, agentic workflow,
> architecture, MVP, reusable resources, evaluation, hackathon
> requirements, and implementation sequence.
>
> **Project name:** ContextGuard (working name; check name, domain, and
> trademark availability before public launch).
>
> **Project stage:** Product concept and planning. Features described
> here are planned, not already implemented.
>
> **Relationship to Synora:** The user has an existing project called
> Synora focused on project context/memory, multi-source ingestion,
> decision history, and shared project context. ContextGuard must be a
> distinct new product and implementation, not a renamed copy of Synora.
> Synora can inspire lessons, but do not copy its code or submit it as
> the hackathon project.

------------------------------------------------------------------------

## 1. Executive summary

**ContextGuard is an agentic AI system that checks whether the
information available is sufficiently reliable and complete for a
specific decision or task.** The user supplies a goal and relevant
documents. ContextGuard investigates the evidence, detects
contradictions, identifies missing requirements and unsupported
assumptions, and produces an evidence-linked Context Gap Report with
targeted questions and next steps.

### The central user question

> "Do I have enough reliable information to make this decision or
> proceed---and what must be resolved first?"

### The core product loop

1.  **Define the goal:** User states the intended decision or action,
    such as "Are we ready to start development?"
2.  **Collect context:** User uploads relevant documents or pastes
    notes/instructions.
3.  **Plan checks:** A Planner Agent translates the goal into
    requirements and checks.
4.  **Find evidence:** An Evidence Agent extracts relevant facts and
    source passages.
5.  **Challenge the evidence:** A Challenge Agent identifies
    contradictions, missing information, outdated facts, and unsupported
    assumptions.
6.  **Verify findings:** Deterministic checks and a verification layer
    validate references, field consistency, and report structure.
7.  **Resolve uncertainty:** ContextGuard asks targeted questions when
    important facts are missing or ambiguous.
8.  **Produce a report:** The system prioritizes gaps, explains why they
    matter, and suggests next steps.

The signature feature is not summarization. It is **goal-specific
evidence sufficiency checking**: the system tests whether the supplied
information supports proceeding with the user's stated goal.

------------------------------------------------------------------------

## 2. The problem

People often act on incomplete or conflicting information without
realizing it. Examples: - A project proposal and meeting notes contain
different deadlines. - A task depends on a requirement that was never
finalized. - A decision is marked "approved" but there is no evidence of
who approved it. - A student has assignment instructions and a rubric
that appear to disagree. - A team assumes a feature is required even
though no source supports that assumption. - A handover omits a key
dependency or unresolved decision.

A general AI assistant may summarize all the supplied documents without
reliably prioritizing the conflicts and missing information that matter
for the user's goal. ContextGuard is designed to make those gaps
explicit, traceable, and actionable.

### Product hypothesis

Users will value a tool that doesn't just answer questions about
documents, but challenges whether the evidence is adequate for the
intended action.

This hypothesis must be tested. Document Q&A, contract analysis,
requirement checking, and contradiction detection already exist in
various tools. Do not claim ContextGuard is unique until compared with
competitors and evaluated against a baseline.

------------------------------------------------------------------------

## 3. Target users and first use case

### Potential users

-   Software and project teams.
-   Students checking assignment instructions and rubrics.
-   Business operations teams.
-   Teams reviewing proposals or requirements.
-   People preparing project handovers.
-   Small organizations working from scattered documents and meeting
    notes.

### Recommended first demo scenario: project readiness

The user asks: \> "Are we ready to start development?"

They upload: - Project proposal. - Requirements document. - Meeting
notes. - Task list or project plan.

The documents intentionally include: - Two different project
deadlines. - A requirement with no clear approval. - A task that depends
on an unresolved decision. - One unsupported assumption.

ContextGuard should identify the exact passages, classify each finding,
explain why it matters, ask a targeted clarification question, and
provide a prioritized list of next actions.

This scenario is small enough to build and easy for a judge to
understand. The architecture can later be applied to education,
procurement, onboarding, and other document-driven decisions.

------------------------------------------------------------------------

## 4. Product promise and positioning

### Product promise

**"Before you act, ContextGuard checks what your evidence supports, what
is missing, and what must be resolved."**

### ContextGuard does

-   Accepts a user goal plus documents/notes.
-   Converts the goal into a checklist of requirements or evidence
    needs.
-   Extracts relevant facts and source passages.
-   Detects likely contradictions and missing requirements.
-   Flags unsupported assumptions and ambiguous or stale information.
-   Asks clarifying questions when a finding cannot be resolved from
    available sources.
-   Prioritizes findings by relevance to the user's goal.
-   Produces a source-linked Context Gap Report and next-step plan.

### ContextGuard does not

-   Guarantee that a decision is correct or safe.
-   Treat an absent statement as proof that something is false.
-   Treat every apparent conflict as a real contradiction without
    considering context/version/date.
-   Invent missing facts to make a report look complete.
-   Automatically approve projects or take consequential external
    actions.
-   Replace a human decision-maker, legal adviser, auditor, or domain
    expert.
-   Claim that an LLM-generated readiness score is scientifically
    validated.
-   Become a generic chatbot that only summarizes documents.

### Recommended positioning

ContextGuard is a **goal-aware evidence and decision-readiness
checker**, not a document summarizer.

------------------------------------------------------------------------

## 5. Signature differentiators

### A. Goal-specific verification

The system must know what the user intends to do. "Is this information
complete?" is too vague. Instead: - "Are we ready to start
development?" - "Does this assignment submission meet the rubric?" - "Do
we have the required evidence to approve this proposal?"

The goal determines which gaps matter.

### B. Evidence-first findings

Every important finding should show: - Finding title and type. - Source
document and passage/page where available. - Related conflicting passage
if applicable. - Explanation of the conflict or gap. -
Confidence/uncertainty and why. - Why it matters for the stated goal. -
Suggested clarification question or next step.

### C. Active uncertainty detection

ContextGuard should explicitly say: - "I found conflicting dates;
confirm which one is authoritative." - "I cannot verify this approval
from the supplied documents." - "The information needed to assess this
requirement was not provided." - "This appears to be a contradiction,
but the sources may refer to different milestones."

It must distinguish "not found in the supplied sources" from "does not
exist."

### D. Prioritized Context Gap Report

Organize findings by action priority, using transparent rules: -
**Blocking:** likely prevents responsible progress until clarified. -
**Important:** materially affects planning or correctness. -
**Informational:** useful to know, but not currently blocking.

Do not invent a pseudo-scientific confidence or readiness score. If the
app displays an overall status, derive it from explicitly listed rules
and show those rules.

### E. Proof mode / measurable evaluation

Provide a set of fixed test cases with deliberately inserted conflicts,
missing fields, and unsupported assumptions. Show whether ContextGuard
catches them and whether its cited evidence actually supports each
finding. This proves the product does more than sound persuasive.

------------------------------------------------------------------------

## 6. Example user journey

1.  User opens ContextGuard and selects **Check a decision**.
2.  User enters goal: "Check whether our project is ready for
    development."
3.  User uploads a proposal, requirements document, meeting notes, and
    task list.
4.  ContextGuard parses the files and displays the extracted text or
    document previews.
5.  Planner Agent creates checks such as:
    -   Are launch dates consistent?
    -   Are core requirements documented?
    -   Are major decisions approved or explicitly unresolved?
    -   Do planned tasks depend on unresolved decisions?
    -   Are task owners and dependencies clear?
6.  Evidence Agent locates relevant passages for each check.
7.  Challenge Agent compares evidence and proposes potential
    gaps/conflicts.
8.  Verification layer checks that the cited passages exist and that
    each finding is grounded.
9.  If needed, ContextGuard asks a small number of high-value
    clarification questions.
10. User sees a Context Gap Report and can mark items resolved, dismiss
    a false positive, or export the report.

Do not force the user to answer a long form before they can see useful
results. Ask only for inputs needed to evaluate the stated goal.

------------------------------------------------------------------------

## 7. Agentic AI architecture

Use agents for planning, evidence interpretation, and challenge/review.
Use deterministic code for document metadata, schema validation,
reference checking, deduplication, and simple consistency rules.

### Proposed workflow

**Step 1 --- Goal Planner** - Understand the user's intended
decision/action. - Generate a structured checklist of required facts and
checks. - Identify which sources or data fields are needed. - Keep
checks relevant to the user's goal; don't perform unbounded research.

**Step 2 --- Evidence Agent** - Search parsed documents for relevant
statements. - Extract facts and source passages. - Return structured
evidence records with document/page/paragraph references where
possible. - Preserve dates, units, versions, and context. - Mark
insufficient or ambiguous evidence instead of guessing.

**Step 3 --- Challenge Agent** - Compare evidence records against the
goal-specific checklist. - Identify: - conflicting values or dates, -
missing required information, - unsupported assumptions, - potentially
outdated statements, - unresolved dependencies, - inconsistent
status/approval claims. - For each finding, provide the supporting
passages, alternative interpretations, and a question or action that
would resolve it. - Do not call a gap a contradiction unless the sources
truly conflict.

**Step 4 --- Deterministic verification layer** - Check that source
references point to actual extracted text. - Check the report schema. -
Detect exact conflicts in structured fields such as dates, versions,
amounts, and status labels when possible. - Deduplicate repeated
findings. - Reject claims without adequate source evidence or mark them
unverified. - Keep a trace of which inputs produced each finding.

**Step 5 --- Resolution / Clarification** - Ask targeted questions for
high-impact ambiguity. - Allow the user to confirm which source is
authoritative or provide missing information. - Re-run only the affected
checks where possible. - Do not invent a resolution.

**Step 6 --- Report Generator** - Produce the final Context Gap
Report. - Separate verified facts, potential conflicts, missing
information, assumptions, and recommendations. - Explain why each
important gap matters for the goal. - Give clear next actions and
unresolved questions.

### Number of agents

For the MVP, use three logical roles: Planner, Evidence, and Challenge.
The report generator may be a deterministic template plus one LLM call.
Do not add more agents unless evaluation shows a real benefit.

A basic sequential Python orchestrator is sufficient. LangGraph is
optional if explicit state, branching, retries, or human review steps
become useful. The purpose is not to maximize the number of agents.

### Human oversight

-   User can confirm or correct important extracted facts.
-   User can dismiss a false positive with a reason.
-   User remains responsible for the final decision.
-   Do not perform external actions automatically.
-   Show unresolved high-impact gaps clearly.

------------------------------------------------------------------------

## 8. Core data model

Use structured records, not only free-form prose.

### Evidence record

``` json
{
  "evidence_id": "E1",
  "document_id": "requirements_v1",
  "document_name": "Requirements",
  "page": 3,
  "passage": "The target release date is November 15.",
  "claim_type": "deadline",
  "normalized_value": "2026-11-15",
  "version": "v1",
  "status": "extracted_unconfirmed"
}
```

### Finding record

``` json
{
  "finding_id": "F1",
  "type": "potential_conflict",
  "priority": "blocking",
  "summary": "Two documents specify different release dates.",
  "evidence_ids": ["E1", "E2"],
  "why_it_matters": "The release plan cannot be finalized until the authoritative date is confirmed.",
  "uncertainty": "The dates may refer to different milestones.",
  "question": "Does November 15 or November 20 represent the final release date?",
  "recommended_action": "Confirm the authoritative deadline and update the affected plan."
}
```

These are illustrative schemas. Final schemas should be defined with
Pydantic, validated, and versioned.

### Distinguish finding types

-   `verified_fact`
-   `potential_conflict`
-   `missing_information`
-   `unsupported_assumption`
-   `possibly_outdated`
-   `unresolved_dependency`
-   `clarification_needed`

Don't overuse the word "contradiction." Some differences are explained
by document version, scope, date, or milestone.

------------------------------------------------------------------------

## 9. MVP scope and out-of-scope features

### P0 --- must work end to end

1.  Goal input field with a few example goals.
2.  Upload PDF and DOCX or paste text.
3.  Document parsing with source passage/page tracking where possible.
4.  Planner Agent that creates a goal-specific checklist.
5.  Evidence extraction with structured records.
6.  Challenge Agent that finds potential conflicts, missing items, and
    unsupported assumptions.
7.  Verification layer for source references and structured report
    validation.
8.  Prioritized Context Gap Report with source passages.
9.  Clarification questions and manual correction/dismissal.
10. A fixed evaluation set with expected findings.
11. A polished demo using fictional project documents.

### P1 --- only after P0 is reliable

-   Export report to PDF/Markdown.
-   Save/reopen a case.
-   Compare document versions.
-   Resolve findings and track status.
-   Search a larger folder of documents.
-   Better OCR for scanned PDFs.
-   More domain templates for education or procurement.

### Out of scope for the hackathon MVP

-   Integrations with Google Drive, Slack, email, WhatsApp, or
    calendars.
-   Persistent enterprise-wide memory.
-   Autonomous actions and sending messages.
-   Full project-management application.
-   General-purpose web research agent.
-   Complex knowledge graph.
-   Multiple organizations and advanced access control.
-   Vector database unless basic parsing/retrieval requires it.
-   A generic chatbot with an enormous scope.

------------------------------------------------------------------------

## 10. Recommended technology stack

### Frontend

-   React + Vite
-   TypeScript if time permits
-   Tailwind CSS
-   A clear document/evidence panel and findings report; no need for
    complex graphics.

### Backend

-   Python + FastAPI
-   Pydantic models for evidence, findings, and reports
-   A small document ingestion module
-   A goal-check planning module
-   Evidence extraction and challenge modules
-   Deterministic validation utilities
-   pytest for tests

### Document processing

Evaluate: 1. **Docling** ---
`https://github.com/docling-project/docling` - Parses PDFs, DOCX,
tables, and layout-oriented documents. - Candidate for structured
document ingestion. - Suggested install: `pip install docling` 2.
**PyMuPDF** --- `https://github.com/pymupdf/PyMuPDF` - Useful for PDF
text extraction and page-level references. - Check current license and
dual-licensing implications before using. 3. **python-docx** ---
`https://python-docx.readthedocs.io/` - Useful for DOCX ingestion. 4.
**Docket** --- `https://github.com/KazKozDev/docket` - Research lead for
structured document extraction and source evidence; verify current
behavior, license, and maintenance.

Do not install every library. Test two candidates against the same
sample documents and choose the simplest one that preserves source
references. Include a paste-text fallback.

### LLM / extraction

-   Use a provider supported by the hackathon and accessible to the
    developer.
-   Use structured output where available and validate it with Pydantic.
-   Every material claim should link to a source passage or be
    explicitly marked as an inference/unknown.
-   Keep API keys in environment variables; never commit secrets.
-   Use a fixed sample mode if API access fails during the demo.

### Agent orchestration

-   Start with straightforward Python functions and a small sequential
    orchestrator.
-   Optional: **LangGraph**
    (`https://github.com/langchain-ai/langgraph`) for stateful
    workflows, conditional paths, and human review.
-   Use one orchestration approach, not multiple frameworks.
-   Don't use multi-agent conversation for simple deterministic checks.

### Storage

-   For MVP, process uploaded documents in memory or use temporary
    storage with clear cleanup.
-   SQLite may be enough for saved reports.
-   Avoid long-term storage of sensitive documents unless required and
    clearly disclosed.

### Deployment

-   Use a platform that is quick to configure and supports the
    frontend/backend.
-   Keep secrets in environment variables.
-   Provide a public demo if required by the hackathon.
-   Include sample documents and an offline/fallback demo path.

------------------------------------------------------------------------

## 11. Existing projects and competitors to study

These are research leads, not proof of product quality or uniqueness.
Re-check current status, features, licenses, and maintenance.

### Open-source/document tooling

-   **Docling:** `https://github.com/docling-project/docling`
-   **PyMuPDF:** `https://github.com/pymupdf/PyMuPDF`
-   **python-docx:** `https://python-docx.readthedocs.io/`
-   **Docket:** `https://github.com/KazKozDev/docket`
-   **LangGraph:** `https://github.com/langchain-ai/langgraph`

### Existing products/categories to compare

-   **Google NotebookLM:** document-grounded Q&A and source references.
-   **Notion AI:** workspace context, meeting summaries, action items.
-   **Glean:** enterprise search and work context.
-   **Fireflies.ai:** meeting summaries, action items, searchable
    conversations.
-   **DocsBot:** document-grounded knowledge assistants.
-   Existing project-management and contract-analysis tools.

These products already cover aspects of summarization, document Q&A,
meeting notes, knowledge retrieval, and task extraction. ContextGuard
must demonstrate the difference between answering a question about
documents and systematically testing evidence sufficiency for a specific
decision.

### Competitor matrix questions

For each competitor, record: - Who is the user? - What input does it
accept? - Does the user state a specific decision/goal? - Does it create
a goal-specific verification checklist? - Does it detect conflicts
between sources and handle versions/milestones? - Does it identify
missing information vs. asserting something is false? - Does it cite the
exact source passages? - Can the user resolve an issue and rerun
affected checks? - Does it provide measurable accuracy evidence? -
Pricing, license, integrations, and deployment model.

Don't claim "no product does this" unless research supports it.

------------------------------------------------------------------------

## 12. Relationship to Synora and hackathon eligibility

The user has an existing repository/project called **Synora**, a
context/memory platform with multi-source ingestion, project memory,
evidence-linked revisions, decision history, and context routing. This
is adjacent to ContextGuard but is not the same product problem.

### Separation

-   **Synora:** Preserve and retrieve project context over time so teams
    don't lose decisions and history.
-   **ContextGuard:** Given a particular goal and a set of sources, test
    whether the evidence is sufficient, identify conflicts/gaps, and
    show what must be resolved before proceeding.

ContextGuard should have its own: - Product requirements and scope. -
Source code and architecture. - Test cases and evaluation results. -
Interface and demo narrative. - Repository and documentation.

Do not clone Synora, rename it, or copy its implementation into the
hackathon submission.

### Hackathon requirements to verify

Build With AI: Basics: - Challenge page:
`https://learn-ai-basics.devpost.com/` - Official rules:
`https://learn-ai-basics.devpost.com/rules` - Learn Skill Pack:
`https://github.com/challengepost/learn-ai-basics`

Previously identified required workflow: `1-start` → `2-scope` → `3-prd`
→ `4-spec` → `5-build` → `6-ship`

Previously identified required planning files: - `devpost/scope.md` -
`devpost/prd.md` - `devpost/spec.md`

The challenge was understood to require a new project started during the
submission period, a public repository, an open-source license, and a
public demo video under three minutes. **Re-check the live official
rules for the current deadline, project reuse rules, required workflow,
video limit, and all submission requirements.**

Start the new project in an empty directory during the eligible period
and follow the skill pack. Existing ideas are different from reusing an
old implementation.

------------------------------------------------------------------------

## 13. Evaluation plan

A ContextGuard demo must show that it detects real gaps and does not
produce excessive false alarms.

### Fixed fictional evaluation set

Create 8--12 small document bundles with expected findings: 1.
Conflicting release dates in proposal vs. meeting notes. 2. Two dates
that differ but refer to different milestones (should not be flagged as
a contradiction). 3. A requirement with no approval evidence. 4. A task
dependent on an unresolved requirement. 5. A missing owner for a
critical task. 6. An outdated requirements document vs. a newer approved
version. 7. An assignment prompt and rubric with a genuinely conflicting
instruction. 8. An unsupported assumption in a project plan. 9. No gap
(negative control). 10. A false conflict caused by a date-format or
version misunderstanding. 11. Duplicate evidence across documents. 12. A
source with ambiguous wording that should trigger clarification.

### Metrics

-   **Conflict detection recall:** proportion of known genuine conflicts
    detected.
-   **Conflict precision / false-positive rate:** how many flagged
    conflicts are actually conflicts.
-   **Evidence accuracy:** whether cited passages support each finding.
-   **Missing-information precision:** whether the reported gap is
    relevant and truly absent from supplied sources.
-   **Unsupported-assumption precision:** whether the claim lacks
    adequate evidence.
-   **Question quality:** whether clarification questions resolve
    important uncertainty.
-   **Deduplication quality:** whether the same issue is not repeated
    needlessly.
-   **Robustness:** behavior with irrelevant content, unusual layouts,
    or ambiguous language.
-   **Baseline comparison:** run the same bundles through a general AI
    summarizer or document-Q&A assistant, then compare results fairly.

Keep the test set fixed, report failures honestly, and don't cherry-pick
only examples that work.

------------------------------------------------------------------------

## 14. UI and Context Gap Report

### Suggested UI flow

1.  **Start check:** User enters a goal and chooses a template (project
    readiness, assignment check, proposal review).
2.  **Add sources:** Upload PDF/DOCX or paste text.
3.  **Review extracted text:** Display document names and page/paragraph
    references.
4.  **Run analysis:** Show clear progress states for planning, evidence
    gathering, challenge checks, and verification.
5.  **Review findings:** Sort by priority and type; allow expansion to
    show evidence.
6.  **Resolve uncertainty:** User confirms which version/date is
    authoritative or supplies missing information.
7.  **Export/share:** Optional report export after P0 works.

### Report sections

-   User goal.
-   Sources analyzed and any parsing failures.
-   Summary of important gaps.
-   Verified facts.
-   Potential conflicts with source passages side by side.
-   Missing information.
-   Unsupported assumptions.
-   Possibly outdated information.
-   Unresolved dependencies.
-   Priority and reason each item matters.
-   Targeted clarification questions.
-   Recommended next steps.
-   Limitations and uncertainty.

### UI principles

-   Put evidence next to findings, not hidden behind vague citations.
-   Clearly distinguish source facts, inferences, and suggestions.
-   Use neutral language: "not found in supplied documents" instead of
    "does not exist."
-   Explain why a conflict may be false or context-dependent.
-   Allow a finding to be dismissed or marked resolved.
-   Avoid a single unvalidated "Readiness Score."
-   Show the sources and parsing status, so a missed document is not
    mistaken for proof of completeness.

------------------------------------------------------------------------

## 15. Recommended repository structure

``` text
contextguard/
├── README.md
├── LICENSE
├── THIRD_PARTY_NOTICES.md
├── .env.example
├── .gitignore
├── frontend/
│   ├── src/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── schemas/
│   │   ├── ingestion/
│   │   ├── planner/
│   │   ├── evidence/
│   │   ├── challenge/
│   │   ├── verification/
│   │   ├── reporting/
│   │   └── workflow/
│   ├── tests/
│   └── requirements.txt
├── sample_data/
│   ├── project_proposal.md
│   ├── requirements_v1.md
│   ├── meeting_notes.md
│   ├── task_list.md
│   └── expected_findings.json
├── evaluation/
│   ├── test_cases.md
│   └── results.md
├── devpost/
│   ├── scope.md
│   ├── prd.md
│   └── spec.md
└── demo/
    └── demo_script.md
```

This is a proposed layout. Create folders only when needed; keep the MVP
simple.

------------------------------------------------------------------------

## 16. Autonomous development, testing, validation, and enhancement loop

**Do not organize development into sequential phases.** The AI coding agent should own the complete ContextGuard lifecycle and work continuously toward a functioning, tested, validated, and polished product.

It should not stop after writing a plan, producing a few source files, or making one demo work. It must repeatedly inspect the actual project, implement the highest-value improvement, execute tests, validate the complete user journey, fix failures, and enhance the product.

### The continuous loop

1. **Inspect the real state**
   - Read this context, the actual repository, requirements, current hackathon rules, and existing test results.
   - Run the app and tests when possible.
   - Distinguish implemented and verified features from planned or untested features.

2. **Identify the most important gap**
   - Compare the current implementation with the definition of done and the intended demo.
   - Prioritize evidence accuracy, correct conflict handling, low false-positive rates, usable clarification flow, and end-to-end reliability.
   - Avoid adding features that do not improve the core product.

3. **Implement a complete improvement**
   - Update code, schemas, UI, tests, and documentation as needed.
   - Integrate the feature into the actual user journey.
   - Handle errors and uncertain inputs explicitly.
   - Do not leave disconnected modules or placeholders presented as completed features.

4. **Run tests and diagnose failures**
   - Run focused unit tests, integration tests, and the fixed evaluation set.
   - Test true conflicts, false-conflict traps, missing information, ambiguous dates, different milestones, outdated versions, duplicate evidence, and irrelevant text.
   - Check that cited passages exist and actually support the finding.
   - Fix defects and add regression tests.

5. **Validate the whole user journey**
   - Enter a goal.
   - Upload or paste documents.
   - Inspect extracted source text.
   - Run the Planner, Evidence, and Challenge workflow.
   - Inspect findings and evidence.
   - Resolve an ambiguity or dismiss a false positive.
   - Re-run affected checks and confirm the report updates correctly.

6. **Review product quality**
   - Inspect false positives, missed findings, unsupported claims, duplicate alerts, and unclear explanations.
   - Check parsing failures, API failures, empty states, loading states, responsive UI, accessibility, privacy, and secrets handling.
   - Compare results with the fixed baseline and document actual performance.

7. **Improve and repeat**
   - Fix the highest-impact issues first.
   - Re-run affected tests and the end-to-end flow.
   - Continue until acceptance criteria are met or a genuine external blocker prevents progress.

### Autonomous execution rules

- Own planning, coding, integration, testing, validation, debugging, documentation, and product enhancement.
- Do not ask the user to approve every small reversible decision. Make reasonable choices and record important assumptions.
- Ask for input only when a decision materially changes the product direction, required credentials/private data are unavailable, an external action needs authorization, or a real blocker cannot be resolved independently.
- Do not claim a feature works until it has been executed and tested.
- If a package, parser, model API, or deployment service fails, diagnose the issue and try a sensible alternative when possible.
- Keep the repository runnable after meaningful changes.
- Track implemented features, tests executed, failures, fixes, remaining limitations, and the next highest-value improvement.
- Never fabricate accuracy numbers, test results, competitor research, or successful deployment.
- If external access is blocked, complete all independent work and state the exact blocker.

### Definition of done

ContextGuard is ready for submission only when the actual implementation can demonstrate all of the following:

- A user can enter a goal and upload supported documents or paste text.
- Source passages and document/page references are preserved where available.
- The Planner creates checks relevant to the stated goal.
- The Evidence Agent returns traceable evidence.
- The Challenge Agent identifies meaningful conflicts, missing information, unsupported assumptions, and uncertainty.
- The verification layer rejects or flags findings without adequate evidence.
- The system distinguishes genuine conflicts from differences explained by milestones, versions, or context.
- The Context Gap Report prioritizes findings and offers targeted clarification questions.
- Users can correct extracted facts, resolve ambiguity, or dismiss a false positive.
- The fixed evaluation set runs, results are recorded, and known limitations are documented.
- The complete app works from a clean setup and has a reliable demo path.
- The repository, license, required planning artifacts, and submission materials comply with current official hackathon rules.

### Hackathon workflow remains mandatory

The continuous loop does not replace official challenge requirements. Verify the current Build With AI: Basics rules and complete the required Learn Skill Pack workflow and planning artifacts where applicable. Continue iterating on the product while satisfying those requirements.

## 17. Three-minute demo script

**0:00--0:20 --- Problem** "Teams often make decisions using incomplete
or conflicting documents. A summary can look convincing without
revealing the gaps that matter."

**0:20--0:40 --- Goal and sources** Enter "Are we ready to start
development?" Upload a proposal, requirements document, meeting notes,
and task list.

**0:40--1:05 --- Plan and evidence** Show the goal-specific checklist
and evidence passages relevant to launch dates and requirements.

**1:05--1:40 --- Challenge** ContextGuard flags the conflicting release
dates and an unapproved requirement. Expand the source passages side by
side.

**1:40--2:05 --- Uncertainty** Show that the tool does not blindly
declare the project blocked: it asks whether the two dates refer to the
same milestone and asks which source is authoritative.

**2:05--2:35 --- Context Gap Report** Show prioritized findings, why
each matters, and recommended next steps.

**2:35--2:50 --- Proof** Show one evaluation result or fixed test case
demonstrating a true conflict detected and a false conflict correctly
ignored.

**2:50--3:00 --- Differentiation** "ContextGuard doesn't merely
summarize documents. It tests whether the evidence supports a specific
decision and shows exactly what must be resolved."

The demo must use a functioning implementation, not only mockups. If the
current hackathon video limit differs, obey the official rules.

------------------------------------------------------------------------

## 18. Risks and mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  False-positive contradictions       Preserve dates, versions,
                                      milestones, and context; ask
                                      clarifying questions

  Missing evidence mistaken for       Say "not found in supplied sources"
  falsehood                           and show which sources were
                                      analyzed

  Unsupported LLM claims              Require source evidence, structured
                                      schemas, and deterministic
                                      verification

  Too many generic findings           Use a goal-specific checklist and
                                      relevance thresholds

  Poor document parsing               Use source-preserving parser, show
                                      parsing status, offer paste-text
                                      fallback

  Looks like a generic document       Center the product on goal-specific
  chatbot                             checks, gap report, and
                                      clarification loop

  Broad scope                         Start with one project-readiness
                                      use case

  Existing Synora overlap             New implementation, separate
                                      requirements, distinct workflow,
                                      and own evaluation

  Hackathon eligibility risk          Follow current rules and do not
                                      submit old code as-is

  API failure during demo             Fixed fictional fixture data and
                                      graceful fallback

  Sensitive document exposure         Fictional demo data, minimal
                                      retention, no secrets in repository

  Unverified "readiness score"        Use explicit, inspectable rules
                                      instead of arbitrary scores
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 19. Decisions to validate instead of assuming

-   Whether the Planner/Evidence/Challenge separation improves results
    over one well-prompted model.
-   Whether source citations are accurate enough.
-   Whether the tool can distinguish true conflicts from different
    milestones or versions.
-   Whether users find the prioritized gap report more useful than
    ordinary document Q&A.
-   Which parser best preserves source locations.
-   Which LLM/provider is available and suitable.
-   Whether LangGraph is necessary.
-   Whether the ContextGuard name is available.
-   Whether the product is sufficiently differentiated from existing
    document-grounded assistants and project tools.

Use a small controlled evaluation to answer these questions.

------------------------------------------------------------------------

## 20. Instructions for the next ChatGPT conversation or coding agent

Treat this document as the full ContextGuard product context and operate as the autonomous lead developer.

The agent is responsible for the **complete development lifecycle in a continuous loop**: requirements, architecture, implementation, integration, testing, evaluation, debugging, validation, security/privacy review, UI/UX improvement, documentation, deployment preparation, and submission readiness.

The agent should:

1. Read this document fully and inspect the actual repository and runtime before making assumptions.
2. Verify the latest official hackathon rules, deadline, and Learn Skill Pack requirements.
3. Complete required scope/PRD/spec artifacts, but do not stop at planning.
4. Build a working application end to end, rather than only providing advice, plans, or isolated code.
5. Run the app, tests, and fixed evaluation set after meaningful changes.
6. Diagnose failures, fix defects, add regression tests, and repeat validation and enhancement.
7. Keep evidence traceability and uncertainty handling central to the implementation.
8. Test true and false conflicts, missing information, ambiguous dates, version/milestone differences, unsupported assumptions, and no-gap control cases.
9. Use deterministic verification where possible and never claim a finding is proven when the evidence does not support it.
10. Keep ContextGuard genuinely distinct from Synora. Do not copy or repackage Synora's existing implementation.
11. Verify licenses and installation instructions before adopting open-source code or dependencies.
12. Make reasonable reversible decisions autonomously. Ask only for essential missing information, credentials, high-impact product decisions, or actions requiring explicit authorization.
13. Keep the app runnable, protect secrets and uploaded documents, and never invent evaluation results.
14. Maintain a concise status record of implementation, tests, failures and fixes, known limitations, blockers, and next improvements.
15. Prioritize a polished, measurable end-to-end product over adding more agents or features.

**Default operating instruction:** Inspect → decide → implement → run → test → validate → review → improve → repeat. Continue autonomously until the acceptance criteria are met or a genuine blocker requires user input.

## 21. Useful links

### Hackathon

-   Build With AI: Basics: `https://learn-ai-basics.devpost.com/`
-   Official rules: `https://learn-ai-basics.devpost.com/rules`
-   Learn Skill Pack: `https://github.com/challengepost/learn-ai-basics`

### Document processing

-   Docling: `https://github.com/docling-project/docling`
-   PyMuPDF: `https://github.com/pymupdf/PyMuPDF`
-   python-docx: `https://python-docx.readthedocs.io/`
-   Docket: `https://github.com/KazKozDev/docket`

### Workflow orchestration

-   LangGraph: `https://github.com/langchain-ai/langgraph`

### Competitor/product research

-   Google NotebookLM: `https://notebooklm.google.com/`
-   Notion AI: `https://www.notion.com/product/ai`
-   Glean: `https://www.glean.com/`
-   Fireflies.ai: `https://fireflies.ai/`
-   DocsBot: `https://docsbot.ai/`

### Existing user project (reference only; do not reuse its implementation)

-   Synora: `https://github.com/Ratnadeep-2007/Synora`

------------------------------------------------------------------------

## Final one-sentence definition

**ContextGuard takes a user's goal and source documents, checks whether
the evidence is sufficient and consistent for that goal, identifies
conflicts and missing information with traceable citations, and guides
the user toward resolving the gaps before proceeding.**
