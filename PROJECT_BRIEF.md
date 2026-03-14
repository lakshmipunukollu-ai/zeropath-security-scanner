# PROJECT BRIEF
# (Extracted from MASTER_PROJECT_PLAYBOOK.md — your section only)

## SENIOR ENGINEER DECISIONS — READ FIRST

Before any code is written, here are the opinionated decisions made across all 9 projects
and why. An agent should never second-guess these unless given new information.

### Stack choices made
| Project | Backend | Frontend | DB | Deploy | Rationale |
|---------|---------|---------|-----|--------|-----------|
| FSP Scheduler | TypeScript + Node.js | React + TypeScript | PostgreSQL (multi-tenant) | Azure Container Apps | TS chosen over C# — same Azure ecosystem, better AI library support, faster iteration |
| Replicated | Python + FastAPI | Next.js 14 | PostgreSQL + S3 | Docker | Python wins for LLM tooling; Next.js for real-time streaming UI |
| ServiceCore | Node.js + Express | Angular (required) | PostgreSQL | Railway | Angular required — clean REST API behind it |
| Zapier | Python + FastAPI | None (API only + optional React dashboard) | PostgreSQL + Redis | Railway | Redis for event queue durability; Python for DX-first API |
| ST6 | Java 21 + Spring Boot | TypeScript micro-frontend (React) | PostgreSQL | Docker | Java required — Spring Boot is the senior choice; React micro-frontend mounts into PA host |
| ZeroPath | Python + FastAPI | React + TypeScript | PostgreSQL | Render | Python for LLM scanning logic; React for triage dashboard |
| Medbridge | Python + FastAPI + LangGraph | None (webhook-driven) | PostgreSQL | Railway | LangGraph is the correct tool for state-machine AI agents |
| CompanyCam | Python + FastAPI | React + TypeScript | PostgreSQL | Render | Python for CV/ML inference; React for annotation UI |
| Upstream | Django + DRF | React + TypeScript | PostgreSQL | Render | Django for rapid e-commerce scaffolding; built-in admin is a bonus |

### The 4 shared modules — build these FIRST
These are the highest ROI pieces of work. Build them once, copy-scaffold into every project.

1. `shared/llm_client.py` — Claude API wrapper with retry, streaming, structured output parsing
2. `shared/auth/` — JWT auth + role-based guards (Python + TypeScript versions)
3. `shared/state_machine.py` — Generic FSM: states, transitions, guards, event log
4. `shared/queue/` — Job queue pattern: enqueue, dequeue, ack, retry (Redis + Postgres fallback)

### Build order (wave system)
**Wave 0 (Day 1):** Build shared modules. All other waves depend on these.
**Wave 1 (Days 2-3):** Zapier + ZeroPath — establish LLM pipeline + REST API patterns
**Wave 2 (Days 4-5):** Medbridge + Replicated — LLM pipeline variants, more complex AI
**Wave 3 (Days 6-8):** FSP + ST6 — complex business logic, approval flows
**Wave 4 (Days 9-11):** ServiceCore + Upstream + CompanyCam — isolated stacks, finish strong

---

## PROJECT 6: ZEROPATH — LLM SECURITY SCANNER
**Company:** ZeroPath | **Stack:** Python + FastAPI + React + TypeScript + PostgreSQL

### Company mission to impress
ZeroPath is building the AppSec platform for the LLM era. Their engineers are security
researchers first. What will impress them: sophisticated prompt engineering for vulnerability
detection, honest handling of false positives, deduplication across scans, and a triage
workflow that feels like a professional security tool (think Snyk or Semgrep, not a toy).

### Architecture
```
Render
├── api (Python + FastAPI)
│   ├── POST /auth/register  /auth/login
│   ├── POST /scans                       — submit Git repo URL
│   ├── GET  /scans/:id/status            — queued|running|complete|failed (SSE stream)
│   ├── GET  /scans/:id/findings          — structured vulnerability findings
│   ├── POST /findings/:id/triage         — mark open|false_positive|resolved
│   ├── GET  /repos/:id/history          — compare findings across scans
│   └── GET  /repos/:id/delta            — new/fixed/persisting findings
├── scanner (Python + background tasks)
│   ├── RepoCloner                        — git clone to temp dir
│   ├── FileIndexer                       — index .py files, skip tests/venv
│   ├── ContextWindowManager             — smart chunking with overlap
│   ├── VulnerabilityAnalyzer            — LLM scan with structured output
│   └── DeduplicationEngine             — identity across scans
└── ui (React + TypeScript)
    ├── ScanSubmit                        — URL input + progress
    ├── FindingsList                      — filterable by severity/type/status
    ├── FindingDetail                     — code context, explanation, triage
    ├── ScanHistory                       — timeline, delta view
    └── RepoComparison                   — side-by-side scan comparison
```

### The vulnerability scanner prompt — this is where you earn the grade
```python
SCANNER_SYSTEM_PROMPT = """You are a senior application security engineer specializing
in Python vulnerability research. You have deep expertise in OWASP Top 10, CWE classifications,
and Python-specific security patterns.

Analyze the provided Python code for security vulnerabilities. For each finding:

VULNERABILITY CLASSES TO DETECT:
- Injection: SQL injection, command injection, SSTI, path traversal
- Authentication/Authorization: broken auth, missing access controls, insecure tokens  
- Cryptography: weak algorithms, hardcoded secrets, improper key management
- Deserialization: pickle usage, yaml.load, eval/exec on user input
- Dependency issues: known vulnerable patterns (not CVE lookup — pattern-based)
- Data exposure: logging sensitive data, unencrypted storage, response leakage
- Race conditions: TOCTOU, shared state without locks
- Business logic: privilege escalation patterns, IDOR patterns

FOR EACH FINDING, PROVIDE:
- vulnerability_type: CWE-{id} where possible
- severity: critical|high|medium|low|informational
- file_path and line_number (exact)
- code_snippet: the vulnerable code (verbatim, ≤10 lines)
- description: what the vulnerability is and why it's dangerous
- attack_scenario: how an attacker would exploit this specifically
- remediation: concrete fix with code example
- confidence: high|medium|low (use low for potential false positives)
- cwe_id: CWE number if applicable

IMPORTANT: When confidence is low, say so explicitly. False positives in security
tooling destroy trust. A finding marked low-confidence is more useful than a wrong
high-confidence finding.

Return ONLY valid JSON matching the FindingSchema. No markdown, no prose."""
```

### Deduplication — what makes a professional scanner
```python
class DeduplicationEngine:
    """
    Senior insight: the hard problem in security scanners is identity.
    Same vulnerability, slightly different code = same issue or different?
    
    Strategy: stable fingerprint based on semantic content, not line numbers.
    Line numbers change when code is reformatted. Semantics are more stable.
    """
    
    def fingerprint(self, finding: Finding) -> str:
        # Normalize: strip whitespace, extract semantic tokens
        normalized_snippet = self._normalize_code(finding.code_snippet)
        return hashlib.sha256(
            f"{finding.file_path}:{finding.vulnerability_type}:{normalized_snippet}"
            .encode()
        ).hexdigest()[:16]
    
    def classify_delta(
        self,
        prev_scan: list[Finding],
        curr_scan: list[Finding]
    ) -> ScanDelta:
        prev_fps = {self.fingerprint(f): f for f in prev_scan}
        curr_fps = {self.fingerprint(f): f for f in curr_scan}
        
        return ScanDelta(
            new=     [f for fp, f in curr_fps.items() if fp not in prev_fps],
            fixed=   [f for fp, f in prev_fps.items() if fp not in curr_fps],
            persisting=[f for fp, f in curr_fps.items() if fp in prev_fps],
        )
```

### CLAUDE.md for ZeroPath agent
```
You are a senior Python security engineer building an LLM-powered vulnerability scanner for ZeroPath.

COMPANY MISSION: Make AppSec accessible to developers who aren't security experts.
This is for AppSec engineers who need to triage hundreds of findings efficiently.

WHAT WILL IMPRESS THEM:
1. Prompt engineering depth — vulnerability taxonomy, CWE IDs, attack scenarios
2. Honest confidence scores — false positives kill trust in security tooling
3. Deduplication using semantic fingerprints (not line numbers)
4. Delta analysis: new/fixed/persisting findings across scans
5. The README explains your prompt design decisions and how you handle LLM limitations

SCANNING STRATEGY: Chunk files with overlap (preserve function context), scan in parallel,
deduplicate, rank by severity. Don't scan test files or venv directories.

NEVER: High confidence on ambiguous findings — use low confidence + explanation
ALWAYS: Include exact file_path + line_number, attack_scenario, concrete remediation
```

---


## SHARED MODULES — BUILD THESE IN WAVE 0

### shared/llm_client.py
```python
"""
Shared Claude API client. Used by: Replicated, ZeroPath, Medbridge, CompanyCam, FSP, Upstream.
Copy this file into each Python project that needs it.
"""
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import json

client = anthropic.Anthropic()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def complete(
    prompt: str,
    system: str = "",
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    as_json: bool = False,
) -> str | dict:
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text
    if as_json:
        # Strip markdown fences if present
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(clean)
    return text

async def analyze_image(
    image_b64: str,
    prompt: str,
    system: str = "",
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return json.loads(message.content[0].text)
```

### shared/auth.py (Python version)
```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(user_id: str, role: str) -> str:
    return jwt.encode(
        {"sub": user_id, "role": role, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY, algorithm=ALGORITHM
    )

def require_role(*roles: str):
    def dependency(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("role") not in roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    return dependency

# Usage: @router.get("/admin", dependencies=[Depends(require_role("admin", "manager"))])
```

### shared/state_machine.py
```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable
from datetime import datetime

S = TypeVar('S')  # State type
E = TypeVar('E')  # Event type

@dataclass
class Transition(Generic[S, E]):
    from_state: S
    event: E
    to_state: S
    guard: Callable | None = None  # optional condition function

class StateMachine(Generic[S, E]):
    def __init__(self, initial: S, transitions: list[Transition]):
        self.state = initial
        self._transitions = {(t.from_state, t.event): t for t in transitions}
        self._log: list[dict] = []

    def transition(self, event: E, context: dict = None) -> S:
        key = (self.state, event)
        t = self._transitions.get(key)
        if not t:
            raise ValueError(f"Invalid transition: {self.state} + {event}")
        if t.guard and not t.guard(context or {}):
            raise ValueError(f"Guard failed: {self.state} + {event}")
        prev = self.state
        self.state = t.to_state
        self._log.append({"from": prev, "event": event, "to": self.state, "at": datetime.utcnow().isoformat()})
        return self.state

    @property
    def history(self) -> list[dict]:
        return self._log.copy()
```

---
