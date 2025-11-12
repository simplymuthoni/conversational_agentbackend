from fastapi import APIRouter, Form, BackgroundTasks
from ..schemas import ResearchResponse
from ..langgraph_agent import ResearchAgent
from ..services.llm import send_sms_reply


router = APIRouter()
agent = ResearchAgent()


@router.post("/sms/inbound")
async def inbound_sms(from_number: str = Form(...), text: str = Form(...)):
# Kick off research and reply
result = await agent.run(text, source='sms')
# Format short SMS-friendly reply (truncated)
short_reply = result['answer'][:1500]
# send via Africa's Talking helper (async or sync)
await send_sms_reply(to=from_number, message=short_reply)
return {"status": "accepted"}