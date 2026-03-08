# Implementation Plan: MedAssist Conversational Enhancements

## Overview

This implementation plan breaks down the conversational enhancements into discrete coding tasks. The approach follows a layered implementation strategy: backend infrastructure first (conversation memory and structured extraction), then frontend integration, and finally UI refinements. Each task builds incrementally to ensure the system remains functional throughout development.

## Tasks

- [x] 1. Set up backend conversation memory infrastructure
  - [x] 1.1 Modify Chat Lambda to accept and process chat history
    - Update `rag.py` handler to parse `chatHistory` array from request body
    - Add default empty array handling for backward compatibility
    - Implement `format_chat_history()` function to convert history to string format
    - Limit formatted history to last 10 exchanges
    - _Requirements: 2.2, 2.4, 2.5_
  
  - [ ]* 1.2 Write property test for chat history formatting
    - **Property 7: Chat History Chronological Ordering**
    - **Validates: Requirements 2.4**
  
  - [x] 1.3 Implement chat history update logic in Chat Lambda
    - Create `update_chat_history()` function to append new exchanges
    - Implement automatic truncation when history exceeds 10 exchanges
    - Return updated history in response payload
    - _Requirements: 4.1, 4.3, 4.4, 4.5_
  
  - [ ]* 1.4 Write unit tests for chat history update logic
    - Test appending to empty history
    - Test appending to existing history
    - Test truncation when exceeding 10 exchanges
    - Test timestamp preservation
    - _Requirements: 4.1, 4.3, 4.4, 4.5_

- [x] 2. Implement role-based prompt system
  - [x] 2.1 Create role-specific prompt instructions
    - Implement `get_role_prompt_instructions()` function in `rag.py`
    - Define patient role instructions (simple language, avoid jargon)
    - Define doctor role instructions (clinical terminology, diagnostic focus)
    - Define ASHA worker role instructions (community health, referral guidance)
    - _Requirements: 8.1, 8.5, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [x] 2.2 Integrate role instructions into conversational prompt
    - Modify prompt construction to include role parameter
    - Add role-specific instructions to system message
    - Include formatted chat history in prompt context
    - Structure prompt to handle follow-up questions and pronoun resolution
    - _Requirements: 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 8.1_
  
  - [ ]* 2.3 Write property test for role-based prompt construction
    - **Property 24: Role Inclusion in Chat Prompt**
    - **Property 25: Role-Specific Instructions in Prompt**
    - **Validates: Requirements 8.1, 8.5**
  
  - [ ]* 2.4 Write unit tests for role-specific responses
    - Test patient role generates simple language responses
    - Test doctor role generates clinical terminology responses
    - Test ASHA worker role generates community health guidance
    - Verify role switching changes prompt instructions
    - _Requirements: 8.6, 9.1, 10.1, 11.1_

- [x] 3. Checkpoint - Verify backend conversation memory
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement structured health metrics extraction
  - [x] 4.1 Create Gemini extraction prompt for health metrics
    - Implement `create_extraction_prompt()` function in `dashboard.py`
    - Define JSON schema for extracted metrics (hemoglobin, WBC, platelets, glucose, cholesterol)
    - Include standard medical reference ranges for abnormal detection
    - Specify extraction instructions for key findings and abnormal flags
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 7.1, 7.2, 7.3, 7.4_
  
  - [x] 4.2 Implement JSON parsing and validation for extracted metrics
    - Create `parse_gemini_extraction()` function to parse Gemini JSON response
    - Handle markdown code block removal from response
    - Validate presence of expected metric keys
    - Set null for missing metrics
    - _Requirements: 7.5_
  
  - [ ]* 4.3 Write property test for metric extraction
    - **Property 14: Comprehensive Metric Extraction**
    - **Property 23: JSON Response Parsing**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6, 7.5**
  
  - [x] 4.3 Implement stat card generation from extracted metrics
    - Create `generate_stat_cards()` function to convert metrics to card format
    - Map each metric to StatCardData structure (title, value, unit, insight, severity)
    - Set severity based on abnormal flag (normal vs warning)
    - Generate Key Medical Insights card from key_findings array
    - _Requirements: 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 4.4 Write property test for stat card generation
    - **Property 17: Stat Card Generation from Metrics**
    - **Property 18: Stat Card Content Mapping**
    - **Property 19: Abnormal Metric Visual Indication**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5**
  
  - [x] 4.5 Add error handling and fallback for extraction failures
    - Implement `extract_metrics_with_fallback()` wrapper function
    - Create `generate_basic_stat_cards()` fallback for extraction failures
    - Add CloudWatch logging for extraction errors
    - Handle partial extraction success (display available metrics)
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_
  
  - [ ]* 4.6 Write unit tests for extraction error handling
    - Test complete extraction failure fallback
    - Test partial extraction success
    - Test JSON parsing failure handling
    - Test abnormal flag detection failure
    - Verify CloudWatch logging
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 5. Update Dashboard Lambda to use structured extraction
  - [x] 5.1 Modify dashboard handler to call extraction functions
    - Update `dashboard.py` handler to retrieve document text from DynamoDB
    - Call `extract_metrics_with_fallback()` for each document
    - Aggregate stat cards from all documents
    - Return stat cards in response payload
    - _Requirements: 5.1, 7.1_
  
  - [x] 5.2 Implement metric caching for performance
    - Add session-based caching for extracted metrics
    - Check cache before re-extraction on dashboard refresh
    - Set cache expiration based on document updates
    - _Requirements: 15.4_
  
  - [ ]* 5.3 Write property test for extraction performance
    - **Property 30: Metric Extraction Performance**
    - **Validates: Requirements 15.2**

- [x] 6. Checkpoint - Verify backend structured extraction
  - Ensure all tests pass, ask the user if questions arise.

- [-] 7. Implement frontend chat history state management
  - [x] 7.1 Add chat history state to ChatInterface component
    - Define ChatMessage and ChatHistoryEntry TypeScript interfaces
    - Add `chatHistory` state using useState hook
    - Initialize empty chat history on component mount
    - _Requirements: 1.1, 1.5_
  
  - [x] 7.2 Implement message appending to chat history
    - Update `handleSendMessage()` to append user message to history
    - Append AI response to history when received
    - Add timestamps to each message
    - _Requirements: 1.2, 1.3_
  
  - [ ]* 7.3 Write property test for chat history appending
    - **Property 1: Chat History Message Appending**
    - **Property 2: Chat History Structure Validation**
    - **Validates: Requirements 1.2, 1.3, 1.5**
  
  - [x] 7.4 Implement chat history transmission to backend
    - Modify API request payload to include chatHistory array
    - Send complete history with each chat request
    - _Requirements: 2.1_
  
  - [x] 7.5 Implement frontend history synchronization
    - Update local chatHistory state with backend-returned history
    - Preserve message ordering and timestamps
    - Handle backend modifications (truncation)
    - _Requirements: 4.2, 4.4, 4.5_
  
  - [ ]* 7.6 Write property test for history synchronization
    - **Property 10: Frontend History Synchronization**
    - **Property 11: History Ordering and Timestamp Preservation**
    - **Validates: Requirements 4.2, 4.4**
  
  - [x] 7.7 Add error handling for chat history failures
    - Handle history transmission failures (proceed without context)
    - Handle frontend state update failures (display error, allow retry)
    - Implement graceful degradation
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_
  
  - [ ]* 7.8 Write unit tests for chat history error handling
    - Test transmission failure handling
    - Test state update failure handling
    - Test graceful degradation
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [-] 8. Implement frontend role selection and integration
  - [ ] 8.1 Add role selection UI component
    - Create role selector dropdown or radio buttons
    - Include options for Patient, Doctor, ASHA Worker
    - Store selected role in component state
    - _Requirements: 8.1_
  
  - [ ] 8.2 Pass role parameter in chat requests
    - Include role in API request payload
    - Update request interface to include role field
    - Default to 'patient' role if not specified
    - _Requirements: 8.1_
  
  - [ ] 8.3 Handle role switching
    - Clear chat history when role changes (optional, based on UX decision)
    - Update UI to indicate current role
    - _Requirements: 8.6_
  
  - [ ]* 8.4 Write unit tests for role selection
    - Test role parameter inclusion in requests
    - Test role switching behavior
    - _Requirements: 8.1, 8.6_

- [-] 9. Replace Document Preview with Key Medical Insights component
  - [x] 9.1 Create StatCard component
    - Implement StatCard React component with props for title, value, unit, insight, severity
    - Add severity-based styling (normal, warning, critical)
    - Include visual indicators for abnormal flags
    - _Requirements: 6.2, 6.3, 6.4, 6.5_
  
  - [x] 9.2 Create KeyMedicalInsights component
    - Implement container component for stat cards
    - Add grid layout for organizing cards
    - Handle empty state (no metrics extracted)
    - Display fallback message when extraction fails
    - _Requirements: 6.1, 6.6, 6.7_
  
  - [x] 9.3 Update Dashboard component to use KeyMedicalInsights
    - Remove Document Preview component
    - Add KeyMedicalInsights component
    - Pass stat cards data from API response
    - Update conditional rendering based on documents_uploaded count
    - _Requirements: 6.1, 12.1, 12.2, 12.3_
  
  - [ ]* 9.4 Write unit tests for UI components
    - Test StatCard rendering with different severity levels
    - Test KeyMedicalInsights grid layout
    - Test empty state display
    - Test abnormal flag visual indicators
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [x] 10. Fix document processing status UI
  - [x] 10.1 Update status message conditional logic
    - Remove "Document not processed yet" message when documents_uploaded > 0
    - Display KeyMedicalInsights component when documents_uploaded > 0
    - Show upload prompt when documents_uploaded = 0
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [x] 10.2 Add processing status feedback
    - Display loading indicator during document processing
    - Update documents_uploaded count after successful processing
    - Show success message after processing completes
    - _Requirements: 12.4, 12.5_
  
  - [ ]* 10.3 Write unit tests for status UI
    - Test conditional rendering based on documents_uploaded
    - Test processing status display
    - Test count update after processing
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 11. Checkpoint - Verify frontend integration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Integration testing and backward compatibility verification
  - [ ]* 12.1 Write integration tests for full chat flow
    - Test frontend → API → Lambda → Gemini → response flow
    - Test chat history round-trip (send and receive updated history)
    - Test role-based response generation
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 4.1, 4.2, 8.1_
  
  - [ ]* 12.2 Write integration tests for dashboard flow
    - Test frontend → API → Lambda → DynamoDB → Gemini → response flow
    - Test metric extraction and stat card generation
    - Test error handling and fallback behavior
    - _Requirements: 5.1, 6.2, 7.1, 17.1, 17.2_
  
  - [ ]* 12.3 Verify backward compatibility
    - Test existing upload to dashboard to chat workflow
    - Test API endpoints with old request formats (without chatHistory)
    - Test Lambda functions with missing optional fields
    - Verify DynamoDB schema compatibility
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_
  
  - [ ]* 12.4 Write performance tests
    - Test chat response time (should be < 5 seconds)
    - Test metric extraction time (should be < 3 seconds)
    - Test with various input sizes
    - _Requirements: 15.2, 15.3_
  
  - [ ]* 12.5 Write property tests for conversation context
    - **Property 9: Chat Response History Update**
    - **Property 12: Backend History Modification Reflection**
    - **Validates: Requirements 4.1, 4.3, 4.5**

- [x] 13. Final checkpoint and validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical breakpoints
- Property tests validate universal correctness properties across random inputs
- Unit tests validate specific examples and edge cases
- Backend tasks (1-6) should be completed before frontend tasks (7-11) to enable independent testing
- Integration tests (12) verify end-to-end functionality and backward compatibility
- The implementation maintains the existing architecture and does not require database migrations
