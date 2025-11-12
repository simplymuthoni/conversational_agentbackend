import os
import httpx
from ..config import settings


async def send_sms_reply(to: str, message: str) -> bool:
"""Minimal Africa's Talking outbound via their REST API or SDK. Replace body with SDK.
Note: keep SMS message length in mind and PII redaction.
"""
# Placeholder: use Africa's Talking SDK in production
print(f"Sending SMS to {to}: {message[:160]}")
return True


async def call_llm(prompt: str) -> str:
"""Call Google Gemini or other LLM. Replace with real client.
"""
# Dummy reply for now
return "This is a stubbed LLM response. Replace with Gemini call."