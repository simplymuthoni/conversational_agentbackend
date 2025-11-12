# API Security

## Authentication
- SMS: Verified by AT webhook signature
- API: Bearer token (JWT)

## Rate Limiting
- Research endpoint: 10 req/min per user
- SMS endpoint: 30 req/min per phone number

## PII Handling
- Phone numbers hashed before storage
- User data encrypted at rest
- No logs contain sensitive data

## Secrets Management
- All keys in environment variables
- Never commit `.env` to git
- Use `.env.example` as template