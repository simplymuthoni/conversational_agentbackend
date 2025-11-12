"""
Answer Synthesis Service Module

Synthesizes research answers from search results using LLM.
Handles citation formatting, answer quality checks, and fact verification.

Key responsibilities:
- Generate coherent answers from multiple sources
- Create proper citations with source attribution
- Verify factual consistency
- Check for hallucinations
- Format answers for different outputs (web, SMS)
"""

import logging
import re
from typing import List, Dict, Tuple, Optional, Any
import json

from .llm import get_llm, GeminiLLM
from ..utils.filters import (
    check_hallucination,
    check_bias,
    sanitize_output
)
from ..config import settings

logger = logging.getLogger(__name__)


class AnswerSynthesizer:
    """
    Synthesizes research answers from search results.
    
    Uses LLM to generate coherent, well-cited answers from
    multiple source documents.
    """
    
    def __init__(self):
        """Initialize answer synthesizer."""
        self.llm = get_llm()
    
    async def synthesize(
        self,
        query: str,
        docs: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> Tuple[str, List[Dict], float]:
        """
        Synthesize answer from search results.
        
        Args:
            query: Original research query
            docs: List of search result documents
            context: Optional additional context
            
        Returns:
            Tuple of (answer: str, citations: List[Dict], confidence: float)
            
        Example:
            >>> docs = [{"title": "...", "snippet": "..."}]
            >>> answer, citations, confidence = await synthesizer.synthesize(
            ...     "What is quantum computing?", docs
            ... )
        """
        if not docs:
            logger.warning("No documents provided for synthesis")
            return self._generate_no_results_answer(query), [], 0.0
        
        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(query, docs, context)
        
        # Generate answer
        try:
            answer = await self.llm.generate(prompt)
            logger.info(f"Generated answer ({len(answer)} chars)")
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            return self._generate_error_answer(), [], 0.0
        
        # Extract and format citations
        citations = self._extract_citations(docs)
        
        # Check answer quality
        confidence = await self._assess_answer_quality(answer, docs)
        
        # Sanitize output
        if settings.enable_pii_filter:
            answer = await sanitize_output(answer)
        
        return answer, citations, confidence
    
    def _build_synthesis_prompt(
        self,
        query: str,
        docs: List[Dict],
        context: Optional[str] = None
    ) -> str:
        """
        Build LLM prompt for answer synthesis.
        
        Args:
            query: Research query
            docs: Source documents
            context: Optional context
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a research assistant synthesizing information from multiple sources.

Research Query: {query}

Your task: Synthesize a comprehensive, accurate answer based on the provided sources. Follow these guidelines:

1. **Accuracy**: Only include information supported by the sources
2. **Comprehensiveness**: Cover all relevant aspects from the sources
3. **Clarity**: Write in clear, accessible language
4. **Citations**: Reference sources naturally in your answer (e.g., "According to [Source 1]...")
5. **Balance**: Present multiple perspectives when sources disagree
6. **Conciseness**: Be thorough but avoid unnecessary repetition

Source Documents:
"""
        
        # Add documents with citations
        for i, doc in enumerate(docs[:10], 1):  # Limit to top 10 sources
            title = doc.get('title', 'Unknown')
            url = doc.get('url', '')
            snippet = doc.get('snippet', '')
            source = doc.get('source', 'Web')
            
            prompt += f"\n[Source {i}] {title}\n"
            prompt += f"URL: {url}\n"
            prompt += f"Content: {snippet}\n"
            prompt += f"Provider: {source}\n"
        
        if context:
            prompt += f"\nAdditional Context: {context}\n"
        
        prompt += """
Answer Requirements:
- Length: 200-400 words (adjust based on query complexity)
- Format: Well-structured paragraphs
- Tone: Informative and professional
- Citations: Mention sources naturally (e.g., "Research from [Source 1] shows...")
- Uncertainty: If sources conflict or lack information, acknowledge this

Generate your answer now:"""
        
        return prompt
    
    def _extract_citations(self, docs: List[Dict]) -> List[Dict]:
        """
        Extract and format citations from documents.
        
        Args:
            docs: Source documents
            
        Returns:
            List of formatted citation dictionaries
        """
        citations = []
        
        for doc in docs:
            citation = {
                'title': doc.get('title', 'Unknown Source'),
                'url': doc.get('url', ''),
                'snippet': doc.get('snippet', '')[:200],  # Truncate long snippets
                'source': doc.get('source', 'Web'),
                'relevance_score': doc.get('relevance_score')
            }
            citations.append(citation)
        
        return citations
    
    async def _assess_answer_quality(
        self,
        answer: str,
        docs: List[Dict]
    ) -> float:
        """
        Assess the quality and reliability of the generated answer.
        
        Checks for:
        - Hallucinations
        - Citation coverage
        - Bias
        - Factual consistency
        
        Args:
            answer: Generated answer
            docs: Source documents
            
        Returns:
            Confidence score (0.0-1.0)
        """
        scores = []
        
        # Check for hallucinations
        if settings.enable_hallucination_check:
            is_hallucinated, hall_confidence = await check_hallucination(answer, docs)
            scores.append(hall_confidence)
            
            if is_hallucinated:
                logger.warning("Potential hallucination detected in answer")
        
        # Check citation coverage
        if docs:
            # Simple heuristic: answer should be longer than average snippet
            avg_snippet_length = sum(len(d.get('snippet', '')) for d in docs) / len(docs)
            answer_length = len(answer)
            
            if answer_length < avg_snippet_length * 0.5:
                logger.warning("Answer may be too short given source material")
                scores.append(0.6)
            elif answer_length > avg_snippet_length * 5:
                logger.warning("Answer may contain unsupported elaboration")
                scores.append(0.7)
            else:
                scores.append(0.9)
        
        # Check for bias
        if settings.enable_bias_detection:
            bias_result = await check_bias(answer)
            if bias_result['has_bias']:
                logger.info(f"Potential bias detected: {bias_result['bias_types']}")
                scores.append(max(0.5, 1.0 - bias_result['confidence']))
            else:
                scores.append(0.95)
        
        # Calculate overall confidence
        if scores:
            confidence = sum(scores) / len(scores)
        else:
            confidence = 0.8  # Default confidence
        
        logger.info(f"Answer quality confidence: {confidence:.2f}")
        return confidence
    
    def _generate_no_results_answer(self, query: str) -> str:
        """
        Generate answer when no search results are available.
        
        Args:
            query: Original query
            
        Returns:
            Fallback answer string
        """
        return f"""I apologize, but I couldn't find sufficient information to answer your question about "{query}". 

This could be because:
- The topic is very recent or emerging
- The search terms may need refinement
- Information on this topic may be limited

Suggestions:
- Try rephrasing your question with different keywords
- Break down complex questions into simpler parts
- Check if you've spelled technical terms correctly

Please try again with a modified query, and I'll do my best to help!"""
    
    def _generate_error_answer(self) -> str:
        """
        Generate answer when synthesis fails.
        
        Returns:
            Error message string
        """
        return """I encountered an error while synthesizing the answer. Please try again, or rephrase your question. If the problem persists, contact support."""


async def synthesize_answer(
    query: str,
    docs: List[Dict],
    context: Optional[str] = None
) -> Tuple[str, List[Dict]]:
    """
    Convenience function to synthesize answer.
    
    Args:
        query: Research query
        docs: Source documents
        context: Optional context
        
    Returns:
        Tuple of (answer: str, citations: List[Dict])
        
    Example:
        >>> answer, citations = await synthesize_answer(
        ...     "What is AI?",
        ...     [{"title": "AI Basics", "snippet": "..."}]
        ... )
    """
    synthesizer = AnswerSynthesizer()
    answer, citations, confidence = await synthesizer.synthesize(query, docs, context)
    
    # Log confidence for monitoring
    logger.info(f"Answer synthesized with confidence: {confidence:.2f}")
    
    return answer, citations


async def synthesize_with_reflection(
    query: str,
    docs: List[Dict],
    previous_answer: Optional[str] = None,
    reflection_feedback: Optional[str] = None
) -> Tuple[str, List[Dict]]:
    """
    Synthesize answer with reflection on previous attempt.
    
    Used in iterative refinement loops.
    
    Args:
        query: Research query
        docs: Source documents
        previous_answer: Previous answer attempt
        reflection_feedback: Feedback from reflection step
        
    Returns:
        Tuple of (improved_answer: str, citations: List[Dict])
    """
    synthesizer = AnswerSynthesizer()
    
    # Build context with reflection
    context = None
    if previous_answer and reflection_feedback:
        context = f"""
Previous Answer: {previous_answer}

Reflection Feedback: {reflection_feedback}

Please improve the answer based on this feedback.
"""
    
    answer, citations, confidence = await synthesizer.synthesize(
        query, docs, context
    )
    
    return answer, citations


async def format_sms_answer(
    answer: str,
    citations: List[Dict],
    max_length: int = 1600
) -> str:
    """
    Format answer for SMS delivery.
    
    Args:
        answer: Full answer text
        citations: List of citations
        max_length: Maximum SMS length
        
    Returns:
        SMS-formatted answer string
        
    Example:
        >>> sms_answer = await format_sms_answer(answer, citations, 1600)
        >>> print(len(sms_answer))
        1580
    """
    # Start with answer
    formatted = answer
    
    # Add top 2 citations
    if citations:
        formatted += "\n\n📚 Sources:"
        for i, citation in enumerate(citations[:2], 1):
            url = citation.get('url', '')
            # Shorten URL for SMS
            short_url = url.replace('https://', '').replace('http://', '')
            if len(short_url) > 40:
                short_url = short_url[:37] + '...'
            
            formatted += f"\n{i}. {short_url}"
    
    # Truncate if needed
    if len(formatted) > max_length:
        truncate_at = max_length - 50
        formatted = formatted[:truncate_at] + "...\n\nFor full answer, visit our web app."
    
    return formatted


async def create_citation_summary(citations: List[Dict]) -> str:
    """
    Create a summary of citations for display.
    
    Args:
        citations: List of citation dictionaries
        
    Returns:
        Formatted citation summary string
    """
    if not citations:
        return "No sources cited."
    
    summary = f"**Sources ({len(citations)} total):**\n\n"
    
    for i, citation in enumerate(citations, 1):
        title = citation.get('title', 'Unknown')
        url = citation.get('url', '')
        source = citation.get('source', 'Web')
        
        summary += f"{i}. **{title}**\n"
        summary += f"   - URL: {url}\n"
        summary += f"   - Source: {source}\n\n"
    
    return summary
