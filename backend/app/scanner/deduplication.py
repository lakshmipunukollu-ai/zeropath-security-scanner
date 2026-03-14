import hashlib
import re


class DeduplicationEngine:
    """
    Semantic fingerprinting for vulnerability deduplication.
    Uses file_path + vulnerability_type + normalized code to create stable identities
    that survive code reformatting and line number changes.
    """

    def _normalize_code(self, code: str) -> str:
        """Strip whitespace, comments, and normalize variable names for stable fingerprinting."""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code).strip()
        # Remove string contents (replace with placeholder)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        return code

    def fingerprint(self, finding) -> str:
        """Generate a stable semantic fingerprint for a finding."""
        normalized = self._normalize_code(finding.code_snippet or "")
        raw = f"{finding.file_path}:{finding.vulnerability_type}:{normalized}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def classify_delta(self, prev_findings: list, curr_findings: list) -> dict:
        """Classify findings as new, fixed, or persisting by comparing fingerprints."""
        prev_fps = {self.fingerprint(f): f for f in prev_findings}
        curr_fps = {self.fingerprint(f): f for f in curr_findings}

        return {
            "new": [f for fp, f in curr_fps.items() if fp not in prev_fps],
            "fixed": [f for fp, f in prev_fps.items() if fp not in curr_fps],
            "persisting": [f for fp, f in curr_fps.items() if fp in prev_fps],
        }
