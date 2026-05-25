# Separação PROVA × SIMULADO — Design

**Data:** 2026-05-25
**Status:** Aprovado

---

## Objetivo

Adicionar ao sistema a distinção entre **PROVA** (provas oficiais já aplicadas) e **SIMULADO** (provas preditivas inéditas), de forma que qualquer fonte (ENEM, EXATO, futuras) possa conter questões dos dois tipos. O usuário filtra por tipo via toggle "Todos · Provas · Simulados" na home, na listagem de questões e na criação de simulados. O corretor expõe o filtro de tipo como seletor paralelo ao de fonte.

---

## Princípio fundamental

`tipo` é propriedade da **questão individual**, não da fonte/banco. ENEM e EXATO (e qualquer fonte futura) podem conter questões de ambos os tipos simultaneamente. Os dois eixos são ortogonais:

```
eixo 1: fonte  → ENEM | EXATO | <futuras>
eixo 2: tipo   → PROVA | SIMULADO
```

---

## 1. Banco de dados

### Migration: `migracao_tipo.sql`

```sql
-- 1. Adiciona coluna
ALTER TABLE questoes
  ADD COLUMN IF NOT EXISTS tipo TEXT NOT NULL DEFAULT 'PROVA';

-- 2. Backfill inicial
UPDATE questoes SET tipo = 'PROVA'    WHERE fonte = 'ENEM';
UPDATE questoes SET tipo = 'SIMULADO' WHERE fonte = 'EXATO';

-- 3. Índice para filtros rápidos
CREATE INDEX IF NOT EXISTS idx_questoes_tipo ON questoes(tipo);
```

### Contrato do campo `tipo`

| Valor | Significado |
|---|---|
| `'PROVA'` | Prova oficial já aplicada (ENEM 2009–2024; futuras provas antigas do EXATO) |
| `'SIMULADO'` | Prova preditiva inédita (EXATO atual; futuros simulados de qualquer fonte) |

- Sem `CHECK` constraint — permite adicionar valores futuros (`'LISTA'`, `'REVISAO'`, etc.) sem nova migration
- Sem enum SQL — mantém flexibilidade
- A coluna é `NOT NULL` com `DEFAULT 'PROVA'` para segurança em inserts sem tipo explícito

### Execução

Migration executada manualmente no Supabase Dashboard (SQL Editor). Não há script automatizado — o arquivo `.sql` serve como documentação e pode ser re-executado (os comandos são idempotentes via `IF NOT EXISTS` e `UPDATE` com `WHERE`).

---

## 2. Frontend — `lib/provas.ts`

Nenhuma mudança. `provas.ts` registra fontes, não tipos. Uma fonte não é "um tipo" — ela contém questões de ambos os tipos. O `tipo` nunca entra na interface `Prova`.

---

## 3. Frontend — Componente `TipoToggle`

**Arquivo:** `frontend/components/TipoToggle.tsx`

Client Component com três pills:

```
[ Todos ]  [ Provas ]  [ Simulados ]
```

- Lê `searchParams.get('tipo')` via `useSearchParams()`
- Escreve `?tipo=PROVA`, `?tipo=SIMULADO` ou remove o parâmetro (Todos) via `useRouter().push()`
- Preserva os demais parâmetros de URL (`fonte`, `ano`, `dia`, etc.)
- Sem estado local — URL é fonte de verdade (compatível com SSR, deep-link e compartilhamento)
- Estilo: pills da paleta Biblioteca Cálida; pill ativo = borda dourada + texto `#F2EDE4`; inativo = `#A89880`

---

## 4. Frontend — Home (`app/page.tsx`)

- Toggle `TipoToggle` aparece acima da seção "Escolha sua prova"
- Filtro aplicado no **servidor** via `searchParams` prop (sem JS extra no client)
- `tipo=PROVA` → mostra só fontes que têm questões com `tipo='PROVA'`
- `tipo=SIMULADO` → mostra só fontes que têm questões com `tipo='SIMULADO'`
- Sem parâmetro → mostra todas as fontes (comportamento atual)
- Cards de fontes sem questões do tipo selecionado ficam ocultos (não desabilitados)

---

## 5. Frontend — Questões (`app/questoes/page.tsx`)

- Toggle `TipoToggle` aparece no topo da sidebar, acima das tabs de fonte
- O parâmetro `tipo` é adicionado ao query do Supabase: `AND tipo = 'PROVA'` (quando selecionado)
- As tabs de fonte (ENEM / EXATO) permanecem visíveis independente do tipo — o filtro de tipo se aplica *dentro* da fonte ativa
- Quando `tipo` é alterado, a listagem recarrega com o filtro combinado `fonte + tipo`

---

## 6. Frontend — Simulado (`app/simulado/page.tsx`)

- Toggle `TipoToggle` aparece no topo do formulário de criação
- Filtra questões disponíveis para o simulado pelo tipo selecionado
- Exemplo: `tipo=PROVA` → simulado só usa questões de provas oficiais; `tipo=SIMULADO` → só preditivas
- Sem parâmetro → mistura ambos os tipos (comportamento atual)

---

## 7. CORRETOR — `data_layer.py`

### `listar_categorias()` — sem mudança de assinatura

Continua retornando `list[str]` com as fontes disponíveis. O tipo não entra aqui — é um filtro paralelo.

### `buscar_questoes()` — novo parâmetro opcional

```python
def buscar_questoes(
    fonte: str,
    filtros: dict,
    tipo: str | None = None,   # 'PROVA' | 'SIMULADO' | None (todos)
) -> list[dict]:
```

Quando `tipo` é passado, adiciona `tipo=eq.{tipo}` ao query REST do Supabase.

### `upsert_questao()` — campo `tipo` incluído no payload

O dict de questão deve incluir `tipo` explicitamente. O default do banco (`'PROVA'`) serve como fallback para inserts legados.

---

## 8. CORRETOR — `ui_questoes.py`

### Filtro `tipo` paralelo ao `fonte`

O cabeçalho dark do painel de questões ganha um combobox `TIPO` independente:

```
QUESTÕES  |  PROVA: [ENEM ▾]  |  TIPO: [Todos ▾]  |  ANO: [2024 ▾]  |  DIA: [dia1 ▾]
```

- `TIPO` tem valores: `Todos`, `Prova`, `Simulado`
- Ao mudar qualquer combobox (fonte, tipo, ano/evento, dia/turno), `_load_questoes()` é chamado com os filtros combinados
- `tipo='Todos'` → não passa filtro de tipo para `buscar_questoes()` (retorna ambos)

### Campo `tipo` no staging

Ao salvar uma questão no staging, o campo `tipo` da questão atual é preservado. Se a questão foi carregada com `tipo='SIMULADO'`, o upsert mantém esse valor.

---

## Arquivos modificados

| Arquivo | Tipo | O que muda |
|---|---|---|
| `migracao_tipo.sql` | Novo | Migration + backfill no Supabase |
| `frontend/components/TipoToggle.tsx` | Novo | Pills Todos / Provas / Simulados |
| `frontend/app/page.tsx` | Modificado | Filtro de cards por `searchParams.tipo` |
| `frontend/app/questoes/page.tsx` | Modificado | Toggle no topo da sidebar; `tipo` no query Supabase |
| `frontend/app/simulado/page.tsx` | Modificado | Toggle filtra questões disponíveis |
| `data_layer.py` | Modificado | `buscar_questoes()` aceita `tipo`; `upsert_questao()` inclui campo |
| `ui_questoes.py` | Modificado | Combobox `TIPO` paralelo no cabeçalho |

---

## Fora do escopo

- Edição do `tipo` de questões já existentes via CORRETOR (por enquanto o tipo vem do banco; edição manual pode ser adicionada depois)
- Filtro de `tipo` no Tira Teima e no Progresso (não afeta o fluxo de estudo principal)
- Constraint `CHECK` no banco (mantido aberto para extensão futura)
