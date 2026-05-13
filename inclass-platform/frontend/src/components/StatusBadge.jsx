import React from 'react';
import { statusLabel } from '../utils/helpers';

export default function StatusBadge({ status }) {
  const key = String(status || '').toUpperCase();
  const tone =
    key === 'ACTIVE' ? 'success' : key === 'NOT_STARTED' ? 'warning' : key === 'ENDED' ? 'danger' : 'neutral';

  return <span className={`status-badge status-${tone}`}>{statusLabel(key)}</span>;
}
