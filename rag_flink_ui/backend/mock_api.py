"""
Mock API service for testing the frontend.
"""

import random
from typing import Dict, List
import json
from datetime import datetime

class MockQAService:
    """Mock Q&A service that simulates responses."""
    
    def __init__(self):
        """Initialize the mock service with some predefined responses."""
        self.responses = [
            "I understand your question about {topic}. Here's what I know...",
            "That's an interesting question! Let me explain...",
            "Based on my knowledge, I can tell you that...",
            "I'm not entirely sure about that, but I think...",
            "Let me break this down for you...",
        ]
        
        self.topics = [
            "data processing",
            "streaming",
            "machine learning",
            "data analysis",
            "big data",
            "distributed systems",
            "real-time processing",
            "data pipelines",
        ]

    def get_response(self, message: str) -> Dict:
        """
        Generate a mock response for the given message.
        
        Args:
            message: The user's message
            
        Returns:
            Dict containing the response data
        """
        # Simulate some processing time
        import time
        time.sleep(random.uniform(0.5, 2.0))
        
        # Extract a random topic
        topic = random.choice(self.topics)
        
        # Generate a response
        response = random.choice(self.responses).format(topic=topic)
        
        return {
            "type": "response",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": random.uniform(0.5, 1.0),
            "processing_time": random.uniform(0.5, 2.0)
        }

# Create a singleton instance
mock_service = MockQAService() 