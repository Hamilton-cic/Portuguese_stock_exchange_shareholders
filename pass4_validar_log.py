"""Validate the board extraction log and print a compact summary.

Pass --year YYYY to validate a specific year's log instead of the 2024 default.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from board_pipeline import get_year_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate board extraction log")
    parser.add_argument("--year", type=int, default=None, help="Year to validate (e.g. 2018). Omit for 2024 defaults.")
    parser.add_argument("--log", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_year_paths(args.year)
    log_path = Path(args.log) if args.log else paths["log"]
    if not log_path.exists():
        raise SystemExit(f"Log not found: {log_path}")

    log = pd.read_csv(log_path)
    required = {"pdf_filename", "members_found", "status", "new_nodes", "new_edges"}
    missing = sorted(required - set(log.columns))
    if missing:
        raise SystemExit(f"Log is missing expected columns: {', '.join(missing)}")

    pdf_summary = log.sort_values(["members_found", "pdf_filename"], ascending=[False, True]).reset_index(drop=True)

    total_pdfs = len(pdf_summary)
    success = int((pdf_summary["status"] == "ok").sum())
    zero_members = pdf_summary[pdf_summary["members_found"] == 0]
    large_counts = pdf_summary[pdf_summary["members_found"] > 20]
    new_nodes = int(pdf_summary["new_nodes"].sum())
    new_edges = int(pdf_summary["new_edges"].sum())

    print(f"log={log_path}")
    print(f"rows={len(log)}")
    print(f"pdfs={total_pdfs}")
    print(f"success={success}")
    print(f"zero_members={len(zero_members)}")
    print(f"new_nodes={new_nodes}")
    print(f"new_edges={new_edges}")

    if not large_counts.empty:
        print("large_member_counts:")
        print(large_counts[["pdf_filename", "company_id", "members_found"]].to_string(index=False))

    if not zero_members.empty:
        print("zero_member_pdfs:")
        print(zero_members[["pdf_filename", "company_id"]].to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())