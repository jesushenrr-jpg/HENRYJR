"""Compara campos de resultados manuais com o texto da página oficial."""

from __future__ import annotations

import argparse
import io
import json
import re
import unicodedata
import zipfile
from pathlib import Path

from pypdf import PdfReader


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("−", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).strip()


def fragments(item: dict) -> list[tuple[str, str]]:
    values = [(f"enunciado[{index}]", str(value)) for index, value in enumerate(item["enunciado"])]
    values.append(("comando", str(item["comando"])))
    values.extend((f"alternativa.{key}", str(value)) for key, value in item["alternativas"].items() if value)
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("batch_zip", type=Path)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8-sig"))
    with zipfile.ZipFile(args.batch_zip) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        by_id = {int(item["id"]): item for item in manifest["items"]}
        readers: dict[str, PdfReader] = {}
        output = []
        for item in result["items"]:
            reference = by_id[int(item["id"])]
            pdf_name = reference["pdf"]
            if pdf_name not in readers:
                readers[pdf_name] = PdfReader(io.BytesIO(archive.read(pdf_name)))
            page_text = norm(readers[pdf_name].pages[int(item["pagina_pdf"])].extract_text() or "")
            misses = []
            for label, value in fragments(item):
                normalized = norm(value)
                if normalized and normalized not in page_text:
                    misses.append({"field": label, "preview": value[:120]})
            output.append({"id": item["id"], "misses": misses})
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
