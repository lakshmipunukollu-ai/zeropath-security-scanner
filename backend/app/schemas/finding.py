from pydantic import BaseModel
from typing import Optional, List


class FindingResponse(BaseModel):
    id: str
    scan_id: str
    fingerprint: str
    vulnerability_type: str
    cwe_id: Optional[str] = None
    severity: str
    confidence: str
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    attack_scenario: str
    remediation: str
    status: str
    created_at: str

    class Config:
        from_attributes = True


class FindingsListResponse(BaseModel):
    findings: List[FindingResponse]
    total: int


class TriageRequest(BaseModel):
    status: str  # open, false_positive, resolved


class DeltaResponse(BaseModel):
    new: List[FindingResponse]
    fixed: List[FindingResponse]
    persisting: List[FindingResponse]
