"""
inference/refusal.py
--------------------
Handles queries classified as ADVISORY by returning a standard,
compliant refusal message pointing users back to the actual fund pages.
"""

from datetime import date
from ingestion.corpus_urls import CORPUS_FUNDS

def get_refusal_message() -> str:
    """
    Returns the standard refusal template.
    """
    today_str = date.today().strftime("%Y-%m-%d")
    
    msg = (
        "I'm designed to answer factual questions about mutual fund schemes only "
        "and cannot provide investment advice or recommendations.\n\n"
        "For factual details about the funds in this assistant, please visit the "
        "respective Groww fund page directly.\n\n"
        f"Last updated from sources: {today_str}"
    )
    return msg
