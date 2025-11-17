# Research-Augmented Conversational Agent

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A fullstack research assistant that performs iterative web research using LangGraph and Google Gemini, providing comprehensive answers with citations through an intuitive web interface.

## 🎯 Project Overview

### What It Does

The Research Agent helps users find comprehensive, well-cited answers to complex questions by:

1. **Understanding Queries**: Accepts natural language questions via web UI or SMS
2. **Intelligent Research**: Generates optimized search queries and explores multiple sources
3. **Iterative Refinement**: Reflects on results quality and searches again if needed
4. **Answer Synthesis**: Combines information from multiple sources into coherent answers
5. **Citation Tracking**: Provides full source attribution with relevance scoring
6. **Real-time Updates**: Shows the agent's reasoning process step-by-step

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Query Input │  │  Timeline   │  │  Citations  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└───────────────────────┬─────────────────────────────────┘
                        │ REST API
┌───────────────────────▼─────────────────────────────────┐
│              Backend (FastAPI + LangGraph)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Research   │  │     SMS      │  │    Health    │ │
│  │   Endpoint   │  │   Webhook    │  │    Check     │ │
│  └──────┬───────┘  └──────────────┘  └──────────────┘ │
│         │                                                │
│  ┌──────▼───────────────────────────────────────────┐  │
│  │           LangGraph Research Agent                │  │
│  │  ┌─────────────┐  ┌──────────┐  ┌────────────┐  │  │
│  │  │   Query     │→ │  Search  │→ │ Reflection │  │  │
│  │  │ Generation  │  │          │  │            │  │  │
│  │  └─────────────┘  └──────────┘  └─────┬──────┘  │  │
│  │                                        │         │  │
│  │  ┌─────────────┐  ┌──────────────────▼──────┐  │  │
│  │  │  Quality    │← │      Synthesis           │  │  │
│  │  │   Check     │  │    (Answer + Citations)  │  │  │
│  │  └─────────────┘  └──────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Gemini     │  │    Search    │  │    Safety    │ │
│  │     LLM      │  │   Providers  │  │   Filters    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└───────────────────────┬─────────────┬───────────────────┘
                        │             │
            ┌───────────▼─────┐   ┌───▼────────┐
            │   PostgreSQL    │   │   Redis    │
            │   (Persistence) │   │  (Cache)   │
            └─────────────────┘   └────────────┘
```

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **API Keys**:
  - [Google Gemini API](https://makersuite.google.com/app/apikey)
  - [LangSmith API](https://smith.langchain.com/)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/simplymuthoni/research-agent.git
cd research-agent

# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

**Minimum required in `.env`:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
POSTGRES_PASSWORD=secure_password_here
SEARCH_PROVIDER=mock  # or gemini for real search
```

### 2. Start All Services

```bash
# Start everything (backend, frontend, database, cache)
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Access the Application

- **🌐 Frontend**: http://localhost:5173 (development) or http://localhost:3000 (production)
- **📡 Backend API**: http://localhost:8000
- **📖 API Docs**: http://localhost:8000/docs
- **💚 Health Check**: http://localhost:8000/api/health

### 4. Test It Out

1. Open http://localhost:5173
2. Enter a question: *"What are the latest developments in quantum computing?"*
3. Watch the agent work through the research process
4. View the synthesized answer with citations

## 📁 Project Structure

```
research-agent/
├── frontend/                    # React + Vite frontend
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # API client & utilities
│   │   └── pages/              # Page components
│   ├── Dockerfile              # Production container
│   ├── Dockerfile.dev          # Development container
│   ├── nginx.conf              # Nginx configuration
│   └── package.json
│
├── backend/                     # FastAPI + LangGraph backend
│   ├── backend/
│   │   ├── main.py             # FastAPI application
│   │   ├── config.py           # Configuration
│   │   ├── langgraph_agent.py  # Research agent
│   │   ├── schemas.py          # Data models
│   │   ├── routes/             # API endpoints
│   │   │   ├── research.py     # Research endpoint
│   │   │   └── sms.py          # SMS webhook
│   │   ├── services/           # Business logic
│   │   │   ├── search.py       # Web search
│   │   │   ├── llm.py          # Gemini LLM
│   │   │   └── synthesis.py    # Answer synthesis
│   │   └── utils/              # Utilities
│   │       ├── db.py           # Database
│   │       ├── cache.py        # Redis cache
│   │       └── filters.py      # Safety filters
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│
├── docker-compose.yml           # Production setup
├── docker-compose.override.yml  # Development overrides
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
└── CAPSTONE.md                  # Project requirements

```

## 🎨 Frontend (React + Vite)

### Features

- **🎯 Clean Interface**: Modern, responsive design
- **⚡ Real-time Updates**: Watch agent execution live
- **📱 Mobile Friendly**: Works on all devices
- **🎨 Beautiful UI**: Tailwind CSS + Shadcn UI components
- **♿ Accessible**: WCAG 2.1 AA compliant

### Key Components

**ResearchForm** - Query input with validation
**Timeline** - Real-time agent step tracking
**Citations** - Source display with links
**AnswerDisplay** - Formatted research results

### Technology Stack

- **React 18** - UI framework
- **Vite 5** - Build tool with HMR
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Shadcn UI** - Component library

### Development

```bash
# Navigate to frontend
cd frontend/

# Install dependencies
npm install

# Start dev server
npm run dev

# Access at http://localhost:5173
```

See [frontend/README.md](./frontend/README.md) for detailed documentation.

## 🔧 Backend (FastAPI + LangGraph)

### Features

- **🤖 LangGraph Agent**: Multi-step research workflow
- **🧠 Google Gemini**: Advanced LLM for synthesis
- **🔍 Multiple Search Options**: Mock, Gemini, SerpAPI, Brave, Google
- **🔒 Safety Filters**: PII, toxicity, hallucination checks
- **📱 SMS Support**: Africa's Talking integration
- **💾 Persistence**: PostgreSQL + Redis

### API Endpoints

#### POST /api/research
Submit research query and receive comprehensive answer.

**Request:**
```json
{
  "query": "What is quantum computing?",
  "source": "web_ui",
  "max_iterations": 3
}
```

**Response:**
```json
{
  "answer": "Quantum computing is...",
  "citations": [
    {
      "title": "Quantum Computing Basics",
      "url": "https://example.com",
      "snippet": "...",
      "relevance_score": 0.95
    }
  ],
  "timeline": [
    {
      "step": "query_generation",
      "description": "Generated 3 search queries",
      "duration_ms": 1200,
      "status": "success"
    }
  ],
  "metadata": {
    "iterations": 2,
    "confidence_score": 0.92
  }
}
```

#### GET /api/health
Check service health.

#### POST /api/sms/inbound
SMS webhook for Africa's Talking.

### Technology Stack

- **FastAPI** - Modern web framework
- **LangGraph** - Agent orchestration
- **Google Gemini** - LLM (gemini-1.5-pro)
- **PostgreSQL** - Data persistence
- **Redis** - Caching & rate limiting
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation

### Development

```bash
# Navigate to backend
cd backend/

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn backend.main:app --reload

# Access at http://localhost:8000
```

See [backend/README.md](./backend/README.md) for detailed documentation.

## 🔍 Search Providers

Multiple search providers supported:

| Provider | API Key Required | Cost | Best For |
|----------|-----------------|------|----------|
| **mock** | No | Free | Development/Testing |
| **gemini** | Gemini key only | Free | MVP/Quick start |
| **serpapi** | Yes | $50/month | Production quality |
| **brave** | Yes | $5/month | Budget production |
| **google** | Yes + Engine ID | $5/1000 queries | Google integration |

### Configuration

In `.env`:
```env
# For development (no extra cost)
SEARCH_PROVIDER=mock

# For MVP (uses existing Gemini key)
SEARCH_PROVIDER=gemini

# For production
SEARCH_PROVIDER=brave
SEARCH_API_KEY=your_brave_api_key
```

## 🔒 Safety & Security

### Built-in Safety Features

#### PII Detection & Redaction
- Social Security Numbers
- Phone numbers
- Email addresses
- Credit card numbers
- IP addresses

#### Content Filtering
- **Toxicity Filter**: Blocks harmful content
- **Prompt Injection**: Prevents malicious prompts
- **Hallucination Check**: Validates answer quality
- **Bias Detection**: Identifies potential biases

#### Security Headers
- XSS Protection
- Content Security Policy
- CORS configuration
- Rate limiting

### Configuration

Enable/disable in `.env`:
```env
ENABLE_PII_FILTER=true
ENABLE_TOXICITY_FILTER=true
ENABLE_HALLUCINATION_CHECK=true
ENABLE_BIAS_DETECTION=true
ENABLE_PROMPT_INJECTION_CHECK=true
```

## 📊 Database & Caching

### PostgreSQL
Stores:
- Research queries and metadata
- Synthesized answers and citations
- Agent execution timeline

**Access:**
```bash
docker-compose exec postgres psql -U postgres -d research
```

### Redis
Used for:
- Search result caching
- Rate limiting
- Session management

**Access:**
```bash
docker-compose exec redis redis-cli
```

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
docker-compose exec langgraph-api pytest

# With coverage
docker-compose exec langgraph-api pytest --cov=backend

# Specific test file
docker-compose exec langgraph-api pytest backend/tests/test_research.py -v
```

### Frontend Tests

```bash
# Run tests (if added)
cd frontend/
npm run test

# E2E tests
npm run test:e2e
```

## 📱 SMS Integration (Optional)

### Setup Africa's Talking

1. Sign up at [Africa's Talking](https://africastalking.com/)
2. Get your API key and username
3. Configure webhook: `https://yourdomain.com/api/sms/inbound`

### Configuration

```env
AT_USERNAME=your_username
AT_API_KEY=your_api_key
AT_WEBHOOK_SECRET=your_secret
ENABLE_SMS=true
```

### Usage

Users can text questions to your shortcode:
```
SMS: "What is artificial intelligence?"
Reply: "Artificial intelligence (AI) is... [citations]"
```

## 🚢 Deployment

### Development

```bash
# Start with hot-reload
docker-compose up

# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

### Production

```bash
# Build and start
docker-compose -f docker-compose.yml up -d --build

# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Cloud Deployment

**Environment Variables for Production:**
```env
APP_ENV=production
LOG_LEVEL=warning
POSTGRES_PASSWORD=strong_secure_password
SEARCH_PROVIDER=brave
NODE_ENV=production
VITE_API_URL=https://api.yourdomain.com
```

**Recommended Platforms:**
- **Backend**: AWS ECS, Google Cloud Run, DigitalOcean App Platform
- **Frontend**: Vercel, Netlify, Cloudflare Pages
- **Database**: AWS RDS, Google Cloud SQL, Supabase
- **Cache**: AWS ElastiCache, Redis Cloud

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose up --build
```

### API Connection Failed

```bash
# Verify backend is running
curl http://localhost:8000/api/health

# Check frontend .env
cat frontend/.env | grep VITE_API_URL

# Should be: VITE_API_URL=http://localhost:8000
```

### Database Issues

```bash
# Reset database (WARNING: deletes data!)
docker-compose down -v
docker-compose up -d
```

### Port Conflicts

```bash
# Check ports in use
sudo lsof -i :8000
sudo lsof -i :5173

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Backend
  - "3001:5173"  # Frontend
```

## 📚 Documentation

- **[Backend README](./backend/README.md)** - Backend detailed docs
- **[Frontend README](./frontend/README.md)** - Frontend detailed docs
- **[Environment Setup](./backend/ENV_SETUP.md)** - Configuration guide
- **[Search Providers](./backend/SEARCH_PROVIDERS.md)** - Search setup
- **[Docker Guide](./backend/DOCKER_GUIDE.md)** - Docker reference
- **[API Docs](http://localhost:8000/docs)** - Interactive API docs

## 🎓 Academic Use

### Capstone Project Checklist

- [x] Fullstack implementation (React + FastAPI)
- [x] LangGraph agent with iterative research
- [x] Multiple search provider integration
- [x] SMS integration (Africa's Talking)
- [x] Docker Compose deployment
- [x] Safety filters (PII, toxicity, hallucination)
- [x] Database persistence
- [x] Caching and rate limiting
- [x] Comprehensive documentation
- [x] API documentation (Swagger)
- [x] Health check endpoints
- [x] Citation tracking
- [x] Real-time timeline

### Citation

```bibtex
@software{research_agent_2025,
  title = {Research-Augmented Conversational Agent},
  author = {Mugo Patricia},
  year = {2025},
  institution = {Africas Talking x Google},
  url = {https://github.com/simplymuthoni/research-agent},
  note = {Capstone Project}
}
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

[MIT License](LICENSE) - See LICENSE file for details

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/simplymuthoni/research-agent/issues)
- **Email**: patriciamuthoni414@gmail.com

## 🙏 Acknowledgments

- **Google Gemini** - Advanced LLM capabilities
- **LangChain/LangGraph** - Agent orchestration framework
- **Africa's Talking** - SMS gateway services
- **FastAPI** - Modern Python web framework
- **React & Vite** - Frontend development

---

**Built with ❤️ for advancing AI research capabilities**

*A capstone project demonstrating fullstack AI application development with production-ready architecture, comprehensive safety features, and intuitive user experience.*