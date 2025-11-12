"""
LangGraph Research Agent Module

Implements the core research agent using LangGraph for orchestration.
The agent performs iterative web research with reflection and synthesis.

Workflow:
1. Query Generation - Generate optimized search queries
2. Web Search - Execute searches and gather results
3. Reflection - Evaluate result quality and decide on iteration
4. Synthesis - Generate final answer with citations
5. Quality Check - Validate answer quality and citations

The agent uses LangGraph's state management and node system for
reliable, traceable execution.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import time

from .services import search, synthesis
from .services.llm import get_llm, generate_search_queries
from .utils import filters
from .utils.db import (
    create_research_query,
    update_query_status,
    save_research_result,
    add_timeline_step
)
from .config import settings

logger = logging.getLogger(__name__)


# ==================== State Definition ====================

class AgentState(TypedDict):
    """
    State object passed between agent nodes.
    
    Contains all information needed for research workflow.
    """
    # Input
    query: str
    source: str
    max_iterations: int
    
    # Generated data
    search_queries: List[str]
    documents: List[Dict[str, Any]]
    answer: str
    citations: List[Dict]
    
    # Metadata
    iteration_count: int
    should_continue: bool
    timeline: List[Dict[str, Any]]
    confidence_score: float
    
    # Database
    query_id: Optional[int]
    start_time: float
    
    # Errors
    errors: List[str]


class ResearchAgent:
    """
    LangGraph-powered research agent.
    
    Orchestrates the research workflow with reflection and iteration.
    """
    
    def __init__(self):
        """Initialize research agent."""
        self.llm = get_llm()
        logger.info("Research agent initialized")
    
    async def run(
        self,
        query: str,
        source: str = 'web_ui',
        max_iterations: int = None
    ) -> Dict[str, Any]:
        """
        Execute research workflow for a query.
        
        Args:
            query: Research question
            source: Query source (web_ui, sms, api)
            max_iterations: Maximum reflection iterations
            
        Returns:
            Dictionary with answer, citations, and timeline
            
        Raises:
            ValueError: If query is invalid
            Exception: If research fails
            
        Example:
            >>> agent = ResearchAgent()
            >>> result = await agent.run("What is quantum computing?")
            >>> print(result['answer'])
            >>> print(len(result['citations']))
        """
        # Validate input
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if max_iterations is None:
            max_iterations = settings.max_reflection_iterations
        
        # Initialize state
        start_time = time.time()
        state: AgentState = {
            'query': query.strip(),
            'source': source,
            'max_iterations': max_iterations,
            'search_queries': [],
            'documents': [],
            'answer': '',
            'citations': [],
            'iteration_count': 0,
            'should_continue': True,
            'timeline': [],
            'confidence_score': 0.0,
            'query_id': None,
            'start_time': start_time,
            'errors': []
        }
        
        logger.info(f"Starting research for query: {query[:50]}...")
        
        # Create database record
        try:
            db_query = await create_research_query(
                query_text=query,
                source=source
            )
            state['query_id'] = db_query.id
            logger.info(f"Created database record with ID: {db_query.id}")
        except Exception as e:
            logger.error(f"Failed to create DB record: {str(e)}")
            # Continue without DB persistence
        
        # Execute workflow
        try:
            # Node 1: Generate search queries
            state = await self._generate_queries_node(state)
            
            # Node 2: Execute searches
            state = await self._search_node(state)
            
            # Reflection loop
            while state['should_continue'] and state['iteration_count'] < max_iterations:
                # Node 3: Reflect on results
                state = await self._reflection_node(state)
                
                # If need more results, search again
                if state['should_continue'] and state['iteration_count'] < max_iterations:
                    state = await self._search_node(state)
            
            # Node 4: Synthesize answer
            state = await self._synthesis_node(state)
            
            # Node 5: Quality check
            state = await self._quality_check_node(state)
            
            # Update database
            if state['query_id']:
                try:
                    duration_ms = int((time.time() - start_time) * 1000)
                    await update_query_status(
                        query_id=state['query_id'],
                        status='completed',
                        completed_at=datetime.utcnow(),
                        duration_ms=duration_ms,
                        iterations=state['iteration_count']
                    )
                    
                    await save_research_result(
                        query_id=state['query_id'],
                        answer=state['answer'],
                        citations=state['citations'],
                        confidence_score=state['confidence_score']
                    )
                except Exception as e:
                    logger.error(f"Failed to update DB: {str(e)}")
            
            # Build response
            return {
                'answer': state['answer'],
                'citations': state['citations'],
                'timeline': state['timeline'],
                'query': query,
                'completed_at': datetime.utcnow(),
                'total_duration_ms': int((time.time() - start_time) * 1000),
                'metadata': {
                    'iterations': state['iteration_count'],
                    'sources_found': len(state['documents']),
                    'confidence_score': state['confidence_score'],
                    'source': source
                }
            }
        
        except Exception as e:
            logger.error(f"Research workflow failed: {str(e)}", exc_info=True)
            
            # Update DB as failed
            if state.get('query_id'):
                try:
                    await update_query_status(
                        query_id=state['query_id'],
                        status='failed'
                    )
                except:
                    pass
            
            # Return error response
            return {
                'answer': f"I apologize, but I encountered an error while researching your question: {str(e)}",
                'citations': [],
                'timeline': state.get('timeline', []),
                'query': query,
                'completed_at': datetime.utcnow(),
                'total_duration_ms': int((time.time() - start_time) * 1000),
                'metadata': {
                    'error': str(e),
                    'source': source
                }
            }
    
    async def _generate_queries_node(self, state: AgentState) -> AgentState:
        """
        Node: Generate optimized search queries.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with search queries
        """
        step_start = time.time()
        logger.info("Node: Generate search queries")
        
        try:
            # Generate queries using LLM
            queries = await generate_search_queries(
                state['query'],
                num_queries=3
            )
            
            state['search_queries'] = queries
            
            # Add to timeline
            duration_ms = int((time.time() - step_start) * 1000)
            timeline_entry = {
                'step': 'query_generation',
                'description': f'Generated {len(queries)} search queries',
                'details': {'queries': queries},
                'timestamp': datetime.utcnow(),
                'duration_ms': duration_ms,
                'status': 'success'
            }
            state['timeline'].append(timeline_entry)
            
            # Save to database
            if state.get('query_id'):
                await add_timeline_step(
                    query_id=state['query_id'],
                    step_name='query_generation',
                    description=timeline_entry['description'],
                    details=timeline_entry['details'],
                    duration_ms=duration_ms
                )
            
            logger.info(f"Generated queries: {queries}")
        
        except Exception as e:
            logger.error(f"Query generation failed: {str(e)}")
            state['errors'].append(f"Query generation: {str(e)}")
            # Fallback to original query
            state['search_queries'] = [state['query']]
        
        return state
    
    async def _search_node(self, state: AgentState) -> AgentState:
        """
        Node: Execute web searches.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with search results
        """
        step_start = time.time()
        logger.info("Node: Execute web searches")
        
        try:
            # Search with all generated queries
            results = await search.search_with_queries(state['search_queries'])
            
            # Add to existing documents (for iterations)
            state['documents'].extend(results)
            
            # Deduplicate by URL
            seen_urls = set()
            unique_docs = []
            for doc in state['documents']:
                url = doc.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_docs.append(doc)
            
            state['documents'] = unique_docs
            
            # Add to timeline
            duration_ms = int((time.time() - step_start) * 1000)
            timeline_entry = {
                'step': 'web_search',
                'description': f'Found {len(results)} results from {len(state["search_queries"])} queries',
                'details': {
                    'num_queries': len(state['search_queries']),
                    'num_results': len(results),
                    'total_documents': len(state['documents'])
                },
                'timestamp': datetime.utcnow(),
                'duration_ms': duration_ms,
                'status': 'success'
            }
            state['timeline'].append(timeline_entry)
            
            # Save to database
            if state.get('query_id'):
                await add_timeline_step(
                    query_id=state['query_id'],
                    step_name='web_search',
                    description=timeline_entry['description'],
                    details=timeline_entry['details'],
                    duration_ms=duration_ms
                )
            
            logger.info(f"Found {len(state['documents'])} total documents")
        
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            state['errors'].append(f"Web search: {str(e)}")
        
        return state
    
    async def _reflection_node(self, state: AgentState) -> AgentState:
        """
        Node: Reflect on result quality and decide on iteration.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with reflection decision
        """
        step_start = time.time()
        logger.info("Node: Reflection")
        
        state['iteration_count'] += 1
        
        try:
            # Check if we have enough results
            num_docs = len(state['documents'])
            min_docs = 3
            
            if num_docs >= min_docs:
                # Sufficient results
                state['should_continue'] = False
                decision = "sufficient_results"
                reason = f"Found {num_docs} documents, proceeding to synthesis"
            else:
                # Need more results
                if state['iteration_count'] < state['max_iterations']:
                    state['should_continue'] = True
                    decision = "need_more_results"
                    reason = f"Only {num_docs} documents found, will search again"
                else:
                    state['should_continue'] = False
                    decision = "max_iterations_reached"
                    reason = f"Reached maximum iterations ({state['max_iterations']})"
            
            # Add to timeline
            duration_ms = int((time.time() - step_start) * 1000)
            timeline_entry = {
                'step': 'reflection',
                'description': reason,
                'details': {
                    'decision': decision,
                    'num_documents': num_docs,
                    'iteration': state['iteration_count'],
                    'continue': state['should_continue']
                },
                'timestamp': datetime.utcnow(),
                'duration_ms': duration_ms,
                'status': 'success'
            }
            state['timeline'].append(timeline_entry)
            
            # Save to database
            if state.get('query_id'):
                await add_timeline_step(
                    query_id=state['query_id'],
                    step_name='reflection',
                    description=timeline_entry['description'],
                    details=timeline_entry['details'],
                    duration_ms=duration_ms
                )
            
            logger.info(f"Reflection: {decision} - {reason}")
        
        except Exception as e:
            logger.error(f"Reflection failed: {str(e)}")
            state['errors'].append(f"Reflection: {str(e)}")
            state['should_continue'] = False
        
        return state
    
    async def _synthesis_node(self, state: AgentState) -> AgentState:
        """
        Node: Synthesize answer from documents.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with answer and citations
        """
        step_start = time.time()
        logger.info("Node: Synthesize answer")
        
        try:
            # Synthesize answer
            answer, citations = await synthesis.synthesize_answer(
                query=state['query'],
                docs=state['documents']
            )
            
            state['answer'] = answer
            state['citations'] = citations
            
            # Add to timeline
            duration_ms = int((time.time() - step_start) * 1000)
            timeline_entry = {
                'step': 'synthesis',
                'description': f'Synthesized answer with {len(citations)} citations',
                'details': {
                    'answer_length': len(answer),
                    'num_citations': len(citations)
                },
                'timestamp': datetime.utcnow(),
                'duration_ms': duration_ms,
                'status': 'success'
            }
            state['timeline'].append(timeline_entry)
            
            # Save to database
            if state.get('query_id'):
                await add_timeline_step(
                    query_id=state['query_id'],
                    step_name='synthesis',
                    description=timeline_entry['description'],
                    details=timeline_entry['details'],
                    duration_ms=duration_ms
                )
            
            logger.info(f"Synthesized answer: {len(answer)} chars, {len(citations)} citations")
        
        except Exception as e:
            logger.error(f"Synthesis failed: {str(e)}")
            state['errors'].append(f"Synthesis: {str(e)}")
            state['answer'] = "I apologize, but I encountered an error while synthesizing the answer."
            state['citations'] = []
        
        return state
    
    async def _quality_check_node(self, state: AgentState) -> AgentState:
        """
        Node: Check answer quality and confidence.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with quality metrics
        """
        step_start = time.time()
        logger.info("Node: Quality check")
        
        try:
            # Check for hallucinations
            if settings.enable_hallucination_check:
                is_hallucinated, confidence = await filters.check_hallucination(
                    state['answer'],
                    state['documents']
                )
                state['confidence_score'] = confidence
                
                if is_hallucinated:
                    logger.warning(f"Hallucination detected (confidence: {confidence:.2f})")
            else:
                state['confidence_score'] = 0.8  # Default
            
            # Add to timeline
            duration_ms = int((time.time() - step_start) * 1000)
            timeline_entry = {
                'step': 'quality_check',
                'description': f'Quality check complete (confidence: {state["confidence_score"]:.2f})',
                'details': {
                    'confidence_score': state['confidence_score'],
                    'hallucination_check': settings.enable_hallucination_check
                },
                'timestamp': datetime.utcnow(),
                'duration_ms': duration_ms,
                'status': 'success'
            }
            state['timeline'].append(timeline_entry)
            
            # Save to database
            if state.get('query_id'):
                await add_timeline_step(
                    query_id=state['query_id'],
                    step_name='quality_check',
                    description=timeline_entry['description'],
                    details=timeline_entry['details'],
                    duration_ms=duration_ms
                )
            
            logger.info(f"Quality check complete: confidence={state['confidence_score']:.2f}")
        
        except Exception as e:
            logger.error(f"Quality check failed: {str(e)}")
            state['errors'].append(f"Quality check: {str(e)}")
            state['confidence_score'] = 0.5  # Low confidence on error
        
        return state
