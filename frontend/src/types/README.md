# Health Insights UX Improvements - Type Definitions

This directory contains TypeScript type definitions for the Health Insights UX Improvements feature.

## Overview

The Health Insights feature enhances the MedAssist AI system by:
- Extracting and visualizing key medical metrics from uploaded health documents
- Structuring AI chat responses into digestible sections
- Managing conversation context to reduce repetitive information

## Type Definitions

### Core Models

#### `HealthMetric`
Represents a single health metric extracted from medical documents.

```typescript
interface HealthMetric {
  metric_name: string;                    // e.g., "Hemoglobin"
  value: number;                          // e.g., 14.5
  unit: string;                           // e.g., "g/dL"
  reference_range_min: number;            // e.g., 13.5
  reference_range_max: number;            // e.g., 17.5
  status_indicator: StatusIndicator;      // Normal, Low, High, or Critical
  extraction_timestamp: string;           // ISO8601 format
  category: string;                       // Blood_Work, Metabolic_Panel, Thyroid_Function
  document_id?: string;                   // Optional reference to source document
}
```

#### `ChatResponse`
Structured chat response with four distinct sections.

```typescript
interface ChatResponse {
  summary: string;                        // 1-2 sentence overview
  important_findings: string[];           // 3-7 key findings
  what_it_means: string;                  // 2-3 sentences explaining significance
  suggested_action: string[];             // 1-3 actionable recommendations
  timestamp: string;                      // ISO8601 format
  conversationId: string;                 // Reference to conversation
}
```

#### `ChatMessage`
Single message in a chat conversation.

```typescript
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;                      // ISO8601 format
  structuredResponse?: ChatResponse;      // Only for assistant messages
}
```

#### `ContextWindow`
Manages conversation history (last 3 messages).

```typescript
interface ContextWindow {
  conversationId: string;
  userId: string;
  messages: ChatMessage[];                // Last 3 messages (max)
  lastUpdated: string;                    // ISO8601 format
  expiresAt: string;                      // ISO8601 format (session end)
}
```

### API Response Models

#### `DashboardApiResponse`
Response from Dashboard Lambda function.

```typescript
interface DashboardApiResponse {
  metrics: HealthMetric[];
  document_count: number;
  word_count: number;
  extraction_timestamp: string;           // ISO8601 format
  status: 'success' | 'partial' | 'error';
  message?: string;
}
```

#### `ChatApiResponse`
Response from Chat Lambda function.

```typescript
interface ChatApiResponse {
  response: ChatResponse;
  context_window_size: number;
  retry_count: number;
  timestamp: string;                      // ISO8601 format
  status: 'success' | 'error';
  error_message?: string;
}
```

## Constants

### Metric Categories
```typescript
METRIC_CATEGORIES = {
  BLOOD_WORK: 'Blood_Work',
  METABOLIC_PANEL: 'Metabolic_Panel',
  THYROID_FUNCTION: 'Thyroid_Function',
}
```

### Reference Ranges
Standard medical reference ranges for each metric type:
- Hemoglobin: 13.5-17.5 g/dL
- WBC: 4.5-11.0 K/uL
- Platelets: 150-400 K/uL
- Blood Glucose: 70-100 mg/dL
- Cholesterol: 0-200 mg/dL
- TSH: 0.4-4.0 mIU/L

## Usage

### Importing Types

```typescript
import type {
  HealthMetric,
  ChatResponse,
  ChatMessage,
  ContextWindow,
  DashboardApiResponse,
  ChatApiResponse,
  StatusIndicator,
} from '@/types';

import {
  METRIC_CATEGORIES,
  REFERENCE_RANGES,
} from '@/types';
```

### Creating Instances

```typescript
// Create a health metric
const metric: HealthMetric = {
  metric_name: 'Hemoglobin',
  value: 14.5,
  unit: 'g/dL',
  reference_range_min: 13.5,
  reference_range_max: 17.5,
  status_indicator: 'Normal',
  extraction_timestamp: generateTimestamp(),
  category: METRIC_CATEGORIES.BLOOD_WORK,
};

// Create a chat response
const response: ChatResponse = {
  summary: 'Your blood work shows normal levels.',
  important_findings: ['Hemoglobin is normal', 'WBC is elevated'],
  what_it_means: 'Your results indicate good overall health.',
  suggested_action: ['Monitor WBC levels'],
  timestamp: generateTimestamp(),
  conversationId: 'conv-123',
};
```

## Testing

All types are tested with:
- Unit tests validating type creation and structure
- Property-based tests using fast-check
- Integration tests with API responses

Run tests:
```bash
npm run test:run -- src/types/health-insights.test.ts
```

## Related Files

- `health-insights.ts` - Type definitions
- `health-insights.test.ts` - Type tests
- `../utils/timestamp.ts` - Timestamp utilities
- `../utils/timestamp.test.ts` - Timestamp tests
