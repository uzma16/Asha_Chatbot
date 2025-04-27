# Asha Chatbot Documentation

## Overview
Asha is an AI-powered career assistant designed specifically for women in tech. It uses advanced natural language processing and retrieval-augmented generation (RAG) to provide personalized career guidance, job recommendations, and mentorship opportunities.

## Table of Contents
1. [Features](#features)
2. [Technical Architecture](#technical-architecture)
3. [Setup Instructions](#setup-instructions)
4. [API Documentation](#api-documentation)
5. [Components](#components)
6. [Data Flow](#data-flow)
7. [Deployment](#deployment)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

## Features

### Core Features
- **Intelligent Chat Interface**
  - Context-aware conversations
  - Session management
  - History tracking
  - Quick action buttons

- **Career Guidance**
  - Job recommendations
  - Skill assessment
  - Career path suggestions
  - Resume feedback

- **Gender Bias Detection**
  - Real-time analysis
  - Alternative phrasing suggestions
  - Inclusive language promotion

- **Multi-Source Integration**
  - HerKey job listings
  - Naukri.com integration
  - Events and workshops
  - Mentorship programs

### Advanced Features
- **RAG System**
  - Document retrieval
  - Semantic search
  - Dynamic content updates
  - Contextual responses

- **Analytics Dashboard**
  - Usage metrics
  - Popular queries
  - User engagement
  - Success tracking

## Technical Architecture

### Frontend (Streamlit)
```python
frontend/
├── app.py                 # Main Streamlit application
├── components/           # UI components
├── utils/               # Helper functions
└── assets/             # Static resources
```

### Backend (FastAPI)
```python
backend/
├── app/
│   ├── main.py          # FastAPI application
│   ├── routers/         # API routes
│   ├── services/        # Business logic
│   ├── models/          # Data models
│   └── utils/           # Utilities
├── tests/              # Test cases
└── config/            # Configuration files
```

## Setup Instructions

### Prerequisites
```bash
# Python 3.9+
python -m venv env
source env/bin/activate  # Linux/Mac
env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
```env
HUGGINGFACEHUB_API_TOKEN=your_token
SERPER_API_KEY=your_key
OPENAI_API_KEY=your_key
DATABASE_URL=your_db_url
```

### Running the Application
```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend
cd frontend
streamlit run app.py
```

## API Documentation

### Chat Endpoints
```python
POST /api/chat
{
    "query": "string",
    "session_id": "string",
    "context": "string"
}

GET /api/chat/history/{session_id}
DELETE /api/chat/history/{session_id}
```

### Job Search Endpoints
```python
GET /api/jobs/search
GET /api/jobs/{job_id}
POST /api/jobs/apply
```

### Events Endpoints
```python
GET /api/events
GET /api/events/{event_id}
POST /api/events/register
```

## Components

### RAG Service
```python
class RAGService:
    """Handles document retrieval and generation"""
    def query(self, question: str) -> str:
        # Document retrieval
        # Context processing
        # Response generation
```

### Chat Service
```python
class ChatService:
    """Manages chat interactions"""
    def process_message(self, chat_request: ChatRequest) -> ChatResponse:
        # Intent classification
        # Bias detection
        # Response generation
```

### Search Service
```python
class SerperService:
    """Handles external search requests"""
    def search(self, query: str) -> List[SearchResult]:
        # API integration
        # Result formatting
        # Cache management
```

## Data Flow

1. **User Input Processing**
   ```mermaid
   graph LR
   A[User Input] --> B[Frontend]
   B --> C[Backend API]
   C --> D[Intent Classification]
   D --> E[Specialized Handler]
   E --> F[Response Generation]
   F --> B
   ```

2. **RAG System Flow**
   ```mermaid
   graph LR
   A[Query] --> B[Document Retrieval]
   B --> C[Context Processing]
   C --> D[LLM Generation]
   D --> E[Response]
   ```

## Deployment

### Docker Setup
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### Cloud Deployment
- AWS EC2 instance
- Docker containers
- Load balancing
- Auto-scaling

## Testing

### Unit Tests
```python
def test_chat_service():
    service = ChatService()
    response = service.process_message(test_request)
    assert response.status == 200
```

### Integration Tests
```python
async def test_rag_integration():
    rag = RAGService()
    result = await rag.query("test query")
    assert result is not None
```

## Troubleshooting

### Common Issues
1. **API Connection Errors**
   - Check API keys
   - Verify network connection
   - Review rate limits

2. **Performance Issues**
   - Monitor cache usage
   - Check database connections
   - Review log files

### Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Contributing
1. Fork the repository
2. Create feature branch
3. Submit pull request
4. Follow code style guidelines

## License
MIT License - See LICENSE file for details