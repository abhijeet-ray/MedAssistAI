"""
MedAssist Knowledge Base Embedding Lambda Function
Initializes knowledge base by reading files from S3, chunking text,
generating embeddings, and storing them in DynamoDB and FAISS index.

Requirements: 5.1, 5.2, 5.4, 6.6, 6.7, 17.3, 18.2
"""
import json
import os
import boto3
import uuid
from datetime import datetime
from typing import List, Dict, Tuple
import tiktoken

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Environment variables
KNOWLEDGE_BASE_BUCKET = os.environ.get('KNOWLEDGE_BASE_BUCKET')
EMBEDDINGS_TABLE = os.environ.get('EMBEDDINGS_TABLE')
CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 50  # tokens

# Initialize tokenizer for accurate token counting
tokenizer = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    return len(tokenizer.encode(text))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, any]]:
    """
    Split text into chunks of specified token size with overlap.
    
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
    
    Requirements: 5.2, 6.6
    
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
    
    Requirements: 5.3, 17.3
    
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


def process_knowledge_base_file(bucket: str, key: str) -> List[Dict]:
    """
    Process a single knowledge base file: read, chunk, embed, and store.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        List of embedding data dictionaries
    """
    print(f"Processing knowledge base file: {key}")
    
    try:
        # Read file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        text_content = response['Body'].read().decode('utf-8')
        
        print(f"Read {len(text_content)} characters from {key}")
        
        # Extract filename without extension for topic identification
        filename = key.split('/')[-1]
        topic = filename.replace('.txt', '')
        
        # Chunk the text
        chunks = chunk_text(text_content)
        print(f"Created {len(chunks)} chunks from {key}")
        
        # Generate embeddings for each chunk
        embeddings_data = []
        
        for chunk in chunks:
            # Generate unique embedding ID
            embedding_id = str(uuid.uuid4())
            
            # Generate embedding vector
            embedding_vector = generate_embedding(chunk['text'])
            
            # Prepare data for storage
            embedding_data = {
                'PK': f"EMB#{embedding_id}",
                'SK': f"CHUNK#{chunk['chunk_index']}",
                'embeddingId': embedding_id,
                'documentId': f"KB_{topic}",
                'sessionId': 'KNOWLEDGE_BASE',
                'chunkIndex': chunk['chunk_index'],
                'chunkText': chunk['text'],
                'embedding': embedding_vector,
                'source': 'knowledge_base',
                'topic': topic,
                'metadata': {
                    'startToken': chunk['start_token'],
                    'endToken': chunk['end_token'],
                    'tokenCount': chunk['token_count'],
                    'filename': filename
                },
                'createdAt': datetime.utcnow().isoformat()
            }
            
            # Store in DynamoDB
            store_embedding_dynamodb(embedding_data)
            
            embeddings_data.append(embedding_data)
        
        print(f"Successfully processed {key}: {len(embeddings_data)} embeddings created")
        return embeddings_data
    
    except Exception as e:
        print(f"Error processing file {key}: {str(e)}")
        raise


def handler(event, context):
    """
    Lambda handler to initialize knowledge base embeddings.
    
    This function processes all knowledge base files in S3, generates embeddings,
    stores them in DynamoDB, and builds a FAISS index for similarity search.
    
    Requirements: 5.1, 5.2, 5.4, 6.6, 6.7, 17.3, 18.2
    
    Event format:
    {
        "files": ["diabetes.txt", "blood-pressure.txt", ...] (optional),
        "build_faiss_index": true (optional, default: true)
    }
    
    If no files specified, processes all .txt files in knowledge-base/ prefix.
    """
    print(json.dumps({
        'event': 'kb_embedding_start',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': {
            'bucket': KNOWLEDGE_BASE_BUCKET,
            'table': EMBEDDINGS_TABLE
        }
    }))
    
    try:
        # Get list of files to process
        files_to_process = event.get('files', [])
        build_faiss = event.get('build_faiss_index', True)
        
        if not files_to_process:
            # List all .txt files in knowledge-base/ prefix
            print("No files specified, listing all knowledge base files...")
            response = s3_client.list_objects_v2(
                Bucket=KNOWLEDGE_BASE_BUCKET,
                Prefix='knowledge-base/'
            )
            
            if 'Contents' in response:
                files_to_process = [
                    obj['Key'] for obj in response['Contents']
                    if obj['Key'].endswith('.txt')
                ]
            else:
                print("No knowledge base files found in S3")
                return {
                    'statusCode': 404,
                    'body': json.dumps({
                        'message': 'No knowledge base files found',
                        'bucket': KNOWLEDGE_BASE_BUCKET
                    })
                }
        else:
            # Prepend prefix if not already present
            files_to_process = [
                f"knowledge-base/{f}" if not f.startswith('knowledge-base/') else f
                for f in files_to_process
            ]
        
        print(f"Processing {len(files_to_process)} knowledge base files")
        
        # Process each file
        all_embeddings = []
        processed_files = []
        failed_files = []
        
        for file_key in files_to_process:
            try:
                embeddings = process_knowledge_base_file(KNOWLEDGE_BASE_BUCKET, file_key)
                all_embeddings.extend(embeddings)
                processed_files.append(file_key)
            except Exception as e:
                print(f"Failed to process {file_key}: {str(e)}")
                failed_files.append({
                    'file': file_key,
                    'error': str(e)
                })
        
        # Build FAISS index if requested and embeddings were created
        faiss_result = None
        if build_faiss and all_embeddings:
            try:
                print("Building FAISS index for knowledge base...")
                from faiss_utils import build_and_persist_knowledge_base_index
                faiss_result = build_and_persist_knowledge_base_index()
                print(f"FAISS index built successfully: {faiss_result}")
            except Exception as e:
                print(f"Warning: Failed to build FAISS index: {str(e)}")
                # Don't fail the entire operation if FAISS indexing fails
                faiss_result = {'error': str(e)}
        
        # Log completion
        print(json.dumps({
            'event': 'kb_embedding_complete',
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_files': len(files_to_process),
                'processed_files': len(processed_files),
                'failed_files': len(failed_files),
                'total_embeddings': len(all_embeddings),
                'faiss_index_built': faiss_result is not None and 'error' not in faiss_result
            }
        }))
        
        response_body = {
            'message': 'Knowledge base embedding completed',
            'processed_files': processed_files,
            'failed_files': failed_files,
            'total_embeddings': len(all_embeddings),
            'embedding_ids': [emb['embeddingId'] for emb in all_embeddings[:10]]  # First 10 for reference
        }
        
        if faiss_result:
            response_body['faiss_index'] = faiss_result
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }
    
    except Exception as e:
        print(f"Error in knowledge base embedding handler: {str(e)}")
        print(json.dumps({
            'event': 'kb_embedding_error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing knowledge base',
                'error': str(e)
            })
        }
