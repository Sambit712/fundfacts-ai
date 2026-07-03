"""
ingestion/corpus_urls.py
------------------------
Registry of the 7 mutual fund Groww pages that form the RAG corpus.
Each entry provides all metadata needed for scraping, chunking, and retrieval.
"""

CORPUS_FUNDS = [
    {
        "id": "hdfc-mid-cap",
        "fund_name": "HDFC Mid Cap Fund Direct Growth",
        "amc": "HDFC Mutual Fund",
        "category": "Equity",
        "sub_category": "Mid Cap",
        "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    },
    {
        "id": "hdfc-multi-cap",
        "fund_name": "HDFC Multi Cap Fund Direct Growth",
        "amc": "HDFC Mutual Fund",
        "category": "Equity",
        "sub_category": "Multi Cap",
        "url": "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth",
    },
    {
        "id": "icici-multi-asset",
        "fund_name": "ICICI Prudential Multi Asset Fund Direct Growth",
        "amc": "ICICI Prudential Mutual Fund",
        "category": "Hybrid",
        "sub_category": "Multi Asset Allocation",
        "url": "https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth",
    },
    {
        "id": "sbi-contra",
        "fund_name": "SBI Contra Fund Direct Growth",
        "amc": "SBI Mutual Fund",
        "category": "Equity",
        "sub_category": "Contra",
        "url": "https://groww.in/mutual-funds/sbi-contra-fund-direct-growth",
    },
    {
        "id": "sbi-small-midcap",
        "fund_name": "SBI Small Midcap Fund Direct Growth",
        "amc": "SBI Mutual Fund",
        "category": "Equity",
        "sub_category": "Small Cap / Mid Cap",
        "url": "https://groww.in/mutual-funds/sbi-small-midcap-fund-direct-growth",
    },
    {
        "id": "uti-innovation",
        "fund_name": "UTI Innovation Fund Direct Growth",
        "amc": "UTI Mutual Fund",
        "category": "Equity",
        "sub_category": "Thematic / Sectoral",
        "url": "https://groww.in/mutual-funds/uti-innovation-fund-direct-growth",
    },
    {
        "id": "uti-small-cap",
        "fund_name": "UTI Small Cap Fund Direct Growth",
        "amc": "UTI Mutual Fund",
        "category": "Equity",
        "sub_category": "Small Cap",
        "url": "https://groww.in/mutual-funds/uti-small-cap-fund-direct-growth",
    },
]
