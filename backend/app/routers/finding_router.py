from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.finding import Finding
from app.models.scan import Scan
from app.auth import get_current_user
from app.schemas.finding import FindingResponse, TriageRequest

router = APIRouter(tags=["findings"])

VALID_STATUSES = {"open", "false_positive", "resolved"}


@router.post("/findings/{finding_id}/triage", response_model=FindingResponse)
def triage_finding(
    finding_id: str,
    req: TriageRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")

    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    # Verify user owns the scan
    scan = db.query(Scan).filter(Scan.id == finding.scan_id, Scan.user_id == current_user["id"]).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Finding not found")

    finding.status = req.status
    db.commit()
    db.refresh(finding)

    return FindingResponse(
        id=finding.id,
        scan_id=finding.scan_id,
        fingerprint=finding.fingerprint,
        vulnerability_type=finding.vulnerability_type,
        cwe_id=finding.cwe_id,
        severity=finding.severity,
        confidence=finding.confidence,
        file_path=finding.file_path,
        line_number=finding.line_number,
        code_snippet=finding.code_snippet,
        description=finding.description,
        attack_scenario=finding.attack_scenario,
        remediation=finding.remediation,
        status=finding.status,
        created_at=finding.created_at.isoformat() if finding.created_at else "",
    )
