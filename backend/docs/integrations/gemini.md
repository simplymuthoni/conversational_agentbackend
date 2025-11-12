# Gemini API Integration

## Configuration
- Model: `gemini-pro`
- Temperature: 0.7
- Max tokens: 2048

## Rate Limits
- Free tier: 60 RPM
- Our usage: ~30 RPM average

## Error Handling
- 429: Exponential backoff (2^n seconds)
- 500: Retry 3 times with 5s delay

## Cost Estimates
- $0.00025 per 1K characters
- Monthly budget: ~$50 (200K requests)