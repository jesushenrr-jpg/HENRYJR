# Corretor - HenryJr: Design Spec
**Data:** 2026-05-25  
**Status:** Aprovado pelo usuário

---

## Visão Geral

Transformação do `gerenciar_imagens.py` em uma aplicação desktop portátil chamada **CORRETOR - HenryJr**, empacotada como `.exe`, cloud-first (Supabase), com sistema de staging em memória, suporte a todas as categorias de provas (ENEM, EXATO e futuras), e novas abas para frases e acompanhamento de upload.

---

## Arquitetura Geral

```
corretor.py          ← ponto de entrada / janela principal
     │
     ├── ui_questoes.py    (aba "Questões" — editor migrado do gerenciar_imagens.py)
     ├── ui_frases.py      (aba "Frases" — nova)
     ├── ui_upload.py      (aba "Upload" — nova)
     │
     ├── staging.py        (acumula mudanças em memória)
     └── data_layer.py     (toda comunicação com Supabase)
```

**Fluxo principal:**
1. Corretor abre → `data_layer` busca lista de provas/questões do Supabase
2. Usuário edita → `staging` registra a mudança localmente
3. Barra no topo mostra: `● 3 questões · 2 imagens · 1 frase pendentes`
4. Usuário clica **Enviar pacote** → `data_layer` sobe tudo em batch → aba Upload mostra progresso em tempo real

---

## Módulos

### `data_layer.py`
Única peça que se comunica com o Supabase. Interface pública:

| Função | Descrição |
|---|---|
| `listar_categorias()` | Retorna `['ENEM', 'EXATO', ...]` lidos dinamicamente do banco |
| `listar_filtros(categoria)` | Retorna filtros específicos da categoria (ano+dia ou evento+turno) |
| `buscar_questoes(categoria, filtros)` | Retorna lista de questões |
| `buscar_questao(id)` | Retorna questão completa |
| `upsert_questao(q)` | Insere ou atualiza questão |
| `upsert_imagem(path, bytes)` | Faz upload de imagem para o Storage |
| `upsert_frase(f)` | Insere ou atualiza frase |
| `listar_frases()` | Retorna todas as frases do banco |
| `deletar_frase(id)` | Remove frase |
| `renomear_subfiltro(categoria, de, para)` | UPDATE em batch em todas as questões afetadas |

---

### `staging.py`
Memória de sessão — nada sobe ao Supabase sem o clique em "Enviar pacote".

| Função | Descrição |
|---|---|
| `registrar_questao(q)` | Adiciona/substitui questão no staging |
| `registrar_imagem(path, bytes)` | Enfileira imagem para upload |
| `registrar_frase(f)` | Registra frase nova ou editada |
| `listar_pendentes()` | Retorna `{questoes: N, imagens: N, frases: N}` |
| `enviar_tudo(callback_progresso)` | Chama `data_layer` em sequência, reporta progresso via callback |
| `limpar()` | Chamado após upload bem-sucedido |

> O staging é volátil — fechando o Corretor sem enviar, as alterações são perdidas. Comportamento esperado e documentado no guia de testes.

---

### `ui_questoes.py`
Editor migrado do `gerenciar_imagens.py`. Funcionalidades preservadas integralmente:

| Funcionalidade | Origem |
|---|---|
| Navegação por questão (← →, campo numérico) | `_anterior`, `_proxima`, `_ir_para_numero` |
| Edição de enunciado e parágrafos | `_salvar_enunciado` |
| Edição de alternativas A–E (inline) | `_salvar_alternativas` |
| Adicionar imagem (enunciado ou alternativa) | `_adicionar_imagem` |
| Recorte interativo de imagem | `JanelaRecorte` |
| Visualização em tela cheia | `JanelaVisualizacao` |
| Fórmulas LaTeX com preview matplotlib | `JanelaFormula` |
| Subscritos e sobrescritos Unicode | `_aplicar_mapa` |
| Posicionamento de imagem no enunciado | `posicoes_para_n`, editor de posição |
| Miniaturas com Ver / Recortar / Deletar | `_render_thumb_card` |
| Atalhos de teclado e Tab entre campos | `_bind_teclado`, `_configurar_tab` |
| Modo revisão (`--revisao`) | argparse no `corretor.py` |

**Única mudança:** salvamento chama `staging.registrar_questao()` e `staging.registrar_imagem()` em vez de `salvar_json()` e gravar no disco.

---

### `ui_frases.py`
Aba nova para gerenciar frases livres (não vinculadas a uma prova específica).

- Lista de frases existentes carregadas do Supabase ao abrir a aba
- Campos por frase: **Título** + **Texto** + **Categoria** (campo livre)
- Botões: **+ Adicionar** / **Editar** (clique duplo na lista) / **Deletar**
- Ao salvar → `staging.registrar_frase()`

---

### `ui_upload.py`
Aba de acompanhamento de envios.

- Tabela com histórico de uploads da sessão (✅ sucesso / ❌ erro por item)
- Botão **"Enviar pacote"** — dispara `staging.enviar_tudo()` em thread separada
- Barra de progresso por item + barra global
- Botão **"Ver Relatório"** — janela resumida com:
  - Questões enviadas com sucesso / com erro
  - Imagens enviadas / com erro
  - Frases enviadas / com erro
  - Total de itens da sessão
  - Timestamp do último envio

---

### `corretor.py`
Ponto de entrada da aplicação.

- Janela principal com `ttk.Notebook` (abas: **Questões** / **Frases** / **Upload**)
- Barra fina no topo: `● N questões · N imagens · N frases pendentes` — atualizada em tempo real
- Menu **Configurações → Gerenciar Provas** (ver seção abaixo)
- Lê `config.json` ao iniciar; se não existir, exibe tela de configuração de credenciais
- Aceita argumento `--revisao` (modo de revisão de erros pendentes)

---

## Navegação por Categoria de Prova

Dropdown em cascata no topo da aba Questões:

1. **Dropdown 1 — Categoria:** `ENEM` / `EXATO` / futuras (lidas dinamicamente via `data_layer.listar_categorias()`)
2. **Dropdown 2 — Filtro específico:** dinâmico por categoria
   - ENEM → Ano (2009–2024) + Dia (dia1 / dia2)
   - EXATO → Evento (CICLO_ZERO, 1_SIMULADO_TESSAT...) + Turno (MANHA / TARDE)
   - Futuras → conforme campos `evento`/`turno`/`dia` no banco
3. **Dropdown 3 — Número da questão**

**Regra:** nunca filtrar questões EXATO por `ano` — campo é `NULL` intencionalmente.

---

## Gerenciar Provas (Configurações)

Acessível via menu **Configurações → Gerenciar Provas**.

- Lista todas as categorias e seus subfiltros (lidos do Supabase)
- **Renomear:** clique duplo em qualquer item → campo vira editável inline → Salvar
  - Confirmação obrigatória: *"Isso atualizará N questões no banco. Confirmar?"*
  - Operação vai para o staging — só sobe ao clicar "Enviar pacote"
- **Nova categoria:** botão `+ Nova categoria` → preencher nome + subfiltros → Confirmar
  - Nova categoria aparece imediatamente no Dropdown 1
- **Proteções:**
  - Não permite deletar categoria com questões vinculadas
  - Renomear é sempre UPDATE — nunca deleta e recria registros

---

## Portabilidade e Empacotamento .exe

**Ferramenta:** PyInstaller — gera `.exe` com Python e todas as dependências embutidas.

**Estrutura distribuível:**
```
CORRETOR-HENRYJR/
├── CORRETOR-HENRYJR.exe   ← duplo clique para abrir
└── config.json            ← criado automaticamente na 1ª abertura
```

**Primeira abertura:**
- Se `config.json` não existir, janela de configuração pede `SUPABASE_URL` e `SUPABASE_KEY`
- Salva em `config.json` ao lado do `.exe`
- Para trocar credenciais: editar ou deletar `config.json`

**Dependências:** todas embutidas (Tkinter, Pillow, requests, matplotlib). Nenhuma instalação necessária.

**Tamanho estimado:** 80–120 MB (matplotlib é pesado por incluir renderização LaTeX).

**Script de build:**
```
build.bat   ← gera dist/CORRETOR-HENRYJR/ com o .exe pronto
```

---

## Guia de Testes

### Teste 1 — Primeira abertura e configuração
1. Deletar `config.json` (se existir) e abrir `CORRETOR-HENRYJR.exe`
2. ✅ Tela de credenciais aparece
3. Inserir `SUPABASE_URL` e `SUPABASE_KEY` → Salvar
4. ✅ Corretor abre, barra superior mostra *"0 alterações pendentes"*

### Teste 2 — Navegação por categoria
1. Selecionar `ENEM` → ano 2021 → dia1 → questão 5
2. ✅ Enunciado, alternativas e imagens carregam do Supabase
3. Trocar para `EXATO` → selecionar evento e turno
4. ✅ Questões EXATO carregam corretamente

### Teste 3 — Edição e staging
1. Editar enunciado de qualquer questão → Salvar
2. ✅ Barra superior: *"● 1 questão pendente"*
3. Editar alternativa de outra questão → Salvar
4. ✅ Barra superior: *"● 2 questões pendentes"*
5. Fechar e reabrir sem enviar
6. ✅ Staging limpo (comportamento esperado)

### Teste 4 — Adicionar e recortar imagem
1. Clicar **Adicionar imagem** → selecionar `.jpg`
2. ✅ Miniatura aparece, staging: *"+1 imagem pendente"*
3. Clicar **✂ Recortar** → selecionar região → confirmar
4. ✅ Imagem recortada substitui a anterior no staging

### Teste 5 — Fórmulas LaTeX e caracteres especiais
1. Clicar ícone de fórmula → inserir `$x^2 + y^2 = r^2$`
2. ✅ Preview renderiza corretamente
3. Confirmar → texto inserido com sintaxe `$...$`
4. Testar subscrito (H₂O) e sobrescrito (m²)
5. ✅ Caracteres Unicode corretos no campo de texto

### Teste 6 — Aba Frases
1. Abrir aba **Frases**
2. ✅ Lista de frases carregada do Supabase
3. Clicar **+ Adicionar** → preencher Título, Texto, Categoria → Salvar
4. ✅ Frase na lista, barra: *"+1 frase pendente"*
5. Clicar duas vezes em frase → editar → Salvar
6. ✅ Frase atualizada no staging

### Teste 7 — Envio de pacote e progresso
1. Acumular: 2 questões + 1 imagem + 1 frase no staging
2. Aba **Upload** → clicar **"Enviar pacote"**
3. ✅ Barra global no topo avança em tempo real
4. ✅ Tabela mostra cada item com ✅ ou ❌
5. Clicar **"Ver Relatório"**
6. ✅ Janela mostra totais: *"2 questões ✅ · 1 imagem ✅ · 1 frase ✅"*
7. ✅ Barra superior volta para *"0 alterações pendentes"*

### Teste 8 — Gerenciar Provas
1. Abrir **Configurações → Gerenciar Provas**
2. Renomear subfiltro do EXATO
3. ✅ Confirmação com número de questões afetadas
4. Confirmar → verificar no Supabase que o campo foi atualizado
5. Clicar **+ Nova categoria** → preencher → Confirmar
6. ✅ Nova categoria aparece no Dropdown 1

### Teste 9 — Portabilidade
1. Copiar pasta `CORRETOR-HENRYJR/` para outro computador
2. Abrir `CORRETOR-HENRYJR.exe` sem instalar Python
3. ✅ Tela de credenciais aparece
4. Inserir credenciais → ✅ Corretor funciona com os dados do Supabase

---

## Decisões de Design Registradas

| Decisão | Escolha | Motivo |
|---|---|---|
| Arquitetura de dados | Cloud-first (Supabase) | Portabilidade total — sem arquivos locais |
| Upload | Staging em memória + batch | Controle do usuário, evita uploads parciais |
| Navegação por prova | Dropdown em cascata | Interface limpa e extensível para novas categorias |
| Frases | Campo livre (título + texto + categoria) | Não vinculado a uma prova específica |
| Abordagem de código | Refatoração modular (Opção C) | Preserva todas as funcionalidades existentes |
| Empacotamento | PyInstaller | Sem dependências externas no computador de destino |

---

## Arquivos a Criar/Modificar

| Arquivo | Ação |
|---|---|
| `corretor.py` | Criar — ponto de entrada |
| `data_layer.py` | Criar — comunicação Supabase |
| `staging.py` | Criar — acumulador de mudanças |
| `ui_questoes.py` | Criar — migrado de `gerenciar_imagens.py` |
| `ui_frases.py` | Criar — nova aba |
| `ui_upload.py` | Criar — nova aba |
| `build.bat` | Criar — script PyInstaller |
| `gerenciar_imagens.py` | Manter (não deletar até validação completa do Corretor) |
