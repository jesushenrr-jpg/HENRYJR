-- migracao_tipo.sql
-- Execução: Supabase Dashboard → SQL Editor → Run
-- Todos os comandos são idempotentes (podem ser re-executados sem efeito colateral).

-- 1. Adiciona coluna tipo
ALTER TABLE questoes
  ADD COLUMN IF NOT EXISTS tipo TEXT NOT NULL DEFAULT 'PROVA';

-- 2. Backfill: ENEM = provas passadas, EXATO = simulados preditivos
UPDATE questoes SET tipo = 'PROVA'    WHERE fonte = 'ENEM';
UPDATE questoes SET tipo = 'SIMULADO' WHERE fonte = 'EXATO';

-- 3. Índice para filtros rápidos
CREATE INDEX IF NOT EXISTS idx_questoes_tipo ON questoes(tipo);
