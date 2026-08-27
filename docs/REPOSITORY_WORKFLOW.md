# Fluxo seguro do repositório

## Fonte de verdade

- Repositório remoto: `origin`.
- Branch de produção: `main`.
- Aplicação implantada: `frontend/`.
- Dados brutos e PDFs locais não devem ser publicados por padrão.

## Antes de alterar

1. Execute `git fetch origin main`.
2. Confirme que a branch de trabalho parte de `origin/main`.
3. Crie uma branch com prefixo `codex/` para mudanças novas.
4. Não use a cópia auxiliar `.codex-clean-publish` como fonte permanente.

## Conteúdo de commits

- Adicione arquivos explicitamente; evite `git add .` neste projeto.
- Nunca inclua `.env`, chaves, logs, caches, builds ou arquivos de diagnóstico.
- Separe código, migrações e correções de dados em commits distintos.
- Uma correção no banco deve ter relatório de auditoria e mecanismo de rollback.

## Validação do frontend

Execute em `frontend/`:

```powershell
npm run lint
npm run build
```

## Publicação

1. Revise `git diff --cached`.
2. Confirme que o commit esperado é descendente de `origin/main`.
3. Envie a branch ou `main`, conforme o fluxo aprovado.
4. No Vercel, confirme commit, ambiente `Production` e domínio atribuído.
5. Teste autenticação, busca, filtros e explicação por IA.

## Dados e credenciais

- Credenciais ficam somente em `.env` local e nas variáveis Secret do Vercel.
- PDFs e resultados intermediários ficam fora do Git, salvo decisão explícita.
- Scripts de correção devem suportar modo somente leitura/dry-run antes de gravar.
- Não exclua conjuntos locais sem inventário, backup e autorização do responsável.
