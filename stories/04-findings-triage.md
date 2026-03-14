# Story 4: Finding Triage

## As a security engineer, I want to triage findings as open, false_positive, or resolved.

### Acceptance Criteria
- GET /scans/:id/findings returns filterable finding list
- Filter by severity, status, confidence
- POST /findings/:id/triage updates finding status
- FindingDetail shows code snippet, description, attack scenario, remediation
- Triage buttons in UI for each finding

### Technical Notes
- Findings default to status "open"
- Support filtering via query parameters
- Return total count for pagination
