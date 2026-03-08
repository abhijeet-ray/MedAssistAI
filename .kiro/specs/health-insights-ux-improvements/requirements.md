# Requirements Document: Health Insights UX Improvements

## Introduction

The Health Insights Dashboard and Chat output in the MedAssist AI system require significant UX improvements to provide users with more actionable medical insights. Currently, the dashboard displays only document and word counts, while chat responses are unstructured paragraphs that may contain repetitive information. This feature improves both components by extracting and displaying key medical metrics with reference ranges, structuring chat responses into digestible sections, and implementing context management to reduce repetition. All improvements maintain the system's lightweight architecture using existing dependencies and the Nova Lite model.

## Glossary

- **Health_Metrics**: Quantifiable medical parameters extracted from health documents (e.g., Hemoglobin, WBC, Platelets, Blood Glucose, Cholesterol, Thyroid levels)
- **Reference_Range**: The normal or expected range for a health metric, typically defined by medical standards
- **Status_Indicator**: A visual or textual representation (e.g., Normal, Low, High, Critical) indicating whether a metric falls within, above, or below its reference range
- **Dashboard**: The frontend component displaying aggregated health information and metrics
- **Chat_Response**: Structured output from the AI model in response to user queries
- **Context_Window**: The set of previous messages (up to 3) maintained to inform current AI responses
- **Medical_Document**: A health-related document (lab results, reports, etc.) uploaded by the user
- **Text_Parser**: A lightweight component that extracts health metrics from unstructured document text
- **API_Contract**: The interface specification between frontend and backend services
- **Nova_Lite_Model**: Amazon Bedrock's lightweight AI model used for generating responses
- **Repetition_Detection**: Logic to identify and prevent duplicate information in consecutive chat messages

## Requirements

### Requirement 1: Extract Health Metrics from Medical Documents

**User Story:** As a user, I want the dashboard to automatically extract and display key medical metrics from my uploaded documents, so that I can quickly see my important health parameters without manually searching through documents.

#### Acceptance Criteria

1. WHEN a medical document is uploaded, THE Text_Parser SHALL extract the following health metrics if present: Hemoglobin, WBC (White Blood Cell count), Platelets, Blood Glucose, Cholesterol, and Thyroid levels
2. WHEN a health metric is extracted, THE Text_Parser SHALL identify and store its corresponding Reference_Range from the document or use standard medical reference ranges
3. WHEN a health metric is extracted, THE Dashboard SHALL display the metric name, value, unit, and Reference_Range
4. IF a health metric value falls outside its Reference_Range, THEN THE Dashboard SHALL assign a Status_Indicator (Low, Normal, High, or Critical) based on the deviation
5. WHEN multiple documents are uploaded, THE Dashboard SHALL aggregate and display the most recent value for each health metric
6. THE Text_Parser SHALL use only existing dependencies and simple regex-based pattern matching, without introducing new libraries

### Requirement 2: Display Health Metrics with Visual Status Indicators

**User Story:** As a user, I want to see visual indicators for my health metrics, so that I can quickly identify which metrics are concerning and need attention.

#### Acceptance Criteria

1. THE Dashboard SHALL display each health metric with a Status_Indicator color or icon (e.g., green for Normal, yellow for Low/High, red for Critical)
2. WHEN a metric Status_Indicator is displayed, THE Dashboard SHALL also show the metric value, unit, and Reference_Range in a clear, scannable format
3. THE Dashboard SHALL organize metrics into logical groups (e.g., Blood Work, Metabolic Panel, Thyroid Function)
4. WHILE the Dashboard is rendering metrics, THE Dashboard SHALL maintain responsive performance with no perceptible lag (< 100ms render time)
5. WHERE a health metric cannot be extracted from documents, THE Dashboard SHALL not display that metric rather than showing placeholder or error states

### Requirement 3: Structure Chat Responses into Formatted Sections

**User Story:** As a user, I want AI chat responses to be structured and easy to scan, so that I can quickly understand the key findings and recommended actions without reading long paragraphs.

#### Acceptance Criteria

1. WHEN the Chat_Response is generated, THE Nova_Lite_Model SHALL structure the response into exactly four sections: Summary, Important_Findings, What_It_Means, and Suggested_Action
2. THE Summary section SHALL contain a brief overview (1-2 sentences) of the response
3. THE Important_Findings section SHALL present findings as a bullet list with 3-7 items, each item being a concise statement
4. THE What_It_Means section SHALL explain the clinical significance of the findings in 2-3 sentences
5. THE Suggested_Action section SHALL provide 1-3 actionable recommendations for the user
6. THE Chat_Response formatter SHALL validate that all four sections are present before displaying the response to the user
7. IF a Chat_Response section is missing or malformed, THEN THE Chat_Response formatter SHALL return an error and request regeneration

### Requirement 4: Implement Context Management to Reduce Repetition

**User Story:** As a user, I want the AI to remember my recent questions and avoid repeating information, so that conversations feel more natural and efficient.

#### Acceptance Criteria

1. WHEN a user sends a chat message, THE Chat_Service SHALL maintain a Context_Window containing the last 3 messages (user and AI responses)
2. WHEN generating a new Chat_Response, THE Nova_Lite_Model SHALL receive the Context_Window as part of the prompt to inform response generation
3. WHEN a new Chat_Response is generated, THE Repetition_Detection logic SHALL compare the response against the previous message to identify duplicate or near-duplicate content
4. IF the Repetition_Detection logic identifies significant overlap (> 50% semantic similarity) with the previous message, THEN THE Chat_Service SHALL request a regenerated response from the Nova_Lite_Model
5. THE Context_Window SHALL be cleared when a user starts a new conversation or explicitly requests a reset
6. THE Context_Window data SHALL not be persisted across user sessions; it SHALL only exist in memory during active conversations

### Requirement 5: Update Dashboard API Contract

**User Story:** As a backend developer, I want the Dashboard API to return structured health metrics data, so that the frontend can display metrics with status indicators without additional processing.

#### Acceptance Criteria

1. WHEN the Dashboard API is called, THE API SHALL return a response containing an array of extracted health metrics
2. EACH health metric object in the response SHALL include: metric_name, value, unit, reference_range_min, reference_range_max, status_indicator, and extraction_timestamp
3. THE API SHALL return metrics grouped by category (e.g., "Blood_Work", "Metabolic_Panel", "Thyroid_Function")
4. WHEN no health metrics are found in documents, THE API SHALL return an empty metrics array rather than an error
5. THE API response time SHALL not exceed 500ms for documents up to 10 pages in length
6. THE API SHALL maintain backward compatibility by continuing to return document_count and word_count in the response

### Requirement 6: Update Chat API Contract

**User Story:** As a backend developer, I want the Chat API to return structured responses with defined sections, so that the frontend can reliably parse and display chat output.

#### Acceptance Criteria

1. WHEN the Chat API is called, THE API SHALL return a response containing a structured Chat_Response object
2. THE Chat_Response object SHALL include four fields: summary, important_findings (array), what_it_means, and suggested_action
3. WHEN the Chat_Response is generated, THE API SHALL include the Context_Window (last 3 messages) in the request to the Nova_Lite_Model
4. THE API response time SHALL not exceed 3 seconds for typical queries
5. IF the Nova_Lite_Model fails to generate a properly structured response, THEN THE API SHALL retry up to 2 times before returning an error
6. THE API SHALL validate the Chat_Response structure before returning it to the frontend

### Requirement 7: Implement Frontend Dashboard Component Updates

**User Story:** As a frontend developer, I want to update the Dashboard component to display health metrics with status indicators, so that users see a professional, scannable health overview.

#### Acceptance Criteria

1. THE Dashboard component SHALL render health metrics in a grid or card-based layout with clear visual hierarchy
2. EACH metric card SHALL display: metric name, value, unit, reference range, and status indicator (color/icon)
3. THE Dashboard component SHALL group metrics by category and display category headers
4. WHEN a user hovers over a metric, THE Dashboard component SHALL display a tooltip with additional context (e.g., clinical significance)
5. THE Dashboard component SHALL handle loading and error states gracefully
6. THE Dashboard component SHALL use only existing React/TypeScript patterns and dependencies

### Requirement 8: Implement Frontend Chat Component Updates

**User Story:** As a frontend developer, I want to update the Chat component to display structured responses, so that users see well-formatted, scannable AI responses.

#### Acceptance Criteria

1. THE Chat component SHALL render each Chat_Response section (Summary, Important_Findings, What_It_Means, Suggested_Action) with distinct visual styling
2. THE Important_Findings section SHALL render as a bullet list with consistent formatting
3. THE Chat component SHALL display the response sections in a vertical layout with clear section headers
4. WHEN a Chat_Response is received, THE Chat component SHALL validate the structure and display an error message if any section is missing
5. THE Chat component SHALL maintain conversation history and display previous messages in chronological order
6. THE Chat component SHALL use only existing React/TypeScript patterns and dependencies

### Requirement 9: Maintain Lightweight Architecture

**User Story:** As a system architect, I want to ensure all improvements use existing dependencies and the Nova Lite model, so that the system remains lightweight and cost-effective.

#### Acceptance Criteria

1. THE Text_Parser SHALL use only built-in JavaScript/Python string manipulation and regex, without introducing new npm or pip dependencies
2. THE Repetition_Detection logic SHALL use simple string similarity algorithms (e.g., Levenshtein distance or token overlap), without introducing new ML libraries
3. THE Context_Window management SHALL use in-memory data structures (arrays/lists), without introducing new caching libraries
4. ALL improvements SHALL use the existing Nova_Lite_Model without upgrading to a larger or more expensive model
5. THE total bundle size increase for frontend changes SHALL not exceed 50KB
6. THE Lambda function memory and execution time SHALL not increase by more than 20% compared to current baselines

### Requirement 10: Handle Edge Cases and Error Conditions

**User Story:** As a quality assurance engineer, I want the system to handle edge cases gracefully, so that users experience reliable functionality even with unusual inputs.

#### Acceptance Criteria

1. IF a medical document contains no recognizable health metrics, THEN THE Dashboard SHALL display a message indicating no metrics were found
2. IF a health metric value is malformed or unreadable, THEN THE Text_Parser SHALL skip that metric and continue processing other metrics
3. IF the Chat_Response structure is invalid, THEN THE Chat component SHALL display an error message and allow the user to request a regenerated response
4. WHEN the Context_Window is full (3 messages), THE Chat_Service SHALL remove the oldest message before adding a new one
5. IF the Nova_Lite_Model fails to generate a response, THEN THE Chat_Service SHALL return a user-friendly error message and suggest retrying
6. WHEN a user uploads a document in an unsupported format, THE Dashboard SHALL display a clear error message indicating the format is not supported

