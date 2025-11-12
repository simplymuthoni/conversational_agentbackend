# Developer Setup

## Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Git

## Environment Variables
Copy `.env.example` to `.env` and fill in:
```bash
# Required
GEMINI_API_KEY=       # Get from: https://aistudio.google.com/
LANGSMITH_API_KEY=    # Get from: https://smith.langchain.com/
AT_API_KEY=           # Get from: https://account.africastalking.com/
AT_USERNAME=          # Your AT username

# Optional (defaults provided)
POSTGRES_PASSWORD=your_secure_password
```

## Quick Start
```bash
# 1. Clone & setup
git clone <repo>
cd backend
cp .env.example .env

# 2. Start services
docker compose up -d

# 3. Run migrations
docker compose exec backend alembic upgrade head

# 4. Test
curl http://localhost:8000/docs
```

## API Testing
- Swagger UI: http://localhost:8000/docs
- Postman Collection: `docs/postman/collection.json`