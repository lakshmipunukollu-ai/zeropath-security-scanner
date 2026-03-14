def test_register(client):
    resp = client.post("/auth/register", json={"email": "user@test.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "user@test.com"


def test_register_duplicate(client):
    client.post("/auth/register", json={"email": "dup@test.com", "password": "pass123"})
    resp = client.post("/auth/register", json={"email": "dup@test.com", "password": "pass123"})
    assert resp.status_code == 400


def test_login(client):
    client.post("/auth/register", json={"email": "login@test.com", "password": "pass123"})
    resp = client.post("/auth/login", json={"email": "login@test.com", "password": "pass123"})
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "wrong@test.com", "password": "pass123"})
    resp = client.post("/auth/login", json={"email": "wrong@test.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_protected_endpoint_no_token(client):
    resp = client.post("/scans", json={"repo_url": "https://github.com/test/repo"})
    assert resp.status_code == 401
