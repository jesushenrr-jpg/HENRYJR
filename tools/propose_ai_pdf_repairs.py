"""Propõe reparos de questões a partir da imagem da página do PDF.

O processamento externo precisa ser autorizado pelo responsável pelo acervo.
Este utilitário é deliberadamente *read-only*: não possui código de PATCH no
Supabase. Resultados e checkpoints ficam em ``reports/``.

Exemplo:
    python tools/propose_ai_pdf_repairs.py --max-items 5 --delay 8
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_question_quality import fetch_questions, inspect, load_env, normalized  # noqa: E402

MODEL = "qwen/qwen3.8-27b"
ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_MODEL = "gemini-2.5-flash"
LETTERS = "ABCDE"
SUSPICIOUS = re.compile(r"(?:não consigo|ilegível|consultar|invent|```|�)", re.I)
MOJIBAKE = re.compile(r"(?:Ã.|Â.|â€|â€™|â€œ|â€)")


def pdf_for(row: dict[str, Any]) -> Path | None:
    if row.get("fonte") == "ENEM" and row.get("tipo") == "PROVA":
        path = ROOT / "DADOS" / "PROVAS" / str(row.get("ano")) / f"{row.get('dia')}.pdf"
        return path if path.exists() else None
    return None


def candidates() -> list[dict[str, Any]]:
    selected = []
    for row in fetch_questions():
        codes = {item["code"] for item in inspect(row)}
        if not codes.intersection({"statement_missing", "statement_placeholder", "alternatives_incomplete", "alternatives_duplicate"}):
            continue
        path = pdf_for(row)
        page = row.get("pagina_pdf")
        if path and isinstance(page, int) and page >= 0:
            selected.append({**row, "_pdf": str(path), "_issues": sorted(codes)})
    return selected


def render_page(path: Path, page_index: int) -> bytes:
    with tempfile.TemporaryDirectory(prefix="henryjr_pdf_") as directory:
        target = Path(directory) / "page"
        subprocess.run(
            ["pdftoppm", "-f", str(page_index + 1), "-l", str(page_index + 1),
             "-r", "180", "-jpeg", "-singlefile", str(path), str(target)],
            check=True, capture_output=True, timeout=120,
        )
        rendered = target.with_suffix(".jpg")
        if not rendered.exists():
            raise RuntimeError(f"pdftoppm não gerou a página {page_index}")
        return rendered.read_bytes()


def prompt(row: dict[str, Any]) -> str:
    current = {
        "numero": row.get("numero"),
        "enunciado": row.get("enunciado"),
        "comando": row.get("comando"),
        "alternativas": row.get("alternativas"),
    }
    return f"""Você é um transcritor rigoroso de provas brasileiras. A imagem contém a página completa.
Extraia SOMENTE a questão de número {row.get('numero')}. Não resolva, corrija, resuma ou complete por conhecimento.
Preserve fórmulas, acentos e unidades. Se um trecho for realmente ilegível, use null no campo, sem inventar.
Texto compartilhado indicado para um intervalo de questões pertence ao enunciado.
Retorne exclusivamente JSON com estas chaves: numero, enunciado (array de parágrafos), comando,
alternativas (objeto A-E; valor null quando a opção for somente gráfica), confianca (0 a 1), observacoes.
Registro atual, fornecido apenas para localizar lacunas e nunca para ser copiado sem confirmação visual:
{json.dumps(current, ensure_ascii=False)}"""


def request_groq(row: dict[str, Any], image: bytes, retries: int = 5) -> dict[str, Any]:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY ausente")
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt(row)},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(image).decode()}},
        ]}],
        "temperature": 0.01,
        "max_completion_tokens": 3000,
        "response_format": {"type": "json_object"},
    }
    for attempt in range(retries):
        process = subprocess.run(
            ["curl.exe", "-sS", "-w", "\n%{http_code}", "-X", "POST", ENDPOINT,
             "-H", f"Authorization: Bearer {key}", "-H", "Content-Type: application/json",
             "-H", "User-Agent: HenryJr-Quality-Audit/1.0", "--data-binary", "@-"],
            input=json.dumps(payload), text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=150,
        )
        if process.returncode:
            if attempt == retries - 1:
                raise RuntimeError(f"Falha curl Groq: {process.stderr[:500]}")
            wait = min(90, (2 ** attempt) * 5 + random.random() * 2)
            print(f"Falha de rede Groq; aguardando {wait:.1f}s", flush=True)
            time.sleep(wait)
            continue
        raw, _, status_text = process.stdout.rpartition("\n")
        status = int(status_text or 0)
        if status >= 400:
                if status not in {429, 500, 502, 503, 504} or attempt == retries - 1:
                    raise RuntimeError(f"Groq HTTP {status}: {raw[:500]}")
                wait = min(90, (2 ** attempt) * 5 + random.random() * 2)
                print(f"Limite/instabilidade HTTP {status}; aguardando {wait:.1f}s", flush=True)
                time.sleep(wait)
                continue
        body = json.loads(raw)
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
    raise AssertionError("retentativas esgotadas")


def request_gemini(row: dict[str, Any], image: bytes, retries: int = 5) -> dict[str, Any]:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY ausente")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(image).decode()}},
            {"text": prompt(row)},
        ]}],
        "generationConfig": {
            "temperature": 0.01, "maxOutputTokens": 3000,
            "responseMimeType": "application/json",
        },
    }
    data = json.dumps(payload).encode()
    for attempt in range(retries):
        req = urllib.request.Request(endpoint, data=data, method="POST", headers={
            "x-goog-api-key": key, "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                body = json.loads(response.read())
            content = body["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(content)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries - 1:
                raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}") from exc
            wait = min(90, (2 ** attempt) * 5 + random.random() * 2)
            print(f"Limite/instabilidade Gemini HTTP {exc.code}; aguardando {wait:.1f}s", flush=True)
            time.sleep(wait)
    raise AssertionError("retentativas esgotadas")


def validate(row: dict[str, Any], proposal: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons = []
    if str(proposal.get("numero")) != str(row.get("numero")):
        reasons.append("número divergente")
    statement = proposal.get("enunciado")
    if not isinstance(statement, list) or len(normalized(" ".join(map(str, statement)))) < 25:
        reasons.append("enunciado ausente/curto")
    command = proposal.get("comando")
    if not isinstance(command, str) or len(normalized(command)) < 8:
        reasons.append("comando ausente/curto")
    alternatives = proposal.get("alternativas")
    if not isinstance(alternatives, dict) or set(alternatives) != set(LETTERS):
        reasons.append("estrutura das alternativas inválida")
    else:
        textual = [normalized(str(alternatives[k])) for k in LETTERS if alternatives[k] is not None]
        if len(textual) >= 2 and len(textual) != len(set(textual)):
            reasons.append("alternativas repetidas")
    confidence = proposal.get("confianca")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        reasons.append("confiança inválida")
    all_text = json.dumps(proposal, ensure_ascii=False)
    if SUSPICIOUS.search(all_text):
        reasons.append("marcador suspeito")
    if MOJIBAKE.search(all_text):
        reasons.append("codificação corrompida")
    return not reasons, reasons


def verify_against_local_extraction(row: dict[str, Any], proposal: dict[str, Any]) -> list[str]:
    source_path = ROOT / "DADOS" / "json" / f"enem_{row.get('ano')}.json"
    if not source_path.exists():
        return ["extração local do PDF não encontrada"]
    try:
        source_rows = json.loads(source_path.read_text(encoding="utf-8"))
        source = next(
            item for item in source_rows
            if str(item.get("numero")) == str(row.get("numero")) and str(item.get("dia")) == str(row.get("dia"))
        )
    except (json.JSONDecodeError, StopIteration):
        return ["questão ausente na extração local do PDF"]
    source_text = " ".join([
        str(source.get("enunciado") or ""), str(source.get("comando") or ""),
        *[str(value or "") for value in (source.get("alternativas") or {}).values()],
    ])
    source_norm = normalized(source_text)
    checks: list[tuple[str, Any]] = [("comando", proposal.get("comando"))]
    checks.extend((f"enunciado[{index}]", value) for index, value in enumerate(proposal.get("enunciado") or []))
    checks.extend((f"alternativa {letter}", value) for letter, value in (proposal.get("alternativas") or {}).items())
    failures = []
    for label, value in checks:
        candidate = normalized(str(value or ""))
        if candidate and candidate not in source_norm:
            failures.append(f"{label} não confirmado na extração local do PDF")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items", type=int, default=5)
    parser.add_argument("--delay", type=float, default=65)
    parser.add_argument("--provider", choices=("gemini", "groq"), default="gemini")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.max_items < 1 or args.max_items > 100:
        raise SystemExit("--max-items deve estar entre 1 e 100")
    load_env()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or ROOT / "reports" / f"ai_pdf_proposals_{stamp}.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    already = set()
    if output.exists():
        for line in output.read_text(encoding="utf-8").splitlines():
            try:
                already.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                pass
    rows = [row for row in candidates() if row["id"] not in already][:args.max_items]
    selected_model = GEMINI_MODEL if args.provider == "gemini" else MODEL
    print(f"Candidatos selecionados: {len(rows)}; modelo: {selected_model}")
    for index, row in enumerate(rows, 1):
        record: dict[str, Any] = {
            "id": row["id"], "fonte": row.get("fonte"), "ano": row.get("ano"),
            "dia": row.get("dia"), "numero": row.get("numero"), "pagina_pdf": row.get("pagina_pdf"),
            "issues": row["_issues"], "model": selected_model,
        }
        try:
            image = render_page(Path(row["_pdf"]), int(row["pagina_pdf"]))
            proposal = request_gemini(row, image) if args.provider == "gemini" else request_groq(row, image)
            valid, reasons = validate(row, proposal)
            reasons.extend(verify_against_local_extraction(row, proposal))
            valid = not reasons
            record.update({"status": "proposed" if valid else "rejected", "validation": reasons, "proposal": proposal})
        except Exception as exc:
            record.update({"status": "error", "error": str(exc)[:1000]})
        with output.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[{index}/{len(rows)}] id={row['id']} q={row.get('numero')}: {record['status']}", flush=True)
        if index < len(rows):
            time.sleep(args.delay)
    print(f"Propostas: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
