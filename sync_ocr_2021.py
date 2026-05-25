"""Sincroniza questões de 2021 com OCR extraído para o Supabase (sem campo ocr)."""
import json, requests, time

BASE     = "C:/PROJETOS/HENRYJR/DADOS"
SUPA_URL = "https://bmhudlpihwxvaelokugh.supabase.co"
SUPA_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtaHVkbHBpaHd4dmFlbG9rdWdoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMwNDAzOSwiZXhwIjoyMDkxODgwMDM5fQ.KucpbBiIhjPKQCEBIdV8sGuDw_F5CZdXWlZy39h-I7M"

HEADERS = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

with open(f"{BASE}/json_v2/enem_2021.json", encoding='utf-8') as f:
    qs = json.load(f)

synced = errors = 0
for q in qs:
    if not q.get('ocr'):
        continue
    url = f"{SUPA_URL}/rest/v1/questoes"
    params = {"ano": f"eq.{q['ano']}", "dia": f"eq.{q['dia']}", "numero": f"eq.{q['numero']}"}
    # Nao incluir campo 'ocr' — nao existe na tabela Supabase
    updates = {
        'enunciado': q['enunciado'],
        'alternativas': q.get('alternativas', {}),
    }
    r = requests.patch(url, params=params, json=updates, headers=HEADERS, timeout=15)
    if r.status_code in (200, 204):
        synced += 1
    else:
        errors += 1
        print(f"  ERRO {r.status_code} Q{q['numero']}: {r.text[:120]}")
    time.sleep(0.02)

print(f"\nSincronizadas: {synced} | Erros: {errors}")
