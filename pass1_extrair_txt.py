"""Extract text and tables from each PDF into TXT files."""

from __future__ import annotations

import argparse
from pathlib import Path

from board_pipeline import DEFAULT_PDF_DIR, DEFAULT_TXT_DIR, extract_pdf_text, save_text_output, timestamp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract PDF text into TXT files")
    parser.add_argument("--pdf-dir", default=str(DEFAULT_PDF_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_TXT_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_dir = Path(args.pdf_dir)
    output_dir = Path(args.output_dir)
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
