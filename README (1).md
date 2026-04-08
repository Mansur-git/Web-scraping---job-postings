# Job Listing Scraper — TimesJobs + BeautifulSoup

Scrapes job listings from TimesJobs and exports them to a CSV file.

## What it collects

| Field      | Example                          |
|------------|----------------------------------|
| title      | Senior Python Developer          |
| company    | Infosys Ltd                      |
| location   | Hyderabad, Bengaluru             |
| experience | 3 - 6 yrs                       |
| salary     | Not disclosed / ₹8-12 LPA        |
| skills     | Python, Django, REST APIs        |
| posted     | Posted few days ago              |
| url        | https://timesjobs.com/...        |

---

## Setup

### 1. Clone / download the project

```
job_scraper/
├── scraper.py
├── requirements.txt
└── README.md
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Basic run

```bash
python scraper.py
```

By default it searches for **"python developer"** and scrapes up to **5 pages**.

### Change the search keyword

Open `scraper.py` and edit line near the bottom:

```python
SEARCH_KEYWORD = "data analyst"   # ← change this
```

### Change the number of pages

```python
MAX_PAGES = 10    # scrape up to 10 pages (~100 jobs)
MAX_PAGES = None  # scrape all available pages
```

---

## Output

A CSV file is saved in the same directory:

```
jobs_python_developer_20240315_143022.csv
```

---

## How it works

```
scraper.py
│
├── build_url()       — builds paginated TimesJobs search URLs
├── fetch_page()      — fetches HTML with error handling + headers
├── parse_jobs()      — extracts fields from each <li> job card
├── scrape_jobs()     — loop across pages, collect all results
└── save_to_csv()     — dumps DataFrame to timestamped CSV
```

---

## Notes

- A 2-second delay is added between pages to avoid overwhelming the server.
- If the site changes its HTML structure, update the CSS selectors in `parse_jobs()`.
- This scraper is for **educational purposes only**. Always check a website's `robots.txt` and Terms of Service before scraping.
