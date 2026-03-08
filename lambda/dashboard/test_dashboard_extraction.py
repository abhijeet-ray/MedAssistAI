"""
Tests for dashboard health metrics extraction functions.
Tests cover metric extraction, JSON parsing, stat card generation, and error handling.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from dashboard import (
    create_extraction_prompt,
    parse_gemini_extraction,
    generate_stat_cards,
    generate_basic_stat_cards,
    extract_metrics_with_fallback
)


class TestCreateExtractionPrompt:
    """Tests for create_extraction_prompt function"""
    
    def test_prompt_includes_document_text(self):
        """Test that prompt includes the document text"""
        doc_text = "Patient has hemoglobin of 13.5 g/dL"
        prompt = create_extraction_prompt(doc_text)
        assert doc_text in prompt
    
    def test_prompt_requests_json_format(self):
        """Test that prompt explicitly requests JSON format"""
        prompt = create_extraction_prompt("test document")
        assert "JSON" in prompt
        assert "json" in prompt.lower()
    
    def test_prompt_specifies_metric_types(self):
        """Test that prompt specifies all required metric types"""
        prompt = create_extraction_prompt("test document")
        metrics = ["hemoglobin", "wbc", "platelets", "glucose", "cholesterol"]
        for metric in metrics:
            assert metric in prompt
    
    def test_prompt_includes_reference_ranges(self):
        """Test that prompt includes standard medical reference ranges"""
        prompt = create_extraction_prompt("test document")
        # Check for reference ranges
        assert "12-16" in prompt or "14-18" in prompt  # Hemoglobin ranges
        assert "4000-11000" in prompt  # WBC range
        assert "150000-400000" in prompt  # Platelets range
        assert "70-100" in prompt  # Glucose range
        assert "200" in prompt  # Cholesterol range
    
    def test_prompt_includes_abnormal_flag_instruction(self):
        """Test that prompt instructs to mark abnormal flags"""
        prompt = create_extraction_prompt("test document")
        assert "abnormal" in prompt.lower()


class TestParseGeminiExtraction:
    """Tests for parse_gemini_extraction function"""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON response"""
        response = json.dumps({
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": {"value": "7500", "unit": "cells/μL", "abnormal": False},
            "platelets": {"value": "250000", "unit": "cells/μL", "abnormal": False},
            "glucose": {"value": "95", "unit": "mg/dL", "abnormal": False},
            "cholesterol": {"value": "180", "unit": "mg/dL", "abnormal": False},
            "key_findings": ["finding 1"],
            "abnormal_flags": []
        })
        
        result = parse_gemini_extraction(response)
        assert result is not None
        assert result["hemoglobin"]["value"] == "13.5"
        assert result["wbc"]["value"] == "7500"
    
    def test_parse_json_with_markdown_code_blocks(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        json_data = {
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        }
        response = f"```json\n{json.dumps(json_data)}\n```"
        
        result = parse_gemini_extraction(response)
        assert result is not None
        assert result["hemoglobin"]["value"] == "13.5"
    
    def test_parse_json_with_triple_backticks(self):
        """Test parsing JSON wrapped in triple backticks"""
        json_data = {
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        }
        response = f"```\n{json.dumps(json_data)}\n```"
        
        result = parse_gemini_extraction(response)
        assert result is not None
        assert result["hemoglobin"]["value"] == "13.5"
    
    def test_parse_invalid_json_returns_none(self):
        """Test that invalid JSON returns None"""
        response = "This is not JSON"
        result = parse_gemini_extraction(response)
        assert result is None
    
    def test_parse_sets_null_for_missing_metrics(self):
        """Test that missing metric keys are set to null"""
        response = json.dumps({
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "key_findings": [],
            "abnormal_flags": []
        })
        
        result = parse_gemini_extraction(response)
        assert result is not None
        assert result["wbc"] is None
        assert result["platelets"] is None
        assert result["glucose"] is None
        assert result["cholesterol"] is None
    
    def test_parse_preserves_abnormal_flag(self):
        """Test that abnormal flags are preserved"""
        response = json.dumps({
            "hemoglobin": {"value": "10.5", "unit": "g/dL", "abnormal": True},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": ["Low hemoglobin"]
        })
        
        result = parse_gemini_extraction(response)
        assert result["hemoglobin"]["abnormal"] is True


class TestGenerateStatCards:
    """Tests for generate_stat_cards function"""
    
    def test_generate_card_for_hemoglobin(self):
        """Test generating stat card for hemoglobin metric"""
        extracted_data = {
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        }
        
        cards = generate_stat_cards(extracted_data)
        hb_card = next((c for c in cards if c["title"] == "Hemoglobin"), None)
        
        assert hb_card is not None
        assert hb_card["value"] == "13.5"
        assert hb_card["unit"] == "g/dL"
        assert hb_card["severity"] == "normal"
    
    def test_generate_card_for_all_metrics(self):
        """Test generating cards for all metrics"""
        extracted_data = {
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": {"value": "7500", "unit": "cells/μL", "abnormal": False},
            "platelets": {"value": "250000", "unit": "cells/μL", "abnormal": False},
            "glucose": {"value": "95", "unit": "mg/dL", "abnormal": False},
            "cholesterol": {"value": "180", "unit": "mg/dL", "abnormal": False},
            "key_findings": ["Normal results"],
            "abnormal_flags": []
        }
        
        cards = generate_stat_cards(extracted_data)
        titles = [c["title"] for c in cards]
        
        assert "Hemoglobin" in titles
        assert "White Blood Cells" in titles
        assert "Platelets" in titles
        assert "Glucose" in titles
        assert "Cholesterol" in titles
        assert "Key Medical Insights" in titles
    
    def test_abnormal_metric_has_warning_severity(self):
        """Test that abnormal metrics have warning severity"""
        extracted_data = {
            "hemoglobin": {"value": "10.5", "unit": "g/dL", "abnormal": True},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        }
        
        cards = generate_stat_cards(extracted_data)
        hb_card = next((c for c in cards if c["title"] == "Hemoglobin"), None)
        
        assert hb_card["severity"] == "warning"
    
    def test_normal_metric_has_normal_severity(self):
        """Test that normal metrics have normal severity"""
        extracted_data = {
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        }
        
        cards = generate_stat_cards(extracted_data)
        hb_card = next((c for c in cards if c["title"] == "Hemoglobin"), None)
        
        assert hb_card["severity"] == "normal"
    
    def test_key_findings_card_generated(self):
        """Test that Key Medical Insights card is generated from key_findings"""
        extracted_data = {
            "hemoglobin": None,
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": ["Finding 1", "Finding 2"],
            "abnormal_flags": []
        }
        
        cards = generate_stat_cards(extracted_data)
        insights_card = next((c for c in cards if c["title"] == "Key Medical Insights"), None)
        
        assert insights_card is not None
        assert "Finding 1" in insights_card["insight"]
        assert "Finding 2" in insights_card["insight"]
    
    def test_key_findings_card_has_warning_severity_with_abnormal_flags(self):
        """Test that Key Medical Insights card has warning severity when abnormal flags exist"""
        extracted_data = {
            "hemoglobin": None,
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": ["Finding 1"],
            "abnormal_flags": ["Abnormal result"]
        }
        
        cards = generate_stat_cards(extracted_data)
        insights_card = next((c for c in cards if c["title"] == "Key Medical Insights"), None)
        
        assert insights_card["severity"] == "warning"
    
    def test_no_cards_for_null_metrics(self):
        """Test that no cards are generated for null metrics"""
        extracted_data = {
            "hemoglobin": None,
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        }
        
        cards = generate_stat_cards(extracted_data)
        assert len(cards) == 0


class TestGenerateBasicStatCards:
    """Tests for generate_basic_stat_cards function"""
    
    def test_generates_single_card(self):
        """Test that basic stat cards generates a single card"""
        doc_text = "This is a test document with some medical information."
        cards = generate_basic_stat_cards(doc_text)
        
        assert len(cards) == 1
    
    def test_card_has_word_count(self):
        """Test that card contains word count"""
        doc_text = "This is a test document with some medical information."
        cards = generate_basic_stat_cards(doc_text)
        
        card = cards[0]
        assert card["title"] == "Document Processed"
        assert card["unit"] == "words"
        assert card["value"] == "9"
    
    def test_card_has_normal_severity(self):
        """Test that fallback card has normal severity"""
        doc_text = "Test document"
        cards = generate_basic_stat_cards(doc_text)
        
        assert cards[0]["severity"] == "normal"


class TestExtractMetricsWithFallback:
    """Tests for extract_metrics_with_fallback function"""
    
    @patch('dashboard.call_gemini')
    def test_successful_extraction(self, mock_gemini):
        """Test successful metric extraction"""
        mock_gemini.return_value = json.dumps({
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        })
        
        doc_text = "Patient hemoglobin: 13.5 g/dL"
        cards = extract_metrics_with_fallback(doc_text)
        
        assert len(cards) > 0
        assert any(c["title"] == "Hemoglobin" for c in cards)
    
    @patch('dashboard.call_gemini')
    def test_fallback_on_gemini_failure(self, mock_gemini):
        """Test fallback to basic cards when Gemini fails"""
        mock_gemini.return_value = None
        
        doc_text = "Test document with medical information"
        cards = extract_metrics_with_fallback(doc_text)
        
        assert len(cards) > 0
        assert cards[0]["title"] == "Document Processed"
    
    @patch('dashboard.call_gemini')
    def test_fallback_on_invalid_json(self, mock_gemini):
        """Test fallback when Gemini returns invalid JSON"""
        mock_gemini.return_value = "This is not JSON"
        
        doc_text = "Test document"
        cards = extract_metrics_with_fallback(doc_text)
        
        assert len(cards) > 0
        assert cards[0]["title"] == "Document Processed"
    
    @patch('dashboard.call_gemini')
    def test_fallback_on_exception(self, mock_gemini):
        """Test fallback when exception occurs"""
        mock_gemini.side_effect = Exception("API error")
        
        doc_text = "Test document"
        cards = extract_metrics_with_fallback(doc_text)
        
        assert len(cards) > 0
        assert cards[0]["title"] == "Document Processed"
    
    @patch('dashboard.call_gemini')
    def test_partial_extraction_success(self, mock_gemini):
        """Test handling of partial extraction success"""
        mock_gemini.return_value = json.dumps({
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": {"value": "7500", "unit": "cells/μL", "abnormal": False},
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": ["Some findings"],
            "abnormal_flags": []
        })
        
        doc_text = "Test document"
        cards = extract_metrics_with_fallback(doc_text)
        
        # Should have cards for hemoglobin, wbc, and key findings
        assert len(cards) >= 2
        titles = [c["title"] for c in cards]
        assert "Hemoglobin" in titles
        assert "White Blood Cells" in titles


class TestStatCardStructure:
    """Tests for stat card data structure"""
    
    def test_stat_card_has_required_fields(self):
        """Test that stat cards have all required fields"""
        extracted_data = {
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        }
        
        cards = generate_stat_cards(extracted_data)
        card = cards[0]
        
        assert "title" in card
        assert "value" in card
        assert "unit" in card
        assert "insight" in card
        assert "severity" in card
    
    def test_stat_card_severity_values(self):
        """Test that severity values are valid"""
        extracted_data = {
            "hemoglobin": {"value": "13.5", "unit": "g/dL", "abnormal": False},
            "wbc": None,
            "platelets": None,
            "glucose": None,
            "cholesterol": None,
            "key_findings": [],
            "abnormal_flags": []
        }
        
        cards = generate_stat_cards(extracted_data)
        
        for card in cards:
            assert card["severity"] in ["normal", "warning", "critical"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
