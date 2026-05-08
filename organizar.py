import os
import shutil

# ─── CONFIGURAÇÃO ─────────────────────────────────────────────────────────────
# Aponte esta variável para a pasta onde estão seus PDFs baixados
PASTA_ORIGEM = r"C:\Projetos\HENRYJR\dados\provas"

# Palavras-chave para identificar cada tipo de arquivo
# Edite aqui se os seus arquivos tiverem nomes diferentes
PALAVRAS_DIA1 = ["dia 1", "primeiro", "1dia", "linguagens", "humanas", "d1"]
PALAVRAS_DIA2 = ["dia 2", "segundo", "2dia", "natureza", "matematica", "d2"]
PALAVRAS_GAB1 = ["gabarito_dia1", "gab dia 1", "gabarito1", "gab1", "gabarito_1"]
PALAVRAS_GAB2 = ["gabarito_dia2", "gab dia 2", "gabarito2", "gab2", "gabarito_2"]

# ─── FUNÇÕES ──────────────────────────────────────────────────────────────────
def identificar_tipo(nome_arquivo):
    """Identifica o tipo do PDF pelo nome atual do arquivo."""
    nome = nome_arquivo.lower()
    
    # Gabaritos primeiro (mais específicos)
    for palavra in PALAVRAS_GAB1:
        if palavra in nome:
            return "gabarito_dia1.pdf"
    for palavra in PALAVRAS_GAB2:
        if palavra in nome:
            return "gabarito_dia2.pdf"
    
    # Provas
    for palavra in PALAVRAS_DIA1:
        if palavra in nome:
            return "dia1.pdf"
    for palavra in PALAVRAS_DIA2:
        if palavra in nome:
            return "dia2.pdf"
    
    return None  # Não identificado

def organizar_pastas():
    print("\n" + "="*60)
    print("  ORGANIZADOR DE PDFs — BANCO DE QUESTÕES ENEM")
    print("="*60)
    
    if not os.path.exists(PASTA_ORIGEM):
        print(f"\n❌ Pasta não encontrada: {PASTA_ORIGEM}")
        print("   Verifique o caminho em PASTA_ORIGEM no início do script.")
        return
    
    arquivos_renomeados = []
    arquivos_nao_identificados = []
    
    # Percorre todas as subpastas (uma por ano)
    for ano in sorted(os.listdir(PASTA_ORIGEM)):
        pasta_ano = os.path.join(PASTA_ORIGEM, ano)
        
        if not os.path.isdir(pasta_ano):
            continue
        
        print(f"\n📁 Processando ano: {ano}")
        
        pdfs = [f for f in os.listdir(pasta_ano) if f.lower().endswith(".pdf")]
        
        if not pdfs:
            print(f"   ⚠️  Nenhum PDF encontrado nesta pasta")
            continue
        
        for pdf in pdfs:
            caminho_atual = os.path.join(pasta_ano, pdf)
            novo_nome = identificar_tipo(pdf)
            
            if novo_nome:
                caminho_novo = os.path.join(pasta_ano, novo_nome)
                
                # Evita sobrescrever se já tem o nome correto
                if pdf == novo_nome:
                    print(f"   ✅ {pdf} — já está no padrão correto")
                    continue
                
                # Renomeia o arquivo
                if os.path.exists(caminho_novo):
                    print(f"   ⚠️  {pdf} → {novo_nome} — JÁ EXISTE um arquivo com esse nome, pulando")
                    continue
                
                os.rename(caminho_atual, caminho_novo)
                print(f"   ✅ {pdf} → {novo_nome}")
                arquivos_renomeados.append(f"{ano}/{pdf} → {novo_nome}")
            else:
                print(f"   ❓ {pdf} — não identificado (veja lista abaixo)")
                arquivos_nao_identificados.append(f"{ano}/{pdf}")
    
    # Relatório final
    print("\n" + "="*60)
    print(f"  RELATÓRIO FINAL")
    print("="*60)
    print(f"\n✅ Arquivos renomeados: {len(arquivos_renomeados)}")
    
    if arquivos_nao_identificados:
        print(f"\n❓ Arquivos NÃO identificados ({len(arquivos_nao_identificados)}):")
        print("   (Esses precisam ser renomeados manualmente)")
        for arq in arquivos_nao_identificados:
            print(f"   - {arq}")
        print("\n   Nomes esperados após renomear:")
        print("   - dia1.pdf           → Prova 1º dia")
        print("   - dia2.pdf           → Prova 2º dia")
        print("   - gabarito_dia1.pdf  → Gabarito 1º dia")
        print("   - gabarito_dia2.pdf  → Gabarito 2º dia")
    else:
        print("\n🎉 Todos os arquivos foram identificados e organizados!")
    
    print("\n" + "="*60 + "\n")

# ─── EXECUÇÃO ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nEste script vai RENOMEAR os seus PDFs automaticamente.")
    print("Os arquivos não serão deletados — apenas renomeados.")
    confirmar = input("\nDeseja continuar? (s/n): ").strip().lower()
    
    if confirmar == "s":
        organizar_pastas()
    else:
        print("\nOperação cancelada. Nenhum arquivo foi alterado.\n")