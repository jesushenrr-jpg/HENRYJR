"""Gera ZIP rastreável para extração manual no ChatGPT.

Inclui PDFs originais deduplicados, PNGs das páginas-alvo, manifesto JSON e
prompt. O banco é acessado somente para leitura.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_question_quality import fetch_questions, inspect  # noqa: E402


def pdf_for(row: dict[str, Any]) -> Path | None:
    if row.get("fonte") == "ENEM" and row.get("tipo") == "PROVA":
        path = ROOT / "DADOS" / "PROVAS" / str(row.get("ano")) / f"{row.get('dia')}.pdf"
        return path if path.exists() else None
    return None


def existing_batch_ids() -> set[int]:
    ids: set[int] = set()
    stage_root = ROOT / "tmp" / "manual_extraction"
    if not stage_root.exists():
        return ids
    for manifest_path in stage_root.glob("*/manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            ids.update(int(item["id"]) for item in manifest.get("items", []))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    return ids


def select(limit: int, excluded_ids: set[int] | None = None) -> list[dict[str, Any]]:
    excluded_ids = excluded_ids or set()
    result = []
    for row in fetch_questions():
        if int(row["id"]) in excluded_ids:
            continue
        if "statement_missing" not in {item["code"] for item in inspect(row)}:
            continue
        pdf = pdf_for(row)
        if not pdf or not isinstance(row.get("pagina_pdf"), int):
            continue
        result.append({**row, "_pdf": pdf})
        if len(result) == limit:
            break
    return result


def prompt_text() -> str:
    return """TAREFA: extração literal e auditável de questões de vestibular.

1. Descompacte o ZIP e leia manifest.json antes de começar.
2. Processe SOMENTE as questões listadas no manifesto. Use primeiro o PNG da página-alvo e consulte o PDF correspondente quando precisar de contexto.
3. Transcreva literalmente; não resolva, resuma, corrija ou complete por conhecimento.
4. Texto compartilhado indicado para um intervalo de questões pertence ao campo enunciado.
5. Separe:
   - enunciado: contexto/texto-base, como array de parágrafos;
   - comando: pergunta ou instrução respondida pelas alternativas;
   - alternativas: objeto A-E. Use null apenas quando a alternativa for exclusivamente gráfica;
   - observacoes: descreva elementos visuais necessários para compreender a questão.
6. Preserve acentos, fórmulas, unidades, referências e pontuação. Não inclua cabeçalhos, rodapés ou conteúdo de questões vizinhas.
7. Se qualquer trecho estiver ilegível ou a questão não estiver na página indicada, marque status="revisar" e explique; não invente.
8. Crie para download um único arquivo resultado.json em UTF-8. Não entregue somente um bloco de código na conversa.

Formato obrigatório de resultado.json:
{
  "schema_version": "henryjr-question-extraction-v1",
  "items": [
    {
      "id": 123,
      "fonte": "ENEM",
      "ano": 2010,
      "dia": "dia2",
      "numero": 153,
      "pagina_pdf": 24,
      "status": "extraido|revisar",
      "enunciado": ["parágrafo 1"],
      "comando": "texto",
      "alternativas": {"A": "texto ou null", "B": "...", "C": "...", "D": "...", "E": "..."},
      "observacoes": "texto ou null"
    }
  ]
}

Antes de finalizar, confirme que existe exatamente um item para cada ID do manifesto, sem IDs adicionais ou repetidos.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--batch", default="batch_001")
    parser.add_argument(
        "--include-existing-batches", action="store_true",
        help="permite repetir IDs que já constam de manifestos locais",
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        raise SystemExit("--limit deve estar entre 1 e 20")
    excluded_ids = set() if args.include_existing_batches else existing_batch_ids()
    rows = select(args.limit, excluded_ids)
    output_root = ROOT / "output" / "quality_batches"
    stage = ROOT / "tmp" / "manual_extraction" / args.batch
    if stage.exists():
        raise SystemExit(f"diretório de lote já existe: {stage}; use outro --batch")
    (stage / "pdfs").mkdir(parents=True)
    (stage / "pages").mkdir(parents=True)
    pdf_names: dict[Path, str] = {}
    items = []
    for row in rows:
        pdf: Path = row["_pdf"]
        if pdf not in pdf_names:
            name = f"enem_{row['ano']}_{row['dia']}.pdf"
            pdf_names[pdf] = name
            shutil.copy2(pdf, stage / "pdfs" / name)
        page_index = int(row["pagina_pdf"])
        page_name = f"id_{row['id']}_q{row['numero']}_pagina_{page_index + 1}.png"
        target = stage / "pages" / Path(page_name).stem
        subprocess.run(
            ["pdftoppm", "-f", str(page_index + 1), "-l", str(page_index + 1),
             "-r", "180", "-png", "-singlefile", str(pdf), str(target)],
            check=True, capture_output=True, timeout=120,
        )
        items.append({
            "id": row["id"], "fonte": row.get("fonte"), "ano": row.get("ano"),
            "dia": row.get("dia"), "numero": row.get("numero"),
            "pagina_pdf": page_index, "pagina_humana": page_index + 1,
            "pdf": f"pdfs/{pdf_names[pdf]}", "pagina_renderizada": f"pages/{page_name}",
            "problemas": [item["code"] for item in inspect(row)],
        })
    manifest = {"schema_version": "henryjr-manifest-v1", "count": len(items), "items": items}
    (stage / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (stage / "PROMPT_CHATGPT.txt").write_text(prompt_text(), encoding="utf-8")
    output_root.mkdir(parents=True, exist_ok=True)
    zip_path = output_root / f"{args.batch}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(stage))
    print(json.dumps({
        "zip": str(zip_path), "questions": len(items), "pdfs": len(pdf_names),
        "bytes": zip_path.stat().st_size, "ids": [item["id"] for item in items],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
