import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { RepoHistory, Scan } from '../types';
import StatusBadge from '../components/StatusBadge';
import DeltaView from '../components/DeltaView';
import api from '../hooks/useApi';

export default function RepoHistoryPage() {
  const { repoId } = useParams<{ repoId: string }>();
  const [history, setHistory] = useState<RepoHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDelta, setShowDelta] = useState(false);

  useEffect(() => {
    if (!repoId) return;
    const load = async () => {
      try {
        const data = await api.getRepoHistory(repoId);
        setHistory(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load history');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [repoId]);

  if (!repoId) return <div className="error-msg">Repository ID required</div>;
  if (loading) return <div className="loading">Loading history...</div>;
  if (error) return <div className="error-msg">{error}</div>;
  if (!history) return null;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Repository: {history.repo.name}</h1>
        <Link to="/dashboard" className="btn btn-outline">Back to Dashboard</Link>
      </div>
      <p className="repo-url">{history.repo.url}</p>

      <div className="history-actions">
        <button
          className={`btn ${showDelta ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setShowDelta(!showDelta)}
        >
          {showDelta ? 'Hide Delta Analysis' : 'Show Delta Analysis'}
        </button>
      </div>

      {showDelta && <DeltaView repoId={repoId} />}

      <h2>Scan History</h2>
      <div className="scan-timeline" data-testid="scan-timeline">
        {history.scans.length === 0 ? (
          <p>No scans found for this repository.</p>
        ) : (
          history.scans.map((scan: Scan) => (
            <div key={scan.id} className="scan-timeline-item">
              <div className="scan-timeline-header">
                <StatusBadge status={scan.status} />
                <span className="scan-date">
                  {scan.created_at ? new Date(scan.created_at).toLocaleString() : 'N/A'}
                </span>
              </div>
              <div className="scan-timeline-detail">
                <span>{scan.files_scanned} files scanned</span>
                {scan.status === 'complete' && (
                  <Link to={`/scans/${scan.id}/findings`} className="btn btn-sm btn-outline">
                    View Findings
                  </Link>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
