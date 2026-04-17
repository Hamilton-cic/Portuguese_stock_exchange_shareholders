"""Use Gemini Flash to extract Conselho de Administração members from TXT files."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from board_pipeline import (
    DEFAULT_JSON_DIR,
    DEFAULT_PDF_DIR,
    DEFAULT_TXT_DIR,
    AIContentExtractor,
    load_dataset,
    load_json_members,
    read_mapping,
    save_json_output,
    timestamp,
    _members_have_quality_issues,
)


def load_env_api_key() -> str:
    """Read GEMINI_API_KEY from .env if it is not already in the environment."""
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract board members with Gemini")
    parser.add_argument("--txt-dir", default=str(DEFAULT_TXT_DIR))
    parser.add_argument("--json-dir", default=str(DEFAULT_JSON_DIR))
    parser.add_argument("--mapping", default=str(DEFAULT_PDF_DIR / "pdf_company_mapping.csv"))
    parser.add_argument("--api-key", default=load_env_api_key())
    parser.add_argument("--model", default="gemini-2.5-pro")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Missing Gemini API key. Set GEMINI_API_KEY or pass --api-key.")

    txt_dir = Path(args.txt_dir)
    json_dir = Path(args.json_dir)
    mapping = read_mapping(Path(args.mapping))
    dataset = load_dataset()
    company_ids = set(dataset["id"].astype(str))

    extractor = AIContentExtractor(api_key=args.api_key, model_name=args.model)

    mapping_by_pdf = {row.pdf_filename: row.company_id for row in mapping.itertuples(index=False)}
    processed = 0
    skipped = 0
    failed = 0

    for txt_path in sorted(txt_dir.glob("*.txt")):
        json_path = json_dir / f"{txt_path.stem}_members.json"
        if json_path.exists():
            try:
                existing_payload = json.loads(json_path.read_text(encoding="utf-8"))
                existing_members = existing_payload.get("members", [])
                if (
                    isinstance(existing_members, list)
                    and len(existing_members) > 0
                    and not _members_have_quality_issues(existing_members)
                ):
                    skipped += 1
                    continue
                if _members_have_quality_issues(existing_members):
                    print(f"[{timestamp()}] Reprocessing (quality issues): {json_path.name}")
            except Exception:
                pass

        pdf_filename = f"{txt_path.stem}.pdf"
        company_id = str(mapping_by_pdf.get(pdf_filename, "")).strip()
        company_label = company_id if company_id else txt_path.stem
        if company_id not in company_ids and company_id not in {"fidelidade", "grupo_jose_de_mello", "cuf", "luz_saude"}:
            company_label = txt_path.stem

        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        try:
            payload = extractor.extract_members_from_text(text, company_name=company_label)
            payload["pdf_filename"] = pdf_filename
            payload["company_id"] = company_id
            payload["source_txt"] = txt_path.name
            payload["model_name"] = args.model
            payload["created_at"] = timestamp()
            if not payload.get("members"):
                payload["notes"] = (payload.get("notes") or "").strip()
                payload["notes"] = (payload["notes"] + " Heuristic fallback returned no members.").strip()
            save_json_output(Path(pdf_filename), payload, json_dir)
            processed += 1
            print(f"[{timestamp()}] JSON saved: {json_path.name} members={len(payload.get('members', []))}")
        except Exception as exc:
            failed += 1
            print(f"[{timestamp()}] ERROR: {txt_path.name} -> {exc}")
        time.sleep(1)

    print(f"Done. processed={processed} skipped={skipped} failed={failed} output={json_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
