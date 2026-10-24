from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def uid() -> str:
    return uuid4().hex


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Passage(Model):
    id: str
    document_id: str
    location: str
    text: str


class Source(Model):
    id: str
    name: str
    kind: str
    content_hash: str
    status: Literal["ready", "failed"] = "ready"
    passages: list[Passage] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    added_at: str = Field(default_factory=now)


class Criterion(Model):
    id: str
    title: str
    description: str
    origin: Literal["suggested", "user", "source"] = "suggested"
    source_passage_id: str | None = None
    excluded: bool = False
    exclusion_reason: str = ""
    coverage: Literal["not_assessed", "evidence_reviewed", "insufficient_evidence", "excluded"] = "not_assessed"


class PlannedCheck(Model):
    id: str
    title: str
    description: str
    origin: Literal["suggested", "user", "source"]
    source_passage_id: str | None


class PlanOutput(Model):
    checks: list[PlannedCheck] = Field(max_length=8)


class Evidence(Model):
    id: str
    check_id: str
    passage_id: str
    quote: str = Field(min_length=5, max_length=3000)


class EvidenceOutput(Model):
    evidence: list[Evidence] = Field(max_length=60)


FindingType = Literal["potential_conflict", "missing_information", "unsupported_assumption", "unresolved_dependency", "possibly_outdated", "clarification_needed"]


class AnswerOption(Model):
    text: str = Field(min_length=5, max_length=3000)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)


class ClarificationChoice(Model):
    id: str
    label: str
    answer: str
    action: Literal['confirm', 'unknown', 'dismiss', 'accept_risk']
    kind: Literal['source', 'decision']
    evidence_ids: list[str] = Field(default_factory=list)


class Candidate(Model):
    check_id: str
    title: str
    type: FindingType
    priority: Literal["blocking", "important", "informational"]
    explanation: str
    impact: str
    uncertainty: str
    question: str
    recommended_action: str
    evidence_ids: list[str]
    answer_options: list[AnswerOption] = Field(default_factory=list, max_length=4)


class ChallengeOutput(Model):
    findings: list[Candidate] = Field(max_length=20)
    limitations: list[str] = Field(max_length=12)


class Finding(Candidate):
    id: str
    status: Literal["open", "user_confirmed", "dismissed", "risk_accepted"] = "open"
    answer: str = ""
    owner: str = ""
    option_text: str = ""
    option_passage_ids: list[str] = Field(default_factory=list)
    clarification_choices: list[ClarificationChoice] = Field(default_factory=list)
    choice_id: str = ''


class Trace(Model):
    role: str
    provider: str
    model: str
    duration_ms: int
    input_tokens: int = 0
    output_tokens: int = 0


class Project(Model):
    id: str = Field(default_factory=uid)
    name: str = Field(min_length=1, max_length=100)
    created_at: str = Field(default_factory=now)


class DecisionSource(Model):
    document_id: str
    name: str
    passage_id: str
    location: str
    quote: str


class PriorDecision(Model):
    id: str
    project_id: str
    case_id: str
    case_title: str
    finding_id: str
    title: str
    question: str
    answer: str
    owner: str
    source_fingerprint: str
    sources: list[DecisionSource] = Field(default_factory=list)
    created_at: str


class Report(Model):
    checks: list[Criterion]
    evidence: list[Evidence]
    findings: list[Finding]
    limitations: list[str]
    traces: list[Trace]
    rejected_count: int = 0
    created_at: str = Field(default_factory=now)
    prior_decisions: list[PriorDecision] = Field(default_factory=list)


class Resolution(Model):
    id: str = Field(default_factory=uid)
    finding_id: str
    action: Literal["confirm", "dismiss", "unknown", "accept_risk"]
    answer: str = Field(max_length=3000)
    owner: str = Field(default="", max_length=120)
    source_fingerprint: str
    option_text: str = ""
    option_evidence_ids: list[str] = Field(default_factory=list)
    option_passage_ids: list[str] = Field(default_factory=list)
    finding_title: str = ""
    finding_question: str = ""
    source_snapshot: list[DecisionSource] = Field(default_factory=list)
    choice_id: str = ''
    created_at: str = Field(default_factory=now)
    revoked: bool = False


class Run(Model):
    id: str = Field(default_factory=uid)
    status: Literal["running", "completed", "failed", "cancelled"] = "running"
    stage: str = "Preparing review"
    error: str = ""
    started_at: str = Field(default_factory=now)
    finished_at: str | None = None


class Case(Model):
    id: str = Field(default_factory=uid)
    title: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=5, max_length=1000)
    scope: str = Field(default="", max_length=2000)
    project_id: str | None = None
    mode: Literal["live", "sample"] = "live"
    allow_fallback: bool = True
    sources: list[Source] = Field(default_factory=list)
    criteria: list[Criterion] = Field(default_factory=list)
    report: Report | None = None
    resolutions: list[Resolution] = Field(default_factory=list)
    run: Run | None = None
    changes: list[str] = Field(default_factory=list)
    prior_decisions: list[PriorDecision] = Field(default_factory=list)
    version: int = 0
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


def default_criteria() -> list[Criterion]:
    return [
        Criterion(id="dates", title="Dates & milestones", description="Check whether dates describe the same milestone and whether versions explain differences."),
        Criterion(id="approval", title="Scope & approvals", description="Look for required decisions and approval evidence in the supplied sources."),
        Criterion(id="dependencies", title="Dependencies", description="Identify planned work that depends on unresolved decisions."),
        Criterion(id="owners", title="Task ownership", description="Check whether critical actions have an explicitly named owner."),
        Criterion(id="assumptions", title="Assumptions", description="Distinguish documented commitments from unsupported planning assumptions."),
    ]
