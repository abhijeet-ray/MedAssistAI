import React, { useState, useEffect } from 'react';
import type { StatCardData } from './StatCard';
import { KeyMedicalInsights } from './KeyMedicalInsights';
import { fetchDashboard, exportDashboardPDF } from '../utils/api';

interface DashboardProps {
  sessionId: string;
  role: string;
  statCards?: StatCardData[];
  documentsUploaded?: number;
  isProcessing?: boolean;
  processingMessage?: string | null;
  onExport?: () => void;
  onDashboardUpdate?: (cards: StatCardData[]) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  sessionId,
  role,
  statCards = [],
  documentsUploaded = 0,
  isProcessing = false,
  processingMessage = null,
  onExport,
  onDashboardUpdate,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [displayedCards, setDisplayedCards] = useState<StatCardData[]>(statCards);
  const [language, setLanguage] = useState<'en' | 'hi'>('en');
  
  // Show translation toggle only for Patient and ASHA Worker roles
  const showTranslationToggle = role === 'patient' || role === 'asha';

  // Update displayed cards when props change
  useEffect(() => {
    setDisplayedCards(statCards);
  }, [statCards]);

  // Fetch dashboard on mount and when sessionId/role changes
  useEffect(() => {
    const loadDashboard = async () => {
      setIsLoading(true);
      const result = await fetchDashboard(sessionId, role, language);
      setIsLoading(false);

      if (!result) {
        console.error('Failed to fetch dashboard: No response');
        return;
      }

      if (result.error) {
        console.error('Failed to fetch dashboard:', result.error.message);
        return;
      }

      if (result.data?.statCards) {
        setDisplayedCards(result.data.statCards);
        onDashboardUpdate?.(result.data.statCards);
      }
    };

    loadDashboard();
  }, [sessionId, role, language]);

  const handleExport = async () => {
    setIsExporting(true);
    setExportError(null);
    try {
      const result = await exportDashboardPDF(sessionId, role, language, displayedCards);

      if (result.error) {
        setExportError(result.error.message);
        return;
      }

      if (result.data?.pdfUrl) {
        window.open(result.data.pdfUrl, '_blank');
        onExport?.();
      }
    } catch (error) {
      setExportError(error instanceof Error ? error.message : 'Failed to export PDF');
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Health Insights Dashboard</h2>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {showTranslationToggle && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                Language:
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as 'en' | 'hi')}
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-primary)',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer',
                }}
              >
                <option value="en">English</option>
                <option value="hi">हिंदी (Hindi)</option>
              </select>
            </div>
          )}
          <button
            onClick={handleExport}
            disabled={isExporting || displayedCards.length === 0 || isLoading}
            style={{
              background: 'var(--accent-primary)',
              border: 'none',
              color: 'white',
              padding: '10px 20px',
              borderRadius: '8px',
              cursor: isExporting || displayedCards.length === 0 || isLoading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              opacity: isExporting || displayedCards.length === 0 || isLoading ? 0.5 : 1,
              transition: 'all 0.3s ease',
            }}
            onMouseEnter={(e) => {
              if (!isExporting && displayedCards.length > 0 && !isLoading) {
                e.currentTarget.style.background = 'var(--accent-hover)';
                e.currentTarget.style.boxShadow = '0 4px 20px rgba(99, 102, 241, 0.4)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--accent-primary)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            {isExporting ? '📥 Exporting...' : '📥 Export PDF'}
          </button>
        </div>
      </div>

      {exportError && (
        <div
          style={{
            marginBottom: '16px',
            padding: '12px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            color: '#fca5a5',
            fontSize: '14px',
          }}
        >
          ❌ {exportError}
        </div>
      )}

      {isProcessing && processingMessage && (
        <div
          style={{
            marginBottom: '16px',
            padding: '12px',
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '8px',
            color: '#93c5fd',
            fontSize: '14px',
          }}
        >
          ⏳ {processingMessage}
        </div>
      )}

      {isLoading ? (
        <p className="placeholder-text">Loading dashboard...</p>
      ) : documentsUploaded === 0 ? (
        <p className="placeholder-text">Upload a document to see your health insights</p>
      ) : (
        <KeyMedicalInsights statCards={displayedCards} isLoading={isLoading} />
      )}

      <div style={{ marginTop: '20px', padding: '12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', fontSize: '12px', color: '#fca5a5' }}>
        ⚠️ This AI system provides informational insights only and does not provide medical diagnosis. Always consult a licensed healthcare professional.
      </div>
    </div>
  );
};
