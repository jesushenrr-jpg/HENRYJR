"""Aplica um resultado manual revisado contra o manifesto do lote.

Este script é específico para resultados que já passaram por inspeção visual.
Exige conjunto de IDs idêntico ao manifesto, salva backup e só grava com
``--confirm APPLY``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_question_quality import fetch_questions, load_env, normalized  # noqa: E402


def validate_and_prepare(result_path: Path, batch_zip: Path) -> list[dict[str, Any]]:
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    with zipfile.ZipFile(batch_zip) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    if result.get("schema_version") != "henryjr-question-extraction-v1":
        raise ValueError("schema_version inesperada")
    items = result.get("items")
    if not isinstance(items, list):
        raise ValueError("items deve ser uma lista")
    expected = {int(item["id"]): item for item in manifest["items"]}
    received = {int(item["id"]): item for item in items}
    if len(received) != len(items) or set(received) != set(expected):
        raise ValueError("IDs recebidos não coincidem exatamente com o manifesto")
    prepared = []
    for question_id, item in received.items():
        reference = expected[question_id]
        for key in ("fonte", "ano", "dia", "numero", "pagina_pdf"):
            if str(item.get(key)) != str(reference.get(key)):
                raise ValueError(f"id {question_id}: metadado divergente em {key}")
        if item.get("status") != "extraido":
            raise ValueError(f"id {question_id}: status não aprovado")
        statement = item.get("enunciado")
        command = item.get("comando")
        alternatives = item.get("alternativas")
        if not isinstance(statement, list) or len(normalized(" ".join(map(str, statement)))) < 25:
            raise ValueError(f"id {question_id}: enunciado inválido")
        if not isinstance(command, str) or len(normalized(command)) < 8:
            raise ValueError(f"id {question_id}: comando inválido")
        if not isinstance(alternatives, dict) or set(alternatives) != set("ABCDE"):
            raise ValueError(f"id {question_id}: alternativas inválidas")
        if any(not isinstance(alternatives[key], str) or not alternatives[key].strip() for key in "ABCDE"):
            raise ValueError(f"id {question_id}: alternativa textual vazia")
        if question_id == 237:
            alternatives["E"] = alternatives["E"].replace(
                "exercícios que permitem um aumento", "exercícios que permitam um aumento"
            )
        prepared.append({"id": question_id, "changes": {
            "enunciado": statement, "comando": command, "alternativas": alternatives,
        }})
    return prepared


def upload_shared_image(path: Path, remote: str) -> str:
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    request = urllib.request.Request(
        f"{base}/storage/v1/object/imagens-questoes/{remote}", method="POST",
        data=path.read_bytes(), headers={
            "apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "image/jpeg",
            "x-upsert": "true",
        },
    )
    with urllib.request.urlopen(request, timeout=60):
        pass
    return f"{base}/storage/v1/object/public/imagens-questoes/{remote}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("batch_zip", type=Path)
    parser.add_argument("--shared-image", type=Path)
    parser.add_argument("--confirm")
    args = parser.parse_args()
    if args.confirm != "APPLY":
        raise SystemExit("Use --confirm APPLY para gravar")
    repairs = validate_and_prepare(args.result, args.batch_zip)
    load_env()
    if args.shared_image:
        remote = "2011/dia2/q133_q134_1.jpg"
        public_url = upload_shared_image(args.shared_image, remote)
        image_value = [{"path": remote, "posicao": "antes_1", "supabase_url": public_url}]
        for repair in repairs:
            if repair["id"] in {274, 275}:
                repair["changes"].update({"imagens": image_value, "tem_imagem": True})
    current = {int(row["id"]): row for row in fetch_questions() if int(row["id"]) in {r["id"] for r in repairs}}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / "reports" / f"manual_result_backup_{stamp}.json"
    backup.write_text(json.dumps([
        {"id": repair["id"], "before": {key: current[repair["id"]].get(key) for key in repair["changes"]}}
        for repair in repairs
    ], ensure_ascii=False, indent=2), encoding="utf-8")
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {
        "apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    for repair in repairs:
        query = urllib.parse.urlencode({"id": f"eq.{repair['id']}"})
        request = urllib.request.Request(
            f"{base}/rest/v1/questoes?{query}", method="PATCH", headers=headers,
            data=json.dumps(repair["changes"], ensure_ascii=False).encode("utf-8"),
        )
        with urllib.request.urlopen(request, timeout=30):
            pass
    print(json.dumps({"applied": len(repairs), "ids": [r["id"] for r in repairs], "backup": str(backup)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
