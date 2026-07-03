"""
config/settings.py
------------------
Central configuration for the Mutual Fund FAQ Assistant.
All tuneable parameters live here; secrets are loaded from .env.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ── LLM settings — Groq ──────────────────────────────────────────────────────
LLM_PROVIDER = "groq"
LLM_MODEL = "llama3-8b-8192"             # Fast, free-tier Groq model
LLM_MAX_TOKENS = 300
LLM_TEMPERATURE = 0.0                           # Deterministic for facts
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Embedding settings — BGE Small ───────────────────────────────────────────
# bge-small: 384d, ~130MB, 33M params — ideal for 21 short structured chunks
# Upgrade to bge-base (768d) only if corpus grows beyond ~5,000 chunks
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384

# ── Vector store settings ─────────────────────────────────────────────────────
VECTOR_STORE_PATH = "./data/chroma_db"
COLLECTION_NAME = "mutual_fund_corpus"

# ── Retrieval settings ────────────────────────────────────────────────────────
TOP_K = 4
MAX_CONTEXT_TOKENS = 1500

# ── Groq rate limits (llama-3.1-8b-instant free tier) ────────────────────────
GROQ_RPM_LIMIT   = 30       # Requests per minute
GROQ_TPM_LIMIT   = 6000     # Tokens per minute

# ── Response cache ────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS = 3600    # Cache identical query responses for 1 hour

# ── Chunking settings — semantic field-level ──────────────────────────────────
# Each fund is split into 3 topic chunks (not token-based)
CHUNKS_PER_FUND = 3                             # key_facts, investment, profile

# ── Corpus refresh ────────────────────────────────────────────────────────────
SCRAPE_DATE_FORMAT = "%Y-%m-%d"
STALENESS_DAYS = 30
