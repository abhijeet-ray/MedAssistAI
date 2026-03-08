# Design Document: MedAssist Conversational Enhancements

## Overview

This design document specifies the technical implementation for adding conversation memory, structured health metrics extraction, role-based prompt adaptation, and UI refinements to the existing MedAssist AI system. The enhancements maintain backward compatibility with the current architecture (Frontend → API Gateway → Lambda → Textract → DynamoDB → Gemini) while improving user experience through contextual conversations and structured data presentation.

### Design Goals

1. **Conversation Memory**: Enable the system to maintain chat history during a user session, allowing natural follow-up questions without context repetition
2. **Structured Insights**: Replace raw document text display with extracted, labeled health metrics (hemoglobin, glucose, etc.)
3. **Role-Based Responses**: Adapt AI response style based on user role (Patient, Doctor, ASHA Worker)
4. **Backward Compatibility**: Preserve existing functionality and architecture without breaking changes

### Key Design Decisions

- **Frontend-Only Session Memory**: Chat history stored in browser memory (React state) rather than backend persistence, simplifying implementation and avoiding database schema changes
- **Gemini for Extraction**: Leverage existing Gemini integration for structured data extraction instead of adding new dependencies
- **Prompt Engineering**: Use role-specific system prompts to control response style without model switching
- **Incremental Enhancement**: Modify existing Lambda functions rather than creating new services

## Architecture

### System Context

The MedAssist system processes medical documents and provides AI-powered insights through a conversational interface. The existing architecture consists of:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│ API Gateway  │─────▶│   Lambda    │
│   (React)   │◀─────│              │◀─────│  Functions  │
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │  Textract   │
                                            └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │  DynamoDB   │
                                            └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │   Gemini    │
                                            │     AI      │
                                            └─────────────┘
```

### Enhanced Architecture

The conversational enhancements add new data flows without changing the core pipeline:

```mermaid
graph TB
    subgraph "Frontend (React)"
        UI[User Interface]
        ChatState[Chat History State]
        DashState[Dashboard State]
    end
    
    subgraph "API Gateway"
        ChatAPI[/chat endpoint]
        DashAPI[/dashboard endpoint]
    end
    
    subgraph "Lambda Functions"
        ChatLambda[Chat Lambda<br/>rag.py]
        DashLambda[Dashboard Lambda<br/>dashboard.py]
    end
    
    subgraph "Data Layer"
        DDB[(DynamoDB<br/>Documents)]
    end
    
    subgraph "AI Services"
        Gemini[Google Gemini API]
    end
    
    UI -->|User message + history| ChatState
    ChatState -->|POST /chat| ChatAPI
    ChatAPI --> ChatLambda
    ChatLambda -->|Query documents| DDB
    ChatLambda -->|Prompt with history + role| Gemini
    Gemini -->|Response| ChatLambda
    ChatLambda -->|Updated history| ChatAPI
    ChatAPI -->|Response + history| ChatState
    
    UI -->|Request insights| DashAPI
    DashAPI --> DashLambda
    DashLambda -->|Query documents| DDB
    DashLambda -->|Extract metrics prompt| Gemini
    Gemini -->|Structured JSON| DashLambda
    DashLambda -->|Stat cards| DashAPI
    DashAPI -->|Display metrics| DashState
```

### Component Responsibilities

**Frontend Components**:
- `ChatInterface`: Manages chat UI, maintains chat history in React state, sends history with each request
- `Dashboard`: Displays structured health metrics as stat cards instead of raw text
- `App`: Coordinates session state and role selection

**Backend Lambda Functions**:
- `rag.py` (Chat Lambda): Processes chat requests with conversation context and role-based prompts
- `dashboard.py` (Dashboard Lambda): Extracts structured health metrics using Gemini

**Data Storage**:
- DynamoDB: Stores processed document text (no schema changes required)
- Browser Memory: Stores chat history for session duration only

## Components and Interfaces

### Frontend Components

#### ChatInterface Component

**Purpose**: Manages conversational UI with memory support

**State Management**:
```typescript
interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

interface ChatHistoryEntry {
  user: string;
  ai: string;
}

// Component state
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [chatHistory, setChatHistory] = useState<ChatHistoryEntry[]>([]);
```

**Key Methods**:
- `handleSendMessage()`: Appends user message to history, sends request with full history, updates state with AI response
- `updateChatHistory()`: Synchronizes local history with backend-returned history
- `formatHistoryForDisplay()`: Renders conversation thread in UI

**API Integration**:
```typescript
// Request payload
{
  sessionId: string,
  message: string,
  role: 'patient' | 'doctor' | 'asha',
  chatHistory: ChatHistoryEntry[]  // NEW: conversation context
}

// Response payload
{
  answer: string,
  chatHistory: ChatHistoryEntry[],  // NEW: updated history
  source: string,
  timestamp: string
}
```

#### Dashboard Component

**Purpose**: Displays structured health metrics instead of raw document text

**Current Implementation** (to be modified):
- Shows "Document Preview" with raw extracted text
- Basic stat cards for document count and word count

**Enhanced Implementation**:
- Replaces "Document Preview" with "Key Medical Insights" component
- Displays extracted health metrics in labeled stat cards
- Shows abnormal flags with visual indicators

**Stat Card Structure**:
```typescript
interface StatCardData {
  title: string;           // e.g., "Hemoglobin"
  value: string;           // e.g., "13.5"
  unit: string;            // e.g., "g/dL"
  insight: string;         // Explanation text
  severity: 'normal' | 'warning' | 'critical';  // Visual indicator
}
```

### Backend Components

#### Chat Lambda (rag.py)

**Current Functionality**:
- Retrieves document text from DynamoDB
- Constructs prompt with role-based instructions
- Calls Gemini API for response generation

**Enhanced Functionality**:

1. **Chat History Processing**:
```python
def format_chat_history(chat_history: list) -> str:
    """
    Formats chat history for inclusion in Gemini prompt.
    Limits to last 10 exchanges to manage token count.
    """
    if not chat_history:
        return "No previous conversation."
    
    # Take last 10 exchanges
    recent_history = chat_history[-10:]
    
    formatted = []
    for entry in recent_history:
        user_msg = entry.get('user', '')
        ai_msg = entry.get('ai', '')
        formatted.append(f"User: {user_msg}\nAI: {ai_msg}")
    
    return "\n\n".join(formatted)
```

2. **Role-Based Prompt Construction**:
```python
def get_role_prompt_instructions(role: str) -> str:
    """
    Returns role-specific instructions for Gemini prompt.
    """
    instructions = {
        'patient': """
            - Use simple, everyday language
            - Avoid medical jargon
            - Explain terms in plain English
            - Focus on practical health implications
            - Provide actionable advice
            - Use analogies when helpful
        """,
        'doctor': """
            - Use clinical medical terminology
            - Include diagnostic considerations
            - Reference clinical guidelines
            - Provide detailed pathophysiology
            - Structure with assessment and management
        """,
        'asha': """
            - Focus on community health education
            - Emphasize when to refer to facilities
            - Include preventive health guidance
            - Use accessible language for health workers
            - Provide practical advice for resource-limited settings
        """
    }
    return instructions.get(role, instructions['patient'])
```

3. **Conversational Prompt Template**:
```python
prompt = f"""You are a medical AI assistant.

Medical report:
{document_text}

Conversation history:
{formatted_history}

User role: {role}
Response style: {role_instructions}

Current question: {question}

Instructions:
- Consider the conversation history when answering
- Do NOT repeat information already provided
- Answer the current question directly
- Reference previous context when relevant
- If using pronouns (it, that, etc.), resolve them from history
- Be concise and focused

Respond now:"""
```

4. **History Update Logic**:
```python
def update_chat_history(current_history: list, user_msg: str, ai_response: str) -> list:
    """
    Appends new exchange to history and maintains size limit.
    """
    updated = current_history.copy()
    updated.append({
        'user': user_msg,
        'ai': ai_response
    })
    
    # Keep only last 10 exchanges (20 messages total)
    if len(updated) > 10:
        updated = updated[-10:]
    
    return updated
```

**Modified Handler Flow**:
```python
def handler(event, context):
    # 1. Parse request (including chatHistory)
    body = json.loads(event['body'])
    session_id = body['sessionId']
    question = body['message']
    role = body.get('role', 'patient')
    chat_history = body.get('chatHistory', [])
    
    # 2. Retrieve document text
    document_text = get_document_text(session_id)
    
    # 3. Format chat history
    formatted_history = format_chat_history(chat_history)
    
    # 4. Get role-specific instructions
    role_instructions = get_role_prompt_instructions(role)
    
    # 5. Construct conversational prompt
    prompt = build_conversational_prompt(
        document_text, 
        formatted_history, 
        role, 
        role_instructions, 
        question
    )
    
    # 6. Call Gemini
    answer = call_gemini(prompt)
    
    # 7. Update chat history
    updated_history = update_chat_history(chat_history, question, answer)
    
    # 8. Return response with updated history
    return {
        'statusCode': 200,
        'body': json.dumps({
            'answer': answer,
            'chatHistory': updated_history,  # NEW
            'source': 'uploaded_document',
            'timestamp': datetime.utcnow().isoformat()
        })
    }
```

#### Dashboard Lambda (dashboard.py)

**Current Functionality**:
- Retrieves documents from DynamoDB
- Generates basic stat cards (document count, word count, preview)

**Enhanced Functionality**:

1. **Structured Extraction Prompt**:
```python
def create_extraction_prompt(document_text: str) -> str:
    """
    Creates prompt for Gemini to extract structured health metrics.
    """
    return f"""Extract health metrics from this medical report.

Medical Report:
{document_text}

Return ONLY a valid JSON object with this structure:
{{
  "hemoglobin": {{"value": "13.5", "unit": "g/dL", "abnormal": false}},
  "wbc": {{"value": "7500", "unit": "cells/μL", "abnormal": false}},
  "platelets": {{"value": "250000", "unit": "cells/μL", "abnormal": false}},
  "glucose": {{"value": "95", "unit": "mg/dL", "abnormal": false}},
  "cholesterol": {{"value": "180", "unit": "mg/dL", "abnormal": false}},
  "key_findings": ["finding 1", "finding 2"],
  "abnormal_flags": ["any abnormal results"]
}}

Use null for missing values. Mark abnormal=true if outside normal ranges:
- Hemoglobin: 12-16 g/dL (female), 14-18 g/dL (male)
- WBC: 4000-11000 cells/μL
- Platelets: 150000-400000 cells/μL
- Glucose (fasting): 70-100 mg/dL
- Cholesterol: <200 mg/dL

Return ONLY the JSON, no additional text."""
```

2. **JSON Parsing and Validation**:
```python
def parse_gemini_extraction(response: str) -> dict:
    """
    Parses Gemini response and validates structure.
    """
    try:
        # Remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # Parse JSON
        data = json.loads(cleaned)
        
        # Validate structure
        expected_keys = ['hemoglobin', 'wbc', 'platelets', 'glucose', 'cholesterol']
        for key in expected_keys:
            if key not in data:
                data[key] = None
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        return None
```

3. **Stat Card Generation**:
```python
def generate_stat_cards(extracted_data: dict) -> list:
    """
    Converts extracted metrics to stat card format.
    """
    cards = []
    
    # Hemoglobin card
    if extracted_data.get('hemoglobin'):
        hb = extracted_data['hemoglobin']
        cards.append({
            'title': 'Hemoglobin',
            'value': hb['value'],
            'unit': hb['unit'],
            'insight': 'Hemoglobin carries oxygen in your blood.',
            'severity': 'warning' if hb.get('abnormal') else 'normal'
        })
    
    # WBC card
    if extracted_data.get('wbc'):
        wbc = extracted_data['wbc']
        cards.append({
            'title': 'White Blood Cells',
            'value': wbc['value'],
            'unit': wbc['unit'],
            'insight': 'WBC count indicates immune system health.',
            'severity': 'warning' if wbc.get('abnormal') else 'normal'
        })
    
    # Similar for other metrics...
    
    # Key Medical Insights card (replaces Document Preview)
    if extracted_data.get('key_findings'):
        findings_text = '\n'.join([f'• {f}' for f in extracted_data['key_findings']])
        cards.append({
            'title': 'Key Medical Insights',
            'value': 'Available',
            'unit': '',
            'insight': findings_text,
            'severity': 'warning' if extracted_data.get('abnormal_flags') else 'normal'
        })
    
    return cards
```

4. **Error Handling**:
```python
def extract_metrics_with_fallback(document_text: str) -> list:
    """
    Attempts structured extraction, falls back to basic insights on failure.
    """
    try:
        # Try Gemini extraction
        prompt = create_extraction_prompt(document_text)
        response = call_gemini(prompt)
        
        if response:
            extracted = parse_gemini_extraction(response)
            if extracted:
                return generate_stat_cards(extracted)
        
        # Fallback to basic insights
        print("Structured extraction failed, using fallback")
        return generate_basic_stat_cards(document_text)
        
    except Exception as e:
        print(f"Extraction error: {e}")
        return generate_basic_stat_cards(document_text)

def generate_basic_stat_cards(document_text: str) -> list:
    """
    Fallback: generates basic cards when extraction fails.
    """
    word_count = len(document_text.split())
    return [{
        'title': 'Document Processed',
        'value': str(word_count),
        'unit': 'words',
        'insight': 'Document text available for analysis.',
        'severity': 'normal'
    }]
```

### API Contracts

#### POST /chat

**Request**:
```json
{
  "sessionId": "uuid-v4-string",
  "message": "What is my hemoglobin level?",
  "role": "patient",
  "chatHistory": [
    {
      "user": "What tests were done?",
      "ai": "Your report shows a complete blood count (CBC) test..."
    }
  ]
}
```

**Response**:
```json
{
  "answer": "Your hemoglobin level is 13.5 g/dL, which is within the normal range...",
  "chatHistory": [
    {
      "user": "What tests were done?",
      "ai": "Your report shows a complete blood count (CBC) test..."
    },
    {
      "user": "What is my hemoglobin level?",
      "ai": "Your hemoglobin level is 13.5 g/dL, which is within the normal range..."
    }
  ],
  "source": "uploaded_document",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Error Response**:
```json
{
  "error": "Failed to process chat request",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET /dashboard

**Request**:
```
GET /dashboard?sessionId=uuid-v4-string&role=patient
```

**Response**:
```json
{
  "statCards": [
    {
      "title": "Hemoglobin",
      "value": "13.5",
      "unit": "g/dL",
      "insight": "Hemoglobin carries oxygen in your blood.",
      "severity": "normal"
    },
    {
      "title": "Key Medical Insights",
      "value": "Available",
      "unit": "",
      "insight": "• Complete blood count within normal limits\n• No abnormal findings detected",
      "severity": "normal"
    }
  ],
  "documents": 2,
  "status": "processed",
  "lastUpdated": "2024-01-15T10:30:00Z"
}
```

## Data Models

### Chat History Entry

**Purpose**: Represents a single question-answer exchange in the conversation

**Structure**:
```typescript
interface ChatHistoryEntry {
  user: string;    // User's question
  ai: string;      // AI's response
}
```

**Storage**: Frontend React state only (not persisted to backend)

**Lifecycle**:
- Created when AI responds to user message
- Maintained in browser memory during session
- Cleared on page refresh or tab close
- Limited to last 10 exchanges (20 messages total)

### Chat Message (UI Display)

**Purpose**: Represents a message in the chat UI with metadata

**Structure**:
```typescript
interface ChatMessage {
  id: string;              // Unique identifier for React key
  sender: 'user' | 'ai';   // Message source
  content: string;         // Message text
  timestamp: Date;         // When message was sent/received
}
```

**Storage**: Frontend React state for UI rendering

**Relationship**: Multiple ChatMessage objects are derived from ChatHistoryEntry for display purposes

### Stat Card Data

**Purpose**: Represents a structured health metric for dashboard display

**Structure**:
```typescript
interface StatCardData {
  title: string;      // Metric name (e.g., "Hemoglobin")
  value: string;      // Numeric value (e.g., "13.5")
  unit: string;       // Unit of measurement (e.g., "g/dL")
  insight: string;    // Explanatory text
  severity: 'normal' | 'warning' | 'critical';  // Visual indicator
}
```

**Storage**: 
- Generated by Dashboard Lambda from DynamoDB document text
- Cached in frontend React state during session
- Not persisted to database

### Health Metric (Extracted Data)

**Purpose**: Intermediate structure for Gemini extraction results

**Structure**:
```python
{
  "hemoglobin": {
    "value": "13.5",
    "unit": "g/dL",
    "abnormal": false
  },
  "wbc": {
    "value": "7500",
    "unit": "cells/μL",
    "abnormal": false
  },
  "platelets": {
    "value": "250000",
    "unit": "cells/μL",
    "abnormal": false
  },
  "glucose": {
    "value": "95",
    "unit": "mg/dL",
    "abnormal": false
  },
  "cholesterol": {
    "value": "180",
    "unit": "mg/dL",
    "abnormal": false
  },
  "key_findings": ["finding 1", "finding 2"],
  "abnormal_flags": ["any abnormal results"]
}
```

**Usage**: Parsed from Gemini JSON response, transformed into StatCardData for frontend

### DynamoDB Document Schema (Unchanged)

**Purpose**: Stores processed medical documents

**Existing Structure**:
```python
{
  "PK": "session-id",           # Partition key
  "SK": "document-id",          # Sort key
  "documentText": "...",        # Extracted text from Textract
  "timestamp": "2024-01-15...", # Upload timestamp
  "status": "processed"         # Processing status
}
```

**No Changes Required**: Conversation memory and structured extraction do not require schema modifications


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies and consolidations:

**Redundancy Analysis**:
- Requirements 5.2-5.6 (extracting specific metrics) can be combined into a single property about metric extraction
- Requirements 6.3-6.4 (stat card label and content) can be combined into one property about card structure
- Requirements 1.2 and 1.3 (appending user/AI messages) can be combined into one property about message appending
- Requirements 2.1 and 2.3 (including history in request and prompt) are related but test different layers
- Requirements 8.2-8.4 (role-specific prompts) are examples that don't need separate properties

**Consolidated Properties**:
The following properties provide comprehensive coverage without redundancy:

### Property 1: Chat History Message Appending

*For any* user message or AI response, when added to the chat history, the system should append it with a timestamp and appropriate role designation (user or assistant).

**Validates: Requirements 1.2, 1.3, 1.5**

### Property 2: Chat History Structure Validation

*For any* chat history entry, it must contain the required fields: role (user or assistant), content (non-empty string), and timestamp (valid date).

**Validates: Requirements 1.5**

### Property 3: Chat History Persistence During Session

*For any* sequence of chat interactions during an active frontend session, the chat history should remain accessible and unchanged until the session ends (page refresh or tab close).

**Validates: Requirements 1.4, 14.1**

### Property 4: Chat History Transmission

*For any* chat request sent to the backend, the request payload must include the complete current chat history array.

**Validates: Requirements 2.1**

### Property 5: Chat History Extraction in Backend

*For any* valid chat request received by the Chat Lambda, the system should successfully extract the chat history array from the request payload.

**Validates: Requirements 2.2**

### Property 6: Chat History Inclusion in Prompts

*For any* Gemini prompt constructed by the Chat Lambda, if chat history exists, it must be included in the prompt as conversation context.

**Validates: Requirements 2.3**

### Property 7: Chat History Chronological Ordering

*For any* chat history formatted for the Gemini prompt, messages must appear in chronological order (oldest to newest).

**Validates: Requirements 2.4**

### Property 8: Chat History Size Limiting

*For any* chat history with more than 10 exchanges, only the most recent 10 exchanges should be included in the Gemini prompt.

**Validates: Requirements 2.5, 15.1**

### Property 9: Chat Response History Update

*For any* successful chat response from the backend, the response payload must include an updated chat history array containing both the user's question and the AI's answer.

**Validates: Requirements 4.1, 4.3**

### Property 10: Frontend History Synchronization

*For any* chat response received by the frontend, the local chat history state should be updated to match the backend-returned history array.

**Validates: Requirements 4.2**

### Property 11: History Ordering and Timestamp Preservation

*For any* chat history returned from the backend, message ordering and timestamps must be preserved from the original history.

**Validates: Requirements 4.4**

### Property 12: Backend History Modification Reflection

*For any* chat history modified by the backend (such as truncation), the returned history array should reflect those modifications.

**Validates: Requirements 4.5**

### Property 13: Health Metric Extraction Invocation

*For any* document processing request to the Dashboard Lambda, the system should construct and send an extraction prompt to Gemini.

**Validates: Requirements 5.1, 7.1**

### Property 14: Comprehensive Metric Extraction

*For any* medical document containing health metrics (hemoglobin, WBC, platelets, glucose, cholesterol), the system should attempt to extract all present metrics.

**Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6**

### Property 15: Abnormal Flag Detection

*For any* extracted health metric with a value outside standard reference ranges, the system should set the abnormal flag to true.

**Validates: Requirements 5.7**

### Property 16: Health Metric Structure Validation

*For any* extracted health metric, it must contain the required fields: metric name, value, unit, and abnormal status.

**Validates: Requirements 5.8**

### Property 17: Stat Card Generation from Metrics

*For any* successfully extracted health metric, the system should generate a corresponding stat card for display.

**Validates: Requirements 6.2**

### Property 18: Stat Card Content Mapping

*For any* stat card generated from a health metric, the card's title should match the metric name, and the card's content should display the metric value and unit.

**Validates: Requirements 6.3, 6.4**

### Property 19: Abnormal Metric Visual Indication

*For any* stat card representing a health metric with an abnormal flag, the card should have a severity level of 'warning' or 'critical' to trigger visual highlighting.

**Validates: Requirements 6.5**

### Property 20: JSON Format Request in Extraction Prompt

*For any* extraction prompt sent to Gemini, the prompt must explicitly request JSON-formatted output.

**Validates: Requirements 7.2**

### Property 21: Metric Types Specification in Prompt

*For any* extraction prompt, it must specify the health metric types to extract: hemoglobin, WBC, platelets, glucose, and cholesterol.

**Validates: Requirements 7.3**

### Property 22: Reference Ranges in Extraction Prompt

*For any* extraction prompt, it must include standard medical reference ranges for abnormal flag detection.

**Validates: Requirements 7.4**

### Property 23: JSON Response Parsing

*For any* valid JSON response from Gemini containing health metrics, the system should successfully parse it into health metric objects.

**Validates: Requirements 7.5**

### Property 24: Role Inclusion in Chat Prompt

*For any* chat prompt constructed for Gemini, the selected user role (patient, doctor, or asha) must be included in the prompt context.

**Validates: Requirements 8.1**

### Property 25: Role-Specific Instructions in Prompt

*For any* chat prompt, it must include role-specific instruction text appropriate for the selected role.

**Validates: Requirements 8.5**

### Property 26: Role Change Triggers New Prompt

*For any* role change event, subsequent chat requests should use a prompt with the new role's specific instructions.

**Validates: Requirements 8.6**

### Property 27: Document Count Conditional Rendering

*For any* dashboard state where documents_uploaded count is greater than zero, the "Document not processed yet" message should not be displayed, and the Key_Medical_Insights component should be visible.

**Validates: Requirements 12.1, 12.2**

### Property 28: Document Count Update After Processing

*For any* successful document processing event, the documents_uploaded count should be incremented immediately.

**Validates: Requirements 12.4**

### Property 29: Processing Status Display

*For any* document processing operation in progress, the system should display processing status feedback to the user.

**Validates: Requirements 12.5**

### Property 30: Metric Extraction Performance

*For any* health metric extraction request, the processing should complete within 3 seconds.

**Validates: Requirements 15.2**

### Property 31: Chat Response Performance

*For any* chat request, the system should return a response within 5 seconds.

**Validates: Requirements 15.3**

### Property 32: Dashboard Metric Caching

*For any* dashboard refresh during an active session, if metrics were previously extracted, they should be retrieved from cache rather than re-extracted.

**Validates: Requirements 15.4**

### Property 33: Extraction Error Logging

*For any* health metric extraction error, the system should log the error details to CloudWatch.

**Validates: Requirements 17.5**

## Error Handling

### Conversation Memory Error Handling

**Chat History Transmission Failures**:
- If chat history fails to transmit to the backend, the system processes the current question without historical context
- The user receives a response, but it may lack contextual awareness
- No error message is shown to the user (graceful degradation)

**Chat History Parsing Failures**:
- If the backend cannot parse the chat history from the request, it logs the error and proceeds with only the current question
- The conversation continues but without memory of previous exchanges
- CloudWatch logs capture parsing errors for debugging

**Chat History Size Limit Exceeded**:
- If chat history exceeds the maximum size (10 exchanges), the system automatically truncates to the most recent messages
- Truncation happens transparently without user notification
- The backend returns the truncated history to keep frontend and backend synchronized

**Frontend State Update Failures**:
- If the frontend fails to update chat history state, an error message is displayed
- The user can retry the message
- The conversation remains functional even if history synchronization fails

**Graceful Degradation**:
- The system continues functioning even when conversation memory features encounter errors
- Chat functionality works without history if necessary
- No conversation memory error should break the core chat capability

### Structured Insights Error Handling

**Complete Extraction Failure**:
- If Gemini fails to extract any health metrics, the dashboard displays: "No structured metrics were found in your documents"
- The system falls back to basic stat cards (document count, word count)
- Users can still use the chat interface to ask questions about their documents

**Partial Extraction Success**:
- If Gemini extracts some but not all metrics, the system displays the successfully extracted metrics
- Missing metrics are simply not shown (no error indicators for individual missing metrics)
- The dashboard remains functional with partial data

**JSON Parsing Failures**:
- If the Gemini response cannot be parsed as JSON, the system logs the error and displays a fallback message
- The fallback message: "Unable to extract structured insights. Please use the chat to ask specific questions."
- The raw response from Gemini is logged to CloudWatch for debugging

**Abnormal Flag Detection Failures**:
- If abnormal flag detection fails for a specific metric, the metric is displayed without the abnormal indicator
- The metric value and unit are still shown
- No error message is displayed to the user

**Logging Strategy**:
- All extraction errors are logged to CloudWatch with:
  - Session ID
  - Document text length
  - Gemini response (if available)
  - Error message and stack trace
  - Timestamp

### Backward Compatibility Error Handling

**API Endpoint Compatibility**:
- Existing API endpoints continue to work with their original request/response formats
- New fields (chatHistory) are optional in requests
- Responses include new fields but maintain all existing fields

**Lambda Function Compatibility**:
- Lambda functions handle both old and new request formats
- Missing optional fields (like chatHistory) default to empty arrays
- Existing functionality works even if new features are not used

**DynamoDB Schema Compatibility**:
- No schema changes are required
- Existing documents remain readable
- New code works with old data without migration

**Frontend Compatibility**:
- New UI components replace old ones without breaking existing functionality
- Users can continue using the system during gradual rollout
- Feature flags could control new component visibility if needed

## Testing Strategy

### Dual Testing Approach

This feature requires both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and error conditions
- Specific chat history scenarios (empty history, single exchange, multiple exchanges)
- Specific health metrics (hemoglobin = 13.5 g/dL, glucose = 95 mg/dL)
- Error conditions (malformed JSON, missing fields, network failures)
- Integration points (API request/response formats, component interactions)
- Edge cases (empty documents, very long histories, special characters)

**Property-Based Tests**: Verify universal properties across all inputs
- Chat history operations with randomly generated messages
- Health metric extraction with randomly generated document text
- Stat card generation with randomly generated metric values
- Prompt construction with randomly generated roles and histories
- Performance requirements with varied input sizes

Together, unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the input space.

### Property-Based Testing Configuration

**Testing Library**: Use `fast-check` for TypeScript/JavaScript property-based testing

**Test Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `Feature: medassist-conversational-enhancements, Property {number}: {property_text}`

**Example Property Test Structure**:
```typescript
import fc from 'fast-check';

// Feature: medassist-conversational-enhancements, Property 2: Chat History Structure Validation
test('chat history entries have required fields', () => {
  fc.assert(
    fc.property(
      fc.record({
        role: fc.constantFrom('user', 'assistant'),
        content: fc.string({ minLength: 1 }),
        timestamp: fc.date()
      }),
      (entry) => {
        // Verify entry has all required fields
        expect(entry).toHaveProperty('role');
        expect(entry).toHaveProperty('content');
        expect(entry).toHaveProperty('timestamp');
        expect(['user', 'assistant']).toContain(entry.role);
        expect(entry.content.length).toBeGreaterThan(0);
        expect(entry.timestamp).toBeInstanceOf(Date);
      }
    ),
    { numRuns: 100 }
  );
});
```

### Unit Testing Strategy

**Frontend Component Tests**:
- ChatInterface: Message sending, history display, error handling
- Dashboard: Stat card rendering, empty states, loading states
- StatCard: Content display, severity styling, abnormal indicators

**Backend Lambda Tests**:
- Chat Lambda: History formatting, prompt construction, role-based instructions
- Dashboard Lambda: Metric extraction, JSON parsing, stat card generation

**Integration Tests**:
- Full chat flow: Frontend → API → Lambda → Gemini → Response
- Full dashboard flow: Frontend → API → Lambda → DynamoDB → Gemini → Response
- Role switching: Verify prompts change with role
- Error scenarios: Network failures, invalid responses, missing data

**Test Data**:
- Sample medical documents with known metrics
- Chat histories of various lengths
- Malformed JSON responses
- Edge case inputs (empty strings, very long text, special characters)

### Testing Priorities

**High Priority** (Must test before release):
1. Chat history round-trip (send history, receive updated history)
2. Health metric extraction for common metrics (hemoglobin, glucose, WBC)
3. Role-based prompt construction (verify different prompts for each role)
4. Error handling (graceful degradation when features fail)
5. Backward compatibility (existing functionality still works)

**Medium Priority** (Should test):
1. Performance requirements (3s extraction, 5s chat response)
2. Chat history size limiting (truncation to 10 exchanges)
3. Abnormal flag detection (correct flagging of out-of-range values)
4. Partial extraction success (some metrics extracted, others missing)
5. Frontend state synchronization (history updates correctly)

**Low Priority** (Nice to test):
1. UI layout and styling (grid layout, visual indicators)
2. Caching behavior (metrics not re-extracted on refresh)
3. Logging completeness (all errors logged to CloudWatch)
4. Edge cases (very long messages, special characters, unicode)

### Test Environment Setup

**Frontend Testing**:
- Use Vitest with React Testing Library
- Mock API calls with MSW (Mock Service Worker)
- Test in isolation with mocked backend responses

**Backend Testing**:
- Use pytest for Python Lambda functions
- Mock AWS services (DynamoDB, CloudWatch) with moto
- Mock Gemini API calls with fixed responses

**Integration Testing**:
- Use a test AWS environment with real services
- Use a test Gemini API key with rate limiting
- Test with real medical document samples (anonymized)

### Continuous Testing

**Pre-commit Hooks**:
- Run unit tests on changed files
- Run linting and type checking

**CI/CD Pipeline**:
- Run all unit tests on every commit
- Run property-based tests on every pull request
- Run integration tests before deployment
- Performance tests on staging environment

**Monitoring in Production**:
- Track chat response times (should be < 5s)
- Track extraction times (should be < 3s)
- Monitor error rates for conversation memory features
- Monitor error rates for structured extraction
- Alert on elevated error rates or performance degradation
