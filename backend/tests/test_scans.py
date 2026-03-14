"""Tests for scan creation and status endpoints."""
import uuid
from unittest.mock import patch, MagicMock
from app.models.user import User
from app.models.repository import Repository
from app.models.scan import Scan
from app.models.finding import Finding
from app.auth import hash_password, create_access_token


def _make_auth(db_session):
    """Create a user and return auth headers + user_id."""
    user_id = str(uuid.uuid4())
    user = User(id=user_id, email=f"scan-{user_id[:8]}@test.com", password_hash=hash_password("pass"))
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user_id, "user")
    return {"Authorization": f"Bearer {token}"}, user_id


@patch("app.routers.scan_router.run_scan")
def test_create_scan(mock_run, client, db_session):
    """POST /scans creates a scan and returns scan info."""
    headers, _ = _make_auth(db_session)
    resp = client.post("/scans", json={"repo_url": "https://github.com/test/repo.git"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert "id" in data
    assert "repo_id" in data


@patch("app.routers.scan_router.run_scan")
def test_create_scan_creates_repo(mock_run, client, db_session):
    """POST /scans creates a Repository record for a new URL."""
    headers, _ = _make_auth(db_session)
    resp = client.post("/scans", json={"repo_url": "https://github.com/test/new-repo.git"}, headers=headers)
    assert resp.status_code == 200
    repo = db_session.query(Repository).filter(Repository.url == "https://github.com/test/new-repo.git").first()
    assert repo is not None
    assert repo.name == "new-repo"


@patch("app.routers.scan_router.run_scan")
def test_create_scan_reuses_existing_repo(mock_run, client, db_session):
    """POST /scans reuses an existing Repository for the same URL."""
    headers, _ = _make_auth(db_session)
    r1 = client.post("/scans", json={"repo_url": "https://github.com/test/shared.git"}, headers=headers)
    r2 = client.post("/scans", json={"repo_url": "https://github.com/test/shared.git"}, headers=headers)
    assert r1.json()["repo_id"] == r2.json()["repo_id"]


def test_create_scan_requires_auth(client):
    """POST /scans returns 401 without token."""
    resp = client.post("/scans", json={"repo_url": "https://github.com/test/repo"})
    assert resp.status_code == 401


def test_get_scan_status(client, db_session):
    """GET /scans/:id/status returns scan status."""
    headers, user_id = _make_auth(db_session)
    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/t/r.git", name="r")
    db_session.add(repo)
    db_session.flush()
    scan = Scan(id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id, status="running", files_scanned=5)
    db_session.add(scan)
    db_session.commit()

    resp = client.get(f"/scans/{scan.id}/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == scan.id
    assert data["status"] == "running"
    assert data["files_scanned"] == 5


def test_get_scan_status_not_found(client, db_session):
    """GET /scans/:id/status returns 404 for unknown scan."""
    headers, _ = _make_auth(db_session)
    resp = client.get(f"/scans/{uuid.uuid4()}/status", headers=headers)
    assert resp.status_code == 404


def test_get_scan_findings_empty(client, db_session):
    """GET /scans/:id/findings returns empty list for scan with no findings."""
    headers, user_id = _make_auth(db_session)
    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/t/e.git", name="e")
    db_session.add(repo)
    db_session.flush()
    scan = Scan(id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id, status="complete")
    db_session.add(scan)
    db_session.commit()

    resp = client.get(f"/scans/{scan.id}/findings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["findings"] == []
    assert data["total"] == 0


def test_get_scan_findings_with_data(client, db_session):
    """GET /scans/:id/findings returns findings."""
    headers, user_id = _make_auth(db_session)
    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/t/d.git", name="d")
    db_session.add(repo)
    db_session.flush()
    scan = Scan(id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id, status="complete")
    db_session.add(scan)
    db_session.flush()
    finding = Finding(
        id=str(uuid.uuid4()), scan_id=scan.id, fingerprint="abc123",
        vulnerability_type="SQL Injection", cwe_id="CWE-89",
        severity="critical", confidence="high",
        file_path="app/db.py", line_number=10,
        code_snippet="cursor.execute(query)", description="SQL injection",
        attack_scenario="Inject SQL", remediation="Use params", status="open",
    )
    db_session.add(finding)
    db_session.commit()

    resp = client.get(f"/scans/{scan.id}/findings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["findings"][0]["vulnerability_type"] == "SQL Injection"


def test_get_scan_findings_filter_severity(client, db_session):
    """GET /scans/:id/findings?severity=critical filters by severity."""
    headers, user_id = _make_auth(db_session)
    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/t/f.git", name="f")
    db_session.add(repo)
    db_session.flush()
    scan = Scan(id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id, status="complete")
    db_session.add(scan)
    db_session.flush()

    for sev in ["critical", "low"]:
        db_session.add(Finding(
            id=str(uuid.uuid4()), scan_id=scan.id, fingerprint=f"fp-{sev}",
            vulnerability_type="Test", severity=sev, confidence="high",
            file_path="t.py", line_number=1, code_snippet="c",
            description="d", attack_scenario="a", remediation="r", status="open",
        ))
    db_session.commit()

    resp = client.get(f"/scans/{scan.id}/findings?severity=critical", headers=headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["findings"][0]["severity"] == "critical"


def test_get_scan_findings_filter_status(client, db_session):
    """GET /scans/:id/findings?status=open filters by status."""
    headers, user_id = _make_auth(db_session)
    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/t/s.git", name="s")
    db_session.add(repo)
    db_session.flush()
    scan = Scan(id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id, status="complete")
    db_session.add(scan)
    db_session.flush()

    for st in ["open", "resolved"]:
        db_session.add(Finding(
            id=str(uuid.uuid4()), scan_id=scan.id, fingerprint=f"fp-{st}",
            vulnerability_type="T", severity="medium", confidence="medium",
            file_path="t.py", line_number=1, code_snippet="c",
            description="d", attack_scenario="a", remediation="r", status=st,
        ))
    db_session.commit()

    resp = client.get(f"/scans/{scan.id}/findings?status=open", headers=headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["findings"][0]["status"] == "open"
