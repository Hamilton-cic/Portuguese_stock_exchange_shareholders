"""
Euronext Lisbon Shareholder Web Scraper
----------------------------------------
Scrapes shareholder information for each listed company and produces:
  - dataset.csv : nodes with id, label, type (company | person)
  - edges.csv   : directed edges with source, target, weight (% stake)
"""

import re
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MARKET_MIC = {
    "Euronext Lisbon": "XLIS",
    "Euronext Access Lisbon": "ALXL",
    "Euronext Growth Lisbon": "ENXL",
}


def slugify(name: str) -> str:
    """Convert a company/person name to a stable node id."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)          # remove punctuation
    name = re.sub(r"\s+", "_", name)              # spaces → underscores
    name = re.sub(r"_+", "_", name).strip("_")   # collapse consecutive _
    return name


def make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ---------------------------------------------------------------------------
# Scraping logic
# ---------------------------------------------------------------------------

def get_shareholders(driver: webdriver.Chrome, isin: str, mic: str) -> list[tuple[str, float]]:
    """
    Navigate to the company-information page and extract the shareholder table.
    Returns a list of (shareholder_name, percentage) tuples.
    """
    url = (
        f"https://live.euronext.com/pt/product/equities/{isin}-{mic}"
        f"/company-information"
    )
    driver.get(url)

    shareholders = []

    try:
        # Wait until the page body is present (JS has had a chance to run)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # The shareholder data is loaded via DataTables AJAX.
        # Give the page time to fire the AJAX call and populate the table.
        time.sleep(4)

        # --- Strategy 1: find the shareholder table by percentage cell pattern ---
        PCT_RE = re.compile(r"^\d[\d.,\s]*%\s*$")

        tables = driver.find_elements(By.TAG_NAME, "table")
        for table in tables:
            try:
                rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                if not rows:
                    continue

                # Check if last cell of first row looks like a percentage
                first_row_cells = rows[0].find_elements(By.TAG_NAME, "td")
                if len(first_row_cells) < 2:
                    continue
                last_cell_text = first_row_cells[-1].text.strip()
                if not PCT_RE.match(last_cell_text):
                    continue

                # This looks like the shareholder table
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        name = cells[0].text.strip()
                        pct_text = (
                            cells[-1].text.strip()
                            .replace(",", ".")
                            .replace("%", "")
                            .strip()
                        )
                        if name and pct_text:
                            try:
                                pct = float(pct_text)
                                shareholders.append((name, pct))
                            except ValueError:
                                pass

                if shareholders:
                    return shareholders

            except Exception:
                continue

        # --- Strategy 2: intercept the Euronext pd_es JSON API response ---
        # Execute JS to fetch the same endpoint the page uses
        api_url = f"https://live.euronext.com/en/pd_es/data/shareholder/{isin}-{mic}"
        result = driver.execute_script(
            """
            const response = await fetch(arguments[0], {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                }
            });
            return await response.json();
            """,
            api_url,
        )
        if result and result.get("aaData"):
            for row in result["aaData"]:
                # aaData rows are typically [name, pct, ...] or dict
                if isinstance(row, list) and len(row) >= 2:
                    name = re.sub(r"<[^>]+>", "", str(row[0])).strip()
                    pct_text = re.sub(r"[^0-9.,]", "", str(row[-1])).replace(",", ".")
                    if name and pct_text:
                        try:
                            shareholders.append((name, float(pct_text)))
                        except ValueError:
                            pass
                elif isinstance(row, dict):
                    # Column names may vary; pick first string and last numeric key
                    values = list(row.values())
                    if len(values) >= 2:
                        name = re.sub(r"<[^>]+>", "", str(values[0])).strip()
                        pct_text = re.sub(r"[^0-9.,]", "", str(values[-1])).replace(",", ".")
                        if name and pct_text:
                            try:
                                shareholders.append((name, float(pct_text)))
                            except ValueError:
                                pass

    except TimeoutException:
        print(f"  Timeout waiting for page: {isin}-{mic}")
    except Exception as exc:
        print(f"  Error scraping {isin}-{mic}: {exc}")

    return shareholders


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # --- Load and clean the existing CSV ---
    raw = pd.read_csv(
        "Euronext_Equities_2026-04-07.csv",
        sep=";",
        skiprows=[1, 2, 3],
    )

    # Keep only companies that were actively trading (Open Price != "-")
    df = raw[raw["Open Price"] != "-"].copy().reset_index(drop=True)
    print(f"Companies to scrape: {len(df)}")

    # --- Initialise output structures ---
    dataset_rows: list[dict] = []
    edges_rows: list[dict] = []

    # Track which node ids are listed Euronext companies
    listed_ids: set[str] = set()

    for _, row in df.iterrows():
        company_id = slugify(row["Name"])
        dataset_rows.append(
            {"id": company_id, "label": row["Name"], "type": "company"}
        )
        listed_ids.add(company_id)

    # --- Scrape shareholders ---
    driver = make_driver()
    shareholder_nodes: dict[str, str] = {}  # id -> label

    try:
        for _, row in df.iterrows():
            name = row["Name"]
            isin = row["ISIN"]
            market = row["Market"]
            mic = MARKET_MIC.get(market, "XLIS")
            company_id = slugify(name)

            print(f"Scraping {name} ({isin}-{mic}) …", end=" ", flush=True)
            shareholders = get_shareholders(driver, isin, mic)
            print(f"{len(shareholders)} shareholders found")

            for sh_name, pct in shareholders:
                sh_id = slugify(sh_name)
                shareholder_nodes[sh_id] = sh_name
                edges_rows.append(
                    {"source": sh_id, "target": company_id, "weight": pct}
                )

            time.sleep(1)  # polite delay between requests

    finally:
        driver.quit()

    # --- Add shareholder nodes to dataset (person unless already a listed company) ---
    for sh_id, sh_label in shareholder_nodes.items():
        if sh_id not in listed_ids:
            dataset_rows.append(
                {"id": sh_id, "label": sh_label, "type": "person"}
            )
        # If the shareholder is also a listed company, it's already in dataset_rows
        # with type="company" — no duplicate needed.

    # --- Build DataFrames and save ---
    dataset = pd.DataFrame(dataset_rows).drop_duplicates(subset="id").reset_index(drop=True)
    edges = pd.DataFrame(edges_rows).reset_index(drop=True)

    dataset.to_csv("dataset.csv", index=False)
    edges.to_csv("edges.csv", index=False)

    print("\n=== Done ===")
    print(f"dataset.csv  : {len(dataset)} nodes")
    print(f"edges.csv    : {len(edges)} edges")
    print("\nDataset preview:")
    print(dataset.head(10).to_string(index=False))
    print("\nEdges preview:")
    print(edges.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
