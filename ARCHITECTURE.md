# ZeroPath Security Scanner — Architecture

## Overview

ZeroPath is an LLM-powered security vulnerability scanner for Python codebases. Users submit a Git repository URL, the system clones and analyzes the code using Claude, and presents structured vulnerability findings in a professional triage dashboard.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    React Frontend                    │
│  ScanSubmit │ FindingsList │ FindingDetail │ History │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                      │
│  Auth │ Scans │ Findings │ Repos │ Health            │
└──────┬────────────────────────────┬─────────────────┘
       │                            │
┌──────▼──────┐            ┌───────▼────────┐
│ PostgreSQL  │            │ Scanner Engine │
│  (all data) │            │ (background)   │
└─────────────┘            └────────────────┘
```

## Data Models

### User
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| email | String(255) | Unique, indexed |
| password_hash | String(255) | bcrypt |
| role | String(50) | "user" or "admin" |
| created_at | DateTime | UTC |

### Repository
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| user_id | UUID | FK → User |
| url | String(500) | Git clone URL |
| name | String(255) | Extracted repo name |
| created_at | DateTime | UTC |

### Scan
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| repo_id | UUID | FK → Repository |
| user_id | UUID | FK → User |
| status | String(50) | queued, running, complete, failed |
| started_at | DateTime | Nullable |
| completed_at | DateTime | Nullable |
| files_scanned | Integer | Default 0 |
| error_message | Text | Nullable |
| created_at | DateTime | UTC |

### Finding
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| scan_id | UUID | FK → Scan |
| fingerprint | String(16) | Semantic dedup hash |
| vulnerability_type | String(100) | e.g. "SQL Injection" |
| cwe_id | String(20) | e.g. "CWE-89" |
| severity | String(20) | critical, high, medium, low, informational |
| confidence | String(20) | high, medium, low |
| file_path | String(500) | Relative path in repo |
| line_number | Integer | |
| code_snippet | Text | Verbatim code (≤10 lines) |
| description | Text | What and why |
| attack_scenario | Text | Exploitation details |
| remediation | Text | Fix with code example |
| status | String(20) | open, false_positive, resolved |
| created_at | DateTime | UTC |

## API Contracts

### Authentication
```
POST /auth/register
  Body: { email: string, password: string }
  Response: { id: string, email: string, token: string }

POST /auth/login
  Body: { email: string, password: string }
  Response: { token: string, user: { id: string, email: string, role: string } }
```

### Scans
```
POST /scans
  Auth: Bearer token
  Body: { repo_url: string }
  Response: { id: string, repo_id: string, status: "queued" }

GET /scans/:id/status
  Auth: Bearer token
  Response: { id: string, status: string, files_scanned: int, started_at: string, completed_at: string }

GET /scans/:id/findings
  Auth: Bearer token
  Query: ?severity=high&status=open&confidence=high
  Response: { findings: Finding[], total: int }
```

### Findings
```
POST /findings/:id/triage
  Auth: Bearer token
  Body: { status: "open" | "false_positive" | "resolved" }
  Response: { id: string, status: string }
```

### Repositories
```
GET /repos/:id/history
  Auth: Bearer token
  Response: { scans: Scan[] }

GET /repos/:id/delta
  Auth: Bearer token
  Response: { new: Finding[], fixed: Finding[], persisting: Finding[] }
```

### Health
```
GET /health
  Response: { status: "healthy", timestamp: string }
```

## Scanner Engine Design

### Pipeline Stages
1. **RepoCloner** — Clone git repo to temp directory
2. **FileIndexer** — Index .py files, skip tests/, venv/, __pycache__/
3. **ContextWindowManager** — Chunk files with overlap to preserve function boundaries
4. **VulnerabilityAnalyzer** — Send chunks to Claude with security analysis prompt
5. **DeduplicationEngine** — Fingerprint findings using semantic content (not line numbers)

### Deduplication Strategy
Fingerprint = SHA256(file_path + vulnerability_type + normalized_code_snippet)[:16]
- Code normalization strips whitespace, comments, standardizes variable names
- Enables delta analysis: new, fixed, persisting findings across scans

### Vulnerability Classes
- Injection: SQL injection, command injection, SSTI, path traversal
- Authentication/Authorization: broken auth, missing access controls
- Cryptography: weak algorithms, hardcoded secrets
- Deserialization: pickle, yaml.load, eval/exec
- Data exposure: logging PII, unencrypted storage
- Race conditions: TOCTOU, shared state
- Business logic: privilege escalation, IDOR

### Severity Classification
- **Critical**: Remote code execution, authentication bypass
- **High**: SQL injection, command injection, path traversal
- **Medium**: XSS, CSRF, information disclosure
- **Low**: Missing security headers, verbose errors
- **Informational**: Best practice recommendations

## Frontend Components

| Component | Purpose |
|-----------|---------|
| ScanSubmit | URL input form with scan progress indicator |
| FindingsList | Table with severity/type/status filters, sortable |
| FindingDetail | Code snippet viewer, description, attack scenario, remediation, triage buttons |
| ScanHistory | Timeline of scans per repo with status indicators |
| RepoComparison | Delta view showing new/fixed/persisting findings |

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ORM | SQLAlchemy 1.4 (session.query style) | Project requirement |
| DB Driver | psycopg2-binary | PostgreSQL, production-ready |
| Auth | JWT (python-jose + bcrypt) | Stateless, standard |
| LLM | Claude via anthropic SDK | Required for scanning |
| Background Tasks | Threading | Simple, no Celery dependency needed |
| Frontend State | React hooks + fetch | Minimal dependencies |

## Environment Variables (.env)
```
DATABASE_URL=postgresql://user:pass@localhost:5432/zeropath
JWT_SECRET=your-secret-key
ANTHROPIC_API_KEY=your-api-key
CORS_ORIGINS=http://localhost:3000
```

## Deviations from Brief
1. **Background tasks use threading instead of a job queue** — For a demo/interview project, threading is simpler and avoids Redis dependency. The scanner runs in a background thread per scan.
2. **SSE for scan status replaced with polling** — Simpler to implement and test. Frontend polls GET /scans/:id/status every 2 seconds.
