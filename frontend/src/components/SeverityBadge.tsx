import React from 'react';

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#2563eb',
  informational: '#6b7280',
};

interface Props {
  severity: string;
}

export default function SeverityBadge({ severity }: Props) {
  const color = SEVERITY_COLORS[severity] || '#6b7280';
  return (
    <span
      className="severity-badge"
      style={{ backgroundColor: color }}
      data-testid={`severity-${severity}`}
    >
      {severity.toUpperCase()}
    </span>
  );
}
