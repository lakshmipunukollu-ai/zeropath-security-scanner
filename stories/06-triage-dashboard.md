# Story 6: Triage Dashboard UI

## As a security engineer, I want a professional dashboard to manage vulnerabilities.

### Acceptance Criteria
- ScanSubmit: URL input with progress indicator
- FindingsList: Filterable table (severity, type, status, confidence)
- FindingDetail: Code viewer, description, attack scenario, remediation, triage buttons
- ScanHistory: Timeline of scans per repository
- RepoComparison: Side-by-side delta view (new/fixed/persisting)
- Responsive layout, professional styling

### Technical Notes
- React + TypeScript
- Fetch API calls to backend
- Color-coded severity badges
- Syntax highlighting for code snippets
