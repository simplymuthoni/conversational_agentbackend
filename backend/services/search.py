"""
Web Search Service Module

Provides web search capabilities with support for multiple providers:
- Mock search (for testing)
- SerpAPI (Google, Bing, etc.)
- Brave Search API
- Google Custom Search API

Implements result parsing, ranking, and filtering.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import httpx

from ..config import settings
from ..utils.cache import cache_result
from ..utils.filters import contains_pii_in_document

logger = logging.getLogger(__name__)


class SearchProvider(ABC):
    """Abstract base class for search providers."""
    
    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform web search.
        
        Args:
            query: Search query
            num_results: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        pass


class MockSearchProvider(SearchProvider):
    """
    Mock search provider for testing and development.
    
    Returns synthetic search results without external API calls.
    """
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Generate mock search results.
        
        Args:
            query: Search query
            num_results: Number of results to generate
            
        Returns:
            List of mock search results
        """
        logger.info(f"Mock search for query: {query}")
        await asyncio.sleep(0.1)  # Simulate API latency
        
        # Generate mock results
        results = []
        for i in range(min(num_results, 5)):
            results.append({
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/article-{i+1}",
                "snippet": f"This is a mock search result snippet about {query}. "
                          f"It contains relevant information that would typically "
                          f"come from a real search engine.",
                "source": "Mock Search Engine",
                "position": i + 1
            })
        
        return results


class SerpAPIProvider(SearchProvider):
    """
    SerpAPI search provider.
    
    Uses SerpAPI for Google, Bing, and other search engines.
    Website: https://serpapi.com
    """
    
    def __init__(self, api_key: str):
        """
        Initialize SerpAPI provider.
        
        Args:
            api_key: SerpAPI key
        """
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using SerpAPI.
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            List of search results
        """
        logger.info(f"SerpAPI search for query: {query}")
        
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "engine": "google"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # Parse results
            results = []
            for i, item in enumerate(data.get("organic_results", [])[:num_results]):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google (via SerpAPI)",
                    "position": i + 1
                })
            
            logger.info(f"SerpAPI returned {len(results)} results")
            return results
        
        except httpx.HTTPError as e:
            logger.error(f"SerpAPI HTTP error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"SerpAPI error: {str(e)}")
            return []


class BraveSearchProvider(SearchProvider):
    """
    Brave Search API provider.
    
    Uses Brave's independent search index.
    Website: https://brave.com/search/api/
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Brave Search provider.
        
        Args:
            api_key: Brave Search API key
        """
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using Brave Search API.
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            List of search results
        """
        logger.info(f"Brave Search for query: {query}")
        
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": num_results
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse results
            results = []
            for i, item in enumerate(data.get("web", {}).get("results", [])[:num_results]):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", ""),
                    "source": "Brave Search",
                    "position": i + 1
                })
            
            logger.info(f"Brave Search returned {len(results)} results")
            return results
        
        except httpx.HTTPError as e:
            logger.error(f"Brave Search HTTP error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Brave Search error: {str(e)}")
            return []


class SearchService:
    """
    Main search service with provider abstraction.
    
    Handles provider selection, result ranking, and filtering.
    """
    
    def __init__(self):
        """Initialize search service with configured provider."""
        self.provider = self._initialize_provider()
    
    def _initialize_provider(self) -> SearchProvider:
        """
        Initialize search provider based on configuration.
        
        Returns:
            Configured SearchProvider instance
        """
        provider_name = settings.search_provider.lower()
        
        if provider_name == "serpapi":
            if settings.search_api_key:
                logger.info("Using SerpAPI search provider")
                return SerpAPIProvider(settings.search_api_key)
            else:
                logger.warning("SerpAPI key not found, falling back to mock")
                return MockSearchProvider()
        
        elif provider_name == "brave":
            if settings.search_api_key:
                logger.info("Using Brave Search provider")
                return BraveSearchProvider(settings.search_api_key)
            else:
                logger.warning("Brave API key not found, falling back to mock")
                return MockSearchProvider()
        
        else:
            logger.info("Using mock search provider")
            return MockSearchProvider()
    
    @cache_result(ttl=3600, key_prefix="search")
    async def search(
        self,
        query: str,
        num_results: int = None,
        filter_pii: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform web search with filtering and ranking.
        
        Args:
            query: Search query
            num_results: Maximum results (defaults to settings)
            filter_pii: Whether to filter results containing PII
            
        Returns:
            List of filtered and ranked search results
            
        Example:
            >>> results = await search_service.search("quantum computing")
            >>> for result in results:
            ...     print(result['title'], result['url'])
        """
        if num_results is None:
            num_results = settings.max_search_results
        
        # Perform search
        results = await self.provider.search(query, num_results)
        
        if not results:
            logger.warning(f"No results found for query: {query}")
            return []
        
        # Filter PII if enabled
        if filter_pii and settings.enable_pii_filter:
            results = await self._filter_pii_results(results)
        
        # Rank results
        results = self._rank_results(results, query)
        
        logger.info(f"Returning {len(results)} filtered and ranked results")
        return results
    
    async def _filter_pii_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out results containing PII.
        
        Args:
            results: List of search results
            
        Returns:
            Filtered list without PII
        """
        filtered = []
        for result in results:
            has_pii = await contains_pii_in_document(result)
            if not has_pii:
                filtered.append(result)
            else:
                logger.info(f"Filtered result with PII: {result.get('title', '')[:50]}")
        
        return filtered
    
    def _rank_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Rank search results by relevance.
        
        Simple ranking based on:
        - Query term frequency in title/snippet
        - Position in original results
        
        Args:
            results: List of search results
            query: Original query
            
        Returns:
            Ranked list of results
        """
        query_terms = query.lower().split()
        
        for result in results:
            # Calculate relevance score
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            
            # Count query term matches
            title_matches = sum(1 for term in query_terms if term in title)
            snippet_matches = sum(1 for term in query_terms if term in snippet)
            
            # Calculate score (weighted)
            score = (title_matches * 2.0) + snippet_matches
            
            # Penalize lower positions
            position_penalty = result.get("position", 10) * 0.1
            score -= position_penalty
            
            result["relevance_score"] = max(0.0, score)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return results
    
    async def search_multiple(
        self,
        queries: List[str],
        num_results_per_query: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform multiple searches concurrently.
        
        Args:
            queries: List of search queries
            num_results_per_query: Results per query
            
        Returns:
            Combined and deduplicated results
            
        Example:
            >>> queries = ["quantum computing", "quantum algorithms"]
            >>> results = await search_service.search_multiple(queries)
        """
        # Execute searches concurrently
        tasks = [
            self.search(query, num_results=num_results_per_query)
            for query in queries
        ]
        
        results_lists = await asyncio.gather(*tasks)
        
        # Combine and deduplicate
        seen_urls = set()
        combined_results = []
        
        for results in results_lists:
            for result in results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    combined_results.append(result)
        
        logger.info(f"Combined {len(combined_results)} unique results from {len(queries)} queries")
        return combined_results


# Global search service instance
search_service = SearchService()


# ==================== Convenience Functions ====================

async def run_search(query: str, num_results: int = None) -> List[Dict[str, Any]]:
    """
    Convenience function to perform a search.
    
    Args:
        query: Search query
        num_results: Maximum results
        
    Returns:
        List of search results
        
    Example:
        >>> results = await run_search("artificial intelligence")
        >>> print(len(results))
        10
    """
    return await search_service.search(query, num_results)


async def search_with_queries(queries: List[str]) -> List[Dict[str, Any]]:
    """
    Search with multiple queries.
    
    Args:
        queries: List of search queries
        
    Returns:
        Combined search results
    """
    return await search_service.search_multiple(queries)
