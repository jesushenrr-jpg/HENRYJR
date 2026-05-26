# Design: Extração e Integração de Novas Fontes (UFT, EXATO_PROVAS, ENEM_SIMULADOS)

**Data:** 2026-05-26  
**Status:** Aprovado

---

## Contexto

O banco de dados da plataforma HenryJr possui 3.340 questões (2.880 ENEM + 460 EXATO simulados).
Três novas pastas foram adicionadas em `C:\PROJETOS\HENRYJR\DADOS\`:

1. `UFT_PROVAS` — Provas de vestibular da UFT (2018–2024, MANHÃ/TARDE + GAB por ano; 2021 tem 1ª e 2ª edições)
2. `EXATO_PROVAS` — Provas (não simulados) do EXATO (2024, 2025)
3. `ENEM_SIMULADOS` — Simulados preditivos de Bernoulli, Farias Brito, Poliedro, SAS e Somos (2023–2024)

---

## Banco de Dados

### Nova coluna

```sql
ALTER TABLE questoes ADD COLUMN IF NOT EXISTS provedor TEXT NULL;
CREATE INDEX IF NOT EXISTS idx_questoes_provedor ON questoes(provedor);
```

`provedor` armazena quem elaborou o simulado — usado **exclusivamente** por ENEM_SIMULADOS.
Valores: `'BERNOULLI'`, `'SAS'`, `'POLIEDRO'`, `'FARIAS_BRITO'`, `'SOMOS'`.
Para UFT, EXATO e ENEM real: `NULL`.

### Mapeamento completo por fonte

| fonte | tipo | ano | turno | evento | provedor | dia |
|---|---|---|---|---|---|---|
| `ENEM` | `PROVA` | 2009–2024 | NULL | NULL | NULL | `dia1`/`dia2` |
| `ENEM` | `SIMULADO` | 2023/2024 | NULL | `SIM_00`…`SIM_08` | `BERNOULLI`/`SAS`/etc. | `dia1`/`dia2` |
| `EXATO` | `SIMULADO` | NULL | `MANHA`/`TARDE` | `CICLO_ZERO`/`1_SIMULADO_TESSAT`/etc. | NULL | `exato` |
| `EXATO` | `PROVA` | 2024/2025 | `MANHA`/`TARDE` | NULL | NULL | `exato` |
| `UFT` | `PROVA` | 2018–2024 | `MANHA`/`TARDE` | `1_EDICAO`/`2_EDICAO` (só 2021) ou NULL | NULL | `exato` |

> **UFT 2021**: folder `2021 - 1º EDIÇÃO` → `evento='1_EDICAO'`; `2021 - 2º EDIÇÃO` → `evento='2_EDICAO'`. Todos os outros anos: `evento=NULL`.

> **ENEM simulados**: `evento` identifica o número do simulado dentro de provedor+ano (ex: Bernoulli 2023 Sim 01 → `evento='SIM_01'`). `dia='dia1'` ou `'dia2'` mantém a estrutura do ENEM real.

---

## Extração Python

### Arquivos criados

```
C:\PROJETOS\HENRYJR\
├── lib_extrair.py               # Funções compartilhadas de extração
├── extrair_uft.py               # UFT_PROVAS → JSONs em DADOS/json_uft/
├── extrair_exato_provas.py      # EXATO_PROVAS → JSONs em DADOS/json_exato_provas/
├── extrair_enem_simulados.py    # ENEM_SIMULADOS → JSONs em DADOS/json_enem_simulados/
└── upload_novas_questoes.py     # JSONs → Supabase (todas as 3 fontes)
```

### `lib_extrair.py`

Funções reutilizáveis por todos os extratores:

- `extrair_texto_pdf(path: str) -> list[str]`  
  PyMuPDF: retorna lista de strings, uma por página.

- `renderizar_pagina(pdf_path: str, page_num: int, dpi: int = 200) -> bytes`  
  Renderiza página como PNG em memória (para envio ao Vision).

- `pagina_tem_texto(text: str, min_chars: int = 150) -> bool`  
  Retorna `True` se o texto extraído tem conteúdo suficiente (sem Vision fallback).

- `groq_vision_extract(image_bytes: bytes, prompt: str) -> dict`  
  Chama Groq `meta-llama/llama-4-scout-17b-16e-instruct` com imagem + prompt.  
  Retorna JSON com `questoes: [{numero, enunciado, comando, alternativas, area}]`.

- `parse_gabarito_simples(path: str) -> dict[int, str]`  
  Detecta automaticamente os padrões de gabarito:  
  — Tabela: `01 | A | 02 | B`  
  — Lista: `1. C`, `1) C`  
  — Sequência: `ABCDE...` (com offset por número de questão)  
  Retorna `{numero: letra}`. Questão sem gabarito → não incluída no dict.

- `normalizar_area(texto: str) -> str`  
  Mapeia variações de nome para as 4 áreas padrão do banco.

### Estratégia PyMuPDF + Groq Vision

Para cada página do PDF de questões:
1. Extrai texto com PyMuPDF.
2. Se `not pagina_tem_texto(texto)` → renderiza como PNG e envia ao Groq Vision.
3. Groq retorna JSON com as questões da página.
4. Script consolida com gabarito lido do PDF separado.
5. Questões sem gabarito ficam com `gabarito=null` (log de aviso para revisão).

O prompt do Groq Vision deve solicitar JSON estruturado diretamente, com fallback para tentar extrair o máximo possível mesmo em páginas parcialmente legíveis.

### `extrair_uft.py`

- Faz scan de `DADOS/UFT_PROVAS/` buscando sub-pastas por ano.
- Detecta `1º EDIÇÃO` / `2º EDIÇÃO` no nome da pasta → define `evento`.
- Detecta `MANHÃ.pdf`, `TARDE.pdf` → define `turno`.
- Detecta `GAB.pdf` → parse de gabarito.
- Saída: `DADOS/json_uft/{ano}_{turno}[_{edicao}].json`

### `extrair_exato_provas.py`

- Scan de `DADOS/EXATO_PROVAS/` por sub-pastas de ano.
- Mesmo padrão de arquivo que UFT (MANHÃ/TARDE/GAB ou GAB PROVISÓRIO).
- `evento=NULL` (sem identificador de evento, diferente dos simulados EXATO).
- Saída: `DADOS/json_exato_provas/{ano}_{turno}.json`

### `extrair_enem_simulados.py`

- Scan de `DADOS/ENEM_SIMULADOS/{provedor}/{ano}/`.
- Normaliza nome de pasta para enum de provedor (`BERNOULLI`, `SAS`, etc.).
- Detecta pares `prova d1`/`prova d2` + `gabarito d1`/`gabarito d2` (ou `resolução`).
- Identifica número do simulado pelo nome do arquivo (`Sim 01`, `FB 01`, `Ciclo 01`, etc.) → `evento='SIM_01'`.
- Saída: `DADOS/json_enem_simulados/{provedor}_{ano}_sim{nn}_{dia}.json`

### `upload_novas_questoes.py`

- Lê todos os JSONs das pastas `json_uft/`, `json_exato_provas/`, `json_enem_simulados/`.
- Verifica duplicatas: busca por `(fonte, ano, numero, turno, evento)` antes de inserir.
- Classifica competências H01–H30 via Groq para questões com área ENEM (usando lógica do `classificar_competencias.py` existente).
- Insert em batch de 50 questões.
- Exibe relatório final: total inserido / já existentes / erros.

---

## Frontend

### Mudança na navegação

As abas **[ENEM] [EXATO]** são **removidas** do `FiltroSidebar`.

O `TipoToggle` ([Todos] [Provas] [Simulados]) permanece no topo do sidebar como organizador principal.

Uma nova seção **"Fonte"** é adicionada ao sidebar com chips:
```
[Todas]  [ENEM]  [EXATO]  [UFT]
```

Quando `tipo=SIMULADO` está ativo, aparece também **"Provedor"**:
```
[Todos]  [Bernoulli]  [SAS]  [Poliedro]  [Farias Brito]  [Somos]
```

### Filtros condicionais por fonte

| fonte | Filtros exibidos |
|---|---|
| ENEM + PROVA | Área · Ano (2009–2024) · Dia · Competência H01–H30 |
| ENEM + SIMULADO | Área · Ano · Provedor · Evento (Sim 00…) · Dia |
| EXATO + PROVA | Área · Ano (2024/2025) · Turno |
| EXATO + SIMULADO | Área · Evento (Ciclo Zero…) · Turno |
| UFT | Área · Ano (2018–2024) · Turno · Edição (só 2021) |
| Todas as fontes | Só Área (mínimo denominador comum) |

### Arquivos frontend modificados

- **`frontend/components/FiltroSidebar.tsx`**  
  Remove tabs ENEM/EXATO. Adiciona seção Fonte (chips) e seção Provedor (chips condicionais).  
  Lógica de filtros condicionais passa a depender de `fonteAtiva` + `tipoAtivo`.

- **`frontend/app/questoes/page.tsx`**  
  Adiciona `provedor?: string` e `fonte?: string` em `SearchParams`.  
  Aplica `.eq('provedor', provedor)` quando presente.  
  Remove lógica `isExato` hard-coded; usa `fonteAtiva` diretamente.

- **`frontend/app/simulado/page.tsx`**  
  Adiciona filtro por `fonte` (ENEM/EXATO/UFT) e `provedor` na tela de criação de simulado.  
  Expande `PROVAS` para incluir fonte UFT.

### URL parameters

Os parâmetros de URL são ampliados:

```
/questoes?tipo=SIMULADO&fonte=ENEM&provedor=BERNOULLI&ano=2023&evento=SIM_01&dia=dia1
/questoes?tipo=PROVA&fonte=UFT&ano=2022&turno=MANHA
```

---

## CORRETOR (ui_questoes.py / data_layer.py)

### `data_layer.py`

```python
def buscar_questoes(
    fonte: str,
    filtros: dict,
    tipo: str | None = None,
    provedor: str | None = None
) -> list[dict]:
    ...
    if provedor:
        params["provedor"] = f"eq.{provedor}"
```

### `ui_questoes.py`

- Dropdown **Fonte**: `['Todas', 'ENEM', 'EXATO', 'UFT']`
- Dropdown **Provedor**: visível apenas quando `fonte='ENEM'` e `tipo='SIMULADO'`  
  Valores: `['Todos', 'BERNOULLI', 'SAS', 'POLIEDRO', 'FARIAS_BRITO', 'SOMOS']`
- Campo **Evento**: já existente — reutilizado para ENEM simulados (mostra `SIM_00`…)

A lógica de correção em si não muda: `gabarito` existe para todas as questões independente da fonte.

---

## Escopo fora deste design

- OCR das 356 questões EXATO simulados sem enunciado — problema preexistente, não tratado aqui
- Frases motivacionais da capa PDF — não relacionado
- Fase 5.5 (correção por foto) — não relacionado
