import React, { useState } from 'react';
import { Finding } from '../types';
import SeverityBadge from './SeverityBadge';
import StatusBadge from './StatusBadge';
import CodeSnippet from './CodeSnippet';
import api from '../hooks/useApi';

interface Props {
  finding: Finding;
  onTriaged?: (finding: Finding) => void;
}

export default function FindingCard({ finding, onTriaged }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [triaging, setTriaging] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(finding.status);

  const handleTriage = async (status: string) => {
    setTriaging(true);
    try {
      const updated = await api.triageFinding(finding.id, status);
      setCurrentStatus(updated.status);
      if (onTriaged) {
        onTriaged({ ...finding, status: updated.status });
      }
    } catch (err) {
      console.error('Triage failed:', err);
    } finally {
      setTriaging(false);
    }
  };

  return (
    <div className="finding-card" data-testid="finding-card">
      <div className="finding-header" onClick={() => setExpanded(!expanded)}>
        <div className="finding-header-left">
          <SeverityBadge severity={finding.severity} />
          <span className="finding-type">{finding.vulnerability_type}</span>
          {finding.cwe_id && <span className="finding-cwe">{finding.cwe_id}</span>}
        </div>
        <div className="finding-header-right">
          <StatusBadge status={currentStatus} />
          <span className="finding-confidence">Confidence: {finding.confidence}</span>
          <span className="finding-expand">{expanded ? '\u25B2' : '\u25BC'}</span>
        </div>
      </div>

      {expanded && (
        <div className="finding-detail">
          <div className="finding-file">
            <strong>File:</strong> {finding.file_path}:{finding.line_number}
          </div>

          <div className="finding-section">
            <h4>Description</h4>
            <p>{finding.description}</p>
          </div>

          <div className="finding-section">
            <h4>Code</h4>
            <CodeSnippet
              code={finding.code_snippet}
              filePath={finding.file_path}
              lineNumber={finding.line_number}
            />
          </div>

          <div className="finding-section">
            <h4>Attack Scenario</h4>
            <p>{finding.attack_scenario}</p>
          </div>

          <div className="finding-section">
            <h4>Remediation</h4>
            <p>{finding.remediation}</p>
          </div>

          <div className="triage-buttons">
            <button
              className={`btn btn-triage ${currentStatus === 'open' ? 'active' : ''}`}
              onClick={() => handleTriage('open')}
              disabled={triaging || currentStatus === 'open'}
            >
              Open
            </button>
            <button
              className={`btn btn-triage ${currentStatus === 'false_positive' ? 'active' : ''}`}
              onClick={() => handleTriage('false_positive')}
              disabled={triaging || currentStatus === 'false_positive'}
            >
              False Positive
            </button>
            <button
              className={`btn btn-triage ${currentStatus === 'resolved' ? 'active' : ''}`}
              onClick={() => handleTriage('resolved')}
              disabled={triaging || currentStatus === 'resolved'}
            >
              Resolved
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
