import React, { useState, useEffect } from 'react';
import { Finding } from '../types';
import FindingCard from './FindingCard';
import api from '../hooks/useApi';

interface Props {
  scanId: string;
}

export default function FindingsList({ scanId }: Props) {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState('');
  const [sortBy, setSortBy] = useState<'severity' | 'type' | 'status'>('severity');

  const severityOrder: Record<string, number> = {
    critical: 0, high: 1, medium: 2, low: 3, informational: 4,
  };

  useEffect(() => {
    loadFindings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanId, severityFilter, statusFilter, confidenceFilter]);

  const loadFindings = async () => {
    setLoading(true);
    try {
      const filters: any = {};
      if (severityFilter) filters.severity = severityFilter;
      if (statusFilter) filters.status = statusFilter;
      if (confidenceFilter) filters.confidence = confidenceFilter;
      const data = await api.getScanFindings(scanId, filters);
      setFindings(data.findings);
    } catch (err: any) {
      setError(err.message || 'Failed to load findings');
    } finally {
      setLoading(false);
    }
  };

  const handleTriaged = (updated: Finding) => {
    setFindings(prev => prev.map(f => f.id === updated.id ? updated : f));
  };

  const sortedFindings = [...findings].sort((a, b) => {
    if (sortBy === 'severity') {
      return (severityOrder[a.severity] ?? 5) - (severityOrder[b.severity] ?? 5);
    }
    if (sortBy === 'type') return a.vulnerability_type.localeCompare(b.vulnerability_type);
    if (sortBy === 'status') return a.status.localeCompare(b.status);
    return 0;
  });

  if (loading) return <div className="loading">Loading findings...</div>;
  if (error) return <div className="error-msg">{error}</div>;

  return (
    <div className="findings-list" data-testid="findings-list">
      <div className="findings-filters">
        <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} aria-label="Filter by severity">
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="informational">Informational</option>
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} aria-label="Filter by status">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="false_positive">False Positive</option>
          <option value="resolved">Resolved</option>
        </select>
        <select value={confidenceFilter} onChange={e => setConfidenceFilter(e.target.value)} aria-label="Filter by confidence">
          <option value="">All Confidence</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={sortBy} onChange={e => setSortBy(e.target.value as any)} aria-label="Sort by">
          <option value="severity">Sort by Severity</option>
          <option value="type">Sort by Type</option>
          <option value="status">Sort by Status</option>
        </select>
      </div>

      <div className="findings-count">
        {findings.length} finding{findings.length !== 1 ? 's' : ''} found
      </div>

      {sortedFindings.length === 0 ? (
        <div className="no-findings">No findings match the current filters.</div>
      ) : (
        sortedFindings.map(f => (
          <FindingCard key={f.id} finding={f} onTriaged={handleTriaged} />
        ))
      )}
    </div>
  );
}
