/**
 * Tests for Health Insights data models
 * Validates type definitions and constants
 */

import { describe, it, expect } from 'vitest';
import type {
  HealthMetric,
  ChatResponse,
  ChatMessage,
  ContextWindow,
  DashboardApiResponse,
  ChatApiResponse,
  StatusIndicator,
} from './health-insights';
import { METRIC_CATEGORIES, REFERENCE_RANGES } from './health-insights';

describe('Health Insights Types', () => {
  describe('HealthMetric', () => {
    it('should create a valid health metric object', () => {
      const metric: HealthMetric = {
        metric_name: 'Hemoglobin',
        value: 14.5,
        unit: 'g/dL',
        reference_range_min: 13.5,
        reference_range_max: 17.5,
        status_indicator: 'Normal',
        extraction_timestamp: '2024-01-15T10:30:45.123Z',
        category: 'Blood_Work',
      };

      expect(metric.metric_name).toBe('Hemoglobin');
      expect(metric.value).toBe(14.5);
      expect(metric.status_indicator).toBe('Normal');
    });

    it('should support all status indicators', () => {
      const statuses: StatusIndicator[] = ['Normal', 'Low', 'High', 'Critical'];
      statuses.forEach((status) => {
        const metric: HealthMetric = {
          metric_name: 'Test',
          value: 100,
          unit: 'unit',
          reference_range_min: 50,
          reference_range_max: 150,
          status_indicator: status,
          extraction_timestamp: '2024-01-15T10:30:45.123Z',
          category: 'Blood_Work',
        };
        expect(metric.status_indicator).toBe(status);
      });
    });
  });

  describe('ChatResponse', () => {
    it('should create a valid chat response object', () => {
      const response: ChatResponse = {
        summary: 'Your blood work shows normal levels.',
        important_findings: ['Hemoglobin is normal', 'WBC is elevated', 'Platelets are normal'],
        what_it_means: 'Your results indicate good overall health with one minor concern.',
        suggested_action: ['Monitor WBC levels', 'Follow up in 3 months'],
        timestamp: '2024-01-15T10:30:45.123Z',
        conversationId: 'conv-123',
      };

      expect(response.summary).toBeDefined();
      expect(response.important_findings).toHaveLength(3);
      expect(response.what_it_means).toBeDefined();
      expect(response.suggested_action).toHaveLength(2);
    });
  });

  describe('ChatMessage', () => {
    it('should create a user message', () => {
      const message: ChatMessage = {
        role: 'user',
        content: 'What do my results mean?',
        timestamp: '2024-01-15T10:30:45.123Z',
      };

      expect(message.role).toBe('user');
      expect(message.content).toBeDefined();
    });

    it('should create an assistant message with structured response', () => {
      const message: ChatMessage = {
        role: 'assistant',
        content: 'Your results are normal.',
        timestamp: '2024-01-15T10:30:45.123Z',
        structuredResponse: {
          summary: 'Your results are normal.',
          important_findings: ['Finding 1', 'Finding 2', 'Finding 3'],
          what_it_means: 'This means you are healthy.',
          suggested_action: ['Action 1'],
          timestamp: '2024-01-15T10:30:45.123Z',
          conversationId: 'conv-123',
        },
      };

      expect(message.role).toBe('assistant');
      expect(message.structuredResponse).toBeDefined();
    });
  });

  describe('ContextWindow', () => {
    it('should create a context window with messages', () => {
      const contextWindow: ContextWindow = {
        conversationId: 'conv-123',
        userId: 'user-456',
        messages: [
          {
            role: 'user',
            content: 'Hello',
            timestamp: '2024-01-15T10:30:45.123Z',
          },
        ],
        lastUpdated: '2024-01-15T10:30:45.123Z',
        expiresAt: '2024-01-16T10:30:45.123Z',
      };

      expect(contextWindow.conversationId).toBe('conv-123');
      expect(contextWindow.messages).toHaveLength(1);
      expect(contextWindow.messages[0].role).toBe('user');
    });
  });

  describe('API Response Types', () => {
    it('should create a dashboard API response', () => {
      const response: DashboardApiResponse = {
        metrics: [],
        document_count: 1,
        word_count: 500,
        extraction_timestamp: '2024-01-15T10:30:45.123Z',
        status: 'success',
      };

      expect(response.status).toBe('success');
      expect(response.document_count).toBe(1);
    });

    it('should create a chat API response', () => {
      const response: ChatApiResponse = {
        response: {
          summary: 'Summary',
          important_findings: ['Finding 1', 'Finding 2', 'Finding 3'],
          what_it_means: 'Meaning',
          suggested_action: ['Action 1'],
          timestamp: '2024-01-15T10:30:45.123Z',
          conversationId: 'conv-123',
        },
        context_window_size: 3,
        retry_count: 0,
        timestamp: '2024-01-15T10:30:45.123Z',
        status: 'success',
      };

      expect(response.status).toBe('success');
      expect(response.context_window_size).toBe(3);
    });
  });

  describe('Constants', () => {
    it('should define metric categories', () => {
      expect(METRIC_CATEGORIES.BLOOD_WORK).toBe('Blood_Work');
      expect(METRIC_CATEGORIES.METABOLIC_PANEL).toBe('Metabolic_Panel');
      expect(METRIC_CATEGORIES.THYROID_FUNCTION).toBe('Thyroid_Function');
    });

    it('should define reference ranges for all metrics', () => {
      expect(REFERENCE_RANGES.Hemoglobin).toBeDefined();
      expect(REFERENCE_RANGES.WBC).toBeDefined();
      expect(REFERENCE_RANGES.Platelets).toBeDefined();
      expect(REFERENCE_RANGES['Blood Glucose']).toBeDefined();
      expect(REFERENCE_RANGES.Cholesterol).toBeDefined();
      expect(REFERENCE_RANGES.TSH).toBeDefined();
    });

    it('should have correct reference range structure', () => {
      const hemo = REFERENCE_RANGES.Hemoglobin;
      expect(hemo.min).toBe(13.5);
      expect(hemo.max).toBe(17.5);
      expect(hemo.unit).toBe('g/dL');
      expect(hemo.category).toBe('Blood_Work');
    });
  });
});
