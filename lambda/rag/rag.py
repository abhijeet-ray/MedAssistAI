"""
MedAssist RAG Lambda - Using Google Gemini API
Uses Gemini 1.5 Flash with direct DynamoDB text retrieval
"""
import json
import os
import requests
from datetime import datetime
import boto3

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Environment variables
DOCUMENT_TABLE = os.environ.get('DOCUMENT_TABLE', 'MedAssist-Documents')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# CORS headers for all responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}


def get_document_text(session_id):
    """
    Retrieve document text from DynamoDB for the given session.
    Uses query with sessionId as partition key.
    """
    try:
        table = dynamodb.Table(DOCUMENT_TABLE)
        
        # Query for documents with this sessionId as PK
        response = table.query(
            KeyConditionExpression='PK = :sid',
            ExpressionAttributeValues={':sid': session_id}
        )
        
        items = response.get('Items', [])
        
        if not items:
            print(f"No documents found for session {session_id}")
            return ""
        
        # Concatenate all document text
        all_text = []
        for item in items:
            # Use 'documentText' field from schema
            text = item.get('documentText', '')
            if text:
                all_text.append(text[:5000])  # Max 5000 chars per doc
        
        combined = " ".join(all_text)
        print(f"Retrieved {len(items)} documents, total text length: {len(combined)}")
        
        if not combined:
            print(f"WARNING: Documents found but no text extracted")
        
        return combined
        
    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""


def call_gemini(prompt):
    """
    Call Google Gemini API to generate response.
    Returns None on failure so fallback can be used.
    """
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        print(f"Calling Gemini API with prompt length: {len(prompt)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            # Return None to trigger fallback
            return None
        
        data = response.json()
        
        # Extract answer from Gemini response
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
        
        print(f"Gemini response length: {len(answer)}")
        
        return answer
        
    except requests.exceptions.Timeout:
        print("Gemini API timeout - using fallback")
        return None
    
    except requests.exceptions.ConnectionError as e:
        print(f"Gemini API connection error: {str(e)} - using fallback")
        return None
    
    except KeyError as e:
        print(f"Error parsing Gemini response: {str(e)} - using fallback")
        return None
    
    except Exception as e:
        print(f"Error calling Gemini: {str(e)} - using fallback")
        import traceback
        traceback.print_exc()
        return None


def generate_fallback_response(document_text, user_question):
    """
    Generate a fallback response when Gemini API fails.
    Extracts information from document text without AI processing.
    
    Returns structured response with Summary, Important Findings, What It Means, Suggested Action.
    """
    try:
        # Calculate basic metrics
        word_count = len(document_text.split())
        char_count = len(document_text)
        line_count = len(document_text.split('\n'))
        
        # Extract first 300 characters as preview
        preview = document_text[:300].strip()
        if len(document_text) > 300:
            preview += "..."
        
        # Detect if document contains common medical terms
        medical_keywords = ['blood', 'glucose', 'hemoglobin', 'pressure', 'cholesterol', 
                           'test', 'result', 'normal', 'high', 'low', 'report', 'patient',
                           'diagnosis', 'treatment', 'medication', 'symptom']
        found_keywords = [kw for kw in medical_keywords if kw.lower() in document_text.lower()]
        
        # Build fallback response
        summary = f"The uploaded document contains medical test information. Your report has {word_count} words and appears to be a medical document."
        
        important_findings = [
            f"Document uploaded successfully",
            f"{word_count} words detected in the report",
            f"Medical report text is available for analysis"
        ]
        
        if found_keywords:
            important_findings.append(f"Document contains medical terms: {', '.join(found_keywords[:3])}")
        
        what_it_means = "The system detected a medical document and extracted the text successfully. AI analysis may be temporarily unavailable due to external API issues. The document content is preserved and ready for analysis when the service recovers."
        
        suggested_action = [
            "Try asking the question again",
            "Ensure the report text is clear and readable",
            "Consult a healthcare professional for final medical advice"
        ]
        
        # Format as structured response
        response_text = f"""Summary: {summary}

Important Findings:
{chr(10).join([f"• {finding}" for finding in important_findings])}

What It Means: {what_it_means}

Suggested Action:
{chr(10).join([f"• {action}" for action in suggested_action])}"""
        
        print(f"Generated fallback response (length: {len(response_text)})")
        return response_text
        
    except Exception as e:
        print(f"Error generating fallback response: {str(e)}")
        # Return minimal fallback
        return """Summary: Your medical document has been received.

Important Findings:
• Document uploaded successfully
• System is processing your request

What It Means: The system is temporarily experiencing issues with AI analysis but your document is safely stored.

Suggested Action:
• Try asking your question again
• Contact support if issues persist"""


def get_role_explanation_style(role):
    """
    Get explanation style based on user role.
    """
    role_styles = {
        'doctor': 'clinical medical explanation for healthcare professionals with technical terminology',
        'patient': 'simple easy language for patients without medical jargon',
        'asha': 'community health worker explanation for rural healthcare guidance with practical advice'
    }
    return role_styles.get(role, role_styles['patient'])


def get_role_prompt_instructions(role):
    """
    Returns detailed role-specific instructions for Gemini prompt.
    
    Args:
        role: User role - 'patient', 'doctor', or 'asha'
        
    Returns:
        String containing role-specific instruction text for the prompt
    """
    instructions = {
        'patient': """You are a medical AI assistant helping a patient understand their health information.

Response Style Guidelines:
- Use simple, everyday language that a general person can understand
- Avoid medical jargon; if you must use a medical term, explain it in plain English
- Use analogies and examples to clarify complex concepts
- Focus on practical health implications and what the patient should do
- Provide actionable advice and next steps
- Structure responses with clear sections for easy understanding
- Be empathetic and supportive in tone
- Explain why information matters for their health
- Use bullet points for clarity when listing multiple items""",
        
        'doctor': """You are a medical AI assistant helping a healthcare professional analyze patient information.

Response Style Guidelines:
- Use standard clinical medical terminology and professional language
- Include relevant diagnostic considerations and differential diagnoses when appropriate
- Reference clinical guidelines and evidence-based practices
- Provide detailed pathophysiology explanations when relevant to the clinical question
- Structure responses with clinical assessment and management recommendations
- Include relevant lab value interpretations and clinical significance
- Consider drug interactions and contraindications when discussing treatments
- Use precise medical terminology without simplification
- Provide comprehensive clinical context for decision-making""",
        
        'asha': """You are a medical AI assistant helping a community health worker provide healthcare guidance in rural settings.

Response Style Guidelines:
- Focus on community health education and preventive health guidance
- Emphasize when patients should be referred to medical facilities or doctors
- Use language accessible to health workers without formal medical degrees
- Provide practical advice suitable for resource-limited settings
- Include information about local health resources and referral pathways
- Focus on health promotion and disease prevention
- Explain health concepts in simple, relatable terms
- Provide guidance on when to escalate care to higher-level facilities
- Include practical tips for community outreach and health education"""
    }
    
    return instructions.get(role, instructions['patient'])


def format_chat_history(chat_history):
    """
    Format chat history for the prompt.
    Limits to last 10 exchanges to manage token count.
    
    Args:
        chat_history: List of chat history entries with 'user' and 'ai' keys
        
    Returns:
        Formatted string of chat history for inclusion in prompt
    """
    if not chat_history or len(chat_history) == 0:
        return "No previous conversation."
    
    # Take last 10 exchanges to manage token count
    recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
    
    formatted = []
    for entry in recent_history:
        user_msg = entry.get('user', '')
        ai_msg = entry.get('ai', '')
        if user_msg and ai_msg:
            formatted.append(f"User: {user_msg}\nAI: {ai_msg}")
    
    return "\n\n".join(formatted) if formatted else "No previous conversation."


def update_chat_history(current_history, user_msg, ai_response):
    """
    Append new exchange to chat history and maintain size limit.
    
    Args:
        current_history: Current list of chat history entries
        user_msg: User's question/message
        ai_response: AI's response
        
    Returns:
        Updated chat history list with new exchange appended, limited to 10 exchanges
    """
    updated = current_history.copy() if current_history else []
    updated.append({
        'user': user_msg,
        'ai': ai_response
    })
    
    # Keep only last 10 exchanges (20 messages total)
    if len(updated) > 10:
        updated = updated[-10:]
    
    return updated


def handler(event, context):
    """
    Lambda handler for chat requests with conversational memory and role-based responses.
    """
    print(f"Event: {json.dumps(event)}")
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('sessionId')
        question = body.get('message')
        role = body.get('role', 'patient')
        chat_history = body.get('chatHistory', [])
        
        print(f"Session: {session_id}, Question: {question}, Role: {role}, History length: {len(chat_history)}")
        
        if not session_id or not question:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'Missing sessionId or message'
                })
            }
        
        # Step 1: Get document text from DynamoDB
        document_text = get_document_text(session_id)
        
        # Step 2: Check if we have document text (removed "Document not processed yet" message)
        if not document_text:
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'answer': 'Please upload a medical document to get started with your health analysis.',
                    'source': 'none',
                    'timestamp': datetime.utcnow().isoformat(),
                    'chatHistory': chat_history
                })
            }
        
        # Step 3: Get role-specific prompt instructions
        role_instructions = get_role_prompt_instructions(role)
        
        # Step 4: Format chat history
        formatted_history = format_chat_history(chat_history)
        
        # Step 5: Create conversational prompt for Gemini
        prompt = f"""{role_instructions}

Medical report:
{document_text}

Conversation history:
{formatted_history}

Current question: {question}

IMPORTANT: You MUST structure your response with these exact section headers:

Summary: [1-2 sentence summary of your response]

Important Findings:
• [Finding 1]
• [Finding 2]
• [Finding 3]
(Include 3-7 bullet points)

What It Means: [2-3 sentences explaining the clinical significance or implications]

Suggested Action:
• [Action 1]
• [Action 2]
(Include 1-3 actionable items)

Instructions for this response:
- Consider the conversation history when answering
- Do NOT repeat information already provided in the conversation history
- Answer the current question directly and completely
- Reference previous context when relevant to the question
- If using pronouns (it, that, this, etc.), resolve them from the conversation history
- Be concise and focused on the user's specific question
- Use bullet points (•) for all list items
- ALWAYS include all 4 sections: Summary, Important Findings, What It Means, Suggested Action
- Do NOT deviate from this format

Respond now:"""
        
        print(f"Prompt length: {len(prompt)}")
        
        # Step 6: Call Gemini
        answer = call_gemini(prompt)
        
        # Step 6b: Use fallback if Gemini fails
        if answer is None:
            print("Gemini API failed, using fallback response")
            answer = generate_fallback_response(document_text, question)
        
        print(f"Answer length: {len(answer)}")
        
        # Step 7: Update chat history
        updated_history = update_chat_history(chat_history, question, answer)
        
        # Step 8: Return response with updated history
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'answer': answer,
                'source': 'uploaded_document',
                'timestamp': datetime.utcnow().isoformat(),
                'chatHistory': updated_history
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': f'Internal error: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
