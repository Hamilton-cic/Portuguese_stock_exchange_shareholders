"""Download CGOV 2024 corporate governance PDFs.

Target page:
https://cgov.pt/governo-das-sociedades/relatorios-de-governo-das-sociedades/2024

Each report is saved as:
  <company_name_normalized>_sociedade_2024.pdf
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


PAGE_URL = "https://cgov.pt/governo-das-sociedades/relatorios-de-governo-das-sociedades/2024"
PDF_PATH_HINT = "/images/ficheiros/cgs-nacionais/2024/"


def normalize_company_name(name: str) -> str:
    """Create a filesystem-safe ASCII company token for file names."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().strip()
    ascii_text = re.sub(r"[^a-z0-9]+", "_", ascii_text)
    ascii_text = re.sub(r"_+", "_", ascii_text).strip("_")
    return ascii_text or "empresa"


def extract_links_from_html(html: str, base_url: str) -> list[tuple[str, str]]:
    """Extract (company_name, pdf_url) from static HTML."""
    soup = BeautifulSoup(html, "html.parser")
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href:
            continue

        absolute_url = urljoin(base_url, href)
        lowered = absolute_url.lower()
        if not lowered.endswith(".pdf"):
            continue
        if PDF_PATH_HINT not in absolute_url:
            continue

        company_name = " ".join(anchor.get_text(" ", strip=True).split())
        if not company_name:
            continue

        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        pairs.append((company_name, absolute_url))

    return pairs


def scrape_with_requests(
    session: requests.Session,
    url: str,
    timeout: int,
) -> list[tuple[str, str]]:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return extract_links_from_html(response.text, url)


def scrape_with_selenium(url: str) -> list[tuple[str, str]]:
    """Fallback for pages that require JavaScript rendering."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        from webdriver_manager.chrome import ChromeDriverManager
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Selenium fallback is unavailable. Install selenium and webdriver-manager."
        ) from exc

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        pairs: list[tuple[str, str]] = []
        seen: set[str] = set()

        for anchor in driver.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = (anchor.get_attribute("href") or "").strip()
            if not href:
                continue
            lowered = href.lower()
            if not lowered.endswith(".pdf"):
                continue
            if PDF_PATH_HINT not in href:
                continue

            company_name = " ".join((anchor.text or "").split())
            if not company_name:
                continue

            if href in seen:
                continue
            seen.add(href)
            pairs.append((company_name, href))

        return pairs
    finally:
        driver.quit()


def canonical_filename(company_name: str) -> str:
    return f"{normalize_company_name(company_name)}_sociedade_2024.pdf"


def unique_name_for_run(base_name: str, used_names: set[str]) -> str:
    """Return unique file name for duplicates that happen in the same execution."""
    lowered = base_name.lower()
    if lowered not in used_names:
        used_names.add(lowered)
        return base_name

    stem = base_name[:-4] if base_name.lower().endswith(".pdf") else base_name
    counter = 2
    while True:
        candidate = f"{stem}_{counter}.pdf"
        cand_lower = candidate.lower()
        if cand_lower not in used_names:
            used_names.add(cand_lower)
            return candidate
        counter += 1


def is_probably_pdf(content: bytes, content_type: str) -> bool:
    if content.startswith(b"%PDF"):
        return True
    return "pdf" in (content_type or "").lower()


def iter_downloads(
    pairs: Iterable[tuple[str, str]],
    output_dir: Path,
    session: requests.Session,
    timeout: int,
    force: bool,
) -> tuple[int, int, int]:
    """Download files. Returns (downloaded, skipped, failed)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    used_names: set[str] = set()

    for company_name, pdf_url in pairs:
        base_name = canonical_filename(company_name)
        canonical_path = output_dir / base_name

        if canonical_path.exists() and not force:
            print(f"[SKIP] {canonical_path.name} already exists")
            skipped += 1
            continue

        chosen_name = unique_name_for_run(base_name, used_names)
        target_path = output_dir / chosen_name

        if target_path.exists() and not force:
            print(f"[SKIP] {target_path.name} already exists")
            skipped += 1
            continue

        try:
            response = session.get(pdf_url, timeout=(10, timeout))
            response.raise_for_status()
            body = response.content
            if not is_probably_pdf(body[:1024], response.headers.get("Content-Type", "")):
                print(f"[FAIL] {company_name}: response does not look like PDF ({pdf_url})")
                failed += 1
                continue

            target_path.write_bytes(body)
            print(f"[OK]   {target_path.name}")
            downloaded += 1
        except Exception as exc:
            print(f"[FAIL] {company_name}: {exc}")
            failed += 1

    return downloaded, skipped, failed


def run(output: str, timeout: int, force: bool) -> int:
    output_dir = Path(output)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": PAGE_URL,
        }
    )

    try:
        pairs = scrape_with_requests(session, PAGE_URL, timeout=timeout)
        source = "requests"
    except Exception as exc:
        print(f"[WARN] requests scraping failed: {exc}")
        pairs = []
        source = "none"

    if not pairs:
        print("[INFO] Trying Selenium fallback...")
        try:
            pairs = scrape_with_selenium(PAGE_URL)
            source = "selenium"
        except Exception as exc:
            print(f"[ERROR] Selenium fallback failed: {exc}")
            return 1

    print(f"[INFO] Found {len(pairs)} PDF links (source={source})")
    downloaded, skipped, failed = iter_downloads(
        pairs=pairs,
        output_dir=output_dir,
        session=session,
        timeout=timeout,
        force=force,
    )

    print("\n=== Summary ===")
    print(f"Output folder : {output_dir}")
    print(f"Found links   : {len(pairs)}")
    print(f"Downloaded    : {downloaded}")
    print(f"Skipped       : {skipped}")
    print(f"Failed        : {failed}")
    return 0 if failed == 0 else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download CGOV 2024 reports as company_sociedade_2024.pdf"
    )
    parser.add_argument(
        "--output",
        default=r"E:\Sociedade_dados",
        help="Output directory (default: E:\\Sociedade_dados)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=45,
        help="HTTP timeout in seconds (default: 45)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files if present",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    sys.exit(run(output=arguments.output, timeout=arguments.timeout, force=arguments.force))