"""Stream corporate governance PDFs from cgov.pt and extract board members.

No PDFs or TXT files are saved to disk.  Each PDF is fetched into memory,
text is extracted with pdfplumber, Gemini extracts board members, and only
the small JSON result is written to disk.  A mapping CSV is also written.

This script replaces pass0 + pass1 + pass2 for year-specific runs.

Usage:
    python download_pdfs_cgov.py --year 2018
    python download_pdfs_cgov.py --year 2019 --json-dir E:\\Sociedade_dados\\2019\\json_members
    python download_pdfs_cgov.py --year 2020 --selenium  # force JS rendering

After this script completes, run:
    python pass3_atualizar_datasets.py --year YYYY
    python pass4_validar_log.py --year YYYY
"""

from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE_URL = "https://cgov.pt/governo-das-sociedades/relatorios-de-governo-das-sociedades"
REQUEST_DELAY = 1.5  # seconds between requests to avoid hammering the server


def _load_env_api_key() -> str:
    existing = os.getenv("GEMINI_API_KEY", "").strip()
    if existing:
        return existing
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "GEMINI_API_KEY":
            return value.strip().strip('"').strip("'")
    return ""


def _slugify_filename(url: str) -> str:
    """Derive a safe PDF filename from a URL."""
    name = urlparse(url).path.rstrip("/").split("/")[-1]
    name = re.sub(r"[^\w\-.]", "_", name)
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


# ---------------------------------------------------------------------------
# PDF URL discovery — requests + BeautifulSoup
# ---------------------------------------------------------------------------

def _discover_pdf_urls_requests(page_url: str, year: int) -> list[str]:
    """Return PDF URLs found on the year's listing page using BeautifulSoup."""
    import requests
    from bs4 import BeautifulSoup

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    })

    resp = session.get(page_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    pdf_urls: list[str] = []

    # Direct PDF links on the listing page
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"])
        if href.lower().endswith(".pdf") and href not in pdf_urls:
            pdf_urls.append(href)

    if pdf_urls:
        return pdf_urls

    # Follow per-company sub-pages that may contain the PDF link
    sub_links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"])
        if (
            "cgov.pt" in href
            and str(year) in href
            and href != page_url
            and not href.lower().endswith((".jpg", ".png", ".css", ".js"))
        ):
            sub_links.append(href)

    seen: set[str] = set()
    for link in sub_links[:100]:
        if link in seen:
            continue
        seen.add(link)
        try:
            sub_resp = session.get(link, timeout=30)
            sub_soup = BeautifulSoup(sub_resp.text, "html.parser")
            for a in sub_soup.find_all("a", href=True):
                href = urljoin(link, a["href"])
                if href.lower().endswith(".pdf") and href not in pdf_urls:
                    pdf_urls.append(href)
            time.sleep(REQUEST_DELAY)
        except Exception as exc:
            print(f"  [warn] sub-page {link}: {exc}")

    return pdf_urls


# ---------------------------------------------------------------------------
# PDF URL discovery — Selenium fallback
# ---------------------------------------------------------------------------

def _discover_pdf_urls_selenium(page_url: str, year: int) -> list[str]:
    """JS-rendered fallback: use Selenium to collect PDF links."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except Exception:
        service = Service()

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(service=service, options=options)
    pdf_urls: list[str] = []
    try:
        driver.get(page_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        time.sleep(2)

        anchors = driver.find_elements(By.TAG_NAME, "a")
        company_hrefs: list[str] = []
        for a in anchors:
            href = a.get_attribute("href") or ""
            if href.lower().endswith(".pdf"):
                pdf_urls.append(href)
            elif "cgov.pt" in href and str(year) in href and href != page_url:
                company_hrefs.append(href)

        if not pdf_urls:
            seen: set[str] = set()
            for href in company_hrefs[:100]:
                if href in seen:
                    continue
                seen.add(href)
                try:
                    driver.get(href)
                    time.sleep(1.5)
                    for a in driver.find_elements(By.TAG_NAME, "a"):
                        sub_href = a.get_attribute("href") or ""
                        if sub_href.lower().endswith(".pdf") and sub_href not in pdf_urls:
                            pdf_urls.append(sub_href)
                except Exception as exc:
                    print(f"  [warn] {href}: {exc}")
    finally:
        driver.quit()

    return pdf_urls


# ---------------------------------------------------------------------------
# Core streaming extraction loop
# ---------------------------------------------------------------------------

def stream_extract(
    year: int,
    json_dir: Path,
    mapping_path: Path,
    api_key: str,
    model: str,
    force_selenium: bool,
) -> int:
    """Discover PDF URLs, fetch each in memory, extract text + board members.

    Returns the number of companies successfully processed.
    """
    import requests
    import pandas as pd

    from board_pipeline import (
        AIContentExtractor,
        _members_have_quality_issues,
        extract_pdf_text_from_bytes,
        get_year_paths,
        save_json_output,
        slugify,
        timestamp,
    )

    page_url = f"{BASE_URL}/{year}"
    print(f"[{timestamp()}] Fetching listing page: {page_url}")

    if force_selenium:
        pdf_urls = _discover_pdf_urls_selenium(page_url, year)
    else:
        pdf_urls = _discover_pdf_urls_requests(page_url, year)
        if not pdf_urls:
            print("[requests] No PDF links found — trying Selenium...")
            pdf_urls = _discover_pdf_urls_selenium(page_url, year)

    if not pdf_urls:
        print("ERROR: Could not find any PDF links on the page.")
        return 0

    print(f"[{timestamp()}] Found {len(pdf_urls)} PDF URL(s).")

    json_dir.mkdir(parents=True, exist_ok=True)
    mapping_path.parent.mkdir(parents=True, exist_ok=True)

    extractor = AIContentExtractor(api_key=api_key, model_name=model)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    mapping_rows: list[dict] = []
    processed = 0
    skipped = 0
    failed = 0

    for pdf_url in pdf_urls:
        pdf_filename = _slugify_filename(pdf_url)
        company_id = slugify(pdf_filename.replace(".pdf", ""))

        # Strip year suffix from company_id if present (e.g. "_sociedade_2018")
        company_id = re.sub(r"_sociedade_\d{4}$", "", company_id)
        company_id = re.sub(r"_\d{4}$", "", company_id)

        json_path = json_dir / f"{Path(pdf_filename).stem}_members.json"

        # Skip if already extracted and valid
        if json_path.exists():
            try:
                import json as _json
                existing = _json.loads(json_path.read_text(encoding="utf-8"))
                members = existing.get("members", [])
                if members and not _members_have_quality_issues(members):
                    print(f"[{timestamp()}] SKIP (exists) {pdf_filename}")
                    skipped += 1
                    mapping_rows.append({"pdf_filename": pdf_filename, "company_id": company_id})
                    continue
            except Exception:
                pass

        print(f"[{timestamp()}] Fetching {pdf_filename} ...")
        try:
            resp = session.get(pdf_url, timeout=90)
            resp.raise_for_status()
            pdf_bytes = resp.content
            if len(pdf_bytes) < 500:
                print(f"  [warn] Response too small ({len(pdf_bytes)} bytes) — skipping")
                failed += 1
                continue
        except Exception as exc:
            print(f"  [error] fetch {pdf_url}: {exc}")
            failed += 1
            continue

        # Extract text from in-memory bytes
        try:
            text = extract_pdf_text_from_bytes(pdf_bytes)
        except Exception as exc:
            print(f"  [error] PDF parse {pdf_filename}: {exc}")
            failed += 1
            continue

        # Gemini extraction
        try:
            payload = extractor.extract_members_from_text(text, company_name=company_id)
            payload["pdf_filename"] = pdf_filename
            payload["company_id"] = company_id
            payload["source_url"] = pdf_url
            payload["model_name"] = model
            payload["created_at"] = timestamp()
            save_json_output(Path(pdf_filename), payload, json_dir)
            n = len(payload.get("members", []))
            print(f"[{timestamp()}] OK {pdf_filename}  members={n}")
            processed += 1
        except Exception as exc:
            print(f"  [error] Gemini {pdf_filename}: {exc}")
            failed += 1

        mapping_rows.append({"pdf_filename": pdf_filename, "company_id": company_id})
        time.sleep(REQUEST_DELAY)

    # Write mapping CSV
    pd.DataFrame(mapping_rows).to_csv(mapping_path, index=False)
    print(f"\n[{timestamp()}] Mapping written: {mapping_path} ({len(mapping_rows)} rows)")
    print(f"Done. processed={processed}  skipped={skipped}  failed={failed}")
    return processed + skipped


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream PDFs from cgov.pt: fetch in memory, extract board members, save JSON only"
    )
    parser.add_argument("--year", type=int, required=True,
                        help="Year to process (e.g. 2018, 2019, ..., 2023)")
    parser.add_argument("--json-dir", default=None,
                        help="Where to save JSON files. Default: E:\\Sociedade_dados\\{year}\\json_members")
    parser.add_argument("--api-key", default=_load_env_api_key())
    parser.add_argument("--model", default="gemini-2.5-pro")
    parser.add_argument("--selenium", action="store_true",
                        help="Force Selenium even if requests succeeds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Missing Gemini API key. Set GEMINI_API_KEY in .env or pass --api-key.")

    from board_pipeline import get_year_paths
    paths = get_year_paths(args.year)
    json_dir = Path(args.json_dir) if args.json_dir else paths["json_dir"]
    mapping_path = paths["mapping"]

    print(f"=== Stream Extract | year={args.year} | json={json_dir} ===")
    count = stream_extract(
        year=args.year,
        json_dir=json_dir,
        mapping_path=mapping_path,
        api_key=args.api_key,
        model=args.model,
        force_selenium=args.selenium,
    )
    return 0 if count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
