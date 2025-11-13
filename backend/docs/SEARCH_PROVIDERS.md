# Search Providers Configuration Guide

This document explains the different search provider options available in the Research Agent and how to configure them.

## Overview

The Research Agent supports multiple search providers to fetch web information. Each provider has different costs, features, and API key requirements.

## Search Provider Options

### 1. **Mock Search** (Development/Testing)
- **Provider Code**: `mock`
- **API Keys Required**: None
- **Cost**: Free
- **Use Case**: Development, testing, demos without API costs

**Configuration:**
```env
SEARCH_PROVIDER=mock
# No API key needed
```

**Features:**
- ✅ No API costs
- ✅ No rate limits
- ✅ Instant responses
- ❌ Returns synthetic data only
- ❌ Not suitable for production

---

### 2. **Gemini with Google Search** (Recommended for MVP)
- **Provider Code**: `gemini`
- **API Keys Required**: `GEMINI_API_KEY` only
- **Cost**: Included with Gemini API usage
- **Use Case**: Quick start with minimal API keys

**Configuration:**
```env
SEARCH_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
# No separate search API key needed!
```

**Features:**
- ✅ Only needs one API key (Gemini)
- ✅ Uses Google Search grounding
- ✅ Integrated with LLM for better synthesis
- ✅ Good for MVP/prototyping
- ⚠️ Currently in preview (may have limits)
- ⚠️ Results are filtered through Gemini

**How it works:**
```python
# Gemini uses its grounding feature to search Google
# and returns results along with generated content
response = model.generate_content(
    query,
    tools=[Tool(google_search_retrieval=GoogleSearchRetrieval())]
)
```

**Pros:**
- Simplest setup (one API key)
- No additional costs beyond Gemini usage
- Results are pre-processed by Gemini

**Cons:**
- Fewer raw search results
- Less control over search parameters
- Preview feature (subject to changes)

---

### 3. **SerpAPI** (Recommended for Production)
- **Provider Code**: `serpapi`
- **API Keys Required**: `SEARCH_API_KEY` (SerpAPI key)
- **Cost**: ~$50/month for 5,000 searches
- **Use Case**: Production with Google/Bing results

**Configuration:**
```env
SEARCH_PROVIDER=serpapi
SEARCH_API_KEY=your_serpapi_key_here
GEMINI_API_KEY=your_gemini_key_here
```

**Features:**
- ✅ Access to Google, Bing, Yahoo, and more
- ✅ Structured JSON responses
- ✅ Good documentation and support
- ✅ Reliable and fast
- ✅ No Google Cloud project needed
- 💰 Paid service

**Sign up:** https://serpapi.com/

**Pricing:**
- Free tier: 100 searches/month
- Basic: $50/month (5,000 searches)
- Professional: $250/month (30,000 searches)

---

### 4. **Brave Search API**
- **Provider Code**: `brave`
- **API Keys Required**: `SEARCH_API_KEY` (Brave API key)
- **Cost**: Free tier available, then paid
- **Use Case**: Independent search index, privacy-focused

**Configuration:**
```env
SEARCH_PROVIDER=brave
SEARCH_API_KEY=your_brave_api_key_here
GEMINI_API_KEY=your_gemini_key_here
```

**Features:**
- ✅ Independent search index (not Google)
- ✅ Privacy-focused
- ✅ Good free tier
- ✅ Fast responses
- ⚠️ Smaller index than Google
- 💰 Limited free tier

**Sign up:** https://brave.com/search/api/

**Pricing:**
- Free tier: 2,000 queries/month
- Data for AI: $5/month (15,000 queries)
- Pro: Contact for pricing

---

### 5. **Google Custom Search API**
- **Provider Code**: `google`
- **API Keys Required**: `SEARCH_API_KEY` + `SEARCH_ENGINE_ID`
- **Cost**: Free tier (100 queries/day), then $5 per 1,000 queries
- **Use Case**: Direct Google integration

**Configuration:**
```env
SEARCH_PROVIDER=google
SEARCH_API_KEY=your_google_api_key_here
SEARCH_ENGINE_ID=your_custom_search_engine_id_here
GEMINI_API_KEY=your_gemini_key_here
```

**Features:**
- ✅ Official Google API
- ✅ Customizable search
- ✅ Free tier available
- ⚠️ Requires Google Cloud project
- ⚠️ More setup required
- 💰 Costs after free tier

**Setup Steps:**
1. Create Google Cloud project
2. Enable Custom Search API
3. Create Custom Search Engine at https://programmablesearchengine.google.com/
4. Get API key and Engine ID

**Pricing:**
- Free: 100 queries/day
- Paid: $5 per 1,000 queries (up to 10k/day)

---

## Comparison Matrix

| Provider | API Keys Needed | Cost (1000 searches) | Setup Complexity | Production Ready |
|----------|----------------|---------------------|------------------|------------------|
| Mock | None | Free | Easy ⭐ | ❌ Testing only |
| Gemini | 1 (Gemini) | ~$0.50 | Easy ⭐ | ⚠️ Preview |
| SerpAPI | 1 (SerpAPI) | ~$10 | Easy ⭐ | ✅ Yes |
| Brave | 1 (Brave) | ~$0.33 | Easy ⭐ | ✅ Yes |
| Google | 2 (API + Engine) | $5 | Medium ⭐⭐ | ✅ Yes |

## Recommendations

### For Development/Testing:
```env
SEARCH_PROVIDER=mock
```
No API keys needed, instant results.

### For MVP/Prototyping:
```env
SEARCH_PROVIDER=gemini
GEMINI_API_KEY=your_key
```
Only one API key needed, good enough for initial testing.

### For Production (Budget-Friendly):
```env
SEARCH_PROVIDER=brave
SEARCH_API_KEY=your_brave_key
GEMINI_API_KEY=your_gemini_key
```
Good balance of cost and quality.

### For Production (Best Quality):
```env
SEARCH_PROVIDER=serpapi
SEARCH_API_KEY=your_serpapi_key
GEMINI_API_KEY=your_gemini_key
```
Most reliable and comprehensive results.

## Environment Variables Summary

```env
# Required (always)
GEMINI_API_KEY=your_gemini_api_key

# Search Configuration
SEARCH_PROVIDER=mock  # Options: mock, gemini, serpapi, brave, google

# Optional - only if using external search APIs
SEARCH_API_KEY=your_search_api_key  # For serpapi, brave, or google
SEARCH_ENGINE_ID=your_engine_id     # Only for google provider
```

## Testing Search Providers

You can test each provider by running:

```python
from backend.services.search import search_service

# Test search
results = await search_service.search("quantum computing")
print(f"Found {len(results)} results")
for result in results:
    print(f"- {result['title']}: {result['url']}")
```

## Cost Estimation

For a capstone project with **~100 queries** during development and demo:

| Provider | Estimated Cost |
|----------|---------------|
| Mock | $0 |
| Gemini | ~$0.05 (included in Gemini usage) |
| SerpAPI | $0 (free tier covers 100) |
| Brave | $0 (free tier covers 2,000) |
| Google | $0 (free tier covers 100/day) |

**For production with 10,000 queries/month:**

| Provider | Monthly Cost |
|----------|--------------|
| Gemini | ~$5 |
| SerpAPI | ~$100 |
| Brave | ~$3.30 |
| Google | ~$50 |

## Switching Providers

You can easily switch providers by changing one environment variable:

```bash
# Start with mock for development
SEARCH_PROVIDER=mock

# Switch to Gemini for MVP
SEARCH_PROVIDER=gemini

# Upgrade to SerpAPI for production
SEARCH_PROVIDER=serpapi
SEARCH_API_KEY=your_serpapi_key
```

No code changes needed!

## Troubleshooting

### "Using mock search provider" warning
- Check that `SEARCH_PROVIDER` is set correctly
- Verify API keys are present in `.env`
- Check logs for specific error messages

### "No results found"
- Verify API key is valid and has quota
- Check network connectivity
- Review provider's status page
- Check logs for API errors

### Rate limit errors
- Implement caching (already built-in)
- Reduce `max_search_results` in settings
- Upgrade to higher tier plan
- Add delays between requests

---

**Questions?** Check provider documentation:
- Gemini: https://ai.google.dev/docs/grounding
- SerpAPI: https://serpapi.com/docs
- Brave: https://brave.com/search/api/docs
- Google: https://developers.google.com/custom-search
