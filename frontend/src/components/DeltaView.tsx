import React, { useState, useEffect } from 'react';
import { DeltaResponse } from '../types';
import FindingCard from './FindingCard';
import api from '../hooks/useApi';

interface Props {
  repoId: string;
}

export default function DeltaView({ repoId }: Props) {
  const [delta, setDelta] = useState<DeltaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'new' | 'fixed' | 'persisting'>('new');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getRepoDelta(repoId);
        setDelta(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load delta');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [repoId]);

  if (loading) return <div className="loading">Loading delta analysis...</div>;
  if (error) return <div className="error-msg">{error}</div>;
  if (!delta) return null;

  const tabs = [
    { key: 'new' as const, label: 'New', count: delta.new.length, color: '#dc2626' },
    { key: 'fixed' as const, label: 'Fixed', count: delta.fixed.length, color: '#16a34a' },
    { key: 'persisting' as const, label: 'Persisting', count: delta.persisting.length, color: '#ca8a04' },
  ];

  const currentFindings = delta[activeTab];

  return (
    <div className="delta-view" data-testid="delta-view">
      <div className="delta-tabs">
        {tabs.map(tab => (
          <button
            key={tab.key}
            className={`delta-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
            style={activeTab === tab.key ? { borderBottomColor: tab.color } : {}}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      <div className="delta-content">
        {currentFindings.length === 0 ? (
          <div className="no-findings">No {activeTab} findings.</div>
        ) : (
          currentFindings.map(f => <FindingCard key={f.id} finding={f} />)
        )}
      </div>
    </div>
  );
}
