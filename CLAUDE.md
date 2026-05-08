# HenryJr — Banco de Questões ENEM

## Visão Geral do Projeto

Plataforma pública de estudos com todas as questões do ENEM (2009–2024), simulados personalizados, progresso por competência, explicações com IA, caderno de erros ("Tira Teima") e correção automática de simulados por foto. Stack 100% gratuita.

## Stack Tecnológica

| Camada | Tecnologia | Status |
|---|---|---|
| Frontend | Next.js 14 + React + Tailwind CSS | Fase 4 (pendente) |
| Banco de dados | Supabase (PostgreSQL + Auth + Storage) | Fase 3 (pendente) |
| Hospedagem frontend | Vercel | Fase 7 (pendente) |
| Hospedagem microserviço | Railway ou Render (gratuito) | Fase 5.5 (pendente) |
| IA para explicações | Groq API (LLaMA 3, gratuito) | Fase 4 (pendente) |
| Geração de PDF | react-pdf + Puppeteer | Fase 5 (pendente) |
| Correção por foto | FastAPI + OpenCV (microserviço Python) | Fase 5.5 (pendente) |
| Extração de dados | Python + PyMuPDF | Fase 2 (em finalização) |

## Credenciais e Chaves (NUNCA commitar no GitHub)

- **Supabase URL**: ver arquivo `chaves-projeto.txt`
- **Supabase Anon Key**: ver arquivo `chaves-projeto.txt`
- **Groq API Key**: ver arquivo `chaves-projeto.txt` (começa com `gsk_...`)
- **Supabase DB Password**: ver arquivo `chaves-projeto.txt`

## Estrutura de Pastas

```
C:\Projetos\henryjr\
├── dados\
│   ├── provas\              # PDFs originais organizados por ano
│   │   ├── 2009\           # dia1.pdf, dia2.pdf, gabarito_dia1.pdf, gabarito_dia2.pdf
│   │   └── ...até 2024\
│   ├── json\               # JSONs extraídos v1 (com gabaritos validados)
│   ├── json_v2\            # JSONs extraídos v2 (extração melhorada — em andamento)
│   ├── imagens\            # Imagens das questões por ano/dia
│   ├── texto_bruto\        # Texto bruto extraído (intermediário)
│   └── frases_capa.txt     # Frases motivacionais das capas (uma por linha) — Fase 2
├── organizar.py                # Renomeia PDFs para o padrão correto
├── extrair.py                  # Extração v1 (texto + gabaritos dos PDFs)
├── extrair_v2.py               # Extração v2 (melhorada, em andamento)
├── diagnostico.py              # Verifica integridade dos JSONs
├── aplicar_gabarito_2010.py    # Aplica gabaritos manuais do 2010
├── corrigir_imagens_v2.py      # Recorte de imagens por região de questão
├── ferramenta_recorte.py       # Ferramenta visual de recorte (Tkinter)
├── gerenciar_imagens.py        # Gerenciador visual de questões/imagens (Tkinter)
├── extrair_paginas_pdf.py      # Extrai campo pagina_pdf para todos os JSONs — Fase 2
├── classificar_competencias.py # Auto-classifica H01–H30 via Groq — Fase 2
├── upload_provas_supabase.py   # Faz upload dos PDFs para Supabase Storage — Fase 3
├── relatorio_erros.json        # Questões reportadas (local até Supabase ativo) — Fase 2
├── chaves-projeto.txt          # Chaves de API (NÃO commitar)
└── CLAUDE.md                   # Este arquivo
```

## Estrutura do JSON de Questões (v2 — alvo)

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

### Campos do JSON

| Campo | Tipo | Descrição | Fase |
|---|---|---|---|
| `numero` | int | Número da questão no caderno | v1 |
| `ano` | int | Ano do ENEM | v1 |
| `dia` | string | "dia1" ou "dia2" | v1 |
| `area` | string | Área de conhecimento | v1 |
| `competencia` | string | Competência H01–H30 (ex.: "H15") | Fase 2 |
| `enunciado` | list[str] | Parágrafos do enunciado | v2 |
| `comando` | string | Frase final antes das alternativas | v2 |
| `alternativas` | dict | Chaves A–E com texto | v2 |
| `gabarito` | string\|null | Letra correta; null = anulada | v1 |
| `confianca` | float | Confiança da extração (0–1) | v2 |
| `revisado` | bool | Revisado manualmente pelo gerenciador | v2 |
| `anulada` | bool | Questão oficialmente anulada | Fase 2 |
| `imagens` | list[dict] | path + posicao no layout | v2 |
| `tem_imagem` | bool | Atalho para filtrar questões com imagem | v2 |
| `pagina_pdf` | int | Página do PDF original (base 0) | Fase 2 |

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
| 2010 | Texto com encoding corrompido (fonte customizada) | Pendente — mesma abordagem do 2021 |
| 2015 | PDFs dia1 e gabarito_dia1 estavam com nomes trocados | Renomeados manualmente |
| 2021 | Texto completamente corrompido (caracteres de controle) | Pendente — a resolver |
| 2024 | Caracteres estranhos extraídos | Pendente — limpeza no pós-processamento |

## Questões Anuladas (sem gabarito — comportamento esperado)

- 2018: Q150
- 2020: Q114, Q141
- 2021: Q178
- 2022: Q175
- 2023: Q177
- 2024: Q129

## Proteção do 2010

**IMPORTANTE**: O JSON do 2010 tem gabaritos inseridos manualmente. O script `extrair.py` tem proteção para não sobrescrever este arquivo. Se precisar re-extrair todos os anos, o 2010 é ignorado automaticamente. Caso o JSON do 2010 seja sobrescrito acidentalmente, rodar `aplicar_gabarito_2010.py` restaura os gabaritos a partir do Word preenchido.

---

## Planejamento de Fases

---

### Fase 1 — Ambiente e Ferramentas ✅ CONCLUÍDA

- VS Code, Node.js, Git, GitHub, Supabase, Vercel, Groq configurados

---

### Fase 2 — Extração e Preparação de Dados 🔄 EM ANDAMENTO

**Extração de texto e gabaritos**
- [x] Extração v1: 2.865 questões (2009–2024) com gabaritos
- [x] Gabarito 2010: 185/185 questões (163 via preenchimento manual)
- [x] Diagnóstico: todos os 16 anos com 4 arquivos presentes
- [ ] Extração v2: detectar alternativas corretamente (padrão `'A\t'` + span seguinte)
- [ ] Resolver encoding corrompido do 2021
- [ ] Limpar caracteres estranhos do 2024

**Imagens**
- [ ] Concluir extração automática de imagens por questão
- [ ] Validação semiautônoma das imagens extraídas

**Novos campos no JSON**
- [ ] `pagina_pdf`: script `extrair_paginas_pdf.py` percorre todos os PDFs com PyMuPDF
      e registra a página de cada questão (reutiliza `mapear_questoes`)
- [ ] `competencia` (H01–H30): script `classificar_competencias.py` envia cada questão
      ao Groq/LLaMA 3 para classificação automática; gerenciar_imagens.py exibe a
      sugestão para validação/correção manual
- [ ] `anulada`: marcar as questões anuladas conhecidas com `anulada: true`

**Ferramentas locais**
- [ ] Modo `--revisao` no `gerenciar_imagens.py`: carrega `relatorio_erros.json` e
      restringe a navegação apenas às questões com `status: "pendente"`, permitindo
      corrigir uma a uma sem precisar procurá-las manualmente
- [ ] Definir estrutura do `relatorio_erros.json` (já documentado acima)

**Dados estáticos**
- [ ] Receber e salvar `frases_capa.txt` com as frases motivacionais das capas de
      cada prova (2009–2024), uma por linha, fornecido manualmente

---

### Fase 3 — Banco de Dados Supabase ⏳ PENDENTE

**Tabelas principais**
- [ ] `questoes`: todas as questões dos JSONs v2
- [ ] `usuarios`: perfis e progresso
- [ ] `subscriptions`: estrutura para assinatura futura
- [ ] `simulados`: registro de cada simulado gerado (tipo, questões, data)
- [ ] `respostas_simulado`: resposta do aluno por questão em cada simulado
- [ ] `questoes_erradas`: histórico de erros por usuário (avulsas e simulado)
- [ ] `tira_teima`: versões do caderno de erros (v1, v2, v3...)
- [ ] `relatorios_erros`: questões reportadas pelos usuários (migração do JSON local)
- [ ] `competencias`: mapeamento H01–H30 com descrição e área

**Supabase Storage**
- [ ] Bucket `provas-pdf`: upload dos 190MB de PDFs via `upload_provas_supabase.py`
      — URL de cada PDF salva como `pdf_url` referenciado por ano/dia
- [ ] Bucket `imagens-questoes`: imagens das questões

**Auth**
- [ ] Login via email + Google (Supabase Auth)

---

### Fase 4 — Interface Next.js ⏳ PENDENTE

**Card de questão**
- [ ] Exibir enunciado com renderização de LaTeX (KaTeX) e imagens posicionadas
- [ ] Tesoura para eliminar alternativas
- [ ] Revelar resposta: incorreta fica vermelha, gabarito fica verde
- [ ] Botão "Explicar esta questão" via Groq API (streaming)
- [ ] Botão "Ver PDF da prova" — abre Supabase Storage com `#page=N` usando `pagina_pdf`
- [ ] Botão "Reportar Erro" — salva no Supabase (`relatorios_erros`) com tipo e descrição

**Busca e filtros**
- [ ] Busca por tema/conteúdo com IA semântica
- [ ] Filtro por área, competência (H01–H30), ano, dificuldade
- [ ] Dificuldade calculada pela taxa de acerto histórica

**Tela inicial / motivação**
- [ ] Exibir frase da capa do ENEM: rotação aleatória ou por ano
      (carregadas do `frases_capa.txt` convertido para JSON estático)

**Caderno de Erros — Tira Teima**
- [ ] Seção dedicada separando erros avulsos de erros em simulado
- [ ] Sugestão de conteúdos, área e competência a estudar com base nos erros
- [ ] Exibir gabarito comentado pela IA (Groq) para cada questão errada

**Login e progresso**
- [ ] Autenticação Supabase (email + Google)
- [ ] Painel de progresso por área e competência (H01–H30)

---

### Fase 5 — PDF Imprimível Layout ENEM ⏳ PENDENTE

**Simulado em PDF**
- [ ] Layout padrão ENEM: 2 colunas, cabeçalho, numeração oficial
- [ ] Renderização de LaTeX (KaTeX server-side ou imagens pré-geradas)
- [ ] Imagens das questões posicionadas conforme campo `posicao`

**Folha de respostas**
- [ ] Bolinhas A–E para cada questão
- [ ] **Marcadores de registro nos 4 cantos** (quadrados sólidos ou ArUco markers)
      — co-projetados com o algoritmo de escaneamento da Fase 5.5
- [ ] Campos para nome, data e identificação do simulado

**Gabarito**
- [ ] Tabela de gabarito padrão ENEM ao final do PDF

**Tira Teima**
- [ ] Mesmo layout do simulado, gerado a partir das questões erradas
- [ ] Identificação da versão na capa (Tira Teima V1, V2, V3...)

---

### Fase 5.5 — Microserviço de Correção por Foto ⏳ PENDENTE

> Serviço Python independente hospedado no Railway ou Render (gratuito).
> Chamado pelo Next.js via API REST após o aluno enviar a foto.

**Tecnologias:** FastAPI + OpenCV + NumPy

**Pipeline de correção:**
1. Receber imagem (JPEG/PNG, foto de celular com leve torção)
2. Detectar os 4 marcadores de registro nos cantos da folha
3. Calcular e aplicar transformação de perspectiva (homografia via `cv2.findHomography`)
4. Mapear posição de cada bolinha com base no layout fixo da folha
5. Threshold de preenchimento por bolinha (distingue marcada de vazia)
6. Retornar JSON `{"respostas": ["A","C","B",...], "total_questoes": 45}`

**Integração com a plataforma:**
- Next.js envia a foto para `/corrigir` do microserviço
- Microserviço retorna as respostas detectadas
- Plataforma compara com gabarito armazenado no Supabase
- Exibe resultado: acertos, erros, nota e questões para o Tira Teima

---

### Fase 6 — Simulado e Painel de Progresso ⏳ PENDENTE

**Modo simulado online**
- [ ] Cronômetro regressivo com estado salvo no localStorage
- [ ] Seleção de questões por área, ano, competência ou aleatório
- [ ] Correção automática ao final

**Correção por foto (simulado físico)**
- [ ] Upload da foto da folha de respostas pelo celular
- [ ] Integração com microserviço da Fase 5.5
- [ ] Exibição de resultado: acertos, erros, distribuição por área

**Gabarito comentado com IA**
- [ ] Após correção (física ou online), listar questões erradas
- [ ] Para cada erro: enviar enunciado + alternativas + gabarito ao Groq (LLaMA 3)
- [ ] Exibir explicação em streaming na plataforma

**Tira Teima (caderno de erros ativo)**
- [ ] Gerar PDF do Tira Teima a partir das questões erradas (reutiliza Fase 5)
- [ ] Corrigir o Tira Teima (física ou online) → questões ainda erradas viram Tira Teima V2
- [ ] Ciclo se repete: V2 → V3 → V4... até zerar os erros
- [ ] Histórico de versões salvo no Supabase (`tira_teima`)

**Painel de progresso**
- [ ] Desempenho por área e competência (H01–H30)
- [ ] Evolução temporal dos acertos
- [ ] Filtro por dificuldade calculada pela taxa de acerto histórica

---

### Fase 7 — Deploy ⏳ PENDENTE

- [ ] Deploy do frontend Next.js no Vercel
- [ ] Deploy do microserviço FastAPI + OpenCV no Railway ou Render
- [ ] Variáveis de ambiente configuradas em ambos os serviços
- [ ] Testes de integração end-to-end (frontend → Supabase → microserviço)

---

## Estado Atual do Projeto

### Concluído ✅
- Fase 1: Ambiente e ferramentas
- Extração v1: 2.865 questões (2009–2024) com gabaritos
- Gabarito 2010: 185/185 questões
- Diagnóstico: todos os 16 anos com 4 arquivos presentes

### Em andamento 🔄
- Fase 2: extração v2, imagens, novos campos JSON

### Próxima tarefa imediata
Concluir extração v2 (`extrair_v2.py`) com detecção correta de alternativas. Padrão confirmado:

```
Span: 'A\t'  — x≈37, negrito (flags=4 ou 16), tamanho 10
Span: 'texto da alternativa A'  — x≈54, não negrito, tamanho 10
Span: 'continuacao se houver'  — x≈54, não negrito (mesma alternativa)
Span: 'B\t'  — x≈37, negrito — nova alternativa
```

---

## Convenções do Projeto

- Sempre preservar o JSON do 2010 ao re-extrair
- Questões anuladas: `gabarito: null` e `anulada: true`
- Imagens salvas em `dados/imagens/{ano}/{dia}/q{numero:03d}_1.jpg`
- JSONs em `dados/json/enem_{ano}.json` (v1) e `dados/json_v2/enem_{ano}.json` (v2)
- Escala de renderização de imagens: 3 (≈216 DPI)
- Backup automático antes de qualquer operação destrutiva no JSON do 2010
- Fórmulas matemáticas armazenadas como `$formula$` (inline) ou `$$formula$$` (bloco) — renderizar com KaTeX no frontend
- Subscritos/sobrescritos sem Unicode disponível armazenados como LaTeX inline: `$_{c}$`, `$^{2}$`
- `pagina_pdf` é base 0 (primeira página = 0), converter para base 1 no frontend
- PDFs hospedados no Supabase Storage; URL montada por ano/dia, nunca depender de links do governo
