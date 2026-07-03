"""
ingestion/chunker.py
--------------------
Splits each fund's cleaned text into 3 semantic, field-level chunks:
  - key_facts   : Fund Name, NAV, Expense Ratio, Fund Size (AUM)
  - investment  : Fund Name, Min SIP, Exit Load, Benchmark Index, Investment Objective
  - profile     : Fund Name, Fund Manager, Overview

Each chunk carries full fund metadata + chunk_type for precise retrieval.
Expected output: 3 chunks × 7 funds = 21 chunks total.
"""
import re


def _parse_fields(cleaned_text: str) -> dict:
    """Parse the labelled-line output of cleaner.clean() into a field dict."""
    fields = {}
    for line in cleaned_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def chunk(cleaned_text: str, fund_meta: dict) -> list[dict]:
    """
    Build 3 semantic chunks from the cleaned fund text.

    Parameters
    ----------
    cleaned_text : str
        Output of ingestion.cleaner.clean()
    fund_meta : dict
        One entry from ingestion.corpus_urls.CORPUS_FUNDS, plus
        'scraped_date' and 'source_url' added by the scraper.

    Returns
    -------
    list[dict]  — each dict has 'chunk_id', 'content', and metadata keys.
    """
    f = _parse_fields(cleaned_text)

    fund_id       = fund_meta["id"]
    fund_name     = fund_meta["fund_name"]
    amc           = fund_meta["amc"]
    category      = fund_meta["category"]
    sub_category  = fund_meta["sub_category"]
    source_url    = fund_meta.get("source_url", "")
    scraped_date  = fund_meta.get("scraped_date", "")

    # ── Chunk 1: key_facts ────────────────────────────────────────────────────
    key_facts_lines = [f"Fund Name: {fund_name}"]
    for field in ["NAV", "Expense Ratio", "Fund Size (AUM)"]:
        if f.get(field):
            key_facts_lines.append(f"{field}: {f[field]}")

    # ── Chunk 2: investment ───────────────────────────────────────────────────
    investment_lines = [f"Fund Name: {fund_name}"]
    for field in ["Minimum SIP", "Exit Load", "Benchmark Index", "Investment Objective"]:
        if f.get(field):
            investment_lines.append(f"{field}: {f[field]}")

    # ── Chunk 3: profile ──────────────────────────────────────────────────────
    profile_lines = [f"Fund Name: {fund_name}"]
    for field in ["Fund Manager", "Overview"]:
        if f.get(field):
            profile_lines.append(f"{field}: {f[field]}")

    # ── Assemble chunk dicts ──────────────────────────────────────────────────
    base_meta = {
        "fund_name":    fund_name,
        "amc":          amc,
        "category":     category,
        "sub_category": sub_category,
        "source_url":   source_url,
        "scraped_date": scraped_date,
    }

    chunks = []
    for chunk_type, lines in [
        ("key_facts",  key_facts_lines),
        ("investment", investment_lines),
        ("profile",    profile_lines),
    ]:
        content = ". ".join(lines) + "."
        chunks.append({
            "chunk_id":   f"{fund_id}-{chunk_type}",
            "chunk_type": chunk_type,
            "content":    content,
            **base_meta,
        })

    return chunks
