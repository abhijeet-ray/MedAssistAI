# MedAssist Extraction Lambda Function

## Overview

The Extraction Lambda function is a critical component of the MedAssist AI System's document processing pipeline. It extracts text and medical entities from uploaded medical documents (PDFs and images) using AWS AI services.

## Features

### Text Extraction
- **PDF Documents**: Uses AWS Textract to extract text from PDF files (Requirement 3.1)
- **Image Documents**: Uses AWS Textract to extract text from JPEG and PNG images (Requirement 3.2)
- **Image Analysis**: Uses AWS Rekognition to detect visual elements in images (Requirement 3.3)

### Medical Entity Extraction
Uses AWS Comprehend Medical to identify and extract:
- **Medications**: Drug names and prescriptions (Requirement 4.2)
- **Medical Conditions**: Diseases and diagnoses (Requirement 4.3)
- **Test Results**: Lab results and clinical tests (Requirement 4.4)
- **Dosage Information**: Medication dosages and frequencies (Requirement 4.5)

### Data Storage
- Stores extracted text in DynamoDB for session persistence (Requirement 3.5)
- Stores medical entities with confidence scores
- Stores image analysis labels (when applicable)

### Pipeline Integration
- Triggered asynchronously by the Upload Lambda
- Triggers the Embedding Lambda upon successful extraction
- Logs all operations to CloudWatch (Requirement 19.3)

## Event Structure

The function expects the following event structure:

```json
{
  "documentId": "uuid",
  "sessionId": "uuid",
  "s3Bucket": "bucket-name",
  "s3Key": "sessions/{sessionId}/documents/{documentId}.{ext}",
  "contentType": "application/pdf|image/jpeg|image/png"
}
```

## Response Structure

### Success Response (200)
```json
{
  "statusCode": 200,
  "body": {
    "documentId": "uuid",
    "status": "extracted",
    "message": "Text and entities extracted successfully",
    "metrics": {
      "text_length": 1234,
      "entities_count": 5,
      "labels_count": 3
    }
  }
}
```

### Extraction Failure (400)
```json
{
  "statusCode": 400,
  "body": {
    "error": {
      "code": "EXTRACTION_FAILED",
      "message": "We couldn't read your document. Please ensure it's a clear, readable file and try again.",
      "retryable": true,
      "timestamp": "ISO-8601"
    }
  }
}
```

### Server Error (500)
```json
{
  "statusCode": 500,
  "body": {
    "error": {
      "code": "EXTRACTION_FAILED",
      "message": "We couldn't read your document. Please ensure it's a clear, readable file and try again.",
      "retryable": true,
      "timestamp": "ISO-8601"
    }
  }
}
```

## Environment Variables

- `DOCUMENT_TABLE`: DynamoDB table name for document metadata
- `EMBEDDING_LAMBDA`: Name of the Embedding Lambda function to trigger

## AWS Services Used

1. **AWS Textract**: Document text extraction
2. **AWS Rekognition**: Image label detection
3. **AWS Comprehend Medical**: Medical entity extraction
4. **AWS DynamoDB**: Metadata storage
5. **AWS Lambda**: Trigger Embedding Lambda
6. **AWS CloudWatch**: Logging and monitoring

## Error Handling

The function implements comprehensive error handling:

- **Empty Text Extraction**: Returns user-friendly error message (Requirement 3.4)
- **Service Failures**: Logs errors and returns appropriate status codes
- **Missing Parameters**: Validates all required event parameters
- **Non-Critical Failures**: Rekognition failures don't block extraction

All errors are logged to CloudWatch with detailed context for debugging while returning user-friendly messages to the frontend (Requirement 21.6).

## CloudWatch Logging

The function logs the following events:

- `extraction_started`: When processing begins
- `pdf_text_extracted`: PDF text extraction completion
- `image_text_extracted`: Image text extraction completion
- `image_analyzed`: Rekognition analysis completion
- `medical_entities_extracted`: Entity extraction completion
- `extraction_completed`: Full extraction completion with metrics
- `embedding_triggered`: Embedding Lambda invocation
- `extraction_error`: Any errors during processing

## Testing

Unit tests are provided in `test_extraction.py`:

```bash
# Run tests
python -m pytest test_extraction.py -v

# Run with coverage
python -m pytest test_extraction.py --cov=extraction --cov-report=html
```

### Test Coverage

- PDF text extraction (Requirement 3.1)
- Image text extraction (Requirement 3.2)
- Image analysis with Rekognition (Requirement 3.3)
- Empty text error handling (Requirement 3.4)
- Medical entity extraction (Requirements 4.1-4.5)
- CloudWatch logging (Requirement 19.3)
- Missing parameter validation

## Dependencies

See `requirements.txt`:
- `boto3>=1.34.0`: AWS SDK for Python

## Integration

### Upstream
- Triggered by: **Upload Lambda** (asynchronous invocation)
- Input: Document metadata and S3 location

### Downstream
- Triggers: **Embedding Lambda** (asynchronous invocation)
- Output: Extracted text and medical entities

## Performance Considerations

- **Textract Limits**: Handles documents up to AWS Textract limits
- **Comprehend Medical Limits**: Splits text into 20,000 character chunks
- **Asynchronous Processing**: Non-blocking invocations for pipeline efficiency
- **Error Recovery**: Graceful degradation for non-critical failures

## Security

- Uses IAM roles with least privilege access
- Does not log sensitive medical information
- Encrypts data at rest in DynamoDB
- Encrypts data in transit with TLS 1.2+

## Requirements Validated

This implementation validates the following requirements:
- 3.1: PDF text extraction with AWS Textract
- 3.2: Image text extraction with AWS Textract
- 3.3: Image analysis with AWS Rekognition
- 3.4: Extraction error handling
- 3.5: Session text persistence
- 4.1: Medical entity extraction with Comprehend Medical
- 4.2: Medication extraction
- 4.3: Medical condition extraction
- 4.4: Test result extraction
- 4.5: Dosage information extraction
- 19.3: CloudWatch logging of extraction metrics
