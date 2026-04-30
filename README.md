# Vera Message Engine

A production-ready Python FastAPI web service for the magicpin AI Challenge. This service is the intelligent message composition backend for Vera — magicpin's AI assistant for merchant growth.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# 3. Run locally
python main.py
# Or: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

| Endpoint       | Method | Description                             |
| -------------- | ------ | --------------------------------------- |
| `/v1/healthz`  | GET    | Health check                            |
| `/v1/metadata` | GET    | Bot metadata                            |
| `/v1/context`  | POST   | Store merchant/trigger/customer context |
| `/v1/tick`     | POST   | Get next message to send                |
| `/v1/reply`    | POST   | Handle merchant reply                   |

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/v1/healthz

# Push merchant context
curl -X POST http://localhost:8000/v1/context \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "merchant",
    "context_id": "m_001_drmeera",
    "version": 1,
    "payload": {
      "identity": {"name": "Dr. Meera Dental Clinic", "category": "dentist", "locality": "Koramangala, Bengaluru"},
      "performance": {"rating": 4.7, "reviews": 312, "monthly_visits": 890, "visit_trend": "dip_15pct"},
      "offers": [{"id": "o1", "name": "Dental Check-Up", "price": 299, "original": 599, "active": true}]
    },
    "delivered_at": "2026-04-30T10:00:00Z"
  }'

# Push trigger
curl -X POST http://localhost:8000/v1/context \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "trigger",
    "context_id": "t_001",
    "version": 1,
    "payload": {
      "type": "spike",
      "signal": "190 people searched Dental Check Up in Koramangala in last 2 hours",
      "urgency": "high",
      "timestamp": "2026-04-30T10:00:00Z"
    },
    "delivered_at": "2026-04-30T10:00:00Z"
  }'

# Tick — get next message
curl -X POST http://localhost:8000/v1/tick \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "m_001_drmeera",
    "trigger_id": "t_001",
    "tick_id": "tick_test_001",
    "timestamp": "2026-04-30T10:00:00Z"
  }'

# Reply — merchant says yes
curl -X POST http://localhost:8000/v1/reply \
  -H "Content-Type: application/json" \
  -d '{
    "tick_id": "tick_test_001",
    "merchant_id": "m_001_drmeera",
    "reply_text": "Yes go ahead",
    "timestamp": "2026-04-30T10:05:00Z"
  }'
```

## 🏗️ Architecture

### Project Structure

```
vera-engine/
├── main.py                  # FastAPI app entry point
├── routes/
│   ├── health.py            # GET /v1/healthz, GET /v1/metadata
│   ├── context.py           # POST /v1/context
│   ├── tick.py              # POST /v1/tick
│   └── reply.py             # POST /v1/reply
├── core/
│   ├── composer.py          # Main compose() function — THE BRAIN
│   ├── llm_client.py        # Groq + fallback provider abstraction
│   ├── state_store.py       # In-memory context store (thread-safe)
│   └── prompts.py           # All system prompts
├── models/
│   └── schemas.py           # Pydantic models for all request/response
├── .env.example
├── requirements.txt
└── README.md
```

### Key Components

1. **compose()** - The core message composition function in `core/composer.py`
    - Category-aware prompting (dentist, salon, restaurant, gym, pharmacy)
    - Uses real numbers from context (rating, offer price, locality)
    - Deterministic output (temperature=0.1)

2. **LLMClient** - Provider abstraction in `core/llm_client.py`
    - Primary: Groq (llama-3.3-70b-versatile)
    - Fallback: OpenAI-compatible
    - Easy provider switching via `LLM_PROVIDER` env var

3. **StateStore** - In-memory context storage in `core/state_store.py`
    - Thread-safe with locking
    - Version-based idempotency
    - No external dependencies

## 🔧 Configuration

| Variable         | Description       | Default                   |
| ---------------- | ----------------- | ------------------------- |
| `GROQ_API_KEY`   | Your Groq API key | Required                  |
| `LLM_PROVIDER`   | LLM provider      | `groq`                    |
| `LLM_MODEL`      | Model to use      | `llama-3.3-70b-versatile` |
| `OPENAI_API_KEY` | OpenAI fallback   | Optional                  |
| `BOT_NAME`       | Bot display name  | `Vera Message Engine`     |
| `PORT`           | Server port       | `8000`                    |

Get your free Groq API key at [console.groq.com](https://console.groq.com)

## ☁️ Deployment

### Render.com (Free Tier)

1. Push to GitHub
2. Create new Web Service on Render
3. Set environment variables in dashboard:
    - `GROQ_API_KEY` = your key
    - `LLM_PROVIDER` = groq
4. Deploy!

The service runs on port 8000 and is compatible with free tier (single process, no Redis needed).

## 📊 Scoring Criteria

The compose() function is designed to maximize:

1. **Decision quality** — combine trigger + merchant state + category fit BEFORE writing message
2. **Specificity** — use real numbers, offer prices, locality names from context
3. **Category fit** — clinical for dentist, visual for salon, urgent for restaurant
4. **Merchant fit** — mention their actual rating, offer name, locality, trend
5. **Engagement compulsion** — one strong reason to reply NOW, easy yes/no CTA

## ⚖️ Tradeoffs

- **In-memory state**: Resets on restart (intentional for free tier simplicity)
- **Easy Redis swap**: StateStore can be replaced with Redis client without API changes
- **Fast inference**: Groq provides sub-second response times
- **Provider flexibility**: OpenAI fallback available

## 👤 Author

**Rakesh Penugonda**  
Email: rakeshwgpcgr@gmail.com

See [NeoCode v2](https://github.com/rakeshpenugonda/neocode-v2) for evidence of production AI systems.

## 📄 License

MIT License
