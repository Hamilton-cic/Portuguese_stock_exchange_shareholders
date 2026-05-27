"""Update dataset.csv and edges.csv from Gemini JSON outputs.

Strategy (full rebuild of board-member data):
1. Load existing dataset and edges.
2. Drop all person nodes and their edges — they will be rebuilt from scratch.
3. Read every *_members.json file; skip files with quality issues (> 10 % bad
   entries) and print a warning so they can be reprocessed with pass2.
4. For each accepted JSON, clean each member name and upsert into dataset /
   edges, preserving all company nodes and non-board edges unchanged.

Pass --year YYYY to write year-specific output files (dataset_YYYY.csv /
edges_YYYY.csv) instead of the shared 2024 defaults.  Year-specific runs
start from scratch rather than rebuilding over existing data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from board_pipeline import (
    _clean_member_name,
    _members_have_quality_issues,
    canonical_member_id,
    canonical_weight,
    ensure_company_nodes,
    get_year_paths,
    load_dataset,
    load_edges,
    load_json_members,
    read_mapping,
    slugify,
    timestamp,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild board members in dataset/edges")
    parser.add_argument("--year", type=int, default=None, help="Year to process (e.g. 2018). Omit for 2024 defaults.")
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--edges", default=None)
    parser.add_argument("--json-dir", default=None)
    parser.add_argument("--mapping", default=None)
    parser.add_argument("--log", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_year_paths(args.year)
    dataset_path = Path(args.dataset) if args.dataset else paths["dataset"]
    edges_path = Path(args.edges) if args.edges else paths["edges"]
    json_dir = Path(args.json_dir) if args.json_dir else paths["json_dir"]
    mapping_path = Path(args.mapping) if args.mapping else paths["mapping"]
    log_path = Path(args.log) if args.log else paths["log"]

    mapping = read_mapping(mapping_path)
    mapping_by_pdf = {row.pdf_filename: row.company_id for row in mapping.itertuples(index=False)}

    if args.year is not None:
        # Year-specific run: build from scratch (no existing board data to preserve)
        dataset = ensure_company_nodes(pd.DataFrame(columns=["id", "label", "type"]))
        edges = pd.DataFrame(columns=["source", "target", "weight"])
    else:
        dataset = ensure_company_nodes(load_dataset(dataset_path))
        edges = load_edges(edges_path)

    # ------------------------------------------------------------------
    # Step 1 — strip board-member data so we rebuild from scratch with
    # only clean JSON data.
    #
    # Board-member edges were created by canonical_weight() which returns
    # values in [0.1, 0.5].  Shareholder / ownership edges have weights
    # >= 1 (they are percentages).  We remove only the board-member edges
    # and the person nodes that exclusively came from board extraction.
    # ------------------------------------------------------------------
    board_edge_mask = edges["weight"].astype(float) < 1.0
    board_sources = set(edges.loc[board_edge_mask, "source"].astype(str))

    # Remove board-member edges; keep shareholder edges intact
    edges = edges[~board_edge_mask].copy()

    # Remove person nodes that are not referenced by any remaining edge
    # (i.e., they only existed as board members, not as shareholders)
    remaining_sources = set(edges["source"].astype(str)) | set(edges["target"].astype(str))
    person_ids = set(dataset.loc[dataset["type"].astype(str) == "person", "id"].astype(str))
    board_only_persons = person_ids - remaining_sources
    dataset = dataset[~dataset["id"].astype(str).isin(board_only_persons)].copy()

    print(
        f"[{timestamp()}] Removed {len(board_only_persons)} stale person nodes "
        f"and {board_edge_mask.sum()} board-member edges. Rebuilding from JSONs..."
    )

    # ------------------------------------------------------------------
    # Step 2 — iterate JSON files; validate quality before accepting.
    # ------------------------------------------------------------------
    company_lookup = set(dataset["id"].astype(str))
    existing_nodes: set[str] = set(dataset["id"].astype(str))
    existing_edges: set[tuple[str, str]] = set(
        zip(edges["source"].astype(str), edges["target"].astype(str))
    )

    node_rows: list[dict] = []
    edge_rows: list[dict] = []
    log_rows: list[dict] = []

    accepted = 0
    skipped_quality = 0

    for json_path in load_json_members(json_dir):
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        pdf_filename = str(
            payload.get("pdf_filename") or json_path.name.replace("_members.json", ".pdf")
        )
        company_label = str(payload.get("company") or pdf_filename.replace(".pdf", "")).strip()
        company_id = str(
            payload.get("company_id") or mapping_by_pdf.get(pdf_filename, "")
        ).strip()
        if not company_id:
            company_id = slugify(company_label)

        raw_members: list = payload.get("members", []) or []
        if not isinstance(raw_members, list):
            raw_members = []

        # Quality gate — skip files with too many non-name entries
        if _members_have_quality_issues(raw_members):
            bad = [m for m in raw_members if _clean_member_name(str(m).strip()) is None]
            print(
                f"[{timestamp()}] SKIP (quality) {json_path.name}: "
                f"{len(bad)}/{len(raw_members)} entradas inválidas "
                f"-- corre pass2 para reprocessar."
            )
            skipped_quality += 1
            log_rows.append({
                "timestamp": timestamp(),
                "pdf_filename": pdf_filename,
                "company_id": company_id,
                "members_found": len(raw_members),
                "new_nodes": 0,
                "new_edges": 0,
                "status": "skipped_quality",
            })
            continue

        accepted += 1

        # Ensure company node exists
        if company_id and company_id not in company_lookup:
            node_rows.append({"id": company_id, "label": company_label, "type": "company"})
            company_lookup.add(company_id)

        # Clean members and upsert nodes / edges
        clean_members: list[str] = []
        seen_in_file: set[str] = set()
        for raw in raw_members:
            name = _clean_member_name(str(raw).strip())
            if not name:
                continue
            member_id = canonical_member_id(name)
            if not member_id or member_id in seen_in_file:
                continue
            seen_in_file.add(member_id)
            clean_members.append(name)

        pdf_new_nodes = 0
        pdf_new_edges = 0

        for name in clean_members:
            member_id = canonical_member_id(name)
            if member_id not in existing_nodes:
                node_rows.append({"id": member_id, "label": name, "type": "person"})
                existing_nodes.add(member_id)
                pdf_new_nodes += 1

            if company_id:
                edge_key = (member_id, company_id)
                if edge_key not in existing_edges:
                    edge_rows.append({
                        "source": member_id,
                        "target": company_id,
                        "weight": canonical_weight(),
                    })
                    existing_edges.add(edge_key)
                    pdf_new_edges += 1

        log_rows.append({
            "timestamp": timestamp(),
            "pdf_filename": pdf_filename,
            "company_id": company_id,
            "members_found": len(clean_members),
            "new_nodes": pdf_new_nodes,
            "new_edges": pdf_new_edges,
            "status": "ok" if clean_members else "empty",
        })
        print(
            f"[{timestamp()}] OK {json_path.name}: "
            f"{len(clean_members)} membros | +{pdf_new_nodes} nós | +{pdf_new_edges} arestas"
        )

    # ------------------------------------------------------------------
    # Step 3 — merge and save
    # ------------------------------------------------------------------
    if node_rows:
        dataset = pd.concat([dataset, pd.DataFrame(node_rows)], ignore_index=True)
    dataset = dataset.drop_duplicates(subset=["id"], keep="first").reset_index(drop=True)

    if edge_rows:
        edges = pd.concat([edges, pd.DataFrame(edge_rows)], ignore_index=True)
    edges = edges.drop_duplicates(subset=["source", "target"], keep="first").reset_index(drop=True)

    dataset.to_csv(dataset_path, index=False)
    edges.to_csv(edges_path, index=False)
    pd.DataFrame(log_rows).to_csv(log_path, index=False)

    person_final = int((dataset["type"] == "person").sum())
    company_final = int((dataset["type"] == "company").sum())

    print()
    print(f"=== Resumo ===")
    print(f"JSONs aceites:  {accepted}")
    print(f"JSONs ignorados (qualidade): {skipped_quality}  (corre pass2 para corrigir)")
    print(f"dataset:     {dataset_path} ({company_final} empresas, {person_final} pessoas)")
    print(f"edges:       {edges_path} ({len(edges)} arestas)")
    print(f"log:         {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
