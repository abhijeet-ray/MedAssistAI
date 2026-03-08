"""
Shared Bedrock Utilities for MedAssist AI System
Provides resilient embedding generation with retry logic, caching, and throttling protection.

This module implements:
- Exponential backoff with jitter for Bedrock API calls
- Request queueing to prevent overload
- Embedding caching for repeated queries
- Comprehensive error handling and logging
"""
import json
import time
import random
import hashlib
import boto3
from typing import List, Dict, Optional
from datetime import datetime
from botocore.exceptions import ClientError

# AWS clients
bedrock_runtime = None
dynamodb = None

# Cache for embeddings (in-memory for Lambda execution context reuse)
EMBEDDING_CACHE = {}
CACHE_MAX_SIZE = 100  # Maximum number of cached embeddings

# Retry configuration
MAX_RETRIES = 5
BASE_DELAY = 1.0  # Base delay in seconds
MAX_DELAY = 32.0  # Maximum delay in seconds
JITTER_RANGE = 0.5  # Random jitter range (±50%)

# Rate limiting
INTER_REQUEST_DELAY = 0.2  # 200ms delay between requests
LAST_REQUEST_TIME = 0


def initialize_clients(region: str = 'us-east-1'):
    """
    Initialize AWS clients (call once per Lambda execution context).
    
    Args:
        region: AWS region name
    """
    global bedrock_runtime, dynamodb
    
    if bedrock_runtime is None:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
    
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb', region_name=region)


def get_text_hash(text: str) -> str:
    """
    Generate a hash for text to use as cache key.
    
    Args:
        text: Input text
    
    Returns:
        SHA256 hash of the text
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def get_cached_embedding(text: str) -> Optional[List[float]]:
    """
    Retrieve embedding from cache if available.
    
    Args:
        text: Input text
    
    Returns:
        Cached embedding vector or None if not found
    """
    text_hash = get_text_hash(text)
    
    if text_hash in EMBEDDING_CACHE:
        print(f"[CACHE HIT] Retrieved embedding from cache for text hash: {text_hash[:16]}...")
        return EMBEDDING_CACHE[text_hash]
    
    return None


def cache_embedding(text: str, embedding: List[float]) -> None:
    """
    Store embedding in cache with LRU eviction.
    
    Args:
        text: Input text
        embedding: Embedding vector to cache
    """
    global EMBEDDING_CACHE
    
    text_hash = get_text_hash(text)
    
    # Implement simple LRU: if cache is full, remove oldest entry
    if len(EMBEDDING_CACHE) >= CACHE_MAX_SIZE:
        # Remove first (oldest) entry
        oldest_key = next(iter(EMBEDDING_CACHE))
        del EMBEDDING_CACHE[oldest_key]
        print(f"[CACHE EVICT] Removed oldest entry, cache size: {len(EMBEDDING_CACHE)}")
    
    EMBEDDING_CACHE[text_hash] = embedding
    print(f"[CACHE STORE] Cached embedding for text hash: {text_hash[:16]}..., cache size: {len(EMBEDDING_CACHE)}")


def calculate_backoff_delay(attempt: int, base_delay: float = BASE_DELAY, max_delay: float = MAX_DELAY) -> float:
    """
    Calculate exponential backoff delay with jitter.
    
    Formula: min(base_delay * 2^attempt, max_delay) + random_jitter
    
    Args:
        attempt: Current retry attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        Delay in seconds with jitter applied
    """
    # Exponential backoff: 2^attempt
    exponential_delay = base_delay * (2 ** attempt)
    
    # Cap at maximum delay
    delay = min(exponential_delay, max_delay)
    
    # Add random jitter (±50% of delay)
    jitter = delay * JITTER_RANGE * (2 * random.random() - 1)
    final_delay = delay + jitter
    
    # Ensure non-negative
    return max(0, final_delay)


def rate_limit_delay() -> None:
    """
    Enforce rate limiting by adding delay between requests.
    Prevents overwhelming Bedrock API with rapid successive calls.
    """
    global LAST_REQUEST_TIME
    
    current_time = time.time()
    time_since_last_request = current_time - LAST_REQUEST_TIME
    
    if time_since_last_request < INTER_REQUEST_DELAY:
        sleep_time = INTER_REQUEST_DELAY - time_since_last_request
        print(f"[RATE LIMIT] Sleeping for {sleep_time:.3f}s to avoid overwhelming API")
        time.sleep(sleep_time)
    
    LAST_REQUEST_TIME = time.time()


def generate_embedding_with_retry(
    text: str,
    model_id: str = 'amazon.titan-embed-text-v1',
    max_retries: int = MAX_RETRIES,
    use_cache: bool = True
) -> List[float]:
    """
    Generate embedding vector with exponential backoff retry logic.
    
    This function implements:
    - Caching for repeated queries
    - Rate limiting between requests
    - Exponential backoff with jitter on throttling
    - Comprehensive error logging
    - Graceful degradation
    
    Args:
        text: Input text to embed
        model_id: Bedrock model ID (default: amazon.titan-embed-text-v1)
        max_retries: Maximum number of retry attempts
        use_cache: Whether to use embedding cache
    
    Returns:
        Embedding vector as list of floats
    
    Raises:
        Exception: If all retries are exhausted or non-retryable error occurs
    """
    # Initialize clients if not already done
    initialize_clients()
    
    # Check cache first
    if use_cache:
        cached_embedding = get_cached_embedding(text)
        if cached_embedding is not None:
            return cached_embedding
    
    # Enforce rate limiting
    rate_limit_delay()
    
    # Prepare request body
    request_body = json.dumps({
        "inputText": text
    })
    
    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            print(f"[BEDROCK REQUEST] Attempt {attempt + 1}/{max_retries} for embedding generation")
            
            start_time = time.time()
            
            # Call Bedrock Titan Embeddings model
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType='application/json',
                accept='application/json',
                body=request_body
            )
            
            elapsed_time = time.time() - start_time
            
            # Parse response
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding')
            
            if not embedding:
                raise ValueError("No embedding returned from Titan model")
            
            # Log success
            print(json.dumps({
                'event': 'embedding_success',
                'attempt': attempt + 1,
                'elapsed_time_seconds': elapsed_time,
                'text_length': len(text),
                'embedding_dimension': len(embedding),
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # Cache the embedding
            if use_cache:
                cache_embedding(text, embedding)
            
            return embedding
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', '')
            
            # Check if this is a throttling error
            is_throttling = error_code in ['ThrottlingException', 'TooManyRequestsException', 'ServiceUnavailable']
            
            # Log the error
            print(json.dumps({
                'event': 'embedding_error',
                'attempt': attempt + 1,
                'error_code': error_code,
                'error_message': error_message,
                'is_throttling': is_throttling,
                'will_retry': attempt < max_retries - 1,
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # If this is the last attempt, raise the error
            if attempt >= max_retries - 1:
                print(f"[BEDROCK ERROR] Max retries ({max_retries}) exhausted for embedding generation")
                raise Exception(f"Bedrock API call failed after {max_retries} attempts: {error_message}")
            
            # If not a throttling error and not retryable, raise immediately
            if not is_throttling and error_code not in ['InternalServerError', 'ServiceUnavailable']:
                print(f"[BEDROCK ERROR] Non-retryable error: {error_code}")
                raise Exception(f"Bedrock API call failed with non-retryable error: {error_message}")
            
            # Calculate backoff delay
            delay = calculate_backoff_delay(attempt)
            
            print(json.dumps({
                'event': 'embedding_retry',
                'attempt': attempt + 1,
                'next_attempt': attempt + 2,
                'backoff_delay_seconds': delay,
                'error_code': error_code,
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # Wait before retrying
            time.sleep(delay)
        
        except Exception as e:
            # Log unexpected errors
            print(json.dumps({
                'event': 'embedding_unexpected_error',
                'attempt': attempt + 1,
                'error': str(e),
                'error_type': type(e).__name__,
                'will_retry': attempt < max_retries - 1,
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            # If this is the last attempt, raise the error
            if attempt >= max_retries - 1:
                print(f"[BEDROCK ERROR] Max retries ({max_retries}) exhausted")
                raise
            
            # Wait before retrying
            delay = calculate_backoff_delay(attempt)
            print(f"[RETRY] Waiting {delay:.2f}s before retry {attempt + 2}/{max_retries}")
            time.sleep(delay)
    
    # Should never reach here, but just in case
    raise Exception(f"Embedding generation failed after {max_retries} attempts")


def generate_embeddings_batch(
    texts: List[str],
    model_id: str = 'amazon.titan-embed-text-v1',
    max_retries: int = MAX_RETRIES,
    use_cache: bool = True,
    batch_delay: float = 0.5
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts with rate limiting between requests.
    
    Args:
        texts: List of input texts
        model_id: Bedrock model ID
        max_retries: Maximum retry attempts per text
        use_cache: Whether to use embedding cache
        batch_delay: Additional delay between batch items (seconds)
    
    Returns:
        List of embedding vectors
    
    Raises:
        Exception: If any embedding generation fails after retries
    """
    embeddings = []
    
    print(f"[BATCH] Generating embeddings for {len(texts)} texts with {batch_delay}s delay between requests")
    
    for i, text in enumerate(texts):
        print(f"[BATCH] Processing text {i + 1}/{len(texts)}")
        
        try:
            embedding = generate_embedding_with_retry(
                text=text,
                model_id=model_id,
                max_retries=max_retries,
                use_cache=use_cache
            )
            embeddings.append(embedding)
            
            # Add delay between batch items (except for last item)
            if i < len(texts) - 1:
                time.sleep(batch_delay)
        
        except Exception as e:
            print(f"[BATCH ERROR] Failed to generate embedding for text {i + 1}: {str(e)}")
            raise
    
    print(f"[BATCH] Successfully generated {len(embeddings)} embeddings")
    return embeddings


def clear_embedding_cache() -> int:
    """
    Clear the embedding cache.
    
    Returns:
        Number of entries cleared
    """
    global EMBEDDING_CACHE
    
    count = len(EMBEDDING_CACHE)
    EMBEDDING_CACHE.clear()
    
    print(f"[CACHE CLEAR] Cleared {count} cached embeddings")
    return count


def get_cache_stats() -> Dict:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    return {
        'cache_size': len(EMBEDDING_CACHE),
        'cache_max_size': CACHE_MAX_SIZE,
        'cache_utilization': len(EMBEDDING_CACHE) / CACHE_MAX_SIZE if CACHE_MAX_SIZE > 0 else 0
    }
