-- =============================================================================
-- HenryJr — Schema Supabase
-- Execute no Supabase Dashboard > SQL Editor
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Tabela questoes
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS questoes (
    id                   BIGSERIAL    PRIMARY KEY,
    numero               INTEGER      NOT NULL,
    ano                  INTEGER      NOT NULL,
    dia                  TEXT         NOT NULL,   -- 'dia1' | 'dia2'
    area                 TEXT,
    competencia          TEXT,                    -- 'H01'-'H30'
    enunciado            JSONB        NOT NULL DEFAULT '[]',
    comando              TEXT,
    alternativas         JSONB        NOT NULL DEFAULT '{}',
    gabarito             TEXT,                    -- 'A'-'E' | null (anulada)
    confianca            REAL,
    revisado             BOOLEAN      NOT NULL DEFAULT FALSE,
    anulada              BOOLEAN      NOT NULL DEFAULT FALSE,
    tem_imagem           BOOLEAN      NOT NULL DEFAULT FALSE,
    pagina_pdf           INTEGER,
    imagens              JSONB        NOT NULL DEFAULT '[]',
    imagens_alternativas JSONB                 DEFAULT '{}',
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT questoes_unique UNIQUE (ano, dia, numero)
);

-- -----------------------------------------------------------------------------
-- Trigger: atualiza updated_at automaticamente em cada UPDATE
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION atualizar_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tg_questoes_updated_at ON questoes;
CREATE TRIGGER tg_questoes_updated_at
    BEFORE UPDATE ON questoes
    FOR EACH ROW EXECUTE FUNCTION atualizar_updated_at();

-- -----------------------------------------------------------------------------
-- Indices — queries frequentes do frontend
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_questoes_ano_dia      ON questoes (ano, dia);
CREATE INDEX IF NOT EXISTS idx_questoes_area         ON questoes (area);
CREATE INDEX IF NOT EXISTS idx_questoes_competencia  ON questoes (competencia);
CREATE INDEX IF NOT EXISTS idx_questoes_gabarito     ON questoes (gabarito);
CREATE INDEX IF NOT EXISTS idx_questoes_revisado     ON questoes (revisado);
CREATE INDEX IF NOT EXISTS idx_questoes_tem_imagem   ON questoes (tem_imagem);
CREATE INDEX IF NOT EXISTS idx_questoes_anulada      ON questoes (anulada);

-- -----------------------------------------------------------------------------
-- Row Level Security
--   - Leitura: qualquer chave (publica / anon)
--   - Escrita: apenas service_role (gerenciador e scripts de importacao)
--             o service_role bypassa RLS por padrao — politica apenas
--             como documentacao explicita do intento de seguranca
-- -----------------------------------------------------------------------------
ALTER TABLE questoes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "leitura_publica"    ON questoes;
DROP POLICY IF EXISTS "escrita_service"    ON questoes;

CREATE POLICY "leitura_publica"
    ON questoes FOR SELECT
    USING (true);

CREATE POLICY "escrita_service"
    ON questoes FOR ALL
    USING     (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- -----------------------------------------------------------------------------
-- Verificacao final
-- -----------------------------------------------------------------------------
SELECT
    'questoes' AS tabela,
    COUNT(*)   AS total_questoes
FROM questoes;
