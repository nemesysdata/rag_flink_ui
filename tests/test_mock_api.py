"""
Tests for the mock Q&A API service.
"""

import pytest
from rag_flink_ui.backend.mock_api import MockQAService
import time

def test_mock_service_initialization():
    """Test that the mock service initializes correctly."""
    service = MockQAService()
    assert len(service.responses) > 0
    assert len(service.topics) > 0

def test_mock_service_response_format():
    """Test that the mock service returns responses in the correct format."""
    service = MockQAService()
    response = service.get_response("test question")
    
    assert isinstance(response, dict)
    assert "type" in response
    assert "content" in response
    assert "timestamp" in response
    assert "confidence" in response
    assert "processing_time" in response
    
    assert response["type"] == "response"
    assert isinstance(response["content"], str)
    assert isinstance(response["confidence"], float)
    assert isinstance(response["processing_time"], float)
    
    # Check value ranges
    assert 0.5 <= response["confidence"] <= 1.0
    assert 0.5 <= response["processing_time"] <= 2.0

def test_mock_service_response_variation():
    """Test that the mock service provides varied responses."""
    service = MockQAService()
    responses = set()
    
    # Get multiple responses
    for _ in range(10):
        response = service.get_response("test question")
        responses.add(response["content"])
    
    # Check that we get some variation in responses
    assert len(responses) > 1

def test_mock_service_processing_time():
    """Test that the mock service simulates processing time."""
    service = MockQAService()
    start_time = time.time()
    service.get_response("test question")
    end_time = time.time()
    
    # Check that the response took some time
    assert end_time - start_time >= 0.5 