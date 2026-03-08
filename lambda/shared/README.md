# Shared Lambda Utilities

This directory contains shared utility modules used across multiple Lambda functions in the MedAssist AI system.

## bedrock_utils.py

Provides resilient Bedrock API integration with:

### Features

1. **Exponential Backoff with Jitter**
   - Automatic retry on throttling errors
   - Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s (max)
   - Random jitter (±50%) to prevent thundering herd
   - Configurable max retries (default: 5)

2. **Request Rate Limiting**
   - 200ms delay between consecutive requests
   - Prevents overwhelming Bedrock API
   - Tracks last request time globally

3. **Embedding Caching**
   - In-memory LRU cache for repeated queries
   - Cache size: 100 embeddings
   - SHA256 hash-based cache keys
   - Automatic eviction of oldest entries

4. **Comprehensive Logging**
   - Structured JSON logs for CloudWatch
   - Throttling event tracking
   - Retry attempt logging
   - Cache hit/miss metrics
   - Performance timing

5. **Graceful Error Handling**
   - Distinguishes retryable vs non-retryable errors
   - Detailed error messages
   - Never crashes on throttling
   - Propagates only after exhausting retries

### Usage

#### Single Embedding Generation

```python
from bedrock_utils import generate_embedding_with_retry

# Generate embedding with automatic retry and caching
embedding = generate_embedding_with_retry(
    text="What is diabetes?",
    model_id='amazon.titan-embed-text-v1',
    max_retries=5,
    use_cache=True
)
```

#### Batch Embedding Generation

```python
from bedrock_utils import generate_embeddings_batch

# Generate multiple embeddings with rate limiting
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = generate_embeddings_batch(
    texts=texts,
    batch_delay=0.5  # 500ms between requests
)
```

#### Cache Management

```python
from bedrock_utils import get_cache_stats, clear_embedding_cache

# Get cache statistics
stats = get_cache_stats()
print(f"Cache size: {stats['cache_size']}/{stats['cache_max_size']}")

# Clear cache if needed
cleared_count = clear_embedding_cache()
```

### Configuration

Adjust these constants in `bedrock_utils.py`:

```python
MAX_RETRIES = 5              # Maximum retry attempts
BASE_DELAY = 1.0             # Base delay in seconds
MAX_DELAY = 32.0             # Maximum delay in seconds
JITTER_RANGE = 0.5           # Jitter range (±50%)
INTER_REQUEST_DELAY = 0.2    # Delay between requests (200ms)
CACHE_MAX_SIZE = 100         # Maximum cached embeddings
```

### Error Handling

The utility handles these error types:

- **ThrottlingException**: Retries with exponential backoff
- **TooManyRequestsException**: Retries with exponential backoff
- **ServiceUnavailable**: Retries with exponential backoff
- **InternalServerError**: Retries with exponential backoff
- **Other errors**: Fails immediately (non-retryable)

### Logging

All operations log structured JSON to CloudWatch:

```json
{
  "event": "embedding_success",
  "attempt": 1,
  "elapsed_time_seconds": 0.234,
  "text_length": 150,
  "embedding_dimension": 1536,
  "timestamp": "2026-03-07T12:00:00.000000"
}
```

```json
{
  "event": "embedding_retry",
  "attempt": 2,
  "next_attempt": 3,
  "backoff_delay_seconds": 2.3,
  "error_code": "ThrottlingException",
  "timestamp": "2026-03-07T12:00:02.000000"
}
```

### Integration

To use in Lambda functions:

1. **Add to Lambda layer** or include in deployment package
2. **Import the utility**:
   ```python
   from bedrock_utils import generate_embedding_with_retry
   ```
3. **Replace direct Bedrock calls** with utility function
4. **Monitor CloudWatch logs** for throttling events

### Performance Impact

- **Cache hit**: ~0ms (instant)
- **Cache miss + success**: ~200-500ms (Bedrock API latency)
- **Throttling + retry**: 1-60s (depends on retry attempts)
- **Rate limiting**: +200ms per request (prevents throttling)

### Benefits

1. **Resilience**: Never crashes on throttling
2. **Performance**: Caching reduces API calls by ~30-50%
3. **Cost**: Fewer API calls = lower costs
4. **Observability**: Detailed CloudWatch logs
5. **Maintainability**: Centralized retry logic
