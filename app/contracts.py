from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Passage(Contract):
    item_id: str = Field(min_length=1, max_length=300)
    text: str = Field(max_length=30000)
    author: str | None = None
    external_identity: str | None = None
    timestamp: datetime | None = None
    location: str = ''
    link: str = ''
    details: dict = Field(default_factory=dict)
    extraction: Literal['complete', 'partial', 'failed'] = 'complete'
    uncertainty: str = ''
    confidence: float | None = Field(default=None, ge=0, le=1)
    deleted: bool = False


class Delivery(Contract):
    source_id: str
    project_id: str | None = None
    consent: bool = Field(default=False, strict=True)
    test_mode: bool = Field(default=False, strict=True)
    passages: list[Passage] = Field(min_length=1, max_length=300)
    original: dict = Field(default_factory=dict)


class Citation(Contract):
    evidence_id: str
    quote: str = Field(min_length=4, max_length=3000)


class ProposedFinding(Contract):
    kind: Literal['verified_fact', 'potential_conflict', 'missing_information', 'unsupported_assumption',
                  'possibly_outdated', 'unresolved_dependency', 'clarification_needed']
    title: str = Field(min_length=3, max_length=180)
    impact: str = Field(min_length=3, max_length=1500)
    question: str = Field(max_length=1000)
    next_action: str = Field(min_length=3, max_length=1000)
    priority: Literal['high', 'medium', 'low']
    citations: list[Citation] = Field(min_length=1, max_length=8)
    decision_ids: list[str] = Field(default_factory=list, max_length=8)
    uncertainty: str = Field(min_length=3, max_length=1500)
    # Models must explicitly describe the comparison boundaries, not infer them from dates alone.
    same_scope: bool = False
    same_version: bool = False
    same_period: bool = False


class Analysis(Contract):
    findings: list[ProposedFinding] = Field(max_length=40)
    limitations: list[str] = Field(min_length=1, max_length=20)


class ProjectSuggestion(Contract):
    project_id: str
    reason: str = Field(min_length=5, max_length=1000)
    uncertainty: str = Field(min_length=5, max_length=1000)


class RoutingProposal(Contract):
    suggestions: list[ProjectSuggestion] = Field(max_length=5)
