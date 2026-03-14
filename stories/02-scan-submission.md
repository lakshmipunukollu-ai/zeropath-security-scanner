# Story 2: Scan Submission

## As a user, I want to submit a Git repository URL for security scanning.

### Acceptance Criteria
- POST /scans accepts { repo_url: string }
- Creates Repository record if new URL
- Creates Scan record with status "queued"
- Kicks off background scanning pipeline
- Returns scan ID immediately

### Technical Notes
- Validate URL format before accepting
- Clone repo to temp directory
- Scanner runs in background thread
- Scan status transitions: queued → running → complete/failed
