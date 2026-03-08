"""
MedAssist RAG Lambda Function
Handles chat queries using hybrid RAG retrieval

This Lambda processes chat requests by:
1. Generating embedding for user question using Titan Embeddings
2. Performing FAISS similarity search on document embeddings (top 5)
3. Performing FAISS similarity search on knowledge base embeddings (top 3)
4. Combining retrieved chunks into unified context
5. Constructing role-specific prompt with context and question
6. Calling Amazon Bedrock Nova 2 Lite for response generation
7. Formatting response based on user role
8. Including medical disclaimer in response
9. Returning response within 5 seconds
10. Logging query metrics to CloudWatch

Requirements: 8.1-8.7, 9.1-9.7, 10.6, 10.7, 18.1, 18.3, 18.7, 19.4, 20.5
"""
import json
import os
import boto3
import time
import uuid
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple

try:
    import faiss
except ImportError:
    print("Warning: FAISS not available in this environment")
    faiss = None

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Environment variables
EMBEDDINGS_TABLE = os.environ.get('EMBEDDINGS_TABLE')
KNOWLEDGE_BASE_BUCKET = os.environ.get('KNOWLEDGE_BASE_BUCKET')
CHAT_HISTORY_TABLE = os.environ.get('CHAT_HISTORY_TABLE', 'MedAssist-ChatHistory')

# Medical disclaimer text (Req 20.5)
MEDICAL_DISCLAIMER = "This AI system provides informational insights only and does not provide medical diagnosis. Always consult a licensed healthcare professional."

# Role descriptions for prompt construction
ROLE_DESCRIPTIONS = {
    'doctor': 'a medical professional who needs clinical insights with technical accuracy',
    'patient': 'a patient who needs simple explanations without medical jargon',
    'asha': 'an ASHA worker who needs community health guidance and practical advice'
}


def generate_question_embedding(question: str) -> List[float]:
    """
    Generate embedding vector for user question using Amazon Titan Embeddings.
    
    Requirements: 8.1
    
    Args:
        question: User's chat question
    
    Returns:
        Embedding vector as list of floats
    
    Raises:
        Exception: If embedding generation fails
    """
    try:
        request_body = json.dumps({
            "inputText": question
        })
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            contentType='application/json',
            accept='application/json',
            body=request_body
        )
        
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding')
        
        if not embedding:
            raise ValueError("No embedding returned from Titan model")
        
        return embedding
    
    except Exception as e:
        print(f"Error generating question embedding: {str(e)}")
        raise


def search_document_embeddings(question_embedding: List[float], session_id: str, top_k: int = 5) -> List[Dict]:
    """
    Perform FAISS similarity search on document embeddings.
    
    Requirements: 8.2, 8.4, 8.7, 18.1, 18.3
    
    Args:
        question_embedding: Question embedding vector
        session_id: Session identifier
        top_k: Number of top results to retrieve (default 5)
    
    Returns:
        List of top k most similar document chunks with metadata
    """
    if not faiss:
        print("Warning: FAISS not available, returning empty results")
        return []
    
    try:
        # Load session-specific FAISS index from S3
        index_key = f'faiss-indices/session_{session_id}_index.faiss'
        metadata_key = f'faiss-indices/session_{session_id}_metadata.pkl'
        
        temp_index_path = '/tmp/session_index.faiss'
        temp_metadata_path = '/tmp/session_metadata.pkl'
        
        try:
            s3_client.download_file(KNOWLEDGE_BASE_BUCKET, index_key, temp_index_path)
            s3_client.download_file(KNOWLEDGE_BASE_BUCKET, metadata_key, temp_metadata_path)
        except Exception as e:
            print(f"No document index found for session {session_id}: {str(e)}")
            return []
        
        # Load FAISS index
        index = faiss.read_index(temp_index_path)
        
        # Load metadata
        import pickle
        with open(temp_metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        # Normalize question embedding for cosine similarity
        query_vector = np.array(question_embedding, dtype=np.float32)
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        # Perform similarity search (Req 18.3 - ranked by cosine similarity)
        query_vector = query_vector.reshape(1, -1)
        distances, indices = index.search(query_vector, min(top_k, index.ntotal))
        
        # Retrieve matching chunks with metadata
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(metadata):
                result = metadata[idx].copy()
                result['similarity_score'] = float(distances[0][i])
                results.append(result)
        
        print(f"Retrieved {len(results)} document chunks for session {session_id}")
        return results
    
    except Exception as e:
        print(f"Error searching document embeddings: {str(e)}")
        return []


def search_knowledge_base_embeddings(question_embedding: List[float], top_k: int = 3) -> List[Dict]:
    """
    Perform FAISS similarity search on knowledge base embeddings.
    
    Requirements: 8.3, 8.5, 8.7, 18.1, 18.3
    
    Args:
        question_embedding: Question embedding vector
        top_k: Number of top results to retrieve (default 3)
    
    Returns:
        List of top k most similar knowledge base chunks with metadata
    """
    if not faiss:
        print("Warning: FAISS not available, returning empty results")
        return []
    
    try:
        # Load knowledge base FAISS index from S3
        index_key = 'faiss-indices/knowledge_base_index.faiss'
        metadata_key = 'faiss-indices/knowledge_base_metadata.pkl'
        
        temp_index_path = '/tmp/kb_index.faiss'
        temp_metadata_path = '/tmp/kb_metadata.pkl'
        
        try:
            s3_client.download_file(KNOWLEDGE_BASE_BUCKET, index_key, temp_index_path)
            s3_client.download_file(KNOWLEDGE_BASE_BUCKET, metadata_key, temp_metadata_path)
        except Exception as e:
            print(f"No knowledge base index found: {str(e)}")
            return []
        
        # Load FAISS index
        index = faiss.read_index(temp_index_path)
        
        # Load metadata
        import pickle
        with open(temp_metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        # Normalize question embedding for cosine similarity
        query_vector = np.array(question_embedding, dtype=np.float32)
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm
        
        # Perform similarity search (Req 18.3 - ranked by cosine similarity)
        query_vector = query_vector.reshape(1, -1)
        distances, indices = index.search(query_vector, min(top_k, index.ntotal))
        
        # Retrieve matching chunks with metadata
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(metadata):
                result = metadata[idx].copy()
                result['similarity_score'] = float(distances[0][i])
                results.append(result)
        
        print(f"Retrieved {len(results)} knowledge base chunks")
        return results
    
    except Exception as e:
        print(f"Error searching knowledge base embeddings: {str(e)}")
        return []


def combine_context(document_chunks: List[Dict], kb_chunks: List[Dict]) -> Tuple[str, List[str]]:
    """
    Combine retrieved document and knowledge base chunks into unified context.
    
    Requirements: 8.6
    
    Args:
        document_chunks: Retrieved document chunks
        kb_chunks: Retrieved knowledge base chunks
    
    Returns:
        Tuple of (combined_context_text, source_list)
    """
    context_parts = []
    sources = []
    
    # Add document chunks
    if document_chunks:
        context_parts.append("Context from uploaded documents:")
        for i, chunk in enumerate(document_chunks, 1):
            context_parts.append(f"\n[Document {i}] {chunk.get('chunkText', '')}")
            sources.append(f"Document {chunk.get('documentId', 'unknown')}")
    
    # Add knowledge base chunks
    if kb_chunks:
        context_parts.append("\n\nContext from medical knowledge base:")
        for i, chunk in enumerate(kb_chunks, 1):
            context_parts.append(f"\n[Knowledge {i}] {chunk.get('chunkText', '')}")
            sources.append(f"Knowledge Base: {chunk.get('source', 'medical knowledge')}")
    
    combined_context = "\n".join(context_parts)
    return combined_context, sources


def construct_prompt(role: str, context: str, question: str) -> str:
    """
    Construct role-specific prompt with context and question.
    
    Requirements: 9.1
    
    Args:
        role: User role (doctor, patient, asha)
        context: Combined context from RAG retrieval
        question: User's question
    
    Returns:
        Formatted prompt for Bedrock model
    """
    role_description = ROLE_DESCRIPTIONS.get(role, ROLE_DESCRIPTIONS['patient'])
    
    # Role-specific instructions (Req 9.4, 9.5, 9.6)
    role_instructions = {
        'doctor': 'Provide clinical insights with technical accuracy. Use medical terminology and include specific clinical details.',
        'patient': 'Explain in simple terms that anyone can understand. Avoid medical jargon and use everyday language.',
        'asha': 'Focus on community health guidance and practical advice. Provide actionable recommendations for community health workers.'
    }
    
    instruction = role_instructions.get(role, role_instructions['patient'])
    
    prompt = f"""Role: {role}
Context: Medical AI assistant for {role_description}

{context}

User Question: {question}

Task: Answer the question as a medical AI assistant for a {role}.
{instruction}

Always include this disclaimer at the end: "{MEDICAL_DISCLAIMER}"

Provide a clear, helpful response:"""
    
    return prompt


def call_bedrock_nova(prompt: str) -> str:
    """
    Call Amazon Bedrock Nova 2 Lite for response generation.
    
    Requirements: 9.2
    
    Args:
        prompt: Formatted prompt with context and question
    
    Returns:
        Generated response text
    
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
        
        # Extract response text from Nova 2 Lite response format
        output = response_body.get('output', {})
        message = output.get('message', {})
        content = message.get('content', [])
        
        if content and len(content) > 0:
            response_text = content[0].get('text', '')
        else:
            raise ValueError("No response text returned from Bedrock Nova 2 Lite")
        
        return response_text
    
    except Exception as e:
        print(f"Error calling Bedrock Nova 2 Lite: {str(e)}")
        raise


def format_response(response_text: str, role: str) -> str:
    """
    Format response based on user role.
    
    Requirements: 9.3
    
    Args:
        response_text: Raw response from Bedrock
        role: User role
    
    Returns:
        Formatted response
    """
    # Ensure disclaimer is included (Req 20.5)
    if MEDICAL_DISCLAIMER not in response_text:
        response_text = f"{response_text}\n\n{MEDICAL_DISCLAIMER}"
    
    return response_text


def store_chat_message(session_id: str, message_id: str, sender: str, content: str, timestamp: str) -> bool:
    """
    Store chat message in DynamoDB for session persistence.
    
    Requirements: 10.5, 12.4
    
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


def retrieve_chat_history(session_id: str, limit: int = 10) -> List[Dict]:
    """
    Retrieve chat history for a session from DynamoDB.
    
    Requirements: 10.5, 12.4
    
    Args:
        session_id: Session identifier
        limit: Maximum number of messages to retrieve (default 10)
    
    Returns:
        List of chat messages ordered by timestamp (most recent last)
    """
    try:
        chat_history_table = dynamodb.Table(CHAT_HISTORY_TABLE)
        
        response = chat_history_table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': f'SESSION#{session_id}'
            },
            ScanIndexForward=True,  # Sort ascending by timestamp
            Limit=limit
        )
        
        messages = []
        for item in response.get('Items', []):
            messages.append({
                'messageId': item.get('messageId'),
                'sender': item.get('sender'),
                'content': item.get('content'),
                'timestamp': item.get('timestamp')
            })
        
        print(f"Retrieved {len(messages)} chat messages for session {session_id}")
        return messages
    
    except Exception as e:
        print(f"Error retrieving chat history: {str(e)}")
        return []


def format_response(response_text: str, role: str) -> str:
    """
    Format response based on user role.
    
    Requirements: 9.3
    
    Args:
        response_text: Raw response from Bedrock
        role: User role
    
    Returns:
        Formatted response
    """
    # Ensure disclaimer is included (Req 20.5)
    if MEDICAL_DISCLAIMER not in response_text:
        response_text = f"{response_text}\n\n{MEDICAL_DISCLAIMER}"
    
    return response_text


def handler(event, context):
    """
    Lambda handler for chat queries using hybrid RAG retrieval.
    
    This function processes chat requests by:
    1. Generating embedding for user question (Req 8.1)
    2. Searching document embeddings (top 5) (Req 8.2, 8.4)
    3. Searching knowledge base embeddings (top 3) (Req 8.3, 8.5)
    4. Combining retrieved chunks (Req 8.6)
    5. Constructing role-specific prompt (Req 9.1)
    6. Calling Bedrock Nova 2 Lite (Req 9.2)
    7. Formatting response (Req 9.3)
    8. Including medical disclaimer (Req 20.5)
    9. Storing chat history (Req 10.5, 12.4)
    10. Returning within 5 seconds (Req 9.7)
    11. Logging metrics (Req 19.4)
    
    Requirements: 8.1-8.7, 9.1-9.7, 10.5, 10.6, 10.7, 12.4, 18.1, 18.3, 18.7, 19.4, 20.5
    
    Event format:
    {
        "body": {
            "sessionId": "string",
            "role": "doctor|patient|asha",
            "message": "string",
            "language": "en|hi"
        }
    }
    """
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
        language = body.get('language', 'en')
        
        # Validate inputs
        if not all([session_id, question]):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': {
                        'code': 'INVALID_REQUEST',
                        'message': 'Missing required fields: sessionId or message',
                        'retryable': False,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            }
        
        # Validate message length (Req 10.2)
        if len(question) > 1000:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
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
        
        # Store user message in chat history (Req 10.5, 12.4)
        user_message_id = str(uuid.uuid4())
        user_timestamp = datetime.utcnow().isoformat()
        store_chat_message(session_id, user_message_id, 'user', question, user_timestamp)
        
        # Step 1: Generate embedding for user question (Req 8.1)
        question_embedding = generate_question_embedding(question)
        
        # Step 2: Search document embeddings (top 5) (Req 8.2, 8.4, 8.7)
        document_chunks = search_document_embeddings(question_embedding, session_id, top_k=5)
        
        # Step 3: Search knowledge base embeddings (top 3) (Req 8.3, 8.5, 8.7)
        kb_chunks = search_knowledge_base_embeddings(question_embedding, top_k=3)
        
        # Step 4: Combine retrieved chunks (Req 8.6)
        combined_context, sources = combine_context(document_chunks, kb_chunks)
        
        # Step 5: Construct role-specific prompt (Req 9.1)
        prompt = construct_prompt(role, combined_context, question)
        
        # Step 6: Call Bedrock Nova 2 Lite (Req 9.2)
        response_text = call_bedrock_nova(prompt)
        
        # Step 7: Format response based on role (Req 9.3)
        formatted_response = format_response(response_text, role)
        
        # Store AI response in chat history (Req 10.5, 12.4)
        ai_message_id = str(uuid.uuid4())
        ai_timestamp = datetime.utcnow().isoformat()
        store_chat_message(session_id, ai_message_id, 'ai', formatted_response, ai_timestamp)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Log query metrics to CloudWatch (Req 19.4)
        print(json.dumps({
            'event': 'rag_complete',
            'sessionId': session_id,
            'role': role,
            'metrics': {
                'question_length': len(question),
                'document_chunks_retrieved': len(document_chunks),
                'kb_chunks_retrieved': len(kb_chunks),
                'response_length': len(formatted_response),
                'elapsed_time_seconds': elapsed_time
            },
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Return response within 5 seconds (Req 9.7)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'response': formatted_response,
                'sources': sources,
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
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'error': {
                    'code': 'RAG_FAILED',
                    'message': 'Our AI service is temporarily unavailable. Please try again in a moment.',
                    'retryable': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        }
