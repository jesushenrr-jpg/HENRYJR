# Observabilidade operacional

## Eventos estruturados

As rotas de IA escrevem uma linha JSON por evento, sem registrar prompts ou chaves.

Eventos de busca:

- `ai.search.success`
- `ai.search.config_missing`
- `ai.search.network_error`
- `ai.search.provider_error`

Eventos de explicação:

- `ai.explain.stream_started`
- `ai.explain.config_missing`
- `ai.explain.network_error`
- `ai.explain.provider_error`
- `ai.explain.empty_stream`

Campos úteis: `request_id`, `duration_ms`, `provider_status` e `event`.

## Diagnóstico no Vercel

1. Abra `Logs` no projeto.
2. Filtre por `ai.search` ou `ai.explain`.
3. Para erros do provedor, confira `provider_status`:
   - `400`: parâmetros/modelo;
   - `401` ou `403`: credencial;
   - `429`: cota ou limite;
   - `5xx`: indisponibilidade do provedor.
4. Compare `request_id` com o cabeçalho `X-Request-Id` quando disponível.

## Privacidade

Não registrar:

- chaves e tokens;
- cookies ou cabeçalhos de autorização;
- texto integral das questões;
- consultas pessoais do usuário;
- respostas completas do provedor.

## Checklist após deploy

- O commit correto está em Production.
- `henryjr.vercel.app` aponta para o deploy atual.
- Busca IA gera `ai.search.success`.
- Explicação gera `ai.explain.stream_started`.
- Não há sequência anormal de `provider_error` ou respostas `429`.
