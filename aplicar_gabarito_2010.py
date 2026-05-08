from docx import Document
import json
import os
import shutil
from datetime import datetime

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
CAMINHO_WORD = r"C:\Projetos\henryjr\Gabarito_2010_Preencher.docx"
CAMINHO_JSON = r"C:\Projetos\henryjr\dados\json\enem_2010.json"

# ─── EXECUÇÃO ─────────────────────────────────────────────────────────────────
def aplicar_gabaritos():
    print("\n" + "="*60)
    print("  APLICANDO GABARITOS 2010 — WORD → JSON")
    print("="*60)

    # Verifica arquivos
    for caminho, nome in [(CAMINHO_WORD, "Word"), (CAMINHO_JSON, "JSON")]:
        if not os.path.exists(caminho):
            print(f"\n❌ Arquivo não encontrado: {caminho}")
            print(f"   Verifique o caminho de {nome} no início do script.")
            return

    # ── Extrai gabaritos do Word ───────────────────────────────────────
    print("\n📖 Lendo gabaritos do Word...")
    doc = Document(CAMINHO_WORD)
    gabaritos_word = {}

    for tabela in doc.tables[2:4]:
        for row in tabela.rows[1:]:
            cells = [c.text.strip() for c in row.cells]
            for q_col, g_col in [(0, 1), (2, 3)]:
                q_texto = cells[q_col]
                g_texto = cells[g_col].upper()
                if not q_texto or 'Questão' not in q_texto:
                    continue
                try:
                    num = int(q_texto.replace('Questão', '').strip())
                except:
                    continue
                if g_texto in ['A', 'B', 'C', 'D', 'E']:
                    gabaritos_word[num] = g_texto

    print(f"   ✅ {len(gabaritos_word)} gabaritos lidos do Word")

    # ── Faz backup do JSON original ────────────────────────────────────
    backup = CAMINHO_JSON.replace(".json", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    shutil.copy2(CAMINHO_JSON, backup)
    print(f"\n💾 Backup criado: {os.path.basename(backup)}")

    # ── Carrega e atualiza o JSON ──────────────────────────────────────
    print("\n🔄 Atualizando JSON...")
    with open(CAMINHO_JSON, encoding="utf-8") as f:
        questoes = json.load(f)

    ja_tinham   = 0
    atualizadas = 0
    conflitos   = []

    for q in questoes:
        num = q["numero"]
        gab_word = gabaritos_word.get(num)
        gab_atual = q.get("gabarito")

        if gab_word:
            if gab_atual and gab_atual != gab_word:
                # Conflito: já tinha gabarito diferente
                conflitos.append(f"Q{num:03d}: JSON={gab_atual} vs Word={gab_word} → mantido Word")
                q["gabarito"] = gab_word
                atualizadas += 1
            elif not gab_atual:
                q["gabarito"] = gab_word
                atualizadas += 1
            else:
                ja_tinham += 1  # Mesmo valor, sem mudança necessária

    # Salva JSON atualizado
    with open(CAMINHO_JSON, "w", encoding="utf-8") as f:
        json.dump(questoes, f, ensure_ascii=False, indent=2)

    # ── Relatório final ────────────────────────────────────────────────
    sem_gabarito_final = [q["numero"] for q in questoes if not q.get("gabarito")]
    total_com_gab = len(questoes) - len(sem_gabarito_final)

    print("\n" + "="*60)
    print("  RELATÓRIO FINAL")
    print("="*60)
    print(f"\n  Total de questões no JSON:    {len(questoes)}")
    print(f"  Gabaritos aplicados do Word:  {atualizadas}")
    print(f"  Já tinham gabarito (ok):      {ja_tinham}")
    print(f"  Com gabarito agora:           {total_com_gab}")
    print(f"  Ainda sem gabarito:           {len(sem_gabarito_final)}")

    if conflitos:
        print(f"\n  ⚠️  Conflitos resolvidos (Word prevaleceu):")
        for c in conflitos:
            print(f"     {c}")

    if sem_gabarito_final:
        print(f"\n  ❓ Questões ainda sem gabarito: {sem_gabarito_final}")
        print("     Verifique se estas questões foram anuladas pelo INEP.")
    else:
        print("\n  🎉 COMPLETO — todas as questões de 2010 têm gabarito!")

    print(f"\n  📁 JSON atualizado: {CAMINHO_JSON}")
    print(f"  💾 Backup salvo em: {backup}")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    aplicar_gabaritos()