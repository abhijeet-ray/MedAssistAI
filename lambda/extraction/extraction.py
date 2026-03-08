"""
MedAssist Extraction Lambda Function
Extracts text and medical entities from documents
"""
import json
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')
rekognition_client = boto3.client('rekognition')
comprehend_medical_client = boto3.client('comprehendmedical')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables (with defaults for testing)
DOCUMENT_TABLE = os.environ.get('DOCUMENT_TABLE', 'MedAssist-Documents')
EMBEDDING_LAMBDA = os.environ.get('EMBEDDING_LAMBDA', 'MedAssist-Embedding')

# Initialize DynamoDB table (will be mocked in tests)
try:
    document_table = dynamodb.Table(DOCUMENT_TABLE)
except Exception:
    document_table = None

def extract_text_from_pdf(bucket, key):
    """
    Extract text from PDF using AWS Textract
    
    Requirements: 3.1
    """
    try:
        # Try DetectDocumentText first (faster, synchronous)
        try:
            response = textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            # Extract text from blocks
            text_blocks = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_blocks.append(block.get('Text', ''))
            
            extracted_text = '\n'.join(text_blocks)
            
            print(json.dumps({
                'event': 'pdf_text_extracted',
                'method': 'detect_document_text',
                'blocks_count': len(text_blocks),
                'text_length': len(extracted_text),
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            return extracted_text
            
        except ClientError as detect_error:
            # If DetectDocumentText fails with UnsupportedDocumentException,
            # try AnalyzeDocument as fallback (works with more PDF formats)
            if detect_error.response['Error']['Code'] == 'UnsupportedDocumentException':
                print(json.dumps({
                    'event': 'pdf_detection_failed_trying_analyze',
                    'error': str(detect_error),
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
                # Try AnalyzeDocument with TABLES feature (more robust)
                response = textract_client.analyze_document(
                    Document={
                        'S3Object': {
                            'Bucket': bucket,
                            'Name': key
                        }
                    },
                    FeatureTypes=['TABLES', 'FORMS']
                )
                
                # Extract text from blocks
                text_blocks = []
                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'LINE':
                        text_blocks.append(block.get('Text', ''))
                
                extracted_text = '\n'.join(text_blocks)
                
                print(json.dumps({
                    'event': 'pdf_text_extracted',
                    'method': 'analyze_document',
                    'blocks_count': len(text_blocks),
                    'text_length': len(extracted_text),
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
                return extracted_text
            else:
                # Re-raise if it's a different error
                raise
        
    except Exception as e:
        print(json.dumps({
            'event': 'pdf_extraction_error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))
        raise

def extract_text_from_image(bucket, key):
    """
    Extract text from image using AWS Textract
    
    Requirements: 3.2
    """
    try:
        # Detect text in image
        response = textract_client.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # Extract text from blocks
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block.get('Text', ''))
        
        extracted_text = '\n'.join(text_blocks)
        
        print(json.dumps({
            'event': 'image_text_extracted',
            'blocks_count': len(text_blocks),
            'text_length': len(extracted_text),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        return extracted_text
        
    except Exception as e:
        print(json.dumps({
            'event': 'image_text_extraction_error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))
        raise

def analyze_image_with_rekognition(bucket, key):
    """
    Analyze image using AWS Rekognition
    
    Requirements: 3.3
    """
    try:
        # Detect labels in image
        response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=10,
            MinConfidence=70
        )
        
        labels = [
            {
                'name': label['Name'],
                'confidence': label['Confidence']
            }
            for label in response.get('Labels', [])
        ]
        
        print(json.dumps({
            'event': 'image_analyzed',
            'labels_count': len(labels),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        return labels
        
    except Exception as e:
        print(json.dumps({
            'event': 'image_analysis_error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))
        # Non-critical error, return empty list
        return []

def extract_medical_entities(text):
    """
    Extract medical entities using AWS Comprehend Medical
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    try:
        # Comprehend Medical has a 20,000 character limit
        # Split text if needed
        max_chars = 20000
        entities = []
        
        for i in range(0, len(text), max_chars):
            chunk = text[i:i + max_chars]
            
            # Detect entities
            response = comprehend_medical_client.detect_entities_v2(
                Text=chunk
            )
            
            # Extract relevant entity types
            for entity in response.get('Entities', []):
                entity_type = entity.get('Category')
                entity_text = entity.get('Text')
                score = entity.get('Score', 0)
                
                # Map to our entity types (Req 4.2, 4.3, 4.4, 4.5)
                if entity_type in ['MEDICATION', 'MEDICAL_CONDITION', 'TEST_TREATMENT_PROCEDURE', 'PROTECTED_HEALTH_INFORMATION']:
                    # Determine specific type
                    if entity_type == 'MEDICATION':
                        specific_type = 'MEDICATION'
                    elif entity_type == 'MEDICAL_CONDITION':
                        specific_type = 'CONDITION'
                    elif entity_type == 'TEST_TREATMENT_PROCEDURE':
                        specific_type = 'TEST_RESULT'
                    else:
                        continue
                    
                    # Check for dosage information in attributes
                    dosage_info = None
                    for attr in entity.get('Attributes', []):
                        if attr.get('Type') in ['DOSAGE', 'STRENGTH', 'FREQUENCY']:
                            dosage_info = attr.get('Text')
                            break
                    
                    entity_data = {
                        'type': specific_type,
                        'text': entity_text,
                        'score': score
                    }
                    
                    if dosage_info:
                        entity_data['dosage'] = dosage_info
                    
                    entities.append(entity_data)
        
        print(json.dumps({
            'event': 'medical_entities_extracted',
            'entities_count': len(entities),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        return entities
        
    except Exception as e:
        print(json.dumps({
            'event': 'entity_extraction_error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))
        # Return empty list on error
        return []

def handler(event, context):
    """
    Extract text and medical entities from documents
    
    Requirements: 3.1, 3.2, 3.3, 3.5, 4.1-4.5, 19.3
    """
    try:
        # Parse event
        document_id = event.get('documentId')
        session_id = event.get('sessionId')
        s3_bucket = event.get('s3Bucket')
        s3_key = event.get('s3Key')
        content_type = event.get('contentType')
        
        if not all([document_id, session_id, s3_bucket, s3_key, content_type]):
            raise ValueError('Missing required event parameters')
        
        print(json.dumps({
            'event': 'extraction_started',
            'documentId': document_id,
            'sessionId': session_id,
            'contentType': content_type,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Extract text based on content type
        extracted_text = ''
        image_labels = []
        
        if content_type == 'application/pdf':
            # Extract text from PDF (Req 3.1)
            extracted_text = extract_text_from_pdf(s3_bucket, s3_key)
        elif content_type in ['image/jpeg', 'image/png']:
            # Extract text from image (Req 3.2)
            extracted_text = extract_text_from_image(s3_bucket, s3_key)
            # Analyze image with Rekognition (Req 3.3)
            image_labels = analyze_image_with_rekognition(s3_bucket, s3_key)
        else:
            raise ValueError(f'Unsupported content type: {content_type}')
        
        # Check if extraction was successful (Req 3.4)
        if not extracted_text or len(extracted_text.strip()) == 0:
            # Store failed status with sessionId as PK
            document_table.put_item(
                Item={
                    'PK': session_id,
                    'SK': f'DOC#{document_id}',
                    'sessionId': session_id,
                    'documentId': document_id,
                    'status': 'extraction_failed',
                    'errorMessage': 'We couldn\'t read your document. Please ensure it\'s a clear, readable file and try again.',
                    'extractedAt': datetime.utcnow().isoformat()
                }
            )
            
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': {
                        'code': 'EXTRACTION_FAILED',
                        'message': 'We couldn\'t read your document. Please ensure it\'s a clear, readable file and try again.',
                        'retryable': True,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })
            }
        
        # Extract medical entities (Req 4.1-4.5)
        medical_entities = extract_medical_entities(extracted_text)
        
        # Store extracted text and entities in DynamoDB (Req 3.5)
        # Store with sessionId as PK for easy retrieval by RAG Lambda
        timestamp = datetime.utcnow().isoformat()
        document_table.put_item(
            Item={
                'PK': session_id,
                'SK': f'DOC#{document_id}',
                'sessionId': session_id,
                'documentId': document_id,
                'extractedText': extracted_text,
                'medicalEntities': medical_entities,
                'imageLabels': image_labels,
                'status': 'extracted',
                'extractedAt': timestamp
            }
        )
        
        # Log extraction metrics to CloudWatch (Req 19.3)
        print(json.dumps({
            'event': 'extraction_completed',
            'documentId': document_id,
            'sessionId': session_id,
            'metrics': {
                'text_length': len(extracted_text),
                'entities_count': len(medical_entities),
                'labels_count': len(image_labels)
            },
            'timestamp': timestamp
        }))
        
        # Trigger EmbeddingLambda with extracted data
        try:
            lambda_client.invoke(
                FunctionName=EMBEDDING_LAMBDA,
                InvocationType='Event',  # Asynchronous invocation
                Payload=json.dumps({
                    'documentId': document_id,
                    'sessionId': session_id,
                    'extractedText': extracted_text,
                    'medicalEntities': medical_entities
                })
            )
            print(json.dumps({
                'event': 'embedding_triggered',
                'documentId': document_id,
                'timestamp': datetime.utcnow().isoformat()
            }))
        except Exception as invoke_error:
            # Log error but don't fail the extraction
            print(json.dumps({
                'event': 'embedding_trigger_failed',
                'documentId': document_id,
                'error': str(invoke_error),
                'timestamp': datetime.utcnow().isoformat()
            }))
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'documentId': document_id,
                'status': 'extracted',
                'message': 'Text and entities extracted successfully',
                'metrics': {
                    'text_length': len(extracted_text),
                    'entities_count': len(medical_entities),
                    'labels_count': len(image_labels)
                }
            })
        }
        
    except Exception as e:
        # Error handling (Req 3.4, 21.2)
        error_message = str(e)
        
        # Provide user-friendly error message based on error type
        if 'UnsupportedDocumentException' in error_message:
            user_message = 'This PDF format is not supported. Please try converting your PDF to a standard format or upload it as an image (JPEG/PNG).'
        else:
            user_message = 'We couldn\'t read your document. Please ensure it\'s a clear, readable file and try again.'
        
        print(json.dumps({
            'event': 'extraction_error',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Update document status if we have document_id
        if 'document_id' in locals() and 'session_id' in locals():
            try:
                document_table.put_item(
                    Item={
                        'PK': session_id,
                        'SK': f'DOC#{document_id}',
                        'sessionId': session_id,
                        'documentId': document_id,
                        'status': 'extraction_failed',
                        'errorMessage': user_message,
                        'extractedAt': datetime.utcnow().isoformat()
                    }
                )
            except Exception:
                pass
        
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': {
                    'code': 'EXTRACTION_FAILED',
                    'message': user_message,
                    'retryable': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        }
