/**
 * Timestamp and ISO8601 formatting utilities
 * Provides functions for generating and formatting timestamps in ISO8601 format
 */

/**
 * Generate current timestamp in ISO8601 format
 * @returns ISO8601 formatted timestamp string (e.g., "2024-01-15T10:30:45.123Z")
 */
export function generateTimestamp(): string {
  return new Date().toISOString();
}

/**
 * Format a Date object to ISO8601 string
 * @param date - Date object to format
 * @returns ISO8601 formatted timestamp string
 */
export function formatToISO8601(date: Date): string {
  return date.toISOString();
}

/**
 * Parse ISO8601 string to Date object
 * @param isoString - ISO8601 formatted timestamp string
 * @returns Date object
 */
export function parseISO8601(isoString: string): Date {
  return new Date(isoString);
}

/**
 * Get current timestamp in milliseconds since epoch
 * @returns Milliseconds since epoch
 */
export function getTimestampMs(): number {
  return Date.now();
}

/**
 * Format ISO8601 timestamp for display (human-readable)
 * @param isoString - ISO8601 formatted timestamp string
 * @param locale - Locale for formatting (default: 'en-US')
 * @returns Human-readable formatted timestamp
 */
export function formatTimestampForDisplay(isoString: string, locale: string = 'en-US'): string {
  const date = parseISO8601(isoString);
  return date.toLocaleString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * Calculate time difference between two ISO8601 timestamps
 * @param startTime - Start timestamp in ISO8601 format
 * @param endTime - End timestamp in ISO8601 format
 * @returns Difference in milliseconds
 */
export function getTimeDifference(startTime: string, endTime: string): number {
  const start = parseISO8601(startTime);
  const end = parseISO8601(endTime);
  return end.getTime() - start.getTime();
}

/**
 * Check if a timestamp is within a certain time window
 * @param timestamp - Timestamp to check in ISO8601 format
 * @param windowMs - Time window in milliseconds
 * @returns True if timestamp is within the window from now
 */
export function isWithinTimeWindow(timestamp: string, windowMs: number): boolean {
  const timestampMs = parseISO8601(timestamp).getTime();
  const nowMs = Date.now();
  return nowMs - timestampMs <= windowMs;
}

/**
 * Get session expiration timestamp (24 hours from now)
 * @returns ISO8601 formatted expiration timestamp
 */
export function getSessionExpirationTime(): string {
  const expirationDate = new Date();
  expirationDate.setHours(expirationDate.getHours() + 24);
  return formatToISO8601(expirationDate);
}
