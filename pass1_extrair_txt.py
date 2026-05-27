"""Extract text and tables from each PDF into TXT files.

Pass --year YYYY to process a specific year's subdirectory instead of the
2024 defaults (e.g. E:\\Sociedade_dados\\2018\\pdfs).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from board_pipeline import DEFAULT_PDF_DIR, DEFAULT_TXT_DIR, extract_pdf_text, get_year_paths, save_text_output, timestamp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract PDF text into TXT files")
    parser.add_argument("--year", type=int, default=None, help="Year to process (e.g. 2018). Omit for 2024 defaults.")
    parser.add_argument("--pdf-dir", default=None)
    parser.add_argument("--output-dir", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_year_paths(args.year)
    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else paths["pdf_dir"]
    output_dir = Path(args.output_dir) if args.output_dir else paths["txt_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped = 0
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        out_path = output_dir / f"{pdf_path.stem}.txt"
        if out_path.exists():
            skipped += 1
            continue
        text = extract_pdf_text(pdf_path)
        save_text_output(pdf_path, text, output_dir)
        processed += 1
        print(f"[{timestamp()}] TXT saved: {out_path.name}")

    print(f"Done. processed={processed} skipped={skipped} output={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
