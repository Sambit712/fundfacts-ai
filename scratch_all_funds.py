import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ingestion.scraper import scrape_all_funds
from ingestion.cleaner import clean
from ingestion.corpus_urls import CORPUS_FUNDS

results = scrape_all_funds(CORPUS_FUNDS)

for result in results:
    cleaned = clean(result["raw_text"])
    lines = [l for l in cleaned.strip().split("\n") if l.strip()]
    char_count = len(cleaned)
    word_count = len(cleaned.split())
    print(f"[{result['fund_id']}] lines={len(lines)} chars={char_count} words={word_count}")
    print(cleaned)
    print("---")
