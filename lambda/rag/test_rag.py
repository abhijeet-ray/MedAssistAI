"""
Unit tests for RAG Lambda function

Tests core functionality including:
- Question embedding generation
- Document and KB similarity search
- Context combination
- Prompt construction
- Response formatting
- Error handling
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the handler and helper functions
import rag


class TestRAGLambda:
    """Test suite for RAG Lambda function"""
    
    def test_generate_question_embedding_success(self):
        """Test successful question embedding generation (Req 8.1)"""
        with patch('rag.bedrock_runtime') as mock_bedrock:
            # Mock Bedrock response
            mock_response = {
                'body': Mock(read=lambda: json.dumps({
                    'embedding': [0.1] * 1536
                }).encode())
            }
            mock_bedrock.invoke_model.return_value = mock_response
            
            # Test embedding generation
            embedding = rag.generate_question_embedding("What is my blood glucose level?")
            
            assert embedding is not None
            assert len(embedding) == 1536
            assert all(isinstance(x, float) for x in embedding)
    
    def test_combine_context_with_both_sources(self):
        """Test context combination with document and KB chunks (Req 8.6)"""
        document_chunks = [
            {'chunkText': 'Blood glucose: 120 mg/dL', 'documentId': 'doc1'},
            {'chunkText': 'Hemoglobin A1C: 6.5%', 'documentId': 'doc1'}
        ]
        
        kb_chunks = [
            {'chunkText': 'Normal blood glucose range is 70-100 mg/dL', 'source': 'diabetes'},
            {'chunkText': 'A1C below 5.7% is normal', 'source': 'diabetes'}
        ]
        
        context, sources = rag.combine_context(document_chunks, kb_chunks)
        
        assert 'Context from uploaded documents:' in context
        assert 'Context from medical knowledge base:' in context
        assert 'Blood glucose: 120 mg/dL' in context
        assert 'Normal blood glucose range' in context
        assert len(sources) == 4
    
    def test_combine_context_documents_only(self):
        """Test context combination with only document chunks"""
        document_chunks = [
            {'chunkText': 'Test result data', 'documentId': 'doc1'}
        ]
        
        context, sources = rag.combine_context(document_chunks, [])
        
        assert 'Context from uploaded documents:' in context
        assert 'Context from medical knowledge base:' not in context
        assert len(sources) == 1
    
    def test_combine_context_kb_only(self):
        """Test context combination with only KB chunks"""
        kb_chunks = [
            {'chunkText': 'Medical knowledge', 'source': 'diabetes'}
        ]
        
        context, sources = rag.combine_context([], kb_chunks)
        
        assert 'Context from uploaded documents:' not in context
        assert 'Context from medical knowledge base:' in context
        assert len(sources) == 1
    
    def test_construct_prompt_doctor_role(self):
        """Test prompt construction for doctor role (Req 9.1, 9.4)"""
        context = "Blood glucose: 120 mg/dL"
        question = "What does this result mean?"
        
        prompt = rag.construct_prompt('doctor', context, question)
        
        assert 'Role: doctor' in prompt
        assert 'technical accuracy' in prompt
        assert 'medical terminology' in prompt
        assert context in prompt
        assert question in prompt
        assert rag.MEDICAL_DISCLAIMER in prompt
    
    def test_construct_prompt_patient_role(self):
        """Test prompt construction for patient role (Req 9.1, 9.5)"""
        context = "Blood glucose: 120 mg/dL"
        question = "What does this result mean?"
        
        prompt = rag.construct_prompt('patient', context, question)
        
        assert 'Role: patient' in prompt
        assert 'simple terms' in prompt
        assert 'everyday language' in prompt
        assert context in prompt
        assert question in prompt
        assert rag.MEDICAL_DISCLAIMER in prompt
    
    def test_construct_prompt_asha_role(self):
        """Test prompt construction for ASHA worker role (Req 9.1, 9.6)"""
        context = "Blood glucose: 120 mg/dL"
        question = "What should I advise?"
        
        prompt = rag.construct_prompt('asha', context, question)
        
        assert 'Role: asha' in prompt
        assert 'community health' in prompt
        assert 'practical advice' in prompt
        assert context in prompt
        assert question in prompt
        assert rag.MEDICAL_DISCLAIMER in prompt
    
    def test_format_response_includes_disclaimer(self):
        """Test response formatting includes disclaimer (Req 9.3, 20.5)"""
        response_text = "Your blood glucose level is slightly elevated."
        
        formatted = rag.format_response(response_text, 'patient')
        
        assert rag.MEDICAL_DISCLAIMER in formatted
        assert response_text in formatted
    
    def test_format_response_preserves_existing_disclaimer(self):
        """Test response formatting preserves existing disclaimer"""
        response_text = f"Your results look good. {rag.MEDICAL_DISCLAIMER}"
        
        formatted = rag.format_response(response_text, 'patient')
        
        # Should not duplicate disclaimer
        assert formatted.count(rag.MEDICAL_DISCLAIMER) == 1
    
    def test_handler_missing_session_id(self):
        """Test handler with missing sessionId (Req 10.2)"""
        event = {
            'body': json.dumps({
                'role': 'patient',
                'message': 'What is my glucose level?'
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error']['code'] == 'INVALID_REQUEST'
    
    def test_handler_missing_message(self):
        """Test handler with missing message"""
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'role': 'patient'
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
    
    def test_handler_message_too_long(self):
        """Test handler with message exceeding 1000 characters (Req 10.2)"""
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'role': 'patient',
                'message': 'x' * 1001
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'MESSAGE_TOO_LONG'
    
    @patch('rag.generate_question_embedding')
    @patch('rag.search_document_embeddings')
    @patch('rag.search_knowledge_base_embeddings')
    @patch('rag.call_bedrock_nova')
    def test_handler_success(self, mock_bedrock, mock_kb_search, mock_doc_search, mock_embedding):
        """Test successful handler execution (Req 8.1-8.7, 9.1-9.7)"""
        # Setup mocks
        mock_embedding.return_value = [0.1] * 1536
        mock_doc_search.return_value = [
            {'chunkText': 'Blood glucose: 120 mg/dL', 'documentId': 'doc1'}
        ]
        mock_kb_search.return_value = [
            {'chunkText': 'Normal range is 70-100 mg/dL', 'source': 'diabetes'}
        ]
        mock_bedrock.return_value = f"Your blood glucose is slightly elevated. {rag.MEDICAL_DISCLAIMER}"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'role': 'patient',
                'message': 'What is my glucose level?'
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'response' in body
        assert 'sources' in body
        assert 'timestamp' in body
        assert rag.MEDICAL_DISCLAIMER in body['response']
        
        # Verify all functions were called
        mock_embedding.assert_called_once()
        mock_doc_search.assert_called_once()
        mock_kb_search.assert_called_once()
        mock_bedrock.assert_called_once()
    
    @patch('rag.generate_question_embedding')
    def test_handler_embedding_error(self, mock_embedding):
        """Test handler error handling when embedding generation fails"""
        mock_embedding.side_effect = Exception("Bedrock service unavailable")
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'role': 'patient',
                'message': 'What is my glucose level?'
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error']['code'] == 'RAG_FAILED'
        assert body['error']['retryable'] is True
    
    def test_role_descriptions_exist(self):
        """Test that all role descriptions are defined"""
        assert 'doctor' in rag.ROLE_DESCRIPTIONS
        assert 'patient' in rag.ROLE_DESCRIPTIONS
        assert 'asha' in rag.ROLE_DESCRIPTIONS
    
    def test_medical_disclaimer_defined(self):
        """Test that medical disclaimer is properly defined (Req 20.5)"""
        assert rag.MEDICAL_DISCLAIMER is not None
        assert len(rag.MEDICAL_DISCLAIMER) > 0
        assert 'informational' in rag.MEDICAL_DISCLAIMER.lower()
        assert 'healthcare professional' in rag.MEDICAL_DISCLAIMER.lower()
    
    @patch('rag.dynamodb')
    def test_store_chat_message_success(self, mock_dynamodb):
        """Test successful chat message storage (Req 10.5, 12.4)"""
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        result = rag.store_chat_message(
            'test-session',
            'msg-123',
            'user',
            'What is my glucose level?',
            '2024-01-01T12:00:00'
        )
        
        assert result is True
        mock_table.put_item.assert_called_once()
        
        # Verify the item structure
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['PK'] == 'SESSION#test-session'
        assert 'MESSAGE#' in item['SK']
        assert item['sender'] == 'user'
        assert item['content'] == 'What is my glucose level?'
        assert item['ttl'] is not None
    
    @patch('rag.dynamodb')
    def test_store_chat_message_ai_response(self, mock_dynamodb):
        """Test storing AI response message (Req 10.5, 12.4)"""
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        result = rag.store_chat_message(
            'test-session',
            'msg-456',
            'ai',
            'Your glucose level is elevated.',
            '2024-01-01T12:00:01'
        )
        
        assert result is True
        call_args = mock_table.put_item.call_args
        item = call_args[1]['Item']
        assert item['sender'] == 'ai'
    
    @patch('rag.dynamodb')
    def test_store_chat_message_error(self, mock_dynamodb):
        """Test error handling when storing chat message fails"""
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamodb.Table.return_value = mock_table
        
        result = rag.store_chat_message(
            'test-session',
            'msg-123',
            'user',
            'Test message',
            '2024-01-01T12:00:00'
        )
        
        assert result is False
    
    @patch('rag.dynamodb')
    def test_retrieve_chat_history_success(self, mock_dynamodb):
        """Test successful chat history retrieval (Req 10.5, 12.4)"""
        mock_table = MagicMock()
        mock_table.query.return_value = {
            'Items': [
                {
                    'messageId': 'msg-1',
                    'sender': 'user',
                    'content': 'First question',
                    'timestamp': '2024-01-01T12:00:00'
                },
                {
                    'messageId': 'msg-2',
                    'sender': 'ai',
                    'content': 'First answer',
                    'timestamp': '2024-01-01T12:00:01'
                },
                {
                    'messageId': 'msg-3',
                    'sender': 'user',
                    'content': 'Second question',
                    'timestamp': '2024-01-01T12:00:02'
                }
            ]
        }
        mock_dynamodb.Table.return_value = mock_table
        
        messages = rag.retrieve_chat_history('test-session', limit=10)
        
        assert len(messages) == 3
        assert messages[0]['sender'] == 'user'
        assert messages[0]['content'] == 'First question'
        assert messages[1]['sender'] == 'ai'
        assert messages[2]['content'] == 'Second question'
        
        # Verify query was called correctly
        mock_table.query.assert_called_once()
        call_args = mock_table.query.call_args
        assert call_args[1]['KeyConditionExpression'] is not None
    
    @patch('rag.dynamodb')
    def test_retrieve_chat_history_empty(self, mock_dynamodb):
        """Test retrieving chat history when no messages exist"""
        mock_table = MagicMock()
        mock_table.query.return_value = {'Items': []}
        mock_dynamodb.Table.return_value = mock_table
        
        messages = rag.retrieve_chat_history('test-session')
        
        assert len(messages) == 0
    
    @patch('rag.dynamodb')
    def test_retrieve_chat_history_error(self, mock_dynamodb):
        """Test error handling when retrieving chat history fails"""
        mock_table = MagicMock()
        mock_table.query.side_effect = Exception("DynamoDB error")
        mock_dynamodb.Table.return_value = mock_table
        
        messages = rag.retrieve_chat_history('test-session')
        
        assert messages == []
    
    @patch('rag.generate_question_embedding')
    @patch('rag.search_document_embeddings')
    @patch('rag.search_knowledge_base_embeddings')
    @patch('rag.call_bedrock_nova')
    @patch('rag.store_chat_message')
    def test_handler_stores_chat_history(self, mock_store, mock_bedrock, mock_kb_search, mock_doc_search, mock_embedding):
        """Test that handler stores both user and AI messages (Req 10.5, 12.4)"""
        # Setup mocks
        mock_embedding.return_value = [0.1] * 1536
        mock_doc_search.return_value = []
        mock_kb_search.return_value = []
        mock_bedrock.return_value = f"Response text. {rag.MEDICAL_DISCLAIMER}"
        mock_store.return_value = True
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'role': 'patient',
                'message': 'What is my glucose level?'
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify store_chat_message was called twice (user and AI)
        assert mock_store.call_count == 2
        
        # Verify first call is for user message
        first_call = mock_store.call_args_list[0]
        assert first_call[0][0] == 'test-session'  # session_id
        assert first_call[0][2] == 'user'  # sender
        assert first_call[0][3] == 'What is my glucose level?'  # content
        
        # Verify second call is for AI message
        second_call = mock_store.call_args_list[1]
        assert second_call[0][0] == 'test-session'  # session_id
        assert second_call[0][2] == 'ai'  # sender
        assert rag.MEDICAL_DISCLAIMER in second_call[0][3]  # content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
