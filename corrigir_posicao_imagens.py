"""
Corrige o campo 'posicao' ausente em todas as entradas de imagens nos JSONs v2.
Depois sincroniza o campo 'imagens' atualizado para o Supabase via REST API.

Problema: CardQuestao.tsx exige img.posicao === 'antes_1' para exibir imagens.
Todas as 751 entradas estão sem o campo posicao → NENHUMA imagem aparece na plataforma.

Este script:
  1. Adiciona "posicao": "antes_1" a cada dict de imagem nos JSONs v2
  2. Salva os JSONs localmente
  3. Sincroniza o campo 'imagens' atualizado para o Supabase (questoes table)
"""

import json, os, glob, requests, time

BASE     = "C:/PROJETOS/HENRYJR/DADOS"
SUPA_URL = "https://bmhudlpihwxvaelokugh.supabase.co"
SUPA_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJtaHVkbHBpaHd4dmFlbG9rdWdoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjMwNDAzOSwiZXhwIjoyMDkxODgwMDM5fQ.KucpbBiIhjPKQCEBIdV8sGuDw_F5CZdXWlZy39h-I7M"

HEADERS = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def patch_questao(ano, dia, numero, imagens):
    """Atualiza o campo imagens de uma questão no Supabase."""
    url = f"{SUPA_URL}/rest/v1/questoes"
    params = {
        "ano": f"eq.{ano}",
        "dia": f"eq.{dia}",
        "numero": f"eq.{numero}"
    }
    payload = {"imagens": imagens}
    r = requests.patch(url, params=params, json=payload, headers=HEADERS, timeout=15)
    return r.status_code

total_fixed_local = 0
total_synced = 0
total_errors = 0

json_files = sorted(glob.glob(f"{BASE}/json_v2/enem_*.json"))
print(f"Encontrados {len(json_files)} arquivos JSON v2.\n")

for jf in json_files:
    ano = int(os.path.basename(jf).replace("enem_", "").replace(".json", ""))
    with open(jf, encoding="utf-8") as f:
        qs = json.load(f)

    modified = False
    questoes_para_sync = []

    for q in qs:
        if not (q.get("tem_imagem") and q.get("imagens")):
            continue
        changed = False
        for img in q["imagens"]:
            if "posicao" not in img:
                img["posicao"] = "antes_1"
                changed = True
        if changed:
            total_fixed_local += 1
            modified = True
            questoes_para_sync.append(q)

    if modified:
        with open(jf, "w", encoding="utf-8") as f:
            json.dump(qs, f, ensure_ascii=False, indent=2)
        print(f"  [{ano}] JSON salvo — {len(questoes_para_sync)} questões corrigidas localmente.")

        # Sincronizar com Supabase
        print(f"  [{ano}] Sincronizando {len(questoes_para_sync)} questões com Supabase...")
        for q in questoes_para_sync:
            status = patch_questao(q["ano"], q["dia"], q["numero"], q["imagens"])
            if status in (200, 204):
                total_synced += 1
            else:
                total_errors += 1
                print(f"    ERRO {status} — {ano} {q['dia']} Q{q['numero']}")
            time.sleep(0.02)  # evitar rate limit
    else:
        print(f"  [{ano}] Sem alterações necessárias.")

print(f"\n{'='*50}")
print(f"RESUMO:")
print(f"  Questões corrigidas localmente : {total_fixed_local}")
print(f"  Sincronizadas no Supabase      : {total_synced}")
print(f"  Erros de sync                  : {total_errors}")
print(f"{'='*50}")
print("\nDone. Imagens agora têm campo 'posicao' e devem aparecer no CardQuestao.")
