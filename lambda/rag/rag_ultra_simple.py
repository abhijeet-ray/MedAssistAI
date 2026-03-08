"""
MedAssist RAG Lambda - Ultra Simple for Demo
Uses only Amazon Nova 2 Lite with direct DynamoDB text retrieval
"""
import json
import os
import boto3
from datetime import datetime

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Environment variables
DOCUMENT_TABLE = os.environ.get('DOCUMENT_TABLE', 'MedAssist-Documents')

# CORS headers for all responses
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}


def get_document_text(session_id):
    """
    Retrieve document text from DynamoDB for the given session.
    """
    try:
        table = dynamodb.Table(DOCUMENT_TABLE)
        
        # Scan for documents with this sessionId
        response = table.scan(
            FilterExpression='sessionId = :sid',
            ExpressionAttributeValues={':sid': session_id}
        )
        
        documents = response.get('Items', [])
        
        if not documents:
            print(f"No documents found for session {session_id}")
            return ""
        
        # Concatenate all document text
        all_text = []
        for doc in documents:
            text = doc.get('extractedText', '')
            if text:
                all_text.append(text[:5000])  # Max 5000 chars per doc
        
        combined = "\n\n".join(all_text)
        print(f"Retrieved {len(documents)} documents, total text length: {len(combined)}")
        return combined
        
    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return ""


def call_nova_lite(prompt):
    """
    Call Amazon Bedrock Nova 2 Lite model.
    """
    try:
        request_body = {
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
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-lite-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract text from Nova response
        output = response_body.get('output', {})
        message = output.get('message', {})
        content = message.get('content', [])
        
        if content and len(content) > 0:
            return content[0].get('text', '')
        
        return "I couldn't generate a response. Please try again."
        
    except Exception as e:
        print(f"Error calling Nova Lite: {str(e)}")
        return f"Error generating response: {str(e)}"


def handler(event, context):
    """
    Lambda handler for chat requests.
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
        
        print(f"Session: {session_id}, Question: {question}")
        
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
        
        # Step 2: Check if we have document text
        if not document_text:
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'answer': 'Please upload a medical document first.',
                    'source': 'none',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Step 3: Create simple prompt
        prompt = f"""You are a medical assistant AI.
Use the following medical report text to answer the user's question.

Medical Report:
{document_text}

Question: {question}

Explain clearly in simple language for patients."""
        
        print(f"Prompt length: {len(prompt)}")
        
        # Step 4: Call Nova Lite
        answer = call_nova_lite(prompt)
        
        print(f"Answer length: {len(answer)}")
        
        # Step 5: Return response
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
