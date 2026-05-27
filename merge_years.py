"""Merge per-year dataset/edges files into combined dataset.csv and edges.csv.

Each year's dataset_{year}.csv and edges_{year}.csv (produced by running
pass3 with --year) is merged into a single combined file.  A ``year`` column
is added to edges so temporal analysis is possible.

Usage:
    python merge_years.py                         # merge all available years
    python merge_years.py --years 2018 2019 2020  # explicit year list
    python merge_years.py --out-dataset combined_dataset.csv --out-edges combined_edges.csv

Output files default to the project directory:
    dataset_all.csv   -- all company + person nodes, deduplicated
    edges_all.csv     -- all edges with an added ``year`` column
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
ALL_YEARS = list(range(2018, 2025))  # 2018..2024 inclusive


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge per-year datasets into combined files")
    parser.add_argument(
        "--years", nargs="+", type=int, default=None,
        help="Years to include. Default: all available (2018-2024)."
    )
    parser.add_argument(
        "--out-dataset", default=str(PROJECT_DIR / "dataset_all.csv"),
        help="Output path for merged dataset (default: dataset_all.csv)"
    )
    parser.add_argument(
        "--out-edges", default=str(PROJECT_DIR / "edges_all.csv"),
        help="Output path for merged edges (default: edges_all.csv)"
    )
    return parser.parse_args()


def load_year(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load dataset_{year}.csv and edges_{year}.csv; return (nodes, edges)."""
    # 2024 uses the legacy filenames dataset.csv / edges.csv
    if year == 2024:
        ds_path = PROJECT_DIR / "dataset.csv"
        ed_path = PROJECT_DIR / "edges.csv"
    else:
        ds_path = PROJECT_DIR / f"dataset_{year}.csv"
        ed_path = PROJECT_DIR / f"edges_{year}.csv"

    if not ds_path.exists():
        return pd.DataFrame(), pd.DataFrame()

    nodes = pd.read_csv(ds_path)
    edges = pd.read_csv(ed_path) if ed_path.exists() else pd.DataFrame(columns=["source", "target", "weight"])
    return nodes, edges


def main() -> int:
    args = parse_args()
    years = sorted(args.years or ALL_YEARS)

    all_nodes: list[pd.DataFrame] = []
    all_edges: list[pd.DataFrame] = []
    found_years: list[int] = []

    for year in years:
        nodes, edges = load_year(year)
        if nodes.empty:
            print(f"[{year}] No dataset found — skipping.")
            continue
        found_years.append(year)
        all_nodes.append(nodes)
        edges = edges.copy()
        edges["year"] = year
        all_edges.append(edges)
        print(f"[{year}] nodes={len(nodes)}  edges={len(edges)}")

    if not found_years:
        print("No year data found. Run pass3 --year YYYY for each year first.")
        return 1

    merged_nodes = (
        pd.concat(all_nodes, ignore_index=True)
        .drop_duplicates(subset=["id"], keep="first")
        .reset_index(drop=True)
    )
    merged_edges = (
        pd.concat(all_edges, ignore_index=True)
        .drop_duplicates(subset=["source", "target", "year"], keep="first")
        .reset_index(drop=True)
    )

    out_ds = Path(args.out_dataset)
    out_ed = Path(args.out_edges)
    merged_nodes.to_csv(out_ds, index=False)
    merged_edges.to_csv(out_ed, index=False)

    print()
    print(f"=== Merged {len(found_years)} years: {found_years} ===")
    print(f"dataset_all: {out_ds}  ({len(merged_nodes)} nodes)")
    print(f"edges_all:   {out_ed}  ({len(merged_edges)} edges)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
