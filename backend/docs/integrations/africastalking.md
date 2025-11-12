# Africa's Talking SMS Integration

## Webhook Configuration
- Inbound URL: `https://your-domain.com/api/sms/inbound`
- Method: POST
- Content-Type: application/x-www-form-urlencoded

## Request Format
```json
{
  "from": "+254712345678",
  "text": "research: climate change",
  "linkId": "unique-id",
  "date": "2025-11-12 10:30:00"
}
```

## Response Requirements
- Must respond within 30 seconds
- Max SMS length: 160 chars (split if longer)