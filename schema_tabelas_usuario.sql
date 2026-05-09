-- =============================================================================
-- HenryJr — Tabelas de Usuário + Auth
-- Execute no Supabase Dashboard > SQL Editor
-- Pré-requisito: schema_supabase.sql já executado (tabela questoes existe)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- usuarios — perfil público que estende auth.users
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id         UUID         PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome       TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS tg_usuarios_updated_at ON usuarios;
CREATE TRIGGER tg_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION atualizar_updated_at();

-- -----------------------------------------------------------------------------
-- competencias — mapeamento H01–H30 com descrição e área
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS competencias (
    codigo    TEXT PRIMARY KEY,   -- 'H01'-'H30'
    descricao TEXT NOT NULL,
    area      TEXT NOT NULL
);

-- -----------------------------------------------------------------------------
-- simulados — cada simulado gerado (online ou impresso)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS simulados (
    id               BIGSERIAL    PRIMARY KEY,
    usuario_id       UUID         NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo             TEXT         NOT NULL DEFAULT 'online',  -- 'online' | 'impresso'
    filtros          JSONB        NOT NULL DEFAULT '{}',      -- {area, ano, competencia...}
    questoes_ids     BIGINT[]     NOT NULL DEFAULT '{}',      -- ids das questoes
    total_questoes   INTEGER      NOT NULL DEFAULT 0,
    acertos          INTEGER               DEFAULT NULL,
    status           TEXT         NOT NULL DEFAULT 'em_andamento',
    -- 'em_andamento' | 'concluido'
    iniciado_em      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    concluido_em     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_simulados_usuario ON simulados (usuario_id);
CREATE INDEX IF NOT EXISTS idx_simulados_status  ON simulados (status);

-- -----------------------------------------------------------------------------
-- respostas_simulado — resposta do aluno por questão
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS respostas_simulado (
    id          BIGSERIAL    PRIMARY KEY,
    simulado_id BIGINT       NOT NULL REFERENCES simulados(id) ON DELETE CASCADE,
    questao_id  BIGINT       NOT NULL REFERENCES questoes(id),
    resposta    TEXT,                    -- 'A'-'E' | null (não respondida)
    correta     BOOLEAN,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT respostas_unique UNIQUE (simulado_id, questao_id)
);

CREATE INDEX IF NOT EXISTS idx_respostas_simulado ON respostas_simulado (simulado_id);
CREATE INDEX IF NOT EXISTS idx_respostas_questao  ON respostas_simulado (questao_id);

-- -----------------------------------------------------------------------------
-- questoes_erradas — histórico de erros por usuário (avulsas e de simulado)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS questoes_erradas (
    id            BIGSERIAL    PRIMARY KEY,
    usuario_id    UUID         NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    questao_id    BIGINT       NOT NULL REFERENCES questoes(id),
    simulado_id   BIGINT                REFERENCES simulados(id) ON DELETE SET NULL,
    resposta_dada TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_erradas_usuario  ON questoes_erradas (usuario_id);
CREATE INDEX IF NOT EXISTS idx_erradas_questao  ON questoes_erradas (questao_id);

-- -----------------------------------------------------------------------------
-- tira_teima — versões do caderno de erros (V1, V2, V3...)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tira_teima (
    id                  BIGSERIAL    PRIMARY KEY,
    usuario_id          UUID         NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    versao              INTEGER      NOT NULL DEFAULT 1,
    simulado_origem_id  BIGINT                REFERENCES simulados(id) ON DELETE SET NULL,
    questoes_ids        BIGINT[]     NOT NULL DEFAULT '{}',
    status              TEXT         NOT NULL DEFAULT 'pendente',
    -- 'pendente' | 'concluido'
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT tira_teima_versao_unique UNIQUE (usuario_id, versao)
);

CREATE INDEX IF NOT EXISTS idx_tira_teima_usuario ON tira_teima (usuario_id);

-- -----------------------------------------------------------------------------
-- relatorios_erros — questões reportadas pelos usuários
-- Migração futura do relatorio_erros.json local
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS relatorios_erros (
    id          BIGSERIAL    PRIMARY KEY,
    questao_id  BIGINT                REFERENCES questoes(id),
    usuario_id  UUID                  REFERENCES usuarios(id) ON DELETE SET NULL,
    ano         INTEGER      NOT NULL,
    dia         TEXT         NOT NULL,
    numero      INTEGER      NOT NULL,
    tipo_erro   TEXT         NOT NULL,
    descricao   TEXT,
    status      TEXT         NOT NULL DEFAULT 'pendente',
    -- 'pendente' | 'resolvido' | 'rejeitado'
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_relatorios_status ON relatorios_erros (status);

-- =============================================================================
-- Auth: trigger para criar perfil ao registrar novo usuário
-- =============================================================================
CREATE OR REPLACE FUNCTION criar_perfil_usuario()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.usuarios (id, nome, avatar_url)
    VALUES (
        NEW.id,
        COALESCE(
            NEW.raw_user_meta_data->>'full_name',
            NEW.raw_user_meta_data->>'name',
            split_part(NEW.email, '@', 1)
        ),
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tg_criar_perfil_usuario ON auth.users;
CREATE TRIGGER tg_criar_perfil_usuario
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION criar_perfil_usuario();

-- =============================================================================
-- Row Level Security — cada usuário acessa apenas seus próprios dados
-- =============================================================================

-- usuarios: lê e edita apenas o próprio perfil
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "usuario_le_proprio"   ON usuarios;
DROP POLICY IF EXISTS "usuario_edita_proprio" ON usuarios;
CREATE POLICY "usuario_le_proprio"
    ON usuarios FOR SELECT USING (auth.uid() = id);
CREATE POLICY "usuario_edita_proprio"
    ON usuarios FOR UPDATE USING (auth.uid() = id);

-- competencias: leitura pública
ALTER TABLE competencias ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "competencias_publicas" ON competencias;
CREATE POLICY "competencias_publicas"
    ON competencias FOR SELECT USING (true);

-- simulados
ALTER TABLE simulados ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "simulados_proprio_usuario" ON simulados;
CREATE POLICY "simulados_proprio_usuario"
    ON simulados FOR ALL USING (auth.uid() = usuario_id);

-- respostas_simulado
ALTER TABLE respostas_simulado ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "respostas_via_simulado" ON respostas_simulado;
CREATE POLICY "respostas_via_simulado"
    ON respostas_simulado FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM simulados s
            WHERE s.id = simulado_id AND s.usuario_id = auth.uid()
        )
    );

-- questoes_erradas
ALTER TABLE questoes_erradas ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "erradas_proprio_usuario" ON questoes_erradas;
CREATE POLICY "erradas_proprio_usuario"
    ON questoes_erradas FOR ALL USING (auth.uid() = usuario_id);

-- tira_teima
ALTER TABLE tira_teima ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "tira_teima_proprio_usuario" ON tira_teima;
CREATE POLICY "tira_teima_proprio_usuario"
    ON tira_teima FOR ALL USING (auth.uid() = usuario_id);

-- relatorios_erros: qualquer autenticado pode inserir, service_role gerencia
ALTER TABLE relatorios_erros ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "relatorio_insert_auth"   ON relatorios_erros;
DROP POLICY IF EXISTS "relatorio_select_service" ON relatorios_erros;
CREATE POLICY "relatorio_insert_auth"
    ON relatorios_erros FOR INSERT
    WITH CHECK (auth.role() IN ('authenticated', 'service_role'));
CREATE POLICY "relatorio_select_service"
    ON relatorios_erros FOR SELECT
    USING (auth.uid() = usuario_id OR auth.role() = 'service_role');

-- =============================================================================
-- Verificação final
-- =============================================================================
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
