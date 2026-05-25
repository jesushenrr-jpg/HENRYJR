"""
Sincroniza o campo pagina_pdf de todos os JSONs v2 para o Supabase.
Só atualiza questões onde pagina_pdf é diferente do que está no Supabase.
"""

import json, glob, os, requests, time

BASE     = "C:/PROJETOS/HENRYJR/DADOS"
SUPA_URL = "https://bmhudlpihwxvaelokugh.supabase.co"
SUPA_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtaHVkbHBpaHd4dmFlbG9rdWdoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMwNDAzOSwiZXhwIjoyMDkxODgwMDM5fQ.KucpbBiIhjPKQCEBIdV8sGuDw_F5CZdXWlZy39h-I7M"

HEADERS = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

total_updated = 0
total_skip = 0
total_error = 0

json_files = sorted(glob.glob(f"{BASE}/json_v2/enem_*.json"))
print(f"Processando {len(json_files)} arquivos JSON...")

for jf in json_files:
    ano = int(os.path.basename(jf).replace("enem_", "").replace(".json", ""))
    with open(jf, encoding="utf-8") as f:
        qs = json.load(f)

    qs_com_pagina = [q for q in qs if q.get("pagina_pdf") is not None]
    print(f"  [{ano}] {len(qs_com_pagina)} questões com pagina_pdf -> sincronizando...", end=" ")

    ano_updated = 0
    for q in qs_com_pagina:
        url = f"{SUPA_URL}/rest/v1/questoes"
        params = {"ano": f"eq.{q['ano']}", "dia": f"eq.{q['dia']}", "numero": f"eq.{q['numero']}"}
        updates = {"pagina_pdf": q["pagina_pdf"]}
        r = requests.patch(url, params=params, json=updates, headers=HEADERS, timeout=15)
        if r.status_code in (200, 204):
            ano_updated += 1
            total_updated += 1
        else:
            total_error += 1
        time.sleep(0.01)

    print(f"OK ({ano_updated})")

print(f"\nRESUMO: atualizadas={total_updated} | erros={total_error}")
