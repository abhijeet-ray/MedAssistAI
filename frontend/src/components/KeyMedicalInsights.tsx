import React from 'react';
import type { StatCardData } from './StatCard';
import { StatCard } from './StatCard';
import { HealthStatusSummary } from './HealthStatusSummary';

interface KeyMedicalInsightsProps {
  statCards: StatCardData[];
  isLoading?: boolean;
}

export const KeyMedicalInsights: React.FC<KeyMedicalInsightsProps> = ({
  statCards,
  isLoading = false,
}) => {
  if (isLoading) {
    return <p className="placeholder-text">Loading health insights...</p>;
  }

  if (statCards.length === 0) {
    return (
      <p className="placeholder-text">
        No health metrics extracted. Upload a document to see your health insights.
      </p>
    );
  }

  return (
    <div>
      <HealthStatusSummary statCards={statCards} />
      <div className="stat-cards">
        {statCards.map((card, index) => (
          <StatCard key={index} data={card} />
        ))}
      </div>
    </div>
  );
};
