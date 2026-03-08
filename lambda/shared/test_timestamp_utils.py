"""
Tests for timestamp and ISO8601 formatting utilities
Validates timestamp generation and formatting functions
"""

import unittest
from datetime import datetime, timezone, timedelta
from timestamp_utils import (
    generate_timestamp,
    format_to_iso8601,
    parse_iso8601,
    get_timestamp_ms,
    format_timestamp_for_display,
    get_time_difference,
    is_within_time_window,
    get_session_expiration_time,
    get_time_until_expiration,
    is_expired,
)


class TestTimestampUtilities(unittest.TestCase):
    """Test suite for timestamp utilities"""

    def test_generate_timestamp_format(self):
        """Test that generated timestamp is in valid ISO8601 format"""
        timestamp = generate_timestamp()
        # Should match ISO8601 format with Z suffix
        self.assertRegex(timestamp, r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$')

    def test_generate_timestamp_is_recent(self):
        """Test that generated timestamp is recent"""
        timestamp = generate_timestamp()
        dt = parse_iso8601(timestamp)
        now = datetime.now(timezone.utc)
        diff_ms = abs((now - dt).total_seconds() * 1000)
        self.assertLess(diff_ms, 1000)  # Within 1 second

    def test_format_to_iso8601(self):
        """Test formatting datetime to ISO8601"""
        dt = datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)
        formatted = format_to_iso8601(dt)
        self.assertEqual(formatted, '2024-01-15T10:30:45.123Z')

    def test_parse_iso8601(self):
        """Test parsing ISO8601 string to datetime"""
        iso_string = '2024-01-15T10:30:45.123Z'
        dt = parse_iso8601(iso_string)
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 15)
        self.assertEqual(dt.hour, 10)
        self.assertEqual(dt.minute, 30)

    def test_parse_iso8601_with_plus_offset(self):
        """Test parsing ISO8601 with +00:00 offset"""
        iso_string = '2024-01-15T10:30:45.123+00:00'
        dt = parse_iso8601(iso_string)
        self.assertEqual(dt.year, 2024)
        self.assertEqual(dt.month, 1)

    def test_round_trip_iso8601(self):
        """Test that formatting and parsing preserves datetime"""
        original_dt = datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)
        formatted = format_to_iso8601(original_dt)
        parsed = parse_iso8601(formatted)
        # Allow 1ms difference due to precision
        diff_ms = abs((original_dt - parsed).total_seconds() * 1000)
        self.assertLess(diff_ms, 2)

    def test_get_timestamp_ms(self):
        """Test getting timestamp in milliseconds"""
        ms = get_timestamp_ms()
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        diff = abs(ms - now_ms)
        self.assertLess(diff, 100)  # Within 100ms

    def test_format_timestamp_for_display(self):
        """Test formatting timestamp for display"""
        iso_string = '2024-01-15T10:30:45.123Z'
        formatted = format_timestamp_for_display(iso_string)
        self.assertIn('2024', formatted)
        self.assertIn('01', formatted)
        self.assertIn('15', formatted)

    def test_get_time_difference(self):
        """Test calculating time difference between timestamps"""
        start = '2024-01-15T10:00:00.000Z'
        end = '2024-01-15T10:01:00.000Z'
        diff = get_time_difference(start, end)
        self.assertEqual(diff, 60000)  # 60 seconds in milliseconds

    def test_get_time_difference_negative(self):
        """Test negative time difference"""
        start = '2024-01-15T10:01:00.000Z'
        end = '2024-01-15T10:00:00.000Z'
        diff = get_time_difference(start, end)
        self.assertEqual(diff, -60000)

    def test_get_time_difference_zero(self):
        """Test zero time difference"""
        timestamp = '2024-01-15T10:00:00.000Z'
        diff = get_time_difference(timestamp, timestamp)
        self.assertEqual(diff, 0)

    def test_is_within_time_window_recent(self):
        """Test that recent timestamp is within window"""
        recent_timestamp = generate_timestamp()
        result = is_within_time_window(recent_timestamp, 5000)  # 5 second window
        self.assertTrue(result)

    def test_is_within_time_window_old(self):
        """Test that old timestamp is outside window"""
        old_dt = datetime.now(timezone.utc) - timedelta(hours=1)
        old_timestamp = format_to_iso8601(old_dt)
        result = is_within_time_window(old_timestamp, 5000)  # 5 second window
        self.assertFalse(result)

    def test_get_session_expiration_time(self):
        """Test getting session expiration time (24 hours from now)"""
        expiration = get_session_expiration_time()
        expiration_dt = parse_iso8601(expiration)
        now = datetime.now(timezone.utc)
        diff_hours = (expiration_dt - now).total_seconds() / 3600
        self.assertGreater(diff_hours, 23.9)
        self.assertLess(diff_hours, 24.1)

    def test_get_session_expiration_time_format(self):
        """Test that session expiration time is in valid ISO8601 format"""
        expiration = get_session_expiration_time()
        self.assertRegex(expiration, r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$')

    def test_get_time_until_expiration_future(self):
        """Test getting time until future expiration"""
        future_dt = datetime.now(timezone.utc) + timedelta(hours=1)
        future_timestamp = format_to_iso8601(future_dt)
        time_until = get_time_until_expiration(future_timestamp)
        # Should be approximately 1 hour in milliseconds
        self.assertGreater(time_until, 3500000)  # ~58 minutes
        self.assertLess(time_until, 3700000)     # ~62 minutes

    def test_get_time_until_expiration_past(self):
        """Test getting time until past expiration (negative)"""
        past_dt = datetime.now(timezone.utc) - timedelta(hours=1)
        past_timestamp = format_to_iso8601(past_dt)
        time_until = get_time_until_expiration(past_timestamp)
        self.assertLess(time_until, 0)

    def test_is_expired_future(self):
        """Test that future timestamp is not expired"""
        future_dt = datetime.now(timezone.utc) + timedelta(hours=1)
        future_timestamp = format_to_iso8601(future_dt)
        result = is_expired(future_timestamp)
        self.assertFalse(result)

    def test_is_expired_past(self):
        """Test that past timestamp is expired"""
        past_dt = datetime.now(timezone.utc) - timedelta(hours=1)
        past_timestamp = format_to_iso8601(past_dt)
        result = is_expired(past_timestamp)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
