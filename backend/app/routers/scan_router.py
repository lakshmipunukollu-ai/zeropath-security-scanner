import threading
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.models.repository import Repository
from app.models.scan import Scan
from app.models.finding import Finding
from app.auth import get_current_user
from app.schemas.scan import ScanCreateRequest, ScanResponse, ScanStatusResponse
from app.schemas.finding import FindingResponse, FindingsListResponse
from app.scanner.engine import run_scan

router = APIRouter(tags=["scans"])


def _extract_repo_name(url: str) -> str:
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


@router.post("/scans", response_model=ScanResponse)
def create_scan(req: ScanCreateRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Find or create repository
    repo = db.query(Repository).filter(
        Repository.url == req.repo_url,
        Repository.user_id == current_user["id"],
    ).first()

    if not repo:
        repo = Repository(
            url=req.repo_url,
            name=_extract_repo_name(req.repo_url),
            user_id=current_user["id"],
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

    scan = Scan(
        repo_id=repo.id,
        user_id=current_user["id"],
        status="queued",
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Start scan in background thread
    thread = threading.Thread(target=run_scan, args=(scan.id,), daemon=True)
    thread.start()

    return ScanResponse(
        id=scan.id,
        repo_id=scan.repo_id,
        status=scan.status,
        files_scanned=scan.files_scanned or 0,
        created_at=scan.created_at.isoformat() if scan.created_at else "",
    )


@router.get("/scans/{scan_id}/status", response_model=ScanStatusResponse)
def get_scan_status(scan_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == current_user["id"]).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanStatusResponse(
        id=scan.id,
        status=scan.status,
        files_scanned=scan.files_scanned or 0,
        started_at=scan.started_at.isoformat() if scan.started_at else None,
        completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
    )


@router.get("/scans/{scan_id}/findings", response_model=FindingsListResponse)
def get_scan_findings(
    scan_id: str,
    severity: str = None,
    status: str = None,
    confidence: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == current_user["id"]).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    query = db.query(Finding).filter(Finding.scan_id == scan_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    if status:
        query = query.filter(Finding.status == status)
    if confidence:
        query = query.filter(Finding.confidence == confidence)

    findings = query.all()
    return FindingsListResponse(
        findings=[
            FindingResponse(
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
            for f in findings
        ],
        total=len(findings),
    )
