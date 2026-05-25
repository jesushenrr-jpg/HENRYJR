"""
config.py — Lê e escreve config.json próximo ao executável.

Quando frozen pelo PyInstaller: config.json fica em sys.executable/../config.json
Quando rodando como script: config.json fica em __file__/../config.json
"""
import json
import sys
from pathlib import Path


def _config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "config.json"
    return Path(__file__).parent / "config.json"


def carregar() -> dict:
    """Retorna dict com 'url' e 'key', ou {} se não existir."""
    p = _config_path()
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar(url: str, key: str) -> None:
    """Persiste as credenciais em config.json."""
    p = _config_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"url": url.strip(), "key": key.strip()}, f, indent=2)


def credenciais_ok() -> bool:
    """True se config.json existe e tem url + key não-vazios."""
    c = carregar()
    return bool(c.get("url") and c.get("key"))
