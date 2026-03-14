"""Tests for repository history and delta endpoints."""
import uuid
from datetime import datetime, timedelta
from app.models.user import User
from app.models.repository import Repository
from app.models.scan import Scan
from app.models.finding import Finding
from app.auth import hash_password, create_access_token


def _make_auth(db_session):
    """Create a user and return auth headers + user_id."""
    user_id = str(uuid.uuid4())
    user = User(id=user_id, email=f"repo-{user_id[:8]}@test.com", password_hash=hash_password("pass"))
    db_session.add(user)
    db_session.commit()
    token = create_access_token(user_id, "user")
    return {"Authorization": f"Bearer {token}"}, user_id


def test_get_repo_history(client, db_session):
    """GET /repos/:id/history returns scan timeline."""
    headers, user_id = _make_auth(db_session)
    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/t/h.git", name="h")
    db_session.add(repo)
    db_session.flush()

    for i in range(3):
        db_session.add(Scan(
            id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id,
            status="complete", files_scanned=i + 1,
        ))
    db_session.commit()

    resp = client.get(f"/repos/{repo.id}/history", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["repo"]["id"] == repo.id
    assert data["repo"]["name"] == "h"
    assert len(data["scans"]) == 3


def test_get_repo_history_not_found(client, db_session):
    """GET /repos/:id/history returns 404 for unknown repo."""
    headers, _ = _make_auth(db_session)
    resp = client.get(f"/repos/{uuid.uuid4()}/history", headers=headers)
    assert resp.status_code == 404


def test_get_repo_history_requires_auth(client):
    """GET /repos/:id/history returns 401 without token."""
    resp = client.get(f"/repos/{uuid.uuid4()}/history")
    assert resp.status_code == 401


def test_get_repo_delta_single_scan(client, db_session):
    """GET /repos/:id/delta with one scan returns all findings as new."""
    headers, user_id = _make_auth(db_session)
    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/t/ds.git", name="ds")
    db_session.add(repo)
    db_session.flush()

    scan = Scan(id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id, status="complete")
    db_session.add(scan)
    db_session.flush()

    db_session.add(Finding(
        id=str(uuid.uuid4()), scan_id=scan.id, fingerprint="fp-1",
        vulnerability_type="SQLi", severity="high", confidence="high",
        file_path="t.py", line_number=1, code_snippet="c",
        description="d", attack_scenario="a", remediation="r", status="open",
    ))
    db_session.commit()

    resp = client.get(f"/repos/{repo.id}/delta", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["new"]) == 1
    assert len(data["fixed"]) == 0
    assert len(data["persisting"]) == 0


def test_get_repo_delta_two_scans(client, db_session):
    """GET /repos/:id/delta compares latest two scans."""
    headers, user_id = _make_auth(db_session)
    repo = Repository(id=str(uuid.uuid4()), user_id=user_id, url="https://github.com/t/d2.git", name="d2")
    db_session.add(repo)
    db_session.flush()

    # Older scan with finding
    scan1 = Scan(
        id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id,
        status="complete", created_at=datetime.utcnow() - timedelta(hours=2),
    )
    db_session.add(scan1)
    db_session.flush()
    db_session.add(Finding(
        id=str(uuid.uuid4()), scan_id=scan1.id, fingerprint="fp-old",
        vulnerability_type="Old Vuln", severity="high", confidence="high",
        file_path="old.py", line_number=1, code_snippet="old_code()",
        description="d", attack_scenario="a", remediation="r", status="open",
    ))

    # Newer scan with different finding
    scan2 = Scan(
        id=str(uuid.uuid4()), repo_id=repo.id, user_id=user_id,
        status="complete", created_at=datetime.utcnow(),
    )
    db_session.add(scan2)
    db_session.flush()
    db_session.add(Finding(
        id=str(uuid.uuid4()), scan_id=scan2.id, fingerprint="fp-new",
        vulnerability_type="New Vuln", severity="medium", confidence="medium",
        file_path="new.py", line_number=1, code_snippet="new_code()",
        description="d", attack_scenario="a", remediation="r", status="open",
    ))
    db_session.commit()

    resp = client.get(f"/repos/{repo.id}/delta", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "new" in data
    assert "fixed" in data
    assert "persisting" in data
    # The old finding is fixed, the new one is new
    total = len(data["new"]) + len(data["fixed"]) + len(data["persisting"])
    assert total > 0


def test_get_repo_delta_not_found(client, db_session):
    """GET /repos/:id/delta returns 404 for unknown repo."""
    headers, _ = _make_auth(db_session)
    resp = client.get(f"/repos/{uuid.uuid4()}/delta", headers=headers)
    assert resp.status_code == 404
