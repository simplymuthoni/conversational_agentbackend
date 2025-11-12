import re


PII_PATTERNS = [
re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), # SSN-ish
re.compile(r"\+?\d{7,15}") # phone number naive
]




def contains_pii(doc: dict) -> bool:
text = ' '.join([str(doc.get(k, '')) for k in ('title', 'snippet', 'url')])
for p in PII_PATTERNS:
if p.search(text):
return True
return False




def toxicity_check(text: str) -> bool:
# placeholder: integrate a safety model
return False




def hallucination_check(answer: str, do