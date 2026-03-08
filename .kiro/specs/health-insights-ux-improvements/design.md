# Design Document: Health Insights UX Improvements

## Overview

The Health Insights UX Improvements feature enhances the MedAssist AI system by extracting and visualizing key medical metrics from uploaded health documents and structuring AI chat responses into digestible sections. The design maintains a lightweight architecture using existing dependencies, regex-based pattern matching for metric extraction, and simple string similarity algorithms for repetition detection.

**Key Design Goals:**
- Extract health metrics (Hemoglobin, WBC, Platelets, Blood Glucose, Cholesterol, Thyroid) with reference ranges and status indicators
- Structure chat responses into four consistent sections (Summary, Important Findings, What It Means, Suggested Action)
- Implement context management (last 3 messages) to reduce repetitive information
- Maintain lightweight architecture with no new dependencies
- Ensure responsive performance (<100ms dashboard render, <3s chat response)

**Scope:**
- Backend: Two Lambda functions (Dashboard metrics extraction, Chat context management)
- Frontend: Two React components (Dashboard metrics display, Chat structured response rendering)
- Data models for health metrics, chat responses, and context windows
- API contract updates for both Dashboard and Chat endpoints

---

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐         ┌──────────────────────────┐  │
│  │ Dashboard Component  │         │  Chat Component          │  │
│  │ - Metric Cards       │         │  - Structured Sections   │  │
│  │ - Category Groups    │         │  - Validation            │  │
│  │ - Status Indicators  │         │  - Error Handling        │  │
│  └──────────────────────┘         └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │                                    │
           │ HTTP                               │ HTTP
           ▼                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (AWS Lambda)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐         ┌──────────────────────────┐  │
│  │ Dashboard Lambda     │         │  Chat/RAG Lambda         │  │
│  │ - Metric Extraction  │         │  - Context Management    │  │
│  │ - Regex Parsing      │         │  - Repetition Detection  │  │
│  │ - Status Calculation │         │  - Response Formatting   │  │
│  │ - Reference Ranges   │         │  - Nova Lite Integration │  │
│  └──────────────────────┘         └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │                                    │
           │                                    │
           ▼                                    ▼
    ┌─────────────┐                    ┌──────────────────┐
    │  Documents  │                    │  Context Window  │
    │  (S3/DB)    │                    │  (In-Memory)     │
    └─────────────┘                    └──────────────────┘
```

### Component Interaction Flow

**Dashboard Metrics Flow:**
1. User uploads medical document
2. Dashboard Lambda receives document text
3. Text Parser extracts metrics using regex patterns
4. Status indicators calculated based on reference ranges
5. Metrics grouped by category
6. API returns structured JSON response
7. Frontend Dashboard component renders metric cards with color-coded status

**Chat Response Flow:**
1. User sends chat message
2. Chat Lambda retrieves last 3 messages (context window)
3. Repetition detection checks against previous message
4. Prompt includes context window and structured response format requirement
5. Nova Lite model generates response
6. Response structure validated (all 4 sections present)
7. If invalid, retry up to 2 times
8. Frontend Chat component renders structured sections

---

## Components and Interfaces

### Backend Components

#### 1. Dashboard Lambda Function

**Responsibility:** Extract health metrics from medical documents and return structured data with status indicators.

**Key Operations:**
- `extractMetrics(documentText)` - Parse document text and extract health metrics
- `calculateStatus(value, referenceMin, referenceMax)` - Determine status indicator
- `groupByCategory(metrics)` - Organize metrics into logical groups
- `formatResponse(metrics)` - Return structured JSON response

**Input:**
```
{
  "documentText": string,
  "documentId": string,
  "userId": string
}
```

**Output:**
```
{
  "metrics": [
    {
      "metric_name": string,
      "value": number,
      "unit": string,
      "reference_range_min": number,
      "reference_range_max": number,
      "status_indicator": "Normal" | "Low" | "High" | "Critical",
      "extraction_timestamp": ISO8601,
      "category": string
    }
  ],
  "document_count": number,
  "word_count": number,
  "extraction_timestamp": ISO8601
}
```

**Regex Patterns:**
- Hemoglobin: `/hemoglobin[:\s]+(\d+\.?\d*)\s*(g\/dL|g\/100mL)/i`
- WBC: `/wbc|white\s+blood\s+cell[:\s]+(\d+\.?\d*)\s*(K\/uL|×10\^9\/L)/i`
- Platelets: `/platelet[:\s]+(\d+\.?\d*)\s*(K\/uL|×10\^9\/L)/i`
- Blood Glucose: `/glucose|blood\s+sugar[:\s]+(\d+\.?\d*)\s*(mg\/dL|mmol\/L)/i`
- Cholesterol: `/cholesterol|total\s+cholesterol[:\s]+(\d+\.?\d*)\s*(mg\/dL|mmol\/L)/i`
- Thyroid: `/tsh|t3|t4|thyroid[:\s]+(\d+\.?\d*)\s*(mIU\/L|pmol\/L|ng\/dL)/i`

**Reference Ranges (Standard Medical):**
- Hemoglobin: 13.5-17.5 g/dL (male), 12.0-15.5 g/dL (female)
- WBC: 4.5-11.0 K/uL
- Platelets: 150-400 K/uL
- Blood Glucose (fasting): 70-100 mg/dL
- Cholesterol (total): <200 mg/dL (desirable)
- TSH: 0.4-4.0 mIU/L

#### 2. Chat/RAG Lambda Function

**Responsibility:** Manage context window, detect repetition, format structured responses, and integrate with Nova Lite model.

**Key Operations:**
- `getContextWindow(userId, conversationId)` - Retrieve last 3 messages
- `detectRepetition(currentResponse, previousMessage)` - Calculate semantic similarity
- `formatPrompt(userMessage, contextWindow)` - Build prompt with context and format requirements
- `validateResponseStructure(response)` - Ensure all 4 sections present
- `parseStructuredResponse(response)` - Extract sections from model output

**Input:**
```
{
  "userId": string,
  "conversationId": string,
  "userMessage": string,
  "documentContext": string (optional)
}
```

**Output:**
```
{
  "summary": string,
  "important_findings": string[],
  "what_it_means": string,
  "suggested_action": string[],
  "timestamp": ISO8601
}
```

**Context Window Structure (In-Memory):**
```
{
  "conversationId": string,
  "messages": [
    {
      "role": "user" | "assistant",
      "content": string,
      "timestamp": ISO8601
    }
  ],
  "lastUpdated": ISO8601
}
```

**Repetition Detection Algorithm:**
- Calculate token overlap between current and previous response
- If overlap > 50%, request regeneration
- Use simple token-based similarity (not ML-based)

**Prompt Template:**
```
You are a medical insights assistant. Provide responses in exactly this format:

SUMMARY: [1-2 sentence overview]

IMPORTANT FINDINGS:
- [Finding 1]
- [Finding 2]
- [Finding 3-7 findings total]

WHAT IT MEANS: [2-3 sentences explaining clinical significance]

SUGGESTED ACTION:
- [Action 1]
- [Action 2-3 actions total]

Context from previous messages:
[Last 3 messages]

User question: [Current user message]
```

### Frontend Components

#### 1. Dashboard Component

**Responsibility:** Display extracted health metrics in a scannable, visually organized format with status indicators.

**Props:**
```typescript
interface DashboardProps {
  metrics: HealthMetric[];
  loading: boolean;
  error?: string;
  onRetry?: () => void;
}
```

**State:**
```typescript
interface DashboardState {
  groupedMetrics: Map<string, HealthMetric[]>;
  selectedMetric?: HealthMetric;
  tooltipVisible: boolean;
}
```

**Rendering Logic:**
- Group metrics by category (Blood Work, Metabolic Panel, Thyroid Function)
- Render category headers
- Render metric cards in grid layout (3-4 columns responsive)
- Color-code status: Green (Normal), Yellow (Low/High), Red (Critical)
- Show tooltip on hover with clinical significance
- Handle loading state with skeleton cards
- Handle error state with retry button

**Performance Constraints:**
- Render time < 100ms
- Memoize metric cards to prevent unnecessary re-renders
- Use CSS Grid for layout (native browser performance)

#### 2. Chat Component

**Responsibility:** Display structured chat responses with four distinct sections and validate response structure.

**Props:**
```typescript
interface ChatProps {
  messages: ChatMessage[];
  loading: boolean;
  error?: string;
  onSendMessage: (message: string) => void;
  onRetry?: () => void;
}
```

**State:**
```typescript
interface ChatState {
  inputValue: string;
  conversationHistory: ChatMessage[];
  selectedMessage?: ChatMessage;
}
```

**Rendering Logic:**
- Display conversation history in chronological order
- For each AI response, render four sections:
  - Summary (bold header, 1-2 lines)
  - Important Findings (bullet list)
  - What It Means (paragraph)
  - Suggested Action (numbered list)
- Validate response structure before rendering
- Show error message if structure invalid
- Provide "Regenerate" button on error
- Handle loading state with typing indicator

**Validation Logic:**
- Check all 4 sections present
- Check important_findings is array with 3-7 items
- Check suggested_action is array with 1-3 items
- Return error if validation fails

---

## Data Models

### Health Metric Model

```typescript
interface HealthMetric {
  metric_name: string;           // e.g., "Hemoglobin"
  value: number;                 // e.g., 14.5
  unit: string;                  // e.g., "g/dL"
  reference_range_min: number;   // e.g., 13.5
  reference_range_max: number;   // e.g., 17.5
  status_indicator: "Normal" | "Low" | "High" | "Critical";
  extraction_timestamp: string;  // ISO8601
  category: string;              // e.g., "Blood_Work"
  document_id?: string;
}
```

**Status Indicator Logic:**
```
if value < reference_range_min:
  if value < (reference_range_min * 0.7):
    status = "Critical"
  else:
    status = "Low"
else if value > reference_range_max:
  if value > (reference_range_max * 1.3):
    status = "Critical"
  else:
    status = "High"
else:
  status = "Normal"
```

### Chat Response Model

```typescript
interface ChatResponse {
  summary: string;                    // 1-2 sentences
  important_findings: string[];       // 3-7 items
  what_it_means: string;              // 2-3 sentences
  suggested_action: string[];         // 1-3 items
  timestamp: string;                  // ISO8601
  conversationId: string;
}
```

### Chat Message Model

```typescript
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;                  // ISO8601
  structuredResponse?: ChatResponse;  // Only for assistant messages
}
```

### Context Window Model

```typescript
interface ContextWindow {
  conversationId: string;
  userId: string;
  messages: ChatMessage[];            // Last 3 messages
  lastUpdated: string;                // ISO8601
  expiresAt: string;                  // ISO8601 (session end)
}
```

### Dashboard API Response Model

```typescript
interface DashboardApiResponse {
  metrics: HealthMetric[];
  document_count: number;
  word_count: number;
  extraction_timestamp: string;       // ISO8601
  status: "success" | "partial" | "error";
  message?: string;
}
```

### Chat API Response Model

```typescript
interface ChatApiResponse {
  response: ChatResponse;
  context_window_size: number;
  retry_count: number;
  timestamp: string;                  // ISO8601
  status: "success" | "error";
  error_message?: string;
}
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Metric Extraction Completeness

*For any* medical document containing health metrics (Hemoglobin, WBC, Platelets, Blood Glucose, Cholesterol, Thyroid), the Text_Parser should extract all metrics present in the document.

**Validates: Requirements 1.1**

### Property 2: Reference Range Assignment

*For any* extracted health metric, the metric object should include a reference_range_min and reference_range_max value (either from document or standard medical ranges).

**Validates: Requirements 1.2**

### Property 3: Status Indicator Accuracy

*For any* health metric with a value and reference range, the status_indicator should be correctly assigned based on deviation: Normal (within range), Low (below range), High (above range), or Critical (significantly outside range).

**Validates: Requirements 1.4**

### Property 4: Most Recent Metric Aggregation

*For any* set of documents containing the same health metric at different timestamps, the Dashboard should display only the metric with the most recent extraction_timestamp.

**Validates: Requirements 1.5**

### Property 5: Status Indicator Visual Mapping

*For any* health metric with a status_indicator, the Dashboard component should render the metric with the correct color/icon mapping: green for Normal, yellow for Low/High, red for Critical.

**Validates: Requirements 2.1**

### Property 6: Metric Category Grouping

*For any* set of health metrics from different categories (Blood_Work, Metabolic_Panel, Thyroid_Function), the Dashboard should group metrics by category and display category headers.

**Validates: Requirements 2.3**

### Property 7: Missing Metrics Not Displayed

*For any* medical document that does not contain a specific health metric, that metric should not appear in the Dashboard output (no placeholders or error states).

**Validates: Requirements 2.5**

### Property 8: Chat Response Structure Completeness

*For any* Chat_Response object, all four required fields should be present: summary, important_findings (array), what_it_means, and suggested_action (array).

**Validates: Requirements 3.1, 6.2**

### Property 9: Important Findings Array Bounds

*For any* Chat_Response, the important_findings array should contain between 3 and 7 items (inclusive).

**Validates: Requirements 3.3**

### Property 10: Suggested Action Array Bounds

*For any* Chat_Response, the suggested_action array should contain between 1 and 3 items (inclusive).

**Validates: Requirements 3.5**

### Property 11: Chat Response Validation

*For any* Chat_Response object, if any required field is missing or malformed, the response validator should reject it and return an error.

**Validates: Requirements 3.6, 3.7**

### Property 12: Context Window Size

*For any* active conversation, the Context_Window should contain at most 3 messages. When a 4th message is added, the oldest message should be removed.

**Validates: Requirements 4.1, 10.4**

### Property 13: Context Window Inclusion in Prompt

*For any* Chat API request, the prompt sent to the Nova_Lite_Model should include the Context_Window messages as part of the prompt content.

**Validates: Requirements 4.2, 6.3**

### Property 14: Repetition Detection Threshold

*For any* Chat_Response that has >50% semantic similarity (token overlap) with the previous message, the Repetition_Detection logic should flag it for regeneration.

**Validates: Requirements 4.3, 4.4**

### Property 15: Context Window Lifecycle

*For any* conversation, when a user starts a new conversation or explicitly requests a reset, the Context_Window should be cleared (empty messages array).

**Validates: Requirements 4.5**

### Property 16: Context Window In-Memory Only

*For any* Context_Window, the data should exist only in memory during active conversations and should not be persisted to disk or database.

**Validates: Requirements 4.6**

### Property 17: Dashboard API Response Structure

*For any* Dashboard API response, the response should include a metrics array, document_count, word_count, extraction_timestamp, and status field.

**Validates: Requirements 5.1, 5.6**

### Property 18: Metric Object Completeness

*For any* health metric object in the Dashboard API response, the object should include all required fields: metric_name, value, unit, reference_range_min, reference_range_max, status_indicator, and extraction_timestamp.

**Validates: Requirements 5.2**

### Property 19: Metrics Grouped by Category

*For any* Dashboard API response, metrics should be organized by category (Blood_Work, Metabolic_Panel, Thyroid_Function) in the response structure.

**Validates: Requirements 5.3**

### Property 20: Empty Metrics Array on No Extraction

*For any* medical document that contains no recognizable health metrics, the Dashboard API should return an empty metrics array (not an error).

**Validates: Requirements 5.4, 10.1**

### Property 21: Chat API Response Structure

*For any* Chat API response, the response should include a structured Chat_Response object with all four required sections.

**Validates: Requirements 6.1**

### Property 22: Chat API Retry Logic

*For any* Chat API request where the Nova_Lite_Model fails to generate a properly structured response, the API should retry up to 2 times before returning an error.

**Validates: Requirements 6.5**

### Property 23: Chat API Response Validation

*For any* Chat API response, the response structure should be validated before being returned to the frontend.

**Validates: Requirements 6.6**

### Property 24: Dashboard Component Grid Layout

*For any* set of health metrics, the Dashboard component should render them in a grid or card-based layout with clear visual hierarchy.

**Validates: Requirements 7.1**

### Property 25: Metric Card Information Completeness

*For any* metric card rendered in the Dashboard component, the card should display: metric name, value, unit, reference range, and status indicator.

**Validates: Requirements 7.2**

### Property 26: Dashboard Component Category Headers

*For any* set of metrics grouped by category, the Dashboard component should display category headers above each group.

**Validates: Requirements 7.3**

### Property 27: Dashboard Tooltip on Hover

*For any* metric card in the Dashboard component, hovering over the card should display a tooltip with additional context.

**Validates: Requirements 7.4**

### Property 28: Dashboard Loading and Error States

*For any* Dashboard component, loading and error states should be rendered gracefully with appropriate UI feedback.

**Validates: Requirements 7.5**

### Property 29: Chat Component Section Styling

*For any* Chat_Response rendered in the Chat component, each section (Summary, Important_Findings, What_It_Means, Suggested_Action) should have distinct visual styling.

**Validates: Requirements 8.1**

### Property 30: Chat Component Findings List Rendering

*For any* Chat_Response, the Important_Findings section should be rendered as a bullet list with consistent formatting.

**Validates: Requirements 8.2**

### Property 31: Chat Component Vertical Layout

*For any* Chat_Response rendered in the Chat component, sections should be displayed in a vertical layout with clear section headers.

**Validates: Requirements 8.3**

### Property 32: Chat Component Structure Validation

*For any* Chat_Response received by the Chat component, if the structure is invalid (missing sections), an error message should be displayed and a regenerate button should be available.

**Validates: Requirements 8.4, 10.3**

### Property 33: Chat Component Message History

*For any* conversation in the Chat component, previous messages should be maintained in conversation history and displayed in chronological order.

**Validates: Requirements 8.5**

### Property 34: Malformed Metric Handling

*For any* medical document containing malformed or unreadable metric values, the Text_Parser should skip those metrics and continue processing other metrics.

**Validates: Requirements 10.2**

### Property 35: Model Failure Error Handling

*For any* Chat API request where the Nova_Lite_Model fails to generate a response, the Chat_Service should return a user-friendly error message suggesting retry.

**Validates: Requirements 10.5**

### Property 36: Unsupported Document Format Handling

*For any* document uploaded in an unsupported format, the Dashboard should display a clear error message indicating the format is not supported.

**Validates: Requirements 10.6**

---

## Error Handling

### Dashboard Lambda Error Scenarios

**Scenario 1: Malformed Document Text**
- **Trigger:** Document text is null, empty, or not a string
- **Handling:** Return error response with status "error" and message "Invalid document format"
- **Frontend:** Display error message to user

**Scenario 2: No Metrics Extracted**
- **Trigger:** Document contains no recognizable health metrics
- **Handling:** Return success response with empty metrics array and status "partial"
- **Frontend:** Display "No health metrics found in this document" message

**Scenario 3: Malformed Metric Values**
- **Trigger:** Metric value cannot be parsed as a number
- **Handling:** Skip that metric and continue processing others
- **Frontend:** Display only successfully extracted metrics

**Scenario 4: Unsupported Document Format**
- **Trigger:** Document format is not text/plain or PDF
- **Handling:** Return error response with status "error" and message "Unsupported document format"
- **Frontend:** Display error message with supported formats

**Scenario 5: Lambda Timeout**
- **Trigger:** Document processing exceeds Lambda timeout (15 seconds)
- **Handling:** Return partial response with metrics extracted so far
- **Frontend:** Display partial results with warning message

### Chat Lambda Error Scenarios

**Scenario 1: Invalid User Message**
- **Trigger:** User message is null, empty, or not a string
- **Handling:** Return error response with message "Invalid message format"
- **Frontend:** Display error and prevent message submission

**Scenario 2: Model Generation Failure**
- **Trigger:** Nova Lite model fails to generate response
- **Handling:** Retry up to 2 times, then return error response
- **Frontend:** Display error message with "Retry" button

**Scenario 3: Invalid Response Structure**
- **Trigger:** Model response missing required sections or malformed
- **Handling:** Validate structure, retry if invalid (up to 2 times), return error if all retries fail
- **Frontend:** Display error message with "Regenerate" button

**Scenario 4: High Repetition Detected**
- **Trigger:** Response has >50% semantic similarity with previous message
- **Handling:** Request regeneration from model (counts as retry)
- **Frontend:** Transparent to user (automatic retry)

**Scenario 5: Context Window Overflow**
- **Trigger:** More than 3 messages in context window
- **Handling:** Remove oldest message before adding new one
- **Frontend:** Transparent to user (automatic management)

**Scenario 6: Lambda Timeout**
- **Trigger:** Chat processing exceeds Lambda timeout (30 seconds)
- **Handling:** Return error response with message "Request timeout, please try again"
- **Frontend:** Display error message with "Retry" button

### Frontend Error Handling

**Dashboard Component:**
- Display loading skeleton while fetching metrics
- Show error banner if API call fails
- Provide "Retry" button on error
- Display "No metrics found" message for empty results
- Gracefully handle missing tooltip data

**Chat Component:**
- Show typing indicator while waiting for response
- Display error message if response structure invalid
- Provide "Regenerate" button on error
- Show error banner if API call fails
- Maintain conversation history even on error

---

## Testing Strategy

### Unit Testing Approach

**Dashboard Lambda Unit Tests:**
- Test metric extraction with various document formats and metric types
- Test status indicator calculation with edge cases (boundary values)
- Test reference range assignment for each metric type
- Test metric aggregation with multiple documents
- Test error handling for malformed inputs
- Test regex patterns for each metric type

**Chat Lambda Unit Tests:**
- Test context window management (add, remove, clear operations)
- Test repetition detection with various similarity levels
- Test response structure validation
- Test prompt formatting with context inclusion
- Test retry logic for failed generations
- Test error handling for invalid inputs

**Dashboard Component Unit Tests:**
- Test metric card rendering with various metric types
- Test category grouping logic
- Test status indicator color mapping
- Test tooltip display on hover
- Test loading and error state rendering
- Test responsive grid layout

**Chat Component Unit Tests:**
- Test section rendering with valid responses
- Test structure validation with invalid responses
- Test message history management
- Test chronological ordering of messages
- Test error message display
- Test regenerate button functionality

### Property-Based Testing Approach

**Property-Based Test Configuration:**
- Minimum 100 iterations per property test
- Use fast-check (JavaScript) or Hypothesis (Python) for generators
- Tag each test with feature name and property number
- Generate realistic health metric values and ranges
- Generate various document formats and content

**Property Test Examples:**

```typescript
// Property 1: Metric Extraction Completeness
// Feature: health-insights-ux-improvements, Property 1: Metric Extraction Completeness
test.prop([fc.array(fc.record({
  name: fc.constantFrom('Hemoglobin', 'WBC', 'Platelets', 'Blood Glucose', 'Cholesterol', 'TSH'),
  value: fc.float({ min: 0, max: 500 }),
  unit: fc.string()
}))])('extracts all metrics from document', (metrics) => {
  const doc = generateDocumentWithMetrics(metrics);
  const extracted = extractMetrics(doc);
  expect(extracted.length).toBe(metrics.length);
});

// Property 3: Status Indicator Accuracy
// Feature: health-insights-ux-improvements, Property 3: Status Indicator Accuracy
test.prop([
  fc.float({ min: 0, max: 500 }),
  fc.float({ min: 0, max: 500 })
])('calculates correct status indicator', (value, refMin, refMax) => {
  fc.pre(refMin < refMax);
  const status = calculateStatus(value, refMin, refMax);
  if (value >= refMin && value <= refMax) {
    expect(status).toBe('Normal');
  } else if (value < refMin * 0.7) {
    expect(status).toBe('Critical');
  } else if (value < refMin) {
    expect(status).toBe('Low');
  } else if (value > refMax * 1.3) {
    expect(status).toBe('Critical');
  } else {
    expect(status).toBe('High');
  }
});

// Property 12: Context Window Size
// Feature: health-insights-ux-improvements, Property 12: Context Window Size
test.prop([fc.array(fc.string(), { minLength: 1, maxLength: 10 })])
('maintains context window at max 3 messages', (messages) => {
  const window = new ContextWindow();
  messages.forEach(msg => window.addMessage(msg));
  expect(window.messages.length).toBeLessThanOrEqual(3);
  if (messages.length > 3) {
    expect(window.messages[0]).toBe(messages[messages.length - 3]);
  }
});

// Property 8: Chat Response Structure Completeness
// Feature: health-insights-ux-improvements, Property 8: Chat Response Structure Completeness
test.prop([fc.record({
  summary: fc.string(),
  important_findings: fc.array(fc.string(), { minLength: 3, maxLength: 7 }),
  what_it_means: fc.string(),
  suggested_action: fc.array(fc.string(), { minLength: 1, maxLength: 3 })
})])('validates complete chat response structure', (response) => {
  const isValid = validateChatResponse(response);
  expect(isValid).toBe(true);
  expect(response).toHaveProperty('summary');
  expect(response).toHaveProperty('important_findings');
  expect(response).toHaveProperty('what_it_means');
  expect(response).toHaveProperty('suggested_action');
});
```

### Test Coverage Goals

- **Dashboard Lambda:** 85%+ code coverage
- **Chat Lambda:** 85%+ code coverage
- **Dashboard Component:** 80%+ code coverage
- **Chat Component:** 80%+ code coverage
- **All 36 properties:** Minimum 100 iterations each

### Integration Testing

- Test Dashboard API end-to-end with real documents
- Test Chat API end-to-end with context window
- Test frontend components with mock API responses
- Test error scenarios and recovery flows
- Test performance with large documents (10+ pages)

### Performance Testing

- Dashboard Lambda: Verify <500ms response time for 10-page documents
- Chat Lambda: Verify <3s response time for typical queries
- Dashboard Component: Verify <100ms render time for 50+ metrics
- Chat Component: Verify smooth scrolling with 100+ messages

