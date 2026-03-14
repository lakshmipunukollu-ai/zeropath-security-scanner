import React, { useState, useEffect } from 'react';
import { ScanStatus } from '../types';
import StatusBadge from './StatusBadge';
import api from '../hooks/useApi';

interface Props {
  scanId: string;
  onComplete?: () => void;
}

export default function ScanProgress({ scanId, onComplete }: Props) {
  const [status, setStatus] = useState<ScanStatus | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const poll = async () => {
      try {
        const data = await api.getScanStatus(scanId);
        setStatus(data);
        if (data.status === 'complete' || data.status === 'failed') {
          clearInterval(interval);
          if (data.status === 'complete' && onComplete) {
            onComplete();
          }
        }
      } catch (err: any) {
        setError(err.message || 'Failed to get scan status');
        clearInterval(interval);
      }
    };

    poll();
    interval = setInterval(poll, 2000);

    return () => clearInterval(interval);
  }, [scanId, onComplete]);

  if (error) return <div className="error-msg">{error}</div>;
  if (!status) return <div className="loading">Loading scan status...</div>;

  return (
    <div className="scan-progress" data-testid="scan-progress">
      <div className="scan-progress-header">
        <StatusBadge status={status.status} />
        <span className="scan-files">{status.files_scanned} files scanned</span>
      </div>
      {status.status === 'running' && (
        <div className="progress-bar-container">
          <div className="progress-bar progress-bar-animated" />
        </div>
      )}
      {status.started_at && (
        <div className="scan-time">Started: {new Date(status.started_at).toLocaleString()}</div>
      )}
      {status.completed_at && (
        <div className="scan-time">Completed: {new Date(status.completed_at).toLocaleString()}</div>
      )}
    </div>
  );
}
