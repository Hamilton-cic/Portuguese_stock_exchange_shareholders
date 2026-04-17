"""Generate the pdf_company_mapping.csv draft in E:\Sociedade_dados."""

from __future__ import annotations

import argparse
from pathlib import Path

from board_pipeline import DEFAULT_DATASET_PATH, DEFAULT_PDF_DIR, DEFAULT_MAPPING_PATH, create_mapping_from_pdfs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate PDF -> company mapping")
    parser.add_argument("--pdf-dir", default=str(DEFAULT_PDF_DIR))
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--output", default=str(DEFAULT_MAPPING_PATH))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = create_mapping_from_pdfs(
        pdf_dir=Path(args.pdf_dir),
        dataset_path=Path(args.dataset),
        output_path=Path(args.output),
    )
    print(f"Mapping written to {args.output} ({len(output)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
