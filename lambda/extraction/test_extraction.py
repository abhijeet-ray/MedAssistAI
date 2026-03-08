"""
Unit tests for MedAssist Extraction Lambda Function

Requirements: 3.1, 3.2, 3.3, 3.5, 4.1-4.5, 19.3
"""
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import extraction


class TestExtractionLambda(unittest.TestCase):
    """Unit tests for extraction lambda handler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_event = {
            'documentId': 'test-doc-123',
            'sessionId': 'test-session-456',
            's3Bucket': 'test-bucket',
            's3Key': 'sessions/test-session-456/documents/test-doc-123.pdf',
            'contentType': 'application/pdf'
        }
        
        self.sample_context = Mock()
        
        # Set environment variables
        os.environ['DOCUMENT_TABLE'] = 'test-documents-table'
        os.environ['EMBEDDING_LAMBDA'] = 'test-embedding-lambda'
    
    @patch('extraction.textract_client')
    @patch('extraction.comprehend_medical_client')
    @patch('extraction.document_table')
    @patch('extraction.lambda_client')
    def test_pdf_extraction_success(self, mock_lambda, mock_table, mock_comprehend, mock_textract):
        """Test successful PDF text extraction (Req 3.1)"""
        # Mock Textract response
        mock_textract.detect_document_text.return_value = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Patient Name: John Doe'},
                {'BlockType': 'LINE', 'Text': 'Glucose: 120 mg/dL'},
                {'BlockType': 'LINE', 'Text': 'Medication: Metformin 500mg'}
            ]
        }
        
        # Mock Comprehend Medical response
        mock_comprehend.detect_entities_v2.return_value = {
            'Entities': [
                {
                    'Category': 'MEDICATION',
                    'Text': 'Metformin',
                    'Score': 0.95,
                    'Attributes': [{'Type': 'DOSAGE', 'Text': '500mg'}]
                }
            ]
        }
        
        # Mock DynamoDB update
        mock_table.update_item.return_value = {}
        
        # Mock Lambda invoke
        mock_lambda.invoke.return_value = {}
        
        # Call handler
        response = extraction.handler(self.sample_event, self.sample_context)
        
        # Assertions
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['status'], 'extracted')
        self.assertIn('metrics', body)
        
        # Verify Textract was called
        mock_textract.detect_document_text.assert_called_once()
        
        # Verify Comprehend Medical was called
        mock_comprehend.detect_entities_v2.assert_called_once()
        
        # Verify DynamoDB update
        mock_table.update_item.assert_called()
        
        # Verify Lambda invocation
        mock_lambda.invoke.assert_called_once()
    
    @patch('extraction.textract_client')
    @patch('extraction.rekognition_client')
    @patch('extraction.comprehend_medical_client')
    @patch('extraction.document_table')
    @patch('extraction.lambda_client')
    def test_image_extraction_with_rekognition(self, mock_lambda, mock_table, mock_comprehend, mock_rekognition, mock_textract):
        """Test image extraction with Rekognition analysis (Req 3.2, 3.3)"""
        # Update event for image
        event = self.sample_event.copy()
        event['contentType'] = 'image/jpeg'
        event['s3Key'] = 'sessions/test-session-456/documents/test-doc-123.jpg'
        
        # Mock Textract response
        mock_textract.detect_document_text.return_value = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Lab Report'},
                {'BlockType': 'LINE', 'Text': 'Hemoglobin: 14.5 g/dL'}
            ]
        }
        
        # Mock Rekognition response
        mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Document', 'Confidence': 95.5},
                {'Name': 'Text', 'Confidence': 92.3}
            ]
        }
        
        # Mock Comprehend Medical response
        mock_comprehend.detect_entities_v2.return_value = {
            'Entities': [
                {
                    'Category': 'TEST_TREATMENT_PROCEDURE',
                    'Text': 'Hemoglobin',
                    'Score': 0.98,
                    'Attributes': []
                }
            ]
        }
        
        # Mock DynamoDB and Lambda
        mock_table.update_item.return_value = {}
        mock_lambda.invoke.return_value = {}
        
        # Call handler
        response = extraction.handler(event, self.sample_context)
        
        # Assertions
        self.assertEqual(response['statusCode'], 200)
        
        # Verify Rekognition was called for image
        mock_rekognition.detect_labels.assert_called_once()
    
    @patch('extraction.textract_client')
    @patch('extraction.document_table')
    def test_extraction_failure_empty_text(self, mock_table, mock_textract):
        """Test extraction failure when no text is extracted (Req 3.4)"""
        # Mock Textract returning empty text
        mock_textract.detect_document_text.return_value = {
            'Blocks': []
        }
        
        # Mock DynamoDB update
        mock_table.update_item.return_value = {}
        
        # Call handler
        response = extraction.handler(self.sample_event, self.sample_context)
        
        # Assertions
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('error', body)
        self.assertEqual(body['error']['code'], 'EXTRACTION_FAILED')
        
        # Verify error message is user-friendly (Req 21.6)
        self.assertIn('couldn\'t read your document', body['error']['message'])
    
    @patch('extraction.comprehend_medical_client')
    def test_medical_entity_extraction(self, mock_comprehend):
        """Test medical entity extraction (Req 4.1, 4.2, 4.3, 4.4, 4.5)"""
        # Mock Comprehend Medical response with various entity types
        mock_comprehend.detect_entities_v2.return_value = {
            'Entities': [
                {
                    'Category': 'MEDICATION',
                    'Text': 'Aspirin',
                    'Score': 0.95,
                    'Attributes': [{'Type': 'DOSAGE', 'Text': '100mg'}]
                },
                {
                    'Category': 'MEDICAL_CONDITION',
                    'Text': 'Diabetes',
                    'Score': 0.92,
                    'Attributes': []
                },
                {
                    'Category': 'TEST_TREATMENT_PROCEDURE',
                    'Text': 'Blood glucose test',
                    'Score': 0.88,
                    'Attributes': []
                }
            ]
        }
        
        # Call the extraction function
        text = "Patient has Diabetes and takes Aspirin 100mg. Blood glucose test performed."
        entities = extraction.extract_medical_entities(text)
        
        # Assertions
        self.assertEqual(len(entities), 3)
        
        # Check medication entity (Req 4.2)
        medication = next(e for e in entities if e['type'] == 'MEDICATION')
        self.assertEqual(medication['text'], 'Aspirin')
        self.assertEqual(medication['dosage'], '100mg')
        
        # Check condition entity (Req 4.3)
        condition = next(e for e in entities if e['type'] == 'CONDITION')
        self.assertEqual(condition['text'], 'Diabetes')
        
        # Check test result entity (Req 4.4)
        test = next(e for e in entities if e['type'] == 'TEST_RESULT')
        self.assertEqual(test['text'], 'Blood glucose test')
    
    def test_missing_event_parameters(self):
        """Test error handling for missing event parameters"""
        # Create event with missing parameters
        invalid_event = {
            'documentId': 'test-doc-123'
            # Missing other required fields
        }
        
        # Call handler
        response = extraction.handler(invalid_event, self.sample_context)
        
        # Assertions
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('error', body)
    
    @patch('extraction.textract_client')
    @patch('extraction.comprehend_medical_client')
    @patch('extraction.document_table')
    @patch('extraction.lambda_client')
    def test_cloudwatch_logging(self, mock_lambda, mock_table, mock_comprehend, mock_textract):
        """Test CloudWatch logging of extraction metrics (Req 19.3)"""
        # Mock AWS services
        mock_textract.detect_document_text.return_value = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Test document'}
            ]
        }
        mock_comprehend.detect_entities_v2.return_value = {'Entities': []}
        mock_table.update_item.return_value = {}
        mock_lambda.invoke.return_value = {}
        
        # Capture print statements (CloudWatch logs)
        with patch('builtins.print') as mock_print:
            response = extraction.handler(self.sample_event, self.sample_context)
            
            # Verify logging occurred
            self.assertTrue(mock_print.called)
            
            # Check for specific log events
            log_calls = [call[0][0] for call in mock_print.call_args_list]
            log_events = [json.loads(log) for log in log_calls if log.startswith('{')]
            
            # Verify extraction_started event
            started_events = [e for e in log_events if e.get('event') == 'extraction_started']
            self.assertTrue(len(started_events) > 0)
            
            # Verify extraction_completed event with metrics
            completed_events = [e for e in log_events if e.get('event') == 'extraction_completed']
            self.assertTrue(len(completed_events) > 0)
            if completed_events:
                self.assertIn('metrics', completed_events[0])


if __name__ == '__main__':
    unittest.main()
