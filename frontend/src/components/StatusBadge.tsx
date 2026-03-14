import React from 'react';

const STATUS_COLORS: Record<string, string> = {
  open: '#dc2626',
  false_positive: '#6b7280',
  resolved: '#16a34a',
  queued: '#ca8a04',
  running: '#2563eb',
  complete: '#16a34a',
  failed: '#dc2626',
};

interface Props {
  status: string;
}

export default function StatusBadge({ status }: Props) {
  const color = STATUS_COLORS[status] || '#6b7280';
  const label = status.replace('_', ' ').toUpperCase();
  return (
    <span
      className="status-badge"
      style={{ backgroundColor: color }}
      data-testid={`status-${status}`}
    >
      {label}
    </span>
  );
}
