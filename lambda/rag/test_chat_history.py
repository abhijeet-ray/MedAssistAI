"""
Unit tests for chat history functionality in RAG Lambda

Tests for:
- Chat history formatting
- Chat history update logic
- Chat history truncation
- Backward compatibility
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the handler and helper functions
import rag


class TestChatHistoryFormatting:
    """Test suite for chat history formatting (Requirement 2.4)"""
    
    def test_format_empty_chat_history(self):
        """Test formatting empty chat history"""
        result = rag.format_chat_history([])
        assert result == "No previous conversation."
    
    def test_format_none_chat_history(self):
        """Test formatting None chat history"""
        result = rag.format_chat_history(None)
        assert result == "No previous conversation."
    
    def test_format_single_exchange(self):
        """Test formatting single user-AI exchange"""
        history = [
            {
                'user': 'What is my glucose level?',
                'ai': 'Your glucose level is 95 mg/dL.'
            }
        ]
        result = rag.format_chat_history(history)
        
        assert 'User: What is my glucose level?' in result
        assert 'AI: Your glucose level is 95 mg/dL.' in result
    
    def test_format_multiple_exchanges(self):
        """Test formatting multiple exchanges in chronological order"""
        history = [
            {
                'user': 'What is my glucose level?',
                'ai': 'Your glucose level is 95 mg/dL.'
            },
            {
                'user': 'Is that normal?',
                'ai': 'Yes, that is within normal range.'
            },
            {
                'user': 'What about my hemoglobin?',
                'ai': 'Your hemoglobin is 13.5 g/dL, which is normal.'
            }
        ]
        result = rag.format_chat_history(history)
        
        # Verify all exchanges are present
        assert 'What is my glucose level?' in result
        assert 'Is that normal?' in result
        assert 'What about my hemoglobin?' in result
        
        # Verify chronological order (first exchange should appear before last)
        first_pos = result.find('What is my glucose level?')
        last_pos = result.find('What about my hemoglobin?')
        assert first_pos < last_pos
    
    def test_format_chat_history_with_incomplete_entry(self):
        """Test formatting history with incomplete entry (missing user or ai)"""
        history = [
            {
                'user': 'What is my glucose level?',
                'ai': 'Your glucose level is 95 mg/dL.'
            },
            {
                'user': 'Is that normal?'
                # Missing 'ai' field
            }
        ]
        result = rag.format_chat_history(history)
        
        # Should only include complete exchanges
        assert 'What is my glucose level?' in result
        assert 'Is that normal?' not in result
    
    def test_format_chat_history_limits_to_10_exchanges(self):
        """Test that formatting limits to last 10 exchanges (Requirement 2.5)"""
        # Create 15 exchanges
        history = []
        for i in range(15):
            history.append({
                'user': f'Question {i}',
                'ai': f'Answer {i}'
            })
        
        result = rag.format_chat_history(history)
        
        # Should include last 10 exchanges (5-14)
        assert 'Question 5' in result
        assert 'Question 14' in result
        
        # Should NOT include first 5 exchanges
        assert 'Question 0' not in result
        assert 'Question 4' not in result


class TestChatHistoryUpdate:
    """Test suite for chat history update logic (Requirement 4.1, 4.3, 4.5)"""
    
    def test_update_empty_history(self):
        """Test appending to empty history"""
        result = rag.update_chat_history([], 'What is my glucose?', 'Your glucose is 95.')
        
        assert len(result) == 1
        assert result[0]['user'] == 'What is my glucose?'
        assert result[0]['ai'] == 'Your glucose is 95.'
    
    def test_update_none_history(self):
        """Test appending to None history"""
        result = rag.update_chat_history(None, 'What is my glucose?', 'Your glucose is 95.')
        
        assert len(result) == 1
        assert result[0]['user'] == 'What is my glucose?'
        assert result[0]['ai'] == 'Your glucose is 95.'
    
    def test_update_existing_history(self):
        """Test appending to existing history"""
        existing = [
            {
                'user': 'First question',
                'ai': 'First answer'
            }
        ]
        
        result = rag.update_chat_history(existing, 'Second question', 'Second answer')
        
        assert len(result) == 2
        assert result[0]['user'] == 'First question'
        assert result[1]['user'] == 'Second question'
    
    def test_update_preserves_original_history(self):
        """Test that update doesn't modify original history (immutability)"""
        original = [
            {
                'user': 'First question',
                'ai': 'First answer'
            }
        ]
        
        result = rag.update_chat_history(original, 'Second question', 'Second answer')
        
        # Original should be unchanged
        assert len(original) == 1
        # Result should have new entry
        assert len(result) == 2
    
    def test_update_truncates_at_10_exchanges(self):
        """Test automatic truncation when exceeding 10 exchanges"""
        # Create history with 10 exchanges
        history = []
        for i in range(10):
            history.append({
                'user': f'Question {i}',
                'ai': f'Answer {i}'
            })
        
        # Add 11th exchange
        result = rag.update_chat_history(history, 'Question 10', 'Answer 10')
        
        # Should still have 10 exchanges (oldest removed)
        assert len(result) == 10
        
        # Should have newest exchanges
        assert result[-1]['user'] == 'Question 10'
        
        # Should NOT have oldest exchange
        assert result[0]['user'] != 'Question 0'
        assert result[0]['user'] == 'Question 1'
    
    def test_update_truncates_to_keep_most_recent(self):
        """Test that truncation keeps most recent exchanges"""
        # Create history with 15 exchanges
        history = []
        for i in range(15):
            history.append({
                'user': f'Question {i}',
                'ai': f'Answer {i}'
            })
        
        # Add 16th exchange
        result = rag.update_chat_history(history, 'Question 15', 'Answer 15')
        
        # Should have exactly 10 exchanges
        assert len(result) == 10
        
        # Should have exchanges 6-15
        assert result[0]['user'] == 'Question 6'
        assert result[-1]['user'] == 'Question 15'


class TestChatHistoryIntegration:
    """Integration tests for chat history in handler"""
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_handler_returns_updated_history(self, mock_gemini, mock_get_doc):
        """Test that handler returns updated chat history in response"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose?',
                'role': 'patient',
                'chatHistory': [
                    {
                        'user': 'Previous question',
                        'ai': 'Previous answer'
                    }
                ]
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Should have updated history with new exchange
        assert 'chatHistory' in body
        assert len(body['chatHistory']) == 2
        assert body['chatHistory'][0]['user'] == 'Previous question'
        assert body['chatHistory'][1]['user'] == 'What is my glucose?'
        assert body['chatHistory'][1]['ai'] == 'Test response'
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_handler_with_empty_history(self, mock_gemini, mock_get_doc):
        """Test handler with empty initial chat history"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose?',
                'role': 'patient',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Should have single exchange
        assert len(body['chatHistory']) == 1
        assert body['chatHistory'][0]['user'] == 'What is my glucose?'
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_handler_without_chat_history_field(self, mock_gemini, mock_get_doc):
        """Test backward compatibility when chatHistory field is missing"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose?',
                'role': 'patient'
                # No chatHistory field
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Should initialize with empty history and add new exchange
        assert 'chatHistory' in body
        assert len(body['chatHistory']) == 1
        assert body['chatHistory'][0]['user'] == 'What is my glucose?'
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_handler_includes_history_in_prompt(self, mock_gemini, mock_get_doc):
        """Test that chat history is included in the Gemini prompt"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'Follow-up question',
                'role': 'patient',
                'chatHistory': [
                    {
                        'user': 'Initial question',
                        'ai': 'Initial answer'
                    }
                ]
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify Gemini was called with history in prompt
        mock_gemini.assert_called_once()
        prompt = mock_gemini.call_args[0][0]
        
        # Prompt should include conversation history
        assert 'Conversation history:' in prompt
        assert 'Initial question' in prompt
        assert 'Initial answer' in prompt
        assert 'Follow-up question' in prompt


class TestBackwardCompatibility:
    """Test backward compatibility with existing API"""
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_handler_without_role_field(self, mock_gemini, mock_get_doc):
        """Test that handler defaults to 'patient' role when not specified"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose?'
                # No role field
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify prompt uses patient role
        prompt = mock_gemini.call_args[0][0]
        assert 'simple, everyday language' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_handler_response_includes_all_fields(self, mock_gemini, mock_get_doc):
        """Test that response includes all expected fields"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose?',
                'role': 'patient'
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Verify all expected fields are present
        assert 'answer' in body
        assert 'source' in body
        assert 'timestamp' in body
        assert 'chatHistory' in body


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
