from typing import List, Dict, Tuple
from .llm import call_llm


async def synthesize_answer(query: str, docs: List[Dict]) -> Tuple[str, List[Dict]]:
# Build a prompt with docs and ask the LLM to synthesize + cite
prompt = f"Synthesize an answer to: {query}\n\nDocuments:\n"
for i, d in enumerate(docs):
prompt += f"[{i}] {d.get('title')} - {d.get('url')}\n{d.get('snippet')}\n\n"


answer = await call_llm(prompt)
citations = [
{"title": d.get('title'), "url": d.get('url'), "snippet": d.get('snippet'), "source": d.get('source')}
for d in docs
]
return answer, citations