"""Generate the pdf_company_mapping.csv draft in E:\Sociedade_dados.

Pass --year YYYY to process a specific year's subdirectory instead of the
2024 defaults (e.g. E:\\Sociedade_dados\\2018\\pdfs).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from board_pipeline import DEFAULT_DATASET_PATH, DEFAULT_PDF_DIR, DEFAULT_MAPPING_PATH, create_mapping_from_pdfs, get_year_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate PDF -> company mapping")
    parser.add_argument("--year", type=int, default=None, help="Year to process (e.g. 2018). Omit for 2024 defaults.")
    parser.add_argument("--pdf-dir", default=None)
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_year_paths(args.year)
    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else paths["pdf_dir"]
    output_path = Path(args.output) if args.output else paths["mapping"]

    output = create_mapping_from_pdfs(
        pdf_dir=pdf_dir,
        dataset_path=Path(args.dataset),
        output_path=output_path,
    )
    print(f"Mapping written to {output_path} ({len(output)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
