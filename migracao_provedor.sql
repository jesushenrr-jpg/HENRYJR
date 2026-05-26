-- migracao_provedor.sql
-- Adiciona coluna provedor para identificar elaborador de simulados ENEM
-- (BERNOULLI, SAS, POLIEDRO, FARIAS_BRITO, SOMOS)
-- Para ENEM real, EXATO e UFT: NULL

ALTER TABLE questoes ADD COLUMN IF NOT EXISTS provedor TEXT NULL;
CREATE INDEX IF NOT EXISTS idx_questoes_provedor ON questoes(provedor);
