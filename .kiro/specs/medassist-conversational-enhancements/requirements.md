# Requirements Document

## Introduction

The MedAssist Conversational Enhancements feature improves the user experience of the existing MedAssist AI system by adding conversation memory, structured dashboard insights, role-based AI response customization, and UI refinements. The system currently processes medical documents through a pipeline (Frontend → API Gateway → Lambda → Textract → DynamoDB → Gemini) but lacks conversational context retention, presents raw document text in an unstructured format, and provides identical responses regardless of user role. These enhancements maintain the existing architecture while improving how users interact with and understand their medical information.

## Glossary

- **MedAssist_System**: The existing medical document analysis web application
- **Chat_History**: An array of previous messages and responses maintained during a conversation session
- **Conversation_Memory**: The system's ability to reference and build upon previous exchanges in a chat session
- **Frontend_Session**: Client-side state management maintaining user data during active application use
- **Chat_Endpoint**: The backend API endpoint (/chat) that processes user questions and returns AI responses
- **Gemini**: The Google Gemini AI model used for generating responses and extracting insights
- **Dashboard**: The main interface displaying health insights from analyzed documents
- **Key_Medical_Insights**: Structured health metrics extracted from documents (hemoglobin, glucose, etc.)
- **Health_Metric**: A specific measurable health indicator with label and value
- **Abnormal_Flag**: An indicator that a health metric falls outside normal ranges
- **Role**: User profile type (Doctor, Patient, ASHA_Worker) determining response style
- **Response_Style**: The language complexity, terminology, and focus adapted for each role
- **Document_Preview**: The current UI component showing raw extracted document text
- **Stat_Card**: A visual component displaying a specific health metric or insight
- **Backend_Prompt**: The instruction text sent to Gemini that controls response generation behavior
- **Extraction_Lambda**: The Lambda function that processes documents with Textract
- **Chat_Lambda**: The Lambda function that handles chat requests and AI response generation
- **Dashboard_Lambda**: The Lambda function that generates dashboard data and insights

## Requirements

### Requirement 1: Conversation Memory Storage

**User Story:** As a User, I want the system to remember our conversation, so that I don't have to repeat context and can have natural follow-up discussions.

#### Acceptance Criteria

1. WHEN a User starts a new chat session, THE MedAssist_System SHALL initialize an empty Chat_History array in the Frontend_Session
2. WHEN a User submits a message, THE MedAssist_System SHALL append the message to the Chat_History array with a timestamp
3. WHEN the AI generates a response, THE MedAssist_System SHALL append the response to the Chat_History array with a timestamp
4. WHILE a Frontend_Session is active, THE MedAssist_System SHALL maintain the Chat_History array in browser memory
5. THE MedAssist_System SHALL structure each Chat_History entry with fields for role (user or assistant), content, and timestamp

### Requirement 2: Conversation Context Transmission

**User Story:** As a User, I want the AI to consider previous messages when answering, so that responses are contextually relevant to our ongoing conversation.

#### Acceptance Criteria

1. WHEN a User submits a question to the Chat_Endpoint, THE MedAssist_System SHALL include the complete Chat_History array in the request payload
2. WHEN the Chat_Lambda receives a request, THE MedAssist_System SHALL extract the Chat_History from the request payload
3. WHEN constructing a prompt for Gemini, THE MedAssist_System SHALL include previous messages from Chat_History as conversation context
4. THE MedAssist_System SHALL format Chat_History messages in chronological order when building the Gemini prompt
5. THE MedAssist_System SHALL include the most recent 10 messages from Chat_History in the Gemini prompt to maintain context while managing token limits

### Requirement 3: Contextual Response Generation

**User Story:** As a User, I want AI responses that reference previous conversation points, so that I can ask follow-up questions naturally without repeating information.

#### Acceptance Criteria

1. WHEN Gemini generates a response, THE MedAssist_System SHALL base the response on both the current question and Chat_History context
2. WHEN a User asks a follow-up question using pronouns or references, THE MedAssist_System SHALL resolve the references using Chat_History
3. WHEN a User asks "what about that medication", THE MedAssist_System SHALL identify the medication from previous Chat_History messages
4. THE MedAssist_System SHALL generate responses that acknowledge previous conversation points when relevant
5. IF Chat_History contains contradictory information, THEN THE MedAssist_System SHALL prioritize the most recent context

### Requirement 4: Updated Chat History Return

**User Story:** As a User, I want the system to maintain conversation state consistently, so that my chat history stays synchronized between frontend and backend.

#### Acceptance Criteria

1. WHEN the Chat_Lambda generates a response, THE MedAssist_System SHALL return the updated Chat_History array in the response payload
2. WHEN the frontend receives a chat response, THE MedAssist_System SHALL update the Frontend_Session Chat_History with the returned array
3. THE MedAssist_System SHALL include both the user message and AI response in the returned Chat_History
4. THE MedAssist_System SHALL preserve message ordering and timestamps in the returned Chat_History
5. IF the backend modifies Chat_History (such as truncating old messages), THEN THE MedAssist_System SHALL reflect those changes in the returned array

### Requirement 5: Structured Health Metrics Extraction

**User Story:** As a User, I want to see my health metrics in a clear, organized format, so that I can quickly understand my test results without reading raw document text.

#### Acceptance Criteria

1. WHEN documents are processed, THE Dashboard_Lambda SHALL use Gemini to extract Health_Metric instances from document text
2. THE MedAssist_System SHALL extract hemoglobin values as Health_Metric instances when present in documents
3. THE MedAssist_System SHALL extract white blood cell count values as Health_Metric instances when present in documents
4. THE MedAssist_System SHALL extract platelet count values as Health_Metric instances when present in documents
5. THE MedAssist_System SHALL extract glucose values as Health_Metric instances when present in documents
6. THE MedAssist_System SHALL extract cholesterol values as Health_Metric instances when present in documents
7. THE MedAssist_System SHALL identify Abnormal_Flag indicators for metrics outside normal ranges
8. THE MedAssist_System SHALL structure each Health_Metric with fields for metric name, value, unit, and abnormal status

### Requirement 6: Key Medical Insights Display

**User Story:** As a User, I want to see extracted health metrics in labeled cards, so that I can understand my results at a glance without parsing raw text.

#### Acceptance Criteria

1. THE MedAssist_System SHALL replace the Document_Preview component with a Key_Medical_Insights component in the Dashboard
2. WHEN Health_Metric instances are extracted, THE MedAssist_System SHALL display each metric in a labeled Stat_Card
3. THE MedAssist_System SHALL display the metric name as the Stat_Card label
4. THE MedAssist_System SHALL display the metric value and unit as the Stat_Card content
5. WHERE a Health_Metric has an Abnormal_Flag, THE MedAssist_System SHALL highlight the Stat_Card with a visual indicator
6. THE MedAssist_System SHALL organize Stat_Card components in a grid layout within the Key_Medical_Insights component
7. IF no Health_Metric instances are extracted, THEN THE MedAssist_System SHALL display a message indicating no structured metrics were found

### Requirement 7: Gemini-Based Metric Extraction

**User Story:** As a developer, I want to use Gemini for extracting structured health data, so that the system leverages existing AI capabilities without adding new dependencies.

#### Acceptance Criteria

1. WHEN the Dashboard_Lambda processes document text, THE MedAssist_System SHALL construct a prompt instructing Gemini to extract Health_Metric instances
2. THE MedAssist_System SHALL request Gemini to return Health_Metric data in JSON format
3. THE MedAssist_System SHALL specify in the prompt which Health_Metric types to extract (hemoglobin, WBC, platelets, glucose, cholesterol)
4. THE MedAssist_System SHALL instruct Gemini to identify Abnormal_Flag indicators based on standard medical reference ranges
5. WHEN Gemini returns extracted metrics, THE MedAssist_System SHALL parse the JSON response into Health_Metric objects
6. IF Gemini fails to extract structured data, THEN THE MedAssist_System SHALL log the error and display a fallback message

### Requirement 8: Role-Based Prompt Adaptation

**User Story:** As a User, I want AI responses tailored to my role, so that explanations match my medical knowledge level and information needs.

#### Acceptance Criteria

1. WHEN constructing a Backend_Prompt for Gemini, THE MedAssist_System SHALL include the selected Role in the prompt context
2. WHERE the Role is Patient, THE MedAssist_System SHALL instruct Gemini to use simple language suitable for general users
3. WHERE the Role is Doctor, THE MedAssist_System SHALL instruct Gemini to use clinical medical terminology and technical explanations
4. WHERE the Role is ASHA_Worker, THE MedAssist_System SHALL instruct Gemini to focus on community healthcare guidance for rural health workers
5. THE MedAssist_System SHALL include role-specific instruction text in the Backend_Prompt system message
6. WHEN a User switches roles, THE MedAssist_System SHALL regenerate responses using the new role-specific Backend_Prompt

### Requirement 9: Patient Role Response Style

**User Story:** As a Patient, I want explanations in simple language, so that I can understand my health information without medical training.

#### Acceptance Criteria

1. WHERE the Role is Patient, THE MedAssist_System SHALL generate responses avoiding technical medical jargon
2. WHERE the Role is Patient, THE MedAssist_System SHALL explain medical terms using everyday language
3. WHERE the Role is Patient, THE MedAssist_System SHALL focus on practical health implications and actionable advice
4. WHERE the Role is Patient, THE MedAssist_System SHALL use analogies and examples to clarify complex concepts
5. WHERE the Role is Patient, THE MedAssist_System SHALL structure responses with clear sections for understanding and next steps

### Requirement 10: Doctor Role Response Style

**User Story:** As a Doctor, I want clinical explanations with medical terminology, so that I receive professional-level information for patient care decisions.

#### Acceptance Criteria

1. WHERE the Role is Doctor, THE MedAssist_System SHALL generate responses using standard clinical medical terminology
2. WHERE the Role is Doctor, THE MedAssist_System SHALL include relevant diagnostic considerations and differential diagnoses
3. WHERE the Role is Doctor, THE MedAssist_System SHALL reference clinical guidelines and evidence-based practices
4. WHERE the Role is Doctor, THE MedAssist_System SHALL provide detailed pathophysiology explanations when relevant
5. WHERE the Role is Doctor, THE MedAssist_System SHALL structure responses with clinical assessment and management recommendations

### Requirement 11: ASHA Worker Role Response Style

**User Story:** As an ASHA_Worker, I want community health guidance, so that I can provide appropriate support and referrals in rural healthcare settings.

#### Acceptance Criteria

1. WHERE the Role is ASHA_Worker, THE MedAssist_System SHALL generate responses focused on community health education
2. WHERE the Role is ASHA_Worker, THE MedAssist_System SHALL emphasize when to refer patients to medical facilities
3. WHERE the Role is ASHA_Worker, THE MedAssist_System SHALL include preventive health guidance suitable for community outreach
4. WHERE the Role is ASHA_Worker, THE MedAssist_System SHALL use language accessible to health workers without formal medical degrees
5. WHERE the Role is ASHA_Worker, THE MedAssist_System SHALL provide practical advice for resource-limited settings

### Requirement 12: Document Processing Status UI Fix

**User Story:** As a User, I want accurate status messages, so that I understand when my documents are ready for analysis.

#### Acceptance Criteria

1. WHEN documents_uploaded count is greater than zero, THE MedAssist_System SHALL remove the "Document not processed yet" message
2. WHEN documents_uploaded count is greater than zero, THE MedAssist_System SHALL display the Key_Medical_Insights component
3. WHEN documents_uploaded count is zero, THE MedAssist_System SHALL display a message prompting the User to upload documents
4. THE MedAssist_System SHALL update the documents_uploaded count immediately after successful document processing
5. THE MedAssist_System SHALL display processing status feedback while documents are being analyzed

### Requirement 13: Backward Compatibility

**User Story:** As a developer, I want enhancements to integrate seamlessly, so that existing functionality continues working without disruption.

#### Acceptance Criteria

1. THE MedAssist_System SHALL maintain the existing upload to dashboard to chat workflow
2. THE MedAssist_System SHALL preserve the existing API Gateway endpoint structure
3. THE MedAssist_System SHALL maintain compatibility with existing Lambda function signatures
4. THE MedAssist_System SHALL preserve existing DynamoDB schema and data structures
5. THE MedAssist_System SHALL maintain existing Textract document processing pipeline
6. THE MedAssist_System SHALL continue using Gemini as the AI model without switching providers

### Requirement 14: Chat History Persistence Scope

**User Story:** As a User, I want conversation memory during my session, so that I can have continuous discussions while using the application.

#### Acceptance Criteria

1. WHILE a Frontend_Session is active, THE MedAssist_System SHALL maintain Chat_History in browser memory
2. WHEN a User refreshes the browser page, THE MedAssist_System SHALL clear the Chat_History
3. WHEN a User closes the browser tab, THE MedAssist_System SHALL clear the Chat_History
4. THE MedAssist_System SHALL not persist Chat_History to backend storage or databases
5. THE MedAssist_System SHALL initialize a new empty Chat_History when a new Frontend_Session starts

### Requirement 15: Performance Optimization

**User Story:** As a User, I want fast responses, so that conversations feel natural and dashboard loads quickly.

#### Acceptance Criteria

1. WHEN including Chat_History in requests, THE MedAssist_System SHALL limit history to the most recent 10 messages to manage payload size
2. WHEN extracting Health_Metric instances, THE MedAssist_System SHALL complete processing within 3 seconds
3. WHEN generating role-based responses, THE MedAssist_System SHALL return responses within 5 seconds
4. THE MedAssist_System SHALL cache extracted Health_Metric instances to avoid re-extraction on dashboard refresh
5. THE MedAssist_System SHALL optimize Gemini prompts to minimize token usage while maintaining response quality

### Requirement 16: Error Handling for Conversation Memory

**User Story:** As a User, I want graceful error handling, so that conversation issues don't break the application.

#### Acceptance Criteria

1. IF Chat_History transmission fails, THEN THE MedAssist_System SHALL process the current question without historical context
2. IF Chat_History parsing fails in the backend, THEN THE MedAssist_System SHALL log the error and proceed with the current question only
3. IF Chat_History exceeds maximum size limits, THEN THE MedAssist_System SHALL truncate to the most recent messages
4. IF the frontend fails to update Chat_History, THEN THE MedAssist_System SHALL display an error message and allow retry
5. THE MedAssist_System SHALL continue functioning even when Conversation_Memory features encounter errors

### Requirement 17: Error Handling for Structured Insights

**User Story:** As a User, I want to see available information even when extraction partially fails, so that I can still benefit from successfully extracted metrics.

#### Acceptance Criteria

1. IF Gemini fails to extract any Health_Metric instances, THEN THE MedAssist_System SHALL display a message indicating no structured metrics were found
2. IF Gemini extracts some but not all Health_Metric instances, THEN THE MedAssist_System SHALL display the successfully extracted metrics
3. IF JSON parsing of extracted metrics fails, THEN THE MedAssist_System SHALL log the error and display a fallback message
4. IF Abnormal_Flag detection fails for a metric, THEN THE MedAssist_System SHALL display the metric without the abnormal indicator
5. THE MedAssist_System SHALL log all extraction errors to CloudWatch for debugging

### Requirement 18: Testing and Validation

**User Story:** As a developer, I want to verify enhancements work correctly, so that users receive reliable and accurate information.

#### Acceptance Criteria

1. THE MedAssist_System SHALL validate that Chat_History maintains correct message ordering
2. THE MedAssist_System SHALL validate that role-based responses differ appropriately between Patient, Doctor, and ASHA_Worker roles
3. THE MedAssist_System SHALL validate that Health_Metric extraction correctly identifies values and units
4. THE MedAssist_System SHALL validate that Abnormal_Flag indicators match standard medical reference ranges
5. THE MedAssist_System SHALL validate that conversation context correctly resolves pronoun references
6. THE MedAssist_System SHALL validate that the existing upload and processing pipeline continues functioning after enhancements

