# Implementation Plan: Simplified RAG Pipeline

## Overview

This implementation plan simplifies the MedAssist AI system by removing FAISS vector search, Titan embeddings, and Hindi translation features. The simplified architecture uses direct DynamoDB text retrieval and Amazon Nova Lite for stable demo performance. The implementation focuses on modifying existing Lambda functions (RAG, Extraction) and the frontend chat interface to remove complexity while maintaining core functionality.

## Tasks

- [x] 1. Remove FAISS and vector search dependencies from RAG Lambda
  - [x] 1.1 Remove FAISS and numpy imports from rag.py
    - Remove `import faiss` and `import numpy` statements
    - Remove any vector search utility imports
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.2 Remove vector search logic and embedding generation functions
    - Delete FAISS index loading code
    - Delete embedding generation functions
    - Delete vector similarity search functions
    - _Requirements: 1.3, 1.4, 4.5_
  
  - [x] 1.3 Update requirements.txt to remove FAISS and numpy
    - Remove faiss-cpu or faiss-gpu from requirements.txt
    - Remove numpy from requirements.txt
    - _Requirements: 1.1, 1.2_

- [x] 2. Remove translation features from RAG Lambda and frontend
  - [x] 2.1 Remove translation function from rag.py
    - Delete translate_to_hindi() function
    - Remove AWS Comprehend translation service calls
    - Remove language parameter handling from handler function
    - _Requirements: 2.3, 2.4, 2.5, 9.1_
  
  - [x] 2.2 Remove language selector from frontend chat interface
    - Remove language selector dropdown component
    - Remove translation toggle button
    - Remove language state management code
    - Remove language parameter from API calls
    - _Requirements: 2.1, 2.2, 6.4, 6.5_

- [ ] 3. Implement direct document text retrieval in RAG Lambda
  - [x] 3.1 Create retrieve_document_text() function
    - Query DynamoDB for all documents with matching sessionId
    - Concatenate extracted text from each document (max 4000 chars per document)
    - Return combined text as context string
    - Handle case where no documents exist for session
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ]* 3.2 Write property test for document retrieval
    - **Property 4: Document Retrieval Uses Session ID**
    - **Validates: Requirements 4.1, 9.2, 9.3**
    - Generate random sessionIds with varying numbers of documents
    - Verify all documents for session are retrieved
  
  - [ ]* 3.3 Write property test for text truncation
    - **Property 5: Document Text Truncation**
    - **Validates: Requirements 4.2**
    - Generate random text strings of varying lengths (including > 4000 chars)
    - Verify truncated text is ≤ 4000 characters per document

- [ ] 4. Implement Nova Lite prompt construction and LLM calling
  - [x] 4.1 Create construct_prompt() function
    - Implement prompt template with document context and user question
    - Use template: "You are a medical document assistant. The following medical document text was uploaded by the user.\n\nDocument: {context}\n\nUser Question: {question}\n\nAnswer clearly using the document information. If the answer is not in the document, say you cannot find it in the report."
    - Add optional role-specific instructions (doctor, patient, asha)
    - _Requirements: 5.1, 5.2_
  
  - [x] 4.2 Create call_nova_lite() function
    - Call Amazon Bedrock with modelId "us.amazon.nova-lite-v1:0"
    - Pass constructed prompt to Nova Lite
    - Parse response and extract answer text
    - Return answer in format {"answer": string, "source": "uploaded_document"}
    - _Requirements: 5.3, 5.4, 5.5_
  
  - [ ]* 4.3 Write property test for prompt construction
    - **Property 6: Prompt Construction with Template**
    - **Validates: Requirements 5.1, 5.2**
    - Generate random contexts and questions
    - Verify prompt contains template text, context, and question
  
  - [ ]* 4.4 Write property test for Nova Lite model usage
    - **Property 7: Nova Lite Model Usage**
    - **Validates: Requirements 5.3, 5.5**
    - Generate random prompts
    - Verify modelId is "us.amazon.nova-lite-v1:0"
    - Verify response format is {"answer": string, "source": "uploaded_document"}

- [ ] 5. Update RAG Lambda handler function
  - [x] 5.1 Refactor handler to use new retrieval and generation functions
    - Parse request (remove language parameter handling)
    - Call retrieve_document_text() with sessionId
    - Call construct_prompt() with context, question, and role
    - Call call_nova_lite() with prompt
    - Return response in required format
    - _Requirements: 4.1, 5.1, 5.5, 9.2, 9.3_
  
  - [ ]* 5.2 Write unit tests for handler function
    - Test successful flow with valid session and documents
    - Test error case with no documents
    - Test error case with Nova Lite failure
    - _Requirements: 5.5, 10.1, 10.3_

- [ ] 6. Implement error handling in RAG Lambda
  - [x] 6.1 Add error handling for no documents case
    - Check if retrieve_document_text() returns empty context
    - Return error: {"error": {"code": "NO_DOCUMENTS", "message": "No documents found. Please upload a document first.", "retryable": false}}
    - _Requirements: 10.1_
  
  - [x] 6.2 Add error handling for Nova Lite failures
    - Catch Bedrock API exceptions
    - Return error: {"error": {"code": "LLM_FAILED", "message": "Failed to generate answer. Please try again.", "retryable": true}}
    - _Requirements: 10.3_
  
  - [ ] 6.3 Add error handling for DynamoDB failures
    - Catch DynamoDB query exceptions
    - Return error: {"error": {"code": "DATABASE_ERROR", "message": "Failed to retrieve documents. Please try again.", "retryable": true}}
    - _Requirements: 10.5_
  
  - [ ] 6.4 Add context truncation handling
    - Check if combined context exceeds token limits
    - Truncate context to fit within limits
    - Log warning to CloudWatch
    - Proceed with answer generation
    - _Requirements: 10.4_
  
  - [x] 6.5 Implement structured error logging
    - Log all errors to CloudWatch with JSON format
    - Include event type, sessionId, error message, and timestamp
    - _Requirements: 10.5_
  
  - [ ]* 6.6 Write property test for error logging
    - **Property 12: Error Logging**
    - **Validates: Requirements 10.5**
    - Generate random error conditions
    - Verify CloudWatch receives structured log entry

- [ ] 7. Checkpoint - Ensure RAG Lambda tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Remove embedding generation from Extraction Lambda
  - [ ] 8.1 Remove Embedding Lambda invocation from extraction.py
    - Delete code that invokes Embedding Lambda after text extraction
    - Remove embedding-related imports
    - _Requirements: 8.3_
  
  - [ ] 8.2 Update DynamoDB storage to remove embedding fields
    - Remove embedding vector storage code
    - Store only extractedText field
    - _Requirements: 1.5, 8.4_
  
  - [ ] 8.3 Simplify extraction flow
    - Keep Textract text extraction logic
    - Store extracted text in DynamoDB with sessionId
    - Remove medical entity extraction (Comprehend Medical) for simplicity
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 8.4 Write property test for extraction storage
    - **Property 2: Successful Extraction Stores Text with Session**
    - **Validates: Requirements 3.3, 3.4**
    - Generate random extracted text and sessionIds
    - Verify text is stored in DynamoDB with correct sessionId
  
  - [ ]* 8.5 Write unit tests for extraction error handling
    - Test Textract failure returns error message
    - Verify error message: "Failed to extract text from document. Please try again."
    - _Requirements: 3.5, 10.2_

- [ ] 9. Update frontend chat interface
  - [x] 9.1 Remove language-related UI components
    - Remove language selector dropdown from chat interface
    - Remove translation toggle button
    - Remove language state variables
    - _Requirements: 2.1, 2.2, 6.4, 6.5_
  
  - [x] 9.2 Update API call to remove language parameter
    - Modify sendChatMessage() to not include language parameter
    - Ensure request body contains only sessionId, role, and message
    - _Requirements: 6.1, 9.1, 9.2_
  
  - [ ]* 9.3 Write property test for chat request format
    - **Property 8: Chat Request Contains Required Fields**
    - **Validates: Requirements 6.1**
    - Generate random sessionIds, roles, and messages
    - Verify request body contains sessionId, role, and message
  
  - [ ]* 9.4 Write property test for message display
    - **Property 9: Messages Display in Chat History**
    - **Validates: Requirements 6.2, 6.3**
    - Generate random user and AI messages
    - Verify messages appear in chat history after being sent/received

- [ ] 10. Update backend API endpoints
  - [ ] 10.1 Remove language parameter from upload endpoint
    - Modify upload Lambda to not accept language parameter
    - Ensure endpoint accepts only sessionId, role, file, filename, contentType
    - _Requirements: 9.1_
  
  - [ ] 10.2 Remove language parameter from chat endpoint
    - Modify RAG Lambda handler to not accept language parameter
    - Ensure endpoint accepts only sessionId, role, message
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [ ] 10.3 Update API responses to remove translation fields
    - Ensure responses do not include language or translation-related fields
    - Return responses in English only
    - _Requirements: 9.4, 9.5_

- [ ] 11. Remove Titan embedding service calls
  - [ ] 11.1 Remove Titan embedding calls from all Lambda functions
    - Search for and remove all Bedrock Titan embedding model invocations
    - Remove embedding generation for user questions
    - Remove embedding generation for document text
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [ ] 11.2 Remove knowledge base embedding logic
    - Delete or disable knowledge base embedding Lambda
    - Remove knowledge base embedding generation code
    - _Requirements: 8.5_

- [ ] 12. Clean up DynamoDB schema
  - [ ] 12.1 Update Document table schema documentation
    - Document that embedding fields are no longer used
    - Document that only extractedText field is stored
    - Note: Existing records with embeddings can remain (no migration needed)
    - _Requirements: 1.5, 8.4_

- [ ] 13. Update Lambda deployment packages
  - [ ] 13.1 Rebuild RAG Lambda deployment package
    - Run pip install with updated requirements.txt (no FAISS, no numpy)
    - Create new deployment zip
    - _Requirements: 1.1, 1.2_
  
  - [ ] 13.2 Rebuild Extraction Lambda deployment package
    - Create new deployment zip with updated code
    - _Requirements: 8.3_

- [ ] 14. Final checkpoint - Integration testing
  - [ ] 14.1 Test complete upload and extraction flow
    - Upload a test PDF document
    - Verify text extraction completes within 30 seconds
    - Verify extracted text is stored in DynamoDB
    - _Requirements: 7.1_
  
  - [ ] 14.2 Test complete chat flow
    - Ask a question with valid sessionId
    - Verify answer is returned within 10 seconds
    - Verify answer format is correct
    - _Requirements: 7.2_
  
  - [ ] 14.3 Test error scenarios
    - Test asking question with no documents uploaded
    - Verify error message is correct
    - _Requirements: 10.1_
  
  - [ ]* 14.4 Write property test for end-to-end flow
    - **Property 10: End-to-End Flow Completion**
    - **Validates: Requirements 7.5**
    - Test complete flow: upload document, extract text, ask question
    - Verify all steps complete successfully and return an answer
  
  - [ ] 14.5 Verify no Lambda crashes
    - Confirm RAG Lambda does not crash due to missing dependencies
    - Confirm no Bedrock throttling occurs with Nova Lite
    - _Requirements: 7.3, 7.4_

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation removes complexity rather than adding features
- Existing DynamoDB records with embeddings can remain (no data migration needed)
- Focus on stability and reliability for demo performance
- Property tests use Hypothesis (Python) for Lambda functions and fast-check (TypeScript) for frontend
- Each property test runs minimum 100 iterations with randomized inputs
