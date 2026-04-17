"""Run the complete board extraction pipeline with dependency management."""

from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path


def ensure_package(package_name: str, import_name: str | None = None) -> bool:
    """Install a package if not already present."""
    import_name = import_name or package_name.split("[")[0]
    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "-q"])
        return True


def load_env_file(project_dir: Path) -> dict[str, str]:
    """Load simple KEY=VALUE pairs from .env into a subprocess environment."""
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


def main() -> int:
    print("[0] Checking dependencies...")
    ensure_package("pdfplumber")
    ensure_package("pandas")
    ensure_package("google-genai", "google.genai")
    print("[0] Dependencies OK\n")

    project_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_dir))
    subprocess_env = load_env_file(project_dir)

    print("[1] Running Passo 1 (TXT extraction)...")
    subprocess.check_call([sys.executable, str(project_dir / "pass1_extrair_txt.py")], env=subprocess_env)

    print("\n[2] Running Passo 2 (Gemini extraction)...")
    result = subprocess.call([sys.executable, str(project_dir / "pass2_gemini_extrair_nomes.py")], env=subprocess_env)
    if result != 0:
        print("WARNING: Passo 2 failed or was skipped. Check for API key issues.")
        return result

    print("\n[3] Running Passo 3 (Dataset upsert)...")
    subprocess.check_call([sys.executable, str(project_dir / "pass3_atualizar_datasets.py")], env=subprocess_env)

    print("\n[4] Running Passo 4 (Validation)...")
    subprocess.check_call([sys.executable, str(project_dir / "pass4_validar_log.py")], env=subprocess_env)

    print("\n=== Pipeline Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
