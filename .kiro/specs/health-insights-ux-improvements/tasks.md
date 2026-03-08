# Implementation Plan: Health Insights UX Improvements

## Overview

This implementation plan breaks down the Health Insights UX Improvements feature into discrete, incremental coding tasks. The feature enhances the MedAssist AI system by extracting and visualizing health metrics from medical documents and structuring AI chat responses into four digestible sections. Implementation follows a backend-first approach (Lambda functions), then frontend components, followed by comprehensive testing with property-based tests for all 36 correctness properties.

## Tasks

- [x] 1. Set up project structure and core data models
  - Create TypeScript interfaces for HealthMetric, ChatResponse, ChatMessage, ContextWindow, and API response models
  - Set up test infrastructure with Jest and fast-check for property-based testing
  - Create utility functions for timestamp generation and ISO8601 formatting
  - _Requirements: 1.1, 3.1, 5.1, 6.1_

- [ ] 2. Implement Dashboard Lambda - Metric Extraction
  - [ ] 2.1 Implement Text Parser with regex patterns for all six metric types
    - Create regex patterns for Hemoglobin, WBC, Platelets, Blood Glucose, Cholesterol, and Thyroid
    - Implement extractMetrics() function to parse document text and return array of extracted metrics
    - Handle case-insensitive matching and multiple unit formats
    - _Requirements: 1.1, 1.6_
  
  - [ ]* 2.2 Write property test for metric extraction completeness
    - **Property 1: Metric Extraction Completeness**
    - **Validates: Requirements 1.1**
  
  - [ ] 2.3 Implement reference range assignment logic
    - Create reference range lookup table for each metric type (standard medical ranges)
    - Implement assignReferenceRanges() function to attach ranges to extracted metrics
    - Support both document-provided and standard ranges
    - _Requirements: 1.2_
  
  - [ ]* 2.4 Write property test for reference range assignment
    - **Property 2: Reference Range Assignment**
    - **Validates: Requirements 1.2_

- [ ] 3. Implement Dashboard Lambda - Status Calculation
  - [ ] 3.1 Implement status indicator calculation logic
    - Create calculateStatus() function with deviation-based logic (Normal, Low, High, Critical)
    - Implement critical threshold detection (30% deviation from range boundaries)
    - Attach status_indicator to each metric object
    - _Requirements: 1.4_
  
  - [ ]* 3.2 Write property test for status indicator accuracy
    - **Property 3: Status Indicator Accuracy**
    - **Validates: Requirements 1.4**
  
  - [ ] 3.3 Implement metric aggregation for multiple documents
    - Create aggregateMetrics() function to select most recent metric by extraction_timestamp
    - Handle duplicate metrics across multiple documents
    - _Requirements: 1.5_
  
  - [ ]* 3.4 Write property test for most recent metric aggregation
    - **Property 4: Most Recent Metric Aggregation**
    - **Validates: Requirements 1.5**

- [ ] 4. Implement Dashboard Lambda - Response Formatting
  - [ ] 4.1 Implement metric grouping by category
    - Create groupByCategory() function to organize metrics into Blood_Work, Metabolic_Panel, Thyroid_Function
    - Implement formatResponse() to structure API response with metrics array, document_count, word_count, extraction_timestamp
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ] 4.2 Implement error handling for Dashboard Lambda
    - Handle malformed document text (null, empty, non-string)
    - Handle no metrics extracted scenario (return empty array, not error)
    - Handle malformed metric values (skip and continue)
    - Handle unsupported document formats
    - _Requirements: 10.1, 10.2, 10.6_
  
  - [ ]* 4.3 Write property test for empty metrics array on no extraction
    - **Property 20: Empty Metrics Array on No Extraction**
    - **Validates: Requirements 5.4, 10.1**

- [ ] 5. Implement Chat Lambda - Context Window Management
  - [ ] 5.1 Implement ContextWindow class with in-memory storage
    - Create ContextWindow class with messages array (max 3 items)
    - Implement addMessage() to append and auto-remove oldest if exceeding 3
    - Implement getMessages() to retrieve current context
    - Implement clear() to reset context window
    - _Requirements: 4.1, 4.5, 4.6_
  
  - [ ]* 5.2 Write property test for context window size
    - **Property 12: Context Window Size**
    - **Validates: Requirements 4.1, 10.4**
  
  - [ ]* 5.3 Write property test for context window lifecycle
    - **Property 15: Context Window Lifecycle**
    - **Validates: Requirements 4.5**
  
  - [ ]* 5.4 Write property test for context window in-memory only
    - **Property 16: Context Window In-Memory Only**
    - **Validates: Requirements 4.6**

- [ ] 6. Implement Chat Lambda - Repetition Detection
  - [ ] 6.1 Implement repetition detection algorithm
    - Create detectRepetition() function using token-based similarity (>50% overlap threshold)
    - Tokenize strings by splitting on whitespace and punctuation
    - Calculate overlap percentage between current and previous response
    - _Requirements: 4.3, 4.4_
  
  - [ ]* 6.2 Write property test for repetition detection threshold
    - **Property 14: Repetition Detection Threshold**
    - **Validates: Requirements 4.3, 4.4**

- [ ] 7. Implement Chat Lambda - Response Validation and Formatting
  - [ ] 7.1 Implement Chat response structure validation
    - Create validateChatResponse() function to check all 4 sections present
    - Validate important_findings is array with 3-7 items
    - Validate suggested_action is array with 1-3 items
    - Return validation error if any check fails
    - _Requirements: 3.6, 3.7, 6.6_
  
  - [ ]* 7.2 Write property test for chat response structure completeness
    - **Property 8: Chat Response Structure Completeness**
    - **Validates: Requirements 3.1, 6.2**
  
  - [ ]* 7.3 Write property test for important findings array bounds
    - **Property 9: Important Findings Array Bounds**
    - **Validates: Requirements 3.3**
  
  - [ ]* 7.4 Write property test for suggested action array bounds
    - **Property 10: Suggested Action Array Bounds**
    - **Validates: Requirements 3.5**
  
  - [ ]* 7.5 Write property test for chat response validation
    - **Property 11: Chat Response Validation**
    - **Validates: Requirements 3.6, 3.7**

- [ ] 8. Implement Chat Lambda - Prompt Formatting and Nova Lite Integration
  - [ ] 8.1 Implement prompt template formatting
    - Create formatPrompt() function to build prompt with context window and format requirements
    - Include last 3 messages in prompt as context
    - Include structured response format instructions (4 sections)
    - _Requirements: 4.2, 6.3_
  
  - [ ]* 8.2 Write property test for context window inclusion in prompt
    - **Property 13: Context Window Inclusion in Prompt**
    - **Validates: Requirements 4.2, 6.3**
  
  - [ ] 8.3 Implement Chat Lambda main handler with retry logic
    - Create main handler to receive user message and conversation context
    - Call formatPrompt() to build prompt with context window
    - Call Nova Lite model with formatted prompt
    - Validate response structure, retry up to 2 times if invalid
    - Check for repetition, request regeneration if detected
    - Return structured ChatResponse or error
    - _Requirements: 3.1, 4.3, 6.5, 6.6_
  
  - [ ]* 8.4 Write property test for chat API retry logic
    - **Property 22: Chat API Retry Logic**
    - **Validates: Requirements 6.5**

- [ ] 9. Implement Chat Lambda - Error Handling
  - [ ] 9.1 Implement error handling for Chat Lambda
    - Handle invalid user message (null, empty, non-string)
    - Handle model generation failure with user-friendly error message
    - Handle invalid response structure with retry and error fallback
    - Handle context window overflow (auto-remove oldest)
    - Handle Lambda timeout with error response
    - _Requirements: 10.3, 10.5_
  
  - [ ]* 9.2 Write property test for model failure error handling
    - **Property 35: Model Failure Error Handling**
    - **Validates: Requirements 10.5**

- [ ] 10. Checkpoint - Backend Lambda Functions Complete
  - Ensure all Dashboard Lambda tests pass (metric extraction, status calculation, aggregation)
  - Ensure all Chat Lambda tests pass (context management, repetition detection, response validation)
  - Verify error handling for all edge cases
  - Ask the user if questions arise.

- [ ] 11. Implement Dashboard Component - Metric Card Rendering
  - [ ] 11.1 Create HealthMetric data model and types
    - Define TypeScript interface for HealthMetric with all required fields
    - Create utility functions for metric formatting (value + unit display)
    - _Requirements: 5.2, 7.2_
  
  - [ ] 11.2 Implement MetricCard component
    - Create React component to render single metric card
    - Display metric name, value, unit, reference range, status indicator
    - Implement color mapping: green (Normal), yellow (Low/High), red (Critical)
    - Add hover tooltip with clinical significance
    - _Requirements: 2.1, 7.2, 7.4_
  
  - [ ]* 11.3 Write unit tests for MetricCard component
    - Test rendering with various metric types
    - Test status indicator color mapping
    - Test tooltip display on hover
    - Test reference range display
    - _Requirements: 2.1, 7.2_

- [ ] 12. Implement Dashboard Component - Category Grouping and Layout
  - [ ] 12.1 Implement metric grouping logic
    - Create groupMetricsByCategory() function to organize metrics
    - Define category order (Blood_Work, Metabolic_Panel, Thyroid_Function)
    - _Requirements: 2.3, 7.3_
  
  - [ ] 12.2 Implement Dashboard component main layout
    - Create React component with grid/card-based layout
    - Render category headers for each group
    - Render MetricCard components in responsive grid (3-4 columns)
    - Implement memoization to prevent unnecessary re-renders
    - _Requirements: 2.2, 2.3, 2.4, 7.1, 7.3_
  
  - [ ]* 12.3 Write property test for metric category grouping
    - **Property 6: Metric Category Grouping**
    - **Validates: Requirements 2.3**
  
  - [ ]* 12.4 Write property test for missing metrics not displayed
    - **Property 7: Missing Metrics Not Displayed**
    - **Validates: Requirements 2.5**

- [ ] 13. Implement Dashboard Component - Loading and Error States
  - [ ] 13.1 Implement loading state with skeleton cards
    - Create skeleton card component for loading state
    - Display 6 skeleton cards while metrics are loading
    - _Requirements: 7.5_
  
  - [ ] 13.2 Implement error state with retry button
    - Display error banner with error message
    - Provide "Retry" button to re-fetch metrics
    - Handle "No metrics found" message for empty results
    - _Requirements: 7.5, 10.1_
  
  - [ ]* 13.3 Write unit tests for Dashboard loading and error states
    - Test skeleton card rendering during loading
    - Test error message display on API failure
    - Test retry button functionality
    - _Requirements: 7.5_

- [ ] 14. Implement Dashboard Component - Performance and Accessibility
  - [ ] 14.1 Implement performance optimizations
    - Use React.memo for MetricCard to prevent re-renders
    - Use CSS Grid for layout (native browser performance)
    - Verify render time < 100ms for 50+ metrics
    - _Requirements: 2.4_
  
  - [ ]* 14.2 Write property test for dashboard component grid layout
    - **Property 24: Dashboard Component Grid Layout**
    - **Validates: Requirements 7.1**
  
  - [ ]* 14.3 Write property test for metric card information completeness
    - **Property 25: Metric Card Information Completeness**
    - **Validates: Requirements 7.2**
  
  - [ ]* 14.4 Write property test for dashboard component category headers
    - **Property 26: Dashboard Component Category Headers**
    - **Validates: Requirements 7.3**
  
  - [ ]* 14.5 Write property test for dashboard tooltip on hover
    - **Property 27: Dashboard Tooltip on Hover**
    - **Validates: Requirements 7.4**
  
  - [ ]* 14.6 Write property test for dashboard loading and error states
    - **Property 28: Dashboard Loading and Error States**
    - **Validates: Requirements 7.5**

- [ ] 15. Checkpoint - Dashboard Component Complete
  - Ensure all Dashboard component tests pass
  - Verify render performance < 100ms
  - Verify responsive layout on mobile/tablet/desktop
  - Ask the user if questions arise.

- [ ] 16. Implement Chat Component - Response Section Rendering
  - [ ] 16.1 Create ChatResponse data model and types
    - Define TypeScript interface for ChatResponse with 4 sections
    - Create utility functions for section formatting
    - _Requirements: 3.1, 6.1_
  
  - [ ] 16.2 Implement response section components
    - Create SummarySection component (bold header, 1-2 lines)
    - Create ImportantFindingsSection component (bullet list)
    - Create WhatItMeansSection component (paragraph)
    - Create SuggestedActionSection component (numbered list)
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ]* 16.3 Write unit tests for response section components
    - Test rendering of each section with valid data
    - Test bullet list formatting for findings
    - Test numbered list formatting for actions
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 17. Implement Chat Component - Structure Validation and Error Handling
  - [ ] 17.1 Implement response structure validation in component
    - Create validateResponseStructure() function to check all 4 sections
    - Check important_findings array bounds (3-7 items)
    - Check suggested_action array bounds (1-3 items)
    - _Requirements: 8.4, 10.3_
  
  - [ ] 17.2 Implement error display and regenerate button
    - Display error message if structure invalid
    - Provide "Regenerate" button to request new response
    - Show error banner with user-friendly message
    - _Requirements: 8.4, 10.3_
  
  - [ ]* 17.3 Write property test for chat component structure validation
    - **Property 32: Chat Component Structure Validation**
    - **Validates: Requirements 8.4, 10.3**

- [ ] 18. Implement Chat Component - Message History and Layout
  - [ ] 18.1 Implement message history management
    - Create ChatMessage data model with role, content, timestamp
    - Implement message history state management
    - Display messages in chronological order
    - _Requirements: 8.5_
  
  - [ ] 18.2 Implement Chat component main layout
    - Create React component with message list and input area
    - Render user messages and AI responses in conversation view
    - Render AI responses with structured sections
    - Implement auto-scroll to latest message
    - _Requirements: 8.3, 8.5_
  
  - [ ]* 18.3 Write property test for chat component message history
    - **Property 33: Chat Component Message History**
    - **Validates: Requirements 8.5**

- [ ] 19. Implement Chat Component - Input Handling and Loading States
  - [ ] 19.1 Implement message input and submission
    - Create input field for user messages
    - Implement message submission handler
    - Validate message before submission (not empty)
    - Clear input after submission
    - _Requirements: 3.1_
  
  - [ ] 19.2 Implement loading state with typing indicator
    - Display typing indicator while waiting for response
    - Disable input during loading
    - Show loading state in message list
    - _Requirements: 8.5_
  
  - [ ]* 19.3 Write unit tests for Chat component input and loading
    - Test message input and submission
    - Test typing indicator display
    - Test input disabled during loading
    - _Requirements: 3.1_

- [ ] 20. Implement Chat Component - Section Styling and Visual Hierarchy
  - [ ] 20.1 Implement distinct visual styling for each section
    - Style Summary section with bold header and larger font
    - Style Important Findings with bullet points and consistent spacing
    - Style What It Means with paragraph formatting
    - Style Suggested Action with numbered list and action-oriented styling
    - _Requirements: 8.1, 8.3_
  
  - [ ]* 20.2 Write property test for chat component section styling
    - **Property 29: Chat Component Section Styling**
    - **Validates: Requirements 8.1**
  
  - [ ]* 20.3 Write property test for chat component findings list rendering
    - **Property 30: Chat Component Findings List Rendering**
    - **Validates: Requirements 8.2**
  
  - [ ]* 20.4 Write property test for chat component vertical layout
    - **Property 31: Chat Component Vertical Layout**
    - **Validates: Requirements 8.3**

- [ ] 21. Checkpoint - Chat Component Complete
  - Ensure all Chat component tests pass
  - Verify response structure validation works correctly
  - Verify message history displays in correct order
  - Ask the user if questions arise.

- [ ] 22. Implement API Integration Tests
  - [ ] 22.1 Write integration tests for Dashboard API
    - Test end-to-end flow: document upload → metric extraction → API response
    - Test with various document formats and metric types
    - Test error scenarios (malformed input, no metrics)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ] 22.2 Write integration tests for Chat API
    - Test end-to-end flow: user message → context window → Nova Lite → response
    - Test context window management across multiple messages
    - Test repetition detection and regeneration
    - Test error scenarios (invalid response, model failure)
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6_

- [ ] 23. Implement Property-Based Tests for Remaining Properties
  - [ ]* 23.1 Write property test for dashboard API response structure
    - **Property 17: Dashboard API Response Structure**
    - **Validates: Requirements 5.1, 5.6**
  
  - [ ]* 23.2 Write property test for metric object completeness
    - **Property 18: Metric Object Completeness**
    - **Validates: Requirements 5.2**
  
  - [ ]* 23.3 Write property test for metrics grouped by category
    - **Property 19: Metrics Grouped by Category**
    - **Validates: Requirements 5.3**
  
  - [ ]* 23.4 Write property test for status indicator visual mapping
    - **Property 5: Status Indicator Visual Mapping**
    - **Validates: Requirements 2.1**
  
  - [ ]* 23.5 Write property test for chat API response structure
    - **Property 21: Chat API Response Structure**
    - **Validates: Requirements 6.1**
  
  - [ ]* 23.6 Write property test for chat API response validation
    - **Property 23: Chat API Response Validation**
    - **Validates: Requirements 6.6**
  
  - [ ]* 23.7 Write property test for unsupported document format handling
    - **Property 36: Unsupported Document Format Handling**
    - **Validates: Requirements 10.6**
  
  - [ ]* 23.8 Write property test for malformed metric handling
    - **Property 34: Malformed Metric Handling**
    - **Validates: Requirements 10.2**

- [ ] 24. Final Checkpoint - All Tests Pass
  - Run full test suite (unit tests, integration tests, property-based tests)
  - Verify all 36 properties pass with minimum 100 iterations each
  - Verify code coverage: Dashboard Lambda 85%+, Chat Lambda 85%+, Dashboard Component 80%+, Chat Component 80%+
  - Verify performance: Dashboard Lambda <500ms, Chat Lambda <3s, Dashboard Component render <100ms
  - Ask the user if questions arise.

- [ ] 25. Documentation and Deployment Preparation
  - [ ] 25.1 Create API documentation
    - Document Dashboard API endpoint, request/response format, error codes
    - Document Chat API endpoint, request/response format, error codes
    - Include example requests and responses
    - _Requirements: 5.1, 6.1_
  
  - [ ] 25.2 Create component documentation
    - Document Dashboard component props, state, and usage
    - Document Chat component props, state, and usage
    - Include usage examples and prop descriptions
    - _Requirements: 7.1, 8.1_
  
  - [ ] 25.3 Prepare deployment checklist
    - Verify all tests pass in CI/CD pipeline
    - Verify performance benchmarks met
    - Verify backward compatibility maintained
    - Prepare rollback plan if needed

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP, but are recommended for comprehensive correctness validation
- Each task references specific requirements for traceability
- Property-based tests use fast-check library with minimum 100 iterations per property
- All property tests are tagged with feature name and property number for identification
- Checkpoints at tasks 10, 15, 21, and 24 ensure incremental validation and early error detection
- Dashboard Lambda should complete before Chat Lambda to establish data model patterns
- Frontend components should be implemented after backend to ensure API contracts are stable
- Performance targets: Dashboard Lambda <500ms, Chat Lambda <3s, Dashboard Component <100ms render
- All code should follow existing TypeScript/React patterns and use only existing dependencies
