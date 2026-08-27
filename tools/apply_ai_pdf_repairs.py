"""Aplica propostas já validadas de ``propose_ai_pdf_repairs.py``.

Somente campos que continuam defeituosos no banco são alterados. O estado
anterior é salvo em backup e a execução exige ``--confirm APPLY``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_question_quality import fetch_questions, inspect, load_env, normalized  # noqa: E402


def read_proposals(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("status") == "proposed" and not record.get("validation") and isinstance(record.get("proposal"), dict):
            records.append(record)
    return records


def changes_for(row: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    codes = {item["code"] for item in inspect(row)}
    changes: dict[str, Any] = {}
    statement = proposal.get("enunciado")
    if codes.intersection({"statement_missing", "statement_placeholder", "statement_too_short"}):
        if isinstance(statement, list) and len(normalized(" ".join(map(str, statement)))) >= 25:
            changes["enunciado"] = statement
    command = proposal.get("comando")
    if codes.intersection({"command_missing", "command_too_short"}):
        if isinstance(command, str) and len(normalized(command)) >= 8:
            changes["comando"] = command
    alternatives = proposal.get("alternativas")
    if codes.intersection({"alternatives_incomplete", "alternatives_duplicate", "alternative_too_short"}):
        if isinstance(alternatives, dict) and set(alternatives) == set("ABCDE"):
            textual = {key: str(value).strip() for key, value in alternatives.items() if value is not None}
            values = [normalized(value) for value in textual.values()]
            if len(textual) == 5 and len(values) == len(set(values)):
                changes["alternativas"] = textual
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposal_file", type=Path)
    parser.add_argument("--confirm")
    args = parser.parse_args()
    if args.confirm != "APPLY":
        raise SystemExit("Use --confirm APPLY para gravar")
    proposals = {int(item["id"]): item for item in read_proposals(args.proposal_file)}
    rows = {int(row["id"]): row for row in fetch_questions() if int(row["id"]) in proposals}
    repairs = []
    for question_id, record in proposals.items():
        row = rows.get(question_id)
        if not row:
            continue
        changes = changes_for(row, record["proposal"])
        if changes:
            repairs.append({
                "id": question_id,
                "before": {key: row.get(key) for key in changes},
                "changes": changes,
                "source_report": str(args.proposal_file),
                "model": record.get("model"),
            })
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / "reports" / f"ai_pdf_repairs_backup_{stamp}.json"
    backup.write_text(json.dumps(repairs, ensure_ascii=False, indent=2), encoding="utf-8")
    load_env()
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {
        "apikey": key, "Authorization": f"Bearer {key}",
        "Content-Type": "application/json", "Prefer": "return=minimal",
    }
    for repair in repairs:
        query = urllib.parse.urlencode({"id": f"eq.{repair['id']}"})
        request = urllib.request.Request(
            f"{base}/rest/v1/questoes?{query}", method="PATCH", headers=headers,
            data=json.dumps(repair["changes"], ensure_ascii=False).encode("utf-8"),
        )
        with urllib.request.urlopen(request, timeout=30):
            pass
    print(json.dumps({"applied": len(repairs), "ids": [item["id"] for item in repairs], "backup": str(backup)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
