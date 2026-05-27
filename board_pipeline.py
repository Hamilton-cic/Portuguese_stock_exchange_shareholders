"""Shared helpers for extracting board members from PDF reports.

The pipeline is intentionally split into 4 steps:
1. PDF -> TXT
2. TXT -> JSON via Gemini Flash
3. JSON -> dataset.csv / edges.csv
4. Validate logs
"""

from __future__ import annotations

import csv
import json
import os
import random
import re
import time
import unicodedata
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import pdfplumber
from google import genai
from google.genai import types


DEFAULT_PDF_DIR = Path(r"E:\Sociedade_dados")
DEFAULT_TXT_DIR = DEFAULT_PDF_DIR / "txt_output"
DEFAULT_JSON_DIR = DEFAULT_PDF_DIR / "json_members"
DEFAULT_MAPPING_PATH = DEFAULT_PDF_DIR / "pdf_company_mapping.csv"
DEFAULT_LOG_PATH = DEFAULT_PDF_DIR / "board_extraction_log.csv"
DEFAULT_DATASET_PATH = Path(__file__).resolve().parent / "dataset.csv"
DEFAULT_EDGES_PATH = Path(__file__).resolve().parent / "edges.csv"


def get_year_paths(year: int | None) -> dict[str, Path]:
    """Return all file/directory paths for a given year.

    When year is None, returns the 2024 defaults (backward-compatible).
    When year is given (e.g. 2018), returns year-specific paths under
    E:\\Sociedade_dados\\{year}\\ so each year's data is isolated.
    """
    project_dir = Path(__file__).resolve().parent
    if year is None:
        return {
            "pdf_dir": DEFAULT_PDF_DIR,
            "txt_dir": DEFAULT_TXT_DIR,
            "json_dir": DEFAULT_JSON_DIR,
            "mapping": DEFAULT_MAPPING_PATH,
            "log": DEFAULT_LOG_PATH,
            "dataset": DEFAULT_DATASET_PATH,
            "edges": DEFAULT_EDGES_PATH,
        }
    year_dir = DEFAULT_PDF_DIR / str(year)
    return {
        "pdf_dir": year_dir / "pdfs",
        "txt_dir": year_dir / "txt_output",
        "json_dir": year_dir / "json_members",
        "mapping": year_dir / "pdf_company_mapping.csv",
        "log": year_dir / "board_extraction_log.csv",
        "dataset": project_dir / f"dataset_{year}.csv",
        "edges": project_dir / f"edges_{year}.csv",
    }

NEW_COMPANY_LABELS = {
    "fidelidade": "Fidelidade",
    "grupo_jose_de_mello": "Grupo José de Mello",
    "cuf": "CUF",
    "luz_saude": "Luz Saúde",
}


def slugify(value: str) -> str:
    """Create a stable ASCII identifier for nodes."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower().strip()
    ascii_text = re.sub(r"[^a-z0-9]+", "_", ascii_text)
    ascii_text = re.sub(r"_+", "_", ascii_text).strip("_")
    return ascii_text


def normalize_for_match(value: str) -> str:
    """Normalize a string for loose matching against filenames/labels."""
    return slugify(value).replace("_", "")


def load_dataset(path: Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        return pd.DataFrame(columns=["id", "label", "type"])
    return pd.read_csv(path)


def load_edges(path: Path = DEFAULT_EDGES_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        return pd.DataFrame(columns=["source", "target", "weight"])
    return pd.read_csv(path)


def ensure_company_nodes(dataset: pd.DataFrame) -> pd.DataFrame:
    """Insert the four new company nodes if they are not already present."""
    dataset = dataset.copy()
    existing = set(dataset["id"].astype(str))
    rows = []
    for company_id, label in NEW_COMPANY_LABELS.items():
        if company_id not in existing:
            rows.append({"id": company_id, "label": label, "type": "company"})
    if rows:
        dataset = pd.concat([dataset, pd.DataFrame(rows)], ignore_index=True)
    dataset = dataset.drop_duplicates(subset=["id"], keep="first").reset_index(drop=True)
    return dataset


def build_company_lookup(dataset: pd.DataFrame) -> dict[str, str]:
    """Map normalized labels and ids to canonical company ids."""
    lookup: dict[str, str] = {}
    for _, row in dataset.iterrows():
        if str(row.get("type", "")).lower() != "company":
            continue
        company_id = str(row["id"])
        label = str(row.get("label", company_id))
        lookup[normalize_for_match(company_id)] = company_id
        lookup[normalize_for_match(label)] = company_id
    for company_id in NEW_COMPANY_LABELS:
        lookup[normalize_for_match(company_id)] = company_id
        lookup[normalize_for_match(NEW_COMPANY_LABELS[company_id])] = company_id
    return lookup


def read_mapping(mapping_path: Path = DEFAULT_MAPPING_PATH) -> pd.DataFrame:
    return pd.read_csv(mapping_path)


def create_mapping_from_pdfs(
    pdf_dir: Path = DEFAULT_PDF_DIR,
    dataset_path: Path = DEFAULT_DATASET_PATH,
    output_path: Path = DEFAULT_MAPPING_PATH,
) -> pd.DataFrame:
    """Generate a pdf_filename -> company_id mapping draft from current files."""
    dataset = load_dataset(dataset_path)
    lookup = build_company_lookup(dataset)
    rows = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        stem_match = normalize_for_match(pdf_path.stem)
        company_id = lookup.get(stem_match, "")
        if not company_id:
            for candidate_key, candidate_id in lookup.items():
                if candidate_key and (candidate_key in stem_match or stem_match in candidate_key):
                    company_id = candidate_id
                    break
        if not company_id:
            company_id = slugify(pdf_path.stem)
        rows.append({"pdf_filename": pdf_path.name, "company_id": company_id})

    mapping = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(output_path, index=False)
    return mapping


def _extract_pdf_pages(pdf_obj) -> str:
    """Shared page-extraction logic for both file-path and in-memory PDF objects."""
    parts: list[str] = []
    for page_number, page in enumerate(pdf_obj.pages, start=1):
        parts.append(f"=== PAGE {page_number} ===")
        text = page.extract_text() or ""
        text = text.replace("\x00", " ").strip()
        if text:
            parts.append(text)
        tables = page.extract_tables() or []
        for table_index, table in enumerate(tables, start=1):
            parts.append(f"--- TABLE {page_number}.{table_index} ---")
            for row in table:
                if not row:
                    continue
                cells = [str(cell).strip() if cell is not None else "" for cell in row]
                parts.append(" | ".join(cells))
        parts.append("")
    return "\n".join(parts).strip() + "\n"


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text and tables from a PDF file on disk."""
    with pdfplumber.open(pdf_path) as pdf:
        return _extract_pdf_pages(pdf)


def extract_pdf_text_from_bytes(pdf_bytes: bytes) -> str:
    """Extract all text and tables from PDF bytes in memory (no disk I/O)."""
    import io
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return _extract_pdf_pages(pdf)


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse the first JSON object from a model response."""
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\s*```$", "", candidate)
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        candidate = candidate[start : end + 1]
    return json.loads(candidate)


# ---------------------------------------------------------------------------
# Name validation helpers
# ---------------------------------------------------------------------------

_PARTICLES: frozenset[str] = frozenset({
    "de", "da", "do", "dos", "das", "e", "di", "del", "la", "le",
    "von", "van", "y", "ao", "à", "às", "aos", "na", "no", "nas", "nos",
    "em", "um", "uma",
})

_ROLE_SUFFIXES: frozenset[str] = frozenset({
    "vice", "presidente", "vogal", "administrador", "administradora",
    "ceo", "cfo", "coo", "cto", "cro", "director", "diretora",
    "independente", "membro", "chairman",
})

_COMPANY_MARKERS: frozenset[str] = frozenset({
    "s.a.", "sgps", "s.g.p.s.", "gmbh", "sàrl", "sarl", "ltd", "llc",
    "sa", "srl", "nv", "plc", "inc", "corp", "cie", "ag", "bv",
    "associação", "fundação", "banco", "grupo", "cotec",
})

# Words that are common in Portuguese phrases but never start a person's name
_PHRASE_STARTERS: frozenset[str] = frozenset({
    "cargo", "mandato", "funções", "funcoes", "compete", "exerceu",
    "exercer", "faltando", "poderá", "variável", "variavel",
    "impostos", "designadamente", "que", "do", "da", "ao", "à",
    "pelo", "pela", "pelos", "pelas", "em", "na", "no",
    "milhões", "milhoestais", "data",
})


def _clean_member_name(raw: str) -> str | None:
    """Validate and clean a raw member entry.

    Returns the cleaned name if it looks like a real person name,
    or None if it appears to be a phrase, company name, or other noise.
    """
    name = raw.strip().strip(".,;:\"'")
    if not name:
        return None

    words = name.split()

    # Strip trailing role words (e.g. "Luísa Alexandra Ramos Amorim Vice")
    while words and words[-1].lower() in _ROLE_SUFFIXES:
        words.pop()

    if len(words) < 2 or len(words) > 10:
        return None

    first_word_lower = words[0].lower()

    # Reject if first word is a known phrase-starter
    if first_word_lower in _PHRASE_STARTERS:
        return None

    # Reject if any word looks like a company marker or legal suffix
    if any(w.lower().rstrip(".") in _COMPANY_MARKERS for w in words):
        return None

    # Every content word (non-particle) must start with an uppercase letter
    content_words = [w for w in words if w.lower() not in _PARTICLES]
    if not content_words:
        return None

    if not all(w[0].isupper() for w in content_words):
        return None

    return " ".join(words)


def _members_have_quality_issues(members: list[str]) -> bool:
    """Return True if the member list contains obvious non-name entries.

    Threshold is intentionally low (10 %) so that files with even a few
    garbage entries are reprocessed rather than silently kept.
    """
    if not members:
        return False
    bad = sum(1 for m in members if _clean_member_name(m) is None)
    return bad > 0 and (bad / len(members)) > 0.10


def extract_candidate_member_names(text: str) -> list[str]:
    """Heuristic fallback for board member names when the model returns empty."""
    lines = [line.strip() for line in text.replace("\r\n", "\n").splitlines() if line.strip()]
    role_patterns = [
        re.compile(
            r"^(?P<name>[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ'.-]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ'.-]+){1,8})\s*[\-–—:]?\s*(?P<role>Presidente|Vogal|Administrador|Administradora|Membro|CEO|CFO|COO|CITO|CRO)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"^(?P<role>Presidente|Vogal|Administrador|Administradora|Membro|CEO|CFO|COO|CITO|CRO)\b[:\-–—]?(?P<name>\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ'.-]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ'.-]+){1,8})$",
            re.IGNORECASE,
        ),
    ]
    stop_tokens = {
        "comissão",
        "executiva",
        "auditoria",
        "fiscal",
        "governance",
        "governo",
        "societário",
        "societario",
        "saúde",
        "saude",
        "empresa",
        "grupo",
    }
    names: list[str] = []
    seen: set[str] = set()
    for line in lines:
        for pattern in role_patterns:
            match = pattern.search(line)
            if not match:
                continue
            name = match.group("name").strip().strip("-–—:,")
            if not name:
                continue
            lowered = name.lower()
            if any(token in lowered for token in stop_tokens):
                continue
            if len(name.split()) < 2:
                continue
            key = slugify(name)
            if key and key not in seen:
                seen.add(key)
                names.append(name)
            break
    return names


def extract_relevant_excerpt(text: str, max_chars: int = 20000) -> str:
    """Keep the most relevant board/governance windows for Gemini input.

    Prioritises sections that list board composition (membership tables) rather
    than biography sections so the model sees names in a clean list format.
    """
    normalized = text.replace("\r\n", "\n")
    lower_text = normalized.lower()

    # High-priority keywords: these appear right before the list of members
    priority_keywords = [
        "composição do conselho de administração",
        "composicao do conselho de administracao",
        "conselho de administração é composto",
        "conselho de administração é constituído",
        "membros executivos",
        "membros não executivos",
        "membros nao executivos",
        "presidente do conselho de administração",
        "órgãos sociais",
        "orgaos sociais",
        "membros do conselho",
    ]
    # Fallback keywords — broader
    fallback_keywords = [
        "conselho de administração",
        "conselho de administracao",
        "board of directors",
        "governo societário",
        "governo societario",
        "administração",
    ]

    hits: list[str] = []
    seen_windows: set[tuple[int, int]] = set()

    def _add_window(idx: int, before: int = 300, after: int = 6000) -> None:
        window_start = max(0, idx - before)
        window_end = min(len(normalized), idx + after)
        key = (window_start, window_end)
        if key not in seen_windows:
            seen_windows.add(key)
            hits.append(normalized[window_start:window_end].strip())

    for keyword in priority_keywords:
        start = 0
        while True:
            idx = lower_text.find(keyword, start)
            if idx < 0:
                break
            _add_window(idx, before=200, after=6000)
            start = idx + len(keyword)
            if len(hits) >= 5:
                break
        if len(hits) >= 5:
            break

    if not hits:
        for keyword in fallback_keywords:
            start = 0
            while True:
                idx = lower_text.find(keyword, start)
                if idx < 0:
                    break
                _add_window(idx, before=500, after=5000)
                start = idx + len(keyword)
                if len(hits) >= 3:
                    break
            if len(hits) >= 3:
                break

    if not hits:
        return normalized[:max_chars].strip()

    excerpt = "\n\n---\n\n".join(hits)
    return excerpt[:max_chars].strip()


class AIContentExtractor:
    """
    Extrai conselhos de administração usando o Gemini Flash.

    Examples:
        >>> generator = AIContentExtractor(api_key="your_key")
        >>> result = generator.extract_members_from_text("...", "Fidelidade")
        >>> print(result["members"])
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-pro"):
        """
        Inicializa o extractor.

        Args:
            api_key: Gemini API key.
            model_name: Modelo a usar.
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def build_prompt(self, company_name: str, text: str) -> str:
        excerpt = extract_relevant_excerpt(text)
        return (
            "És um extrator especializado em relatórios de governo societário português.\n"
            "A tua ÚNICA tarefa: devolver os nomes completos das pessoas que são membros "
            "do Conselho de Administração da empresa indicada.\n\n"
            "=== INSTRUÇÕES ESTRITAS ===\n"
            "PASSO 1 — Localiza a secção de COMPOSIÇÃO do Conselho de Administração "
            "(normalmente uma tabela ou lista com cargos como Presidente, Vogal, etc.).\n"
            "PASSO 2 — Para cada linha com um cargo executivo ou não executivo, "
            "extrai APENAS o nome completo da PESSOA (nome próprio + apelidos).\n"
            "PASSO 3 — Verifica que cada entrada é exclusivamente um nome de pessoa humana.\n\n"
            "=== O QUE INCLUIR ===\n"
            "✓ Nomes completos de pessoas físicas membros do Conselho de Administração\n"
            "  Ex: 'António Rios de Amorim', 'Luísa Alexandra Ramos Amorim',\n"
            "      'Helena Sofia Silva Borges Salgado Fonseca Cerveira Pinto'\n\n"
            "=== O QUE EXCLUIR ABSOLUTAMENTE ===\n"
            "✗ Cargos ou títulos: 'Presidente', 'Vogal', 'CEO', 'Vice', 'independente'\n"
            "✗ Frases ou fragmentos do documento: 'cargo de', 'data da designação para',\n"
            "  'do exercício pelo', 'faltando definitivamente', 'Compete ao'\n"
            "✗ Nomes de empresas, bancos, associações ou fundações:\n"
            "  'Banco CTT', 'COTEC Portugal', 'Rabobank España', 'Associação Business Roundtable'\n"
            "✗ Membros de OUTROS órgãos: Mesa da Assembleia Geral, Conselho Fiscal,\n"
            "  Comissão de Auditoria, Comissão de Remunerações\n"
            "✗ Textos sobre remunerações, políticas, competências ou mandatos\n\n"
            "=== ATENÇÃO ESPECIAL ===\n"
            "Os relatórios incluem biografias detalhadas de cada membro com cargos passados,\n"
            "empresas onde trabalhou, associações onde participa — IGNORA TUDO ISSO.\n"
            "Só interessa o nome da pessoa que é membro do Conselho de Administração.\n\n"
            f"Empresa: {company_name}\n\n"
            "=== TEXTO DO RELATÓRIO ===\n"
            f"{excerpt}"
        )

    def extract_members_from_text(self, text: str, company_name: str) -> dict[str, Any]:
        json_schema = {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "members": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de nomes completos de pessoas (e APENAS pessoas) "
                        "que são membros do Conselho de Administração."
                    ),
                },
                "notes": {"type": "string"},
            },
            "required": ["company", "members", "notes"],
        }
        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=json_schema,
        )

        last_error: Exception | None = None
        for attempt in range(5):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.build_prompt(company_name, text),
                    config=gen_config,
                )
                raw_text = getattr(response, "text", "") or str(response)
                payload = extract_json_object(raw_text)
                break
            except Exception as exc:  # pragma: no cover
                last_error = exc
                message = str(exc)
                lowered = message.lower()
                if "429" in message or "quota" in lowered or "503" in message or "unavailable" in lowered:
                    wait_seconds = 20 + attempt * 15
                    time.sleep(wait_seconds)
                    continue
                raise
        else:
            raise last_error or RuntimeError("Gemini extraction failed")

        members = payload.get("members", [])
        if not isinstance(members, list):
            members = []

        cleaned_members = []
        seen: set[str] = set()
        for member in members:
            if isinstance(member, dict):
                raw = str(member.get("name", "")).strip()
            else:
                raw = str(member).strip()
            name = _clean_member_name(raw)
            if name:
                key = slugify(name)
                if key and key not in seen:
                    seen.add(key)
                    cleaned_members.append(name)

        if not cleaned_members:
            cleaned_members = extract_candidate_member_names(text)

        payload["members"] = cleaned_members
        payload["company"] = company_name
        return payload


def save_text_output(pdf_path: Path, text: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{pdf_path.stem}.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path


def save_json_output(pdf_path: Path, payload: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{pdf_path.stem}_members.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def canonical_member_id(name: str) -> str:
    return slugify(name)


def canonical_weight() -> float:
    return round(random.uniform(0.1, 0.5), 3)


def timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def load_json_members(json_dir: Path) -> Iterable[Path]:
    return sorted(json_dir.glob("*_members.json"))
