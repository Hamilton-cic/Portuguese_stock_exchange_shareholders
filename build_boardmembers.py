"""Build boardmembers_YYYY.csv files and dataset_2024.csv.

What this script does:
1. Converts each year dataset (2018-2023) into boardmembers_YYYY.csv
   with columns: name, company
2. Creates dataset_2024.csv from edges.csv (board-member edges, weight < 1)
   with the same format: name, company
3. Updates the Fidelidade JSON with full member names
4. Adds Nuno Terras Marques to the Martifer JSON
5. Creates JSON files for: Champalimaud, BPI, Banco Big, Cerealis,
   BA Glass, Visabeira, Simoldes, Santander
6. Appends all new companies to dataset_2024.csv
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent
JSON_DIR = PROJECT / "json_members"

# ---------------------------------------------------------------------------
# New / updated member data
# ---------------------------------------------------------------------------

NEW_COMPANIES: dict[str, dict] = {

    "fidelidade": {
        "label": "Fidelidade",
        "json_file": "Fidelidade_sociedade_2024_members.json",
        "mode": "replace",  # replace all members (current ones are abbreviated)
        "members": [
            "Jorge Manuel Baptista Magalhães Correia",
            "Eduardo José Stock da Cunha",
            "Carlos António Torroaes Albuquerque",
            "Lingjiang Xu",
            "Rogério Miguel Antunes Campos Henriques",
            "António Manuel Marques de Sousa Noronha",
            "Wai Lam William Mak",
            "André Simões Cardoso",
            "Hui Chen",
            "Juan Ignacio Arsuaga Serrats",
            "Miguel Barroso Abecasis",
        ],
    },

    "martifer": {
        "label": "Martifer",
        "json_file": "martifer_sgps_s_a_sociedade_2024_members.json",
        "mode": "add",  # add only missing members
        "members": [
            "Nuno Miguel Rodrigues Terras Marques",
        ],
    },

    "grupo_champalimaud": {
        "label": "Grupo Champalimaud",
        "json_file": "grupo_champalimaud_sociedade_2024_members.json",
        "mode": "create",
        "members": [
            "Manuel Carlos de Mello Champalimaud",
            "Duarte Palma Leal Champalimaud",
            "Tomás Palma Leal Champalimaud",
            "Ana Palma Leal Champalimaud",
            "José Gonçalo Ferreira Maury",
            "Mário Silva Santos",
            "Teresa Abecasis",
        ],
    },

    "bpi": {
        "label": "BPI",
        "json_file": "bpi_sociedade_2024_members.json",
        "mode": "create",
        "members": [
            "Fernando Ulrich",
            "Cristina Rios de Amorim Baptista",
            "Afonso Fuzeta Eça",
            "Ana Rosas Oliveira",
            "António Bernardo Aranha da Gama Lobo Xavier",
            "Diogo Sousa Louro",
            "Maria de Fátima Henriques da Silva Barros",
            "Francisco Artur Matos",
            "Gonzalo Gortázar Rotaeche",
            "Inês Valadas",
            "Javier Pano Riera",
            "Joana Freitas",
            "João Pedro Oliveira e Costa",
            "Natividad Capella",
            "Susana Trigo Cabral",
        ],
    },

    "banco_big": {
        "label": "Banco Big",
        "json_file": "banco_big_sociedade_2024_members.json",
        "mode": "create",
        "members": [
            "Carlos Rodrigues",
            "José Galamba de Oliveira",
            "Teresa Cardoso de Menezes",
            "Mário Bolota",
            "Ana Rita Gil",
            "João Henrique",
            "Vitor Luís",
            "Sara Carbonell",
            "Carlos Pompeu Ramalhão Fortunato",
            "Maria João Ricou",
            "Ricardo Dias Carneiro e Gomes de Pinho",
            "Maria Aline Bastos Moreira Veloso de Almeida",
            "Pedro Rogério Barata do Ouro Lameira",
            "Jorge Manuel Jacob Miguel Tainha",
            "Vitor João Tavares Maia",
        ],
    },

    "cerealis": {
        "label": "Cerealis",
        "json_file": "cerealis_sociedade_2024_members.json",
        "mode": "create",
        "members": [
            "Carlos António Rocha Moreira da Silva",
            "Pedro Miranda Moreira da Silva",
            "Francisco José Mestre Mira da Silva Domingues",
            "Frederico José Ortigão da Silva Pinto",
            "Maria Alves Machado de Sousa de Macedo Estarreja",
            "Rita Mestre Mira da Silva Domingues",
            "Rui Manuel de Amorim Silva e Sousa",
        ],
    },

    "ba_glass": {
        "label": "BA Glass",
        "json_file": "ba_glass_sociedade_2024_members.json",
        "mode": "create",
        "members": [
            "Paulo Azevedo",
            "Jacqueline Hoogerbrugge",
            "Pedro Miranda Moreira da Silva",
            "Tiago Moreira da Silva",
            "James Thompson",
            "Rita Mestre Mira da Silva Domingues",
            "António Bernardo Aranha da Gama Lobo Xavier",
            "Jorge Alexandre Ferreira",
            "Rui Correia",
            "Francisco José Mestre Mira da Silva Domingues",
            "Marco Marques",
            "Federico Bisio",
            "Pedro Mc Carthy da Cunha",
            "Isabel Monteiro",
            "Reinaldo Coelho",
            "Iva Rodrigues Dias",
            "Sylwia Mistrzak",
            "Jakub Kaczmarek",
            "Joana Osório",
        ],
    },

    "visabeira": {
        "label": "Visabeira",
        "json_file": "visabeira_sociedade_2024_members.json",
        "mode": "create",
        "members": [
            "Nuno Miguel Rodrigues Terras Marques",
            "Fernando Daniel Leocadio Campos Nunes",
            "Alexandra da Conceição Lopes",
            "Luís Alexandre de Almeida Ferreira",
        ],
    },

    "simoldes": {
        "label": "Simoldes",
        "json_file": "simoldes_sociedade_2024_members.json",
        "mode": "create",
        "members": [
            "António da Silva Rodrigues",
            "Rui Paulo Rodrigues",
        ],
    },

    "santander": {
        "label": "Santander",
        "json_file": "santander_sociedade_2024_members.json",
        "mode": "create",
        "members": [
            "José Carlos Brito Sítima",
            "Pedro Aires Coruche Castro e Almeida",
            "Amílcar da Silva Lourenço",
            "Ana Isabel Abranches Pereira de Carvalho Morais",
            "Cristina Alvarez Alvarez",
            "Daniel Abel Monteiro Palhares Traça",
            "Isabel Cristina da Silva Guerreiro",
            "João Pedro Cabral Tavares",
            "Manuel António Amaral Franco Preto",
            "Manuel Maria de Olazábal Albuquerque",
            "Maria Manuela Machado Costa Farelo Ataíde Marques",
            "Miguel Belo de Carvalho",
            "Remedios Ruiz Maciá",
            "Ricardo Lopes da Costa Jorge",
        ],
    },
}


# ---------------------------------------------------------------------------
# Step 1 — Convert year datasets (2018-2023) to name/company format
# ---------------------------------------------------------------------------

def build_year_boardmembers(year: int) -> pd.DataFrame:
    """Return a name/company DataFrame for board members in a given year."""
    ds_path = PROJECT / f"dataset_{year}.csv"
    ed_path = PROJECT / f"edges_{year}.csv"
    if not ds_path.exists() or not ed_path.exists():
        return pd.DataFrame(columns=["name", "company"])

    nodes = pd.read_csv(ds_path)
    edges = pd.read_csv(ed_path)

    # Board member edges: weight < 1
    board_edges = edges[edges["weight"].astype(float) < 1.0].copy()

    # Build id → label lookups
    id_to_label = dict(zip(nodes["id"].astype(str), nodes["label"].astype(str)))

    rows = []
    for _, row in board_edges.iterrows():
        person_label = id_to_label.get(str(row["source"]), str(row["source"]))
        company_label = id_to_label.get(str(row["target"]), str(row["target"]))
        rows.append({"name": person_label, "company": company_label})

    return pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)


def step1_year_csvs():
    print("=== Step 1: Building boardmembers_YYYY.csv for 2018-2023 ===")
    for year in range(2018, 2024):
        df = build_year_boardmembers(year)
        out = PROJECT / f"boardmembers_{year}.csv"
        df.to_csv(out, index=False)
        print(f"  boardmembers_{year}.csv  ({len(df)} rows)")


# ---------------------------------------------------------------------------
# Step 2 — Create dataset_2024.csv from edges.csv (board-member edges)
# ---------------------------------------------------------------------------

def step2_dataset_2024() -> pd.DataFrame:
    print("\n=== Step 2: Creating dataset_2024.csv from edges.csv ===")
    nodes = pd.read_csv(PROJECT / "dataset.csv")
    edges = pd.read_csv(PROJECT / "edges.csv")

    board_edges = edges[edges["weight"].astype(float) < 1.0].copy()
    id_to_label = dict(zip(nodes["id"].astype(str), nodes["label"].astype(str)))

    rows = []
    for _, row in board_edges.iterrows():
        person_label = id_to_label.get(str(row["source"]), str(row["source"]))
        company_label = id_to_label.get(str(row["target"]), str(row["target"]))
        rows.append({"name": person_label, "company": company_label})

    df = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    print(f"  {len(df)} board-member rows from edges.csv")
    return df


# ---------------------------------------------------------------------------
# Step 3 — Update / create JSON files
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def step3_json_files():
    print("\n=== Step 3: Updating / creating JSON files ===")
    JSON_DIR.mkdir(parents=True, exist_ok=True)

    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    for company_id, info in NEW_COMPANIES.items():
        json_path = JSON_DIR / info["json_file"]
        mode = info["mode"]
        new_members = info["members"]

        if mode == "create":
            payload = {
                "company": company_id,
                "members": new_members,
                "notes": "Manually curated.",
                "pdf_filename": info["json_file"].replace("_members.json", ".pdf"),
                "company_id": company_id,
                "source_txt": "",
                "model_name": "manual",
                "created_at": ts,
            }
            _save_json(json_path, payload)
            print(f"  CREATED  {json_path.name}  ({len(new_members)} members)")

        elif mode == "replace":
            payload = _load_json(json_path)
            payload["members"] = new_members
            payload["notes"] = (payload.get("notes") or "") + " Members updated with full names."
            _save_json(json_path, payload)
            print(f"  REPLACED {json_path.name}  ({len(new_members)} members)")

        elif mode == "add":
            payload = _load_json(json_path)
            existing = [m.strip().lower() for m in (payload.get("members") or [])]
            added = []
            for name in new_members:
                if name.strip().lower() not in existing:
                    payload.setdefault("members", []).append(name)
                    added.append(name)
            if added:
                payload["notes"] = (payload.get("notes") or "") + f" Added: {', '.join(added)}."
                _save_json(json_path, payload)
                print(f"  UPDATED  {json_path.name}  +{len(added)} member(s): {added}")
            else:
                print(f"  SKIP     {json_path.name}  (no new members to add)")


# ---------------------------------------------------------------------------
# Step 4 — Append new companies to dataset_2024.csv
# ---------------------------------------------------------------------------

def step4_append_new_companies(df_2024: pd.DataFrame) -> pd.DataFrame:
    print("\n=== Step 4: Appending new companies to dataset_2024.csv ===")
    new_rows = []
    for company_id, info in NEW_COMPANIES.items():
        company_label = info["label"]
        for name in info["members"]:
            new_rows.append({"name": name, "company": company_label})

    df_new = pd.DataFrame(new_rows)

    # Combine and deduplicate on (name, company) — case-insensitive
    combined = pd.concat([df_2024, df_new], ignore_index=True)
    combined["_key"] = combined["name"].str.strip().str.lower() + "|" + combined["company"].str.strip().str.lower()
    combined = combined.drop_duplicates(subset=["_key"]).drop(columns=["_key"])
    combined = combined.reset_index(drop=True)
    print(f"  Total rows in dataset_2024.csv: {len(combined)}")
    return combined


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    step1_year_csvs()
    df_2024 = step2_dataset_2024()
    step3_json_files()
    df_2024 = step4_append_new_companies(df_2024)

    out = PROJECT / "boardmembers_2024.csv"
    df_2024.to_csv(out, index=False)
    print(f"\nSaved: {out}")
    print("\nAll done.")


if __name__ == "__main__":
    main()
