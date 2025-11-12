# Capstone Project: Research-Augmented Conversational Agent

## Overview

A production-capable fullstack research assistant that accepts user queries through web UI and SMS, performs iterative web research using LangGraph and Google Gemini, and synthesizes comprehensive answers with citations.

### Key Features

- **Multi-channel input**: Web interface and SMS (via Africa's Talking)
- **Intelligent research**: Iterative query generation, web search, reflection, and synthesis
- **Real-time feedback**: Activity timeline showing agent's research process
- **Cited responses**: All answers include source citations
- **Production-ready**: Containerized deployment with Docker Compose

## Architecture

### System Components

```
┌─────────────┐
│   Frontend  │  React + Vite
│   (Web UI)  │  - Query input
└──────┬──────┘  - Activity timeline
       │         - Citation display
       │
┌──────▼──────────────────────────┐
│        FastAPI Backend          │
│  ┌──────────────────────────┐  │
│  │   LangGraph Agent        │  │
│  │  • Query generation      │  │
│  │  • Web search connector  │  │
│  │  • Reflection loop       │  │
│  │  • Answer synthesis      │  │
│  └──────────────────────────┘  │
└──────┬──────────────────────────┘
       │
┌──────▼──────┐    ┌─────────────┐
│  Redis      │    │  Postgres   │
│  (Pub/Sub)  │    │ (Persistence)│
└─────────────┘    └─────────────┘

External Services:
• Google Gemini (LLM)
• LangSmith/LangGraph (Orchestration)
• Africa's Talking (SMS)
```

### Technology Stack

- **Frontend**: React, Vite
- **Backend**: FastAPI, LangGraph, Python
- **LLM**: Google Gemini
- **Infrastructure**: Docker, Docker Compose, Redis, PostgreSQL
- **SMS**: Africa's Talking API

## Learning Objectives

1. Build a production-capable fullstack application with React and FastAPI
2. Implement a LangGraph agent with iterative research capabilities
3. Integrate two-way SMS communication for mobile access
4. Containerize and deploy using Docker Compose with proper secrets management
5. Design comprehensive tests and evaluation metrics
6. Implement AI safety measures (hallucination checks, PII detection, toxicity filtering)

## Minimum Viable Product (MVP)

### Core Requirements

- **Input**: Accept queries via web UI or SMS
- **Processing Pipeline**:
  1. Generate search queries
  2. Execute web searches
  3. Reflect on results
  4. Iterate if needed
  5. Synthesize final answer
- **Output**: Coherent answer with citations and activity timeline

### Success Criteria

- End-to-end execution returns coherent answers with at least one citation
- Activity timeline displays agent's research process
- AI safety blocks implemented:
  - Hallucination detection
  - PII checker
  - Toxicity filter
  - Bias detection
  - Prompt injection protection

### Error Handling

- Missing API keys
- Rate limit exceeded
- Search failures
- License errors

## Project Scope

### Assumptions

- Developer has basic Python (FastAPI) and React (Vite) experience
- Docker and Docker Compose knowledge
- Required API keys available:
  - `GEMINI_API_KEY`
  - `LANGSMITH_API_KEY` or `LANGGRAPH_CLOUD_LICENSE_KEY`
  - `AFRICAS_TALKING_API_KEY` (for SMS features)

### Two Development Tracks

**MVP Track**: Core research loop with web UI  
**Production Track**: Robust infrastructure, comprehensive tests, SMS integration, monitoring

## Timeline & Estimates

### Solo Developer (Recommended)

**MVP Phase: 4–6 weeks (160–240 hours)**

- **Week 0** (Planning): 4–8 hours
  - Environment setup
  - API key acquisition
  - Architecture review

- **Week 1** (Backend Core): 16–24 hours
  - FastAPI setup
  - LangGraph graph implementation
  - Prompt engineering

- **Week 2** (Search Integration): 24–32 hours
  - Web search connector
  - Data ingestion pipeline
  - Citation extraction

- **Week 3** (Frontend MVP): 24–32 hours
  - React UI components
  - Streaming timeline
  - Results display

- **Week 4** (Integration & Testing): 24–40 hours
  - Docker Compose setup
  - Persistence layer
  - Unit and integration tests
  - Demo preparation

**Production Enhancement: +4–8 weeks (160–320 hours)**

- PostgreSQL integration
- Metrics and monitoring
- SMS integration
- CI/CD pipeline
- Advanced secrets management

### Team of 2–3 Engineers

- **MVP**: 2–3 weeks (parallel development)
- **Production**: 3–6 additional weeks

## Milestones & Deliverables

### M1: Repository Foundation (1 day)
- Repository structure
- README.md with setup instructions
- `.env.example` template
- Initial documentation

### M2: LangGraph Agent Core (4–7 days)
- Query generation logic
- Reflection mechanism
- Answer synthesis
- Prompt templates

### M3: Search Integration (3–5 days)
- Search API adapter
- Response parsing
- Citation extraction
- Data ingestion pipeline

### M4: Frontend MVP (3–5 days)
- Query input interface
- Activity timeline component
- Results and citations display
- Error handling UI

### M5: Containerization (2–3 days)
- Dockerfile
- docker-compose.yml
- Development override configuration
- Demo script

### M6: Production Polish (2–6 weeks)
- Data persistence (PostgreSQL)
- Comprehensive test suite
- CI/CD integration
- SMS integration
- Monitoring and observability

## Acceptance Criteria

### Repository Structure
```
project-root/
├── README.md
├── pyproject.toml
├── CAPSTONE.md
├── .gitignore
├── docker-compose.yml
├── docker-compose.override.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── langgraph_agent.py
│   ├── schemas.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── research.py
│   │   └── sms.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search.py
│   │   ├── llm.py
│   │   └── synthesis.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── cache.py
│   │   └── filters.py
│   |── tests/
│   ├── __init__.py
│   └── test_research.py
|   ├── docs/
|   │   ├── architecture.md
|   │   ├── setup.md
|   │   ├── security.md
|   │   └── integrations/
|   │       ├── gemini.md
|   │       └── africastalking.md
└── frontend/
    ├── src/
    ├── public/
    └── package.json
```

### Functional Requirements

✅ Local deployment via Docker Compose  
✅ Agent executes full research cycle  
✅ Frontend displays timeline and results  
✅ Citations included in responses  
✅ No startup errors with correct API keys  
✅ Basic error handling implemented

## Testing & Evaluation

### Test Coverage

**Unit Tests**
- Prompt template validation
- Query generation logic
- Citation parsing
- Error handling

**Integration Tests**
- Agent workflow with mocked search
- API endpoint responses
- Database operations

**End-to-End Tests**
- 5–10 test questions
- Assertion: non-empty answers
- Assertion: at least one citation per answer

### Evaluation Metrics

- **Latency**: Median and P95 response times
- **Citation Coverage**: Percentage of answers with citations
- **Success Rate**: Successful completions across test prompts
- **Quality**: Human evaluation of accuracy and usefulness (10–20 samples)

### Human Evaluation

Blind review of 10–20 outputs assessing:
- Factual accuracy
- Citation relevance
- Answer completeness
- Response clarity

## Demo Scenarios

### 1. Technical Research Query
**Query**: "What are the latest trends in wind turbine technology?"

**Expected Output**:
- Generated search queries displayed in timeline
- Interim search results shown
- Final synthesized answer with citations
- Links to authoritative sources

### 2. SMS Integration Demo
**Setup**: Use ngrok for local webhook testing

**Flow**:
1. Send question via SMS to Africa's Talking number
2. System receives webhook
3. Agent processes query
4. Response sent back via SMS

### 3. Failure Handling
**Query**: Obscure or unanswerable question

**Expected Output**:
- Reflection loop iterations visible
- Graceful fallback message
- Explanation of limitations

## Quick Start Commands

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd <project-directory>

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### Development Mode
```bash
# Start with hot-reload (mounts source code)
docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build

# View logs
docker-compose logs -f langgraph-api

# Verify environment variables
docker-compose exec langgraph-api env | grep -E 'LANGSMITH|LANGGRAPH|GEMINI'
```

### Production Mode
```bash
# Build and start services
docker-compose up --build -d

# Check service health
docker-compose ps

# Stop services
docker-compose down

# Clean up (including volumes)
docker-compose down -v
```

### Optional: Build Custom Image
```bash
docker build -t gemini-fullstack-langgraph -f Dockerfile .
```

## Security & Ethics

### Security Best Practices

🔒 **Never commit secrets to git**
- Add `.env` to `.gitignore`
- Provide only `.env.example` template
- Use Docker secrets in production

🔒 **PII Protection**
- Redact personal information in logs
- Implement PII detection in agent pipeline
- Follow data privacy regulations

🔒 **SMS Security**
- Rate limit SMS endpoints
- Validate webhook signatures
- Follow Africa's Talking policies

### Ethical Considerations

- Respect `robots.txt` and website terms of service
- Prefer official search APIs over scraping
- Implement bias detection in responses
- Provide source attribution for all claims
- Handle sensitive topics responsibly

## Risk Management

### Identified Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LangGraph license failures | High | Clear documentation, validation scripts |
| LLM cost overruns | Medium | Caching, request limits, monitoring |
| Rate limit exceeded | Medium | Exponential backoff, request queuing |
| Data privacy violations | High | PII detection, data retention policy |
| Search API unavailable | Medium | Fallback mechanisms, error handling |

## Grading Rubric

### Functionality (40%)
- Web UI operates correctly
- API endpoints functional
- Agent completes research cycle
- SMS demo working

### Answer Quality (25%)
- Citation coverage
- Response clarity
- Factual accuracy (human-evaluated)
- Appropriate handling of ambiguity

### Engineering & Reproducibility (20%)
- Test coverage
- Docker Compose setup
- Documentation quality
- Code organization

### Presentation (15%)
- Demo video
- Final writeup
- Code walkthrough
- Architecture explanation

## Next Steps

### Immediate Actions

1. **Setup Repository**
   - Create project structure
   - Add `.env.example` (no secrets)
   - Initialize git with proper `.gitignore`

2. **Backend Foundation**
   - Scaffold FastAPI application
   - Implement basic LangGraph graph
   - Create prompt templates

3. **Prototyping**
   - Mock LLM responses for rapid development
   - Mock search API for testing
   - Build minimal UI for feedback

4. **Iteration**
   - Test with real APIs
   - Refine prompts based on results
   - Expand test coverage

### Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Gemini API](https://ai.google.dev/)
- [Africa's Talking API](https://africastalking.com/api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Guide](https://docs.docker.com/compose/)

---

**Project Duration**: 4–14 weeks depending on scope  
**Difficulty**: Intermediate to Advanced  
**Prerequisites**: Python, React, Docker, API integration experience