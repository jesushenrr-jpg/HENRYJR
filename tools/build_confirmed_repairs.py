"""Monta reparos conservadores confirmados por fontes locais.

Nenhuma gravação é feita sem ``--apply --confirm APPLY``. Antes de aplicar, o
script salva os valores originais em ``reports/confirmed_repairs_backup.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_question_quality import fetch_questions, load_env, normalized  # noqa: E402

LETTERS = "ABCDE"
UNSAFE_TEXT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]|�|(?:Caderno|Página)\s+\d+", re.I)


def clean_pdf_text(value: str) -> str:
    value = value.replace("\t", " ").replace("\u00ad", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def coverage(value: str, page: str) -> float:
    tokens = normalized(value).split()
    page_norm = normalized(page)
    return sum(token in page_norm for token in tokens) / len(tokens) if tokens else 0


def exact_in_page(value: str, page: str) -> bool:
    candidate = normalized(value)
    return bool(candidate) and candidate in normalized(page) and not UNSAFE_TEXT.search(value)


def local_enem() -> dict[tuple[int, str, int], dict[str, Any]]:
    result = {}
    for path in (ROOT / "DADOS" / "json").glob("enem_20*.json"):
        if "backup" in path.name:
            continue
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for row in rows:
            if row.get("ano") and row.get("dia") and row.get("numero"):
                result[(int(row["ano"]), str(row["dia"]), int(row["numero"]))] = row
    return result


def shared_stimulus(page: str, number: int) -> str | None:
    heading = re.search(
        r"(?:Texto|Textos)\s+para\s+(?:as\s+)?quest(?:ões|oes)\s+(\d+)\s*(?:e|a|–|-)\s*(\d+)",
        page, re.I,
    )
    if not heading or not (int(heading.group(1)) <= number <= int(heading.group(2))):
        return None
    first = int(heading.group(1))
    marker = re.search(rf"quest(?:ão|ao)\s+{first}\b", page[heading.end():], re.I)
    if not marker:
        return None
    text = page[heading.end(): heading.end() + marker.start()]
    text = clean_pdf_text(text)
    return text if len(normalized(text)) >= 40 else None


def build() -> dict[str, Any]:
    old = local_enem()
    readers: dict[str, PdfReader] = {}
    repairs = []
    for row in fetch_questions():
        changes: dict[str, Any] = {}
        reasons: list[str] = []
        pdf_page = None
        statement = [str(v).strip() for v in (row.get("enunciado") or []) if str(v).strip()]
        current = row.get("alternativas") if isinstance(row.get("alternativas"), dict) else {}
        current_values = [normalized(str(current.get(letter) or "")) for letter in LETTERS]
        current_bad = any(not value for value in current_values) or len(set(v for v in current_values if v)) < 5
        needs_pdf = not statement or current_bad
        if needs_pdf and row.get("fonte") == "ENEM" and row.get("tipo") == "PROVA" and row.get("pagina_pdf") is not None:
            pdf = ROOT / "DADOS" / "PROVAS" / str(row["ano"]) / f"{row['dia']}.pdf"
            if pdf.exists():
                reader = readers.setdefault(str(pdf), PdfReader(str(pdf)))
                page_index = int(row["pagina_pdf"])
                if 0 <= page_index < len(reader.pages):
                    pdf_page = reader.pages[page_index].extract_text() or ""

        if pdf_page:
            if not statement:
                shared = shared_stimulus(pdf_page, int(row["numero"]))
                if shared:
                    changes["enunciado"] = [shared]
                    reasons.append("texto compartilhado confirmado pelo cabeçalho do PDF")

            previous = old.get((int(row["ano"]), str(row["dia"]), int(row["numero"])))
            old_alts = previous.get("alternativas") if previous and isinstance(previous.get("alternativas"), dict) else {}
            candidate = {letter: str(old_alts.get(letter) or "").strip() for letter in LETTERS}
            candidate_norm = [normalized(value) for value in candidate.values()]
            if (
                current_bad
                and all(candidate.values())
                and len(set(candidate_norm)) == 5
                and all(exact_in_page(value, pdf_page) for value in candidate.values())
            ):
                changes["alternativas"] = candidate
                reasons.append("cinco alternativas da extração anterior confirmadas no PDF")

        images = row.get("imagens") if isinstance(row.get("imagens"), list) else []
        alt_images = row.get("imagens_alternativas") if isinstance(row.get("imagens_alternativas"), dict) else {}
        expected_image_flag = bool(images or alt_images)
        if bool(row.get("tem_imagem")) != expected_image_flag:
            changes["tem_imagem"] = expected_image_flag
            reasons.append("flag reconciliada com referências de imagem")

        if changes:
            repairs.append({
                "id": row["id"], "fonte": row.get("fonte"), "ano": row.get("ano"),
                "dia": row.get("dia"), "numero": row.get("numero"),
                "pagina_pdf": row.get("pagina_pdf"), "reasons": reasons,
                "before": {key: row.get(key) for key in changes}, "changes": changes,
            })
    return {"summary": {"repairs": len(repairs)}, "repairs": repairs}


def apply(report: dict[str, Any]) -> None:
    load_env()
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {
        "apikey": key, "Authorization": f"Bearer {key}",
        "Content-Type": "application/json", "Prefer": "return=minimal",
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / "reports" / f"confirmed_repairs_backup_{stamp}.json"
    backup.write_text(json.dumps(report["repairs"], ensure_ascii=False, indent=2), encoding="utf-8")
    for index, repair in enumerate(report["repairs"], 1):
        query = urllib.parse.urlencode({"id": f"eq.{repair['id']}"})
        request = urllib.request.Request(
            f"{base}/rest/v1/questoes?{query}", data=json.dumps(repair["changes"]).encode(),
            method="PATCH", headers=headers,
        )
        with urllib.request.urlopen(request, timeout=30):
            pass
        if index % 50 == 0:
            print(f"Aplicados {index}/{len(report['repairs'])}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "confirmed_repairs.json")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    report = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if args.apply:
        if args.confirm != "APPLY":
            raise SystemExit("Use --confirm APPLY para gravar")
        apply(report)
        print("Reparos aplicados com backup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
