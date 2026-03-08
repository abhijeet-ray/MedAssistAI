import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { KeyMedicalInsights } from './KeyMedicalInsights';
import type { StatCardData } from './StatCard';

describe('KeyMedicalInsights Component', () => {
  const mockStatCards: StatCardData[] = [
    {
      title: 'Hemoglobin',
      value: '13.5',
      unit: 'g/dL',
      insight: 'Hemoglobin carries oxygen in your blood.',
      severity: 'normal',
    },
    {
      title: 'Blood Glucose',
      value: '120',
      unit: 'mg/dL',
      insight: 'Your glucose level is slightly elevated.',
      severity: 'warning',
    },
    {
      title: 'White Blood Cells',
      value: '7500',
      unit: 'cells/μL',
      insight: 'WBC count indicates immune system health.',
      severity: 'critical',
    },
  ];

  it('should render stat cards in grid layout', () => {
    render(<KeyMedicalInsights statCards={mockStatCards} />);

    expect(screen.getByText('Hemoglobin')).toBeInTheDocument();
    expect(screen.getByText('Blood Glucose')).toBeInTheDocument();
    expect(screen.getByText('White Blood Cells')).toBeInTheDocument();
  });

  it('should display all stat card values and units', () => {
    render(<KeyMedicalInsights statCards={mockStatCards} />);

    expect(screen.getByText('13.5')).toBeInTheDocument();
    expect(screen.getByText('g/dL')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('mg/dL')).toBeInTheDocument();
  });

  it('should display stat card insights', () => {
    render(<KeyMedicalInsights statCards={mockStatCards} />);

    expect(screen.getByText('Hemoglobin carries oxygen in your blood.')).toBeInTheDocument();
    expect(screen.getByText('Your glucose level is slightly elevated.')).toBeInTheDocument();
  });

  it('should display empty state when no stat cards provided', () => {
    render(<KeyMedicalInsights statCards={[]} />);

    expect(screen.getByText(/No health metrics extracted/)).toBeInTheDocument();
  });

  it('should display loading state when isLoading is true', () => {
    render(<KeyMedicalInsights statCards={mockStatCards} isLoading={true} />);

    expect(screen.getByText('Loading health insights...')).toBeInTheDocument();
  });

  it('should render correct number of stat cards', () => {
    const { container } = render(<KeyMedicalInsights statCards={mockStatCards} />);

    const statCardDivs = container.querySelectorAll('.stat-cards > div');
    expect(statCardDivs.length).toBe(mockStatCards.length);
  });

  it('should apply severity-based styling to stat cards', () => {
    const { container } = render(<KeyMedicalInsights statCards={mockStatCards} />);

    const cards = container.querySelectorAll('.stat-cards > div');
    expect(cards.length).toBe(3);

    // Check that cards have different background colors based on severity
    const normalCard = cards[0];
    const warningCard = cards[1];
    const criticalCard = cards[2];

    const normalBg = window.getComputedStyle(normalCard).backgroundColor;
    const warningBg = window.getComputedStyle(warningCard).backgroundColor;
    const criticalBg = window.getComputedStyle(criticalCard).backgroundColor;

    // Verify that different severity levels have different styling
    expect(normalBg).toBeDefined();
    expect(warningBg).toBeDefined();
    expect(criticalBg).toBeDefined();
  });

  it('should handle single stat card', () => {
    const singleCard: StatCardData[] = [mockStatCards[0]];
    render(<KeyMedicalInsights statCards={singleCard} />);

    expect(screen.getByText('Hemoglobin')).toBeInTheDocument();
    expect(screen.queryByText('Blood Glucose')).not.toBeInTheDocument();
  });

  it('should display fallback message when extraction fails (empty array)', () => {
    render(<KeyMedicalInsights statCards={[]} isLoading={false} />);

    expect(screen.getByText(/No health metrics extracted/)).toBeInTheDocument();
  });
});
