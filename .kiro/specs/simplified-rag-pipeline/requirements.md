# Requirements Document

## Introduction

This document specifies requirements for simplifying the MedAssist AI system to ensure a stable demo. The current system uses FAISS embeddings, Titan embeddings, Hindi translation, and a complex RAG pipeline that causes Lambda crashes and Bedrock throttling. The simplified system will remove vector search complexity and translation features, replacing them with direct document text retrieval and a single LLM model (Amazon Nova Lite) for reliable demo performance.

## Glossary

- **RAG_Lambda**: The AWS Lambda function that processes user questions and generates AI responses
- **Document_Store**: DynamoDB table storing extracted document text and metadata
- **Textract_Service**: AWS Textract service for extracting text from PDF and image documents
- **Nova_Lite**: Amazon Bedrock model (us.amazon.nova-lite-v1:0) used for generating answers
- **Chat_Interface**: Frontend user interface for asking questions and viewing answers
- **Upload_Service**: Backend service handling document upload and text extraction
- **Session**: A user session containing uploaded documents and chat history
- **Document_Context**: Concatenated text from uploaded documents used as context for the LLM

## Requirements

### Requirement 1: Remove Vector Search Dependencies

**User Story:** As a system administrator, I want to remove FAISS and vector search dependencies, so that the system avoids Lambda crashes and complexity.

#### Acceptance Criteria

1. THE RAG_Lambda SHALL NOT import the faiss library
2. THE RAG_Lambda SHALL NOT import the numpy library
3. THE RAG_Lambda SHALL NOT contain vector search logic
4. THE RAG_Lambda SHALL NOT contain embedding generation functions
5. THE Document_Store SHALL NOT store embedding vectors

### Requirement 2: Remove Translation Features

**User Story:** As a developer, I want to remove Hindi translation features, so that the system is simpler and more stable for the demo.

#### Acceptance Criteria

1. THE Chat_Interface SHALL NOT display a language selector
2. THE Chat_Interface SHALL NOT display a translation button
3. THE RAG_Lambda SHALL NOT contain translate_to_hindi() function
4. THE RAG_Lambda SHALL NOT call AWS Comprehend translation service
5. THE RAG_Lambda SHALL process all requests in English only

### Requirement 3: Upload and Extract Document Text

**User Story:** As a user, I want to upload PDF or image documents, so that I can ask questions about my medical reports.

#### Acceptance Criteria

1. WHEN a user uploads a PDF document, THE Upload_Service SHALL extract text using Textract_Service
2. WHEN a user uploads an image document, THE Upload_Service SHALL extract text using Textract_Service
3. WHEN text extraction completes, THE Upload_Service SHALL store the extracted text in Document_Store
4. THE Document_Store SHALL associate extracted text with the user Session
5. WHEN extraction fails, THE Upload_Service SHALL return a descriptive error message

### Requirement 4: Retrieve Document Context Directly

**User Story:** As a system, I want to retrieve document text directly from DynamoDB, so that I can provide context to the LLM without vector search.

#### Acceptance Criteria

1. WHEN a user asks a question, THE RAG_Lambda SHALL retrieve document text from Document_Store using the Session identifier
2. THE RAG_Lambda SHALL concatenate document text up to 4000 characters per document
3. THE RAG_Lambda SHALL use the concatenated text as Document_Context
4. IF no documents exist for the Session, THEN THE RAG_Lambda SHALL return an error message indicating no documents are uploaded
5. THE RAG_Lambda SHALL NOT perform embedding generation during retrieval

### Requirement 5: Generate Answers Using Nova Lite

**User Story:** As a user, I want to receive AI-generated answers to my questions, so that I can understand my medical reports.

#### Acceptance Criteria

1. WHEN a user question is received, THE RAG_Lambda SHALL create a prompt containing Document_Context and the user question
2. THE RAG_Lambda SHALL use the prompt template: "You are a medical document assistant. The following medical document text was uploaded by the user.\n\nDocument: {context}\n\nUser Question: {question}\n\nAnswer clearly using the document information. If the answer is not in the document, say you cannot find it in the report."
3. THE RAG_Lambda SHALL call Nova_Lite with modelId "us.amazon.nova-lite-v1:0"
4. THE RAG_Lambda SHALL NOT call any other Bedrock models
5. WHEN Nova_Lite returns a response, THE RAG_Lambda SHALL return JSON with format {"answer": generated_answer, "source": "uploaded_document"}

### Requirement 6: Simplified Chat Interface

**User Story:** As a user, I want to ask questions through a simple chat interface, so that I can interact with the AI assistant.

#### Acceptance Criteria

1. THE Chat_Interface SHALL send chat requests with JSON body containing sessionId, role, and message fields
2. THE Chat_Interface SHALL display user questions in the chat history
3. WHEN an answer is received, THE Chat_Interface SHALL display the answer in the chat history
4. THE Chat_Interface SHALL operate in English only
5. THE Chat_Interface SHALL NOT include language selection controls

### Requirement 7: Stable Demo Flow

**User Story:** As a demo presenter, I want the system to work reliably during the demo, so that judges can evaluate the application successfully.

#### Acceptance Criteria

1. WHEN a judge uploads a medical report, THE Upload_Service SHALL successfully extract and store the text within 30 seconds
2. WHEN a judge asks a question, THE RAG_Lambda SHALL return an answer within 10 seconds
3. THE RAG_Lambda SHALL NOT crash due to missing dependencies
4. THE RAG_Lambda SHALL NOT experience Bedrock throttling when using Nova_Lite
5. THE system SHALL support the complete flow: upload document, extract text, store text, ask question, receive answer

### Requirement 8: Remove Titan Embedding Service

**User Story:** As a developer, I want to remove Titan embedding generation, so that the system avoids throttling and complexity.

#### Acceptance Criteria

1. THE RAG_Lambda SHALL NOT call Bedrock Titan embedding models
2. THE RAG_Lambda SHALL NOT generate embeddings for user questions
3. THE Upload_Service SHALL NOT generate embeddings for document text
4. THE Document_Store SHALL NOT store Titan embedding vectors
5. THE system SHALL NOT include knowledge base embedding logic

### Requirement 9: Simplified Backend API

**User Story:** As a frontend developer, I want simplified backend endpoints, so that integration is straightforward.

#### Acceptance Criteria

1. THE backend API SHALL NOT accept language parameters in any endpoint
2. THE backend API SHALL accept sessionId in all document and chat requests
3. WHEN processing chat requests, THE backend SHALL retrieve documents using sessionId only
4. THE backend SHALL return responses in English only
5. THE backend SHALL NOT include translation-related response fields

### Requirement 10: Error Handling

**User Story:** As a user, I want clear error messages, so that I understand when something goes wrong.

#### Acceptance Criteria

1. IF no documents are uploaded for a Session, THEN THE RAG_Lambda SHALL return "No documents found. Please upload a document first."
2. IF Textract_Service fails, THEN THE Upload_Service SHALL return "Failed to extract text from document. Please try again."
3. IF Nova_Lite fails to respond, THEN THE RAG_Lambda SHALL return "Failed to generate answer. Please try again."
4. IF Document_Context exceeds token limits, THEN THE RAG_Lambda SHALL truncate the context and proceed
5. THE system SHALL log all errors for debugging purposes
