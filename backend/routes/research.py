from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..schemas import ResearchRequest, ResearchResponse, Citation, TimelineStep
from ..langgraph_agent import ResearchAgent
from ..config import settings


router = APIRouter()


agent = ResearchAgent()


@router.post("/research", response_model=ResearchResponse)
async def run_research(req: ResearchRequest):
if not req.query or len(req.query.strip()) == 0:
raise HTTPException(status_code=400, detail="Query is required")


# Run agent synchronously for MVP; later switch to background + job ID model
result = await agent.run(req.query, source=req.source)


return ResearchResponse(**result)