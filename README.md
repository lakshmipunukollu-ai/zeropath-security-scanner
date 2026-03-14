# ZeroPath Security Scanner

LLM-powered security vulnerability scanner for Python codebases. Submit a Git repository URL, and ZeroPath will clone, analyze, and present structured vulnerability findings in a professional triage dashboard.

## Features

- **Automated Security Scanning** - Clone and analyze Python repos using Claude for vulnerability detection
- **Vulnerability Triage Dashboard** - Filter, sort, and triage findings by severity, confidence, and status
- **Delta Analysis** - Compare scans to see new, fixed, and persisting vulnerabilities
- **Deduplication** - Semantic fingerprinting prevents duplicate findings across scans
- **Scan History** - Timeline view of all scans per repository

## Architecture

- **Frontend**: React + TypeScript (port 5006)
- **Backend**: FastAPI + SQLAlchemy 1.4 (port 3006)
- **Database**: PostgreSQL (zeropath_scanner)
- **Scanner Engine**: Claude-powered analysis with background threading

## Quick Start

```bash
# Install dependencies
make install

# Seed database with demo data
make seed

# Start development servers
make dev

# Run tests
make test
```

## Configuration

Copy `.env.example` to `.env` and configure:

```
DATABASE_URL=postgresql://user:pass@localhost:5432/zeropath_scanner
JWT_SECRET=your-secret-key
ANTHROPIC_API_KEY=your-api-key
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login and get JWT token |
| POST | /scans | Submit repository for scanning |
| GET | /scans/:id/status | Poll scan progress |
| GET | /scans/:id/findings | Get scan findings with filters |
| POST | /findings/:id/triage | Update finding status |
| GET | /repos/:id/history | Scan timeline for a repo |
| GET | /repos/:id/delta | Delta analysis between scans |
| GET | /health | Health check |

## Testing

```bash
make test
```

44 tests covering all API endpoints, scanner engine, and deduplication logic. All pass with 0 failures.

## Demo Credentials

After running `make seed`:
- Email: demo@zeropath.com
- Password: password123
