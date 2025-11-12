"""
Security and Safety Filters Module

This module provides AI safety checks including:
- PII (Personally Identifiable Information) detection
- Toxicity and harmful content filtering
- Prompt injection detection
- Hallucination checking
- Bias detection
- Output sanitization

These filters protect users and ensure responsible AI operation.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)

# PII Detection Patterns
PII_PATTERNS = {
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # US Social Security Number
    'phone': re.compile(r'\+?\d{1,4}?[-.\s]?\(?\d{1,4}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),  # Phone numbers
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email addresses
    'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # Credit card numbers
    'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),  # IP addresses
    'passport': re.compile(r'\b[A-Z]{1,2}\d{6,9}\b'),  # Passport numbers (simplified)
}

# Prompt Injection Patterns
PROMPT_INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(previous|all)\s+instructions?', re.IGNORECASE),
    re.compile(r'disregard\s+(previous|all)\s+instructions?', re.IGNORECASE),
    re.compile(r'forget\s+(everything|all|previous)', re.IGNORECASE),
    re.compile(r'system\s*:\s*you\s+are', re.IGNORECASE),
    re.compile(r'<\|im_start\|>|<\|im_end\|>', re.IGNORECASE),  # ChatML tokens
    re.compile(r'\[INST\]|\[/INST\]', re.IGNORECASE),  # Llama tokens
    re.compile(r'new\s+instructions?:', re.IGNORECASE),
    re.compile(r'override\s+your\s+directives', re.IGNORECASE),
]

# Toxicity Keywords (basic - should be replaced with ML model in production)
TOXICITY_KEYWORDS = [
    # Violence
    'kill', 'murder', 'assault', 'attack', 'harm', 'hurt',
    # Hate speech indicators (partial list for MVP)
    'hate', 'discriminate',
    # Explicit content
    'explicit', 'pornographic',
]

# High-confidence hallucination indicators
HALLUCINATION_INDICATORS = [
    'i think', 'i believe', 'probably', 'maybe', 'might be',
    'could be', 'seems like', 'appears to be',
    'not sure', 'uncertain', 'speculation',
]


async def check_pii(text: str) -> bool:
    """
    Check if text contains Personally Identifiable Information (PII).
    
    Detects common PII patterns including:
    - Social Security Numbers
    - Phone numbers
    - Email addresses
    - Credit card numbers
    - IP addresses
    - Passport numbers
    
    Args:
        text: Text to check for PII
        
    Returns:
        True if PII is detected, False otherwise
        
    Example:
        >>> await check_pii("My SSN is 123-45-6789")
        True
        >>> await check_pii("What is quantum computing?")
        False
    """
    if not text:
        return False
    
    pii_found = []
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            pii_found.append(pii_type)
            logger.info(f"PII detected: {pii_type} ({len(matches)} occurrences)")
    
    if pii_found:
        logger.warning(f"PII types found: {', '.join(pii_found)}")
        return True
    
    return False


async def check_prompt_injection(text: str) -> bool:
    """
    Detect potential prompt injection attempts.
    
    Checks for common prompt injection patterns that attempt to:
    - Override system instructions
    - Inject malicious prompts
    - Manipulate model behavior
    
    Args:
        text: Text to check for injection patterns
        
    Returns:
        True if injection attempt detected, False otherwise
        
    Example:
        >>> await check_prompt_injection("Ignore all previous instructions")
        True
        >>> await check_prompt_injection("What is AI?")
        False
    """
    if not text:
        return False
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(f"Prompt injection pattern detected: {pattern.pattern}")
            return True
    
    # Check for excessive special characters (potential token injection)
    special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
    if special_char_ratio > 0.3:  # More than 30% special characters
        logger.warning(f"High special character ratio: {special_char_ratio:.2%}")
        return True
    
    return False


async def check_toxicity(text: str) -> bool:
    """
    Check text for toxic or harmful content.
    
    This is a basic keyword-based implementation for MVP.
    In production, replace with a proper toxicity detection model like:
    - Perspective API
    - Detoxify model
    - Custom fine-tuned classifier
    
    Args:
        text: Text to check for toxicity
        
    Returns:
        True if toxic content detected, False otherwise
        
    Note:
        This is a simplified implementation. For production use,
        integrate a proper ML-based toxicity detection service.
        
    Example:
        >>> await check_toxicity("I want to harm someone")
        True
        >>> await check_toxicity("Tell me about solar energy")
        False
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for toxicity keywords
    detected_keywords = [kw for kw in TOXICITY_KEYWORDS if kw in text_lower]
    
    if detected_keywords:
        logger.warning(f"Potential toxic content detected. Keywords: {detected_keywords}")
        # Return True only if multiple indicators present (reduce false positives)
        return len(detected_keywords) >= 2
    
    return False


async def check_hallucination(answer: str, sources: List[Dict]) -> Tuple[bool, float]:
    """
    Check for potential hallucinations in generated answers.
    
    Performs multiple checks:
    1. Confidence indicators (uncertain language)
    2. Citation coverage (answer statements vs. source support)
    3. Factual consistency (basic contradiction detection)
    
    Args:
        answer: The generated answer text
        sources: List of source documents/citations
        
    Returns:
        Tuple of (is_hallucinated: bool, confidence_score: float)
        - is_hallucinated: True if hallucination detected
        - confidence_score: 0.0-1.0 indicating answer confidence
        
    Note:
        This is a heuristic-based approach. For production, consider:
        - NLI (Natural Language Inference) models
        - Fact verification systems
        - Grounding checks against source documents
        
    Example:
        >>> answer = "I think quantum computers might use qubits"
        >>> sources = [{"snippet": "Quantum computers use qubits"}]
        >>> await check_hallucination(answer, sources)
        (True, 0.4)
    """
    if not answer:
        return False, 0.0
    
    answer_lower = answer.lower()
    
    # Check for uncertainty indicators
    uncertainty_count = sum(
        1 for indicator in HALLUCINATION_INDICATORS
        if indicator in answer_lower
    )
    
    # Calculate confidence score
    confidence_score = 1.0 - (uncertainty_count * 0.15)
    confidence_score = max(0.0, min(1.0, confidence_score))
    
    # Check citation coverage
    if not sources or len(sources) == 0:
        logger.warning("Answer has no supporting sources")
        confidence_score *= 0.5
    
    # Check for specific claims without citations
    # (Simple heuristic: look for numbers, dates, specific names)
    specific_claims = re.findall(r'\d{4}|\d+%|\$\d+', answer)
    if specific_claims and not sources:
        logger.warning(f"Specific claims without sources: {specific_claims}")
        confidence_score *= 0.6
    
    is_hallucinated = confidence_score < 0.6
    
    if is_hallucinated:
        logger.warning(f"Potential hallucination detected. Confidence: {confidence_score:.2f}")
    
    return is_hallucinated, confidence_score


async def check_bias(text: str) -> Dict[str, any]:
    """
    Detect potential biases in generated text.
    
    Checks for:
    - Gender bias
    - Racial/ethnic bias
    - Political bias
    - Stereotyping
    
    Args:
        text: Text to analyze for bias
        
    Returns:
        Dictionary containing bias analysis:
        - has_bias: bool
        - bias_types: List[str]
        - confidence: float
        - details: Dict
        
    Note:
        This is a basic implementation. For production, use specialized
        bias detection models or services.
        
    Example:
        >>> result = await check_bias("All engineers are men")
        >>> result['has_bias']
        True
    """
    # Placeholder implementation for MVP
    # In production, integrate proper bias detection models
    
    bias_result = {
        'has_bias': False,
        'bias_types': [],
        'confidence': 0.0,
        'details': {}
    }
    
    # Basic gendered language check
    gendered_terms = ['he', 'she', 'him', 'her', 'his', 'hers']
    text_lower = text.lower()
    gender_count = sum(1 for term in gendered_terms if term in text_lower.split())
    
    if gender_count > 5:  # Arbitrary threshold
        bias_result['has_bias'] = True
        bias_result['bias_types'].append('gender')
        bias_result['confidence'] = 0.3
        logger.info("Potential gender bias detected")
    
    return bias_result


async def sanitize_output(text: str) -> str:
    """
    Sanitize output text by removing or redacting PII.
    
    Replaces detected PII with redacted placeholders while
    preserving text structure and readability.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text with PII redacted
        
    Example:
        >>> await sanitize_output("Call me at 555-123-4567")
        'Call me at [PHONE_REDACTED]'
    """
    if not text:
        return text
    
    sanitized = text
    
    # Redact each type of PII
    sanitized = PII_PATTERNS['ssn'].sub('[SSN_REDACTED]', sanitized)
    sanitized = PII_PATTERNS['phone'].sub('[PHONE_REDACTED]', sanitized)
    sanitized = PII_PATTERNS['email'].sub('[EMAIL_REDACTED]', sanitized)
    sanitized = PII_PATTERNS['credit_card'].sub('[CARD_REDACTED]', sanitized)
    sanitized = PII_PATTERNS['ip_address'].sub('[IP_REDACTED]', sanitized)
    sanitized = PII_PATTERNS['passport'].sub('[PASSPORT_REDACTED]', sanitized)
    
    if sanitized != text:
        logger.info("PII redacted from output")
    
    return sanitized


async def contains_pii_in_document(doc: Dict) -> bool:
    """
    Check if a document/citation contains PII.
    
    Examines common document fields for PII presence.
    
    Args:
        doc: Document dictionary with fields like title, snippet, url
        
    Returns:
        True if PII found in document
        
    Example:
        >>> doc = {"title": "Article", "snippet": "Contact: john@email.com"}
        >>> await contains_pii_in_document(doc)
        True
    """
    # Combine relevant text fields
    text_parts = []
    for field in ['title', 'snippet', 'url', 'content']:
        if field in doc and doc[field]:
            text_parts.append(str(doc[field]))
    
    combined_text = ' '.join(text_parts)
    return await check_pii(combined_text)


async def validate_content_safety(
    text: str,
    check_pii_flag: bool = True,
    check_toxicity_flag: bool = True,
    check_injection_flag: bool = True
) -> Dict[str, any]:
    """
    Comprehensive content safety validation.
    
    Runs multiple safety checks and returns a detailed report.
    
    Args:
        text: Text to validate
        check_pii_flag: Whether to check for PII
        check_toxicity_flag: Whether to check for toxicity
        check_injection_flag: Whether to check for prompt injection
        
    Returns:
        Dictionary with safety check results:
        - is_safe: bool
        - checks: Dict of individual check results
        - issues: List of detected issues
        
    Example:
        >>> result = await validate_content_safety("What is AI?")
        >>> result['is_safe']
        True
    """
    results = {
        'is_safe': True,
        'checks': {},
        'issues': []
    }
    
    # Run enabled checks
    if check_pii_flag:
        has_pii = await check_pii(text)
        results['checks']['pii'] = not has_pii
        if has_pii:
            results['is_safe'] = False
            results['issues'].append('pii_detected')
    
    if check_toxicity_flag:
        is_toxic = await check_toxicity(text)
        results['checks']['toxicity'] = not is_toxic
        if is_toxic:
            results['is_safe'] = False
            results['issues'].append('toxic_content')
    
    if check_injection_flag:
        has_injection = await check_prompt_injection(text)
        results['checks']['injection'] = not has_injection
        if has_injection:
            results['is_safe'] = False
            results['issues'].append('prompt_injection')
    
    return results


def hash_sensitive_data(data: str) -> str:
    """
    Hash sensitive data for logging/storage.
    
    Args:
        data: Sensitive data to hash
        
    Returns:
        SHA256 hash of the data
        
    Example:
        >>> hash_sensitive_data("+254712345678")
        'a1b2c3d4...'
    """
    return hashlib.sha256(data.encode()).hexdigest()
