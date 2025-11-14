# Frontend Integration Guide

Complete guide to running the Research Agent with frontend.

## 📁 Required Files Structure

Make sure your frontend folder has these files:

```
frontend/
├── Dockerfile           # ← Create this (production build)
├── Dockerfile.dev       # ← Create this (development)
├── nginx.conf           # ← Create this (nginx config)
├── .env.example         # ← Create this
├── package.json         # ✓ Already from Lovable
├── package-lock.json    # ✓ Already from Lovable
├── vite.config.ts       # ✓ Already from Lovable
├── src/                 # ✓ Already from Lovable
└── public/              # ✓ Already from Lovable
```

## 🚀 Quick Start

### 1. Setup Frontend Files

Create the 4 new files in your `frontend/` directory (see artifacts above):
- `Dockerfile` - Production build
- `Dockerfile.dev` - Development with hot-reload
- `nginx.conf` - Nginx configuration
- `.env.example` - Environment template

### 2. Update Frontend API Configuration

In your frontend code (likely in `src/lib/api.ts` or similar), update the API URL:

```typescript
// Before (Lovable default)
const API_URL = "http://localhost:8000";

// After (use environment variable)
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

### 3. Start Everything

```bash
# Development mode (with hot-reload)
docker-compose up

# Or in background
docker-compose up -d
```

### 4. Access Your Application

- **Frontend**: http://localhost:5173 (dev) or http://localhost:3000 (prod)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🔧 Development vs Production

### Development Mode (Default)

```bash
docker-compose up
```

**What you get:**
- ✅ Hot-reload for frontend (port 5173)
- ✅ Hot-reload for backend (port 8000)
- ✅ Code changes reflect instantly
- ✅ Vite dev server

### Production Mode

```bash
docker-compose -f docker-compose.yml up
```

**What you get:**
- ✅ Optimized frontend build
- ✅ Nginx serving static files (port 3000)
- ✅ Better performance
- ✅ Smaller image size

---

## 🎯 Frontend Configuration

### Option 1: Use .env File (Recommended)

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
NODE_ENV=development
```

### Option 2: Use Root .env

Add to your root `.env`:
```env
VITE_API_URL=http://localhost:8000
FRONTEND_PORT=5173
NODE_ENV=development
```

---

## 📝 Update Frontend Code

### 1. API Client Setup

Create or update `src/lib/api.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  async research(query: string, source: string = 'web_ui') {
    const response = await fetch(`${API_BASE_URL}/api/research`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, source }),
    });
    
    if (!response.ok) {
      throw new Error('Research request failed');
    }
    
    return response.json();
  },
  
  async healthCheck() {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.json();
  }
};
```

### 2. Example React Component

```typescript
import { useState } from 'react';
import { api } from './lib/api';

function ResearchForm() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const data = await api.research(query);
      setResult(data);
    } catch (error) {
      console.error('Research failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your research question..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Researching...' : 'Research'}
        </button>
      </form>
      
      {result && (
        <div>
          <h2>Answer</h2>
          <p>{result.answer}</p>
          
          <h3>Citations</h3>
          <ul>
            {result.citations.map((citation, i) => (
              <li key={i}>
                <a href={citation.url}>{citation.title}</a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## 🐛 Troubleshooting

### CORS Errors

If you see CORS errors, check:

1. **Backend CORS settings** are correct (already configured in `main.py`)
2. **API URL** is correct in frontend `.env`

### Frontend Not Loading

```bash
# Check if container is running
docker-compose ps

# Check frontend logs
docker-compose logs -f frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### API Connection Failed

```bash
# Test backend directly
curl http://localhost:8000/api/health

# Check if backend is accessible from frontend container
docker-compose exec frontend wget -O- http://langgraph-api:8000/api/health
```

### Port Already in Use

```bash
# Check what's using port 5173
sudo lsof -i :5173

# Change port in .env
echo "FRONTEND_PORT=3001" >> .env
docker-compose up -d
```

---

## 🔄 Common Commands

```bash
# Start everything
docker-compose up

# Start in background
docker-compose up -d

# Rebuild frontend
docker-compose build frontend

# Restart frontend only
docker-compose restart frontend

# View frontend logs
docker-compose logs -f frontend

# Stop everything
docker-compose down

# Fresh start (deletes data!)
docker-compose down -v && docker-compose up --build
```

---

## 📦 What Each File Does

### `Dockerfile` (Production)
- Multi-stage build
- Builds optimized frontend bundle
- Serves with Nginx
- Small image size (~50MB)

### `Dockerfile.dev` (Development)
- Runs Vite dev server
- Hot module replacement
- Fast rebuild
- Larger image (~500MB)

### `nginx.conf`
- Serves static files
- SPA routing (all routes → index.html)
- Gzip compression
- Security headers
- Asset caching

### `docker-compose.yml`
- Orchestrates all services
- Connects frontend ↔ backend
- Sets up networking
- Manages ports

---

## ✅ Verification Checklist

After setup, verify:

- [ ] `docker-compose ps` shows all 4 services running
- [ ] Frontend accessible at http://localhost:5173
- [ ] Backend accessible at http://localhost:8000
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Frontend can make API calls to backend
- [ ] No CORS errors in browser console
- [ ] Research query works end-to-end

---

## 🎓 For Your Capstone Demo

**Recommended setup:**

```bash
# Development mode (easier to demo with hot-reload)
docker-compose up -d

# Access at:
# - Frontend: http://localhost:5173
# - Backend: http://localhost:8000/docs
```

**Demo flow:**
1. Show frontend UI
2. Submit a research query
3. Show real-time timeline updates
4. Show answer with citations
5. Open backend docs to show API
6. Show database persistence (optional)

---

**Your fullstack app is ready! 🚀**