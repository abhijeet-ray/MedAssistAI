/**
 * Tests for timestamp and ISO8601 formatting utilities
 * Validates timestamp generation and formatting functions
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import * as fc from 'fast-check';
import {
  generateTimestamp,
  formatToISO8601,
  parseISO8601,
  getTimestampMs,
  formatTimestampForDisplay,
  getTimeDifference,
  isWithinTimeWindow,
  getSessionExpirationTime,
} from './timestamp';

describe('Timestamp Utilities', () => {
  describe('generateTimestamp', () => {
    it('should generate a valid ISO8601 timestamp', () => {
      const timestamp = generateTimestamp();
      expect(timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    });

    it('should generate timestamps that can be parsed', () => {
      const timestamp = generateTimestamp();
      const date = parseISO8601(timestamp);
      expect(date).toBeInstanceOf(Date);
      expect(date.getTime()).toBeGreaterThan(0);
    });

    it('should generate recent timestamps', () => {
      const timestamp = generateTimestamp();
      const date = parseISO8601(timestamp);
      const now = Date.now();
      expect(Math.abs(date.getTime() - now)).toBeLessThan(1000); // Within 1 second
    });
  });

  describe('formatToISO8601', () => {
    it('should format a Date object to ISO8601 string', () => {
      const date = new Date('2024-01-15T10:30:45.123Z');
      const formatted = formatToISO8601(date);
      expect(formatted).toBe('2024-01-15T10:30:45.123Z');
    });

    it('should produce valid ISO8601 format', () => {
      const date = new Date();
      const formatted = formatToISO8601(date);
      expect(formatted).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    });
  });

  describe('parseISO8601', () => {
    it('should parse ISO8601 string to Date', () => {
      const isoString = '2024-01-15T10:30:45.123Z';
      const date = parseISO8601(isoString);
      expect(date).toBeInstanceOf(Date);
      expect(date.getFullYear()).toBe(2024);
      expect(date.getMonth()).toBe(0); // January is 0
      expect(date.getDate()).toBe(15);
    });

    it('should handle various ISO8601 formats', () => {
      const formats = [
        '2024-01-15T10:30:45.123Z',
        '2024-01-15T10:30:45Z',
        '2024-01-15T10:30:45+00:00',
      ];

      formats.forEach((format) => {
        const date = parseISO8601(format);
        expect(date).toBeInstanceOf(Date);
        expect(date.getTime()).toBeGreaterThan(0);
      });
    });
  });

  describe('getTimestampMs', () => {
    it('should return current timestamp in milliseconds', () => {
      const ms = getTimestampMs();
      const now = Date.now();
      expect(Math.abs(ms - now)).toBeLessThan(100); // Within 100ms
    });

    it('should return a positive number', () => {
      const ms = getTimestampMs();
      expect(ms).toBeGreaterThan(0);
    });
  });

  describe('formatTimestampForDisplay', () => {
    it('should format ISO8601 timestamp for display', () => {
      const isoString = '2024-01-15T10:30:45.123Z';
      const formatted = formatTimestampForDisplay(isoString);
      expect(formatted).toContain('2024');
      expect(formatted).toContain('Jan');
      expect(formatted).toContain('15');
    });

    it('should support different locales', () => {
      const isoString = '2024-01-15T10:30:45.123Z';
      const enFormatted = formatTimestampForDisplay(isoString, 'en-US');
      const deFormatted = formatTimestampForDisplay(isoString, 'de-DE');
      expect(enFormatted).toBeDefined();
      expect(deFormatted).toBeDefined();
    });
  });

  describe('getTimeDifference', () => {
    it('should calculate time difference between two timestamps', () => {
      const start = '2024-01-15T10:00:00.000Z';
      const end = '2024-01-15T10:01:00.000Z';
      const diff = getTimeDifference(start, end);
      expect(diff).toBe(60000); // 60 seconds in milliseconds
    });

    it('should handle negative differences', () => {
      const start = '2024-01-15T10:01:00.000Z';
      const end = '2024-01-15T10:00:00.000Z';
      const diff = getTimeDifference(start, end);
      expect(diff).toBe(-60000);
    });

    it('should handle same timestamps', () => {
      const timestamp = '2024-01-15T10:00:00.000Z';
      const diff = getTimeDifference(timestamp, timestamp);
      expect(diff).toBe(0);
    });
  });

  describe('isWithinTimeWindow', () => {
    it('should return true for recent timestamps', () => {
      const recentTimestamp = generateTimestamp();
      const result = isWithinTimeWindow(recentTimestamp, 5000); // 5 second window
      expect(result).toBe(true);
    });

    it('should return false for old timestamps', () => {
      const oldDate = new Date();
      oldDate.setHours(oldDate.getHours() - 1);
      const oldTimestamp = formatToISO8601(oldDate);
      const result = isWithinTimeWindow(oldTimestamp, 5000); // 5 second window
      expect(result).toBe(false);
    });

    it('should handle edge case at window boundary', () => {
      const now = Date.now();
      const windowMs = 1000;
      const boundaryDate = new Date(now - windowMs);
      const boundaryTimestamp = formatToISO8601(boundaryDate);
      const result = isWithinTimeWindow(boundaryTimestamp, windowMs);
      expect(result).toBe(true);
    });
  });

  describe('getSessionExpirationTime', () => {
    it('should return a timestamp 24 hours in the future', () => {
      const expiration = getSessionExpirationTime();
      const expirationDate = parseISO8601(expiration);
      const now = new Date();
      const diffMs = expirationDate.getTime() - now.getTime();
      const diffHours = diffMs / (1000 * 60 * 60);
      expect(diffHours).toBeGreaterThan(23.9);
      expect(diffHours).toBeLessThan(24.1);
    });

    it('should return valid ISO8601 format', () => {
      const expiration = getSessionExpirationTime();
      expect(expiration).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    });
  });

  describe('Property-based tests', () => {
    it('should round-trip ISO8601 formatting', () => {
      fc.assert(
        fc.property(fc.date(), (date) => {
          const formatted = formatToISO8601(date);
          const parsed = parseISO8601(formatted);
          // Allow 1ms difference due to millisecond precision
          expect(Math.abs(parsed.getTime() - date.getTime())).toBeLessThan(2);
        })
      );
    });

    it('should maintain timestamp ordering', () => {
      fc.assert(
        fc.property(fc.date(), fc.date(), (date1, date2) => {
          const iso1 = formatToISO8601(date1);
          const iso2 = formatToISO8601(date2);
          const diff = getTimeDifference(iso1, iso2);
          const expected = date2.getTime() - date1.getTime();
          expect(diff).toBe(expected);
        })
      );
    });

    it('should generate valid timestamps', () => {
      fc.assert(
        fc.property(fc.integer({ min: 0, max: 100 }), (count) => {
          const timestamps = Array.from({ length: count }, () => generateTimestamp());
          timestamps.forEach((ts) => {
            expect(ts).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
            const date = parseISO8601(ts);
            expect(date).toBeInstanceOf(Date);
          });
        })
      );
    });
  });
});
