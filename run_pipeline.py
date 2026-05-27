"""Run the complete board extraction pipeline.

Two modes:

  Local-file mode (2024 defaults — existing behaviour):
      python run_pipeline.py
      Runs: pass0 -> pass1 -> pass2 -> pass3 -> pass4
      PDFs must already be present in E:\\Sociedade_dados

  Streaming mode (for 2018-2023 from cgov.pt):
      python run_pipeline.py --year 2018
      Runs: download_pdfs_cgov.py -> pass3 -> pass4
      Fetches PDFs from cgov.pt directly in memory — no disk space needed.
      Only JSON results and CSVs are saved.

After processing all years, merge into one combined dataset:
    python merge_years.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import os
from pathlib import Path


def ensure_package(package_name: str, import_name: str | None = None) -> bool:
    import_name = import_name or package_name.split("[")[0]
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "-q"])
        return True


def load_env_file(project_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env_path = project_dir / ".env"
    if not env_path.exists():
        return env
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def run(cmd: list[str], env: dict) -> int:
    return subprocess.call(cmd, env=env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full board extraction pipeline")
    parser.add_argument(
        "--year", type=int, default=None,
        help="Year to process via cgov.pt streaming (e.g. 2018). Omit to run the 2024 local-file pipeline."
    )
    parser.add_argument(
        "--selenium", action="store_true",
        help="Force Selenium for PDF URL discovery (streaming mode only)."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("[0] Checking dependencies...")
    ensure_package("pdfplumber")
    ensure_package("pandas")
    ensure_package("google-genai", "google.genai")
    ensure_package("requests")
    ensure_package("beautifulsoup4", "bs4")
    print("[0] Dependencies OK\n")

    project_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_dir))
    subprocess_env = load_env_file(project_dir)

    if args.year:
        # ----------------------------------------------------------------
        # Streaming mode: fetch PDFs from cgov.pt in memory, extract
        # board members, write JSONs — then pass3 + pass4.
        # ----------------------------------------------------------------
        year_label = f"year={args.year}"
        print(f"=== Streaming pipeline | {year_label} ===\n")

        stream_cmd = [
            sys.executable,
            str(project_dir / "download_pdfs_cgov.py"),
            "--year", str(args.year),
        ]
        if args.selenium:
            stream_cmd.append("--selenium")

        print(f"[1/3] Stream extract (cgov.pt -> memory -> Gemini -> JSON)...")
        result = run(stream_cmd, subprocess_env)
        if result != 0:
            print("WARNING: Streaming extraction failed or found no PDFs.")
            return result

        print(f"\n[2/3] Pass 3 — build dataset_{args.year}.csv + edges_{args.year}.csv...")
        subprocess.check_call(
            [sys.executable, str(project_dir / "pass3_atualizar_datasets.py"), "--year", str(args.year)],
            env=subprocess_env,
        )

        print(f"\n[3/3] Pass 4 — validate log...")
        subprocess.check_call(
            [sys.executable, str(project_dir / "pass4_validar_log.py"), "--year", str(args.year)],
            env=subprocess_env,
        )

        print(f"\n=== Done | {year_label} ===")
        print(f"Output: dataset_{args.year}.csv  edges_{args.year}.csv")
        print("Run merge_years.py to combine all years into dataset_all.csv / edges_all.csv")

    else:
        # ----------------------------------------------------------------
        # Local-file mode: 2024 pipeline using PDFs already on disk.
        # ----------------------------------------------------------------
        print("=== Local-file pipeline (2024 defaults) ===\n")

        print("[1/4] Pass 0 — generate mapping...")
        subprocess.check_call(
            [sys.executable, str(project_dir / "pass0_gerar_mapping.py")],
            env=subprocess_env,
        )

        print("\n[2/4] Pass 1 — extract TXT from PDFs...")
        subprocess.check_call(
            [sys.executable, str(project_dir / "pass1_extrair_txt.py")],
            env=subprocess_env,
        )

        print("\n[3/4] Pass 2 — Gemini extraction...")
        result = run(
            [sys.executable, str(project_dir / "pass2_gemini_extrair_nomes.py")],
            subprocess_env,
        )
        if result != 0:
            print("WARNING: Pass 2 failed. Check GEMINI_API_KEY.")
            return result

        print("\n[4/4] Pass 3 — build dataset.csv + edges.csv...")
        subprocess.check_call(
            [sys.executable, str(project_dir / "pass3_atualizar_datasets.py")],
            env=subprocess_env,
        )

        print("\n[5/5] Pass 4 — validate log...")
        subprocess.check_call(
            [sys.executable, str(project_dir / "pass4_validar_log.py")],
            env=subprocess_env,
        )

        print("\n=== Pipeline Complete (2024) ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
