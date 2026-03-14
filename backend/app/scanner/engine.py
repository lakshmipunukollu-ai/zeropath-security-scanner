"""
Scanner engine: clones repos, indexes files, sends to LLM for analysis,
stores findings with deduplication.
"""
import os
import json
import shutil
import subprocess
import tempfile
import logging
from datetime import datetime

from app.models.base import SessionLocal
from app.models.scan import Scan
from app.models.finding import Finding
from app.scanner.prompts import SCANNER_SYSTEM_PROMPT
from app.scanner.deduplication import DeduplicationEngine
from app.config import settings

logger = logging.getLogger(__name__)
dedup = DeduplicationEngine()

SKIP_DIRS = {"tests", "test", "venv", ".venv", "__pycache__", "node_modules", ".git", ".tox", "env"}
MAX_FILE_SIZE = 100_000  # 100KB
CHUNK_SIZE = 3000  # characters per chunk
CHUNK_OVERLAP = 500  # overlap to preserve function context


def run_scan(scan_id: str):
    """Main scan pipeline — runs in background thread."""
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return

        scan.status = "running"
        scan.started_at = datetime.utcnow()
        db.commit()

        # Step 1: Clone repo
        tmp_dir = tempfile.mkdtemp(prefix="zeropath_")
        try:
            repo_url = scan.repo.url
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, tmp_dir],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                scan.status = "failed"
                scan.error_message = f"Git clone failed: {result.stderr[:500]}"
                scan.completed_at = datetime.utcnow()
                db.commit()
                return

            # Step 2: Index Python files
            py_files = _index_python_files(tmp_dir)
            scan.files_scanned = len(py_files)
            db.commit()

            if not py_files:
                scan.status = "complete"
                scan.completed_at = datetime.utcnow()
                db.commit()
                return

            # Step 3: Analyze each file
            all_findings = []
            for file_path, rel_path in py_files:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if len(content.strip()) < 10:
                        continue

                    chunks = _chunk_code(content, rel_path)
                    for chunk in chunks:
                        findings = _analyze_chunk(chunk, rel_path)
                        all_findings.extend(findings)
                except Exception as e:
                    logger.warning(f"Error analyzing {rel_path}: {e}")

            # Step 4: Store findings with deduplication
            seen_fingerprints = set()
            for finding_data in all_findings:
                finding = Finding(
                    scan_id=scan.id,
                    vulnerability_type=finding_data.get("vulnerability_type", "Unknown"),
                    cwe_id=finding_data.get("cwe_id"),
                    severity=finding_data.get("severity", "medium"),
                    confidence=finding_data.get("confidence", "medium"),
                    file_path=finding_data.get("file_path", ""),
                    line_number=finding_data.get("line_number", 0),
                    code_snippet=finding_data.get("code_snippet", ""),
                    description=finding_data.get("description", ""),
                    attack_scenario=finding_data.get("attack_scenario", ""),
                    remediation=finding_data.get("remediation", ""),
                    fingerprint="",
                )
                fp = dedup.fingerprint(finding)
                if fp in seen_fingerprints:
                    continue
                seen_fingerprints.add(fp)
                finding.fingerprint = fp
                db.add(finding)

            scan.status = "complete"
            scan.completed_at = datetime.utcnow()
            db.commit()

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}")
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = "failed"
                scan.error_message = str(e)[:500]
                scan.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _index_python_files(root_dir: str) -> list:
    """Find all .py files, skipping test/venv directories."""
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root_dir)
            if os.path.getsize(full_path) <= MAX_FILE_SIZE:
                py_files.append((full_path, rel_path))

    return py_files


def _chunk_code(content: str, file_path: str) -> list:
    """Split code into overlapping chunks to preserve function boundaries."""
    if len(content) <= CHUNK_SIZE:
        return [content]

    chunks = []
    start = 0
    while start < len(content):
        end = start + CHUNK_SIZE
        chunk = content[start:end]
        chunks.append(chunk)
        start = end - CHUNK_OVERLAP

    return chunks


def _analyze_chunk(code: str, file_path: str) -> list:
    """Send code chunk to LLM for vulnerability analysis."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = f"File: {file_path}\n\n```python\n{code}\n```"

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SCANNER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        result = json.loads(text)
        findings = result.get("findings", [])

        # Ensure file_path is set
        for f in findings:
            if not f.get("file_path"):
                f["file_path"] = file_path

        return findings

    except Exception as e:
        logger.warning(f"LLM analysis failed for {file_path}: {e}")
        return []
