"""
ingestion/scraper.py
--------------------
Fetches raw page content from each Groww fund URL using Playwright
(headless Chromium) to handle JavaScript-rendered pages.
"""
import datetime
import time
from playwright.sync_api import sync_playwright


def _scrape_page(page, fund: dict, timeout: int = 60000) -> dict:
    """Scrape a single fund page using an already-open Playwright page."""
    url = fund["url"]

    # Navigate — use domcontentloaded (faster) then wait for key content
    page.goto(url, wait_until="domcontentloaded", timeout=timeout)

    # Wait for the fund detail section to render (the "About" or NAV block)
    try:
        page.wait_for_selector("text=Expense ratio", timeout=15000)
    except Exception:
        # Fallback: give the page a few more seconds
        time.sleep(5)

    raw_text = page.locator("body").inner_text()

    return {
        "fund_id": fund["id"],
        "fund_name": fund["fund_name"],
        "amc": fund["amc"],
        "category": f"{fund.get('category', '')} - {fund.get('sub_category', '')}".strip(" -"),
        "source_url": url,
        "scraped_date": datetime.date.today().strftime("%Y-%m-%d"),
        "raw_text": raw_text,
    }


def scrape_fund(fund: dict, retries: int = 2) -> dict:
    """Scrape a single fund (opens and closes its own browser)."""
    for attempt in range(retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                result = _scrape_page(page, fund)
                browser.close()
                return result
        except Exception as e:
            if attempt == retries:
                raise RuntimeError(f"Failed to scrape {fund['id']} after {retries + 1} attempts: {e}")
            time.sleep(3)


def scrape_all_funds(funds: list[dict], retries: int = 2) -> list[dict]:
    """Scrape all funds reusing a single browser instance for speed."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for fund in funds:
            for attempt in range(retries + 1):
                try:
                    result = _scrape_page(page, fund)
                    results.append(result)
                    break
                except Exception as e:
                    if attempt == retries:
                        print(f"[WARN] Skipping {fund['id']}: {e}")
                    else:
                        time.sleep(3)

        browser.close()
    return results
