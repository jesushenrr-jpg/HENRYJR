-- migracao_unique_fontes.sql
-- Corrige a constraint UNIQUE da tabela questoes para suportar múltiplas fontes.
--
-- Problema anterior:
--   UNIQUE (ano, dia, numero) — apenas 3 colunas, sem fonte/provedor/turno.
--   Ao subir UFT 2019 MANHA + TARDE, ambos têm (2019, 'exato', 1) → conflito!
--   Ao subir simulados ENEM de provedores diferentes, Bernoulli Q1 e SAS Q1
--   compartilham (2023, 'simu_dia1', 1) → conflito!
--
-- Solução:
--   Índice único funcional com COALESCE para tratar NULLs (PostgreSQL trata
--   NULL != NULL em constraints, quebrando unicidade para colunas nullable).
--   Inclui: fonte + COALESCE(ano,-1) + dia + numero + COALESCE(provedor,'')
--
-- Após esta migração:
--   • UFT:  dia = 'manha' ou 'tarde' (turno codificado no dia)
--     → (UFT, 2019, 'manha', 1, '') ≠ (UFT, 2019, 'tarde', 1, '') ✓
--   • EXATO provas: dia = 'exato_manha' ou 'exato_tarde'
--     → (EXATO, 2024, 'exato_manha', 1, '') ≠ (EXATO, 2024, 'exato_tarde', 1, '') ✓
--   • ENEM simulados: dia = 'simu_dia1'/'simu_dia2', provedor = 'BERNOULLI'/'SAS'/...
--     → (ENEM, 2023, 'simu_dia1', 1, 'BERNOULLI') ≠ (..., 'SAS') ✓
--   • ENEM real: dia = 'dia1'/'dia2', provedor = NULL → COALESCE = ''
--     → (ENEM, 2019, 'dia1', 1, '') — único ✓
--   • EXATO simulados: ano = NULL → COALESCE = -1
--     → (EXATO, -1, 'exato', 1, '') — único por número global ✓
--
-- COMO EXECUTAR:
--   Abrir o Supabase Dashboard → SQL Editor → colar e rodar este script.
--
-- STATUS: ⏳ Pendente de execução manual no Supabase Dashboard

-- 1. Remove constraint antiga (3 colunas sem fonte)
ALTER TABLE questoes DROP CONSTRAINT IF EXISTS questoes_unique;

-- 2. Cria índice único funcional com 6 dimensões
--    (usa COALESCE para evitar o comportamento NULL != NULL do PostgreSQL)
--    Inclui 'evento' para distinguir SIM_01 vs SIM_02 do mesmo provedor no mesmo ano.
CREATE UNIQUE INDEX questoes_unique
  ON questoes (
    fonte,
    COALESCE(ano, -1),
    dia,
    numero,
    COALESCE(evento, ''),
    COALESCE(provedor, '')
  );
