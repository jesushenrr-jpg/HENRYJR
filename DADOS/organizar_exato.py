"""
Organiza os PDFs da pasta EXATO com base na anÃ¡lise de conteÃºdo.

ClassificaÃ§Ã£o com base na leitura real de cada arquivo:

EVENTOS IDENTIFICADOS:
  1. CICLO ZERO       â€” Simulados TRADICIONAIS, CICLO ZERO no tÃ­tulo
  2. OUTUBRO_2025     â€” "SIMULADO EXATO â€“ TESSAT 2025" (1Âª ediÃ§Ã£o, outubro)
  3. 1_SIMULADO       â€” "SIMULADO OFICIAL EXATO â€“ TESSAT 2025" (36 questÃµes manhÃ£ / sem data explÃ­cita)
  4. 2_SIMULADO       â€” "2Âº SIMULADO OFICIAL EXATO â€“ TESSAT 2025" (40 questÃµes)
  5. 29_ABRIL_2026    â€” "SIMULADO OFICIAL EXATO" / "EXATO 2026 â€“ 1Âª EdiÃ§Ã£o"
  6. TRADICIONAIS     â€” "Simulado TRADICIONAIS (04 de Abril)"
  7. NATUREZAS        â€” "SIMULADO EXATO NATUREZAS â€“ TESSAT 2025"

NOTA sobre "Simulado EXATO MANHÃƒ/TARDE.pdf" (sem data):
  ConteÃºdo: "SIMULADO OFICIAL EXATO â€“ TESSAT 2025", 36 questÃµes (manhÃ£) / 1 Prova Objetiva (tarde)
  Gabarito correspondente: "Gabarito Comentado Exato MANHÃƒ/TARDE.pdf"
  â†’ classificado como evento "1_SIMULADO" (1Âº Simulado Oficial TESSAT 2025)

NOTA sobre "GAB EXATO MANHÃƒ/TARDE REVISADO (Outubro, 2025).pdf":
  ConteÃºdo: "Gabarito Comentado / SIMULADO EXATO / Prova da MANHÃƒ/TARDE"
  â†’ gabarito revisado do Outubro 2025 (questÃµes revisadas / anuladas listadas)
  â†’ classificado como gabarito do evento OUTUBRO_2025

NOTA sobre TESSAT gabaritos (texto extraÃ­do vazio â€” PDFs escaneados/imagem):
  GABARITO - MANHÃƒ - TESSAT.pdf  â†’ 1 pÃ¡gina, texto vazio (imagem)
  GABARITO - TARDE - TESSAT (1).pdf â†’ 1 pÃ¡gina, texto vazio, mesmo hash que MANHÃƒ â†’ DUPLICATA
  â†’ ambos em Nao_Identificados com obs sobre PDF-imagem

NOTA sobre "Gabarito Comentado - EXATO (29 de abril, 2026).pdf":
  Cobre MANHÃƒ + TARDE no mesmo arquivo (11 pÃ¡ginas)

NOTA sobre "GABARITO Exato NATUREZAS.pdf":
  3 pÃ¡ginas, comeÃ§a com resoluÃ§Ãµes de Biologia/FÃ­sica/QuÃ­mica â†’ gabarito do NATUREZAS
"""

import os
import shutil
import json
from datetime import date

ORIGEM = r"C:\PROJETOS\HENRYJR\DADOS\\EXATO_SIMULADOS"
DESTINO = r"C:\PROJETOS\HENRYJR\DADOS\EXATO_ORGANIZADO"

# â”€â”€ DefiniÃ§Ã£o completa dos arquivos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Formato: (arquivo_original, tipo, evento, turno, nome_padronizado, duplicata_de)
# tipo: simulado | gabarito | material_apoio | duplicata | nao_identificado

MAPEAMENTO = [
    # â”€â”€ CICLO ZERO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ("Simulado CICLO ZERO (MANHÃƒ).pdf",
     "simulado", "ciclo_zero", "MANHA",
     "EXATO_CICLO_ZERO_MANHA_SIMULADO.pdf", None),

    ("Simulado CICLO ZERO (TARDE).pdf",
     "simulado", "ciclo_zero", "TARDE",
     "EXATO_CICLO_ZERO_TARDE_SIMULADO.pdf", None),

    ("Gabarito Comentado CICLO ZERO (MANHÃƒ).pdf",
     "gabarito", "ciclo_zero", "MANHA",
     "EXATO_CICLO_ZERO_MANHA_GABARITO.pdf", None),

    ("Gabarito Comentado CICLO ZERO (TARDE).pdf",
     "gabarito", "ciclo_zero", "TARDE",
     "EXATO_CICLO_ZERO_TARDE_GABARITO.pdf", None),

    # Duplicatas CICLO ZERO
    ("Simulado CICLO ZERO (MANHÃƒ)(1).pdf",
     "duplicata", "ciclo_zero", "MANHA", None, "Simulado CICLO ZERO (MANHÃƒ).pdf"),
    ("Simulado CICLO ZERO (MANHÃƒ)(2).pdf",
     "duplicata", "ciclo_zero", "MANHA", None, "Simulado CICLO ZERO (MANHÃƒ).pdf"),
    ("Simulado CICLO ZERO (MANHÃƒ)(3).pdf",
     "duplicata", "ciclo_zero", "MANHA", None, "Simulado CICLO ZERO (MANHÃƒ).pdf"),
    ("Simulado CICLO ZERO (TARDE)(1).pdf",
     "duplicata", "ciclo_zero", "TARDE", None, "Simulado CICLO ZERO (TARDE).pdf"),
    ("Simulado CICLO ZERO (TARDE)(2).pdf",
     "duplicata", "ciclo_zero", "TARDE", None, "Simulado CICLO ZERO (TARDE).pdf"),
    ("Simulado CICLO ZERO (TARDE)(3).pdf",
     "duplicata", "ciclo_zero", "TARDE", None, "Simulado CICLO ZERO (TARDE).pdf"),
    ("Gabarito Comentado CICLO ZERO (MANHÃƒ)(1).pdf",
     "duplicata", "ciclo_zero", "MANHA", None, "Gabarito Comentado CICLO ZERO (MANHÃƒ).pdf"),
    ("Gabarito Comentado CICLO ZERO (TARDE)(1).pdf",
     "duplicata", "ciclo_zero", "TARDE", None, "Gabarito Comentado CICLO ZERO (TARDE).pdf"),

    # â”€â”€ OUTUBRO 2025 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ("Simulado EXATO (MANHÃƒ) OUTUBRO 2025.pdf",
     "simulado", "outubro_2025", "MANHA",
     "EXATO_OUTUBRO2025_MANHA_SIMULADO.pdf", None),

    ("Simulado EXATO (TARDE) OUTUBRO 2025.pdf",
     "simulado", "outubro_2025", "TARDE",
     "EXATO_OUTUBRO2025_TARDE_SIMULADO.pdf", None),

    ("GAB EXATO MANHÃƒ REVISADO (Outubro, 2025).pdf",
     "gabarito", "outubro_2025", "MANHA",
     "EXATO_OUTUBRO2025_MANHA_GABARITO.pdf", None),

    ("GAB EXATO TARDE REVISADO(Outubro, 2025).pdf",
     "gabarito", "outubro_2025", "TARDE",
     "EXATO_OUTUBRO2025_TARDE_GABARITO.pdf", None),

    # Duplicatas OUTUBRO 2025
    ("Simulado EXATO (MANHÃƒ) OUTUBRO 2025(1).pdf",
     "duplicata", "outubro_2025", "MANHA", None, "Simulado EXATO (MANHÃƒ) OUTUBRO 2025.pdf"),
    ("Simulado EXATO (MANHÃƒ) OUTUBRO 2025(2).pdf",
     "duplicata", "outubro_2025", "MANHA", None, "Simulado EXATO (MANHÃƒ) OUTUBRO 2025.pdf"),
    ("Simulado EXATO (TARDE) OUTUBRO 2025(1).pdf",
     "duplicata", "outubro_2025", "TARDE", None, "Simulado EXATO (TARDE) OUTUBRO 2025.pdf"),
    ("Simulado EXATO (TARDE) OUTUBRO 2025(2).pdf",
     "duplicata", "outubro_2025", "TARDE", None, "Simulado EXATO (TARDE) OUTUBRO 2025.pdf"),
    ("GAB EXATO MANHÃƒ REVISADO (Outubro, 2025)(1).pdf",
     "duplicata", "outubro_2025", "MANHA", None, "GAB EXATO MANHÃƒ REVISADO (Outubro, 2025).pdf"),
    ("GAB EXATO MANHÃƒ REVISADO (Outubro, 2025)(2).pdf",
     "duplicata", "outubro_2025", "MANHA", None, "GAB EXATO MANHÃƒ REVISADO (Outubro, 2025).pdf"),
    ("GAB EXATO TARDE REVISADO(Outubro, 2025)(1).pdf",
     "duplicata", "outubro_2025", "TARDE", None, "GAB EXATO TARDE REVISADO(Outubro, 2025).pdf"),
    ("GAB EXATO TARDE REVISADO(Outubro, 2025)(2).pdf",
     "duplicata", "outubro_2025", "TARDE", None, "GAB EXATO TARDE REVISADO(Outubro, 2025).pdf"),

    # â”€â”€ 1Âº SIMULADO OFICIAL TESSAT 2025 (sem data no nome) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ("Simulado EXATO MANHÃƒ.pdf",
     "simulado", "1_simulado", "MANHA",
     "EXATO_1SIMULADO_MANHA_SIMULADO.pdf", None),

    ("Simulado EXATO TARDE.pdf",
     "simulado", "1_simulado", "TARDE",
     "EXATO_1SIMULADO_TARDE_SIMULADO.pdf", None),

    ("Gabarito Comentado Exato MANHÃƒ.pdf",
     "gabarito", "1_simulado", "MANHA",
     "EXATO_1SIMULADO_MANHA_GABARITO.pdf", None),

    ("Gabarito Comentado Exato TARDE.pdf",
     "gabarito", "1_simulado", "TARDE",
     "EXATO_1SIMULADO_TARDE_GABARITO.pdf", None),

    # Duplicatas 1Âº Simulado
    ("Simulado EXATO MANHÃƒ(1).pdf",
     "duplicata", "1_simulado", "MANHA", None, "Simulado EXATO MANHÃƒ.pdf"),
    ("Simulado EXATO MANHÃƒ(2).pdf",
     "duplicata", "1_simulado", "MANHA", None, "Simulado EXATO MANHÃƒ.pdf"),
    ("Simulado EXATO MANHÃƒ(3).pdf",
     "duplicata", "1_simulado", "MANHA", None, "Simulado EXATO MANHÃƒ.pdf"),
    ("Simulado EXATO MANHÃƒ(4).pdf",
     "duplicata", "1_simulado", "MANHA", None, "Simulado EXATO MANHÃƒ.pdf"),
    ("Simulado EXATO TARDE(1).pdf",
     "duplicata", "1_simulado", "TARDE", None, "Simulado EXATO TARDE.pdf"),
    ("Simulado EXATO TARDE(2).pdf",
     "duplicata", "1_simulado", "TARDE", None, "Simulado EXATO TARDE.pdf"),
    ("Simulado EXATO TARDE(3).pdf",
     "duplicata", "1_simulado", "TARDE", None, "Simulado EXATO TARDE.pdf"),
    ("Simulado EXATO TARDE(4).pdf",
     "duplicata", "1_simulado", "TARDE", None, "Simulado EXATO TARDE.pdf"),
    ("Gabarito Comentado Exato MANHÃƒ(1).pdf",
     "duplicata", "1_simulado", "MANHA", None, "Gabarito Comentado Exato MANHÃƒ.pdf"),
    ("Gabarito Comentado Exato MANHÃƒ(2).pdf",
     "duplicata", "1_simulado", "MANHA", None, "Gabarito Comentado Exato MANHÃƒ.pdf"),
    ("Gabarito Comentado Exato MANHÃƒ(3).pdf",
     "duplicata", "1_simulado", "MANHA", None, "Gabarito Comentado Exato MANHÃƒ.pdf"),
    ("Gabarito Comentado Exato MANHÃƒ(4).pdf",
     "duplicata", "1_simulado", "MANHA", None, "Gabarito Comentado Exato MANHÃƒ.pdf"),
    ("Gabarito Comentado Exato TARDE(1).pdf",
     "duplicata", "1_simulado", "TARDE", None, "Gabarito Comentado Exato TARDE.pdf"),
    ("Gabarito Comentado Exato TARDE(2).pdf",
     "duplicata", "1_simulado", "TARDE", None, "Gabarito Comentado Exato TARDE.pdf"),
    ("Gabarito Comentado Exato TARDE(3).pdf",
     "duplicata", "1_simulado", "TARDE", None, "Gabarito Comentado Exato TARDE.pdf"),
    ("Gabarito Comentado Exato TARDE(4).pdf",
     "duplicata", "1_simulado", "TARDE", None, "Gabarito Comentado Exato TARDE.pdf"),

    # â”€â”€ 2Âº SIMULADO OFICIAL TESSAT 2025 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ("2Âº Simulado EXATO - MANHÃƒ.pdf",
     "simulado", "2_simulado", "MANHA",
     "EXATO_2SIMULADO_MANHA_SIMULADO.pdf", None),

    ("2Âº Simulado EXATO - TARDE.pdf",
     "simulado", "2_simulado", "TARDE",
     "EXATO_2SIMULADO_TARDE_SIMULADO.pdf", None),

    ("Gabarito Comentado 2Âº Exato MANHÃƒ.pdf",
     "gabarito", "2_simulado", "MANHA",
     "EXATO_2SIMULADO_MANHA_GABARITO.pdf", None),

    ("Gabarito Comentado 2Âº Exato TARDE.pdf",
     "gabarito", "2_simulado", "TARDE",
     "EXATO_2SIMULADO_TARDE_GABARITO.pdf", None),

    # Duplicatas 2Âº Simulado
    ("2Âº Simulado EXATO - MANHÃƒ(1).pdf",
     "duplicata", "2_simulado", "MANHA", None, "2Âº Simulado EXATO - MANHÃƒ.pdf"),
    ("2Âº Simulado EXATO - TARDE(1).pdf",
     "duplicata", "2_simulado", "TARDE", None, "2Âº Simulado EXATO - TARDE.pdf"),

    # â”€â”€ 29 ABRIL 2026 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ("SIMULADO OFICIAL EXATO (MANHÃƒ) - 29 de abril.pdf",
     "simulado", "29_abril_2026", "MANHA",
     "EXATO_29ABRIL2026_MANHA_SIMULADO.pdf", None),

    ("SIMULADO OFICIAL EXATO (TARDE) - 29 de abril.pdf",
     "simulado", "29_abril_2026", "TARDE",
     "EXATO_29ABRIL2026_TARDE_SIMULADO.pdf", None),

    # Gabarito Ãºnico que cobre MANHÃƒ+TARDE
    ("Gabarito Comentado - EXATO (29 de abril, 2026).pdf",
     "gabarito", "29_abril_2026", "MANHA_E_TARDE",
     "EXATO_29ABRIL2026_MANHA_E_TARDE_GABARITO.pdf", None),

    # â”€â”€ NATUREZAS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ("Simulado Exato NATUREZAS (1)_250421_171103.pdf",
     "simulado", "naturezas", "TARDE",
     "EXATO_NATUREZAS_TARDE_SIMULADO.pdf", None),

    ("GABARITO Exato NATUREZAS.pdf",
     "gabarito", "naturezas", "TARDE",
     "EXATO_NATUREZAS_TARDE_GABARITO.pdf", None),

    # â”€â”€ TRADICIONAIS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ("Simulado TRADICIONAIS (04 de Abril).pdf",
     "simulado", "tradicionais", "SEM_TURNO",
     "EXATO_TRADICIONAIS_04ABRIL2026_SIMULADO.pdf", None),

    # â”€â”€ TESSAT â€” gabaritos escaneados (PDF-imagem, texto nÃ£o extraÃ­vel) â”€â”€â”€
    # Ambos tÃªm hash idÃªntico: e4c7ca64fd6813eff040d24c3b1c22d0 â†’ DUPLICATA
    ("GABARITO - MANHÃƒ - TESSAT.pdf",
     "nao_identificado", None, "MANHA",
     "GABARITO_TESSAT_MANHA_IMAGEM.pdf",
     None),  # original â€” mantido em nao_identificado por ser PDF-imagem sem OCR

    ("GABARITO - TARDE - TESSAT (1).pdf",
     "duplicata", None, "TARDE",
     None,
     "GABARITO - MANHÃƒ - TESSAT.pdf"),  # hash idÃªntico ao MANHÃƒ

    # â”€â”€ MATERIAL DE APOIO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ("Cartilha MED UFT 2025.pdf",
     "material_apoio", None, None,
     "EXATO_CARTILHA_MED_UFT_2025.pdf", None),

    ("RedaÃ§Ã£o Nota Mil ENEM X Nota 100 ExaTO.pdf",
     "material_apoio", None, None,
     "EXATO_REDACAO_NOTA_MIL_ENEM_vs_EXATO.pdf", None),

    ("conexao-uft-exato.pdf",
     "material_apoio", None, None,
     "EXATO_CONEXAO_UFT_QUESTOES_MATEMATICA.pdf", None),

    ("lista-01---projeto-2020.pdf",
     "material_apoio", None, None,
     "EXATO_LISTA01_MATEMATICA_2020.pdf", None),

    ("lista-02-proj-2020.pdf",
     "material_apoio", None, None,
     "EXATO_LISTA02_MATEMATICA_2020.pdf", None),

    ("trilha-exato-parte-1.pdf",
     "material_apoio", None, None,
     "EXATO_TRILHA_PARTE1_SEMANA1.pdf", None),

    ("trilha-exato-parte-2.pdf",
     "material_apoio", None, None,
     "EXATO_TRILHA_PARTE2_SEMANA4.pdf", None),

    ("trilha-exato-parte-3.pdf",
     "material_apoio", None, None,
     "EXATO_TRILHA_PARTE3_SEMANA7.pdf", None),
]

# â”€â”€ Mapeamento de subpastas por evento â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SUBPASTAS_SIM = {
    "ciclo_zero": "simulados/ciclo_zero",
    "outubro_2025": "simulados/outubro_2025",
    "1_simulado": "simulados/1_simulado",
    "2_simulado": "simulados/2_simulado",
    "29_abril_2026": "simulados/29_abril_2026",
    "naturezas": "simulados/naturezas",
    "tradicionais": "simulados/tradicionais",
}
SUBPASTAS_GAB = {
    "ciclo_zero": "gabaritos/ciclo_zero",
    "outubro_2025": "gabaritos/outubro_2025",
    "1_simulado": "gabaritos/1_simulado",
    "2_simulado": "gabaritos/2_simulado",
    "29_abril_2026": "gabaritos/29_abril_2026",
    "naturezas": "gabaritos/naturezas",
    "tradicionais": "gabaritos/tradicionais",
}

# â”€â”€ Criar estrutura de pastas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PASTAS = [
    "simulados/ciclo_zero",
    "simulados/outubro_2025",
    "simulados/1_simulado",
    "simulados/2_simulado",
    "simulados/29_abril_2026",
    "simulados/naturezas",
    "simulados/tradicionais",
    "gabaritos/ciclo_zero",
    "gabaritos/outubro_2025",
    "gabaritos/1_simulado",
    "gabaritos/2_simulado",
    "gabaritos/29_abril_2026",
    "gabaritos/naturezas",
    "gabaritos/tradicionais",
    "material_apoio",
    "Duplicados",
    "Nao_Identificados",
    "Corrompidos",
]

print("Criando estrutura de pastas...")
for p in PASTAS:
    caminho = os.path.join(DESTINO, p)
    os.makedirs(caminho, exist_ok=True)
    print(f"  OK: {caminho}")

# â”€â”€ Copiar e renomear arquivos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\nCopiando arquivos...")
copiados = []
erros = []

for entrada in MAPEAMENTO:
    orig, tipo, evento, turno, nome_pad, dup_de = entrada
    src = os.path.join(ORIGEM, orig)

    if not os.path.exists(src):
        erros.append(f"ARQUIVO NAO ENCONTRADO: {orig}")
        print(f"  ERRO: {orig} nao encontrado")
        continue

    if tipo == "simulado":
        subpasta = SUBPASTAS_SIM[evento]
        dst = os.path.join(DESTINO, subpasta, nome_pad)
        shutil.copy2(src, dst)
        print(f"  SIM  -> {subpasta}/{nome_pad}")

    elif tipo == "gabarito":
        subpasta = SUBPASTAS_GAB[evento]
        dst = os.path.join(DESTINO, subpasta, nome_pad)
        shutil.copy2(src, dst)
        print(f"  GAB  -> {subpasta}/{nome_pad}")

    elif tipo == "material_apoio":
        dst = os.path.join(DESTINO, "material_apoio", nome_pad)
        shutil.copy2(src, dst)
        print(f"  APO  -> material_apoio/{nome_pad}")

    elif tipo == "duplicata":
        dst = os.path.join(DESTINO, "Duplicados", orig)
        shutil.copy2(src, dst)
        print(f"  DUP  -> Duplicados/{orig}")

    elif tipo == "nao_identificado":
        dst = os.path.join(DESTINO, "Nao_Identificados", nome_pad if nome_pad else orig)
        shutil.copy2(src, dst)
        print(f"  NAO  -> Nao_Identificados/{nome_pad if nome_pad else orig}")

    copiados.append(orig)

if erros:
    print("\nERROS:")
    for e in erros:
        print(f"  {e}")

print(f"\nTotal copiado: {len(copiados)} arquivos")
print(f"Erros: {len(erros)}")

# â”€â”€ Gerar relatorio_exato.json â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
relatorio = {
    "gerado_em": str(date.today()),
    "total_arquivos": 66,
    "resumo": {
        "simulados": 0,
        "gabaritos": 0,
        "material_apoio": 0,
        "duplicatas": 0,
        "nao_identificados": 0,
        "corrompidos": 0
    },
    "associacoes": [],
    "duplicatas": [],
    "material_apoio": [],
    "nao_identificados": [],
    "inconsistencias": [],
    "notas_integracao_henryjr": {
        "separacao_enem_exato": "Os arquivos EXATO ficam em DADOS/EXATO_ORGANIZADO/, separados dos dados ENEM em dados/json_v2/ e dados/provas/",
        "identificador_tipo": "fonte=EXATO em todos os JSONs de questoes",
        "recursos_compativeis": ["resposta_ia", "explicacao_ia", "filtro_area", "busca_contextual", "metricas"],
        "recursos_nao_aplicaveis": ["pagina_pdf_enem", "competencias_H01_H30_enem"]
    }
}

# Contagens
for entrada in MAPEAMENTO:
    orig, tipo, evento, turno, nome_pad, dup_de = entrada
    if tipo == "simulado":
        relatorio["resumo"]["simulados"] += 1
    elif tipo == "gabarito":
        relatorio["resumo"]["gabaritos"] += 1
    elif tipo == "material_apoio":
        relatorio["resumo"]["material_apoio"] += 1
    elif tipo == "duplicata":
        relatorio["resumo"]["duplicatas"] += 1
    elif tipo == "nao_identificado":
        relatorio["resumo"]["nao_identificados"] += 1

# AssociaÃ§Ãµes simulado <-> gabarito
ASSOCIACOES = [
    {
        "evento": "CICLO ZERO",
        "turno": "MANHÃƒ",
        "simulado_original": "Simulado CICLO ZERO (MANHÃƒ).pdf",
        "simulado_padronizado": "EXATO_CICLO_ZERO_MANHA_SIMULADO.pdf",
        "gabarito_original": "Gabarito Comentado CICLO ZERO (MANHÃƒ).pdf",
        "gabarito_padronizado": "EXATO_CICLO_ZERO_MANHA_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Titulo interno confirma: 'Simulado CICLO ZERO / Prova da MANHA'"
    },
    {
        "evento": "CICLO ZERO",
        "turno": "TARDE",
        "simulado_original": "Simulado CICLO ZERO (TARDE).pdf",
        "simulado_padronizado": "EXATO_CICLO_ZERO_TARDE_SIMULADO.pdf",
        "gabarito_original": "Gabarito Comentado CICLO ZERO (TARDE).pdf",
        "gabarito_padronizado": "EXATO_CICLO_ZERO_TARDE_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Titulo interno confirma: 'Simulado CICLO ZERO / Prova da TARDE'"
    },
    {
        "evento": "OUTUBRO 2025",
        "turno": "MANHÃƒ",
        "simulado_original": "Simulado EXATO (MANHÃƒ) OUTUBRO 2025.pdf",
        "simulado_padronizado": "EXATO_OUTUBRO2025_MANHA_SIMULADO.pdf",
        "gabarito_original": "GAB EXATO MANHÃƒ REVISADO (Outubro, 2025).pdf",
        "gabarito_padronizado": "EXATO_OUTUBRO2025_MANHA_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Gabarito revisado com questao 2 corrigida para A. Simulado = 'SIMULADO EXATO TESSAT 2025 MANHA'"
    },
    {
        "evento": "OUTUBRO 2025",
        "turno": "TARDE",
        "simulado_original": "Simulado EXATO (TARDE) OUTUBRO 2025.pdf",
        "simulado_padronizado": "EXATO_OUTUBRO2025_TARDE_SIMULADO.pdf",
        "gabarito_original": "GAB EXATO TARDE REVISADO(Outubro, 2025).pdf",
        "gabarito_padronizado": "EXATO_OUTUBRO2025_TARDE_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Gabarito revisado com questoes 15 e 39 ANULADAS, 19-A, 30-C"
    },
    {
        "evento": "1Âº SIMULADO OFICIAL TESSAT 2025",
        "turno": "MANHÃƒ",
        "simulado_original": "Simulado EXATO MANHÃƒ.pdf",
        "simulado_padronizado": "EXATO_1SIMULADO_MANHA_SIMULADO.pdf",
        "gabarito_original": "Gabarito Comentado Exato MANHÃƒ.pdf",
        "gabarito_padronizado": "EXATO_1SIMULADO_MANHA_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Titulo: 'SIMULADO OFICIAL EXATO TESSAT 2025 / 36 questoes'. Gabarito: 'Gabarito Comentado SIMULADO OFICIAL EXATO / Prova da MANHA'"
    },
    {
        "evento": "1Âº SIMULADO OFICIAL TESSAT 2025",
        "turno": "TARDE",
        "simulado_original": "Simulado EXATO TARDE.pdf",
        "simulado_padronizado": "EXATO_1SIMULADO_TARDE_SIMULADO.pdf",
        "gabarito_original": "Gabarito Comentado Exato TARDE.pdf",
        "gabarito_padronizado": "EXATO_1SIMULADO_TARDE_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Titulo: 'SIMULADO OFICIAL EXATO TESSAT 2025 / 1 Prova Objetiva'. Gabarito: 'Gabarito Comentado SIMULADO OFICIAL EXATO / Prova da TARDE'"
    },
    {
        "evento": "2Âº SIMULADO OFICIAL TESSAT 2025",
        "turno": "MANHÃƒ",
        "simulado_original": "2Âº Simulado EXATO - MANHÃƒ.pdf",
        "simulado_padronizado": "EXATO_2SIMULADO_MANHA_SIMULADO.pdf",
        "gabarito_original": "Gabarito Comentado 2Âº Exato MANHÃƒ.pdf",
        "gabarito_padronizado": "EXATO_2SIMULADO_MANHA_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Titulo: '2Â° SIMULADO OFICIAL EXATO TESSAT 2025 / 40 questoes'"
    },
    {
        "evento": "2Âº SIMULADO OFICIAL TESSAT 2025",
        "turno": "TARDE",
        "simulado_original": "2Âº Simulado EXATO - TARDE.pdf",
        "simulado_padronizado": "EXATO_2SIMULADO_TARDE_SIMULADO.pdf",
        "gabarito_original": "Gabarito Comentado 2Âº Exato TARDE.pdf",
        "gabarito_padronizado": "EXATO_2SIMULADO_TARDE_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Titulo: '2Â° SIMULADO OFICIAL EXATO TESSAT 2025 / 40 40'"
    },
    {
        "evento": "29 ABRIL 2026 (EXATO 2026 - 1a Edicao)",
        "turno": "MANHÃƒ",
        "simulado_original": "SIMULADO OFICIAL EXATO (MANHÃƒ) - 29 de abril.pdf",
        "simulado_padronizado": "EXATO_29ABRIL2026_MANHA_SIMULADO.pdf",
        "gabarito_original": "Gabarito Comentado - EXATO (29 de abril, 2026).pdf",
        "gabarito_padronizado": "EXATO_29ABRIL2026_MANHA_E_TARDE_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Gabarito cobre ambos os turnos em 1 arquivo (11 pgs). Simulado: 'EXATO 2026 - 1a Edicao / Prova de Conhecimentos MANHA'"
    },
    {
        "evento": "29 ABRIL 2026 (EXATO 2026 - 1a Edicao)",
        "turno": "TARDE",
        "simulado_original": "SIMULADO OFICIAL EXATO (TARDE) - 29 de abril.pdf",
        "simulado_padronizado": "EXATO_29ABRIL2026_TARDE_SIMULADO.pdf",
        "gabarito_original": "Gabarito Comentado - EXATO (29 de abril, 2026).pdf",
        "gabarito_padronizado": "EXATO_29ABRIL2026_MANHA_E_TARDE_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Mesmo gabarito do turno MANHA (cobre ambos). Simulado: 'EXATO 2026 - 1a Edicao / Prova de Conhecimentos TARDE'"
    },
    {
        "evento": "NATUREZAS TESSAT 2025",
        "turno": "TARDE",
        "simulado_original": "Simulado Exato NATUREZAS (1)_250421_171103.pdf",
        "simulado_padronizado": "EXATO_NATUREZAS_TARDE_SIMULADO.pdf",
        "gabarito_original": "GABARITO Exato NATUREZAS.pdf",
        "gabarito_padronizado": "EXATO_NATUREZAS_TARDE_GABARITO.pdf",
        "confianca": "ALTA",
        "obs": "Simulado: 'SIMULADO EXATO NATUREZAS TESSAT 2025 / TARDE / 20 questoes Ciencias da Natureza'. Gabarito: resolucoes de Bio/Fis/Qui"
    },
    {
        "evento": "TRADICIONAIS 04/04/2026",
        "turno": "SEM TURNO (horario 10h30-12h30)",
        "simulado_original": "Simulado TRADICIONAIS (04 de Abril).pdf",
        "simulado_padronizado": "EXATO_TRADICIONAIS_04ABRIL2026_SIMULADO.pdf",
        "gabarito_original": null,
        "gabarito_padronizado": null,
        "confianca": "ALTA",
        "obs": "Sem gabarito correspondente encontrado. Simulado de 40 questoes (5 por disciplina) datado 04/04/2026"
    },
]
relatorio["associacoes"] = ASSOCIACOES

# Duplicatas
DUPS = []
for entrada in MAPEAMENTO:
    orig, tipo, evento, turno, nome_pad, dup_de = entrada
    if tipo == "duplicata":
        DUPS.append({
            "arquivo": orig,
            "original_correspondente": dup_de,
            "motivo": "Hash MD5 das primeiras 2000 caracteres identico ao original"
        })

# Caso especial: GABARITO TARDE TESSAT tem hash igual ao MANHA
DUPS.append({
    "arquivo": "GABARITO - TARDE - TESSAT (1).pdf",
    "original_correspondente": "GABARITO - MANHÃƒ - TESSAT.pdf",
    "motivo": "Hash MD5 identico (e4c7ca64fd6813eff040d24c3b1c22d0) â€” ambos PDFs-imagem de 1 pagina sem texto"
})
relatorio["duplicatas"] = DUPS

# Material de apoio
MAT = [
    {
        "arquivo_original": "Cartilha MED UFT 2025.pdf",
        "arquivo_padronizado": "EXATO_CARTILHA_MED_UFT_2025.pdf",
        "tipo": "cartilha_informativa",
        "descricao": "Cartilha independente produzida pela Turma 37 de Medicina da UFT. Nao e documento oficial do EXATO."
    },
    {
        "arquivo_original": "RedaÃ§Ã£o Nota Mil ENEM X Nota 100 ExaTO.pdf",
        "arquivo_padronizado": "EXATO_REDACAO_NOTA_MIL_ENEM_vs_EXATO.pdf",
        "tipo": "material_redacao",
        "descricao": "Redacao nota mil (ENEM) vs nota 100 (EXATO), com exemplo de texto dissertativo-argumentativo. Autoria: 'Pai das Letras 2024'."
    },
    {
        "arquivo_original": "conexao-uft-exato.pdf",
        "arquivo_padronizado": "EXATO_CONEXAO_UFT_QUESTOES_MATEMATICA.pdf",
        "tipo": "banco_questoes_revisao",
        "descricao": "Colecao de questoes de Matematica do vestibular UFT (2010 em diante) + 2 edicoes recentes. 51 paginas."
    },
    {
        "arquivo_original": "lista-01---projeto-2020.pdf",
        "arquivo_padronizado": "EXATO_LISTA01_MATEMATICA_2020.pdf",
        "tipo": "lista_exercicios",
        "descricao": "Lista 01 de Matematica - Projeto 2020. 7 paginas."
    },
    {
        "arquivo_original": "lista-02-proj-2020.pdf",
        "arquivo_padronizado": "EXATO_LISTA02_MATEMATICA_2020.pdf",
        "tipo": "lista_exercicios",
        "descricao": "Lista 02 de Matematica - Projeto 2020. 7 paginas."
    },
    {
        "arquivo_original": "trilha-exato-parte-1.pdf",
        "arquivo_padronizado": "EXATO_TRILHA_PARTE1_SEMANA1.pdf",
        "tipo": "trilha_estudo",
        "descricao": "Trilha EXATO - Semana 1. 70 paginas de exercicios de revisao."
    },
    {
        "arquivo_original": "trilha-exato-parte-2.pdf",
        "arquivo_padronizado": "EXATO_TRILHA_PARTE2_SEMANA4.pdf",
        "tipo": "trilha_estudo",
        "descricao": "Trilha EXATO - Semana 4. 77 paginas de exercicios de revisao."
    },
    {
        "arquivo_original": "trilha-exato-parte-3.pdf",
        "arquivo_padronizado": "EXATO_TRILHA_PARTE3_SEMANA7.pdf",
        "tipo": "trilha_estudo",
        "descricao": "Trilha EXATO - Semana 7. 91 paginas de exercicios de revisao."
    },
]
relatorio["material_apoio"] = MAT

# Nao identificados
relatorio["nao_identificados"] = [
    {
        "arquivo": "GABARITO - MANHÃƒ - TESSAT.pdf",
        "motivo": "PDF de 1 pagina com conteudo puramente visual (imagem escaneada). Texto nao extraivel via pdfplumber. Pode ser gabarito do 2o Simulado TESSAT 2025 (turno MANHA), mas nao e possivel confirmar sem OCR.",
        "acao_sugerida": "Aplicar OCR (pytesseract) para extrair texto e reclassificar"
    }
]

# Inconsistencias
relatorio["inconsistencias"] = [
    {
        "arquivo": "Simulado EXATO MANHÃƒ.pdf / Simulado EXATO TARDE.pdf",
        "problema": "Nome do arquivo nao indica data nem edicao. Conteudo revela ser o '1Â° Simulado Oficial EXATO TESSAT 2025' (36 questoes na manha, prova objetiva na tarde). Classificado como '1_simulado' para diferenciar do 2o Simulado.",
        "severidade": "BAIXA"
    },
    {
        "arquivo": "GABARITO - MANHÃƒ - TESSAT.pdf e GABARITO - TARDE - TESSAT (1).pdf",
        "problema": "Ambos sao PDFs-imagem (sem texto), hash identico. O sufixo '(1)' indica duplicata. Nao e possivel confirmar a qual simulado pertencem sem OCR. Possivelmente sao gabaritos do 2o Simulado TESSAT 2025.",
        "severidade": "MEDIA"
    },
    {
        "arquivo": "Simulado TRADICIONAIS (04 de Abril).pdf",
        "problema": "Nao ha gabarito correspondente na pasta. O simulado menciona que o gabarito seria enviado 30 minutos apos o inicio (11h00), sugerindo envio digital e nao em PDF.",
        "severidade": "BAIXA"
    },
    {
        "arquivo": "Gabarito Comentado - EXATO (29 de abril, 2026).pdf",
        "problema": "Um unico arquivo de gabarito cobre MANHA e TARDE. Copiado uma vez em gabaritos/29_abril_2026/ com nome indicando ambos os turnos.",
        "severidade": "INFO"
    },
]

# Salvar relatorio
caminho_relatorio = os.path.join(DESTINO, "relatorio_exato.json")
with open(caminho_relatorio, "w", encoding="utf-8") as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)
print(f"\nRelatorio salvo: {caminho_relatorio}")

# â”€â”€ Gerar metadata_integracao.json â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
metadata = {
    "fonte": "EXATO",
    "tipo_conteudo": "simulado_cursinho",
    "descricao": "Simulados do cursinho EXATO (Araguaina/TO) para preparacao ao TESSAT (Exame de Acesso ao Ensino Superior do Tocantins) e ENEM",
    "separacao_banco": "tabela_questoes com campo fonte='EXATO' para separar de fonte='ENEM'",
    "eventos_identificados": [
        {
            "id": "CICLO_ZERO",
            "nome": "Ciclo Zero",
            "descricao": "Simulado inicial com foco em conteudos tradicionais (Linguagens + Ciencias Humanas + Redacao / Matematica + Ciencias da Natureza)",
            "turnos": ["MANHA", "TARDE"],
            "questoes_por_turno": {"MANHA": 30, "TARDE": 30},
            "status": "completo"
        },
        {
            "id": "OUTUBRO_2025",
            "nome": "Simulado EXATO Outubro 2025",
            "descricao": "SIMULADO EXATO TESSAT 2025 - outubro. Linguagens+Humanas+Redacao (manha) / Matematica+Naturezas (tarde)",
            "turnos": ["MANHA", "TARDE"],
            "questoes_por_turno": {"MANHA": 40, "TARDE": 40},
            "status": "completo"
        },
        {
            "id": "1_SIMULADO",
            "nome": "1Âº Simulado Oficial EXATO TESSAT 2025",
            "descricao": "Primeiro Simulado Oficial EXATO TESSAT 2025. MANHA: 36 questoes (Linguagens+Matematica+Redacao). TARDE: prova objetiva",
            "turnos": ["MANHA", "TARDE"],
            "questoes_por_turno": {"MANHA": 36, "TARDE": "nao_confirmado"},
            "status": "completo"
        },
        {
            "id": "2_SIMULADO",
            "nome": "2Âº Simulado Oficial EXATO TESSAT 2025",
            "descricao": "Segundo Simulado Oficial EXATO TESSAT 2025. 40 questoes por turno.",
            "turnos": ["MANHA", "TARDE"],
            "questoes_por_turno": {"MANHA": 40, "TARDE": 40},
            "status": "completo"
        },
        {
            "id": "29_ABRIL_2026",
            "nome": "Simulado EXATO 29 de Abril 2026 (1a Edicao EXATO 2026)",
            "descricao": "Exame de Acesso ao Ensino Superior do Tocantins EXATO 2026 - 1a Edicao. Simulado de 29/04/2026.",
            "turnos": ["MANHA", "TARDE"],
            "questoes_por_turno": "nao_confirmado",
            "status": "completo"
        },
        {
            "id": "NATUREZAS",
            "nome": "Simulado EXATO Naturezas TESSAT 2025",
            "descricao": "Simulado especifico de Ciencias da Natureza. 20 questoes. Turno: TARDE.",
            "turnos": ["TARDE"],
            "questoes_por_turno": {"TARDE": 20},
            "status": "completo"
        },
        {
            "id": "TRADICIONAIS",
            "nome": "Simulado Tradicionais 04 de Abril 2026",
            "descricao": "Simulado de 40 questoes (5 por disciplina: Portugues, Geografia, Historia, Filosofia/Sociologia, Matematica, Fisica, Quimica, Biologia). Horario 10h30-12h30.",
            "turnos": ["SEM_TURNO"],
            "questoes_por_turno": {"SEM_TURNO": 40},
            "status": "sem_gabarito"
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
        "explicacao_ia": True,
        "busca_contextual": True,
        "filtro_area": True,
        "filtro_disciplina": True,
        "metricas_desempenho": True,
        "tira_teima": True,
        "simulado_cronometrado": True,
        "correcao_automatica": True
    },
    "recursos_desativados": {
        "competencias_h01_h30": False,
        "pagina_pdf_original": False,
        "gabarito_oficial_enem": False
    },
    "notas_tecnicas": [
        "Gabaritos TESSAT (MANHA/TARDE) sao PDFs-imagem (1 pag, sem texto). Requerem OCR antes de uso.",
        "Gabarito do 29 de Abril 2026 cobre ambos os turnos em um unico arquivo.",
        "Simulado TRADICIONAIS nao possui gabarito em PDF â€” gabarito provavelmente enviado digitalmente aos alunos.",
        "Todos os simulados EXATO sao para o TESSAT (vestibular estadual do Tocantins), nao ENEM diretamente.",
        "Material de apoio (trilhas, listas, cartilha, conexao-uft) nao deve ser importado como questoes â€” uso apenas como referencia."
    ]
}

caminho_meta = os.path.join(DESTINO, "metadata_integracao.json")
with open(caminho_meta, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
print(f"Metadata salvo: {caminho_meta}")

# â”€â”€ Resumo final â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n" + "="*60)
print("RESUMO FINAL")
print("="*60)
print(f"  Simulados unicos:     {relatorio['resumo']['simulados']}")
print(f"  Gabaritos unicos:     {relatorio['resumo']['gabaritos']}")
print(f"  Material de apoio:    {relatorio['resumo']['material_apoio']}")
print(f"  Duplicatas:           {relatorio['resumo']['duplicatas']}")
print(f"  Nao identificados:    {relatorio['resumo']['nao_identificados']}")
print(f"  Corrompidos:          {relatorio['resumo']['corrompidos']}")
print(f"  Associacoes SimGab:   {len([a for a in ASSOCIACOES if a['gabarito_original']])}")
print(f"  Inconsistencias:      {len(relatorio['inconsistencias'])}")

