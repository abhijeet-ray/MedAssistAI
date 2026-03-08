"""
Health Insights UX Improvements - Core Data Models (Python)
Defines data structures for health metrics, chat responses, and API contracts
"""

from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Type aliases
StatusIndicator = Literal["Normal", "Low", "High", "Critical"]
Role = Literal["user", "assistant"]


@dataclass
class HealthMetric:
    """
    Health metric extracted from medical documents
    Represents a single quantifiable medical parameter with reference ranges and status
    """
    metric_name: str                    # e.g., "Hemoglobin"
    value: float                        # e.g., 14.5
    unit: str                           # e.g., "g/dL"
    reference_range_min: float          # e.g., 13.5
    reference_range_max: float          # e.g., 17.5
    status_indicator: StatusIndicator   # Normal, Low, High, or Critical
    extraction_timestamp: str           # ISO8601 format
    category: str                       # e.g., "Blood_Work", "Metabolic_Panel", "Thyroid_Function"
    document_id: Optional[str] = None   # Optional reference to source document

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class ChatResponse:
    """
    Structured chat response with four distinct sections
    Provides organized, scannable AI responses to user queries
    """
    summary: str                        # 1-2 sentence overview
    important_findings: List[str]       # 3-7 key findings as bullet points
    what_it_means: str                  # 2-3 sentences explaining clinical significance
    suggested_action: List[str]         # 1-3 actionable recommendations
    timestamp: str                      # ISO8601 format
    conversation_id: str                # Reference to conversation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class ChatMessage:
    """
    Single message in a chat conversation
    Maintains role, content, and optional structured response for AI messages
    """
    role: Role
    content: str
    timestamp: str                      # ISO8601 format
    structured_response: Optional[ChatResponse] = None  # Only for assistant messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.structured_response:
            data['structured_response'] = self.structured_response.to_dict()
        return data


@dataclass
class ContextWindow:
    """
    Context window for managing conversation history
    Maintains last 3 messages in memory to inform AI responses
    Helps reduce repetition and provide contextual awareness
    """
    conversation_id: str
    user_id: str
    messages: List[ChatMessage]         # Last 3 messages (max)
    last_updated: str                   # ISO8601 format
    expires_at: str                     # ISO8601 format (session end)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'last_updated': self.last_updated,
            'expires_at': self.expires_at,
        }


@dataclass
class DashboardApiResponse:
    """
    Dashboard API response containing extracted health metrics
    Provides structured data for frontend dashboard rendering
    """
    metrics: List[HealthMetric]
    document_count: int
    word_count: int
    extraction_timestamp: str           # ISO8601 format
    status: Literal["success", "partial", "error"]
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'metrics': [m.to_dict() for m in self.metrics],
            'document_count': self.document_count,
            'word_count': self.word_count,
            'extraction_timestamp': self.extraction_timestamp,
            'status': self.status,
            'message': self.message,
        }


@dataclass
class ChatApiResponse:
    """
    Chat API response containing structured chat response
    Provides validated structured response with context information
    """
    response: ChatResponse
    context_window_size: int
    retry_count: int
    timestamp: str                      # ISO8601 format
    status: Literal["success", "error"]
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'response': self.response.to_dict(),
            'context_window_size': self.context_window_size,
            'retry_count': self.retry_count,
            'timestamp': self.timestamp,
            'status': self.status,
            'error_message': self.error_message,
        }


@dataclass
class ApiError:
    """
    Generic API error response
    Standardized error format for all API endpoints
    """
    code: str
    message: str
    retryable: bool
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


# Metric categories for organizing health metrics
METRIC_CATEGORIES = {
    'BLOOD_WORK': 'Blood_Work',
    'METABOLIC_PANEL': 'Metabolic_Panel',
    'THYROID_FUNCTION': 'Thyroid_Function',
}

# Reference ranges for standard medical metrics
# Used when document doesn't provide explicit ranges
REFERENCE_RANGES = {
    'Hemoglobin': {
        'min': 13.5,
        'max': 17.5,
        'unit': 'g/dL',
        'category': METRIC_CATEGORIES['BLOOD_WORK']
    },
    'WBC': {
        'min': 4.5,
        'max': 11.0,
        'unit': 'K/uL',
        'category': METRIC_CATEGORIES['BLOOD_WORK']
    },
    'Platelets': {
        'min': 150,
        'max': 400,
        'unit': 'K/uL',
        'category': METRIC_CATEGORIES['BLOOD_WORK']
    },
    'Blood Glucose': {
        'min': 70,
        'max': 100,
        'unit': 'mg/dL',
        'category': METRIC_CATEGORIES['METABOLIC_PANEL']
    },
    'Cholesterol': {
        'min': 0,
        'max': 200,
        'unit': 'mg/dL',
        'category': METRIC_CATEGORIES['METABOLIC_PANEL']
    },
    'TSH': {
        'min': 0.4,
        'max': 4.0,
        'unit': 'mIU/L',
        'category': METRIC_CATEGORIES['THYROID_FUNCTION']
    },
}
