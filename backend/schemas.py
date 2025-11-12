from typing import List, Optional
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
query: str
source: Optional[str] = "web"


class Citation(BaseModel):
title: str
url: str
snippet: Optional[str]
source: Optional[str]


class TimelineStep(BaseModel):
step: str
details: Optional[list]


class ResearchResponse(BaseModel):
answer: str
citations: List[Citation]
timeline: List[TimelineStep]