"""Diagnóstico rápido das imagens 2010 e 2021."""
import json, os, glob, urllib.request

BASE = "C:/PROJETOS/HENRYJR/DADOS"

for ano in [2010, 2021]:
    with open(f"{BASE}/json_v2/enem_{ano}.json", encoding="utf-8") as f:
        qs = json.load(f)

    on_disk, off_disk, no_url_bad = [], [], []
    for q in qs:
        if not (q.get("tem_imagem") and q.get("imagens")):
            continue
        p = q["imagens"][0].get("path", "")
        full = f"{BASE}/imagens/{p}"
        url  = q["imagens"][0].get("supabase_url", "")
        if os.path.exists(full):
            on_disk.append(q["numero"])
        else:
            off_disk.append(q["numero"])

    print(f"\n=== {ano} ===")
    print(f"  Com imagem: {len(on_disk)+len(off_disk)}")
    print(f"  No disco  : {len(on_disk)}")
    print(f"  Faltando  : {len(off_disk)}")
    print(f"  Faltando (primeiros 10): {off_disk[:10]}")

print("\nDone.")
