"""Remove artefatos inequívocos de cabeçalho/rodapé capturados pelo parser.

Escopo inicial deliberadamente restrito ao PAES e ao domínio/marca do PDF
espelho. Não tenta reconstruir conteúdo que atravessou páginas.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_question_quality import fetch_questions, load_env  # noqa: E402

DOMAIN = re.compile(r"(?:www\.)?castrodigital\.com\.br|igital\.com\.br", re.I)
COMPACT_FOOTER = re.compile(
    r"\s+\d{1,3}\s+PROCESSO\s*EDUCAÇÃO\s*SELETIVO\s*SUPERIOR\s*DE ACESSO À",
    re.I,
)
LEADING_COMPACT = re.compile(
    r"^\s*\d{1,3}\s+PROCESSO\s*EDUCAÇÃO\s*SELETIVO\s*SUPERIOR\s*DE ACESSO À\s*",
    re.I,
)
FOOTER_START = re.compile(
    r"(?:\b\d{1,3}\s+)?(?:PROCESSO\s*EDUCAÇÃO\s*SELETIVO\s*SUPERIOR\s*DE ACESSO À|"
    r"PROCESSO\s*SELETIVO.*?EDUCAÇÃO\s*SUPERIOR|EDUCAÇÃO\s+SUPERIOR\s+\d{1,3})",
    re.I | re.S,
)


def clean(value: str) -> tuple[str, bool]:
    leading = LEADING_COMPACT.match(value)
    if leading:
        return value[leading.end():].lstrip(), True
    compact = COMPACT_FOOTER.search(value)
    if compact:
        return value[:compact.start()].rstrip(" -–|\t\n"), True
    match = DOMAIN.search(value)
    if not match:
        return value, False
    prefix_window_start = max(0, match.start() - 900)
    window = value[prefix_window_start:match.start()]
    process_starts = [
        found for found in re.finditer(r"Processo", window, re.I)
        if sum(word in window[found.start():].lower() for word in ("seletivo", "superior", "acesso")) >= 2
    ]
    starts = list(FOOTER_START.finditer(window))
    if process_starts:
        cut = prefix_window_start + process_starts[-1].start()
    elif starts:
        cut = prefix_window_start + starts[-1].start()
    else:
        cut = match.start()
    cleaned = value[:cut].rstrip(" -–|\t\n")
    cleaned = re.sub(r"\s+\d{1,3}\s*$", "", cleaned).rstrip()
    return cleaned, cleaned != value


def build() -> dict[str, Any]:
    repairs = []
    for row in fetch_questions():
        if row.get("fonte") != "PAES":
            continue
        changes: dict[str, Any] = {}
        before: dict[str, Any] = {}

        paragraphs = row.get("enunciado") if isinstance(row.get("enunciado"), list) else []
        new_paragraphs = []
        changed = False
        for paragraph in paragraphs:
            new_value, did_change = clean(str(paragraph))
            changed |= did_change
            if new_value.strip():
                new_paragraphs.append(new_value.strip())
        if changed:
            before["enunciado"] = paragraphs
            changes["enunciado"] = new_paragraphs

        command = str(row.get("comando") or "")
        new_command, changed = clean(command)
        if changed:
            before["comando"] = row.get("comando")
            changes["comando"] = new_command.strip() or None

        alternatives = row.get("alternativas") if isinstance(row.get("alternativas"), dict) else {}
        new_alternatives = dict(alternatives)
        changed = False
        for letter, value in alternatives.items():
            new_value, did_change = clean(str(value or ""))
            changed |= did_change
            new_alternatives[letter] = new_value.strip()
        if changed:
            before["alternativas"] = alternatives
            changes["alternativas"] = new_alternatives

        if changes:
            repairs.append({
                "id": row["id"], "fonte": row["fonte"], "ano": row.get("ano"),
                "dia": row.get("dia"), "numero": row.get("numero"),
                "before": before, "changes": changes,
            })
    return {"summary": {"questions": len(repairs)}, "repairs": repairs}


def apply(report: dict[str, Any]) -> None:
    load_env()
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / "reports" / f"document_artifacts_backup_{stamp}.json"
    backup.write_text(json.dumps(report["repairs"], ensure_ascii=False, indent=2), encoding="utf-8")
    for repair in report["repairs"]:
        query = urllib.parse.urlencode({"id": f"eq.{repair['id']}"})
        request = urllib.request.Request(
            f"{base}/rest/v1/questoes?{query}", data=json.dumps(repair["changes"]).encode(),
            method="PATCH", headers=headers,
        )
        with urllib.request.urlopen(request, timeout=30):
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "document_artifacts.json")
    args = parser.parse_args()
    report = build()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    if args.apply:
        if args.confirm != "APPLY":
            raise SystemExit("Use --confirm APPLY")
        apply(report)
        print("Limpeza aplicada com backup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
