from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.repository import Repository
from app.models.scan import Scan
from app.models.finding import Finding
from app.auth import get_current_user
from app.schemas.scan import ScanResponse
from app.schemas.finding import FindingResponse, DeltaResponse
from app.scanner.deduplication import DeduplicationEngine

router = APIRouter(tags=["repos"])

dedup = DeduplicationEngine()


@router.get("/repos/{repo_id}/history")
def get_repo_history(
    repo_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user["id"],
    ).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    scans = db.query(Scan).filter(Scan.repo_id == repo_id).order_by(Scan.created_at.desc()).all()
    return {
        "repo": {"id": repo.id, "url": repo.url, "name": repo.name},
        "scans": [
            ScanResponse(
                id=s.id,
                repo_id=s.repo_id,
                status=s.status,
                files_scanned=s.files_scanned or 0,
                started_at=s.started_at.isoformat() if s.started_at else None,
                completed_at=s.completed_at.isoformat() if s.completed_at else None,
                created_at=s.created_at.isoformat() if s.created_at else "",
            )
            for s in scans
        ],
    }


@router.get("/repos/{repo_id}/delta", response_model=DeltaResponse)
def get_repo_delta(
    repo_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user["id"],
    ).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    scans = db.query(Scan).filter(
        Scan.repo_id == repo_id,
        Scan.status == "complete",
    ).order_by(Scan.created_at.desc()).limit(2).all()

    if len(scans) < 2:
        # Not enough scans for delta, return current findings as "new"
        if scans:
            findings = db.query(Finding).filter(Finding.scan_id == scans[0].id).all()
            return _build_delta_response(findings, [], [])
        return _build_delta_response([], [], [])

    curr_findings = db.query(Finding).filter(Finding.scan_id == scans[0].id).all()
    prev_findings = db.query(Finding).filter(Finding.scan_id == scans[1].id).all()

    delta = dedup.classify_delta(prev_findings, curr_findings)
    return _build_delta_response(delta["new"], delta["fixed"], delta["persisting"])


def _finding_to_response(f: Finding) -> FindingResponse:
    return FindingResponse(
        id=f.id,
        scan_id=f.scan_id,
        fingerprint=f.fingerprint,
        vulnerability_type=f.vulnerability_type,
        cwe_id=f.cwe_id,
        severity=f.severity,
        confidence=f.confidence,
        file_path=f.file_path,
        line_number=f.line_number,
        code_snippet=f.code_snippet,
        description=f.description,
        attack_scenario=f.attack_scenario,
        remediation=f.remediation,
        status=f.status,
        created_at=f.created_at.isoformat() if f.created_at else "",
    )


def _build_delta_response(new, fixed, persisting) -> DeltaResponse:
    return DeltaResponse(
        new=[_finding_to_response(f) for f in new],
        fixed=[_finding_to_response(f) for f in fixed],
        persisting=[_finding_to_response(f) for f in persisting],
    )
