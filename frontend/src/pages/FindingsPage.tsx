import React from 'react';
import { useParams, Link } from 'react-router-dom';
import FindingsList from '../components/FindingsList';

export default function FindingsPage() {
  const { scanId } = useParams<{ scanId: string }>();

  if (!scanId) {
    return <div className="error-msg">Scan ID is required</div>;
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Scan Findings</h1>
        <Link to="/dashboard" className="btn btn-outline">Back to Dashboard</Link>
      </div>
      <FindingsList scanId={scanId} />
    </div>
  );
}
