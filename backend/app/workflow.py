from __future__ import annotations

import hashlib
import re
from collections.abc import Callable

from .providers import complete
from .sample import fixture_candidates
from .schemas import AnswerOption, Case, Candidate, ChallengeOutput, ClarificationChoice, Criterion, Evidence, EvidenceOutput, Finding, PlanOutput, Report, Trace, now


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def fingerprint(case: Case) -> str:
    context = case.goal + case.scope + "|".join(s.content_hash for s in case.sources) + "|".join(f"{c.id}:{c.description}:{c.excluded}" for c in case.criteria)
    context += "|project:" + case.project_id if case.project_id else ""
    return hashlib.sha256(context.encode()).hexdigest()


def active_assertions(case: Case):
    current = fingerprint(case)
    latest = {}
    for event in case.resolutions:
        if not event.revoked and event.source_fingerprint == current:
            latest[event.finding_id] = event
    return list(latest.values())


def clarification_options(finding: Candidate, evidence: list[Evidence]) -> list[AnswerOption]:
    """Options must reproduce text from the finding's verified evidence, not invent answers."""
    refs = {e.id: e for e in evidence if e.id in finding.evidence_ids}
    options = []
    seen = set()
    for option in finding.answer_options:
        text = normalize(option.text)
        ids = list(dict.fromkeys(option.evidence_ids))
        if len(text) < 5 or text in seen or not ids or not all(eid in refs and text in normalize(refs[eid].quote) for eid in ids):
            continue
        seen.add(text)
        options.append(AnswerOption(text=option.text.strip(), evidence_ids=ids))
    if options:
        return options
    # Older saved reports and fixture replay have no generated choices. Use exact
    # verified statements as transparent choices for conflicts, never made-up values.
    if finding.type == "potential_conflict":
        for ref in refs.values():
            text = normalize(ref.quote)
            if text not in seen:
                seen.add(text)
                options.append(AnswerOption(text=ref.quote, evidence_ids=[ref.id]))
            if len(options) == 4:
                break
    return options


def clarification_choices(finding: Candidate, evidence: list[Evidence]) -> list[ClarificationChoice]:
    choices = []
    refs = {e.id: e for e in evidence}
    for option in clarification_options(finding, evidence):
        identity = normalize(option.text) + '|' + '|'.join(sorted({refs[eid].passage_id for eid in option.evidence_ids if eid in refs}))
        label = normalize(re.sub(r'\*\*|`', '', option.text))
        choices.append(ClarificationChoice(id='source_' + hashlib.sha256(identity.encode()).hexdigest()[:12], label=label if len(label) <= 140 else label[:137] + '...', answer=option.text, action='confirm', kind='source', evidence_ids=option.evidence_ids))
    pending = {
        'potential_conflict': ('Keep both statements unresolved', 'The conflicting statements have not been reconciled.'),
        'missing_information': ('The requested information is still missing', 'The information requested by this question is still unavailable.'),
        'unresolved_dependency': ('Keep the dependent work pending', 'Keep the affected work pending until its listed dependency is clarified.'),
        'unsupported_assumption': ('This assumption has not been confirmed', 'The assumption described in this finding has not been confirmed.'),
        'possibly_outdated': ('Wait for an updated, authoritative source', 'Keep this information unconfirmed until an updated authoritative source is supplied.'),
        'clarification_needed': ('No confirmed answer yet', 'This question still needs a confirmed answer.'),
    }
    label, answer = pending[finding.type]
    choices.append(ClarificationChoice(id='keep_open', label=label, answer=answer, action='unknown', kind='decision'))
    if finding.type == 'unsupported_assumption':
        choices.append(ClarificationChoice(id='drop_assumption', label='Do not use this assumption in the current plan', answer='Do not rely on this assumption for the current decision: ' + finding.title, action='confirm', kind='decision'))
    choices += [
        ClarificationChoice(id='not_relevant', label='This does not apply to the current decision', answer='This finding does not apply to the current decision: ' + finding.title, action='dismiss', kind='decision'),
        ClarificationChoice(id='accept_risk', label='Proceed with this risk recorded', answer='Proceed with the risk described in this finding: ' + finding.impact, action='accept_risk', kind='decision'),
    ]
    for choice in choices:
        if choice.kind == 'decision':
            choice.answer = choice.answer[:3000]
    return choices


def verify(case: Case, checks: list[Criterion], evidence: list[Evidence], candidates: list[Candidate], limitations=None, traces=None) -> Report:
    passages = {p.id: p for s in case.sources if s.status == "ready" for p in s.passages}
    active = {c.id: c for c in checks if not c.excluded}
    valid = {}
    rejected = 0
    rejection_details = []
    for item in evidence:
        if item.check_id not in active:
            continue
        if item.id in valid or len(normalize(item.quote)) < 5 or item.passage_id not in passages or normalize(item.quote) not in normalize(passages.get(item.passage_id).text if item.passage_id in passages else ""):
            rejected += 1
            rejection_details.append(f"Evidence {item.id} was rejected: duplicate ID, missing passage, or quotation not found in its passage.")
            continue
        valid[item.id] = item
    findings = []
    seen = set()
    for item in candidates:
        if item.check_id not in active:
            continue
        # A finding may need qualifying evidence filed under another included check
        # (for example a date plus its unapproved status). Each quote is still verified.
        refs = [valid[x] for x in dict.fromkeys(item.evidence_ids) if x in valid]
        # Every candidate, including a gap, must be anchored to relevant source context.
        if len(refs) != len(set(item.evidence_ids)) or not refs:
            rejected += 1
            rejection_details.append(f"Finding '{item.title}' was rejected: missing, excluded, or invalid evidence reference.")
            continue
        if not any(ref.check_id == item.check_id for ref in refs):
            rejected += 1
            rejection_details.append(f"Finding '{item.title}' was rejected: no evidence is linked to its review check.")
            continue
        if item.type == "potential_conflict" and len({normalize(x.quote) for x in refs}) < 2:
            rejected += 1
            rejection_details.append(f"Finding '{item.title}' was rejected: a potential conflict needs at least two distinct quotations.")
            continue
        key = item.check_id + ":" + item.type + ":" + ":".join(sorted(x.passage_id + ":" + normalize(x.quote) for x in refs))
        if key in seen:
            continue
        seen.add(key)
        finding = Finding(**item.model_dump(), id="F_" + hashlib.sha256(key.encode()).hexdigest()[:12])
        finding.answer_options = clarification_options(finding, refs)
        finding.clarification_choices = clarification_choices(finding, refs)
        if finding.priority == "blocking" and finding.type == "missing_information" and active[item.check_id].origin == "suggested":
            finding.priority = "important"
        latest = next((r for r in reversed(case.resolutions) if r.finding_id == finding.id and not r.revoked and r.source_fingerprint == fingerprint(case)), None)
        if latest:
            finding.answer, finding.owner = latest.answer, latest.owner
            finding.option_text = latest.option_text
            finding.option_passage_ids = latest.option_passage_ids
            finding.choice_id = latest.choice_id
            finding.status = {"confirm": "user_confirmed", "dismiss": "dismissed", "accept_risk": "risk_accepted", "unknown": "open"}[latest.action]
        findings.append(finding)
    rank = {"blocking": 0, "important": 1, "informational": 2}
    findings.sort(key=lambda f: (f.status != "open", rank[f.priority]))
    checks = [c.model_copy(update={"coverage": "excluded" if c.excluded else "evidence_reviewed" if any(e.check_id == c.id for e in valid.values()) else "insufficient_evidence"}) for c in checks]
    warnings = list(limitations or [])
    for source in case.sources:
        warnings += [f"{source.name}: {w}" for w in source.warnings]
    warnings.append("Only the supplied, readable sources and listed checks were assessed. Source quotations are not independent proof of truth.")
    if rejected:
        warnings.append(f"{rejected} unsupported or malformed evidence/finding records were rejected. Coverage may be incomplete; inspect the listed checks.")
        warnings.extend(rejection_details)
    if case.mode == "sample":
        warnings.insert(0, "Fictional sample: a fixed fixture replay, with deterministic reference verification and case-memory updates. No live AI call was made.")
    return Report(checks=checks, evidence=list(valid.values()), findings=findings, limitations=list(dict.fromkeys(warnings)), traces=traces or [], rejected_count=rejected, prior_decisions=case.prior_decisions)


def analyze(case: Case, progress: Callable[[str], None]) -> Report:
    ready = [s for s in case.sources if s.status == "ready"]
    if not ready:
        raise ValueError("Add at least one readable source before starting a review.")
    if not any(not c.excluded for c in case.criteria):
        raise ValueError("Include at least one review criterion.")
    warnings = []
    traces = []
    checks = case.criteria
    progress("Planning checks")
    if case.mode == "sample":
        progress("Finding source evidence")
        evidence, candidates = fixture_candidates(case)
        progress("Challenging assumptions")
        traces = [Trace(role=role, provider="fixture", model="fieldwork-v1", duration_ms=0) for role in ["Planner", "Evidence", "Challenge"]]
    else:
        passages = [p.model_dump() for s in ready for p in s.passages]
        assertions = [r.model_dump() for r in active_assertions(case)]
        base = {"goal": case.goal, "scope": case.scope, "sources": [{"id": s.id, "name": s.name, "warnings": s.warnings} for s in case.sources], "passages": passages, "user_assertions_not_documentary_proof": assertions, "prior_project_decisions_not_documentary_proof": [r.model_dump() for r in case.prior_decisions], "requested_checks": [c.model_dump(exclude={"coverage"}) for c in case.criteria if not c.excluded]}
        plan, trace, info = complete("Planner", "Produce up to 8 relevant checks. Keep IDs of requested checks. Excluded checks are not supplied: do not restore them or add equivalent ones. Only label origin source when source_passage_id cites an explicit requirement. Avoid universal project best practices unrelated to the goal.", PlanPayload(base, case), PlanOutput, case.allow_fallback)
        traces.append(trace)
        warnings += info
        passage_ids = {p["id"] for p in passages}
        excluded = {c.id for c in case.criteria if c.excluded}
        planned = []
        used_ids = set()
        for item in plan.checks:
            if item.id in excluded or item.id in used_ids:
                continue
            used_ids.add(item.id)
            value = Criterion(**item.model_dump())
            if value.origin == "source" and value.source_passage_id not in passage_ids:
                value.origin, value.source_passage_id = "suggested", None
                warnings.append("A planner requirement reference could not be validated and was treated as a suggestion.")
            planned.append(value)
        checks = planned + [c for c in case.criteria if c.excluded]
        if not planned:
            raise ValueError("The planner returned no usable checks. Refine the goal or retry.")
        progress("Finding source evidence")
        evidence_result, trace, info = complete("Evidence", "For each check, extract exact relevant quotes from supplied passages. Every record needs a unique ID, check_id and passage_id. Capture both sides of differences; preserve versions, entity and milestone. Return evidence only, no findings.", {**base, "checks": [c.model_dump(exclude={"coverage"}) for c in planned]}, EvidenceOutput, case.allow_fallback)
        traces.append(trace)
        warnings += info
        evidence = evidence_result.evidence
        progress("Challenging assumptions")
        # Keep all findings in the challenge output, then apply user decisions separately.
        # This prevents a prior confirmation disappearing from the audit trail on a rerun.
        challenge, trace, info = complete("Challenge", "For each finding, supply up to four answer_options with concise exact source text (text) and backing evidence_ids. Offer the competing values or statements the user can choose. Each option text must be an exact substring of every cited evidence quote, and all option references must also appear in the finding evidence_ids. Do not invent options for missing facts or owners. Do not include Other; the UI adds that free-text choice. Evaluate evidence against checks for this decision. Return consequential candidate findings anchored to exact evidence IDs, including existing issues even if the user may later resolve them. A finding may cite qualifying evidence from other included checks, but must cite at least one evidence record for its own check. Do not label different milestones or clearly superseded versions as a direct conflict. No missing-information blocker from a suggested best practice. State affected action, uncertainty, and one actionable question. User assertions may change related impact or questions, but do not replace documentary evidence; preserve existing gaps and let the application's separate status overlay record answers. Reuse exact evidence quotations for unchanged issues. Earlier project decisions are historical user statements, not current documentary proof. If current sources disagree with them, ask the user to reconfirm; never automatically close a finding using remembered context. Do not invent owners or claim a whole project is blocked. Evidence existence is not semantic verification. Coverage status is computed afterward by the application; do not infer it from default or absent fields. Include relevant coverage limitations.", {"goal": case.goal, "scope": case.scope, "checks": [c.model_dump(exclude={"coverage"}) for c in planned], "evidence": [e.model_dump() for e in evidence], "passages": passages, "user_assertions_not_documentary_proof": assertions, "prior_project_decisions_not_documentary_proof": [r.model_dump() for r in case.prior_decisions]}, ChallengeOutput, case.allow_fallback)
        traces.append(trace)
        warnings += info + challenge.limitations
        candidates = challenge.findings
    progress("Verifying source references")
    return verify(case, checks, evidence, candidates, warnings, traces)


def PlanPayload(base: dict, case: Case) -> dict:
    return {**base, "excluded_checks": [{"id": c.id, "title": c.title, "reason": c.exclusion_reason} for c in case.criteria if c.excluded]}


def brief(case: Case) -> str:
    if not case.report:
        raise ValueError("Run the review before preparing a brief.")
    report = case.report
    open_findings = [f for f in report.findings if f.status in {"open", "risk_accepted"}]
    recorded_findings = [f for f in report.findings if f.status not in {"open", "risk_accepted"}]
    lines = [f"# {case.title} - kickoff brief", "", f"Goal: {case.goal}", f"Scope: {case.scope or 'Not further limited'}", f"Reviewed: {report.created_at}", f"Mode: {'Fictional fixture replay; no live AI' if case.mode == 'sample' else 'Live AI-assisted review'}", "", "## Review outcome", f"- User-confirmed clarifications: {sum(f.status == 'user_confirmed' for f in report.findings)}", f"- Marked not relevant: {sum(f.status == 'dismissed' for f in report.findings)}", f"- Accepted risks: {sum(f.status == 'risk_accepted' for f in report.findings)}", f"- Still unanswered: {sum(f.status == 'open' for f in report.findings)}", ""]
    if not open_findings and report.findings:
        lines.append("All listed findings have a recorded answer or relevance decision. Check coverage and limitations before proceeding.")
    sources = {s.id: s for s in case.sources}
    passages = {p.id: p for s in case.sources for p in s.passages}
    evidence = {e.id: e for e in report.evidence}
    for heading, findings in [("Recorded clarifications", recorded_findings), ("Open decisions and accepted risks", open_findings)]:
        lines += ["", f"## {heading}"]
        if not findings:
            lines.append("None in this review.")
        for f in findings:
            lines += ["", f"### {f.title}", f"Priority: {f.priority}; status: {f.status.replace('_', ' ')}", f"Impact: {f.impact}", f"Question: {f.question}", f"Next action: {f.recommended_action}", f"Owner: {f.owner or 'Unassigned'}"]
            if f.answer:
                lines.append(f"User statement (not documentary proof): {f.answer}")
            if f.option_text:
                lines.append(f"Selected source statement: {f.option_text}")
                for pid in f.option_passage_ids:
                    if pid in passages:
                        p = passages[pid]
                        lines.append(f"Choice source: {sources[p.document_id].name}, {p.location}")
            for ref in f.evidence_ids:
                if ref in evidence and evidence[ref].passage_id in passages:
                    e = evidence[ref]
                    p = passages[e.passage_id]
                    lines.append(f"Source: {sources[p.document_id].name}, {p.location} - {e.quote}")
    if not report.findings:
        lines.append("No findings in assessed checks. This is not a project approval.")
    if report.prior_decisions:
        lines += ["", "## Earlier project decisions considered", "These are historical user clarifications, not independent source verification."]
        for prior in report.prior_decisions:
            lines += [f"- {prior.title}: {prior.answer}", f"  Earlier review: {prior.case_title}; recorded: {prior.created_at}; owner: {prior.owner or 'Unassigned'}"]
            for ref in prior.sources:
                lines.append(f"  Earlier source: {ref.name}, {ref.location}")
    lines += ["", "## Sources"] + [f"- {s.name}: {s.status}" for s in case.sources]
    lines += ["", "## Review criteria"] + [f"- {c.title}: {'excluded — ' + c.exclusion_reason if c.excluded else c.coverage.replace('_', ' ')} ({c.origin})" for c in report.checks]
    lines += ["", "## Limitations"] + [f"- {x}" for x in report.limitations]
    lines += ["", "Final decisions remain with the project lead. User-confirmed or risk-accepted issues are not independently verified approvals."]
    return "\n".join(lines)
