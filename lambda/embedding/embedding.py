"""
MedAssist Embedding Lambda Function
Processes extracted text, generates embeddings, and stores them in DynamoDB and FAISS.

This Lambda is triggered by ExtractionLambda after text extraction completes.
It chunks the text, generates embeddings using Amazon Titan, stores them in DynamoDB,
updates the FAISS index, and triggers DashboardLambda.

Requirements: 5.1-5.5, 12.3, 17.2, 18.2, 19.3
"""
import json
import os
import boto3
import uuid
from datetime import datetime
from typing import List, Dict
import tiktoken
import numpy as np

try:
    import faiss
except ImportError:
    print("Warning: FAISS not available in this environment")
    faiss = None

# AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

# Environment variables
EMBEDDINGS_TABLE = os.environ.get('EMBEDDINGS_TABLE')
DASHBOARD_LAMBDA = os.environ.get('DASHBOARD_LAMBDA')
KNOWLEDGE_BASE_BUCKET = os.environ.get('KNOWLEDGE_BASE_BUCKET')
CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 50  # tokens

# Initialize tokenizer for accurate token counting
tokenizer = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text: The text to count tokens for
    
    Returns:
        Number of tokens
    """
    return len(tokenizer.encode(text))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    """
    Split text into chunks of specified token size with overlap.
    Reuses the chunking logic from kb-embedding Lambda for consistency.
    
    Requirements: 5.1, 5.4
    
    Args:
        text: The text to chunk
        chunk_size: Maximum tokens per chunk (default 512)
        overlap: Number of overlapping tokens between chunks (default 50)
    
    Returns:
        List of dictionaries containing chunk text and metadata
    """
    # Tokenize the entire text
    tokens = tokenizer.encode(text)
    chunks = []
    
    start_idx = 0
    chunk_index = 0
    
    while start_idx < len(tokens):
        # Calculate end index for this chunk
        end_idx = min(start_idx + chunk_size, len(tokens))
        
        # Extract chunk tokens and decode back to text
        chunk_tokens = tokens[start_idx:end_idx]
        chunk_text = tokenizer.decode(chunk_tokens)
        
        # Store chunk with metadata
        chunks.append({
            'text': chunk_text,
            'chunk_index': chunk_index,
            'start_token': start_idx,
            'end_token': end_idx,
            'token_count': len(chunk_tokens)
        })
        
        chunk_index += 1
        
        # Move start index forward, accounting for overlap
        # If this is the last chunk, break
        if end_idx >= len(tokens):
            break
        
        start_idx = end_idx - overlap
    
    return chunks


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector using Amazon Titan Embeddings.
    
    Requirements: 5.2
    
    Args:
        text: The text to embed
    
    Returns:
        Embedding vector as list of floats
    """
    try:
        # Prepare request for Titan Embeddings
        request_body = json.dumps({
            "inputText": text
        })
        
        # Call Bedrock Titan Embeddings model
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            contentType='application/json',
            accept='application/json',
            body=request_body
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding')
        
        if not embedding:
            raise ValueError("No embedding returned from Titan model")
        
        return embedding
    
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        raise


def store_embedding_dynamodb(embedding_data: Dict) -> None:
    """
    Store embedding and metadata in DynamoDB.
    
    Requirements: 5.3, 17.2
    
    Args:
        embedding_data: Dictionary containing embedding and metadata
    """
    try:
        table = dynamodb.Table(EMBEDDINGS_TABLE)
        
        # Store in DynamoDB
        table.put_item(Item=embedding_data)
        
        print(f"Stored embedding {embedding_data['embeddingId']} in DynamoDB")
    
    except Exception as e:
        print(f"Error storing embedding in DynamoDB: {str(e)}")
        raise


def update_faiss_index(embeddings_data: List[Dict], session_id: str) -> Dict:
    """
    Update FAISS index with new document embeddings.
    
    Requirements: 5.5, 18.2
    
    Args:
        embeddings_data: List of embedding dictionaries
        session_id: Session identifier
    
    Returns:
        Dictionary with FAISS index information
    """
    if not faiss:
        print("Warning: FAISS not available, skipping index update")
        return {'status': 'skipped', 'reason': 'FAISS not available'}
    
    try:
        # FAISS index key for this session
        index_key = f'faiss-indices/session_{session_id}_index.faiss'
        metadata_key = f'faiss-indices/session_{session_id}_metadata.pkl'
        
        # Try to load existing index for this session
        index = None
        metadata = []
        
        try:
            temp_index_path = '/tmp/session_index.faiss'
            s3_client.download_file(KNOWLEDGE_BASE_BUCKET, index_key, temp_index_path)
            index = faiss.read_index(temp_index_path)
            
            # Load metadata
            import pickle
            temp_metadata_path = '/tmp/session_metadata.pkl'
            s3_client.download_file(KNOWLEDGE_BASE_BUCKET, metadata_key, temp_metadata_path)
            with open(temp_metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            print(f"Loaded existing FAISS index with {index.ntotal} vectors")
        except Exception as e:
            print(f"No existing index found, creating new one: {str(e)}")
            # Create new index (dimension 1536 for Titan Embeddings)
            index = faiss.IndexFlatIP(1536)
        
        # Prepare new vectors and metadata
        new_vectors = []
        
        for emb in embeddings_data:
            vector = emb.get('embedding')
            if not vector:
                continue
            
            # Convert to numpy array and normalize for cosine similarity
            vec_array = np.array(vector, dtype=np.float32)
            norm = np.linalg.norm(vec_array)
            if norm > 0:
                vec_array = vec_array / norm
            
            new_vectors.append(vec_array)
            
            # Add metadata
            metadata.append({
                'embeddingId': emb.get('embeddingId'),
                'documentId': emb.get('documentId'),
                'chunkIndex': emb.get('chunkIndex'),
                'chunkText': emb.get('chunkText'),
                'source': emb.get('source')
            })
        
        # Add new vectors to index
        if new_vectors:
            vectors_array = np.array(new_vectors, dtype=np.float32)
            index.add(vectors_array)
            print(f"Added {len(new_vectors)} vectors to FAISS index, total: {index.ntotal}")
        
        # Save updated index to S3
        temp_index_path = '/tmp/session_index.faiss'
        faiss.write_index(index, temp_index_path)
        
        with open(temp_index_path, 'rb') as f:
            s3_client.put_object(
                Bucket=KNOWLEDGE_BASE_BUCKET,
                Key=index_key,
                Body=f.read(),
                ContentType='application/octet-stream'
            )
        
        # Save metadata
        import pickle
        temp_metadata_path = '/tmp/session_metadata.pkl'
        with open(temp_metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        with open(temp_metadata_path, 'rb') as f:
            s3_client.put_object(
                Bucket=KNOWLEDGE_BASE_BUCKET,
                Key=metadata_key,
                Body=f.read(),
                ContentType='application/octet-stream'
            )
        
        print(f"FAISS index updated and saved to S3: {index_key}")
        
        return {
            'status': 'success',
            'index_location': f"s3://{KNOWLEDGE_BASE_BUCKET}/{index_key}",
            'metadata_location': f"s3://{KNOWLEDGE_BASE_BUCKET}/{metadata_key}",
            'vector_count': index.ntotal
        }
    
    except Exception as e:
        print(f"Error updating FAISS index: {str(e)}")
        # Don't fail the entire operation if FAISS update fails
        return {'status': 'failed', 'error': str(e)}


def trigger_dashboard_lambda(document_id: str, session_id: str) -> None:
    """
    Trigger DashboardLambda after embedding completion.
    
    Args:
        document_id: Document identifier
        session_id: Session identifier
    """
    try:
        lambda_client.invoke(
            FunctionName=DASHBOARD_LAMBDA,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps({
                'documentId': document_id,
                'sessionId': session_id,
                'trigger': 'embedding_complete'
            })
        )
        print(json.dumps({
            'event': 'dashboard_triggered',
            'documentId': document_id,
            'sessionId': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }))
    except Exception as e:
        # Log error but don't fail the embedding operation
        print(json.dumps({
            'event': 'dashboard_trigger_failed',
            'documentId': document_id,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))


def handler(event, context):
    """
    Lambda handler to process extracted text and generate embeddings.
    
    This function is triggered by ExtractionLambda after text extraction completes.
    It performs the following operations:
    1. Chunk the extracted text (512 tokens, 50 token overlap)
    2. Generate embeddings using Amazon Titan Embeddings
    3. Store embeddings in DynamoDB with chunk metadata
    4. Update FAISS index with new vectors
    5. Trigger DashboardLambda after completion
    
    Requirements: 5.1-5.5, 12.3, 17.2, 18.2, 19.3
    
    Event format:
    {
        "documentId": "string",
        "sessionId": "string",
        "extractedText": "string",
        "medicalEntities": [...]
    }
    """
    print(json.dumps({
        'event': 'embedding_start',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': {
            'table': EMBEDDINGS_TABLE,
            'dashboard_lambda': DASHBOARD_LAMBDA
        }
    }))
    
    try:
        # Parse event
        document_id = event.get('documentId')
        session_id = event.get('sessionId')
        extracted_text = event.get('extractedText')
        medical_entities = event.get('medicalEntities', [])
        
        if not all([document_id, session_id, extracted_text]):
            raise ValueError('Missing required event parameters: documentId, sessionId, or extractedText')
        
        print(f"Processing document {document_id} for session {session_id}")
        print(f"Text length: {len(extracted_text)} characters, {count_tokens(extracted_text)} tokens")
        
        # Chunk the text (Req 5.1, 5.4)
        chunks = chunk_text(extracted_text)
        print(f"Created {len(chunks)} chunks from extracted text")
        
        # Generate embeddings for each chunk
        embeddings_data = []
        
        for chunk in chunks:
            # Generate unique embedding ID
            embedding_id = str(uuid.uuid4())
            
            # Generate embedding vector (Req 5.2)
            embedding_vector = generate_embedding(chunk['text'])
            
            # Extract medical entities that appear in this chunk
            chunk_entities = []
            for entity in medical_entities:
                if entity.get('text', '').lower() in chunk['text'].lower():
                    chunk_entities.append(entity.get('text'))
            
            # Prepare data for storage (Req 5.3, 17.2)
            embedding_data = {
                'PK': f"EMB#{embedding_id}",
                'SK': f"CHUNK#{chunk['chunk_index']}",
                'embeddingId': embedding_id,
                'documentId': document_id,
                'sessionId': session_id,
                'chunkIndex': chunk['chunk_index'],
                'chunkText': chunk['text'],
                'embedding': embedding_vector,
                'source': 'document',
                'metadata': {
                    'startToken': chunk['start_token'],
                    'endToken': chunk['end_token'],
                    'tokenCount': chunk['token_count'],
                    'medicalEntities': chunk_entities
                },
                'createdAt': datetime.utcnow().isoformat()
            }
            
            # Store in DynamoDB (Req 5.3, 17.2)
            store_embedding_dynamodb(embedding_data)
            
            embeddings_data.append(embedding_data)
        
        print(f"Successfully generated and stored {len(embeddings_data)} embeddings")
        
        # Update FAISS index (Req 5.5, 18.2)
        faiss_result = update_faiss_index(embeddings_data, session_id)
        
        # Log embedding metrics to CloudWatch (Req 19.3)
        print(json.dumps({
            'event': 'embedding_complete',
            'documentId': document_id,
            'sessionId': session_id,
            'metrics': {
                'text_length': len(extracted_text),
                'token_count': count_tokens(extracted_text),
                'chunk_count': len(chunks),
                'embedding_count': len(embeddings_data),
                'faiss_status': faiss_result.get('status')
            },
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Trigger DashboardLambda
        trigger_dashboard_lambda(document_id, session_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Embeddings generated and stored successfully',
                'documentId': document_id,
                'sessionId': session_id,
                'chunk_count': len(chunks),
                'embedding_count': len(embeddings_data),
                'faiss_index': faiss_result
            })
        }
    
    except Exception as e:
        # Log error with stack trace (Req 19.3)
        import traceback
        print(json.dumps({
            'event': 'embedding_error',
            'error': str(e),
            'stack_trace': traceback.format_exc(),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': {
                    'code': 'EMBEDDING_FAILED',
                    'message': 'Failed to generate embeddings',
                    'details': str(e)
                }
            })
        }
