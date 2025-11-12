"""
Database Utilities Module

Provides async database operations using SQLAlchemy with PostgreSQL.
Includes connection management, session handling, and model definitions.

This module implements:
- Async SQLAlchemy engine and session management
- Database models for research queries and results
- CRUD operations for persistence
- Connection pooling and health checks
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    ForeignKey, JSON, select, and_, or_
)
from sqlalchemy.pool import NullPool, QueuePool

from ..config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


# ==================== Database Models ====================

class ResearchQuery(Base):
    """
    Model for storing research queries and their metadata.
    
    Tracks user queries, their source, and execution metadata.
    """
    __tablename__ = "research_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False, index=True)
    source = Column(String(50), nullable=False, default="web_ui")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Execution metadata
    status = Column(String(50), default="pending")  # pending, completed, failed
    duration_ms = Column(Integer, nullable=True)
    iterations = Column(Integer, default=0)
    
    # User context (hashed for privacy)
    user_hash = Column(String(64), nullable=True, index=True)
    
    # Relationships
    results = relationship("ResearchResult", back_populates="query", cascade="all, delete-orphan")
    timeline_steps = relationship("TimelineStep", back_populates="query", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "query_text": self.query_text,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "iterations": self.iterations
        }


class ResearchResult(Base):
    """
    Model for storing research results with answers and citations.
    """
    __tablename__ = "research_results"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("research_queries.id"), nullable=False)
    
    # Result content
    answer = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)  # List of citation dicts
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    citation_count = Column(Integer, default=0)
    has_hallucination = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    query = relationship("ResearchQuery", back_populates="results")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "query_id": self.query_id,
            "answer": self.answer,
            "citations": self.citations,
            "confidence_score": self.confidence_score,
            "citation_count": self.citation_count,
            "has_hallucination": self.has_hallucination,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class TimelineStep(Base):
    """
    Model for storing agent execution timeline steps.
    """
    __tablename__ = "timeline_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("research_queries.id"), nullable=False)
    
    step_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(50), default="success")
    
    # Relationships
    query = relationship("ResearchQuery", back_populates="timeline_steps")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "step": self.step_name,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration_ms": self.duration_ms,
            "status": self.status
        }


# ==================== Database Manager ====================

class DatabaseManager:
    """
    Database connection and session manager.
    
    Handles SQLAlchemy engine creation, session management,
    and database operations.
    """
    
    def __init__(self):
        """Initialize database manager."""
        self.engine: Optional[AsyncEngine] = None
        self.session_maker: Optional[async_sessionmaker] = None
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize database engine and create tables.
        
        Creates the async engine with connection pooling
        and initializes all tables.
        """
        if self._initialized:
            logger.warning("Database already initialized")
            return
        
        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                settings.postgres_url,
                echo=settings.debug,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
            )
            
            # Create session maker
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create all tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self):
        """
        Get async database session context manager.
        
        Yields:
            AsyncSession for database operations
            
        Example:
            >>> async with db_manager.get_session() as session:
            ...     query = await session.execute(select(ResearchQuery))
            ...     results = query.scalars().all()
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """
        Check database connectivity.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            async with self.get_session() as session:
                await session.execute(select(1))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


# ==================== CRUD Operations ====================

async def create_research_query(
    query_text: str,
    source: str = "web_ui",
    user_hash: Optional[str] = None
) -> ResearchQuery:
    """
    Create a new research query record.
    
    Args:
        query_text: The research query text
        source: Source of the query (web_ui, sms, api)
        user_hash: Hashed user identifier
        
    Returns:
        Created ResearchQuery instance
        
    Example:
        >>> query = await create_research_query("What is quantum computing?", "web_ui")
        >>> print(query.id)
        1
    """
    async with db_manager.get_session() as session:
        query = ResearchQuery(
            query_text=query_text,
            source=source,
            user_hash=user_hash,
            status="pending"
        )
        session.add(query)
        await session.flush()
        await session.refresh(query)
        logger.info(f"Created research query with ID: {query.id}")
        return query


async def update_query_status(
    query_id: int,
    status: str,
    completed_at: Optional[datetime] = None,
    duration_ms: Optional[int] = None,
    iterations: Optional[int] = None
) -> Optional[ResearchQuery]:
    """
    Update research query status and metadata.
    
    Args:
        query_id: ID of the query to update
        status: New status (pending, completed, failed)
        completed_at: Completion timestamp
        duration_ms: Total execution duration
        iterations: Number of reflection iterations
        
    Returns:
        Updated ResearchQuery or None if not found
    """
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(ResearchQuery).where(ResearchQuery.id == query_id)
        )
        query = result.scalar_one_or_none()
        
        if query:
            query.status = status
            if completed_at:
                query.completed_at = completed_at
            if duration_ms is not None:
                query.duration_ms = duration_ms
            if iterations is not None:
                query.iterations = iterations
            
            await session.flush()
            logger.info(f"Updated query {query_id} status to {status}")
        
        return query


async def save_research_result(
    query_id: int,
    answer: str,
    citations: List[Dict],
    confidence_score: Optional[float] = None,
    has_hallucination: bool = False
) -> ResearchResult:
    """
    Save research result with answer and citations.
    
    Args:
        query_id: ID of the parent query
        answer: Synthesized answer text
        citations: List of citation dictionaries
        confidence_score: Answer confidence (0.0-1.0)
        has_hallucination: Whether hallucination was detected
        
    Returns:
        Created ResearchResult instance
    """
    async with db_manager.get_session() as session:
        result = ResearchResult(
            query_id=query_id,
            answer=answer,
            citations=citations,
            citation_count=len(citations),
            confidence_score=confidence_score,
            has_hallucination=has_hallucination
        )
        session.add(result)
        await session.flush()
        await session.refresh(result)
        logger.info(f"Saved research result for query {query_id}")
        return result


async def add_timeline_step(
    query_id: int,
    step_name: str,
    description: str = "",
    details: Optional[Dict] = None,
    duration_ms: Optional[int] = None,
    status: str = "success"
) -> TimelineStep:
    """
    Add a timeline step to a query.
    
    Args:
        query_id: ID of the parent query
        step_name: Name of the step
        description: Human-readable description
        details: Additional structured details
        duration_ms: Step duration in milliseconds
        status: Step status (success, error, skipped)
        
    Returns:
        Created TimelineStep instance
    """
    async with db_manager.get_session() as session:
        step = TimelineStep(
            query_id=query_id,
            step_name=step_name,
            description=description,
            details=details,
            duration_ms=duration_ms,
            status=status
        )
        session.add(step)
        await session.flush()
        return step


async def get_research_query(query_id: int) -> Optional[ResearchQuery]:
    """
    Retrieve a research query by ID.
    
    Args:
        query_id: Query ID to retrieve
        
    Returns:
        ResearchQuery instance or None if not found
    """
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(ResearchQuery).where(ResearchQuery.id == query_id)
        )
        return result.scalar_one_or_none()


async def get_query_with_results(query_id: int) -> Optional[Dict[str, Any]]:
    """
    Get complete query data including results and timeline.
    
    Args:
        query_id: Query ID to retrieve
        
    Returns:
        Dictionary with query, results, and timeline
    """
    async with db_manager.get_session() as session:
        # Get query
        query_result = await session.execute(
            select(ResearchQuery).where(ResearchQuery.id == query_id)
        )
        query = query_result.scalar_one_or_none()
        
        if not query:
            return None
        
        # Get results
        results_query = await session.execute(
            select(ResearchResult).where(ResearchResult.query_id == query_id)
        )
        results = results_query.scalars().all()
        
        # Get timeline
        timeline_query = await session.execute(
            select(TimelineStep)
            .where(TimelineStep.query_id == query_id)
            .order_by(TimelineStep.timestamp)
        )
        timeline = timeline_query.scalars().all()
        
        return {
            "query": query.to_dict(),
            "results": [r.to_dict() for r in results],
            "timeline": [t.to_dict() for t in timeline]
        }


async def get_recent_queries(limit: int = 10, source: Optional[str] = None) -> List[ResearchQuery]:
    """
    Get recent research queries.
    
    Args:
        limit: Maximum number of queries to return
        source: Optional filter by source
        
    Returns:
        List of ResearchQuery instances
    """
    async with db_manager.get_session() as session:
        query = select(ResearchQuery).order_by(ResearchQuery.created_at.desc()).limit(limit)
        
        if source:
            query = query.where(ResearchQuery.source == source)
        
        result = await session.execute(query)
        return result.scalars().all()


# ==================== Initialization Function ====================

async def init_db():
    """
    Initialize database on application startup.
    
    Call this function during FastAPI startup event.
    """
    await db_manager.initialize()
    logger.info("Database initialization complete")


async def close_db():
    """
    Close database connections on application shutdown.
    
    Call this function during FastAPI shutdown event.
    """
    await db_manager.close()
    logger.info("Database connections closed")
