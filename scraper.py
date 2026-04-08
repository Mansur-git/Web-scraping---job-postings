"""
Job Listing Scraper — TimesJobs
Scrapes: Job Title, Company, Location, Experience, Salary, Skills, Posted Date
Output: jobs.csv
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from datetime import datetime

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_URL = "https://www.timesjobs.com/candidate/job-search.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
DELAY_BETWEEN_PAGES = 2   # seconds — be polite to the server
MAX_PAGES = 5             # set to None for unlimited


def build_url(keyword: str, page: int) -> str:
    """Construct a paginated search URL."""
    params = {
        "searchType": "personalizedSearch",
        "from": "submit",
        "txtKeywords": keyword,
        "txtLocation": "",
        "pDate": "I",          # I = any date, 1 = last 1 day, 3 = last 3 days
        "sequence": page,
        "startPage": page,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE_URL}?{query}"


def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetch a page and return a BeautifulSoup object, or None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.HTTPError as e:
        log.error(f"HTTP error: {e}")
    except requests.exceptions.ConnectionError:
        log.error("Connection error — check your internet.")
    except requests.exceptions.Timeout:
        log.error("Request timed out.")
    return None


def clean(text: str) -> str:
    """Strip extra whitespace from scraped text."""
    return " ".join(text.split()) if text else "N/A"


def parse_jobs(soup: BeautifulSoup) -> list[dict]:
    """
    Parse all job cards from a single page.
    TimesJobs wraps each listing in <li class="clearfix job-bx wht-shd-bx">.
    """
    jobs = []
    listings = soup.find_all("li", class_="clearfix job-bx wht-shd-bx")

    if not listings:
        log.warning("No job cards found on this page — structure may have changed.")
        return jobs

    for card in listings:
        try:
            # ── Title ──────────────────────────────────────────────────────────
            title_tag = card.find("h2")
            title = clean(title_tag.get_text()) if title_tag else "N/A"

            # ── Company ────────────────────────────────────────────────────────
            company_tag = card.find("h3", class_="joblist-comp-name")
            company = clean(company_tag.get_text()) if company_tag else "N/A"

            # ── Location ───────────────────────────────────────────────────────
            location_tag = card.find("ul", class_="top-jd-dtl")
            if location_tag:
                loc_items = location_tag.find_all("li")
                location = clean(loc_items[-1].get_text()) if loc_items else "N/A"
            else:
                location = "N/A"

            # ── Experience ────────────────────────────────────────────────────
            exp_tag = card.find("ul", class_="top-jd-dtl")
            experience = "N/A"
            if exp_tag:
                exp_items = exp_tag.find_all("li")
                if exp_items:
                    experience = clean(exp_items[0].get_text())

            # ── Salary ────────────────────────────────────────────────────────
            salary_tag = card.find("li", class_="salary")
            if not salary_tag:
                # alternate path — sometimes inside .jd-desc
                desc = card.find("div", class_="jd-desc")
                salary_tag = desc.find("li", class_="salary") if desc else None
            salary = clean(salary_tag.get_text()) if salary_tag else "Not disclosed"

            # ── Skills ────────────────────────────────────────────────────────
            skills_tag = card.find("span", class_="srp-skills")
            skills = clean(skills_tag.get_text()) if skills_tag else "N/A"

            # ── Posted date ───────────────────────────────────────────────────
            date_tag = card.find("span", class_="sim-posted")
            posted = clean(date_tag.get_text()) if date_tag else "N/A"

            # ── Job URL ───────────────────────────────────────────────────────
            link_tag = title_tag.find("a") if title_tag else None
            job_url = link_tag["href"] if link_tag and link_tag.get("href") else "N/A"

            jobs.append(
                {
                    "title": title,
                    "company": company,
                    "location": location,
                    "experience": experience,
                    "salary": salary,
                    "skills": skills,
                    "posted": posted,
                    "url": job_url,
                }
            )

        except Exception as e:
            log.warning(f"Skipped a card due to error: {e}")
            continue

    return jobs


def scrape_jobs(keyword: str, max_pages: int | None = MAX_PAGES) -> pd.DataFrame:
    """
    Main scraping loop. Iterates pages until max_pages or no more listings.
    Returns a DataFrame of all scraped jobs.
    """
    all_jobs = []
    page = 1

    log.info(f"Starting scrape for: '{keyword}'")

    while True:
        if max_pages and page > max_pages:
            log.info(f"Reached page limit ({max_pages}). Stopping.")
            break

        url = build_url(keyword, page)
        log.info(f"Scraping page {page} → {url}")

        soup = fetch_page(url)
        if soup is None:
            log.error("Could not fetch page. Stopping.")
            break

        jobs = parse_jobs(soup)
        if not jobs:
            log.info("No more listings found. Done.")
            break

        all_jobs.extend(jobs)
        log.info(f"  → Found {len(jobs)} jobs (total so far: {len(all_jobs)})")

        page += 1
        time.sleep(DELAY_BETWEEN_PAGES)

    return pd.DataFrame(all_jobs)


def save_to_csv(df: pd.DataFrame, keyword: str) -> str:
    """Save DataFrame to a timestamped CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_kw = keyword.replace(" ", "_").lower()
    filename = f"jobs_{safe_kw}_{timestamp}.csv"

    df.to_csv(filename, index=False, encoding="utf-8-sig")
    log.info(f"Saved {len(df)} jobs → {filename}")
    return filename


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Change this to any skill/role you want to search
    SEARCH_KEYWORD = "python developer"

    df = scrape_jobs(keyword=SEARCH_KEYWORD, max_pages=MAX_PAGES)

    if df.empty:
        log.warning("No jobs scraped. The site structure may have changed.")
    else:
        # Preview in terminal
        print("\n── Sample Results ──────────────────────────────────")
        print(df[["title", "company", "location", "salary"]].head(10).to_string(index=False))
        print(f"\nTotal jobs scraped: {len(df)}")

        # Save
        save_to_csv(df, SEARCH_KEYWORD)
