# HenryJr — Banco de Questões ENEM + EXATO + UFT

## Visão Geral do Projeto

Plataforma pública de estudos com questões do ENEM (2009–2024), simulados preditivos ENEM (Bernoulli, SAS, Poliedro, Farias Brito, Somos), provas do vestibular UFT (2018–2024) e simulados/provas do EXATO (TESSAT), com simulados personalizados, progresso por competência, explicações com IA, caderno de erros ("Tira Teima") e correção automática de simulados por foto. Stack 100% gratuita. URL em produção: **https://henryjr.vercel.app**

## Stack Tecnológica

| Camada | Tecnologia | Status |
|---|---|---|
| Frontend | Next.js 14 + React + Tailwind CSS | ✅ Em produção (Vercel) |
| Banco de dados | Supabase (PostgreSQL + Auth + Storage) | ✅ Ativo |
| Hospedagem frontend | Vercel | ✅ Em produção |
| Hospedagem microserviço | Railway ou Render (gratuito) | ⏳ Fase 5.5 (pendente) |
| IA para explicações | Groq API (LLaMA 3, gratuito) | ✅ Ativo |
| Geração de PDF | Puppeteer + @sparticuz/chromium | ✅ Implementado (pausado) |
| Correção por foto | FastAPI + OpenCV (microserviço Python) | ⏳ Fase 5.5 (pendente) |
| Extração de dados | Python + PyMuPDF + parser de texto + Groq/Gemini Vision | ✅ Concluído para ENEM, EXATO, UFT, ENEM_SIMULADOS |

## Credenciais e Chaves (NUNCA commitar no GitHub)

- Todas as chaves estão em `C:\PROJETOS\HENRYJR\HENRYJR_CREDENCIAIS.txt`
- **Supabase URL**: `https://bmhudlpihwxvaelokugh.supabase.co`
- **Supabase Anon Key**: ver `HENRYJR_CREDENCIAIS.txt`
- **Supabase Service Role Key**: ver `HENRYJR_CREDENCIAIS.txt`
- **Groq API Key**: ver `HENRYJR_CREDENCIAIS.txt` (chave atual criada em 26/05/2026)
- **Gemini API Key**: obter em https://aistudio.google.com/apikey — adicionar em `HENRYJR_CREDENCIAIS.txt` quando disponível
- **Google OAuth Client ID/Secret**: ver `HENRYJR_CREDENCIAIS.txt`

> ⚠️ Duas chaves Groq já foram revogadas (22/05/2026 e 26/05/2026). A segunda foi exposta no arquivo de plano do git. Sempre criar chave nova após exposição.
> ⚠️ Nunca rodar múltiplas instâncias simultâneas dos extratores no mesmo diretório — race condition sobrescreve arquivos bons (ocorreu em 26/05/2026 com bt30o2rbz vs brbcf6s0z).

## Estrutura de Pastas

```
C:\Projetos\henryjr\
├── dados\
│   ├── provas\              # PDFs originais ENEM organizados por ano
│   │   ├── 2009\           # dia1.pdf, dia2.pdf, gabarito_dia1.pdf, gabarito_dia2.pdf
│   │   └── ...até 2024\
│   ├── json\               # JSONs extraídos v1 (com gabaritos validados)
│   ├── json_v2\            # JSONs extraídos v2 — 2880 questões ENEM completas
│   ├── json_uft\           # JSONs extraídos UFT — uft_{ano}_{turno}[_{edicao}].json
│   ├── json_exato_provas\  # JSONs extraídos EXATO provas — exato_prova_{ano}_{turno}[_{edicao}].json
│   ├── json_enem_simulados\ # JSONs simulados ENEM — {provedor}_{ano}_{evento}_{dia}.json
│   ├── UFT_PROVAS\         # PDFs do vestibular UFT (2018–2024, MANHÃ/TARDE/GAB por ano)
│   ├── EXATO_PROVAS\       # PDFs das provas EXATO (2024, 2025 1ª e 2ª edição)
│   ├── ENEM_SIMULADOS\     # PDFs simulados preditivos ENEM por provedor+ano
│   ├── EXATO_SIMULADOS\    # PDFs dos simulados EXATO/TESSAT (antigo EXATO)
│   ├── imagens\            # Imagens das questões por ano/dia (751 questões com imagem)
│   ├── texto_bruto\        # Texto bruto extraído (intermediário)
│   ├── EXATO_ORGANIZADO\   # PDFs e JSONs do EXATO organizados
│   │   ├── simulados\      # 12 PDFs de simulado por evento
│   │   ├── gabaritos\      # 10 PDFs de gabarito por evento
│   │   ├── material_apoio\ # 8 PDFs (trilhas, listas, cartilha)
│   │   ├── Duplicados\     # 35 cópias preservadas
│   │   ├── Nao_Identificados\ # 1 PDF-imagem sem OCR
│   │   ├── json_exato\     # 12 JSONs — 460 questões EXATO
│   │   ├── relatorio_exato.json
│   │   └── metadata_integracao.json
│   └── frases_capa.txt     # Frases motivacionais das capas (pendente)
├── organizar.py                # Renomeia PDFs para o padrão correto
├── extrair.py                  # Extração v1 (texto + gabaritos dos PDFs)
├── extrair_v2.py               # Extração v2 (melhorada)
├── diagnostico.py              # Verifica integridade dos JSONs
├── aplicar_gabarito_2010.py    # Aplica gabaritos manuais do 2010
├── corrigir_imagens_v2.py      # Recorte de imagens por região de questão
├── ferramenta_recorte.py       # Ferramenta visual de recorte (Tkinter)
├── gerenciar_imagens.py        # Gerenciador visual de questões/imagens (Tkinter) — aceita --revisao
├── extrair_paginas_pdf.py      # Extrai campo pagina_pdf para todos os JSONs
├── classificar_competencias.py # Auto-classifica H01–H30 via Groq
├── upload_provas_supabase.py   # Upload dos PDFs para Supabase Storage
├── upload_questoes_exato.py    # Upload das 460 questões EXATO para Supabase
├── corrigir_posicao_imagens.py # Adiciona campo posicao nas imagens (concluído)
├── reextrair_imagens_2010_2021.py # Re-extrai imagens faltando (concluído)
├── ocr_2021.py                 # OCR Tesseract para questões 2021 corrompidas
├── sync_ocr_2021.py            # Sincroniza questões OCR com Supabase
├── marcar_anuladas.py          # Marca questões anuladas no JSON e Supabase
├── recuperar_alternativas.py   # Tenta recuperar alternativas de questões com imagem
├── sincronizar_paginas_supabase.py # Sincroniza pagina_pdf com Supabase
├── lib_extrair.py              # Biblioteca compartilhada: PyMuPDF + Groq Vision fallback
├── extrair_uft.py              # Extrai vestibulares UFT → DADOS/json_uft/
├── extrair_exato_provas.py     # Extrai provas EXATO → DADOS/json_exato_provas/
├── extrair_enem_simulados.py   # Extrai simulados ENEM → DADOS/json_enem_simulados/
├── upload_novas_questoes.py    # Upload UFT/EXATO_P/ENEM_SIM para Supabase
├── migracao_provedor.sql       # SQL: ADD COLUMN provedor TEXT NULL + índice ✅ Executada
├── migracao_exato.sql          # SQL: adiciona colunas fonte/evento/turno na tabela questoes
├── relatorio_erros.json        # Questões reportadas (local)
├── HENRYJR_CREDENCIAIS.txt     # Chaves de API (NÃO commitar)
└── CLAUDE.md                   # Este arquivo

frontend/
├── app/
│   ├── page.tsx                # Home: cards ENEM e EXATO lado a lado
│   ├── questoes/page.tsx       # Listagem com chips ENEM/EXATO/UFT + filtros por fonte
│   ├── questoes/[id]/page.tsx  # Card de questão individual
│   ├── simulado/page.tsx       # Criação de simulado (ENEM, EXATO ou UFT)
│   ├── simulado/[id]/
│   │   ├── page.tsx            # SimuladoPlayer com cronômetro
│   │   └── resultado/
│   │       ├── page.tsx        # Tela de resultado com ExplicarBtn por questão errada
│   │       └── ExplicarBtn.tsx # Botão streaming de explicação IA
│   ├── tira-teima/
│   │   ├── page.tsx            # Caderno de erros com badges de versão V1/V2/V3
│   │   ├── TiraTeimaVersao.tsx # Placeholder (lógica está em page.tsx)
│   │   └── imprimir/
│   │       ├── page.tsx        # Server Component — busca dados para PDF
│   │       └── TiraTeimaPrint.tsx # Client — layout print completo
│   ├── progresso/page.tsx      # Painel de progresso por área
│   ├── auth/login/page.tsx     # Login email + Google OAuth
│   ├── api/
│   │   ├── explicar/route.ts   # POST → streaming Groq LLaMA 3.3 70B
│   │   ├── busca-ia/route.ts   # POST → extração de termos com LLaMA 3.1 8B
│   │   ├── reportar-erro/route.ts
│   │   ├── pdf/simulado/[id]/route.ts  # GET → PDF via Puppeteer
│   │   ├── pdf/tira-teima/route.ts     # GET → PDF via Puppeteer
│   │   └── tira-teima/nova-versao/route.ts  # POST → ciclo de versões
│   └── ...
├── components/
│   ├── CardQuestao.tsx         # Card completo: tesoura, revelar, explicar, ver PDF, reportar
│   ├── FiltroSidebar.tsx       # Sidebar com chips ENEM/EXATO/UFT + filtros condicionais por fonte+tipo
│   ├── BuscaIA.tsx             # Busca semântica com extração de termos
│   ├── SimuladoPlayer.tsx      # Player do simulado online com cronômetro
│   └── ModalReportarErro.tsx
├── lib/
│   ├── provas.ts               # Registro central de provas (ENEM, EXATO, UFT) + DIA_LABEL + PROVEDOR_LABEL
│   └── supabase/
├── supabase/migrations/
│   ├── 001_questoes_erradas.sql
│   └── 002_tira_teima_versoes.sql  # ✅ Executada
└── ...
```

---

## Banco de Dados — Estado Atual do Supabase

### Totais
- **2.880 questões ENEM reais** (2009–2024, `fonte='ENEM'`, `tipo='PROVA'`, `dia='dia1'|'dia2'`)
- **460 questões EXATO simulados** (`fonte='EXATO'`, `tipo='SIMULADO'`, `dia='exato'`, `ano=NULL`)
- **UFT** — 182 questões extraídas (`fonte='UFT'`, `tipo='PROVA'`, `dia='exato'`, 2018–2024) — upload pendente
- **EXATO provas** — em extração (`fonte='EXATO'`, `tipo='PROVA'`, `dia='exato'`, 2024–2025)
- **ENEM simulados** — em extração (`fonte='ENEM'`, `tipo='SIMULADO'`, `dia='simu_dia1'|'simu_dia2'`)

### Tabela `questoes` — colunas relevantes

| Coluna | Tipo | ENEM real | ENEM simulado | EXATO | UFT |
|---|---|---|---|---|---|
| `id` | int | auto | auto | auto | auto |
| `fonte` | text | 'ENEM' | 'ENEM' | 'EXATO' | 'UFT' |
| `tipo` | text | 'PROVA' | 'SIMULADO' | 'PROVA'\|'SIMULADO' | 'PROVA' |
| `ano` | int\|null | 2009–2024 | 2023–2024 | **NULL** | 2018–2024 |
| `dia` | text | 'dia1'\|'dia2' | 'simu_dia1'\|'simu_dia2' | 'exato' | 'exato' |
| `numero` | int | Q1–Q45 por prova | Q1–Qn por prova | Q1–Q460 global | Q1–Qn por prova |
| `area` | text | 4 áreas | 4 áreas | 4 áreas | 4 áreas |
| `evento` | text\|null | null | 'SIM_00'…'SIM_08' | 'CICLO_ZERO' etc. | '1_EDICAO'\|null |
| `turno` | text\|null | null | null | 'MANHA'\|'TARDE' | 'MANHA'\|'TARDE' |
| `provedor` | text\|null | null | 'BERNOULLI' etc. | null | null |
| `competencia` | text\|null | H01–H30 ✅ | H01–H30 (pós-classif.) | NULL | NULL |
| `pagina_pdf` | int | preenchido ✅ | preenchido | preenchido | preenchido |
| `enunciado` | jsonb | preenchido ✅ | via parser texto (~94%) + Vision | 104/460 (PDFs imagem) | via Vision |

> **UNIQUE constraint**: `(ano, dia, numero, fonte)` — usar `dia='simu_dia1'/'simu_dia2'` para ENEM simulados evita colisão com questões reais do mesmo ano.

### Migrations executadas
- `001_questoes_erradas.sql` — tabela `questoes_erradas` com campos `acertou`, `respondido_em`
- `002_tira_teima_versoes.sql` ✅ — adiciona `versao_tt` e `zerada` em `questoes_erradas`; cria tabela `tira_teima`
- `migracao_exato.sql` ✅ — adiciona colunas `fonte`, `evento`, `turno` em `questoes`
- `migracao_provedor.sql` ✅ — adiciona coluna `provedor TEXT NULL` + índice

### Supabase Storage
- Bucket `provas-pdf`: ✅ 64 PDFs ENEM (2009–2024, 4 por ano)
- Bucket `imagens-questoes`: ✅ todas as 751 questões ENEM com imagem

---

## Questões EXATO — Detalhes

### Estrutura dos simulados EXATO

| Evento | Turno | Questões | Gabarito | Notas |
|---|---|---|---|---|
| CICLO_ZERO | MANHA | Q001–Q040 | 40/40 ✅ | — |
| CICLO_ZERO | TARDE | Q041–Q080 | 38/40 ⚠️ | Q38/Q39 sem gabarito no PDF |
| 1_SIMULADO_TESSAT | MANHA | Q081–Q120 | 39/40 | Q21 anulada |
| 1_SIMULADO_TESSAT | TARDE | Q121–Q160 | 40/40 ✅ | — |
| 2_SIMULADO_TESSAT | MANHA | Q161–Q200 | 40/40 ✅ | — |
| 2_SIMULADO_TESSAT | TARDE | Q201–Q240 | 40/40 ✅ | — |
| OUTUBRO_2025 | MANHA | Q241–Q280 | 40/40 ✅ | Gabarito revisado (Q2→A) |
| OUTUBRO_2025 | TARDE | Q281–Q320 | 38/40 | Q15+Q39 anuladas |
| ABRIL_2026 | MANHA | Q321–Q360 | 40/40 ✅ | — |
| ABRIL_2026 | TARDE | Q361–Q400 | 39/40 ⚠️ | Q15 sem gabarito no PDF |
| NATUREZAS_TESSAT | TARDE | Q401–Q420 | 20/20 ✅ | Apenas 20 questões |
| TRADICIONAIS | MANHA | Q421–Q460 | 0/40 ❌ | Sem PDF de gabarito (enviado digitalmente) |

**Total: 460 questões · 414 com gabarito (90%) · 456 com 5 alternativas (99,1%) · 3 anuladas**

### Por que 356/460 não têm enunciado?
Os PDFs do EXATO são majoritariamente digitalizados (PDF-imagem). O PyMuPDF não extrai texto de imagens — apenas 104 questões tinham texto extraível diretamente. As 356 restantes precisariam de OCR, mas os PDFs escaneados têm baixa qualidade que dificulta o Tesseract. **Não é um erro — é uma limitação conhecida.**

### Filtros no frontend para EXATO
O frontend usa `fonte='EXATO'` como ponto de entrada. Filtros disponíveis:
- `evento`: CICLO_ZERO / 1_SIMULADO_TESSAT / 2_SIMULADO_TESSAT / OUTUBRO_2025 / ABRIL_2026 / NATUREZAS_TESSAT / TRADICIONAIS
- `turno`: MANHA / TARDE
- `area`: 4 áreas (mesmo sistema do ENEM)

**Nunca filtrar por `ano` para o EXATO** — campo é `NULL` intencionalmente.

---

## Frontend — Identidade Visual "Biblioteca Cálida"

### Paleta de cores
| Token | Valor | Uso |
|---|---|---|
| Fundo | `#0E0D0B` | background geral |
| Surface | `#161411` | cards, modais |
| Surface elevada | `#1E1B17` | hover, inputs |
| Borda | `#2C2820` | divisores, bordas de card |
| Texto | `#F2EDE4` | texto principal |
| Dourado (primário) | `#D4A853` | botões, ícones, destaques |
| Dourado hover | `#B8882A` | hover dos botões |

### Tipografia
- **Playfair Display** — títulos e headings
- **Source Serif 4** — enunciados das questões (leitura longa)
- **DM Sans** — UI geral (labels, botões, chips)

### Separação por prova
- `lib/provas.ts` — registro central; adicionar nova prova = inserir um objeto no array `PROVAS`
- `FiltroSidebar.tsx` — chips de fonte `[ENEM][EXATO][UFT]` substituíram as tabs; filtros condicionais por fonte+tipo:
  - ENEM + PROVA: Área / Ano / Dia / Competência H01–H30
  - ENEM + SIMULADO: Área / Elaborador / Ano / Dia
  - EXATO: Evento / Turno / Área
  - UFT: Área / Ano / Turno / Edição
- `questoes/page.tsx`: suporta `?fonte=ENEM|EXATO|UFT` + `?provedor=BERNOULLI|...`
- `simulado/page.tsx`: ENEM, EXATO e UFT disponíveis; Tipo apenas para ENEM; anos ocultos para EXATO
- **Nunca filtrar por `ano` para EXATO** — campo é `NULL` intencionalmente

---

## Estrutura do JSON de Questões ENEM (v2)

```json
{
  "numero": 12,
  "ano": 2023,
  "dia": "dia1",
  "area": "Linguagens, Codigos e suas Tecnologias",
  "competencia": "H15",
  "enunciado": [
    "Paragrafo 1 do enunciado completo.",
    "Paragrafo 2 — pode ser TEXTO I, TEXTO II, citacoes, etc."
  ],
  "comando": "Considerando os elementos da tirinha, conclui-se que o texto tem a finalidade de",
  "alternativas": {
    "A": "texto da alternativa A",
    "B": "texto da alternativa B",
    "C": "texto da alternativa C",
    "D": "texto da alternativa D",
    "E": "texto da alternativa E"
  },
  "gabarito": "B",
  "confianca": 0.95,
  "revisado": false,
  "anulada": false,
  "imagens": [{"path": "2023/dia1/q012_1.jpg", "posicao": "antes_1"}],
  "tem_imagem": true,
  "pagina_pdf": 12
}
```

### Campos do JSON ENEM

| Campo | Tipo | Descrição |
|---|---|---|
| `numero` | int | Número da questão no caderno |
| `ano` | int | Ano do ENEM |
| `dia` | string | "dia1" ou "dia2" |
| `area` | string | Área de conhecimento |
| `competencia` | string | Competência H01–H30 (ex.: "H15") — 100% preenchidas |
| `enunciado` | list[str] | Parágrafos do enunciado |
| `comando` | string | Frase final antes das alternativas |
| `alternativas` | dict | Chaves A–E com texto |
| `gabarito` | string\|null | Letra correta; null = anulada |
| `confianca` | float | Confiança da extração (0–1) |
| `revisado` | bool | Revisado manualmente pelo gerenciador |
| `anulada` | bool | Questão oficialmente anulada |
| `imagens` | list[dict] | path + posicao no layout |
| `tem_imagem` | bool | Atalho para filtrar questões com imagem |
| `pagina_pdf` | int | Página do PDF original (base 0) |

## Estrutura do relatorio_erros.json

```json
[
  {
    "ano": 2023,
    "dia": "dia1",
    "numero": 45,
    "tipo_erro": "alternativa incorreta",
    "descricao": "Alternativa B apresenta texto cortado",
    "reportado_em": "2024-01-15T10:30:00",
    "status": "pendente"
  }
]
```

## Padrões de Texto nos PDFs por Ano

| Anos | Padrão do marcador de questão | Padrão das alternativas |
|---|---|---|
| 2009 | `'Questão'` isolado + número no span seguinte | Spans separados com tab |
| 2010 | `'Questão'` isolado (fonte corrompida) | Gabarito inserido manualmente via Word |
| 2011–2024 | `'QUESTÃO 01'` tudo no mesmo span, negrito | Letra `'A\t'` em span negrito separado + texto no span seguinte em x≈54 |
| 2019–2021 | `'Questão 01'` tamanho 11, negrito | Mesmo padrão acima |

## Anos com Problemas Especiais

| Ano | Problema | Solução aplicada |
|---|---|---|
| 2009 | Imagens em formato .jpx (fundo preto) | Renderização direta das páginas do PDF |
| 2010 | Gabarito em formato visual (respostas circuladas em verde) | Preenchimento manual via Word + `aplicar_gabarito_2010.py` |
| 2010 | Texto com encoding corrompido (fonte customizada) | OCR Tesseract — pendente |
| 2015 | PDFs dia1 e gabarito_dia1 estavam com nomes trocados | Renomeados manualmente |
| 2021 | Texto completamente corrompido (caracteres de controle) | OCR aplicado nas 21 piores — alts ainda pendentes |
| 2024 | Caracteres estranhos extraídos | Verificado: eram nomes próprios em CAPS, sem lixo real |

## Questões Anuladas (sem gabarito)

- 2018: Q150
- 2020: Q114, Q141
- 2021: Q178
- 2022: Q175
- 2023: Q177
- 2024: Q129

Marcadas com `anulada: true, gabarito: null` em todos os JSONs v2 e no Supabase. ✅

## Proteção do 2010

**IMPORTANTE**: O JSON do 2010 tem gabaritos inseridos manualmente. O script `extrair.py` tem proteção para não sobrescrever este arquivo. Caso o JSON do 2010 seja sobrescrito acidentalmente, rodar `aplicar_gabarito_2010.py` restaura os gabaritos a partir do Word preenchido.

---

## Estado Atual do Projeto

### Concluído ✅

**Dados e banco**
- Extração v1: 2.865 questões (2009–2024) com gabaritos
- Extração v2: 2.880 questões ENEM completas nos JSONs `dados/json_v2/`
- Gabarito 2010: 185/185 questões (preenchimento manual)
- Competências H01–H30: 2.880/2.880 questões ENEM classificadas (local + Supabase)
- Questões anuladas marcadas (7 questões)
- `pagina_pdf` preenchido: 2.880/2.880 questões (local + Supabase via `sincronizar_paginas_supabase.py`)
- Imagens: 751/751 questões com imagem têm `posicao: "antes_1"` + arquivo em disco + Supabase Storage
- OCR 2021: 21 questões com enunciado ilegível recuperadas pelo Tesseract PT
- Alternativas recuperadas: 8/22 questões com alternativas em imagem
- PDFs no Storage: 64/64 PDFs ENEM no bucket `provas-pdf`
- EXATO: 460/460 questões extraídas e uploadadas com `fonte`, `evento`, `turno`, numeração contínua Q001–Q460

**Frontend**
- Redesign completo "Biblioteca Cálida" (paleta quente, tipografia editorial)
- `FiltroSidebar.tsx`: chips de fonte ENEM/EXATO/UFT (substituiu tabs); filtros condicionais por fonte+tipo; combo Elaborador para ENEM simulados
- Card de questão: tesoura, revelar gabarito, Explicar com IA (streaming + Markdown), Ver PDF, Reportar Erro
- Busca semântica com IA (extração de termos + inferência de área/competência)
- Simulado online com cronômetro regressivo e auto-submit; ENEM/EXATO/UFT disponíveis
- Tela de resultado com `ExplicarBtn.tsx` — explicação streaming por questão errada
- Tira Teima: página com badges V1/V2/V3 e botão de download PDF
- `/tira-teima/imprimir` — página de impressão completa (`page.tsx` + `TiraTeimaPrint.tsx`)
- Painel de progresso por área
- Login via email ✅ e Google OAuth ✅

**Infraestrutura**
- Supabase Auth: email + Google OAuth configurados ✅
- Migrations executadas: `001_questoes_erradas.sql` + `002_tira_teima_versoes.sql` + `migracao_exato.sql` + `migracao_provedor.sql` ✅
- API Tira Teima: `POST /api/tira-teima/nova-versao` — ciclo V1→V2→V3 implementado
- PDF Puppeteer: infraestrutura funcional no Vercel (pausado para refinamento)
- Deploy automático no Vercel via GitHub ✅

**Ferramentas locais**
- `gerenciar_imagens.py --revisao`: modo de revisão de erros pendentes do `relatorio_erros.json`
- `lib_extrair.py`: biblioteca de extração — parser de texto (zero API) + Groq Vision + Gemini Vision fallback
- `extrair_uft.py` / `extrair_exato_provas.py` / `extrair_enem_simulados.py`: extratores por fonte
- `upload_novas_questoes.py`: upload em lotes para Supabase com retry por questão

**Frontend (novas fontes — 27/05/2026)**
- `FiltroSidebar.tsx`: chips `[ENEM][EXATO][UFT]` substituíram as tabs; filtros condicionais por fonte+tipo
- `lib/provas.ts`: adicionado UFT com `anos=[2018..2024]`; novos exports `DIA_LABEL`, `PROVEDOR_LABEL`, `EVENTO_LABEL` expandido
- `questoes/page.tsx`: suporte a `?fonte=UFT` e `?provedor=...`
- `simulado/page.tsx` + `api/simulado/criar/route.ts`: UFT disponível; TIPO só para ENEM; anos ocultos para EXATO

**lib_extrair.py — arquitetura de extração (27/05/2026)**
- `_parse_questoes_texto()`: parser sem API para PDFs digitais — detecta marcadores `Questão NN`, alternativas A-E com algoritmo de "última sequência válida"; ~94% das páginas de ENEM simulados sem Vision
- `_chamar_gemini_json()`: cliente Gemini Vision — converte formato OpenAI→Gemini; free tier: 1500 RPD, 15 RPM
- `_chamar_vision()`: orquestra Groq→Gemini automaticamente
- Raiz do problema anterior: `urllib.request` não enviava `User-Agent` → Cloudflare retornava HTTP 403; fix: usar `requests`

### Pendente de revisão manual ⚠️

Alternativas extraídas como imagem (não texto — não extraíveis automaticamente):
- 2009 Q93, 2010 Q108, 2020 Q137 → 0 alternativas
- 2016 Q85 → apenas 3/5 alternativas
- 2021: Q2, Q11, Q16, Q43, Q54, Q69, Q107, Q127, Q151, Q169, Q170 → sem alternativas (OCR falhou no layout 2 colunas)

EXATO com enunciado vazio (questões em imagem):
- 356/460 questões sem enunciado — limitação dos PDFs digitalizados

### Próximos passos sugeridos

1. **Obter Gemini API Key** — https://aistudio.google.com/apikey — adicionar em `HENRYJR_CREDENCIAIS.txt` e definir `GEMINI_API_KEY=...` para extratores com PDFs escaneados (UFT re-extração, EXATO provas)
2. **Finalizar extração ENEM simulados** — aguardar `extrair_enem_simulados.py` terminar; conferir total de questões
3. **Rodar `extrair_exato_provas.py`** — PDFs escaneados, precisará de Gemini Vision
4. **Re-rodar `extrair_uft.py`** com Gemini — PDFs escaneados de 2021-2024 ficaram com 0 questões por rate limit; Gemini resolve
5. **Upload** — rodar `upload_novas_questoes.py` após todos os 3 extratores concluídos
6. **Classificar competências ENEM simulados** — rodar `classificar_competencias.py --fonte ENEM --tipo SIMULADO` após upload
7. **Verificar qualidade** — spot-check nos JSONs; questões com enunciado vazio são limitação dos PDFs escaneados
8. **Fase 5 (PDF)** — retomar e verificar layout; habilitar botões na UI
9. **Progresso por competência H01–H30** — adicionar breakdown por competência na página de progresso
10. **Frases motivacionais das capas** — `frases_capa.txt` ainda não fornecido; `FRASES[]` em ImprimirClient.tsx usa placeholders
11. **Fase 5.5 (correção por foto)** — FastAPI + OpenCV; depende dos marcadores de registro na folha de respostas

---

## Fase 5 — PDF: Progresso Técnico (PAUSADO 🔄)

> **Status**: Infraestrutura 100% funcional no Vercel. Layout em refinamento.
> Botões de download/impressão estão desabilitados na UI ("disponível em breve").
> Retomar quando o restante da plataforma estiver mais maduro.

### Stack adotada

| Componente | Solução |
|---|---|
| Geração de PDF | `puppeteer-core` + `@sparticuz/chromium` — Chromium embutido na Vercel Lambda |
| Sem microserviço externo | A função serverless do Vercel roda o Chromium diretamente |
| Timeout | `export const maxDuration = 60` (máximo do plano Hobby) |
| Margem | Apenas CSS `@page { margin: 14mm 10mm 12mm 10mm }` — **não** passar `margin` no `page.pdf()` |

### Arquivos criados/modificados

```
frontend/
├── app/
│   ├── api/pdf/
│   │   ├── simulado/[id]/route.ts    ← GET → navega /simulado/{id}/imprimir?view=1 e gera PDF
│   │   └── tira-teima/route.ts       ← GET → navega /tira-teima/imprimir?view=1 e gera PDF
│   ├── simulado/[id]/imprimir/
│   │   ├── page.tsx                  ← Server component que busca dados do Supabase
│   │   └── ImprimirClient.tsx        ← Layout completo do caderno (capa + questões + folha de respostas)
│   └── tira-teima/imprimir/
│       ├── page.tsx                  ← Server Component — busca questões erradas do usuário
│       └── TiraTeimaPrint.tsx        ← Client — layout de impressão completo
└── next.config.ts                    ← serverExternalPackages + outputFileTracingIncludes
```

### Configurações críticas no next.config.ts

```typescript
serverExternalPackages: ['puppeteer-core', '@sparticuz/chromium'],
outputFileTracingIncludes: {
  '/api/pdf/simulado/[id]': ['./node_modules/@sparticuz/chromium/**/*'],
  '/api/pdf/tira-teima':    ['./node_modules/@sparticuz/chromium/**/*'],
},
```

### Padrão da rota de geração

```typescript
browser = await puppeteer.launch({ executablePath, args: chromium.args, headless: true })
const page = await browser.newPage()
await page.setCookie(...cookies) // injeta sessão Supabase Auth
await page.goto(url, { waitUntil: 'networkidle0', timeout: 40_000 })
await page.waitForSelector('.area-bloco, .sem-questoes', { timeout: 12_000 })
await page.emulateMediaType('print')
const pdf = await page.pdf({ format: 'A4', printBackground: true, displayHeaderFooter: false })
// NÃO passar margin: {...} — conflita com @page CSS e desloca coordenadas do position:fixed
```

### Bugs já corrigidos

| # | Problema | Causa | Fix |
|---|---|---|---|
| 1 | Binário Chromium não encontrado (500) | Vercel file-tracing exclui não-JS | `outputFileTracingIncludes` no next.config.ts |
| 2 | Build error: `Uint8Array` não é `BodyInit` | puppeteer-core 25 retorna Uint8Array | `Buffer.from(pdf)` antes de passar ao NextResponse |
| 3 | Build warning: `@react-pdf/renderer can't be external` | Tentativa anterior com react-pdf | Reescrita completa para Puppeteer |
| 4 | `turbopack.root` conflitando com `outputFileTracingRoot` | Vercel injeta /vercel/path0 | Remover `turbopack: { root: __dirname }` do next.config |
| 5 | pg-head cobrindo conteúdo (Linguagens desaparece) | Margem dupla: page.pdf + @page CSS | Remover `margin` do `page.pdf()` |
| 6 | Cabeçalho de área órfão no fim da página | `.questoes-wrap` sem `break-before: avoid` | Adicionado em @media print |
| 7 | Cores das áreas suprimidas no PDF | `body { color: #111 !important }` vencia inline styles | Remover `!important` do body color |

### O que ainda falta para o PDF ficar completo

- [ ] **Verificar o layout** após os fixes de margem — testar com simulado real no Vercel
- [ ] **Frases oficiais ENEM 2009–2024** — `FRASES[]` em ImprimirClient.tsx usa placeholders
- [ ] **Imagens nas questões** — campo `imagens[]` do JSON não é renderizado ainda
- [ ] **LaTeX/KaTeX** — fórmulas armazenadas como `$formula$` aparecem como texto literal
- [ ] **Marcadores de registro na folha de respostas** — necessários para a Fase 5.5
- [ ] **Gabarito** — tabela de gabarito ao final do PDF

---

## Convenções do Projeto

- **OBRIGATÓRIO**: A cada mudança feita (código, configuração, dados, docs), atualizar este CLAUDE.md em paralelo.
- Sempre preservar o JSON do 2010 ao re-extrair
- Questões anuladas: `gabarito: null` e `anulada: true`
- Imagens ENEM salvas em `dados/imagens/{ano}/{dia}/q{numero:03d}_1.jpg`
- JSONs ENEM em `dados/json/enem_{ano}.json` (v1) e `dados/json_v2/enem_{ano}.json` (v2)
- JSONs EXATO em `dados/EXATO_ORGANIZADO/json_exato/exato_{evento}_{turno}.json`
- Escala de renderização de imagens: 3 (≈216 DPI)
- Fórmulas matemáticas armazenadas como `$formula$` (inline) ou `$$formula$$` (bloco) — renderizar com KaTeX no frontend
- Subscritos/sobrescritos sem Unicode: `$_{c}$`, `$^{2}$`
- `pagina_pdf` é base 0 (primeira página = 0), converter para base 1 no frontend
- PDFs hospedados no Supabase Storage; URL montada por ano/dia, nunca depender de links do governo
- **EXATO simulados**: filtrar por `fonte='EXATO'`; nunca por `ano` (é NULL); usar `evento` e `turno`
- **ENEM simulados**: `dia='simu_dia1'/'simu_dia2'` (NÃO 'dia1'/'dia2') para evitar colisão UNIQUE com ENEM real
- **UFT**: filtrar por `fonte='UFT'`; usar `ano`, `turno`, `evento` (edição: '1_EDICAO'/'2_EDICAO')
- **Provedor**: só ENEM simulados; valores: BERNOULLI, SAS, POLIEDRO, FARIAS_BRITO, SOMOS
- **Extratores novos**: usar `export GROQ_API_KEY=...` (bash) ou `$env:GROQ_API_KEY=...` (PowerShell) — NÃO `set` CMD
- **Gemini Vision**: ativar com `export GEMINI_API_KEY=...`; model padrão `gemini-1.5-flash`; sobrescrever com `GEMINI_MODEL=gemini-2.0-flash` se necessário
- **Arquivo de credenciais**: `HENRYJR_CREDENCIAIS.txt` (não `chaves-projeto.txt`)
- **Race condition extratores**: NUNCA rodar duas instâncias do mesmo extrator simultaneamente — sobrescreve arquivos bons com zeros
- **lib_extrair.py — ordem de extração**: (1) parser de texto sem API → (2) Groq Vision → (3) Gemini Vision fallback
- **Cores proibidas no frontend**: violeta `#7c6af7`, azul frio `#1a1a2e` — substituir sempre pelo dourado `#D4A853`
