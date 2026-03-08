"""
Test suite for Upload Lambda function
Tests session management, document storage, and pipeline triggering
"""
import json
import pytest
import base64
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock environment variables before importing upload module
os.environ['DOCUMENTS_BUCKET'] = 'test-bucket'
os.environ['SESSION_TABLE'] = 'test-session-table'
os.environ['DOCUMENT_TABLE'] = 'test-document-table'
os.environ['EXTRACTION_LAMBDA'] = 'test-extraction-lambda'

from upload import handler


class TestUploadLambda:
    """Test suite for Upload Lambda function"""
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_session_creation_on_first_upload(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda):
        """Test session creation on first document upload (Req 12.1, 17.4)"""
        from botocore.exceptions import ClientError
        
        # Setup mocks
        error_response = {'Error': {'Code': 'ConditionalCheckFailedException'}}
        mock_session_table.update_item.side_effect = ClientError(error_response, 'UpdateItem')
        mock_session_table.put_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Create test event
        file_content = b"test pdf content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'sessionId': None,  # No session ID provided
                'role': 'patient',
                'file': file_base64,
                'filename': 'test.pdf',
                'contentType': 'application/pdf'
            })
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'sessionId' in body
        assert 'documentId' in body
        assert body['status'] == 'processing'
        
        # Verify session was created
        mock_session_table.put_item.assert_called_once()
        call_args = mock_session_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['PK'].startswith('SESSION#')
        assert item['SK'] == 'METADATA'
        assert item['role'] == 'patient'
        assert item['status'] == 'active'
        assert len(item['documentIds']) == 1
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_document_association_with_session(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda):
        """Test document is associated with session ID (Req 12.2, 17.6)"""
        # Setup mocks
        mock_session_table.update_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Create test event
        file_content = b"test pdf content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        session_id = "test-session-123"
        
        event = {
            'body': json.dumps({
                'sessionId': session_id,
                'role': 'doctor',
                'file': file_base64,
                'filename': 'lab-report.pdf',
                'contentType': 'application/pdf'
            })
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['sessionId'] == session_id
        
        # Verify document metadata includes session ID
        mock_doc_table.put_item.assert_called_once()
        call_args = mock_doc_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['sessionId'] == session_id
        assert item['role'] == 'doctor'
        assert item['filename'] == 'lab-report.pdf'
        assert 'uploadedAt' in item
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_session_metadata_storage_in_dynamodb(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda):
        """Test session metadata is stored in DynamoDB (Req 17.4)"""
        # Setup mocks
        mock_session_table.update_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Create test event
        file_content = b"test pdf content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'sessionId': 'session-456',
                'role': 'asha',
                'file': file_base64,
                'filename': 'prescription.pdf',
                'contentType': 'application/pdf'
            })
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify session update was attempted
        mock_session_table.update_item.assert_called_once()
        call_args = mock_session_table.update_item.call_args
        assert call_args[1]['Key']['PK'] == 'SESSION#session-456'
        assert call_args[1]['Key']['SK'] == 'METADATA'
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_file_type_validation_pdf(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda):
        """Test file type validation for PDF (Req 2.1)"""
        # Create test event with PDF
        file_content = b"test pdf content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'sessionId': 'session-123',
                'role': 'patient',
                'file': file_base64,
                'filename': 'test.pdf',
                'contentType': 'application/pdf'
            })
        }
        
        # Setup mocks
        mock_session_table.update_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Execute handler
        response = handler(event, None)
        
        # Verify success
        assert response['statusCode'] == 200
        mock_s3.put_object.assert_called_once()
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_file_type_validation_jpeg(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda):
        """Test file type validation for JPEG (Req 2.2)"""
        # Create test event with JPEG
        file_content = b"test jpeg content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'sessionId': 'session-123',
                'role': 'patient',
                'file': file_base64,
                'filename': 'test.jpg',
                'contentType': 'image/jpeg'
            })
        }
        
        # Setup mocks
        mock_session_table.update_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Execute handler
        response = handler(event, None)
        
        # Verify success
        assert response['statusCode'] == 200
        mock_s3.put_object.assert_called_once()
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_file_type_validation_png(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda):
        """Test file type validation for PNG (Req 2.2)"""
        # Create test event with PNG
        file_content = b"test png content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'sessionId': 'session-123',
                'role': 'patient',
                'file': file_base64,
                'filename': 'test.png',
                'contentType': 'image/png'
            })
        }
        
        # Setup mocks
        mock_session_table.update_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Execute handler
        response = handler(event, None)
        
        # Verify success
        assert response['statusCode'] == 200
        mock_s3.put_object.assert_called_once()
    
    def test_file_type_validation_invalid(self):
        """Test file type validation rejects invalid types (Req 2.1, 2.2)"""
        # Create test event with invalid file type
        file_content = b"test content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'sessionId': 'session-123',
                'role': 'patient',
                'file': file_base64,
                'filename': 'test.txt',
                'contentType': 'text/plain'
            })
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify error
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'INVALID_FILE_TYPE'
        assert 'file format' in body['error']['message'].lower()
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_s3_storage_with_session_path(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda):
        """Test document is stored in S3 with session-based path (Req 2.3, 17.1, 17.5)"""
        # Setup mocks
        mock_session_table.update_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Create test event
        file_content = b"test pdf content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        session_id = "session-789"
        
        event = {
            'body': json.dumps({
                'sessionId': session_id,
                'role': 'patient',
                'file': file_base64,
                'filename': 'test.pdf',
                'contentType': 'application/pdf'
            })
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify S3 storage
        mock_s3.put_object.assert_called_once()
        call_args = mock_s3.put_object.call_args
        s3_key = call_args[1]['Key']
        
        # Verify path structure
        assert s3_key.startswith(f'sessions/{session_id}/documents/')
        assert s3_key.endswith('.pdf')
        
        # Verify encryption
        assert call_args[1]['ServerSideEncryption'] == 'AES256'
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_extraction_lambda_invocation(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda):
        """Test ExtractionLambda is invoked asynchronously (Req 2.4)"""
        # Setup mocks
        mock_session_table.update_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Create test event
        file_content = b"test pdf content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'sessionId': 'session-123',
                'role': 'patient',
                'file': file_base64,
                'filename': 'test.pdf',
                'contentType': 'application/pdf'
            })
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify Lambda invocation
        mock_lambda.invoke.assert_called_once()
        call_args = mock_lambda.invoke.call_args
        assert call_args[1]['InvocationType'] == 'Event'  # Asynchronous
        
        # Verify payload contains required fields
        payload = json.loads(call_args[1]['Payload'])
        assert 'documentId' in payload
        assert 'sessionId' in payload
        assert 's3Bucket' in payload
        assert 's3Key' in payload
        assert 'contentType' in payload
    
    def test_missing_required_fields(self):
        """Test error handling for missing required fields (Req 21.1)"""
        # Create test event with missing file
        event = {
            'body': json.dumps({
                'sessionId': 'session-123',
                'role': 'patient',
                'filename': 'test.pdf',
                'contentType': 'application/pdf'
                # Missing 'file' field
            })
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify error
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'INVALID_REQUEST'
        assert 'required fields' in body['error']['message'].lower()
    
    @patch('upload.lambda_client')
    @patch('upload.document_table')
    @patch('upload.session_table')
    @patch('upload.s3_client')
    def test_cloudwatch_logging(self, mock_s3, mock_session_table, mock_doc_table, mock_lambda, capsys):
        """Test CloudWatch logging of upload events (Req 19.1)"""
        # Setup mocks
        mock_session_table.update_item.return_value = None
        mock_doc_table.put_item.return_value = None
        mock_s3.put_object.return_value = None
        mock_lambda.invoke.return_value = None
        
        # Create test event
        file_content = b"test pdf content"
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        event = {
            'body': json.dumps({
                'sessionId': 'session-123',
                'role': 'patient',
                'file': file_base64,
                'filename': 'test.pdf',
                'contentType': 'application/pdf'
            })
        }
        
        # Execute handler
        response = handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        
        # Verify logging occurred (captured via print statements)
        captured = capsys.readouterr()
        assert 'document_uploaded' in captured.out
        assert 'extraction_triggered' in captured.out


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
