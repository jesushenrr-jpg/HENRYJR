# -*- coding: utf-8 -*-
import os, sys, shutil, json, io
from datetime import date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ORIGEM = r"C:\PROJETOS\HENRYJR\DADOS\\EXATO_SIMULADOS"
DESTINO = r"C:\PROJETOS\HENRYJR\DADOS\EXATO_ORGANIZADO"

reais = sorted([f for f in os.listdir(ORIGEM) if f.endswith(".pdf")])

def achar(contem=None, nao_contem=None, starts=None):
    result = []
    for f in reais:
        ok = True
        if starts and not f.startswith(starts): ok = False
        if ok and contem:
            for c in (contem if isinstance(contem, list) else [contem]):
                if c not in f: ok = False; break
        if ok and nao_contem:
            for c in (nao_contem if isinstance(nao_contem, list) else [nao_contem]):
                if c in f: ok = False; break
        if ok: result.append(f)
    return result

print("Verificando arquivos chave...")
for f in achar(contem=["CICLO ZERO", "MAN"], nao_contem=["(","Gabarito"]):
    print("  CZ_MANHA_SIM:", f)
for f in achar(contem=["Gabarito Comentado CICLO ZERO", "MAN"], nao_contem=["("]):
    print("  CZ_MANHA_GAB:", f)
for f in achar(contem=["Simulado EXATO", "MAN"], nao_contem=["(","OUTUBRO","CICLO","NATUREZAS","OFICIAL","TRADICIONAIS"]):
    print("  1SIM_MANHA:", f)
for f in achar(contem=["GAB EXATO", "MAN", "REVISADO"], nao_contem=["(1)","(2)"]):
    print("  OUT_MANHA_GAB:", f)

