"""
Item 7: Marcar questões anuladas em todos os JSONs v2 e sincronizar com Supabase.

Questões anuladas conhecidas:
  2018: Q150
  2020: Q114, Q141
  2021: Q178
  2022: Q175
  2023: Q177
  2024: Q129
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

# Mapa de questões anuladas: {ano: [numeros]}
ANULADAS = {
    2018: [150],
    2020: [114, 141],
    2021: [178],
    2022: [175],
    2023: [177],
    2024: [129],
}

corrigidas = 0
erros = 0

for ano, numeros in ANULADAS.items():
    json_path = f"{BASE}/json_v2/enem_{ano}.json"
    if not os.path.exists(json_path):
        print(f"[{ano}] JSON nao encontrado")
        continue

    with open(json_path, encoding='utf-8') as f:
        qs = json.load(f)

    modificado = False
    for q in qs:
        if q['numero'] in numeros:
            antes_anulada = q.get('anulada', False)
            antes_gabarito = q.get('gabarito')
            q['anulada'] = True
            q['gabarito'] = None  # anuladas nao tem gabarito
            modificado = True
            print(f"  [{ano}] Q{q['numero']} dia={q['dia']} anulada=True gabarito={antes_gabarito}->{q['gabarito']}")

            # Sincronizar com Supabase
            url = f"{SUPA_URL}/rest/v1/questoes"
            params = {"ano": f"eq.{ano}", "dia": f"eq.{q['dia']}", "numero": f"eq.{q['numero']}"}
            updates = {"anulada": True, "gabarito": None}
            r = requests.patch(url, params=params, json=updates, headers=HEADERS, timeout=15)
            if r.status_code in (200, 204):
                corrigidas += 1
                print(f"    Sync OK")
            else:
                erros += 1
                print(f"    Sync ERRO {r.status_code}: {r.text[:100]}")
            time.sleep(0.05)

    if modificado:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(qs, f, ensure_ascii=False, indent=2)
        print(f"  [{ano}] JSON salvo.")

print(f"\nRESUMO: corrigidas={corrigidas} | erros={erros}")
