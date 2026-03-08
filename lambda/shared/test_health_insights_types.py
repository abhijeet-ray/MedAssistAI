"""
Tests for Health Insights data models (Python)
Validates type definitions and constants
"""

import unittest
from health_insights_types import (
    HealthMetric,
    ChatResponse,
    ChatMessage,
    ContextWindow,
    DashboardApiResponse,
    ChatApiResponse,
    ApiError,
    METRIC_CATEGORIES,
    REFERENCE_RANGES,
)


class TestHealthMetric(unittest.TestCase):
    """Test suite for HealthMetric"""

    def test_create_health_metric(self):
        """Test creating a valid health metric"""
        metric = HealthMetric(
            metric_name='Hemoglobin',
            value=14.5,
            unit='g/dL',
            reference_range_min=13.5,
            reference_range_max=17.5,
            status_indicator='Normal',
            extraction_timestamp='2024-01-15T10:30:45.123Z',
            category='Blood_Work',
        )
        self.assertEqual(metric.metric_name, 'Hemoglobin')
        self.assertEqual(metric.value, 14.5)
        self.assertEqual(metric.status_indicator, 'Normal')

    def test_health_metric_to_dict(self):
        """Test converting health metric to dictionary"""
        metric = HealthMetric(
            metric_name='Hemoglobin',
            value=14.5,
            unit='g/dL',
            reference_range_min=13.5,
            reference_range_max=17.5,
            status_indicator='Normal',
            extraction_timestamp='2024-01-15T10:30:45.123Z',
            category='Blood_Work',
        )
        metric_dict = metric.to_dict()
        self.assertEqual(metric_dict['metric_name'], 'Hemoglobin')
        self.assertEqual(metric_dict['value'], 14.5)
        self.assertIsNone(metric_dict['document_id'])

    def test_health_metric_with_document_id(self):
        """Test health metric with optional document_id"""
        metric = HealthMetric(
            metric_name='WBC',
            value=7.5,
            unit='K/uL',
            reference_range_min=4.5,
            reference_range_max=11.0,
            status_indicator='Normal',
            extraction_timestamp='2024-01-15T10:30:45.123Z',
            category='Blood_Work',
            document_id='doc-123',
        )
        self.assertEqual(metric.document_id, 'doc-123')


class TestChatResponse(unittest.TestCase):
    """Test suite for ChatResponse"""

    def test_create_chat_response(self):
        """Test creating a valid chat response"""
        response = ChatResponse(
            summary='Your blood work shows normal levels.',
            important_findings=['Hemoglobin is normal', 'WBC is elevated', 'Platelets are normal'],
            what_it_means='Your results indicate good overall health with one minor concern.',
            suggested_action=['Monitor WBC levels', 'Follow up in 3 months'],
            timestamp='2024-01-15T10:30:45.123Z',
            conversation_id='conv-123',
        )
        self.assertEqual(response.summary, 'Your blood work shows normal levels.')
        self.assertEqual(len(response.important_findings), 3)
        self.assertEqual(len(response.suggested_action), 2)

    def test_chat_response_to_dict(self):
        """Test converting chat response to dictionary"""
        response = ChatResponse(
            summary='Summary',
            important_findings=['Finding 1', 'Finding 2', 'Finding 3'],
            what_it_means='Meaning',
            suggested_action=['Action 1'],
            timestamp='2024-01-15T10:30:45.123Z',
            conversation_id='conv-123',
        )
        response_dict = response.to_dict()
        self.assertEqual(response_dict['summary'], 'Summary')
        self.assertEqual(len(response_dict['important_findings']), 3)


class TestChatMessage(unittest.TestCase):
    """Test suite for ChatMessage"""

    def test_create_user_message(self):
        """Test creating a user message"""
        message = ChatMessage(
            role='user',
            content='What do my results mean?',
            timestamp='2024-01-15T10:30:45.123Z',
        )
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, 'What do my results mean?')
        self.assertIsNone(message.structured_response)

    def test_create_assistant_message_with_response(self):
        """Test creating an assistant message with structured response"""
        response = ChatResponse(
            summary='Your results are normal.',
            important_findings=['Finding 1', 'Finding 2', 'Finding 3'],
            what_it_means='This means you are healthy.',
            suggested_action=['Action 1'],
            timestamp='2024-01-15T10:30:45.123Z',
            conversation_id='conv-123',
        )
        message = ChatMessage(
            role='assistant',
            content='Your results are normal.',
            timestamp='2024-01-15T10:30:45.123Z',
            structured_response=response,
        )
        self.assertEqual(message.role, 'assistant')
        self.assertIsNotNone(message.structured_response)
        self.assertEqual(message.structured_response.summary, 'Your results are normal.')

    def test_chat_message_to_dict(self):
        """Test converting chat message to dictionary"""
        message = ChatMessage(
            role='user',
            content='Hello',
            timestamp='2024-01-15T10:30:45.123Z',
        )
        message_dict = message.to_dict()
        self.assertEqual(message_dict['role'], 'user')
        self.assertEqual(message_dict['content'], 'Hello')


class TestContextWindow(unittest.TestCase):
    """Test suite for ContextWindow"""

    def test_create_context_window(self):
        """Test creating a context window"""
        message = ChatMessage(
            role='user',
            content='Hello',
            timestamp='2024-01-15T10:30:45.123Z',
        )
        context = ContextWindow(
            conversation_id='conv-123',
            user_id='user-456',
            messages=[message],
            last_updated='2024-01-15T10:30:45.123Z',
            expires_at='2024-01-16T10:30:45.123Z',
        )
        self.assertEqual(context.conversation_id, 'conv-123')
        self.assertEqual(len(context.messages), 1)
        self.assertEqual(context.messages[0].role, 'user')

    def test_context_window_to_dict(self):
        """Test converting context window to dictionary"""
        message = ChatMessage(
            role='user',
            content='Hello',
            timestamp='2024-01-15T10:30:45.123Z',
        )
        context = ContextWindow(
            conversation_id='conv-123',
            user_id='user-456',
            messages=[message],
            last_updated='2024-01-15T10:30:45.123Z',
            expires_at='2024-01-16T10:30:45.123Z',
        )
        context_dict = context.to_dict()
        self.assertEqual(context_dict['conversation_id'], 'conv-123')
        self.assertEqual(len(context_dict['messages']), 1)


class TestApiResponses(unittest.TestCase):
    """Test suite for API response types"""

    def test_dashboard_api_response(self):
        """Test creating a dashboard API response"""
        response = DashboardApiResponse(
            metrics=[],
            document_count=1,
            word_count=500,
            extraction_timestamp='2024-01-15T10:30:45.123Z',
            status='success',
        )
        self.assertEqual(response.status, 'success')
        self.assertEqual(response.document_count, 1)
        self.assertEqual(len(response.metrics), 0)

    def test_dashboard_api_response_to_dict(self):
        """Test converting dashboard API response to dictionary"""
        response = DashboardApiResponse(
            metrics=[],
            document_count=1,
            word_count=500,
            extraction_timestamp='2024-01-15T10:30:45.123Z',
            status='success',
        )
        response_dict = response.to_dict()
        self.assertEqual(response_dict['status'], 'success')
        self.assertEqual(response_dict['document_count'], 1)

    def test_chat_api_response(self):
        """Test creating a chat API response"""
        chat_response = ChatResponse(
            summary='Summary',
            important_findings=['Finding 1', 'Finding 2', 'Finding 3'],
            what_it_means='Meaning',
            suggested_action=['Action 1'],
            timestamp='2024-01-15T10:30:45.123Z',
            conversation_id='conv-123',
        )
        response = ChatApiResponse(
            response=chat_response,
            context_window_size=3,
            retry_count=0,
            timestamp='2024-01-15T10:30:45.123Z',
            status='success',
        )
        self.assertEqual(response.status, 'success')
        self.assertEqual(response.context_window_size, 3)

    def test_api_error(self):
        """Test creating an API error"""
        error = ApiError(
            code='EXTRACTION_ERROR',
            message='Failed to extract metrics',
            retryable=True,
        )
        self.assertEqual(error.code, 'EXTRACTION_ERROR')
        self.assertTrue(error.retryable)


class TestConstants(unittest.TestCase):
    """Test suite for constants"""

    def test_metric_categories(self):
        """Test metric categories constant"""
        self.assertEqual(METRIC_CATEGORIES['BLOOD_WORK'], 'Blood_Work')
        self.assertEqual(METRIC_CATEGORIES['METABOLIC_PANEL'], 'Metabolic_Panel')
        self.assertEqual(METRIC_CATEGORIES['THYROID_FUNCTION'], 'Thyroid_Function')

    def test_reference_ranges(self):
        """Test reference ranges constant"""
        self.assertIn('Hemoglobin', REFERENCE_RANGES)
        self.assertIn('WBC', REFERENCE_RANGES)
        self.assertIn('Platelets', REFERENCE_RANGES)
        self.assertIn('Blood Glucose', REFERENCE_RANGES)
        self.assertIn('Cholesterol', REFERENCE_RANGES)
        self.assertIn('TSH', REFERENCE_RANGES)

    def test_reference_range_structure(self):
        """Test reference range structure"""
        hemo = REFERENCE_RANGES['Hemoglobin']
        self.assertEqual(hemo['min'], 13.5)
        self.assertEqual(hemo['max'], 17.5)
        self.assertEqual(hemo['unit'], 'g/dL')
        self.assertEqual(hemo['category'], 'Blood_Work')


if __name__ == '__main__':
    unittest.main()
