import React from 'react';
import type { StatCardData } from './StatCard';

interface HealthStatusSummaryProps {
  statCards: StatCardData[];
}

export const HealthStatusSummary: React.FC<HealthStatusSummaryProps> = ({ statCards }) => {
  // Calculate overall health status
  const normalCount = statCards.filter((card) => card.severity === 'normal').length;
  const warningCount = statCards.filter((card) => card.severity === 'warning').length;
  const criticalCount = statCards.filter((card) => card.severity === 'critical').length;
  const totalCount = statCards.length;

  // Determine overall status
  let overallStatus: 'healthy' | 'mild-risk' | 'attention-needed';
  let statusColor: string;
  let statusBg: string;
  let statusIcon: string;

  if (criticalCount > 0 || warningCount > 2) {
    overallStatus = 'attention-needed';
    statusColor = '#ef4444';
    statusBg = 'rgba(239, 68, 68, 0.1)';
    statusIcon = '⚠️';
  } else if (warningCount > 0) {
    overallStatus = 'mild-risk';
    statusColor = '#f59e0b';
    statusBg = 'rgba(245, 158, 11, 0.1)';
    statusIcon = '⚡';
  } else {
    overallStatus = 'healthy';
    statusColor = '#10b981';
    statusBg = 'rgba(16, 185, 129, 0.1)';
    statusIcon = '✅';
  }

  const statusLabels = {
    'healthy': 'Healthy',
    'mild-risk': 'Mild Risk',
    'attention-needed': 'Attention Needed',
  };

  return (
    <div
      style={{
        background: statusBg,
        border: `2px solid ${statusColor}`,
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '24px',
        backdropFilter: 'blur(20px)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3
            style={{
              margin: '0 0 8px 0',
              fontSize: '18px',
              fontWeight: '700',
              color: 'var(--text-primary)',
            }}
          >
            {statusIcon} Overall Health Status
          </h3>
          <p
            style={{
              margin: 0,
              fontSize: '14px',
              color: 'var(--text-secondary)',
            }}
          >
            {totalCount === 0
              ? 'No metrics available'
              : `${normalCount} normal, ${warningCount} slightly abnormal, ${criticalCount} critical`}
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: '8px',
          }}
        >
          <div
            style={{
              fontSize: '24px',
              fontWeight: '700',
              color: statusColor,
            }}
          >
            {statusLabels[overallStatus]}
          </div>
          <div
            style={{
              fontSize: '12px',
              color: 'var(--text-secondary)',
              fontWeight: '500',
            }}
          >
            {totalCount} metrics tracked
          </div>
        </div>
      </div>
    </div>
  );
};
