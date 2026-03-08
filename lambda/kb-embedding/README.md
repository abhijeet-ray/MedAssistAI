# Knowledge Base Embedding Lambda Function

This Lambda function initializes the medical knowledge base by processing text files from S3, chunking them into appropriate sizes, generating embeddings using Amazon Titan Embeddings, and storing them in DynamoDB with FAISS indexing for efficient similarity search.

## Requirements Addressed

- **5.1**: Text chunking into 512 tokens or fewer
- **5.2**: Embedding generation using Amazon Titan Embeddings
- **5.4**: Chunk overlap of 50 tokens between consecutive chunks
- **6.6**: Knowledge base embedding generation
- **6.7**: Knowledge base embedding storage in vector store
- **17.3**: Knowledge base embedding storage in DynamoDB
- **18.2**: FAISS index creation and persistence

## Features

1. **Text Chunking**: Splits knowledge base documents into 512-token chunks with 50-token overlap
2. **Embedding Generation**: Uses Amazon Titan Embeddings (amazon.titan-embed-text-v1) to generate 1536-dimensional vectors
3. **DynamoDB Storage**: Stores embeddings with metadata in DynamoDB for persistence
4. **FAISS Indexing**: Creates and persists FAISS index to S3 for fast similarity search
5. **Batch Processing**: Processes multiple knowledge base files in a single invocation

## Environment Variables

- `KNOWLEDGE_BASE_BUCKET`: S3 bucket containing knowledge base files
- `EMBEDDINGS_TABLE`: DynamoDB table name for storing embeddings
- `AWS_REGION`: AWS region (default: us-east-1)

## Input Event Format

```json
{
  "files": ["diabetes.txt", "blood-pressure.txt"],
  "build_faiss_index": true
}
```

### Parameters

- `files` (optional): Array of filenames to process. If omitted, processes all .txt files in `knowledge-base/` prefix
- `build_faiss_index` (optional): Whether to build FAISS index after embedding (default: true)

## Output Format

```json
{
  "statusCode": 200,
  "body": {
    "message": "Knowledge base embedding completed",
    "processed_files": ["knowledge-base/diabetes.txt", "knowledge-base/blood-pressure.txt"],
    "failed_files": [],
    "total_embeddings": 245,
    "embedding_ids": ["uuid1", "uuid2", "..."],
    "faiss_index": {
      "index_location": "s3://bucket/faiss-indices/knowledge_base_index.faiss",
      "metadata_location": "s3://bucket/faiss-indices/knowledge_base_metadata.pkl",
      "vector_count": 245
    }
  }
}
```

## Knowledge Base Files

The function expects knowledge base files to be stored in S3 with the following structure:

```
s3://KNOWLEDGE_BASE_BUCKET/
  knowledge-base/
    diabetes.txt
    blood-pressure.txt
    cholesterol.txt
    heart-health.txt
    basic-health.txt
```

## DynamoDB Schema

Embeddings are stored with the following structure:

```json
{
  "PK": "EMB#<embedding-id>",
  "SK": "CHUNK#<chunk-index>",
  "embeddingId": "uuid",
  "documentId": "KB_diabetes",
  "sessionId": "KNOWLEDGE_BASE",
  "chunkIndex": 0,
  "chunkText": "Full text of the chunk...",
  "embedding": [0.123, 0.456, ...],
  "source": "knowledge_base",
  "topic": "diabetes",
  "metadata": {
    "startToken": 0,
    "endToken": 512,
    "tokenCount": 512,
    "filename": "diabetes.txt"
  },
  "createdAt": "2024-01-01T00:00:00.000Z"
}
```

## FAISS Index

The FAISS index is stored in S3 at:
- Index file: `s3://KNOWLEDGE_BASE_BUCKET/faiss-indices/knowledge_base_index.faiss`
- Metadata file: `s3://KNOWLEDGE_BASE_BUCKET/faiss-indices/knowledge_base_metadata.pkl`

The index uses `IndexFlatIP` (inner product) with normalized vectors for cosine similarity search.

## Dependencies

- `boto3`: AWS SDK for Python
- `tiktoken`: OpenAI's tokenizer for accurate token counting
- `faiss-cpu`: Facebook AI Similarity Search library
- `numpy`: Numerical computing library

## Usage

### Manual Invocation

```bash
aws lambda invoke \
  --function-name KnowledgeBaseEmbeddingFunction \
  --payload '{"files": ["diabetes.txt"], "build_faiss_index": true}' \
  response.json
```

### Process All Files

```bash
aws lambda invoke \
  --function-name KnowledgeBaseEmbeddingFunction \
  --payload '{}' \
  response.json
```

## Error Handling

The function includes comprehensive error handling:
- Individual file processing errors don't stop the entire batch
- Failed files are reported in the response
- FAISS indexing failures are logged but don't fail the embedding storage
- All errors are logged to CloudWatch with detailed context

## Performance Considerations

- Processing time depends on the number and size of knowledge base files
- Each chunk requires an API call to Bedrock for embedding generation
- DynamoDB writes are batched where possible
- FAISS index building is done in-memory and then persisted to S3

## Monitoring

The function logs the following events to CloudWatch:
- `kb_embedding_start`: Function invocation start
- `kb_embedding_complete`: Successful completion with summary
- `kb_embedding_error`: Error during processing

## Testing

To test the function locally, ensure you have:
1. AWS credentials configured
2. Required environment variables set
3. Knowledge base files uploaded to S3
4. DynamoDB table created

## Notes

- The function uses `cl100k_base` tokenizer (GPT-4 tokenizer) for consistent token counting
- Embeddings are normalized before adding to FAISS index for cosine similarity
- The function is idempotent - running it multiple times will overwrite existing embeddings
- Consider running this function on a schedule or after knowledge base updates
