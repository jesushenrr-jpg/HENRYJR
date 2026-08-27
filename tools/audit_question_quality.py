"""Auditoria somente leitura da tabela ``questoes`` no Supabase.

Uso:
    python tools/audit_question_quality.py
    python tools/audit_question_quality.py --json reports/question_quality.json

O script nunca grava no banco. Credenciais são lidas de ``.env`` e não são
incluídas no relatório.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LETTERS = set("ABCDE")
VALID_AREAS = {
    "Linguagens, Codigos e suas Tecnologias",
    "Ciencias Humanas e suas Tecnologias",
    "Ciencias da Natureza e suas Tecnologias",
    "Matematica e suas Tecnologias",
}
MOJIBAKE = re.compile(r"(?:Ã.|Â.|�|\uFFFD)")
PLACEHOLDER = re.compile(
    r"(?:texto indispon[ií]vel|enunciado n[aã]o dispon[ií]vel|quest[aã]o ileg[ií]vel|"
    r"n[aã]o foi poss[ií]vel extrair|consultar pdf|ver no pdf|^\s*⚠)", re.I
)
OCR_NOISE = re.compile(r"(?:\|{3,}|_{4,}|\.{5,}|[■□◆]{2,}|(?:\b[A-Z]\s){6,})")


def load_env() -> None:
    for raw in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def fetch_questions() -> list[dict[str, Any]]:
    load_env()
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not base or not key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY ausentes")

    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    columns = (
        "id,numero,ano,dia,area,competencia,enunciado,comando,alternativas,"
        "gabarito,confianca,revisado,anulada,tem_imagem,pagina_pdf,imagens,"
        "imagens_alternativas,fonte,tipo,evento,turno,provedor"
    )
    rows: list[dict[str, Any]] = []
    page_size = 1000
    for start in range(0, 100_000, page_size):
        query = urllib.parse.urlencode({"select": columns, "order": "id.asc"})
        request = urllib.request.Request(
            f"{base}/rest/v1/questoes?{query}",
            headers={**headers, "Range": f"{start}-{start + page_size - 1}"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            batch = json.loads(response.read())
        rows.extend(batch)
        if len(batch) < page_size:
            break
    return rows


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"\W+", " ", value).strip()


def issue(code: str, severity: str, detail: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "detail": detail}


def inspect(row: dict[str, Any]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    enunciado = row.get("enunciado") if isinstance(row.get("enunciado"), list) else []
    paragraphs = [str(v).strip() for v in enunciado if str(v).strip()]
    statement = "\n".join(paragraphs)
    command = str(row.get("comando") or "").strip()
    alternatives = row.get("alternativas") if isinstance(row.get("alternativas"), dict) else {}
    alternatives = {str(k).upper(): str(v or "").strip() for k, v in alternatives.items()}
    all_text = "\n".join([statement, command, *alternatives.values()])
    source = str(row.get("fonte") or "")

    if not paragraphs:
        found.append(issue("statement_missing", "critical", "enunciado vazio"))
    elif len(normalized(statement)) < 25:
        found.append(issue("statement_too_short", "high", f"{len(statement)} caracteres"))
    if PLACEHOLDER.search(statement):
        found.append(issue("statement_placeholder", "high", "texto provisório/indisponível"))
    if not command:
        found.append(issue("command_missing", "high", "comando vazio"))
    elif len(normalized(command)) < 8:
        found.append(issue("command_too_short", "medium", command[:100]))

    expected_min = 4 if source in {"UFT", "PAES"} else 5
    populated = {k: v for k, v in alternatives.items() if k in LETTERS and v}
    if len(populated) < expected_min:
        found.append(issue("alternatives_incomplete", "critical", f"{len(populated)} preenchidas"))
    invalid_keys = sorted(set(alternatives) - LETTERS)
    if invalid_keys:
        found.append(issue("alternative_keys_invalid", "high", ", ".join(invalid_keys)))
    for letter, text in populated.items():
        if len(normalized(text)) < 2:
            found.append(issue("alternative_too_short", "high", f"{letter}: {text!r}"))

    answer = str(row.get("gabarito") or "").upper()
    annulled = bool(row.get("anulada"))
    if not annulled and answer not in LETTERS:
        found.append(issue("answer_missing", "critical", f"gabarito={answer or 'null'}"))
    elif answer and answer not in populated:
        found.append(issue("answer_without_alternative", "critical", answer))

    if row.get("area") not in VALID_AREAS:
        found.append(issue("area_invalid", "high", str(row.get("area"))))
    competence = row.get("competencia")
    if competence and not re.fullmatch(r"H(?:0[1-9]|[12]\d|30)", str(competence)):
        found.append(issue("competence_invalid", "medium", str(competence)))
    if row.get("pagina_pdf") is None:
        found.append(issue("pdf_page_missing", "medium", "sem referência de página"))

    images = row.get("imagens") if isinstance(row.get("imagens"), list) else []
    alt_images = row.get("imagens_alternativas") if isinstance(row.get("imagens_alternativas"), dict) else {}
    has_images = bool(images or alt_images)
    if bool(row.get("tem_imagem")) != has_images:
        found.append(issue("image_flag_mismatch", "high", f"flag={row.get('tem_imagem')}, refs={has_images}"))
    if MOJIBAKE.search(all_text):
        found.append(issue("encoding_mojibake", "high", "sequência de encoding inválida"))
    if OCR_NOISE.search(all_text):
        found.append(issue("ocr_noise", "medium", "padrão forte de ruído OCR"))
    if len(all_text) > 25_000:
        found.append(issue("text_excessive", "medium", f"{len(all_text)} caracteres"))

    normalized_alts = [normalized(v) for v in populated.values()]
    if len(normalized_alts) != len(set(normalized_alts)):
        found.append(issue("alternatives_duplicate", "critical", "alternativas idênticas"))
    return found


def build_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    records = []
    counts: collections.Counter[str] = collections.Counter()
    severities: collections.Counter[str] = collections.Counter()
    by_source: collections.Counter[str] = collections.Counter()
    fingerprints: dict[str, list[int]] = collections.defaultdict(list)

    for row in rows:
        statement = " ".join(str(v) for v in (row.get("enunciado") or []))
        command = str(row.get("comando") or "")
        fingerprint = hashlib.sha1(normalized(statement + " " + command).encode()).hexdigest()
        if len(normalized(statement + command)) >= 50:
            fingerprints[fingerprint].append(int(row["id"]))

        found = inspect(row)
        if not found:
            continue
        for item in found:
            counts[item["code"]] += 1
            severities[item["severity"]] += 1
        by_source[str(row.get("fonte") or "UNKNOWN")] += 1
        records.append({
            "id": row.get("id"), "fonte": row.get("fonte"), "ano": row.get("ano"),
            "dia": row.get("dia"), "numero": row.get("numero"),
            "pagina_pdf": row.get("pagina_pdf"), "issues": found,
        })

    duplicates = [ids for ids in fingerprints.values() if len(ids) > 1]
    return {
        "summary": {
            "total_questions": len(rows),
            "flagged_questions": len(records),
            "issues_by_code": dict(counts.most_common()),
            "issues_by_severity": dict(severities.most_common()),
            "flagged_by_source": dict(by_source.most_common()),
            "exact_text_duplicate_groups": len(duplicates),
        },
        "duplicate_groups": duplicates,
        "questions": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = build_report(fetch_questions())
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Relatório: {args.json}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise
