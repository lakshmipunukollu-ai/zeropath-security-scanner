"""Tests for finding triage endpoint."""
import uuid
from app.models.user import User
from app.models.repository import Repository
from app.models.scan import Scan
from app.models.finding import Finding
from app.auth import hash_password, create_access_token


def _setup_finding(db_session):
    """Create user, repo, scan, finding directly in DB. Returns (headers, finding_id)."""
    user_id = str(uuid.uuid4())
    user = User(id=user_id, email=f"triage-{user_id[:8]}@test.com", password_hash=hash_password("pass123"))
    db_session.add(user)
    db_session.flush()

    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/test/repo.git", name="repo")
    db_session.add(repo)
    db_session.flush()

    scan = Scan(id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id, status="complete")
    db_session.add(scan)
    db_session.flush()

    finding_id = str(uuid.uuid4())
    finding = Finding(
        id=finding_id, scan_id=scan.id, fingerprint="triage-fp",
        vulnerability_type="Command Injection", cwe_id="CWE-78",
        severity="critical", confidence="high",
        file_path="app/utils.py", line_number=15,
        code_snippet='os.system(f"ping {host}")',
        description="Command injection", attack_scenario="Inject commands",
        remediation="Use subprocess", status="open",
    )
    db_session.add(finding)
    db_session.commit()

    token = create_access_token(user_id, "user")
    headers = {"Authorization": f"Bearer {token}"}
    return headers, finding_id


def test_triage_finding_to_false_positive(client, db_session):
    """POST /findings/:id/triage can mark as false_positive."""
    headers, finding_id = _setup_finding(db_session)
    resp = client.post(f"/findings/{finding_id}/triage", json={"status": "false_positive"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "false_positive"


def test_triage_finding_to_resolved(client, db_session):
    """POST /findings/:id/triage can mark as resolved."""
    headers, finding_id = _setup_finding(db_session)
    resp = client.post(f"/findings/{finding_id}/triage", json={"status": "resolved"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


def test_triage_finding_back_to_open(client, db_session):
    """POST /findings/:id/triage can revert to open."""
    headers, finding_id = _setup_finding(db_session)
    client.post(f"/findings/{finding_id}/triage", json={"status": "resolved"}, headers=headers)
    resp = client.post(f"/findings/{finding_id}/triage", json={"status": "open"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"


def test_triage_finding_invalid_status(client, db_session):
    """POST /findings/:id/triage rejects invalid status."""
    headers, finding_id = _setup_finding(db_session)
    resp = client.post(f"/findings/{finding_id}/triage", json={"status": "invalid"}, headers=headers)
    assert resp.status_code == 400


def test_triage_finding_not_found(client, db_session):
    """POST /findings/:id/triage returns 404 for unknown finding."""
    headers, _ = _setup_finding(db_session)
    resp = client.post(f"/findings/{uuid.uuid4()}/triage", json={"status": "resolved"}, headers=headers)
    assert resp.status_code == 404


def test_triage_requires_auth(client):
    """POST /findings/:id/triage returns 401 without token."""
    resp = client.post(f"/findings/{uuid.uuid4()}/triage", json={"status": "resolved"})
    assert resp.status_code == 401
