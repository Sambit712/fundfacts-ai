"""
api/main.py
-----------
FastAPI server exposing the /chat endpoint.
Pipeline: Classifier -> (Refusal) -> Retriever -> Generator -> Formatter.

Rate limit mitigations (Groq free tier: 30 RPM, 6K TPM):
- In-memory response cache (TTL = CACHE_TTL_SECONDS) eliminates LLM calls for repeated queries.
- Classifier uses max_tokens=5, saving ~145 tokens per Layer 2 call.
- Generator system prompt compressed to ~180 tokens.
- Both LLM calls retry with exponential backoff on 429 RateLimitError.
"""

import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from inference.classifier import classify_query
from inference.refusal import get_refusal_message
from inference.generator import generate_answer
from inference.formatter import format_factual_response, format_refusal_response
from retrieval.retriever import retrieve_chunks
from ingestion.corpus_urls import CORPUS_FUNDS
from config.settings import CACHE_TTL_SECONDS

app = FastAPI(title="Mutual Fund FAQ Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory response cache ──────────────────────────────────────────────────
# { normalized_query: (response_dict, expires_at_unix_ts) }
_response_cache: dict[str, tuple[dict, float]] = {}

def _normalize_query(query: str) -> str:
    """Normalize query for cache key: lowercase + strip whitespace."""
    return " ".join(query.lower().split())

def _cache_get(key: str) -> dict | None:
    entry = _response_cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    if entry:
        del _response_cache[key]   # evict expired entry
    return None

def _cache_set(key: str, value: dict) -> None:
    _response_cache[key] = (value, time.time() + CACHE_TTL_SECONDS)


# ── Request / Response models ─────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str


# ── /chat endpoint ────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    query = request.query.strip()
    if not query:
        return format_refusal_response("Query cannot be empty.")

    cache_key = _normalize_query(query)

    # ── Cache hit: return immediately, 0 LLM calls ────────────────────────────
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "cached": True}

    # ── Step 1: Classify ──────────────────────────────────────────────────────
    intent = classify_query(query)

    if intent == "ADVISORY":
        msg = get_refusal_message()
        response = format_refusal_response(msg)
        response["corpus_links"] = [fund["url"] for fund in CORPUS_FUNDS]
        _cache_set(cache_key, response)
        return response

    # ── Step 2: Retrieve ──────────────────────────────────────────────────────
    chunks = retrieve_chunks(query)

    # ── Step 3: Generate ──────────────────────────────────────────────────────
    raw_answer = generate_answer(query, chunks)

    # ── Step 4: Format ────────────────────────────────────────────────────────
    source_url   = chunks[0].get("source_url", "") if chunks else ""
    scraped_date = chunks[0].get("scraped_date", "") if chunks else ""
    response = format_factual_response(raw_answer, source_url, scraped_date)

    _cache_set(cache_key, response)
    return response

# ── Static UI ─────────────────────────────────────────────────────────────────
app.mount("/ui", StaticFiles(directory="ui"), name="ui")

@app.get("/")
async def read_root():
    return FileResponse("ui/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
