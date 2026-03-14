import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Scan, RepoHistory } from '../types';
import StatusBadge from '../components/StatusBadge';
import DeltaView from '../components/DeltaView';
import api from '../hooks/useApi';

interface RepoWithScans {
  repo: { id: string; url: string; name: string };
  scans: Scan[];
}

export default function DashboardPage() {
  const [repos, setRepos] = useState<RepoWithScans[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      // We need to get repos via scan history. First try health to confirm API is up.
      await api.getHealth();
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to API');
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading dashboard...</div>;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Security Dashboard</h1>
        <Link to="/scan" className="btn btn-primary">New Scan</Link>
      </div>

      {error && <div className="error-msg">{error}</div>}

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <h2>Quick Actions</h2>
          <div className="quick-actions">
            <Link to="/scan" className="action-card">
              <h3>Submit New Scan</h3>
              <p>Analyze a Git repository for security vulnerabilities</p>
            </Link>
          </div>
        </div>

        {selectedRepoId && (
          <div className="dashboard-section">
            <h2>Delta Analysis</h2>
            <DeltaView repoId={selectedRepoId} />
          </div>
        )}
      </div>
    </div>
  );
}
