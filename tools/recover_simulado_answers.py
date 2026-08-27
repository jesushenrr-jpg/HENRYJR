"""Recupera gabaritos de simulados a partir de PDFs locais de resolução.

O modo padrão apenas gera relatório. Gravação exige ``--apply --confirm APPLY``
e só ocorre quando há um único registro no banco e uma única resposta consistente.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_question_quality import fetch_questions, load_env  # noqa: E402


def ascii_text(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).lower()


def resolution_pdfs() -> list[Path]:
    result = []
    for path in (ROOT / "DADOS" / "ENEM_SIMULADOS").rglob("*.pdf"):
        name = ascii_text(path.name)
        if any(token in name for token in ("gab", "resolu", "respost")):
            result.append(path)
    return result


def day_matches(name: str, day: int) -> bool:
    patterns = [
        rf"dia\s*0?{day}\b", rf"\bd{day}\b", rf"\b{day}\s*dia\b",
        rf"\b{day}o\s*dia\b", rf"prova\s*{'i' if day == 1 else 'ii'}\b",
    ]
    return any(re.search(pattern, name) for pattern in patterns)


def path_score(path: Path, provider: str, year: int, sim: int, day: int) -> int:
    full = ascii_text(str(path))
    score = 0
    aliases = {
        "BERNOULLI": ["bernoulli", "berno"], "SAS": ["sas"],
        "POLIEDRO": ["poliedro"], "SOMOS": ["somos"],
        "FARIAS_BRITO": ["farias brito", "fb"],
    }
    if any(alias in full for alias in aliases.get(provider, [provider.lower()])):
        score += 4
    if str(year) in full:
        score += 3
    if re.search(rf"(?:simulado|simu|sas|somos|ciclo|fb|volume|vol)[^0-9]{{0,8}}0?{sim}\b", full):
        score += 5
    if day_matches(ascii_text(path.name), day):
        score += 5
    return score


def find_pdf(provider: str, year: int, sim: int, day: int, pdfs: list[Path]) -> Path | None:
    ranked = sorted(((path_score(p, provider, year, sim, day), p) for p in pdfs), reverse=True)
    if not ranked or ranked[0][0] < 14:
        return None
    if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
        return None
    return ranked[0][1]


QUESTION = re.compile(r"(?:QUEST[AÃ]O|Quest[aã]o)\s*0?(\d{1,3})\b", re.I)
DIRECT = re.compile(r"(?:Resposta(?:\s+correta)?|Alternativa)\s*:?[ \t]*([A-E])\b", re.I)


def parse_answers(path: Path) -> dict[int, set[str]]:
    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)
    markers = list(QUESTION.finditer(text))
    answers: dict[int, set[str]] = defaultdict(set)
    for index, marker in enumerate(markers):
        number = int(marker.group(1))
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        segment = text[marker.end():end]
        found = DIRECT.search(segment)
        if found:
            answers[number].add(found.group(1).upper())
    # Formato compacto: "01. Resposta correta: C"
    for number, answer in re.findall(r"(?m)^\s*0?(\d{1,3})\.\s*Resposta\s+correta:\s*([A-E])\b", text, re.I):
        answers[int(number)].add(answer.upper())
    return answers


def build() -> dict[str, Any]:
    pdfs = resolution_pdfs()
    live_index: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in fetch_questions():
        if row.get("fonte") == "ENEM" and row.get("tipo") == "SIMULADO":
            live_index[(row.get("provedor"), row.get("ano"), row.get("dia"), row.get("evento"), row.get("numero"))].append(row)

    files = []
    candidates = []
    for json_path in sorted((ROOT / "DADOS" / "json_enem_simulados").glob("*.json")):
        match = re.match(r"(.+?)_(20\d{2})_SIM_(\d+)_simu_dia([12])\.json", json_path.name, re.I)
        if not match:
            continue
        provider = match.group(1).upper()
        year, sim, day = map(int, match.groups()[1:])
        pdf = find_pdf(provider, year, sim, day, pdfs)
        if not pdf:
            files.append({"json": json_path.name, "status": "pdf_not_unique"})
            continue
        answers = parse_answers(pdf)
        local_rows = json.loads(json_path.read_text(encoding="utf-8"))
        compared = matched = 0
        provisional = []
        for local in local_rows:
            number = int(local.get("numero") or 0)
            choices = answers.get(number, set())
            if len(choices) != 1:
                continue
            answer = next(iter(choices))
            key = (provider, year, f"simu_dia{day}", f"SIM_{sim:02d}", number)
            live = live_index.get(key, [])
            if len(live) != 1:
                continue
            known = live[0].get("gabarito") or local.get("gabarito")
            if known:
                compared += 1
                matched += str(known).upper() == answer
                continue
            provisional.append({
                "id": live[0]["id"], "provedor": provider, "ano": year,
                "evento": f"SIM_{sim:02d}", "dia": f"simu_dia{day}",
                "numero": number, "gabarito": answer, "pdf": str(pdf.relative_to(ROOT)),
            })
        accuracy = matched / compared if compared else None
        trusted = compared >= 5 and accuracy is not None and accuracy >= 0.98
        if trusted:
            candidates.extend(provisional)
        files.append({
            "json": json_path.name, "pdf": str(pdf.relative_to(ROOT)), "answers": len(answers),
            "compared": compared, "matched": matched, "accuracy": accuracy,
            "trusted": trusted, "candidates": len(provisional) if trusted else 0,
            "withheld": 0 if trusted else len(provisional),
        })
    return {
        "summary": {
            "files_mapped": sum("pdf" in f for f in files),
            "files_unmapped": sum("pdf" not in f for f in files),
            "answer_candidates": len(candidates),
            "trusted_files": sum(bool(f.get("trusted")) for f in files),
            "withheld_candidates": sum(int(f.get("withheld", 0)) for f in files),
        },
        "files": files, "candidates": candidates,
    }


def apply(report: dict[str, Any]) -> None:
    load_env()
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (ROOT / "reports" / f"simulado_answers_backup_{stamp}.json").write_text(
        json.dumps(report["candidates"], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for candidate in report["candidates"]:
        query = urllib.parse.urlencode({"id": f"eq.{candidate['id']}"})
        request = urllib.request.Request(
            f"{base}/rest/v1/questoes?{query}",
            data=json.dumps({"gabarito": candidate["gabarito"]}).encode(),
            method="PATCH", headers=headers,
        )
        with urllib.request.urlopen(request, timeout=30):
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "simulado_answers.json")
    args = parser.parse_args()
    report = build()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    if args.apply:
        if args.confirm != "APPLY":
            raise SystemExit("Use --confirm APPLY")
        apply(report)
        print("Gabaritos aplicados com backup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
