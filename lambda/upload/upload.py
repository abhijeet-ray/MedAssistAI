"""
MedAssist Upload Lambda Function
Handles document upload with synchronous Textract extraction
"""
import json
import os
import base64
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
textract_client = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')

DOCUMENTS_BUCKET = os.environ['DOCUMENTS_BUCKET']
DOCUMENT_TABLE = os.environ['DOCUMENT_TABLE']

document_table = dynamodb.Table(DOCUMENT_TABLE)

ALLOWED_CONTENT_TYPES = ['application/pdf', 'image/jpeg', 'image/png']

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
}


def extract_text_from_document(bucket, key, content_type):
    """
    Extract text from document using AWS Textract synchronously
    """
    try:
        # Use DetectDocumentText for synchronous extraction
        response = textract_client.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # Extract text from LINE blocks and join with spaces
        extracted_text = " ".join([
            block['Text'] 
            for block in response.get('Blocks', []) 
            if block['BlockType'] == 'LINE'
        ])
        
        print(json.dumps({
            'event': 'text_extracted',
            'blocks_count': len([b for b in response.get('Blocks', []) if b['BlockType'] == 'LINE']),
            'text_length': len(extracted_text),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        return extracted_text
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        # If DetectDocumentText fails, try AnalyzeDocument as fallback
        if error_code == 'UnsupportedDocumentException' and content_type == 'application/pdf':
            print(json.dumps({
                'event': 'trying_analyze_document_fallback',
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            try:
                response = textract_client.analyze_document(
                    Document={
                        'S3Object': {
                            'Bucket': bucket,
                            'Name': key
                        }
                    },
                    FeatureTypes=['TABLES', 'FORMS']
                )
                
                # Extract text from LINE blocks and join with spaces
                extracted_text = " ".join([
                    block['Text'] 
                    for block in response.get('Blocks', []) 
                    if block['BlockType'] == 'LINE'
                ])
                
                print(json.dumps({
                    'event': 'text_extracted_via_analyze',
                    'blocks_count': len([b for b in response.get('Blocks', []) if b['BlockType'] == 'LINE']),
                    'text_length': len(extracted_text),
                    'timestamp': datetime.utcnow().isoformat()
                }))
                
                return extracted_text
                
            except Exception as analyze_error:
                print(json.dumps({
                    'event': 'analyze_document_failed',
                    'error': str(analyze_error),
                    'timestamp': datetime.utcnow().isoformat()
                }))
                raise
        else:
            raise
    
    except Exception as e:
        print(json.dumps({
            'event': 'extraction_error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))
        raise


def handler(event, context):
    """
    Handle document upload with synchronous extraction
    """
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        session_id = body.get('sessionId')
        role = body.get('role', 'patient')
        file_data = body.get('file')
        filename = body.get('filename')
        content_type = body.get('contentType')
        
        # Validate inputs
        if not all([session_id, file_data, filename, content_type]):
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'Missing required fields: sessionId, file, filename, or contentType',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Validate file type
        if content_type not in ALLOWED_CONTENT_TYPES:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'Unsupported file type. Please upload PDF, JPEG, or PNG files only.',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Decode base64 file data
        file_bytes = base64.b64decode(file_data)
        
        # Determine file extension
        ext_map = {
            'application/pdf': 'pdf',
            'image/jpeg': 'jpg',
            'image/png': 'png'
        }
        file_ext = ext_map.get(content_type, 'bin')
        
        # Step 1 & 2: Store in S3
        s3_key = f"sessions/{session_id}/documents/{document_id}.{file_ext}"
        
        s3_client.put_object(
            Bucket=DOCUMENTS_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
            ServerSideEncryption='AES256'
        )
        
        print(json.dumps({
            'event': 'document_uploaded_to_s3',
            'documentId': document_id,
            'sessionId': session_id,
            's3Key': s3_key,
            'timestamp': timestamp
        }))
        
        # Step 3 & 4: Extract text using Textract synchronously
        try:
            extracted_text = extract_text_from_document(DOCUMENTS_BUCKET, s3_key, content_type)
            
            # Check if extraction was successful
            if not extracted_text or len(extracted_text.strip()) == 0:
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'error': 'Could not extract text from document. Please ensure the document is clear and readable.',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
            
        except Exception as extraction_error:
            print(json.dumps({
                'event': 'extraction_failed',
                'error': str(extraction_error),
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'error': 'Failed to extract text from document. Please try a different file format.',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Step 5: Store extracted text in DynamoDB with sessionId as PK
        document_table.put_item(
            Item={
                'PK': session_id,
                'SK': f'DOC#{document_id}',
                'sessionId': session_id,
                'documentId': document_id,
                'documentText': extracted_text,
                'filename': filename,
                'contentType': content_type,
                's3Key': s3_key,
                'timestamp': timestamp,
                'status': 'processed'
            }
        )
        
        print(json.dumps({
            'event': 'document_processed',
            'documentId': document_id,
            'sessionId': session_id,
            'text_length': len(extracted_text),
            'text_preview': extracted_text[:100] if extracted_text else '',
            'timestamp': timestamp
        }))
        
        # Step 6: Return success
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'status': 'success',
                'message': 'Document processed successfully',
                'documentId': document_id,
                'sessionId': session_id,
                'timestamp': timestamp
            })
        }
        
    except Exception as e:
        print(json.dumps({
            'event': 'upload_error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': 'Internal server error. Please try again.',
                'timestamp': datetime.utcnow().isoformat()
            })
        }
