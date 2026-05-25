-- Migração: Adicionar suporte a versões no Tira Teima
-- Execute no Supabase SQL Editor:
-- https://supabase.com/dashboard/project/bmhudlpihwxvaelokugh/sql/new

-- 1. Adicionar coluna versao_tt na tabela questoes_erradas
--    Representa em qual versão do Tira Teima a questão foi errada pela última vez.
--    Versão 1 = primeira vez que errou; 2 = errou no Tira Teima V1; etc.
ALTER TABLE questoes_erradas
  ADD COLUMN IF NOT EXISTS versao_tt INTEGER NOT NULL DEFAULT 1;

-- 2. Adicionar coluna para marcar se a questão foi "zerada" (acertou no Tira Teima)
--    Questões com zerada=true não aparecem mais no Tira Teima
ALTER TABLE questoes_erradas
  ADD COLUMN IF NOT EXISTS zerada BOOLEAN NOT NULL DEFAULT FALSE;

-- 3. Tabela tira_teima: registro de cada ciclo/versão por usuário
CREATE TABLE IF NOT EXISTS tira_teima (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id    UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  versao        INTEGER NOT NULL DEFAULT 1,
  questoes_ids  JSONB NOT NULL DEFAULT '[]',  -- IDs das questões nesta versão
  total         INTEGER NOT NULL DEFAULT 0,
  acertos       INTEGER NOT NULL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'em_andamento', 'concluido')),
  criado_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
  concluido_em  TIMESTAMPTZ
);

-- RLS para tira_teima
ALTER TABLE tira_teima ENABLE ROW LEVEL SECURITY;

CREATE POLICY "usuarios_proprios_tt" ON tira_teima
  FOR ALL USING (auth.uid() = usuario_id);

-- 4. Índice para busca eficiente por usuario + versao
CREATE INDEX IF NOT EXISTS idx_questoes_erradas_versao
  ON questoes_erradas(usuario_id, versao_tt, acertou);

CREATE INDEX IF NOT EXISTS idx_tira_teima_usuario
  ON tira_teima(usuario_id, versao DESC);

-- Como usar:
-- Tira Teima atual = versao_tt mais alta onde acertou = false e zerada = false
-- Ao concluir uma sessão de Tira Teima:
--   - Para cada questão acertada: UPDATE questoes_erradas SET zerada = true WHERE ...
--   - Para cada questão errada: INSERT uma nova entrada com versao_tt = versao_atual + 1
-- A próxima versão do Tira Teima = questões com versao_tt = max_versao + 1
