"""Tests for deduplication engine."""
from app.scanner.deduplication import DeduplicationEngine


class MockFinding:
    """Mock finding object for testing deduplication."""
    def __init__(self, file_path, vulnerability_type, code_snippet):
        self.file_path = file_path
        self.vulnerability_type = vulnerability_type
        self.code_snippet = code_snippet


def test_fingerprint_stability():
    """Same finding should produce the same fingerprint."""
    dedup = DeduplicationEngine()
    f1 = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")
    f2 = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")
    assert dedup.fingerprint(f1) == dedup.fingerprint(f2)


def test_fingerprint_different_for_different_files():
    """Different file paths should produce different fingerprints."""
    dedup = DeduplicationEngine()
    f1 = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")
    f2 = MockFinding("app/models.py", "SQL Injection", "cursor.execute(query)")
    assert dedup.fingerprint(f1) != dedup.fingerprint(f2)


def test_fingerprint_different_for_different_types():
    """Different vulnerability types should produce different fingerprints."""
    dedup = DeduplicationEngine()
    f1 = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")
    f2 = MockFinding("app/db.py", "Command Injection", "cursor.execute(query)")
    assert dedup.fingerprint(f1) != dedup.fingerprint(f2)


def test_fingerprint_whitespace_insensitive():
    """Fingerprints should be stable across extra whitespace/newlines."""
    dedup = DeduplicationEngine()
    f1 = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)\n\n")
    f2 = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)  ")
    assert dedup.fingerprint(f1) == dedup.fingerprint(f2)


def test_fingerprint_comment_insensitive():
    """Fingerprints should be stable across comment changes."""
    dedup = DeduplicationEngine()
    f1 = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)  # dangerous")
    f2 = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")
    assert dedup.fingerprint(f1) == dedup.fingerprint(f2)


def test_fingerprint_length():
    """Fingerprints should be 16 chars (SHA256 truncated)."""
    dedup = DeduplicationEngine()
    f = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")
    fp = dedup.fingerprint(f)
    assert len(fp) == 16
    # Should be hex characters
    assert all(c in "0123456789abcdef" for c in fp)


def test_classify_delta_new():
    """New findings should be classified as 'new'."""
    dedup = DeduplicationEngine()
    prev = []
    curr = [MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")]
    delta = dedup.classify_delta(prev, curr)
    assert len(delta["new"]) == 1
    assert len(delta["fixed"]) == 0
    assert len(delta["persisting"]) == 0


def test_classify_delta_fixed():
    """Fixed findings should be classified as 'fixed'."""
    dedup = DeduplicationEngine()
    prev = [MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")]
    curr = []
    delta = dedup.classify_delta(prev, curr)
    assert len(delta["new"]) == 0
    assert len(delta["fixed"]) == 1
    assert len(delta["persisting"]) == 0


def test_classify_delta_persisting():
    """Persisting findings should be classified as 'persisting'."""
    dedup = DeduplicationEngine()
    f = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")
    prev = [f]
    curr = [MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")]
    delta = dedup.classify_delta(prev, curr)
    assert len(delta["new"]) == 0
    assert len(delta["fixed"]) == 0
    assert len(delta["persisting"]) == 1


def test_classify_delta_mixed():
    """Mixed scenario with new, fixed, and persisting findings."""
    dedup = DeduplicationEngine()
    shared = MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)")
    old_only = MockFinding("app/auth.py", "Weak Crypto", "md5.digest()")
    new_only = MockFinding("app/api.py", "XSS", "render(input)")

    prev = [shared, old_only]
    curr = [
        MockFinding("app/db.py", "SQL Injection", "cursor.execute(query)"),
        new_only,
    ]
    delta = dedup.classify_delta(prev, curr)
    assert len(delta["new"]) == 1
    assert len(delta["fixed"]) == 1
    assert len(delta["persisting"]) == 1


def test_normalize_code():
    """Code normalization should strip comments and whitespace."""
    dedup = DeduplicationEngine()
    code = '  cursor.execute(query)  # execute the query  '
    normalized = dedup._normalize_code(code)
    assert "#" not in normalized
    assert "  " not in normalized  # no double spaces
