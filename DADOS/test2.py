# -*- coding: utf-8 -*-
import os, sys, shutil, json, io
from datetime import date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ORIGEM = r"C:\PROJETOS\HENRYJR\DADOS\\EXATO_SIMULADOS"
DESTINO = r"C:\PROJETOS\HENRYJR\DADOS\EXATO_ORGANIZADO"
reais = sorted([f for f in os.listdir(ORIGEM) if f.endswith(".pdf")])

def achar(contem=None, nao_contem=None):
    result = []
    for f in reais:
        ok = True
        if contem:
            for c in (contem if isinstance(contem, list) else [contem]):
                if c not in f: ok = False; break
        if ok and nao_contem:
            for c in (nao_contem if isinstance(nao_contem, list) else [nao_contem]):
                if c in f: ok = False; break
        if ok: result.append(f)
    return result

print("Verificando matches...")
r = achar(['CICLO ZERO', 'ANH'], ['(', 'Gabarito'])
print("  CZ_MS_SIM:", r)
r = achar(['CICLO ZERO', 'TARDE'], ['(', 'Gabarito'])
print("  CZ_T_SIM:", r)
r = achar(['Gabarito Comentado CICLO ZERO', 'ANH'], ['('])
print("  CZ_MS_GAB:", r)
r = achar(['Gabarito Comentado CICLO ZERO', 'TARDE'], ['('])
print("  CZ_T_GAB:", r)
