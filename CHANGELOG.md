# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Kafka consumer service for processing RAG responses
- WebSocket session manager for handling client connections
- Thread-safe session state management
- One question at a time processing
- Comprehensive error handling and recovery
- Detailed logging and monitoring
- Unit tests for new components

### Changed
- Replaced simple connection manager with WebSocket session manager
- Updated WebSocket endpoint to handle session state
- Improved error handling and user feedback
- Enhanced logging for better debugging

### Fixed
- Race conditions in WebSocket message handling
- Resource leaks in connection management
- Error handling in Kafka message processing

## [0.1.0] - 2024-03-19

### Added
- Initial project setup
- FastAPI backend with WebSocket support
- Streamlit frontend
- Kafka integration for question processing
- Basic error handling
- Health check endpoints
- CORS middleware
- Environment variable configuration
- Docker support
- CI/CD pipeline 