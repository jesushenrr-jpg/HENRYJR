-- migration_frases.sql
-- Executar no Supabase SQL Editor: https://supabase.com/dashboard/project/bmhudlpihwxvaelokugh/editor

CREATE TABLE IF NOT EXISTS frases (
  id         BIGSERIAL PRIMARY KEY,
  titulo     TEXT NOT NULL,
  texto      TEXT NOT NULL,
  categoria  TEXT NOT NULL DEFAULT '',
  criado_em  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE frases ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'frases' AND policyname = 'service_role_all'
  ) THEN
    CREATE POLICY "service_role_all" ON frases FOR ALL USING (true);
  END IF;
END $$;
