"""
Health Insights UX Improvements - Metric Extraction Module
Implements text parsing with regex patterns for health metric extraction
and reference range assignment logic.

Requirements: 1.1, 1.2, 1.6
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Import shared types
import sys
sys.path.insert(0, '../shared')
from health_insights_types import HealthMetric, REFERENCE_RANGES, METRIC_CATEGORIES


# Regex patterns for metric extraction
# Each pattern captures metric value and unit with case-insensitive matching
METRIC_PATTERNS = {
    'Hemoglobin': {
        'patterns': [
            r'hemoglobin[:\s]+(\d+\.?\d*)\s*(g/dL|g/100mL)',
            r'hb[:\s]+(\d+\.?\d*)\s*(g/dL|g/100mL)',
        ],
        'unit_map': {'g/dL': 'g/dL', 'g/100mL': 'g/dL'},
    },
    'WBC': {
        'patterns': [
            r'wbc|white\s+blood\s+cell[:\s]+(\d+\.?\d*)\s*(K/uL|×10\^9/L|10\^9/L)',
            r'wbc[:\s]+(\d+\.?\d*)\s*(K/uL|×10\^9/L|10\^9/L)',
        ],
        'unit_map': {'K/uL': 'K/uL', '×10^9/L': 'K/uL', '10^9/L': 'K/uL'},
    },
    'Platelets': {
        'patterns': [
            r'platelet[:\s]+(\d+\.?\d*)\s*(K/uL|×10\^9/L|10\^9/L)',
            r'plt[:\s]+(\d+\.?\d*)\s*(K/uL|×10\^9/L|10\^9/L)',
        ],
        'unit_map': {'K/uL': 'K/uL', '×10^9/L': 'K/uL', '10^9/L': 'K/uL'},
    },
    'Blood Glucose': {
        'patterns': [
            r'glucose|blood\s+sugar[:\s]+(\d+\.?\d*)\s*(mg/dL|mmol/L)',
            r'glucose[:\s]+(\d+\.?\d*)\s*(mg/dL|mmol/L)',
        ],
        'unit_map': {'mg/dL': 'mg/dL', 'mmol/L': 'mg/dL'},
    },
    'Cholesterol': {
        'patterns': [
            r'cholesterol|total\s+cholesterol[:\s]+(\d+\.?\d*)\s*(mg/dL|mmol/L)',
            r'cholesterol[:\s]+(\d+\.?\d*)\s*(mg/dL|mmol/L)',
        ],
        'unit_map': {'mg/dL': 'mg/dL', 'mmol/L': 'mg/dL'},
    },
    'TSH': {
        'patterns': [
            r'tsh|t3|t4|thyroid[:\s]+(\d+\.?\d*)\s*(mIU/L|pmol/L|ng/dL)',
            r'tsh[:\s]+(\d+\.?\d*)\s*(mIU/L|pmol/L|ng/dL)',
        ],
        'unit_map': {'mIU/L': 'mIU/L', 'pmol/L': 'mIU/L', 'ng/dL': 'mIU/L'},
    },
}


def extract_metric_value(text: str, metric_name: str) -> Optional[Tuple[float, str]]:
    """
    Extract a single metric value from text using regex patterns.
    
    Args:
        text: Document text to search
        metric_name: Name of metric to extract (e.g., 'Hemoglobin')
    
    Returns:
        Tuple of (value, unit) if found, None otherwise
        
    Requirements: 1.1, 1.6
    """
    if metric_name not in METRIC_PATTERNS:
        return None
    
    metric_config = METRIC_PATTERNS[metric_name]
    patterns = metric_config['patterns']
    unit_map = metric_config['unit_map']
    
    # Try each pattern for this metric
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                # Extract value and unit from regex groups
                groups = match.groups()
                
                # Find the numeric value and unit in the groups
                value_str = None
                unit_str = None
                
                for group in groups:
                    if group is not None:
                        # Check if it's a number
                        try:
                            float(group)
                            value_str = group
                        except ValueError:
                            # It's a unit
                            unit_str = group
                
                if value_str and unit_str:
                    value = float(value_str)
                    # Map unit to standard format
                    standard_unit = unit_map.get(unit_str, unit_str)
                    return (value, standard_unit)
            except (ValueError, IndexError):
                continue
    
    return None


def extract_metrics(document_text: str) -> List[HealthMetric]:
    """
    Parse document text and extract all health metrics.
    
    Searches for all six metric types using regex patterns with case-insensitive
    matching and multiple unit format support. Returns array of extracted metrics
    with reference ranges assigned.
    
    Args:
        document_text: Raw text from medical document
    
    Returns:
        List of HealthMetric objects with values and reference ranges
        
    Requirements: 1.1, 1.6
    """
    if not document_text or not isinstance(document_text, str):
        return []
    
    metrics = []
    extraction_timestamp = datetime.utcnow().isoformat()
    
    # Try to extract each metric type
    for metric_name in METRIC_PATTERNS.keys():
        result = extract_metric_value(document_text, metric_name)
        
        if result:
            value, unit = result
            
            # Get reference range for this metric
            ref_range = REFERENCE_RANGES.get(metric_name)
            if not ref_range:
                continue
            
            # Create HealthMetric object
            metric = HealthMetric(
                metric_name=metric_name,
                value=value,
                unit=unit,
                reference_range_min=ref_range['min'],
                reference_range_max=ref_range['max'],
                status_indicator='Normal',  # Will be calculated later
                extraction_timestamp=extraction_timestamp,
                category=ref_range['category'],
            )
            
            metrics.append(metric)
    
    return metrics


def assign_reference_ranges(metrics: List[HealthMetric]) -> List[HealthMetric]:
    """
    Assign reference ranges to extracted metrics.
    
    Attaches standard medical reference ranges to each metric. Supports both
    document-provided ranges and standard ranges from REFERENCE_RANGES lookup table.
    
    Args:
        metrics: List of extracted metrics (may have partial range info)
    
    Returns:
        List of metrics with complete reference range information
        
    Requirements: 1.2
    """
    if not metrics:
        return []
    
    updated_metrics = []
    
    for metric in metrics:
        # Check if metric already has reference ranges
        if metric.reference_range_min is not None and metric.reference_range_max is not None:
            # Already has ranges, keep as is
            updated_metrics.append(metric)
        else:
            # Look up standard ranges
            ref_range = REFERENCE_RANGES.get(metric.metric_name)
            if ref_range:
                # Update metric with standard ranges
                metric.reference_range_min = ref_range['min']
                metric.reference_range_max = ref_range['max']
                metric.category = ref_range['category']
            
            updated_metrics.append(metric)
    
    return updated_metrics


def calculate_status(value: float, ref_min: float, ref_max: float) -> str:
    """
    Calculate status indicator based on value and reference range.
    
    Determines if value is Normal, Low, High, or Critical based on deviation
    from reference range boundaries.
    
    Status logic:
    - Normal: value within [ref_min, ref_max]
    - Low: value < ref_min (but not critical)
    - Critical Low: value < ref_min * 0.7
    - High: value > ref_max (but not critical)
    - Critical High: value > ref_max * 1.3
    
    Args:
        value: Metric value
        ref_min: Reference range minimum
        ref_max: Reference range maximum
    
    Returns:
        Status indicator string: 'Normal', 'Low', 'High', or 'Critical'
    """
    if value < ref_min:
        # Below minimum - check if critical
        if value < (ref_min * 0.7):
            return 'Critical'
        else:
            return 'Low'
    elif value > ref_max:
        # Above maximum - check if critical
        if value > (ref_max * 1.3):
            return 'Critical'
        else:
            return 'High'
    else:
        # Within range
        return 'Normal'


def extract_and_assign_metrics(document_text: str) -> List[HealthMetric]:
    """
    Complete metric extraction pipeline: extract metrics and assign reference ranges.
    
    Combines extraction and reference range assignment in a single operation.
    
    Args:
        document_text: Raw text from medical document
    
    Returns:
        List of HealthMetric objects with values, reference ranges, and status indicators
        
    Requirements: 1.1, 1.2, 1.6
    """
    # Extract metrics from document
    metrics = extract_metrics(document_text)
    
    # Assign reference ranges
    metrics = assign_reference_ranges(metrics)
    
    # Calculate status indicators
    for metric in metrics:
        metric.status_indicator = calculate_status(
            metric.value,
            metric.reference_range_min,
            metric.reference_range_max
        )
    
    return metrics
