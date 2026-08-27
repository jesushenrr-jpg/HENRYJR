# Segurança e credenciais

## Incidente identificado em 26/08/2026

O histórico Git contém chaves de IA e uma chave administrativa do Supabase. Remover os valores da versão atual não invalida cópias existentes em commits, clones ou caches.

## Ações obrigatórias antes do próximo deploy

1. Revogar e gerar novamente a chave `service_role` do Supabase exposta.
2. Revogar e gerar novamente as chaves Groq e Gemini expostas.
3. Atualizar as variáveis nos ambientes locais, Vercel e demais serviços de deploy.
4. Confirmar que a aplicação funciona apenas com as novas chaves.
5. Reescrever o histórico Git com `git filter-repo` e coordenar novo clone para todos que usam o repositório.
6. Habilitar secret scanning no provedor Git e em CI.

## Variáveis esperadas

Consulte `/.env.example` para scripts Python e `/frontend/.env.example` para a aplicação Next.js. Arquivos `.env` reais e `config.json` não devem ser versionados.

## Regra operacional

Nunca registrar valores reais de credenciais em documentação, planos, logs, exemplos de comandos ou mensagens de commit.
