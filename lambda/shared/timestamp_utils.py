"""
Timestamp and ISO8601 formatting utilities for Lambda functions
Provides functions for generating and formatting timestamps in ISO8601 format
"""

from datetime import datetime, timedelta, timezone
from typing import Tuple


def generate_timestamp() -> str:
    """
    Generate current timestamp in ISO8601 format
    
    Returns:
        ISO8601 formatted timestamp string (e.g., "2024-01-15T10:30:45.123Z")
    """
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def format_to_iso8601(dt: datetime) -> str:
    """
    Format a datetime object to ISO8601 string
    
    Args:
        dt: datetime object to format
        
    Returns:
        ISO8601 formatted timestamp string
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def parse_iso8601(iso_string: str) -> datetime:
    """
    Parse ISO8601 string to datetime object
    
    Args:
        iso_string: ISO8601 formatted timestamp string
        
    Returns:
        datetime object
    """
    # Handle Z suffix
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1] + '+00:00'
    return datetime.fromisoformat(iso_string)


def get_timestamp_ms() -> int:
    """
    Get current timestamp in milliseconds since epoch
    
    Returns:
        Milliseconds since epoch
    """
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def format_timestamp_for_display(iso_string: str, locale: str = 'en_US') -> str:
    """
    Format ISO8601 timestamp for display (human-readable)
    
    Args:
        iso_string: ISO8601 formatted timestamp string
        locale: Locale for formatting (default: 'en_US')
        
    Returns:
        Human-readable formatted timestamp
    """
    dt = parse_iso8601(iso_string)
    # Simple format - can be extended with locale support
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def get_time_difference(start_time: str, end_time: str) -> int:
    """
    Calculate time difference between two ISO8601 timestamps
    
    Args:
        start_time: Start timestamp in ISO8601 format
        end_time: End timestamp in ISO8601 format
        
    Returns:
        Difference in milliseconds
    """
    start = parse_iso8601(start_time)
    end = parse_iso8601(end_time)
    diff = end - start
    return int(diff.total_seconds() * 1000)


def is_within_time_window(timestamp: str, window_ms: int) -> bool:
    """
    Check if a timestamp is within a certain time window
    
    Args:
        timestamp: Timestamp to check in ISO8601 format
        window_ms: Time window in milliseconds
        
    Returns:
        True if timestamp is within the window from now
    """
    ts_dt = parse_iso8601(timestamp)
    now = datetime.now(timezone.utc)
    diff_ms = int((now - ts_dt).total_seconds() * 1000)
    return diff_ms <= window_ms


def get_session_expiration_time() -> str:
    """
    Get session expiration timestamp (24 hours from now)
    
    Returns:
        ISO8601 formatted expiration timestamp
    """
    expiration_dt = datetime.now(timezone.utc) + timedelta(hours=24)
    return format_to_iso8601(expiration_dt)


def get_time_until_expiration(expires_at: str) -> int:
    """
    Get time remaining until expiration in milliseconds
    
    Args:
        expires_at: Expiration timestamp in ISO8601 format
        
    Returns:
        Milliseconds until expiration (negative if already expired)
    """
    expiration = parse_iso8601(expires_at)
    now = datetime.now(timezone.utc)
    diff = expiration - now
    return int(diff.total_seconds() * 1000)


def is_expired(expires_at: str) -> bool:
    """
    Check if a timestamp has expired
    
    Args:
        expires_at: Expiration timestamp in ISO8601 format
        
    Returns:
        True if timestamp has expired
    """
    return get_time_until_expiration(expires_at) <= 0
