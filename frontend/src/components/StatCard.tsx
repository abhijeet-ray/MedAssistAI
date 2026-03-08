import React from 'react';

export interface StatCardData {
  title: string;
  value: string;
  unit: string;
  insight: string;
  severity: 'normal' | 'warning' | 'critical';
  referenceRange?: string; // e.g., "70-99"
}

interface StatCardProps {
  data: StatCardData;
}

export const StatCard: React.FC<StatCardProps> = ({ data }) => {
  const severityColors = {
    normal: {
      bg: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.3)',
      text: '#86efac',
      statusBg: 'rgba(16, 185, 129, 0.2)',
      statusText: '#10b981',
    },
    warning: {
      bg: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.3)',
      text: '#fcd34d',
      statusBg: 'rgba(245, 158, 11, 0.2)',
      statusText: '#f59e0b',
    },
    critical: {
      bg: 'rgba(239, 68, 68, 0.1)',
      border: 'rgba(239, 68, 68, 0.3)',
      text: '#fca5a5',
      statusBg: 'rgba(239, 68, 68, 0.2)',
      statusText: '#ef4444',
    },
  };

  const colors = severityColors[data.severity];
  const statusLabel =
    data.severity === 'normal' ? 'Normal' : data.severity === 'warning' ? 'Slightly High/Low' : 'Critical';

  return (
    <div
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: '12px',
        padding: '20px',
        backdropFilter: 'blur(20px)',
        transition: 'all 0.3s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = `0 8px 24px ${colors.border}`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {/* Metric Title */}
      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: '600' }}>
          {data.title}
        </p>
      </div>

      {/* Value and Unit */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontSize: '28px', fontWeight: '700', color: colors.text }}>
          {data.value}
        </span>
        <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{data.unit}</span>
      </div>

      {/* Reference Range */}
      {data.referenceRange && (
        <div style={{ marginBottom: '12px', fontSize: '13px', color: 'var(--text-secondary)' }}>
          <span style={{ fontWeight: '500' }}>Range:</span> {data.referenceRange}
        </div>
      )}

      {/* Status Indicator */}
      <div
        style={{
          display: 'inline-block',
          padding: '6px 12px',
          borderRadius: '6px',
          background: colors.statusBg,
          color: colors.statusText,
          fontSize: '12px',
          fontWeight: '600',
          marginBottom: '12px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        ● {statusLabel}
      </div>

      {/* Insight */}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', margin: 0 }}>
        {data.insight}
      </p>
    </div>
  );
};
