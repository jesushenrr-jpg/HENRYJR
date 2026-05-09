"""
importar_para_supabase.py — Importa todas as questoes dos JSONs v2 para o Supabase.

Uso:
    python importar_para_supabase.py

Seguranca:
    Operacao completamente idempotente — pode ser executada multiplas vezes
    sem risco de duplicatas (upsert via UNIQUE(ano, dia, numero)).

Pre-requisito:
    O schema da tabela ja deve ter sido criado no Supabase Dashboard
    rodando o arquivo schema_supabase.sql.
"""

import json
import sys
from pathlib import Path

import supabase_client as sb

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASTA_JSON_V2 = Path(r"C:\PROJETOS\HENRYJR\dados\json_v2")


def carregar_todos_jsons() -> list:
    todas = []
    arquivos = sorted(PASTA_JSON_V2.glob("enem_*.json"))
    if not arquivos:
        print("ERRO: Nenhum arquivo enem_*.json encontrado em", PASTA_JSON_V2)
        sys.exit(1)

    print("Arquivos encontrados:")
    for jp in arquivos:
        with open(jp, encoding="utf-8") as f:
            questoes = json.load(f)
        todas.extend(questoes)
        print(f"  {jp.name}: {len(questoes)} questoes")

    return todas


def main():
    print("=" * 60)
    print("  Importacao para Supabase — HenryJr")
    print("=" * 60)

    # 1. Verificar conectividade
    print("\n[1/3] Verificando conexao com Supabase...")
    if not sb.ping():
        print("  ERRO: Supabase inacessivel. Verifique sua conexao.")
        sys.exit(1)
    print("  OK — Supabase acessivel.")

    # 2. Carregar JSONs
    print("\n[2/3] Carregando JSONs locais...")
    todas = carregar_todos_jsons()
    print(f"\n  Total: {len(todas)} questoes")

    # 3. Upsert em lotes
    print("\n[3/3] Enviando para o Supabase em lotes de 100...")
    ok, erros = sb.upsert_lote(todas, tamanho=100)

    # Resultado
    print("\n" + "=" * 60)
    print(f"  OK:    {ok}")
    print(f"  Erros: {erros}")
    print(f"  Total: {len(todas)}")

    if erros == 0:
        print("\n  Importacao concluida com sucesso!")
        print("  O banco esta pronto para uso pelo gerenciador e pelo frontend.")
    else:
        print(f"\n  ATENCAO: {erros} questoes nao foram importadas.")
        print("  Verifique as mensagens de erro acima e tente novamente.")
        print("  A operacao e idempotente — re-executar nao duplica dados.")

    print("=" * 60)


if __name__ == "__main__":
    main()
