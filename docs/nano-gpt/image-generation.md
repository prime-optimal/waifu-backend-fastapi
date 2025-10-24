# NanoGPT Image Generation API Reference

> **Reference Material:** This is documentation of the NanoGPT API v1/images/generations endpoint. It is not our own work and is kept minimal for reference only. For project-specific implementation, see `docs/features/multi-model-try-on.md`.

## Endpoint

```
POST https://nano-gpt.com/v1/images/generations
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

## Models We Use

| Model       | Processing Time | Input Format      | Image Limit | Notes                   |
| ----------- | --------------- | ----------------- | ----------- | ----------------------- |
| seedream-v4 | 25–35s          | URLs preferred    | 10          | Fast, reliable          |
| google:4@1  | 20–30s          | URLs preferred    | 4           | Fast, 1024x1024 output  |
| qwen-image  | 2–3+ minutes    | base64 required   | 4           | **Slow** — 180s timeout |

⚠️ If tests hang: Check which model is running. `qwen-image` is slow; wait 2–3 minutes.

## Request Format

```json
{
  "model": "google:4@1",
  "prompt": "Virtual try-on with costume references",
  "imageDataUrl": "data:image/jpeg;base64,[user image]",
  "imageDataUrls": ["https://url1", "https://url2"],
  "size": "1024x1024",
  "n": 1
}
```

## Response Format

```json
{
  "data": [
    {"b64_json": "[base64 image data]"}
  ]
}
```

## Error Codes

- `400`: Bad request — check model name, parameters, image format
- `401`: Invalid API key
- `429`: Rate limit exceeded
- `500`: Server error

## For Project Details

See:
- `src/clients/ai_provider.py` — Implementation with model timeouts
- `docs/features/multi-model-try-on.md` — Architecture & usage
