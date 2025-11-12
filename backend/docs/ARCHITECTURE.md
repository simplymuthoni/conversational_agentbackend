# System Architecture

## Components
1. **FastAPI Backend** - REST API & WebSocket
2. **LangGraph Agent** - Multi-step reasoning
3. **PostgreSQL** - Conversation history
4. **Redis** - Caching & rate limiting

## Data Flow
```
User → SMS/API → FastAPI → LangGraph Agent
                              ↓
                         Web Search
                              ↓
                         Gemini LLM
                              ↓
                         PostgreSQL (save)
                              ↓
                         Response → User
```

## External APIs
- **Gemini**: LLM inference
- **Africa's Talking**: SMS gateway
- **Tavily/SerpAPI**: Web search
- **LangSmith**: Observability