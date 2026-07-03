"""
inference/generator.py
----------------------
Generates a factual ≤3-sentence answer from retrieved context using Groq.
System prompt is compressed (~180 tokens) to conserve TPM.
Includes exponential backoff retry on 429 RateLimitError.
"""

import time
from groq import Groq, RateLimitError
from config.settings import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

# ── Compressed system prompt (~180 tokens vs original ~280) ──────────────────
_SYSTEM_PROMPT = (
    "You are a facts-only FAQ assistant for 7 mutual fund schemes: "
    "HDFC Mid Cap, HDFC Multi Cap, ICICI Prudential Multi Asset, "
    "SBI Contra, SBI Small Midcap, UTI Innovation, UTI Small Cap.\n"
    "Rules: (1) Answer in max 3 sentences. "
    "(2) Use ONLY the provided context. "
    "(3) No investment advice, comparisons, or return predictions. "
    "(4) If the answer isn't in the context, say: "
    "\"I don't have that information. Please visit the fund's Groww page for the latest details.\" "
    "(5) Cite the source Groww URL. "
    "(6) End with: \"Last updated: {date}\""
)


def _call_with_retry(fn, *args, retries: int = 3, base_delay: float = 2.0, **kwargs):
    """Retry an LLM call with exponential backoff on 429 RateLimitError."""
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except RateLimitError:
            if attempt == retries - 1:
                raise
            wait = base_delay * (2 ** attempt)  # 2s, 4s, 8s
            print(f"[WARN] Rate limited (generator). Retrying in {wait:.0f}s...")
            time.sleep(wait)


def generate_answer(query: str, retrieved_chunks: list[dict]) -> str:
    """
    Generate an answer using the retrieved context.
    Each chunk should have 'content', 'source_url', and 'scraped_date'.
    Token budget: ~600 tokens per call (180 system + 20 query + 250 context + 150 output).
    """
    if not retrieved_chunks:
        return "I don't have that information. Please visit the fund's Groww page for the latest details."

    # Build compact context string
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks):
        context_parts.append(
            f"[{i+1}] {chunk.get('content', '')}\n"
            f"Source: {chunk.get('source_url', '')} | Date: {chunk.get('scraped_date', '')}"
        )
    context_str = "\n\n".join(context_parts)

    dates = [c.get("scraped_date") for c in retrieved_chunks if c.get("scraped_date")]
    latest_date = max(dates) if dates else "Unknown"

    system = _SYSTEM_PROMPT.replace("{date}", latest_date)
    user_prompt = f"Context:\n{context_str}\n\nQuestion: {query}"

    client = Groq(api_key=GROQ_API_KEY)

    try:
        response = _call_with_retry(
            client.chat.completions.create,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except RateLimitError:
        return (
            "I'm temporarily unable to process your request due to high demand. "
            "Please try again in a moment."
        )
    except Exception as e:
        print(f"[ERROR] Generator LLM failed: {e}")
        return "I am currently unable to process requests. Please try again later."
