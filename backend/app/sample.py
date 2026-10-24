from .ingestion import parse_source
from .schemas import AnswerOption, Case, Candidate, Evidence, default_criteria

SOURCES = [
    ("01_Project_proposal.md", """# Fieldwork — client portal\n\nThe client portal will let account managers share project updates and invoices.\n\nThe final client release is scheduled for November 15, 2026.\n\nThe delivery lead is Maya Patel. The first sprint covers the project dashboard and account sign-in.\n\nPayment processing is proposed for launch, subject to written client approval. No payment work should begin before that approval."""),
    ("02_Requirements.md", """# Requirements — approved scope v1\n\nThe dashboard and account sign-in are approved for the first implementation sprint. Maya Patel owns the dashboard; Leo Chen owns sign-in.\n\nPayment processing remains pending. Written client approval and a payment-provider decision are required before payment integration starts.\n\nAccount managers need to view invoices. Whether invoice collection must happen in the portal is undecided."""),
    ("03_Meeting_notes.md", """# Planning meeting — October 22, 2026\n\nThe team discussed November 20, 2026 as the final client release date. This is not yet confirmed as a change to the proposal.\n\nThe client has not yet provided written approval for payment processing.\n\nPayment-provider selection remains undecided. Maya will bring both decisions to the kickoff meeting.\n\nThe team will use email reminders for the first sprint; no decision has been made on automated SMS."""),
    ("04_Task_list.md", """# First sprint task list\n\nMaya Patel: build the approved project dashboard. Leo Chen: build account sign-in. Neither task depends on payment-provider selection.\n\nLeo Chen: start payment integration on Monday. Dependency: select a payment provider and obtain written client approval; both remain unresolved.\n\nPlanning assumption: automated SMS reminders are included in the fixed launch budget. This assumption needs evidence before it is used for estimates."""),
]


def sample_case() -> Case:
    return Case(title="Fieldwork · kickoff review", goal="Are we ready to start development on the client portal?", scope="Review the first implementation sprint. Distinguish payment work from the approved dashboard and sign-in tasks.", mode="sample", sources=[parse_source(n, t.encode()) for n, t in SOURCES], criteria=default_criteria())


def fixture_candidates(case: Case) -> tuple[list[Evidence], list[Candidate]]:
    evidence = []
    def cite(check, substring):
        passage = next(p for source in case.sources for p in source.passages if substring in p.text)
        item = Evidence(id=f"E{len(evidence) + 1}", check_id=check, passage_id=passage.id, quote=passage.text)
        evidence.append(item)
        return item.id
    e1 = cite("dates", "November 15")
    e2 = cite("dates", "November 20")
    e3 = cite("approval", "written approval for payment")
    e4 = cite("approval", "Written client approval and a payment-provider")
    e5 = cite("dependencies", "Leo Chen: start payment integration")
    e6 = cite("dependencies", "Payment-provider selection remains")
    e7 = cite("assumptions", "Planning assumption:")
    e8 = cite("assumptions", "no decision has been made on automated SMS")
    return evidence, [
        Candidate(check_id="dependencies", title="Payment work depends on two open decisions", type="unresolved_dependency", priority="blocking", explanation="The task list schedules payment integration before a provider is selected and written client approval is supplied.", impact="Payment integration needs these decisions first. The dashboard and sign-in tasks are explicitly independent.", uncertainty="This does not establish whether approval exists outside the supplied documents.", question="Which payment provider is approved, and where is the written scope approval?", recommended_action="Confirm the provider and attach approval evidence before starting payment integration.", evidence_ids=[e5, e6]),
        Candidate(check_id="dates", title="The release date needs confirmation", type="potential_conflict", priority="important", explanation="The proposal names November 15; meeting notes discuss November 20 for the final client release without confirming a change.", impact="Release planning and client commitments depend on one authoritative date. This does not block unrelated implementation.", uncertainty="November 20 may be a proposed revision rather than an agreed date.", question="Is November 20 an approved revision to the November 15 release date?", recommended_action="Confirm the release milestone and authoritative date, then update the plan.", evidence_ids=[e1, e2], answer_options=[AnswerOption(text="November 15, 2026", evidence_ids=[e1]), AnswerOption(text="November 20, 2026", evidence_ids=[e2])]),
        Candidate(check_id="approval", title="Payment approval is not evidenced", type="missing_information", priority="important", explanation="Requirements call for written approval; the supplied meeting notes state that it has not yet been provided.", impact="Treat payment processing as pending scope until approval evidence is added.", uncertainty="The review cannot inspect approvals outside these sources.", question="Can the client provide written approval for payment processing?", recommended_action="Add approval evidence or keep payment processing outside the committed scope.", evidence_ids=[e3, e4]),
        Candidate(check_id="assumptions", title="SMS is included in estimates without a decision", type="unsupported_assumption", priority="important", explanation="The task list includes automated SMS in the fixed launch budget, while meeting notes leave that decision open.", impact="An unsupported feature assumption could distort the estimate and scope.", uncertainty="The supplied sources do not establish an SMS commitment.", question="Should automated SMS be excluded from the launch estimate until it is approved?", recommended_action="Confirm the assumption or remove SMS from the committed estimate.", evidence_ids=[e7, e8]),
    ]
