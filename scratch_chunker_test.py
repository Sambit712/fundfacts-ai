import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ingestion.scraper import scrape_fund
from ingestion.cleaner import clean
from ingestion.chunker import chunk
from ingestion.corpus_urls import CORPUS_FUNDS

fund = CORPUS_FUNDS[0]  # HDFC Mid Cap
scraped = scrape_fund(fund)
cleaned = clean(scraped["raw_text"])

fund_meta = {**fund, "source_url": scraped["source_url"], "scraped_date": scraped["scraped_date"]}
chunks = chunk(cleaned, fund_meta)

print(f"Chunks produced: {len(chunks)}")
for c in chunks:
    cid   = c["chunk_id"]
    ctype = c["chunk_type"]
    ctext = c["content"]
    print()
    print(f"chunk_id   : {cid}")
    print(f"chunk_type : {ctype}")
    print(f"content    : {ctext}")
    print(f"fund_name  : {c['fund_name']} | amc: {c['amc']}")
    print(f"category   : {c['category']} | sub_category: {c['sub_category']}")
    print(f"source_url : {c['source_url']}")
    print(f"scraped_date: {c['scraped_date']}")
