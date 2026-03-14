"""Seed the database with sample data for development."""
import uuid
from datetime import datetime, timedelta
from app.models.base import SessionLocal, engine, Base
from app.models.user import User
from app.models.repository import Repository
from app.models.scan import Scan
from app.models.finding import Finding
from app.auth import hash_password
from app.scanner.deduplication import DeduplicationEngine

dedup = DeduplicationEngine()


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already seeded.")
            return

        # Create demo user
        user = User(
            id=str(uuid.uuid4()),
            email="demo@zeropath.com",
            password_hash=hash_password("password123"),
            role="admin",
        )
        db.add(user)
        db.flush()

        # Create sample repo
        repo = Repository(
            id=str(uuid.uuid4()),
            user_id=user.id,
            url="https://github.com/example/vulnerable-app",
            name="vulnerable-app",
        )
        db.add(repo)
        db.flush()

        # Create completed scan
        scan = Scan(
            id=str(uuid.uuid4()),
            repo_id=repo.id,
            user_id=user.id,
            status="complete",
            started_at=datetime.utcnow() - timedelta(minutes=5),
            completed_at=datetime.utcnow(),
            files_scanned=12,
        )
        db.add(scan)
        db.flush()

        # Create sample findings
        sample_findings = [
            {
                "vulnerability_type": "SQL Injection",
                "cwe_id": "CWE-89",
                "severity": "critical",
                "confidence": "high",
                "file_path": "app/db/queries.py",
                "line_number": 42,
                "code_snippet": 'query = f"SELECT * FROM users WHERE id = {user_id}"\ncursor.execute(query)',
                "description": "User-controlled input is directly interpolated into a SQL query string, enabling SQL injection attacks.",
                "attack_scenario": "An attacker could supply a crafted user_id like '1 OR 1=1' to dump the entire users table, or use UNION-based injection to extract data from other tables.",
                "remediation": "Use parameterized queries:\ncursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                "status": "open",
            },
            {
                "vulnerability_type": "Command Injection",
                "cwe_id": "CWE-78",
                "severity": "critical",
                "confidence": "high",
                "file_path": "app/utils/system.py",
                "line_number": 15,
                "code_snippet": 'os.system(f"ping {host}")',
                "description": "User input is passed directly to os.system(), allowing arbitrary command execution.",
                "attack_scenario": "An attacker could provide host='127.0.0.1; rm -rf /' to execute arbitrary system commands on the server.",
                "remediation": "Use subprocess.run with shell=False:\nsubprocess.run(['ping', host], capture_output=True)",
                "status": "open",
            },
            {
                "vulnerability_type": "Hardcoded Secret",
                "cwe_id": "CWE-798",
                "severity": "high",
                "confidence": "high",
                "file_path": "app/config.py",
                "line_number": 8,
                "code_snippet": 'API_KEY = "sk-1234567890abcdef"',
                "description": "An API key is hardcoded in the source code, which may be exposed through version control.",
                "attack_scenario": "An attacker with access to the repository could extract the API key and use it to authenticate as the application.",
                "remediation": "Use environment variables:\nAPI_KEY = os.getenv('API_KEY')",
                "status": "open",
            },
            {
                "vulnerability_type": "Insecure Deserialization",
                "cwe_id": "CWE-502",
                "severity": "high",
                "confidence": "medium",
                "file_path": "app/cache/loader.py",
                "line_number": 23,
                "code_snippet": "data = pickle.loads(request.data)",
                "description": "Untrusted data is deserialized using pickle, which can execute arbitrary code during deserialization.",
                "attack_scenario": "An attacker could craft a malicious pickle payload that executes arbitrary code when deserialized by the server.",
                "remediation": "Use JSON or a safe deserialization format:\ndata = json.loads(request.data)",
                "status": "open",
            },
            {
                "vulnerability_type": "Path Traversal",
                "cwe_id": "CWE-22",
                "severity": "medium",
                "confidence": "medium",
                "file_path": "app/files/download.py",
                "line_number": 31,
                "code_snippet": 'file_path = os.path.join("/uploads", filename)\nwith open(file_path, "rb") as f:',
                "description": "User-controlled filename is used in file path construction without sanitization, allowing directory traversal.",
                "attack_scenario": "An attacker could request filename='../../etc/passwd' to read arbitrary files from the server.",
                "remediation": "Validate and sanitize the filename:\nfilename = os.path.basename(filename)\nfile_path = os.path.join('/uploads', filename)",
                "status": "open",
            },
            {
                "vulnerability_type": "Missing Authentication",
                "cwe_id": "CWE-306",
                "severity": "medium",
                "confidence": "low",
                "file_path": "app/api/admin.py",
                "line_number": 10,
                "code_snippet": '@app.route("/admin/users")\ndef list_users():\n    return jsonify(User.query.all())',
                "description": "Admin endpoint lacks authentication check, potentially exposing user data to unauthenticated requests.",
                "attack_scenario": "Any unauthenticated user could access the admin user listing endpoint and enumerate all users in the system.",
                "remediation": "Add authentication decorator:\n@app.route('/admin/users')\n@require_admin\ndef list_users():",
                "status": "open",
            },
        ]

        for fd in sample_findings:
            finding = Finding(
                id=str(uuid.uuid4()),
                scan_id=scan.id,
                vulnerability_type=fd["vulnerability_type"],
                cwe_id=fd["cwe_id"],
                severity=fd["severity"],
                confidence=fd["confidence"],
                file_path=fd["file_path"],
                line_number=fd["line_number"],
                code_snippet=fd["code_snippet"],
                description=fd["description"],
                attack_scenario=fd["attack_scenario"],
                remediation=fd["remediation"],
                status=fd["status"],
                fingerprint="",
            )
            finding.fingerprint = dedup.fingerprint(finding)
            db.add(finding)

        db.commit()
        print(f"Seeded: 1 user, 1 repo, 1 scan, {len(sample_findings)} findings")
        print(f"Login: demo@zeropath.com / password123")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
