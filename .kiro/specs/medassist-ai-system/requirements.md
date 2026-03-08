# Requirements Document

## Introduction

The MedAssist AI System is a single-page React web application that analyzes medical documents using AWS Generative AI and Retrieval-Augmented Generation (RAG) to generate role-based dashboards and chat insights. The system processes medical documents (PDFs, lab reports, prescriptions) and provides contextual health insights tailored to three user roles: Doctor, Patient, and ASHA Worker. The application uses Amazon Bedrock Nova 2 Lite model for text generation, AWS services for document processing, and a hybrid RAG architecture combining uploaded documents with a medical knowledge base.

## Glossary

- **MedAssist_System**: The complete web application including frontend, backend, and AI processing pipeline
- **User**: Any person interacting with the application (Doctor, Patient, or ASHA Worker)
- **Document**: Medical files including PDFs, lab report images, and prescription photos
- **RAG_Pipeline**: Retrieval-Augmented Generation system that combines document embeddings with knowledge base for context-aware responses
- **Dashboard**: The main interface displaying health insight stat cards generated from analyzed documents
- **Session**: A single continuous interaction period where uploaded documents and context are maintained
- **Stat_Card**: A visual component displaying a specific health metric or insight
- **Chat_Interface**: The conversational UI component for asking questions about documents and medical topics
- **Knowledge_Base**: Pre-embedded medical information covering diabetes, blood pressure, cholesterol, heart health, and basic health guidance
- **Embedding**: Vector representation of text chunks used for similarity search
- **Role**: User profile type that determines language, complexity, and focus of AI responses
- **Lambda_Function**: AWS serverless compute service executing the processing pipeline
- **Vector_Store**: FAISS-based storage system for document embeddings
- **Bedrock_Model**: Amazon Bedrock Nova 2 Lite generative AI model
- **Medical_Entity**: Health-related information extracted by AWS Comprehend Medical

## Requirements

### Requirement 1: Role Selection

**User Story:** As a User, I want to select my profile role, so that I receive insights appropriate to my medical expertise and needs.

#### Acceptance Criteria

1. THE MedAssist_System SHALL provide three role options: Doctor, Patient, and ASHA Worker
2. WHEN a User selects a role, THE MedAssist_System SHALL configure the interface language and response complexity for that role
3. WHERE the role is Doctor, THE MedAssist_System SHALL provide responses in English with technical clinical terminology
4. WHERE the role is Patient, THE MedAssist_System SHALL provide responses in simple language with optional Hindi translation
5. WHERE the role is ASHA Worker, THE MedAssist_System SHALL provide responses focused on community health guidance with optional Hindi translation
6. WHEN a User switches roles during a Session, THE MedAssist_System SHALL regenerate the Dashboard with role-appropriate insights

### Requirement 2: Document Upload

**User Story:** As a User, I want to upload medical documents, so that the system can analyze them and provide health insights.

#### Acceptance Criteria

1. THE MedAssist_System SHALL accept PDF files as Document uploads
2. THE MedAssist_System SHALL accept image files (JPEG, PNG) as Document uploads
3. WHEN a User uploads a Document, THE MedAssist_System SHALL store it in AWS S3
4. WHEN a User uploads a Document, THE MedAssist_System SHALL initiate the RAG_Pipeline processing
5. WHEN a User uploads multiple Documents within a Session, THE MedAssist_System SHALL process all Documents and combine their context
6. THE MedAssist_System SHALL display upload progress feedback to the User

### Requirement 3: Document Text Extraction

**User Story:** As a User, I want the system to extract text from my documents, so that the content can be analyzed.

#### Acceptance Criteria

1. WHEN a PDF Document is uploaded, THE MedAssist_System SHALL use AWS Textract to extract text content
2. WHEN an image Document is uploaded, THE MedAssist_System SHALL use AWS Textract to extract text content
3. WHEN an image Document is uploaded, THE MedAssist_System SHALL use AWS Rekognition to detect visual elements
4. IF text extraction fails, THEN THE MedAssist_System SHALL return an error message to the User
5. THE MedAssist_System SHALL preserve the extracted text for the duration of the Session

### Requirement 4: Medical Entity Extraction

**User Story:** As a User, I want the system to identify medical information in my documents, so that relevant health data is recognized and analyzed.

#### Acceptance Criteria

1. WHEN text is extracted from a Document, THE MedAssist_System SHALL use AWS Comprehend Medical to identify Medical_Entity instances
2. THE MedAssist_System SHALL extract medication names as Medical_Entity instances
3. THE MedAssist_System SHALL extract medical conditions as Medical_Entity instances
4. THE MedAssist_System SHALL extract test results as Medical_Entity instances
5. THE MedAssist_System SHALL extract dosage information as Medical_Entity instances

### Requirement 5: Document Chunking and Embedding

**User Story:** As a User, I want my documents to be processed into searchable format, so that the AI can retrieve relevant context for my questions.

#### Acceptance Criteria

1. WHEN text is extracted from a Document, THE MedAssist_System SHALL split the text into chunks of 512 tokens or fewer
2. WHEN text chunks are created, THE MedAssist_System SHALL generate Embedding vectors using Amazon Titan Embeddings
3. WHEN Embedding vectors are generated, THE MedAssist_System SHALL store them in DynamoDB with associated metadata
4. THE MedAssist_System SHALL maintain chunk overlap of 50 tokens between consecutive chunks
5. THE MedAssist_System SHALL index Embedding vectors in the Vector_Store for similarity search

### Requirement 6: Knowledge Base Initialization

**User Story:** As a User, I want access to general medical knowledge, so that I can ask health questions beyond my uploaded documents.

#### Acceptance Criteria

1. THE MedAssist_System SHALL initialize a Knowledge_Base containing information about diabetes
2. THE MedAssist_System SHALL initialize a Knowledge_Base containing information about blood pressure
3. THE MedAssist_System SHALL initialize a Knowledge_Base containing information about cholesterol
4. THE MedAssist_System SHALL initialize a Knowledge_Base containing information about heart health
5. THE MedAssist_System SHALL initialize a Knowledge_Base containing basic health guidance
6. WHEN the Knowledge_Base is initialized, THE MedAssist_System SHALL generate Embedding vectors for all knowledge documents
7. WHEN the Knowledge_Base is initialized, THE MedAssist_System SHALL store Knowledge_Base Embedding vectors in the Vector_Store

### Requirement 7: Dashboard Generation

**User Story:** As a User, I want to see a visual dashboard of my health insights, so that I can quickly understand key findings from my documents.

#### Acceptance Criteria

1. WHEN Document processing completes, THE MedAssist_System SHALL generate a Dashboard with Stat_Card components
2. THE MedAssist_System SHALL generate Stat_Card components for blood glucose levels when present in Documents
3. THE MedAssist_System SHALL generate Stat_Card components for hemoglobin levels when present in Documents
4. THE MedAssist_System SHALL generate Stat_Card components for cholesterol levels when present in Documents
5. THE MedAssist_System SHALL generate Stat_Card components for risk scores when calculable from Documents
6. THE MedAssist_System SHALL generate Stat_Card components for key clinical observations
7. WHEN a User uploads additional Documents, THE MedAssist_System SHALL update the Dashboard with combined insights
8. THE MedAssist_System SHALL use the Bedrock_Model to generate role-appropriate summaries for each Stat_Card

### Requirement 8: Hybrid RAG Retrieval

**User Story:** As a User, I want the AI to use both my documents and medical knowledge when answering questions, so that I receive comprehensive and contextual responses.

#### Acceptance Criteria

1. WHEN a User submits a chat question, THE MedAssist_System SHALL generate an Embedding vector for the question
2. WHEN a question Embedding is generated, THE MedAssist_System SHALL perform vector similarity search against uploaded Document Embedding vectors
3. WHEN a question Embedding is generated, THE MedAssist_System SHALL perform vector similarity search against Knowledge_Base Embedding vectors
4. THE MedAssist_System SHALL retrieve the top 5 most similar chunks from uploaded Documents
5. THE MedAssist_System SHALL retrieve the top 3 most similar chunks from the Knowledge_Base
6. THE MedAssist_System SHALL combine retrieved Document chunks and Knowledge_Base chunks into a unified context
7. THE MedAssist_System SHALL use FAISS for vector similarity search operations

### Requirement 9: AI Response Generation

**User Story:** As a User, I want to receive AI-generated answers to my medical questions, so that I can understand my health information better.

#### Acceptance Criteria

1. WHEN context is retrieved from the RAG_Pipeline, THE MedAssist_System SHALL construct a prompt combining the context and user question
2. WHEN a prompt is constructed, THE MedAssist_System SHALL send it to the Bedrock_Model (Amazon Bedrock Nova 2 Lite)
3. WHEN the Bedrock_Model generates a response, THE MedAssist_System SHALL format it according to the selected Role
4. WHERE the Role is Doctor, THE MedAssist_System SHALL generate responses using technical clinical language
5. WHERE the Role is Patient, THE MedAssist_System SHALL generate responses using simple explanatory language
6. WHERE the Role is ASHA Worker, THE MedAssist_System SHALL generate responses focused on community health guidance
7. THE MedAssist_System SHALL display the AI response in the Chat_Interface within 5 seconds of question submission

### Requirement 10: Chat Interface

**User Story:** As a User, I want to chat with the AI about my medical documents, so that I can ask questions and get personalized insights.

#### Acceptance Criteria

1. THE MedAssist_System SHALL provide a Chat_Interface component in the main workspace
2. WHEN a User types a message, THE MedAssist_System SHALL accept text input of up to 1000 characters
3. WHEN a User submits a message, THE MedAssist_System SHALL display the message in the chat history
4. WHEN the AI generates a response, THE MedAssist_System SHALL display it in the chat history below the user message
5. THE MedAssist_System SHALL maintain chat history for the duration of the Session
6. THE MedAssist_System SHALL support asking questions about uploaded Documents
7. THE MedAssist_System SHALL support asking general medical questions using the Knowledge_Base

### Requirement 11: Language Translation

**User Story:** As a Patient or ASHA Worker, I want to view responses in Hindi, so that I can understand health information in my preferred language.

#### Acceptance Criteria

1. WHERE the Role is Patient, THE MedAssist_System SHALL provide a Hindi translation option
2. WHERE the Role is ASHA Worker, THE MedAssist_System SHALL provide a Hindi translation option
3. WHEN a User enables Hindi translation, THE MedAssist_System SHALL translate AI responses to Hindi
4. WHEN a User enables Hindi translation, THE MedAssist_System SHALL translate Dashboard Stat_Card content to Hindi
5. WHERE the Role is Doctor, THE MedAssist_System SHALL provide responses in English only without translation options

### Requirement 12: Session Management

**User Story:** As a User, I want my uploaded documents and context to persist during my session, so that I can work with multiple documents seamlessly.

#### Acceptance Criteria

1. WHEN a User uploads the first Document, THE MedAssist_System SHALL create a new Session
2. WHILE a Session is active, THE MedAssist_System SHALL maintain all uploaded Document references
3. WHILE a Session is active, THE MedAssist_System SHALL maintain all Document Embedding vectors in the Vector_Store
4. WHILE a Session is active, THE MedAssist_System SHALL maintain chat history
5. WHEN a User uploads additional Documents during a Session, THE MedAssist_System SHALL add them to the existing Session context
6. WHEN a User closes the application, THE MedAssist_System SHALL terminate the Session

### Requirement 13: Export Dashboard Report

**User Story:** As a User, I want to export my dashboard insights as a PDF, so that I can save or share my health summary.

#### Acceptance Criteria

1. THE MedAssist_System SHALL provide an export button in the Dashboard interface
2. WHEN a User clicks the export button, THE MedAssist_System SHALL generate a PDF summary report
3. THE MedAssist_System SHALL include all Stat_Card insights in the exported PDF
4. THE MedAssist_System SHALL include the selected Role in the exported PDF
5. THE MedAssist_System SHALL include a timestamp in the exported PDF
6. WHEN PDF generation completes, THE MedAssist_System SHALL download the file to the User's device

### Requirement 14: User Interface Design

**User Story:** As a User, I want a modern and intuitive interface, so that I can easily navigate and use the application.

#### Acceptance Criteria

1. THE MedAssist_System SHALL implement a single-page React application architecture
2. THE MedAssist_System SHALL use a dark theme with liquid glass style visual components
3. THE MedAssist_System SHALL provide a sidebar containing the Role selector
4. THE MedAssist_System SHALL provide a main workspace containing the upload area, Dashboard, and Chat_Interface
5. THE MedAssist_System SHALL style the Chat_Interface similar to ChatGPT's conversational layout
6. THE MedAssist_System SHALL display Stat_Card components using card-based layouts with visual hierarchy

### Requirement 15: API Gateway Integration

**User Story:** As a developer, I want a RESTful API for the frontend to communicate with backend services, so that the application can process documents and handle chat requests.

#### Acceptance Criteria

1. THE MedAssist_System SHALL expose an API endpoint for document upload via AWS API Gateway
2. THE MedAssist_System SHALL expose an API endpoint for chat message submission via AWS API Gateway
3. THE MedAssist_System SHALL expose an API endpoint for dashboard data retrieval via AWS API Gateway
4. THE MedAssist_System SHALL expose an API endpoint for PDF export via AWS API Gateway
5. WHEN an API request is received, THE MedAssist_System SHALL invoke the appropriate Lambda_Function
6. THE MedAssist_System SHALL return API responses in JSON format
7. IF an API request fails, THEN THE MedAssist_System SHALL return an appropriate HTTP error code and error message

### Requirement 16: Lambda Processing Pipeline

**User Story:** As a developer, I want serverless compute functions to process documents and handle AI operations, so that the system scales automatically and minimizes infrastructure management.

#### Acceptance Criteria

1. THE MedAssist_System SHALL implement a Lambda_Function for document upload processing
2. THE MedAssist_System SHALL implement a Lambda_Function for text extraction and entity recognition
3. THE MedAssist_System SHALL implement a Lambda_Function for embedding generation and storage
4. THE MedAssist_System SHALL implement a Lambda_Function for RAG retrieval and AI response generation
5. THE MedAssist_System SHALL implement a Lambda_Function for dashboard generation
6. THE MedAssist_System SHALL implement a Lambda_Function for PDF export
7. WHEN a Lambda_Function executes, THE MedAssist_System SHALL log execution details to AWS CloudWatch

### Requirement 17: Data Storage

**User Story:** As a developer, I want persistent storage for documents and embeddings, so that the system can retrieve and process information efficiently.

#### Acceptance Criteria

1. THE MedAssist_System SHALL store uploaded Documents in AWS S3
2. THE MedAssist_System SHALL store Document Embedding vectors in DynamoDB
3. THE MedAssist_System SHALL store Knowledge_Base Embedding vectors in DynamoDB
4. THE MedAssist_System SHALL store Session metadata in DynamoDB
5. THE MedAssist_System SHALL organize S3 storage by Session identifier
6. THE MedAssist_System SHALL include Document metadata (filename, upload timestamp, role) in DynamoDB records

### Requirement 18: Vector Similarity Search

**User Story:** As a developer, I want efficient vector similarity search, so that the RAG system can quickly retrieve relevant context for user questions.

#### Acceptance Criteria

1. THE MedAssist_System SHALL use FAISS for vector similarity search operations
2. WHEN Embedding vectors are stored, THE MedAssist_System SHALL index them in FAISS
3. WHEN a similarity search is performed, THE MedAssist_System SHALL return results ranked by cosine similarity score
4. THE MedAssist_System SHALL perform similarity searches in under 500 milliseconds for datasets up to 10000 vectors
5. THE MedAssist_System SHALL maintain separate FAISS indices for Document embeddings and Knowledge_Base embeddings

### Requirement 19: Monitoring and Logging

**User Story:** As a developer, I want comprehensive logging and monitoring, so that I can troubleshoot issues and monitor system performance.

#### Acceptance Criteria

1. THE MedAssist_System SHALL log all Lambda_Function invocations to AWS CloudWatch
2. THE MedAssist_System SHALL log all API Gateway requests to AWS CloudWatch
3. THE MedAssist_System SHALL log document processing pipeline stages to AWS CloudWatch
4. THE MedAssist_System SHALL log Bedrock_Model API calls to AWS CloudWatch
5. IF an error occurs in any Lambda_Function, THEN THE MedAssist_System SHALL log the error details with stack trace to AWS CloudWatch
6. THE MedAssist_System SHALL log response latency metrics for all API endpoints

### Requirement 20: Responsible AI Disclaimer

**User Story:** As a User, I want to understand the limitations of the AI system, so that I use it appropriately and seek professional medical advice when needed.

#### Acceptance Criteria

1. THE MedAssist_System SHALL display a disclaimer stating "This AI system provides informational insights only and does not provide medical diagnosis. Always consult a licensed healthcare professional."
2. THE MedAssist_System SHALL display the disclaimer on the initial application load
3. THE MedAssist_System SHALL display the disclaimer in the Dashboard interface
4. THE MedAssist_System SHALL include the disclaimer in exported PDF reports
5. WHEN a User first interacts with the Chat_Interface, THE MedAssist_System SHALL display the disclaimer message

### Requirement 21: Error Handling

**User Story:** As a User, I want clear error messages when something goes wrong, so that I understand what happened and what to do next.

#### Acceptance Criteria

1. IF a Document upload fails, THEN THE MedAssist_System SHALL display an error message indicating the failure reason
2. IF text extraction fails, THEN THE MedAssist_System SHALL display an error message and allow the User to retry
3. IF the Bedrock_Model API call fails, THEN THE MedAssist_System SHALL display an error message in the Chat_Interface
4. IF the RAG_Pipeline fails to retrieve context, THEN THE MedAssist_System SHALL display an error message and suggest uploading documents
5. IF PDF export fails, THEN THE MedAssist_System SHALL display an error message and allow the User to retry
6. THE MedAssist_System SHALL display error messages in user-friendly language without exposing technical implementation details

### Requirement 22: Security and Privacy

**User Story:** As a User, I want my medical documents to be handled securely, so that my health information remains private and protected.

#### Acceptance Criteria

1. THE MedAssist_System SHALL encrypt Documents at rest in AWS S3 using AES-256 encryption
2. THE MedAssist_System SHALL encrypt data in transit using TLS 1.2 or higher
3. THE MedAssist_System SHALL encrypt Embedding vectors in DynamoDB using AWS managed encryption
4. THE MedAssist_System SHALL implement AWS IAM roles with least privilege access for all Lambda_Function executions
5. THE MedAssist_System SHALL not persist User data beyond the Session duration
6. WHEN a Session terminates, THE MedAssist_System SHALL delete all uploaded Documents from S3 within 24 hours
7. THE MedAssist_System SHALL not log sensitive medical information in CloudWatch logs
