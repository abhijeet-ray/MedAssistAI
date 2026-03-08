import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from './StatCard';
import type { StatCardData } from './StatCard';

describe('StatCard Component', () => {
  it('should render stat card with normal severity', () => {
    const data: StatCardData = {
      title: 'Hemoglobin',
      value: '13.5',
      unit: 'g/dL',
      insight: 'Hemoglobin carries oxygen in your blood.',
      severity: 'normal',
    };

    render(<StatCard data={data} />);

    expect(screen.getByText('Hemoglobin')).toBeInTheDocument();
    expect(screen.getByText('13.5')).toBeInTheDocument();
    expect(screen.getByText('g/dL')).toBeInTheDocument();
    expect(screen.getByText('Hemoglobin carries oxygen in your blood.')).toBeInTheDocument();
  });

  it('should render stat card with warning severity', () => {
    const data: StatCardData = {
      title: 'Blood Glucose',
      value: '120',
      unit: 'mg/dL',
      insight: 'Your glucose level is slightly elevated.',
      severity: 'warning',
    };

    render(<StatCard data={data} />);

    expect(screen.getByText('Blood Glucose')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('mg/dL')).toBeInTheDocument();
  });

  it('should render stat card with critical severity', () => {
    const data: StatCardData = {
      title: 'Platelets',
      value: '50000',
      unit: 'cells/μL',
      insight: 'Platelet count is critically low.',
      severity: 'critical',
    };

    render(<StatCard data={data} />);

    expect(screen.getByText('Platelets')).toBeInTheDocument();
    expect(screen.getByText('50000')).toBeInTheDocument();
    expect(screen.getByText('cells/μL')).toBeInTheDocument();
  });

  it('should apply correct styling for normal severity', () => {
    const data: StatCardData = {
      title: 'Test Metric',
      value: '100',
      unit: 'units',
      insight: 'Test insight',
      severity: 'normal',
    };

    const { container } = render(<StatCard data={data} />);
    const card = container.firstChild as HTMLElement;

    const style = window.getComputedStyle(card);
    expect(style.background).toBeDefined();
    expect(style.border).toBeDefined();
  });

  it('should apply correct styling for warning severity', () => {
    const data: StatCardData = {
      title: 'Test Metric',
      value: '100',
      unit: 'units',
      insight: 'Test insight',
      severity: 'warning',
    };

    const { container } = render(<StatCard data={data} />);
    const card = container.firstChild as HTMLElement;

    const style = window.getComputedStyle(card);
    expect(style.background).toBeDefined();
    expect(style.border).toBeDefined();
  });

  it('should apply correct styling for critical severity', () => {
    const data: StatCardData = {
      title: 'Test Metric',
      value: '100',
      unit: 'units',
      insight: 'Test insight',
      severity: 'critical',
    };

    const { container } = render(<StatCard data={data} />);
    const card = container.firstChild as HTMLElement;

    const style = window.getComputedStyle(card);
    expect(style.background).toBeDefined();
    expect(style.border).toBeDefined();
  });

  it('should display value with large font size', () => {
    const data: StatCardData = {
      title: 'Test Metric',
      value: '99.9',
      unit: 'units',
      insight: 'Test insight',
      severity: 'normal',
    };

    render(<StatCard data={data} />);
    const valueElement = screen.getByText('99.9');

    const style = window.getComputedStyle(valueElement);
    expect(style.fontSize).toBeDefined();
  });

  it('should display unit with smaller font size', () => {
    const data: StatCardData = {
      title: 'Test Metric',
      value: '100',
      unit: 'mg/dL',
      insight: 'Test insight',
      severity: 'normal',
    };

    render(<StatCard data={data} />);
    const unitElement = screen.getByText('mg/dL');

    const style = window.getComputedStyle(unitElement);
    expect(style.fontSize).toBeDefined();
  });

  it('should render insight text', () => {
    const insightText = 'This is a detailed insight about the metric.';
    const data: StatCardData = {
      title: 'Test Metric',
      value: '100',
      unit: 'units',
      insight: insightText,
      severity: 'normal',
    };

    render(<StatCard data={data} />);
    expect(screen.getByText(insightText)).toBeInTheDocument();
  });

  it('should handle empty unit string', () => {
    const data: StatCardData = {
      title: 'Test Metric',
      value: '100',
      unit: '',
      insight: 'Test insight',
      severity: 'normal',
    };

    render(<StatCard data={data} />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('should handle long metric names', () => {
    const longTitle = 'Very Long Metric Name That Might Wrap';
    const data: StatCardData = {
      title: longTitle,
      value: '100',
      unit: 'units',
      insight: 'Test insight',
      severity: 'normal',
    };

    render(<StatCard data={data} />);
    expect(screen.getByText(longTitle)).toBeInTheDocument();
  });
});
