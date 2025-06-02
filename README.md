# RAG Flink UI

## Overview
A ChatGPT-like interface that allows users to interact with a Q&A API through a Streamlit frontend and FastAPI backend. The system uses WebSocket for real-time communication and implements session-based message routing.

## Features
- ChatGPT-like chat interface
- Real-time communication via WebSocket
- Session management with UUID v4
- Simple user identification
- In-memory chat history
- FastAPI backend with WebSocket support

## Documentation
- [Architecture Overview](docs/architecture/README.md)
- [API Documentation](docs/api/README.md)
- [Feature Documentation](docs/features/README.md)
- [Development Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Getting Started

### Prerequisites
- Python 3.12
- Poetry for dependency management

### Installation
```bash
# Clone the repository
git clone [repository-url]

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Configuration
1. Set up the environment variables (if needed)
2. Start the FastAPI backend
3. Start the Streamlit frontend

## Development
See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License
This project is licensed under the [LICENSE](LICENSE) - see the LICENSE file for details.
