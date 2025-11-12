import asyncio
from typing import List, Dict


async def run_search(query: str) -> List[Dict]:
"""Replace this with a real web search adapter (Google Custom Search, SerpAPI, etc.)
Return a list of documents: {"title":..., "url":..., "snippet":..., "source":...}
"""
# Mock results for testing
await asyncio.sleep(0.1)
return [
{"title": f"Result for {query}", "url": "https://example.com", "snippet": "Example snippet", "source": "example"}
]