"""
test_full_pipeline.py
---------------------
End-to-end test suite for the Mutual Fund FAQ Assistant.
Tests: settings, vector store, retriever, classifier, generator, caching, API.
Run: python test_full_pipeline.py
"""

import sys
import io
import time
import asyncio

# Fix Windows unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PASS = "\u2705 PASS"
FAIL = "\u274c FAIL"
SKIP = "\u26a0\ufe0f  SKIP"

results = []

def report(name, status, detail=""):
    icon = {"PASS": PASS, "FAIL": FAIL, "SKIP": SKIP}[status]
    line = f"{icon}  {name}"
    if detail:
        line += f"\n        {detail}"
    print(line)
    results.append((name, status))

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print(" MUTUAL FUND FAQ ASSISTANT — TEST SUITE")
print("="*60 + "\n")

# ── T1: Settings load ─────────────────────────────────────────────────────────
print("── T1: Settings ─────────────────────────────────────────")
try:
    from config.settings import (
        LLM_MODEL, EMBEDDING_MODEL, EMBEDDING_DIMENSION,
        TOP_K, CHUNKS_PER_FUND, CACHE_TTL_SECONDS,
        GROQ_RPM_LIMIT, GROQ_TPM_LIMIT, GROQ_API_KEY
    )
    assert LLM_MODEL == "llama-3.1-8b-instant", f"LLM_MODEL mismatch: {LLM_MODEL}"
    assert EMBEDDING_MODEL == "BAAI/bge-small-en-v1.5", f"Embedding model mismatch"
    assert EMBEDDING_DIMENSION == 384
    assert TOP_K == 4
    assert CHUNKS_PER_FUND == 3
    assert CACHE_TTL_SECONDS == 3600
    assert GROQ_RPM_LIMIT == 30
    assert GROQ_TPM_LIMIT == 6000
    assert GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here", "API key not set"
    report("T1-1 All settings load correctly", "PASS", f"model={LLM_MODEL}, embed_dim={EMBEDDING_DIMENSION}, cache_ttl={CACHE_TTL_SECONDS}s")
except Exception as e:
    report("T1-1 All settings load correctly", "FAIL", str(e))

# ── T2: Vector store integrity ─────────────────────────────────────────────────
print("\n── T2: Vector Store ─────────────────────────────────────")
try:
    from config.settings import VECTOR_STORE_PATH, COLLECTION_NAME
    from ingestion.corpus_urls import CORPUS_FUNDS
    import chromadb
    client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    total = collection.count()
    assert total == 21, f"Expected 21 chunks, got {total}"
    report("T2-1 Total chunk count = 21", "PASS", f"{total} chunks in collection")
except Exception as e:
    report("T2-1 Total chunk count = 21", "FAIL", str(e))

try:
    required_meta = ["chunk_id", "chunk_type", "fund_name", "amc", "category", "sub_category", "source_url", "scraped_date"]
    sample = collection.get(limit=5, include=["metadatas", "documents"])
    for i, meta in enumerate(sample["metadatas"]):
        for key in required_meta:
            assert key in meta, f"Chunk {i} missing: {key}"
        assert len(sample["documents"][i]) > 50, f"Chunk {i} content too short"
    report("T2-2 Metadata schema valid (5-chunk sample)", "PASS", f"All {len(required_meta)} keys present")
except Exception as e:
    report("T2-2 Metadata schema valid (5-chunk sample)", "FAIL", str(e))

try:
    for fund in CORPUS_FUNDS:
        r = collection.get(where={"fund_name": fund["fund_name"]}, include=["metadatas"])
        assert len(r["ids"]) == 3, f"{fund['id']}: expected 3 chunks, got {len(r['ids'])}"
    report("T2-3 Every fund has exactly 3 chunks", "PASS", f"All {len(CORPUS_FUNDS)} funds verified")
except Exception as e:
    report("T2-3 Every fund has exactly 3 chunks", "FAIL", str(e))

# ── T3: Retriever ─────────────────────────────────────────────────────────────
print("\n── T3: Retriever ─────────────────────────────────────────")
try:
    from retrieval.retriever import detect_funds, retrieve_chunks
    detected = detect_funds("What is the NAV of HDFC Mid Cap?")
    assert detected == ["HDFC Mid Cap Fund Direct Growth"], f"Got: {detected}"
    report("T3-1 Fund name detection (single)", "PASS", f"Detected: {detected}")
except Exception as e:
    report("T3-1 Fund name detection (single)", "FAIL", str(e))

try:
    detected_multi = detect_funds("Compare SBI Contra and UTI Small Cap expense ratio")
    assert len(detected_multi) == 2, f"Expected 2 funds, got {len(detected_multi)}: {detected_multi}"
    report("T3-2 Fund name detection (multi)", "PASS", f"Detected {len(detected_multi)}: {detected_multi}")
except Exception as e:
    report("T3-2 Fund name detection (multi)", "FAIL", str(e))

try:
    chunks = retrieve_chunks("What is the NAV of HDFC Mid Cap?")
    assert len(chunks) == 3, f"Expected 3 chunks for HDFC Mid Cap, got {len(chunks)}"
    assert all(c["fund_name"] == "HDFC Mid Cap Fund Direct Growth" for c in chunks)
    chunk_types = {c["chunk_type"] for c in chunks}
    assert chunk_types == {"key_facts", "investment", "profile"}, f"Missing chunk types: {chunk_types}"
    report("T3-3 Fund-specific retrieval (HDFC Mid Cap)", "PASS",
           f"Got {len(chunks)} chunks: {sorted(chunk_types)}")
except Exception as e:
    report("T3-3 Fund-specific retrieval (HDFC Mid Cap)", "FAIL", str(e))

try:
    broad_chunks = retrieve_chunks("What is the minimum SIP amount?")
    assert len(broad_chunks) > 0, "No chunks returned for broad query"
    assert len(broad_chunks) <= 6, f"Too many chunks for broad query: {len(broad_chunks)}"
    report("T3-4 Broad query retrieval (no fund mentioned)", "PASS",
           f"Returned {len(broad_chunks)} chunks across funds")
except Exception as e:
    report("T3-4 Broad query retrieval (no fund mentioned)", "FAIL", str(e))

# ── T4: Classifier ─────────────────────────────────────────────────────────────
print("\n── T4: Classifier ────────────────────────────────────────")
try:
    from inference.classifier import is_advisory_by_keywords
    advisory_queries = [
        "Should I invest in HDFC Mid Cap?",
        "which is better UTI or SBI?",
        "recommend a good fund for me",
    ]
    for q in advisory_queries:
        assert is_advisory_by_keywords(q), f"Should be ADVISORY (keyword): {q}"
    report("T4-1 Keyword blocklist (Layer 1) — advisory detection", "PASS",
           f"All {len(advisory_queries)} advisory queries correctly blocked")
except Exception as e:
    report("T4-1 Keyword blocklist (Layer 1) — advisory detection", "FAIL", str(e))

try:
    factual_queries = [
        "What is the NAV of HDFC Mid Cap?",
        "What is the expense ratio of SBI Contra?",
        "Who manages UTI Small Cap Fund?",
    ]
    for q in factual_queries:
        assert not is_advisory_by_keywords(q), f"Should be FACTUAL (keyword): {q}"
    report("T4-2 Keyword blocklist (Layer 1) — factual pass-through", "PASS",
           f"All {len(factual_queries)} factual queries pass through correctly")
except Exception as e:
    report("T4-2 Keyword blocklist (Layer 1) — factual pass-through", "FAIL", str(e))

try:
    from inference.classifier import classify_query
    result = classify_query("Should I invest in HDFC Mid Cap?")
    assert result == "ADVISORY", f"Expected ADVISORY, got {result}"
    report("T4-3 classify_query() — advisory keyword query", "PASS", f"Returned: {result}")
except Exception as e:
    report("T4-3 classify_query() — advisory keyword query", "FAIL", str(e))

try:
    result_factual = classify_query("What is the expense ratio of SBI Contra?")
    assert result_factual == "FACTUAL", f"Expected FACTUAL, got {result_factual}"
    report("T4-4 classify_query() — factual query (LLM Layer 2)", "PASS", f"Returned: {result_factual}")
except Exception as e:
    report("T4-4 classify_query() — factual query (LLM Layer 2)", "FAIL", str(e))

# ── T5: Generator ─────────────────────────────────────────────────────────────
print("\n── T5: Generator ─────────────────────────────────────────")
try:
    from inference.generator import generate_answer
    test_chunks = retrieve_chunks("What is the NAV of HDFC Mid Cap?")
    answer = generate_answer("What is the NAV of HDFC Mid Cap?", test_chunks)
    assert isinstance(answer, str) and len(answer) > 20, "Answer too short or invalid"
    sentences = [s.strip() for s in answer.split(".") if s.strip()]
    assert len(sentences) <= 5, f"Answer may be too long: {len(sentences)} sentences"
    report("T5-1 Generator — factual answer for HDFC Mid Cap NAV", "PASS",
           f"Answer ({len(answer)} chars): {answer[:120]}...")
except Exception as e:
    report("T5-1 Generator — factual answer", "FAIL", str(e))

# ── T6: Cache ─────────────────────────────────────────────────────────────────
print("\n── T6: Response Cache ────────────────────────────────────")
try:
    from api.main import _cache_set, _cache_get, _normalize_query

    q = "What is the NAV of HDFC Mid Cap?"
    key = _normalize_query(q)
    payload = {"type": "factual", "answer": "Test answer", "source": "http://example.com", "last_updated": "2026-07-02"}

    assert _cache_get(key) is None, "Cache should be empty initially"
    _cache_set(key, payload)
    cached = _cache_get(key)
    assert cached == payload, f"Cache miss after set: {cached}"
    report("T6-1 Cache set and get (TTL=1h)", "PASS", f"Key: '{key[:40]}...'")
except Exception as e:
    report("T6-1 Cache set and get", "FAIL", str(e))

try:
    # Test normalisation: different casing/spacing should hit same cache entry
    same_key_variants = [
        "What is the NAV of HDFC Mid Cap?",
        "what is the nav of hdfc mid cap?",
        "  what is the nav of hdfc mid cap?  ",
    ]
    keys = [_normalize_query(v) for v in same_key_variants]
    assert len(set(keys)) == 1, f"Normalisation broken, got distinct keys: {set(keys)}"
    report("T6-2 Cache key normalisation (case/whitespace)", "PASS")
except Exception as e:
    report("T6-2 Cache key normalisation", "FAIL", str(e))

# ── T7: Full API pipeline ──────────────────────────────────────────────────────
print("\n── T7: Full API Pipeline ─────────────────────────────────")
async def run_api_tests():
    from api.main import chat_endpoint, ChatRequest

    # Factual
    try:
        req = ChatRequest(query="What is the expense ratio of SBI Contra?")
        res = await chat_endpoint(req)
        assert res["type"] == "factual", f"Expected factual, got {res['type']}"
        assert res["answer"], "Empty answer"
        assert res["source"], "Missing source URL"
        report("T7-1 POST /chat — factual query (SBI Contra expense ratio)", "PASS",
               f"Answer: {res['answer'][:100]}...")
    except Exception as e:
        report("T7-1 POST /chat — factual query", "FAIL", str(e))

    # Advisory (keyword blocked, 0 LLM calls)
    try:
        req = ChatRequest(query="Should I invest in UTI Innovation Fund?")
        res = await chat_endpoint(req)
        assert res["type"] == "refusal", f"Expected refusal, got {res['type']}"
        assert "corpus_links" in res, "Missing corpus_links in refusal"
        assert len(res["corpus_links"]) == 7
        report("T7-2 POST /chat — advisory query (keyword block)", "PASS",
               f"Refusal returned with {len(res['corpus_links'])} corpus links")
    except Exception as e:
        report("T7-2 POST /chat — advisory query", "FAIL", str(e))

    # Cache hit
    try:
        req = ChatRequest(query="What is the expense ratio of SBI Contra?")
        t0 = time.time()
        res = await chat_endpoint(req)
        elapsed = time.time() - t0
        assert res.get("cached") is True, "Expected cache hit"
        report("T7-3 POST /chat — cache hit on repeated query", "PASS",
               f"Returned in {elapsed*1000:.0f}ms (cached=True)")
    except Exception as e:
        report("T7-3 POST /chat — cache hit", "FAIL", str(e))

    # Empty query
    try:
        req = ChatRequest(query="")
        res = await chat_endpoint(req)
        assert res["type"] == "refusal", f"Expected refusal for empty query, got {res['type']}"
        report("T7-4 POST /chat — empty query handled", "PASS")
    except Exception as e:
        report("T7-4 POST /chat — empty query", "FAIL", str(e))

asyncio.run(run_api_tests())

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for _, s in results if s == "PASS")
failed = sum(1 for _, s in results if s == "FAIL")
skipped = sum(1 for _, s in results if s == "SKIP")
print(f" RESULTS: {passed} passed  |  {failed} failed  |  {skipped} skipped  |  {len(results)} total")
print("="*60 + "\n")
if failed:
    sys.exit(1)
