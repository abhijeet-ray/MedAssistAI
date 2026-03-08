# MedAssist Embedding Lambda Function

## Overview

The EmbeddingLambda function processes extracted text from medical documents, generates embeddings using Amazon Titan Embeddings, and stores them in DynamoDB and FAISS for similarity search. This Lambda is triggered by the ExtractionLambda after text extraction completes.

## Requirements

Implements the following requirements:
- **5.1**: Split text into chunks of 512 tokens or fewer
- **5.2**: Generate embeddings using Amazon Titan Embeddings
- **5.3**: Store embeddings in DynamoDB with metadata
- **5.4**: Maintain 50-token overlap between consecutive chunks
- **5.5**: Index embeddings in FAISS for similarity search
- **12.3**: Maintain document embedding vectors in vector store during session
- **17.2**: Store document embedding vectors in DynamoDB
- **18.2**: Index embeddings in FAISS
- **19.3**: Log embedding metrics to CloudWatch

## Functionality

### Text Chunking
- Uses tiktoken tokenizer for accurate token counting
- Splits text into 512-token chunks with 50-token overlap
- Reuses chunking logic from kb-embedding Lambda for consistency
- Preserves chunk metadata (start/end tokens, token count)

### Embedding Generation
- Generates embeddings using Amazon Titan Embeddings (amazon.titan-embed-text-v1)
- Produces 1536-dimensional vectors
- Handles errors gracefully with detailed logging

### Storage
- **DynamoDB**: Stores embeddings with metadata including:
  - Embedding ID and document ID
  - Session ID for session-based retrieval
  - Chunk text and index
  - Medical entities found in chunk
  - Token position metadata
- **FAISS**: Updates session-specific FAISS index for similarity search
  - Uses cosine similarity (IndexFlatIP with normalized vectors)
  - Maintains separate indices per session
  - Persists indices to S3

### Pipeline Integration
- Triggered asynchronously by ExtractionLambda
- Triggers DashboardLambda after completion
- Logs all operations to CloudWatch

## Event Format

```json
{
  "documentId": "string",
  "sessionId": "string",
  "extractedText": "string",
  "medicalEntities": [
    {
      "type": "MEDICATION|CONDITION|TEST_RESULT",
      "text": "string",
      "score": 0.95
    }
  ]
}
```

## Response Format

### Success (200)
```json
{
  "message": "Embeddings generated and stored successfully",
  "documentId": "string",
  "sessionId": "string",
  "chunk_count": 10,
  "embedding_count": 10,
  "faiss_index": {
    "status": "success",
    "index_location": "s3://bucket/faiss-indices/session_xxx_index.faiss",
    "vector_count": 10
  }
}
```

### Error (500)
```json
{
  "error": {
    "code": "EMBEDDING_FAILED",
    "message": "Failed to generate embeddings",
    "details": "error details"
  }
}
```

## Environment Variables

- `EMBEDDINGS_TABLE`: DynamoDB table name for storing embeddings
- `DASHBOARD_LAMBDA`: Name of DashboardLambda function to trigger
- `KNOWLEDGE_BASE_BUCKET`: S3 bucket for storing FAISS indices
- `AWS_REGION`: AWS region (default: us-east-1)

## Dependencies

- `boto3>=1.34.0`: AWS SDK
- `tiktoken>=0.5.0`: Token counting
- `faiss-cpu>=1.7.4`: Vector similarity search
- `numpy>=1.24.0`: Array operations

## CloudWatch Metrics

Logs the following metrics:
- Text length and token count
- Number of chunks created
- Number of embeddings generated
- FAISS index status
- Processing timestamps
- Error details with stack traces

## Error Handling

- Validates required event parameters
- Handles embedding generation failures
- Continues operation if FAISS update fails (non-critical)
- Continues operation if DashboardLambda trigger fails
- Logs all errors with stack traces to CloudWatch

## Testing

Run unit tests:
```bash
cd lambda/embedding
python -m pytest test_embedding.py -v
```

## Deployment

The Lambda is deployed as part of the MedAssist infrastructure using AWS CDK. See the main deployment documentation for details.
