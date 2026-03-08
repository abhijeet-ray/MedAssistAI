"""
FAISS Index Utilities for Knowledge Base Embeddings

This module provides utilities for creating and managing FAISS indices
for the knowledge base embeddings.

Requirements: 18.2
"""
import json
import os
import boto3
import numpy as np
from typing import List, Dict
import pickle

try:
    import faiss
except ImportError:
    print("FAISS not available in this environment")
    faiss = None

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Environment variables
KNOWLEDGE_BASE_BUCKET = os.environ.get('KNOWLEDGE_BASE_BUCKET')
EMBEDDINGS_TABLE = os.environ.get('EMBEDDINGS_TABLE')
FAISS_INDEX_KEY = 'faiss-indices/knowledge_base_index.faiss'
FAISS_METADATA_KEY = 'faiss-indices/knowledge_base_metadata.pkl'


def load_embeddings_from_dynamodb(source: str = 'knowledge_base') -> List[Dict]:
    """
    Load all embeddings for a specific source from DynamoDB.
    
    Args:
        source: Source type to filter ('knowledge_base' or 'document')
    
    Returns:
        List of embedding dictionaries
    """
    table = dynamodb.Table(EMBEDDINGS_TABLE)
    embeddings = []
    
    try:
        # Scan table for knowledge base embeddings
        # Note: In production, consider using GSI for better performance
        response = table.scan(
            FilterExpression='#src = :source',
            ExpressionAttributeNames={'#src': 'source'},
            ExpressionAttributeValues={':source': source}
        )
        
        embeddings.extend(response.get('Items', []))
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='#src = :source',
                ExpressionAttributeNames={'#src': 'source'},
                ExpressionAttributeValues={':source': source},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            embeddings.extend(response.get('Items', []))
        
        print(f"Loaded {len(embeddings)} embeddings from DynamoDB for source: {source}")
        return embeddings
    
    except Exception as e:
        print(f"Error loading embeddings from DynamoDB: {str(e)}")
        raise


def create_faiss_index(embeddings: List[Dict], dimension: int = 1536) -> tuple:
    """
    Create a FAISS index from embeddings.
    
    Requirements: 18.2
    
    Args:
        embeddings: List of embedding dictionaries
        dimension: Dimension of embedding vectors (Titan default: 1536)
    
    Returns:
        Tuple of (faiss_index, metadata_list)
    """
    if not faiss:
        raise ImportError("FAISS library not available")
    
    if not embeddings:
        raise ValueError("No embeddings provided")
    
    print(f"Creating FAISS index with {len(embeddings)} embeddings, dimension {dimension}")
    
    # Create FAISS index using cosine similarity (normalized L2)
    # IndexFlatIP for inner product (cosine similarity with normalized vectors)
    index = faiss.IndexFlatIP(dimension)
    
    # Prepare vectors and metadata
    vectors = []
    metadata = []
    
    for emb in embeddings:
        # Extract embedding vector
        vector = emb.get('embedding')
        if not vector:
            print(f"Warning: No embedding vector found for {emb.get('embeddingId')}")
            continue
        
        # Convert to numpy array and normalize for cosine similarity
        vec_array = np.array(vector, dtype=np.float32)
        
        # Normalize vector for cosine similarity
        norm = np.linalg.norm(vec_array)
        if norm > 0:
            vec_array = vec_array / norm
        
        vectors.append(vec_array)
        
        # Store metadata for retrieval
        metadata.append({
            'embeddingId': emb.get('embeddingId'),
            'documentId': emb.get('documentId'),
            'chunkIndex': emb.get('chunkIndex'),
            'chunkText': emb.get('chunkText'),
            'topic': emb.get('topic'),
            'source': emb.get('source')
        })
    
    # Convert to numpy array
    vectors_array = np.array(vectors, dtype=np.float32)
    
    # Add vectors to index
    index.add(vectors_array)
    
    print(f"FAISS index created with {index.ntotal} vectors")
    
    return index, metadata


def save_faiss_index_to_s3(index, metadata: List[Dict], bucket: str = None, 
                           index_key: str = None, metadata_key: str = None) -> Dict:
    """
    Save FAISS index and metadata to S3.
    
    Requirements: 18.2
    
    Args:
        index: FAISS index object
        metadata: List of metadata dictionaries
        bucket: S3 bucket name (defaults to KNOWLEDGE_BASE_BUCKET)
        index_key: S3 key for index file
        metadata_key: S3 key for metadata file
    
    Returns:
        Dictionary with S3 locations
    """
    if not faiss:
        raise ImportError("FAISS library not available")
    
    bucket = bucket or KNOWLEDGE_BASE_BUCKET
    index_key = index_key or FAISS_INDEX_KEY
    metadata_key = metadata_key or FAISS_METADATA_KEY
    
    try:
        # Save FAISS index to temporary file
        temp_index_path = '/tmp/faiss_index.faiss'
        faiss.write_index(index, temp_index_path)
        
        # Upload index to S3
        with open(temp_index_path, 'rb') as f:
            s3_client.put_object(
                Bucket=bucket,
                Key=index_key,
                Body=f.read(),
                ContentType='application/octet-stream'
            )
        
        print(f"FAISS index uploaded to s3://{bucket}/{index_key}")
        
        # Save metadata to temporary file
        temp_metadata_path = '/tmp/faiss_metadata.pkl'
        with open(temp_metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        # Upload metadata to S3
        with open(temp_metadata_path, 'rb') as f:
            s3_client.put_object(
                Bucket=bucket,
                Key=metadata_key,
                Body=f.read(),
                ContentType='application/octet-stream'
            )
        
        print(f"FAISS metadata uploaded to s3://{bucket}/{metadata_key}")
        
        return {
            'index_location': f"s3://{bucket}/{index_key}",
            'metadata_location': f"s3://{bucket}/{metadata_key}",
            'vector_count': index.ntotal
        }
    
    except Exception as e:
        print(f"Error saving FAISS index to S3: {str(e)}")
        raise


def load_faiss_index_from_s3(bucket: str = None, index_key: str = None, 
                             metadata_key: str = None) -> tuple:
    """
    Load FAISS index and metadata from S3.
    
    Args:
        bucket: S3 bucket name
        index_key: S3 key for index file
        metadata_key: S3 key for metadata file
    
    Returns:
        Tuple of (faiss_index, metadata_list)
    """
    if not faiss:
        raise ImportError("FAISS library not available")
    
    bucket = bucket or KNOWLEDGE_BASE_BUCKET
    index_key = index_key or FAISS_INDEX_KEY
    metadata_key = metadata_key or FAISS_METADATA_KEY
    
    try:
        # Download index from S3
        temp_index_path = '/tmp/faiss_index.faiss'
        s3_client.download_file(bucket, index_key, temp_index_path)
        
        # Load FAISS index
        index = faiss.read_index(temp_index_path)
        print(f"FAISS index loaded from s3://{bucket}/{index_key} with {index.ntotal} vectors")
        
        # Download metadata from S3
        temp_metadata_path = '/tmp/faiss_metadata.pkl'
        s3_client.download_file(bucket, metadata_key, temp_metadata_path)
        
        # Load metadata
        with open(temp_metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"FAISS metadata loaded with {len(metadata)} entries")
        
        return index, metadata
    
    except Exception as e:
        print(f"Error loading FAISS index from S3: {str(e)}")
        raise


def build_and_persist_knowledge_base_index() -> Dict:
    """
    Build FAISS index for knowledge base embeddings and persist to S3.
    
    This is the main function to call after embeddings are stored in DynamoDB.
    
    Requirements: 18.2
    
    Returns:
        Dictionary with index information
    """
    print("Building FAISS index for knowledge base...")
    
    # Load embeddings from DynamoDB
    embeddings = load_embeddings_from_dynamodb(source='knowledge_base')
    
    if not embeddings:
        raise ValueError("No knowledge base embeddings found in DynamoDB")
    
    # Create FAISS index
    index, metadata = create_faiss_index(embeddings)
    
    # Save to S3
    result = save_faiss_index_to_s3(index, metadata)
    
    print("Knowledge base FAISS index built and persisted successfully")
    
    return result
