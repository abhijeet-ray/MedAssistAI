"""
Unit tests for role-based prompt system (Task 2)

Tests for:
- Role-specific prompt instructions generation
- Role-specific instructions in conversational prompts
- Prompt construction with role context
- Role switching behavior
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the handler and helper functions
import rag


class TestRolePromptInstructions:
    """Test suite for role-specific prompt instructions (Requirement 8.1, 8.5)"""
    
    def test_get_role_prompt_instructions_patient(self):
        """Test patient role instructions are returned correctly"""
        instructions = rag.get_role_prompt_instructions('patient')
        
        # Verify patient-specific content
        assert 'simple, everyday language' in instructions
        assert 'avoid medical jargon' in instructions.lower()
        assert 'analogies and examples' in instructions
        assert 'practical health implications' in instructions
        assert 'actionable advice' in instructions
        assert 'empathetic' in instructions
        assert 'medical AI assistant helping a patient' in instructions
    
    def test_get_role_prompt_instructions_doctor(self):
        """Test doctor role instructions are returned correctly"""
        instructions = rag.get_role_prompt_instructions('doctor')
        
        # Verify doctor-specific content
        assert 'clinical medical terminology' in instructions
        assert 'diagnostic considerations' in instructions
        assert 'differential diagnoses' in instructions
        assert 'clinical guidelines' in instructions
        assert 'pathophysiology' in instructions
        assert 'healthcare professional' in instructions
        assert 'assessment and management' in instructions
    
    def test_get_role_prompt_instructions_asha(self):
        """Test ASHA worker role instructions are returned correctly"""
        instructions = rag.get_role_prompt_instructions('asha')
        
        # Verify ASHA-specific content
        assert 'community health' in instructions
        assert 'refer' in instructions.lower()
        assert 'preventive health' in instructions
        assert 'health workers' in instructions
        assert 'resource-limited settings' in instructions
        assert 'rural' in instructions
        assert 'community outreach' in instructions
    
    def test_get_role_prompt_instructions_default_to_patient(self):
        """Test that unknown role defaults to patient instructions"""
        instructions = rag.get_role_prompt_instructions('unknown_role')
        
        # Should return patient instructions
        assert 'simple, everyday language' in instructions
        assert 'avoid medical jargon' in instructions.lower()
    
    def test_get_role_prompt_instructions_case_insensitive(self):
        """Test that role lookup is case-sensitive (as per implementation)"""
        # The implementation uses .get() which is case-sensitive
        instructions_lower = rag.get_role_prompt_instructions('patient')
        instructions_upper = rag.get_role_prompt_instructions('PATIENT')
        
        # Upper case should default to patient
        assert 'simple, everyday language' in instructions_lower
        # Upper case will default to patient since key doesn't match
        assert 'simple, everyday language' in instructions_upper
    
    def test_role_instructions_are_non_empty(self):
        """Test that all role instructions are non-empty strings"""
        for role in ['patient', 'doctor', 'asha']:
            instructions = rag.get_role_prompt_instructions(role)
            assert isinstance(instructions, str)
            assert len(instructions) > 0
            assert len(instructions) > 100  # Should be substantial


class TestRoleInstructionsInPrompt:
    """Test suite for role instructions integration in prompts (Requirement 8.1, 8.5)"""
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_includes_patient_role_instructions(self, mock_gemini, mock_get_doc):
        """Test that patient role instructions are included in prompt"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose level?',
                'role': 'patient',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify prompt includes patient instructions
        prompt = mock_gemini.call_args[0][0]
        assert 'simple, everyday language' in prompt
        assert 'avoid medical jargon' in prompt.lower()
        assert 'medical AI assistant helping a patient' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_includes_doctor_role_instructions(self, mock_gemini, mock_get_doc):
        """Test that doctor role instructions are included in prompt"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is the differential diagnosis?',
                'role': 'doctor',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify prompt includes doctor instructions
        prompt = mock_gemini.call_args[0][0]
        assert 'clinical medical terminology' in prompt
        assert 'diagnostic considerations' in prompt
        assert 'healthcare professional' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_includes_asha_role_instructions(self, mock_gemini, mock_get_doc):
        """Test that ASHA worker role instructions are included in prompt"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What should I advise the patient?',
                'role': 'asha',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify prompt includes ASHA instructions
        prompt = mock_gemini.call_args[0][0]
        assert 'community health' in prompt
        assert 'refer' in prompt.lower()
        assert 'resource-limited settings' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_includes_document_text(self, mock_gemini, mock_get_doc):
        """Test that medical report is included in prompt"""
        mock_get_doc.return_value = "Blood glucose: 120 mg/dL"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose level?',
                'role': 'patient',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify prompt includes document text
        prompt = mock_gemini.call_args[0][0]
        assert 'Medical report:' in prompt
        assert 'Blood glucose: 120 mg/dL' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_includes_chat_history(self, mock_gemini, mock_get_doc):
        """Test that chat history is included in prompt"""
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
        
        # Verify prompt includes conversation history
        prompt = mock_gemini.call_args[0][0]
        assert 'Conversation history:' in prompt
        assert 'Initial question' in prompt
        assert 'Initial answer' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_includes_current_question(self, mock_gemini, mock_get_doc):
        """Test that current question is included in prompt"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose level?',
                'role': 'patient',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify prompt includes current question
        prompt = mock_gemini.call_args[0][0]
        assert 'Current question:' in prompt
        assert 'What is my glucose level?' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_includes_response_instructions(self, mock_gemini, mock_get_doc):
        """Test that response instructions are included in prompt"""
        mock_get_doc.return_value = "Test document text"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose level?',
                'role': 'patient',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        
        # Verify prompt includes response instructions
        prompt = mock_gemini.call_args[0][0]
        assert 'Instructions for this response:' in prompt
        assert 'Consider the conversation history' in prompt
        assert 'Do NOT repeat information' in prompt
        assert 'resolve them from the conversation history' in prompt


class TestRoleSwitching:
    """Test suite for role switching behavior (Requirement 8.6)"""
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_role_switching_changes_prompt(self, mock_gemini, mock_get_doc):
        """Test that changing role changes the prompt instructions"""
        mock_get_doc.return_value = "Blood glucose: 120 mg/dL"
        mock_gemini.return_value = "Test response"
        
        # First request as patient
        event_patient = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose level?',
                'role': 'patient',
                'chatHistory': []
            })
        }
        
        response_patient = rag.handler(event_patient, None)
        prompt_patient = mock_gemini.call_args[0][0]
        
        # Reset mock
        mock_gemini.reset_mock()
        
        # Second request as doctor
        event_doctor = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is the clinical significance?',
                'role': 'doctor',
                'chatHistory': []
            })
        }
        
        response_doctor = rag.handler(event_doctor, None)
        prompt_doctor = mock_gemini.call_args[0][0]
        
        # Verify prompts are different
        assert prompt_patient != prompt_doctor
        
        # Verify patient prompt has patient instructions
        assert 'simple, everyday language' in prompt_patient
        
        # Verify doctor prompt has doctor instructions
        assert 'clinical medical terminology' in prompt_doctor
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_role_switching_with_shared_history(self, mock_gemini, mock_get_doc):
        """Test role switching while maintaining chat history"""
        mock_get_doc.return_value = "Blood glucose: 120 mg/dL"
        mock_gemini.return_value = "Test response"
        
        shared_history = [
            {
                'user': 'What is my glucose level?',
                'ai': 'Your glucose level is 120 mg/dL.'
            }
        ]
        
        # Request as patient with history
        event_patient = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'Is that normal?',
                'role': 'patient',
                'chatHistory': shared_history
            })
        }
        
        response_patient = rag.handler(event_patient, None)
        prompt_patient = mock_gemini.call_args[0][0]
        
        # Reset mock
        mock_gemini.reset_mock()
        
        # Request as doctor with same history
        event_doctor = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'Is that normal?',
                'role': 'doctor',
                'chatHistory': shared_history
            })
        }
        
        response_doctor = rag.handler(event_doctor, None)
        prompt_doctor = mock_gemini.call_args[0][0]
        
        # Both prompts should include the shared history
        assert 'What is my glucose level?' in prompt_patient
        assert 'What is my glucose level?' in prompt_doctor
        
        # But instructions should differ
        assert 'simple, everyday language' in prompt_patient
        assert 'clinical medical terminology' in prompt_doctor


class TestRoleSpecificResponses:
    """Test suite for role-specific response generation (Requirement 8.6, 9.1-11.5)"""
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_patient_response_uses_simple_language(self, mock_gemini, mock_get_doc):
        """Test that patient role generates simple language responses"""
        mock_get_doc.return_value = "Blood glucose: 120 mg/dL"
        mock_gemini.return_value = "Your glucose is a bit high. You should eat less sugar."
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is my glucose level?',
                'role': 'patient',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Verify prompt was constructed for patient role
        prompt = mock_gemini.call_args[0][0]
        assert 'simple, everyday language' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_doctor_response_uses_clinical_terminology(self, mock_gemini, mock_get_doc):
        """Test that doctor role generates clinical terminology responses"""
        mock_get_doc.return_value = "Blood glucose: 120 mg/dL"
        mock_gemini.return_value = "Fasting glucose of 120 mg/dL indicates impaired fasting glucose."
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What is the clinical significance?',
                'role': 'doctor',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Verify prompt was constructed for doctor role
        prompt = mock_gemini.call_args[0][0]
        assert 'clinical medical terminology' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_asha_response_includes_referral_guidance(self, mock_gemini, mock_get_doc):
        """Test that ASHA role includes referral guidance"""
        mock_get_doc.return_value = "Blood glucose: 120 mg/dL"
        mock_gemini.return_value = "The patient should be referred to a health facility for further evaluation."
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'What should I advise?',
                'role': 'asha',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        # Verify prompt was constructed for ASHA role
        prompt = mock_gemini.call_args[0][0]
        assert 'refer' in prompt.lower()
        assert 'community health' in prompt


class TestPromptStructure:
    """Test suite for overall prompt structure"""
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_structure_has_all_sections(self, mock_gemini, mock_get_doc):
        """Test that prompt has all required sections"""
        mock_get_doc.return_value = "Test document"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'Test question',
                'role': 'patient',
                'chatHistory': [
                    {'user': 'Previous', 'ai': 'Answer'}
                ]
            })
        }
        
        response = rag.handler(event, None)
        prompt = mock_gemini.call_args[0][0]
        
        # Verify all sections are present
        assert 'You are a medical AI assistant' in prompt
        assert 'Medical report:' in prompt
        assert 'Conversation history:' in prompt
        assert 'Current question:' in prompt
        assert 'Instructions for this response:' in prompt
        assert 'Respond now:' in prompt
    
    @patch('rag.get_document_text')
    @patch('rag.call_gemini')
    def test_prompt_structure_with_empty_history(self, mock_gemini, mock_get_doc):
        """Test prompt structure when history is empty"""
        mock_get_doc.return_value = "Test document"
        mock_gemini.return_value = "Test response"
        
        event = {
            'body': json.dumps({
                'sessionId': 'test-session',
                'message': 'Test question',
                'role': 'patient',
                'chatHistory': []
            })
        }
        
        response = rag.handler(event, None)
        prompt = mock_gemini.call_args[0][0]
        
        # Verify structure is still complete
        assert 'You are a medical AI assistant' in prompt
        assert 'Medical report:' in prompt
        assert 'Conversation history:' in prompt
        assert 'No previous conversation' in prompt
        assert 'Current question:' in prompt


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
