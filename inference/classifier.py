"""
inference/classifier.py
-----------------------
Classifies user queries as either FACTUAL or ADVISORY.
Two-layer approach:
  Layer 1 — Keyword blocklist: zero LLM cost, instant.
  Layer 2 — LLM intent (max_tokens=5): minimal token cost (~105 tokens total).
"""

import time
from groq import Groq, RateLimitError
from config.settings import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE

# ── Layer 1: Keyword blocklist ────────────────────────────────────────────────
ADVISORY_KEYWORDS = [
    "should i invest", "is it good to invest", "which is better",
    "recommend", "best fund", "will it grow", "expected return",
    "compare", "outperform", "buy or not", "worth investing",
    "good investment", "safe to invest", "right time to invest"
]

def is_advisory_by_keywords(query: str) -> bool:
    query_lower = query.lower()
    return any(kw in query_lower for kw in ADVISORY_KEYWORDS)


# ── Retry helper ──────────────────────────────────────────────────────────────
def _call_with_retry(fn, *args, retries: int = 3, base_delay: float = 2.0, **kwargs):
    """Retry an LLM call with exponential backoff on 429 RateLimitError."""
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except RateLimitError:
            if attempt == retries - 1:
                raise
            wait = base_delay * (2 ** attempt)   # 2s, 4s, 8s
            print(f"[WARN] Rate limited (classifier). Retrying in {wait:.0f}s...")
            time.sleep(wait)


# ── Layer 2: LLM classifier ───────────────────────────────────────────────────
def classify_query(query: str) -> str:
    """
    Returns 'FACTUAL' or 'ADVISORY'.
    Layer 1 costs 0 tokens. Layer 2 uses max_tokens=5 (~105 tokens total).
    """
    if not query.strip():
        return "FACTUAL"

    # Layer 1 — free
    if is_advisory_by_keywords(query):
        return "ADVISORY"

    # Layer 2 — minimal LLM call
    system_prompt = (
        "You are a query classifier for a mutual fund facts assistant. "
        "Classify the query as FACTUAL or ADVISORY. "
        "FACTUAL: asks for a specific, verifiable fact (expense ratio, NAV, exit load, risk, benchmark, SIP minimum). "
        "ADVISORY: asks for opinions, investment recommendations, comparisons, predictions, or strategy advice. "
        "Respond with only: FACTUAL or ADVISORY"
    )

    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = _call_with_retry(
            client.chat.completions.create,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=5,       # only "FACTUAL" or "ADVISORY" needed — saves ~145 tokens/call
        )
        result = response.choices[0].message.content.strip().upper()
        return "ADVISORY" if "ADVISORY" in result else "FACTUAL"
    except RateLimitError:
        print("[WARN] Classifier rate-limited after retries. Defaulting to FACTUAL (fail open).")
        return "FACTUAL"
    except Exception as e:
        print(f"[WARN] Classifier LLM failed: {e}. Defaulting to FACTUAL (fail open).")
        return "FACTUAL"
