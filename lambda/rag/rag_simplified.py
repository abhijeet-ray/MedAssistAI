"""
MedAssist RAG Lambda Function - Simplified Version
Handles chat queries using direct document text retrieval

This Lambda processes chat requests by:
1. Retrieving document text directly from DynamoDB
2. Constructing simple prompt with document context
3. Calling Amazon Bedrock Nova Lite for response generation
4. Returning answer in JSON format

Simplified for stable demo - no FAISS, no embeddings, no translation
"""
import json
import os
import boto3
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from botocore.exceptions import ClientError

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
dynamodb = boto3.resource('dynamodb')

# Environment variables
DOCUMENT_TABLE = os.environ.get('DOCUMENT_TABLE', 'MedAssist-Documents')
CHAT_HISTORY_TABLE = os.environ.get('CHAT_HISTORY_TABLE', 'MedAssist-ChatHistory')

# Medical disclaimer text
MEDICAL_DISCLAIMER = "This AI system provides informational insights only and does not provide medical diagnosis. Always consult a licensed healthcare professional."

# CORS headers for all responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}


def retrieve_document_text(session_id: str) -> str:
    """
    Retrieve all document text for a session directly from DynamoDB.
    No embedding generation or vector search.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Combined document text (up to 4000 chars per document)
    """
    try:
        document_table = dynamodb.Table(DOCUMENT_TABLE)
        
        # Query all documents for this session using GSI
        response = document_table.query(
            IndexName='SessionIndex',
            KeyConditionExpression='sessionId = :sid',
            ExpressionAttributeValues={
                ':sid': session_id
            }
        )
        
        documents = response.get('Items', [])
        
        if not documents:
            print(f"No documents found for session {session_id}")
            return ""
        
        # Concatenate document text (up to 4000 chars per document)
        context_parts = []
        for doc in documents:
            extracted_text = doc.get('extractedText', '')
            if extracted_text:
                # Truncate to 4000 characters per document
                truncated_text = extracted_text[:4000]
                context_parts.append(truncated_text)
        
        combined_context = "\n\n".join(context_parts)
        print(f"Retrieved {len(documents)} documents for session {session_id}, total context length: {len(combined_context)}")
        
        return combined_context
    
    except Exception as e:
        print(f"Error retrieving document text: {str(e)}")
        raise


def construct_prompt(context: str, question: str, role: str) -> str:
    """
    Construct simple prompt with document context and question.
    
    Args:
        context: Document text
        question: User's question
        role: User role (doctor, patient, asha)
    
    Returns:
        Formatted prompt for Nova Lite
    """
    # Role-specific instructions
    role_instructions = {
        'doctor': 'Provide clinical insights with technical accuracy.',
        'patient': 'Explain in simple terms without medical jargon.',
        'asha': 'Focus on community health guidance and practical advice.'
    }
    
    instruction = role_instructions.get(role, role_instructions['patient'])
    
    prompt = f"""You are a medical document assistant. The following medical document text was uploaded by the user.

Document: {context}

User Question: {question}

{instruction}

Answer clearly using the document information. If the answer is not in the document, say you cannot find it in the report."""
    
    return prompt


def call_nova_lite(prompt: str) -> str:
    """
    Call Amazon Bedrock Nova Lite for answer generation.
    
    Args:
        prompt: Formatted prompt with context and question
    
    Returns:
        Generated answer text
    
    Raises:
        Exception: If Bedrock API call fails
    """
    try:
        request_body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 1000,
                "temperature": 0.7,
                "topP": 0.9
            }
        })
        
        response = bedrock_runtime.invoke_model(
            modelId='us.amazon.nova-lite-v1:0',
            contentType='application/json',
            accept='application/json',
            body=request_body
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract response text from Nova Lite response format
        output = response_body.get('output', {})
        message = output.get('message', {})
        content = message.get('content', [])
        
        if content and len(content) > 0:
            response_text = content[0].get('text', '')
        else:
            raise ValueError("No response text returned from Bedrock Nova Lite")
        
        return response_text
    
    except Exception as e:
        print(f"Error calling Bedrock Nova Lite: {str(e)}")
        raise


def store_chat_message(session_id: str, message_id: str, sender: str, content: str, timestamp: str) -> bool:
    """
    Store chat message in DynamoDB for session persistence.
    
    Args:
        session_id: Session identifier
        message_id: Unique message identifier
        sender: 'user' or 'ai'
        content: Message content
        timestamp: ISO-8601 timestamp
    
    Returns:
        True if successful, False otherwise
    """
    try:
        chat_history_table = dynamodb.Table(CHAT_HISTORY_TABLE)
        
        chat_history_table.put_item(
            Item={
                'PK': f'SESSION#{session_id}',
                'SK': f'MESSAGE#{timestamp}#{message_id}',
                'sessionId': session_id,
                'messageId': message_id,
                'sender': sender,
                'content': content,
                'timestamp': timestamp,
                'ttl': int(datetime.utcnow().timestamp()) + (24 * 60 * 60)  # 24-hour TTL
            }
        )
        
        print(f"Stored {sender} message {message_id} for session {session_id}")
        return True
    
    except Exception as e:
        print(f"Error storing chat message: {str(e)}")
        return False


def handler(event, context):
    """
    Lambda handler for chat queries using simplified direct text retrieval.
    
    This function processes chat requests by:
    1. Retrieving document text from DynamoDB
    2. Constructing prompt with context
    3. Calling Nova Lite
    4. Returning answer
    
    Event format:
    {
        "body": {
            "sessionId": "string",
            "role": "doctor|patient|asha",
            "message": "string"
        }
    }
    """
    # Handle OPTIONS preflight request
    if event.get('httpMethod') == 'OPTIONS' or event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    start_time = time.time()
    
    print(json.dumps({
        'event': 'rag_start',
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        session_id = body.get('sessionId')
        role = body.get('role', 'patient')
        question = body.get('message')
        
        # Validate inputs
        if not all([session_id, question]):
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': 'Missing required fields: sessionId or message',
                        'retryable': False,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            }
        
        # Validate message length
        if len(question) > 1000:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': {
                        'code': 'MESSAGE_TOO_LONG',
                        'message': 'Message exceeds maximum length of 1000 characters',
                        'retryable': False,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            }
        
        print(f"Processing chat query for session {session_id}, role: {role}")
        
        # Store user message in chat history
        user_message_id = str(uuid.uuid4())
        user_timestamp = datetime.utcnow().isoformat()
        store_chat_message(session_id, user_message_id, 'user', question, user_timestamp)
        
        # Step 1: Retrieve document text directly from DynamoDB
        context = retrieve_document_text(session_id)
        
        # Check if no documents found
        if not context:
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': {
                        'code': 'NO_DOCUMENTS',
                        'message': 'No documents found. Please upload a document first.',
                        'retryable': False,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            }
        
        # Step 2: Construct prompt with context and question
        prompt = construct_prompt(context, question, role)
        
        # Step 3: Call Nova Lite for answer generation
        answer = call_nova_lite(prompt)
        
        # Add disclaimer
        if MEDICAL_DISCLAIMER not in answer:
            answer = f"{answer}\n\n{MEDICAL_DISCLAIMER}"
        
        # Store AI response in chat history
        ai_message_id = str(uuid.uuid4())
        ai_timestamp = datetime.utcnow().isoformat()
        store_chat_message(session_id, ai_message_id, 'ai', answer, ai_timestamp)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Log query metrics to CloudWatch
        print(json.dumps({
            'event': 'rag_complete',
            'sessionId': session_id,
            'role': role,
            'metrics': {
                'question_length': len(question),
                'context_length': len(context),
                'answer_length': len(answer),
                'elapsed_time_seconds': elapsed_time
            },
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Return response in required format
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'answer': answer,
                'source': 'uploaded_document',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    except Exception as e:
        # Error handling
        import traceback
        elapsed_time = time.time() - start_time
        
        print(json.dumps({
            'event': 'rag_error',
            'error': str(e),
            'stack_trace': traceback.format_exc(),
            'elapsed_time_seconds': elapsed_time,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': {
                    'code': 'LLM_FAILED',
                    'message': 'Failed to generate answer. Please try again.',
                    'retryable': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        }
