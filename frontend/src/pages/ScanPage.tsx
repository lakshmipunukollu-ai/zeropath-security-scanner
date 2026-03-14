import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../hooks/useApi';
import ScanProgress from '../components/ScanProgress';

export default function ScanPage() {
  const [repoUrl, setRepoUrl] = useState('');
  const [scanId, setScanId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const data = await api.createScan(repoUrl);
      setScanId(data.id);
    } catch (err: any) {
      setError(err.message || 'Failed to start scan');
    } finally {
      setSubmitting(false);
    }
  };

  const handleComplete = () => {
    if (scanId) {
      navigate(`/scans/${scanId}/findings`);
    }
  };

  return (
    <div className="page-container">
      <h1>Submit Repository for Scanning</h1>
      <div className="scan-submit-card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="repo-url">Git Repository URL</label>
            <input
              id="repo-url"
              type="url"
              value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repo.git"
              required
              disabled={!!scanId}
            />
          </div>
          {error && <div className="error-msg">{error}</div>}
          {!scanId && (
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Submitting...' : 'Start Scan'}
            </button>
          )}
        </form>

        {scanId && (
          <div className="scan-progress-section">
            <h3>Scan Progress</h3>
            <ScanProgress scanId={scanId} onComplete={handleComplete} />
          </div>
        )}
      </div>
    </div>
  );
}
