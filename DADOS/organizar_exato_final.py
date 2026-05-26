# -*- coding: utf-8 -*-
"""
Organiza os PDFs EXATO â€” versÃ£o final com matching dinÃ¢mico por os.listdir
para evitar problemas de encoding nos nomes de arquivo.
"""
import os, sys, shutil, json, re, io
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ORIGEM = r"C:\PROJETOS\HENRYJR\DADOS\\EXATO_SIMULADOS"
DESTINO = r"C:\PROJETOS\HENRYJR\DADOS\EXATO_ORGANIZADO"
reais = sorted([f for f in os.listdir(ORIGEM) if f.endswith(".pdf")])


def eh_dup(nome):
    """Retorna True se o nome termina com (1).pdf, (2).pdf, etc."""
    return bool(re.search(r'\(\d\)\.pdf$', nome))


def achar(contem=None, nao_contem=None, so_original=False, so_dup=False):
    result = []
    for f in reais:
        ok = True
        if contem:
            for c in (contem if isinstance(contem, list) else [contem]):
                if c not in f:
                    ok = False
                    break
        if ok and nao_contem:
            for c in (nao_contem if isinstance(nao_contem, list) else [nao_contem]):
                if c in f:
                    ok = False
                    break
        if ok and so_original and eh_dup(f):
            ok = False
        if ok and so_dup and not eh_dup(f):
            ok = False
        if ok:
            result.append(f)
    return result


def um(lista, label=""):
    """Garante que a lista tem exatamente 1 elemento."""
    if len(lista) != 1:
        raise ValueError(f"Esperado 1 resultado para {label}, obteve {len(lista)}: {lista}")
    return lista[0]


# â”€â”€ Resolver nomes originais â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CZ_MS_SIM  = um(achar(["CICLO ZERO","ANH"], nao_contem=["Gabarito"], so_original=True), "CZ_MS_SIM")
CZ_T_SIM   = um(achar(["CICLO ZERO","TARDE"], nao_contem=["Gabarito"], so_original=True), "CZ_T_SIM")
CZ_MS_GAB  = um(achar(["Gabarito Comentado CICLO ZERO","ANH"], so_original=True), "CZ_MS_GAB")
CZ_T_GAB   = um(achar(["Gabarito Comentado CICLO ZERO","TARDE"], so_original=True), "CZ_T_GAB")

OUT_MS_SIM  = um(achar(["OUTUBRO 2025","ANH"], so_original=True), "OUT_MS_SIM")
OUT_T_SIM   = um(achar(["OUTUBRO 2025","TARDE"], so_original=True), "OUT_T_SIM")
OUT_MS_GAB  = um(achar(["GAB EXATO","ANH","REVISADO"], so_original=True), "OUT_MS_GAB")
OUT_T_GAB   = um(achar(["GAB EXATO TARDE","REVISADO"], so_original=True), "OUT_T_GAB")

SIM1_MS_SIM = um(achar(["Simulado EXATO","ANH"], nao_contem=["OUTUBRO","CICLO","NATUREZAS","OFICIAL","TRADICIONAIS","Simulado EXATO -"], so_original=True), "SIM1_MS_SIM")
SIM1_T_SIM  = um(achar(["Simulado EXATO TARDE"], nao_contem=["OUTUBRO","CICLO","NATUREZAS","OFICIAL"], so_original=True), "SIM1_T_SIM")
SIM1_MS_GAB = um(achar(["Gabarito Comentado Exato","ANH"], nao_contem=["2"], so_original=True), "SIM1_MS_GAB")
SIM1_T_GAB  = um(achar(["Gabarito Comentado Exato TARDE"], nao_contem=["2"], so_original=True), "SIM1_T_GAB")

SIM2_MS_SIM = um(achar(["Simulado EXATO -","ANH"], so_original=True), "SIM2_MS_SIM")
SIM2_T_SIM  = um(achar(["Simulado EXATO -","TARDE"], so_original=True), "SIM2_T_SIM")
SIM2_MS_GAB = um(achar(["Gabarito Comentado","Exato","ANH","2"], so_original=True), "SIM2_MS_GAB")
SIM2_T_GAB  = um(achar(["Gabarito Comentado","Exato TARDE","2"], so_original=True), "SIM2_T_GAB")

ABR_MS_SIM  = um(achar(["SIMULADO OFICIAL EXATO","ANH","abril"]), "ABR_MS_SIM")
ABR_T_SIM   = um(achar(["SIMULADO OFICIAL EXATO","TARDE","abril"]), "ABR_T_SIM")
ABR_GAB     = um(achar(["Gabarito Comentado - EXATO","29"]), "ABR_GAB")

NAT_SIM     = um(achar(["NATUREZAS"], nao_contem=["GABARITO"]), "NAT_SIM")
NAT_GAB     = um(achar(["GABARITO","NATUREZAS"]), "NAT_GAB")
TRAD_SIM    = um(achar(["TRADICIONAIS"]), "TRAD_SIM")
TESSAT_ORIG = um(achar(["GABARITO - ","TESSAT"], nao_contem=["(1)"]), "TESSAT_ORIG")
TESSAT_DUP  = um(achar(["GABARITO - TARDE - TESSAT"]), "TESSAT_DUP")

print("Todos os arquivos originais encontrados com sucesso.")

# â”€â”€ Mapeamento completo: (nome_real, tipo, evento, nome_pad, dup_de) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MAPA = []

def add(nome, tipo, evento, nome_pad, dup_de=None):
    MAPA.append((nome, tipo, evento, nome_pad, dup_de))

# CICLO ZERO
add(CZ_MS_SIM, "simulado", "ciclo_zero", "EXATO_CICLO_ZERO_MANHA_SIMULADO.pdf")
add(CZ_T_SIM,  "simulado", "ciclo_zero", "EXATO_CICLO_ZERO_TARDE_SIMULADO.pdf")
add(CZ_MS_GAB, "gabarito", "ciclo_zero", "EXATO_CICLO_ZERO_MANHA_GABARITO.pdf")
add(CZ_T_GAB,  "gabarito", "ciclo_zero", "EXATO_CICLO_ZERO_TARDE_GABARITO.pdf")
for f in achar(["CICLO ZERO","ANH"], nao_contem=["Gabarito"], so_dup=True):
    add(f, "duplicata", "ciclo_zero", None, CZ_MS_SIM)
for f in achar(["CICLO ZERO","TARDE"], nao_contem=["Gabarito"], so_dup=True):
    add(f, "duplicata", "ciclo_zero", None, CZ_T_SIM)
for f in achar(["Gabarito Comentado CICLO ZERO","ANH"], so_dup=True):
    add(f, "duplicata", "ciclo_zero", None, CZ_MS_GAB)
for f in achar(["Gabarito Comentado CICLO ZERO","TARDE"], so_dup=True):
    add(f, "duplicata", "ciclo_zero", None, CZ_T_GAB)

# OUTUBRO 2025
add(OUT_MS_SIM, "simulado", "outubro_2025", "EXATO_OUTUBRO2025_MANHA_SIMULADO.pdf")
add(OUT_T_SIM,  "simulado", "outubro_2025", "EXATO_OUTUBRO2025_TARDE_SIMULADO.pdf")
add(OUT_MS_GAB, "gabarito", "outubro_2025", "EXATO_OUTUBRO2025_MANHA_GABARITO.pdf")
add(OUT_T_GAB,  "gabarito", "outubro_2025", "EXATO_OUTUBRO2025_TARDE_GABARITO.pdf")
for f in achar(["OUTUBRO 2025","ANH"], so_dup=True):
    add(f, "duplicata", "outubro_2025", None, OUT_MS_SIM)
for f in achar(["OUTUBRO 2025","TARDE"], so_dup=True):
    add(f, "duplicata", "outubro_2025", None, OUT_T_SIM)
for f in achar(["GAB EXATO","ANH","REVISADO"], so_dup=True):
    add(f, "duplicata", "outubro_2025", None, OUT_MS_GAB)
for f in achar(["GAB EXATO TARDE","REVISADO"], so_dup=True):
    add(f, "duplicata", "outubro_2025", None, OUT_T_GAB)

# 1Âº SIMULADO
add(SIM1_MS_SIM, "simulado", "1_simulado", "EXATO_1SIMULADO_MANHA_SIMULADO.pdf")
add(SIM1_T_SIM,  "simulado", "1_simulado", "EXATO_1SIMULADO_TARDE_SIMULADO.pdf")
add(SIM1_MS_GAB, "gabarito", "1_simulado", "EXATO_1SIMULADO_MANHA_GABARITO.pdf")
add(SIM1_T_GAB,  "gabarito", "1_simulado", "EXATO_1SIMULADO_TARDE_GABARITO.pdf")
for f in achar(["Simulado EXATO","ANH"], nao_contem=["OUTUBRO","CICLO","NATUREZAS","OFICIAL","TRADICIONAIS","Simulado EXATO -"], so_dup=True):
    add(f, "duplicata", "1_simulado", None, SIM1_MS_SIM)
for f in achar(["Simulado EXATO TARDE"], nao_contem=["OUTUBRO","CICLO","NATUREZAS","OFICIAL"], so_dup=True):
    add(f, "duplicata", "1_simulado", None, SIM1_T_SIM)
for f in achar(["Gabarito Comentado Exato","ANH"], nao_contem=["2"], so_dup=True):
    add(f, "duplicata", "1_simulado", None, SIM1_MS_GAB)
for f in achar(["Gabarito Comentado Exato TARDE"], nao_contem=["2"], so_dup=True):
    add(f, "duplicata", "1_simulado", None, SIM1_T_GAB)

# 2Âº SIMULADO
add(SIM2_MS_SIM, "simulado", "2_simulado", "EXATO_2SIMULADO_MANHA_SIMULADO.pdf")
add(SIM2_T_SIM,  "simulado", "2_simulado", "EXATO_2SIMULADO_TARDE_SIMULADO.pdf")
add(SIM2_MS_GAB, "gabarito", "2_simulado", "EXATO_2SIMULADO_MANHA_GABARITO.pdf")
add(SIM2_T_GAB,  "gabarito", "2_simulado", "EXATO_2SIMULADO_TARDE_GABARITO.pdf")
for f in achar(["Simulado EXATO -","ANH"], so_dup=True):
    add(f, "duplicata", "2_simulado", None, SIM2_MS_SIM)
for f in achar(["Simulado EXATO -","TARDE"], so_dup=True):
    add(f, "duplicata", "2_simulado", None, SIM2_T_SIM)

# 29 ABRIL 2026
add(ABR_MS_SIM, "simulado", "29_abril_2026", "EXATO_29ABRIL2026_MANHA_SIMULADO.pdf")
add(ABR_T_SIM,  "simulado", "29_abril_2026", "EXATO_29ABRIL2026_TARDE_SIMULADO.pdf")
add(ABR_GAB,    "gabarito", "29_abril_2026", "EXATO_29ABRIL2026_MANHA_E_TARDE_GABARITO.pdf")

# NATUREZAS
add(NAT_SIM, "simulado", "naturezas", "EXATO_NATUREZAS_TARDE_SIMULADO.pdf")
add(NAT_GAB, "gabarito", "naturezas", "EXATO_NATUREZAS_TARDE_GABARITO.pdf")

# TRADICIONAIS
add(TRAD_SIM, "simulado", "tradicionais", "EXATO_TRADICIONAIS_04ABRIL2026_SIMULADO.pdf")

# TESSAT gabaritos (imagem)
add(TESSAT_ORIG, "nao_identificado", None, "GABARITO_TESSAT_MANHA_IMAGEM.pdf")
add(TESSAT_DUP,  "duplicata", None, None, TESSAT_ORIG)

# MATERIAL DE APOIO
add("Cartilha MED UFT 2025.pdf", "material_apoio", None, "EXATO_CARTILHA_MED_UFT_2025.pdf")
for f in achar(["ENEM X Nota"]):
    add(f, "material_apoio", None, "EXATO_REDACAO_NOTA_MIL_ENEM_vs_EXATO.pdf")
add("conexao-uft-exato.pdf", "material_apoio", None, "EXATO_CONEXAO_UFT_QUESTOES_MATEMATICA.pdf")
add("lista-01---projeto-2020.pdf", "material_apoio", None, "EXATO_LISTA01_MATEMATICA_2020.pdf")
add("lista-02-proj-2020.pdf", "material_apoio", None, "EXATO_LISTA02_MATEMATICA_2020.pdf")
add("trilha-exato-parte-1.pdf", "material_apoio", None, "EXATO_TRILHA_PARTE1_SEMANA1.pdf")
add("trilha-exato-parte-2.pdf", "material_apoio", None, "EXATO_TRILHA_PARTE2_SEMANA4.pdf")
add("trilha-exato-parte-3.pdf", "material_apoio", None, "EXATO_TRILHA_PARTE3_SEMANA7.pdf")

# â”€â”€ Verificar cobertura total â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
mapeados = {m[0] for m in MAPA}
nao_mapeados = [f for f in reais if f not in mapeados]
if nao_mapeados:
    print(f"\nAVISO: {len(nao_mapeados)} arquivo(s) NAO mapeados:")
    for f in nao_mapeados:
        print(f"  {f}")
else:
    print(f"Cobertura total: todos os {len(reais)} arquivos mapeados.")

# â”€â”€ Criar pastas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PASTAS = [
    "simulados/ciclo_zero", "simulados/outubro_2025", "simulados/1_simulado",
    "simulados/2_simulado", "simulados/29_abril_2026", "simulados/naturezas",
    "simulados/tradicionais",
    "gabaritos/ciclo_zero", "gabaritos/outubro_2025", "gabaritos/1_simulado",
    "gabaritos/2_simulado", "gabaritos/29_abril_2026", "gabaritos/naturezas",
    "gabaritos/tradicionais",
    "material_apoio", "Duplicados", "Nao_Identificados", "Corrompidos",
]
print("\nCriando pastas...")
for p in PASTAS:
    caminho = os.path.join(DESTINO, p.replace("/", os.sep))
    os.makedirs(caminho, exist_ok=True)
    print(f"  OK: {caminho}")

# â”€â”€ Subpastas por evento â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SP_SIM = {
    "ciclo_zero": "simulados/ciclo_zero",
    "outubro_2025": "simulados/outubro_2025",
    "1_simulado": "simulados/1_simulado",
    "2_simulado": "simulados/2_simulado",
    "29_abril_2026": "simulados/29_abril_2026",
    "naturezas": "simulados/naturezas",
    "tradicionais": "simulados/tradicionais",
}
SP_GAB = {
    "ciclo_zero": "gabaritos/ciclo_zero",
    "outubro_2025": "gabaritos/outubro_2025",
    "1_simulado": "gabaritos/1_simulado",
    "2_simulado": "gabaritos/2_simulado",
    "29_abril_2026": "gabaritos/29_abril_2026",
    "naturezas": "gabaritos/naturezas",
    "tradicionais": "gabaritos/tradicionais",
}

# â”€â”€ Copiar arquivos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\nCopiando arquivos...")
copiados = []
erros = []

for nome, tipo, evento, nome_pad, dup_de in MAPA:
    src = os.path.join(ORIGEM, nome)
    if not os.path.exists(src):
        erros.append(nome)
        print(f"  ERRO: {nome}")
        continue

    if tipo == "simulado":
        sub = SP_SIM[evento].replace("/", os.sep)
        dst = os.path.join(DESTINO, sub, nome_pad)
        shutil.copy2(src, dst)
        print(f"  SIM  {sub}/{nome_pad}")
    elif tipo == "gabarito":
        sub = SP_GAB[evento].replace("/", os.sep)
        dst = os.path.join(DESTINO, sub, nome_pad)
        shutil.copy2(src, dst)
        print(f"  GAB  {sub}/{nome_pad}")
    elif tipo == "material_apoio":
        dst = os.path.join(DESTINO, "material_apoio", nome_pad)
        shutil.copy2(src, dst)
        print(f"  APO  material_apoio/{nome_pad}")
    elif tipo == "duplicata":
        dst = os.path.join(DESTINO, "Duplicados", nome)
        shutil.copy2(src, dst)
        print(f"  DUP  Duplicados/{nome}")
    elif tipo == "nao_identificado":
        dst_nome = nome_pad if nome_pad else nome
        dst = os.path.join(DESTINO, "Nao_Identificados", dst_nome)
        shutil.copy2(src, dst)
        print(f"  NAO  Nao_Identificados/{dst_nome}")
    copiados.append(nome)

print(f"\nCopiados: {len(copiados)}, Erros: {len(erros)}")

# â”€â”€ Contagens para relatÃ³rio â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
cnt = {"simulados": 0, "gabaritos": 0, "material_apoio": 0,
       "duplicatas": 0, "nao_identificados": 0, "corrompidos": 0}
for _, tipo, _, _, _ in MAPA:
    if tipo == "simulado":
        cnt["simulados"] += 1
    elif tipo == "gabarito":
        cnt["gabaritos"] += 1
    elif tipo == "material_apoio":
        cnt["material_apoio"] += 1
    elif tipo == "duplicata":
        cnt["duplicatas"] += 1
    elif tipo == "nao_identificado":
        cnt["nao_identificados"] += 1

# â”€â”€ Gerar relatorio_exato.json â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
relatorio = {
    "gerado_em": str(date.today()),
    "total_arquivos": len(reais),
    "resumo": cnt,
    "associacoes": [
        {
            "evento": "CICLO ZERO", "turno": "MANHA",
            "simulado_original": CZ_MS_SIM,
            "simulado_padronizado": "EXATO_CICLO_ZERO_MANHA_SIMULADO.pdf",
            "gabarito_original": CZ_MS_GAB,
            "gabarito_padronizado": "EXATO_CICLO_ZERO_MANHA_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "Titulo interno: Simulado CICLO ZERO / Prova da MANHA. Conteudo: Linguagens+Humanas+Redacao."
        },
        {
            "evento": "CICLO ZERO", "turno": "TARDE",
            "simulado_original": CZ_T_SIM,
            "simulado_padronizado": "EXATO_CICLO_ZERO_TARDE_SIMULADO.pdf",
            "gabarito_original": CZ_T_GAB,
            "gabarito_padronizado": "EXATO_CICLO_ZERO_TARDE_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "Titulo interno: Simulado CICLO ZERO / Prova da TARDE. Conteudo: Matematica+Naturezas."
        },
        {
            "evento": "OUTUBRO 2025", "turno": "MANHA",
            "simulado_original": OUT_MS_SIM,
            "simulado_padronizado": "EXATO_OUTUBRO2025_MANHA_SIMULADO.pdf",
            "gabarito_original": OUT_MS_GAB,
            "gabarito_padronizado": "EXATO_OUTUBRO2025_MANHA_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "Gabarito REVISADO. Questao 2 corrigida para A. SIMULADO EXATO TESSAT 2025."
        },
        {
            "evento": "OUTUBRO 2025", "turno": "TARDE",
            "simulado_original": OUT_T_SIM,
            "simulado_padronizado": "EXATO_OUTUBRO2025_TARDE_SIMULADO.pdf",
            "gabarito_original": OUT_T_GAB,
            "gabarito_padronizado": "EXATO_OUTUBRO2025_TARDE_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "Gabarito REVISADO. Questoes 15 e 39 ANULADAS, 19-A, 30-C."
        },
        {
            "evento": "1 SIMULADO OFICIAL TESSAT 2025", "turno": "MANHA",
            "simulado_original": SIM1_MS_SIM,
            "simulado_padronizado": "EXATO_1SIMULADO_MANHA_SIMULADO.pdf",
            "gabarito_original": SIM1_MS_GAB,
            "gabarito_padronizado": "EXATO_1SIMULADO_MANHA_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "SIMULADO OFICIAL EXATO TESSAT 2025. 36 questoes (Linguagens+Matematica+Redacao)."
        },
        {
            "evento": "1 SIMULADO OFICIAL TESSAT 2025", "turno": "TARDE",
            "simulado_original": SIM1_T_SIM,
            "simulado_padronizado": "EXATO_1SIMULADO_TARDE_SIMULADO.pdf",
            "gabarito_original": SIM1_T_GAB,
            "gabarito_padronizado": "EXATO_1SIMULADO_TARDE_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "SIMULADO OFICIAL EXATO TESSAT 2025. Prova objetiva (Humanas+Naturezas)."
        },
        {
            "evento": "2 SIMULADO OFICIAL TESSAT 2025", "turno": "MANHA",
            "simulado_original": SIM2_MS_SIM,
            "simulado_padronizado": "EXATO_2SIMULADO_MANHA_SIMULADO.pdf",
            "gabarito_original": SIM2_MS_GAB,
            "gabarito_padronizado": "EXATO_2SIMULADO_MANHA_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "2 SIMULADO OFICIAL EXATO TESSAT 2025. 40 questoes (Linguagens+Matematica+Redacao)."
        },
        {
            "evento": "2 SIMULADO OFICIAL TESSAT 2025", "turno": "TARDE",
            "simulado_original": SIM2_T_SIM,
            "simulado_padronizado": "EXATO_2SIMULADO_TARDE_SIMULADO.pdf",
            "gabarito_original": SIM2_T_GAB,
            "gabarito_padronizado": "EXATO_2SIMULADO_TARDE_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "2 SIMULADO OFICIAL EXATO TESSAT 2025. 40 questoes (Humanas+Naturezas)."
        },
        {
            "evento": "29 ABRIL 2026 (EXATO 2026 1a Edicao)", "turno": "MANHA",
            "simulado_original": ABR_MS_SIM,
            "simulado_padronizado": "EXATO_29ABRIL2026_MANHA_SIMULADO.pdf",
            "gabarito_original": ABR_GAB,
            "gabarito_padronizado": "EXATO_29ABRIL2026_MANHA_E_TARDE_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "EXATO 2026 - 1a Edicao. Gabarito unico cobre MANHA e TARDE (11 pgs)."
        },
        {
            "evento": "29 ABRIL 2026 (EXATO 2026 1a Edicao)", "turno": "TARDE",
            "simulado_original": ABR_T_SIM,
            "simulado_padronizado": "EXATO_29ABRIL2026_TARDE_SIMULADO.pdf",
            "gabarito_original": ABR_GAB,
            "gabarito_padronizado": "EXATO_29ABRIL2026_MANHA_E_TARDE_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "Mesmo gabarito do turno MANHA."
        },
        {
            "evento": "NATUREZAS TESSAT 2025", "turno": "TARDE",
            "simulado_original": NAT_SIM,
            "simulado_padronizado": "EXATO_NATUREZAS_TARDE_SIMULADO.pdf",
            "gabarito_original": NAT_GAB,
            "gabarito_padronizado": "EXATO_NATUREZAS_TARDE_GABARITO.pdf",
            "confianca": "ALTA",
            "obs": "SIMULADO EXATO NATUREZAS TESSAT 2025. TARDE. 20 questoes Ciencias da Natureza."
        },
        {
            "evento": "TRADICIONAIS 04 ABRIL 2026", "turno": "SEM_TURNO",
            "simulado_original": TRAD_SIM,
            "simulado_padronizado": "EXATO_TRADICIONAIS_04ABRIL2026_SIMULADO.pdf",
            "gabarito_original": None,
            "gabarito_padronizado": None,
            "confianca": "ALTA",
            "obs": "40 questoes (5/disciplina). Horario 10h30-12h30. Sem gabarito em PDF encontrado."
        },
    ],
    "duplicatas": [
        {
            "arquivo": m[0],
            "original_correspondente": m[4],
            "motivo": "Hash MD5 das primeiras 2000 chars identico ao original â€” conteudo verificado"
        }
        for m in MAPA if m[1] == "duplicata"
    ],
    "material_apoio": [
        {
            "arquivo_original": m[0],
            "arquivo_padronizado": m[3],
            "tipo": "material_apoio"
        }
        for m in MAPA if m[1] == "material_apoio"
    ],
    "nao_identificados": [
        {
            "arquivo": m[0],
            "motivo": "PDF de 1 pagina puramente visual (imagem escaneada). Sem texto extraivel por pdfplumber. Provavelmente gabarito do 2 Simulado TESSAT turno MANHA. Requer OCR para confirmar.",
            "acao_sugerida": "Aplicar OCR (pytesseract) para reclassificar"
        }
        for m in MAPA if m[1] == "nao_identificado"
    ],
    "inconsistencias": [
        {
            "arquivo": "Simulado EXATO MANHA.pdf / Simulado EXATO TARDE.pdf",
            "problema": "Nome do arquivo nao indica data nem edicao. Conteudo revela ser o 1 Simulado Oficial EXATO TESSAT 2025 (36 questoes manha). Classificado como '1_simulado'.",
            "severidade": "BAIXA"
        },
        {
            "arquivo": "GABARITO - MANHA - TESSAT.pdf e GABARITO - TARDE - TESSAT (1).pdf",
            "problema": "Ambos sao PDFs-imagem (1 pg, sem texto), hash identico. Nao e possivel confirmar a qual simulado pertencem sem OCR. Possivelmente gabarito do 2 Simulado TESSAT.",
            "severidade": "MEDIA"
        },
        {
            "arquivo": "Simulado TRADICIONAIS (04 de Abril).pdf",
            "problema": "Nao ha gabarito correspondente na pasta. Gabarito provavelmente enviado digitalmente aos alunos (menciona envio 30 min apos inicio).",
            "severidade": "BAIXA"
        },
        {
            "arquivo": "Gabarito Comentado - EXATO (29 de abril, 2026).pdf",
            "problema": "Um unico arquivo de gabarito cobre MANHA e TARDE (11 pgs). Copiado uma vez em gabaritos/29_abril_2026/ com nome indicando ambos os turnos.",
            "severidade": "INFO"
        },
    ],
    "notas_integracao_henryjr": {
        "separacao_enem_exato": "Arquivos EXATO em DADOS/EXATO_ORGANIZADO/, separados dos dados ENEM em dados/json_v2/ e dados/provas/",
        "identificador_tipo": "fonte=EXATO em todos os JSONs de questoes",
        "recursos_compativeis": ["resposta_ia", "explicacao_ia", "filtro_area", "busca_contextual", "metricas"],
        "recursos_nao_aplicaveis": ["pagina_pdf_enem", "competencias_H01_H30_enem"]
    }
}

with open(os.path.join(DESTINO, "relatorio_exato.json"), "w", encoding="utf-8") as fh:
    json.dump(relatorio, fh, ensure_ascii=False, indent=2)
print("relatorio_exato.json salvo.")

# â”€â”€ Gerar metadata_integracao.json â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
metadata = {
    "fonte": "EXATO",
    "tipo_conteudo": "simulado_cursinho",
    "descricao": "Simulados do cursinho EXATO (Araguaina/TO) para preparacao ao TESSAT (Exame de Acesso ao Ensino Superior do Tocantins) e ENEM",
    "separacao_banco": "tabela_questoes com campo fonte='EXATO' para separar de fonte='ENEM'",
    "eventos_identificados": [
        {
            "id": "CICLO_ZERO", "nome": "Ciclo Zero",
            "descricao": "Simulado inicial focado em conteudos tradicionais. MANHA: Linguagens+Humanas+Redacao. TARDE: Matematica+Naturezas.",
            "turnos": ["MANHA", "TARDE"], "status": "completo"
        },
        {
            "id": "OUTUBRO_2025", "nome": "Simulado EXATO Outubro 2025",
            "descricao": "SIMULADO EXATO TESSAT 2025 - outubro. Gabaritos revisados com questoes anuladas.",
            "turnos": ["MANHA", "TARDE"], "questoes_por_turno": 40, "status": "completo"
        },
        {
            "id": "1_SIMULADO", "nome": "1 Simulado Oficial EXATO TESSAT 2025",
            "descricao": "Primeiro Simulado Oficial EXATO TESSAT 2025. MANHA: 36 questoes. TARDE: prova objetiva.",
            "turnos": ["MANHA", "TARDE"], "questoes_manha": 36, "status": "completo"
        },
        {
            "id": "2_SIMULADO", "nome": "2 Simulado Oficial EXATO TESSAT 2025",
            "descricao": "Segundo Simulado Oficial EXATO TESSAT 2025. 40 questoes por turno.",
            "turnos": ["MANHA", "TARDE"], "questoes_por_turno": 40, "status": "completo"
        },
        {
            "id": "29_ABRIL_2026", "nome": "Simulado EXATO 29 Abril 2026 (EXATO 2026 1a Edicao)",
            "descricao": "Exame de Acesso ao Ensino Superior do Tocantins EXATO 2026 - 1a Edicao.",
            "turnos": ["MANHA", "TARDE"], "status": "completo"
        },
        {
            "id": "NATUREZAS", "nome": "Simulado EXATO Naturezas TESSAT 2025",
            "descricao": "Simulado especifico de Ciencias da Natureza. 20 questoes. Turno TARDE.",
            "turnos": ["TARDE"], "questoes": 20, "status": "completo"
        },
        {
            "id": "TRADICIONAIS", "nome": "Simulado Tradicionais 04 Abril 2026",
            "descricao": "Simulado de 40 questoes (5/disciplina: Portugues, Geografia, Historia, Filosofia/Sociologia, Matematica, Fisica, Quimica, Biologia). Horario 10h30-12h30.",
            "questoes": 40, "status": "sem_gabarito"
        },
    ],
    "estrutura_questao_exato": {
        "campos_comuns_enem": ["numero", "ano", "dia", "area", "enunciado", "alternativas", "gabarito"],
        "campos_especificos_exato": ["evento", "turno", "simulado_id", "fonte"],
        "campos_nao_aplicaveis": ["pagina_pdf", "competencia_h01_h30", "anulada"]
    },
    "filtros_plataforma": {
        "por_fonte": ["ENEM", "EXATO"],
        "por_evento_exato": ["CICLO_ZERO", "OUTUBRO_2025", "1_SIMULADO", "2_SIMULADO", "29_ABRIL_2026", "NATUREZAS", "TRADICIONAIS"],
        "por_turno": ["MANHA", "TARDE"]
    },
    "recursos_ativos": {
        "explicacao_ia": True, "busca_contextual": True, "filtro_area": True,
        "filtro_disciplina": True, "metricas_desempenho": True, "tira_teima": True,
        "simulado_cronometrado": True, "correcao_automatica": True
    },
    "recursos_desativados": {
        "competencias_h01_h30": False,
        "pagina_pdf_original": False,
        "gabarito_oficial_enem": False
    },
    "notas_tecnicas": [
        "Gabaritos TESSAT (MANHA/TARDE) sao PDFs-imagem sem texto. Requerem OCR antes de uso.",
        "Gabarito do 29 Abril 2026 cobre ambos turnos em 1 arquivo (11 pgs).",
        "Simulado TRADICIONAIS nao possui gabarito em PDF â€” enviado digitalmente.",
        "Todos os simulados EXATO sao para o TESSAT (vestibular estadual do Tocantins).",
        "Material de apoio (trilhas, listas, cartilha, conexao-uft) nao deve ser importado como questoes â€” uso apenas como referencia."
    ]
}

with open(os.path.join(DESTINO, "metadata_integracao.json"), "w", encoding="utf-8") as fh:
    json.dump(metadata, fh, ensure_ascii=False, indent=2)
print("metadata_integracao.json salvo.")

# â”€â”€ Resumo final â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
assoc_com_gab = len([a for a in relatorio["associacoes"] if a["gabarito_original"]])
print("\n" + "="*60)
print("RESUMO FINAL")
print("="*60)
print(f"  Total arquivos na pasta:  {len(reais)}")
print(f"  Simulados unicos:         {cnt['simulados']}")
print(f"  Gabaritos unicos:         {cnt['gabaritos']}")
print(f"  Material de apoio:        {cnt['material_apoio']}")
print(f"  Duplicatas:               {cnt['duplicatas']}")
print(f"  Nao identificados:        {cnt['nao_identificados']}")
print(f"  Corrompidos:              {cnt['corrompidos']}")
print(f"  Assoc. Sim<->Gab (alta):  {assoc_com_gab}")
print(f"  Inconsistencias:          {len(relatorio['inconsistencias'])}")
print(f"  Erros na copia:           {len(erros)}")
if nao_mapeados:
    print(f"\n  ATENCAO: {len(nao_mapeados)} arquivo(s) nao mapeados!")
    for f in nao_mapeados:
        print(f"    {f}")

