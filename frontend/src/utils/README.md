# Utility Functions

This directory contains utility functions for the Health Insights UX Improvements feature.

## Timestamp Utilities

The `timestamp.ts` module provides functions for generating and formatting timestamps in ISO8601 format.

### Functions

#### `generateTimestamp(): string`
Generate current timestamp in ISO8601 format.

```typescript
const timestamp = generateTimestamp();
// Returns: "2024-01-15T10:30:45.123Z"
```

#### `formatToISO8601(date: Date): string`
Format a Date object to ISO8601 string.

```typescript
const date = new Date();
const formatted = formatToISO8601(date);
// Returns: "2024-01-15T10:30:45.123Z"
```

#### `parseISO8601(isoString: string): Date`
Parse ISO8601 string to Date object.

```typescript
const date = parseISO8601('2024-01-15T10:30:45.123Z');
// Returns: Date object
```

#### `getTimestampMs(): number`
Get current timestamp in milliseconds since epoch.

```typescript
const ms = getTimestampMs();
// Returns: 1705318245123
```

#### `formatTimestampForDisplay(isoString: string, locale?: string): string`
Format ISO8601 timestamp for human-readable display.

```typescript
const formatted = formatTimestampForDisplay('2024-01-15T10:30:45.123Z');
// Returns: "Jan 15, 2024, 10:30:45 AM"
```

#### `getTimeDifference(startTime: string, endTime: string): number`
Calculate time difference between two ISO8601 timestamps in milliseconds.

```typescript
const diff = getTimeDifference(
  '2024-01-15T10:00:00.000Z',
  '2024-01-15T10:01:00.000Z'
);
// Returns: 60000 (60 seconds)
```

#### `isWithinTimeWindow(timestamp: string, windowMs: number): boolean`
Check if a timestamp is within a certain time window from now.

```typescript
const recent = isWithinTimeWindow(generateTimestamp(), 5000);
// Returns: true (within 5 seconds)
```

#### `getSessionExpirationTime(): string`
Get session expiration timestamp (24 hours from now).

```typescript
const expiration = getSessionExpirationTime();
// Returns: "2024-01-16T10:30:45.123Z"
```

## Usage Examples

### Creating Timestamped Data

```typescript
import { generateTimestamp } from '@/utils/timestamp';
import type { HealthMetric } from '@/types';

const metric: HealthMetric = {
  metric_name: 'Hemoglobin',
  value: 14.5,
  unit: 'g/dL',
  reference_range_min: 13.5,
  reference_range_max: 17.5,
  status_indicator: 'Normal',
  extraction_timestamp: generateTimestamp(),
  category: 'Blood_Work',
};
```

### Checking Timestamp Validity

```typescript
import { isWithinTimeWindow, getSessionExpirationTime } from '@/utils/timestamp';

// Check if data is recent
if (isWithinTimeWindow(metric.extraction_timestamp, 3600000)) {
  // Data is less than 1 hour old
}

// Get session expiration
const expiresAt = getSessionExpirationTime();
```

### Formatting for Display

```typescript
import { formatTimestampForDisplay } from '@/utils/timestamp';

const displayTime = formatTimestampForDisplay(metric.extraction_timestamp);
console.log(`Extracted: ${displayTime}`);
```

## Testing

All utilities are tested with:
- Unit tests for each function
- Property-based tests using fast-check
- Edge case testing (boundary values, timezone handling)

Run tests:
```bash
npm run test:run -- src/utils/timestamp.test.ts
```

## ISO8601 Format

All timestamps use ISO8601 format with UTC timezone:
- Format: `YYYY-MM-DDTHH:mm:ss.sssZ`
- Example: `2024-01-15T10:30:45.123Z`
- Timezone: Always UTC (Z suffix)
- Precision: Milliseconds

## Related Files

- `timestamp.ts` - Timestamp utility functions
- `timestamp.test.ts` - Timestamp tests
- `../types/health-insights.ts` - Type definitions using timestamps
