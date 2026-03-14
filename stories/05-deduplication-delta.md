# Story 5: Deduplication & Delta Analysis

## As a security engineer, I want to see what changed between scans.

### Acceptance Criteria
- Semantic fingerprinting identifies same vulnerability across scans
- GET /repos/:id/delta shows new, fixed, persisting findings
- GET /repos/:id/history shows scan timeline
- Fingerprint based on file_path + vulnerability_type + normalized code

### Technical Notes
- DeduplicationEngine normalizes code before hashing
- SHA256 hash truncated to 16 chars
- Delta compares latest two scans for a repo
