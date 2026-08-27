# Arco C — Upload Script e Frontend: Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Atualizar `upload_novas_questoes.py` com as três novas fontes; adicionar FUVEST, UNICAMP e UNESP ao frontend (lib/provas.ts, FiltroSidebar, questoes/page.tsx, simulado/page.tsx); atualizar CLAUDE.md.

**Architecture:** C1 precisa estar completo antes do Task B4 (upload). C2–C4 são alterações de frontend independentes entre si mas todas dependem de C1 para estar coerentes. C5 finaliza com docs.

**Tech Stack:** Python (upload_novas_questoes.py), Next.js 14 + TypeScript (frontend).

---

## Referências Rápidas

Arquivos a modificar:
- `upload_novas_questoes.py`
- `frontend/lib/provas.ts`
- `frontend/components/FiltroSidebar.tsx`
- `frontend/app/questoes/page.tsx`
- `frontend/app/simulado/page.tsx`
- `CLAUDE.md`

---

## Task C1: Atualizar `upload_novas_questoes.py`

**Files:**
- Modify: `upload_novas_questoes.py`

- [ ] **Step 1: Adicionar UNICAMP, FUVEST, UNESP ao dicionário FONTES**

Localizar o bloco `FONTES` (atualmente linhas ~47-52):

```python
FONTES = {
    "UFT":      BASE / "json_uft",
    "EXATO_P":  BASE / "json_exato_provas",
    "ENEM_SIM": BASE / "json_enem_simulados",
    "PAES":     BASE / "json_paes",
}
```

Substituir por:

```python
FONTES = {
    "UFT":      BASE / "json_uft",
    "EXATO_P":  BASE / "json_exato_provas",
    "ENEM_SIM": BASE / "json_enem_simulados",
    "PAES":     BASE / "json_paes",
    "UNICAMP":  BASE / "json_unicamp",
    "FUVEST":   BASE / "json_fuvest",
    "UNESP":    BASE / "json_unesp",
}
```

- [ ] **Step 2: Atualizar choices do argparse**

Localizar a linha com `choices=["UFT", "EXATO_P", "ENEM_SIM", "PAES"]` e substituir por:

```python
parser.add_argument("--fonte",
                    choices=["UFT", "EXATO_P", "ENEM_SIM", "PAES", "UNICAMP", "FUVEST", "UNESP"],
                    help="Processar só esta fonte (padrão: todas)")
```

- [ ] **Step 3: Verificar dry-run com as novas fontes**

```powershell
python upload_novas_questoes.py --dry-run --fonte UNICAMP
python upload_novas_questoes.py --dry-run --fonte FUVEST
python upload_novas_questoes.py --dry-run --fonte UNESP
```

Esperado: `[dry-run] X questões NÃO inseridas` (ou aviso de pasta não encontrada se ainda não extraído — OK).

- [ ] **Step 4: Commit**

```
git add upload_novas_questoes.py
git commit -m "feat: add UNICAMP/FUVEST/UNESP to upload_novas_questoes.py"
```

---

## Task C2: Atualizar `frontend/lib/provas.ts`

**Files:**
- Modify: `frontend/lib/provas.ts`

- [ ] **Step 1: Adicionar as três novas fontes ao array PROVAS**

Após o objeto `PAES`, adicionar:

```typescript
  {
    id: 'FUVEST',
    nome: 'FUVEST',
    descricao: 'Vestibular da FUVEST (2015–2026)',
    cor: '#8B5CF6',
    corDark: '#6D28D9',
    bg: 'bg-violet-500/15',
    text: 'text-violet-300',
    border: 'border-violet-500/30',
    anos: [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
  },
  {
    id: 'UNICAMP',
    nome: 'UNICAMP',
    descricao: 'Vestibular da UNICAMP (2015–2026)',
    cor: '#06B6D4',
    corDark: '#0891B2',
    bg: 'bg-cyan-500/15',
    text: 'text-cyan-300',
    border: 'border-cyan-500/30',
    anos: [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2026],
  },
  {
    id: 'UNESP',
    nome: 'UNESP',
    descricao: 'Vestibular da UNESP (2017–2025)',
    cor: '#F97316',
    corDark: '#EA580C',
    bg: 'bg-orange-500/15',
    text: 'text-orange-300',
    border: 'border-orange-500/30',
    anos: [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
  },
```

**Nota sobre cores:** O dourado `#D4A853` é reservado para botões/destaque. As cores acima (violeta, ciano, laranja) são para os chips de fonte e são válidas — não violam a regra de "violeta proibido" que se aplica ao violeta `#7c6af7` como cor dominante do layout.

- [ ] **Step 2: Adicionar UNESP ao EVENTO_LABEL**

No objeto `EVENTO_LABEL`, adicionar entradas para edições UNESP (já existem `'1_EDICAO'` e `'2_EDICAO'` para UFT — as mesmas servirão para UNESP):

```typescript
// UFT edições — também usadas por UNESP
'1_EDICAO': '1ª Edição', '2_EDICAO': '2ª Edição',
```

Verificar que estas entradas já existem. Se sim, nenhuma alteração necessária.

- [ ] **Step 3: Verificar que TypeScript compila sem erros**

```powershell
cd frontend
npx tsc --noEmit
```

Esperado: sem erros relacionados a `provas.ts`.

- [ ] **Step 4: Commit**

```
git add frontend/lib/provas.ts
git commit -m "feat: add FUVEST, UNICAMP, UNESP to lib/provas.ts"
```

---

## Task C3: Atualizar `FiltroSidebar.tsx`

**Files:**
- Modify: `frontend/components/FiltroSidebar.tsx`

- [ ] **Step 1: Ler o arquivo para entender o padrão atual**

Verificar como UFT e PAES foram adicionados — localizar os chips de fonte e os filtros condicionais.

- [ ] **Step 2: Adicionar chips `[FUVEST]`, `[UNICAMP]`, `[UNESP]`**

Localizar o bloco de chips de fonte (onde estão `[ENEM]`, `[EXATO]`, `[UFT]`, `[PAES]`).

Adicionar os três novos chips com o mesmo padrão:

```tsx
{/* FUVEST */}
<button
  onClick={() => setFonte('FUVEST')}
  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
    fonte === 'FUVEST'
      ? 'bg-violet-500/30 text-violet-200 border-violet-500/50'
      : 'bg-transparent text-violet-300 border-violet-500/30 hover:bg-violet-500/15'
  }`}
>
  FUVEST
</button>

{/* UNICAMP */}
<button
  onClick={() => setFonte('UNICAMP')}
  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
    fonte === 'UNICAMP'
      ? 'bg-cyan-500/30 text-cyan-200 border-cyan-500/50'
      : 'bg-transparent text-cyan-300 border-cyan-500/30 hover:bg-cyan-500/15'
  }`}
>
  UNICAMP
</button>

{/* UNESP */}
<button
  onClick={() => setFonte('UNESP')}
  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
    fonte === 'UNESP'
      ? 'bg-orange-500/30 text-orange-200 border-orange-500/50'
      : 'bg-transparent text-orange-300 border-orange-500/30 hover:bg-orange-500/15'
  }`}
>
  UNESP
</button>
```

Adaptar os nomes das classes ao padrão exato do arquivo (pode usar `PROVA_MAP['FUVEST'].bg`, `PROVA_MAP['FUVEST'].text` etc. se o arquivo usa a lib/provas.ts para cores).

- [ ] **Step 3: Adicionar filtros condicionais para cada nova fonte**

Usando como modelo os filtros de UFT (que têm Ano + Edição), adicionar:

**FUVEST** — filtro de Ano apenas:
```tsx
{fonte === 'FUVEST' && (
  <div>
    <label className="text-xs text-[#F2EDE4]/60 mb-1 block">Ano</label>
    <select value={ano} onChange={e => setAno(e.target.value)}
            className="w-full bg-[#1E1B17] border border-[#2C2820] rounded px-2 py-1 text-sm text-[#F2EDE4]">
      <option value="">Todos</option>
      {PROVA_MAP['FUVEST'].anos?.map(a => (
        <option key={a} value={String(a)}>{a}</option>
      ))}
    </select>
  </div>
)}
```

**UNICAMP** — filtro de Ano apenas (mesmo padrão, trocar `'FUVEST'` por `'UNICAMP'`).

**UNESP** — filtro de Ano + Edição (para anos com múltiplas edições):
```tsx
{fonte === 'UNESP' && (
  <>
    <div>
      <label className="text-xs text-[#F2EDE4]/60 mb-1 block">Ano</label>
      <select value={ano} onChange={e => setAno(e.target.value)}
              className="w-full bg-[#1E1B17] border border-[#2C2820] rounded px-2 py-1 text-sm text-[#F2EDE4]">
        <option value="">Todos</option>
        {PROVA_MAP['UNESP'].anos?.map(a => (
          <option key={a} value={String(a)}>{a}</option>
        ))}
      </select>
    </div>
    {/* Edição — só para anos com múltiplas aplicações */}
    {['2024', '2025'].includes(ano) && (
      <div>
        <label className="text-xs text-[#F2EDE4]/60 mb-1 block">Edição</label>
        <select value={evento} onChange={e => setEvento(e.target.value)}
                className="w-full bg-[#1E1B17] border border-[#2C2820] rounded px-2 py-1 text-sm text-[#F2EDE4]">
          <option value="">Todas</option>
          <option value="1_EDICAO">1ª Edição</option>
          <option value="2_EDICAO">2ª Edição</option>
        </select>
      </div>
    )}
  </>
)}
```

Adaptar nomes de variáveis de estado (`ano`, `evento`) ao padrão do arquivo.

- [ ] **Step 4: Compilar**

```powershell
npx tsc --noEmit
```

Esperado: sem erros em FiltroSidebar.tsx.

- [ ] **Step 5: Commit**

```
git add frontend/components/FiltroSidebar.tsx
git commit -m "feat: add FUVEST/UNICAMP/UNESP chips and filters to FiltroSidebar"
```

---

## Task C4: Atualizar `questoes/page.tsx` e `simulado/page.tsx`

**Files:**
- Modify: `frontend/app/questoes/page.tsx`
- Modify: `frontend/app/simulado/page.tsx`

- [ ] **Step 1: Verificar como UFT é tratado em `questoes/page.tsx`**

Procurar por `'UFT'` ou `fonte === 'UFT'` no arquivo para entender o padrão de query.

- [ ] **Step 2: Replicar para FUVEST, UNICAMP, UNESP em `questoes/page.tsx`**

Se UFT usa um bloco como:
```tsx
if (fonte === 'UFT') {
  query = query.eq('fonte', 'UFT')
  if (ano) query = query.eq('ano', parseInt(ano))
  if (evento) query = query.eq('evento', evento)
}
```

Adicionar equivalentes:
```tsx
else if (fonte === 'FUVEST') {
  query = query.eq('fonte', 'FUVEST')
  if (ano) query = query.eq('ano', parseInt(ano))
}
else if (fonte === 'UNICAMP') {
  query = query.eq('fonte', 'UNICAMP')
  if (ano) query = query.eq('ano', parseInt(ano))
}
else if (fonte === 'UNESP') {
  query = query.eq('fonte', 'UNESP')
  if (ano) query = query.eq('ano', parseInt(ano))
  if (evento) query = query.eq('evento', evento)
}
```

Adaptar ao padrão exato do arquivo.

- [ ] **Step 3: Atualizar `simulado/page.tsx`**

Localizar onde ENEM/EXATO/UFT são listados como opções de fonte para o simulado.

Adicionar FUVEST, UNICAMP e UNESP como opções válidas:
```tsx
// Na lista de fontes disponíveis para simulado:
const FONTES_SIMULADO = ['ENEM', 'EXATO', 'UFT', 'PAES', 'FUVEST', 'UNICAMP', 'UNESP']
```

Para cada nova fonte, replicar o comportamento de UFT:
- Mostrar seletor de Ano
- Não mostrar Tipo (que é específico do ENEM)
- Para UNESP: mostrar Edição quando o ano selecionado tem múltiplas (2024, 2025)

- [ ] **Step 4: Compilar**

```powershell
npx tsc --noEmit
```

Esperado: sem erros.

- [ ] **Step 5: Verificar funcionamento local**

```powershell
npm run dev
```

Abrir `http://localhost:3000/questoes?fonte=FUVEST` — verificar que a sidebar mostra chip FUVEST selecionado e filtro de Ano.

- [ ] **Step 6: Commit**

```
git add frontend/app/questoes/page.tsx frontend/app/simulado/page.tsx
git commit -m "feat: add FUVEST/UNICAMP/UNESP support to questoes and simulado pages"
```

---

## Task C5: Atualizar CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Atualizar Estrutura de Pastas**

Adicionar ao bloco `dados\`:
```
│   ├── json_unicamp\       # JSONs extraídos UNICAMP — unicamp_{ano}.json
│   ├── json_fuvest\        # JSONs extraídos FUVEST — fuvest_{ano}.json
│   ├── json_unesp\         # JSONs extraídos UNESP — unesp_{ano}[_{evento}].json
│   ├── UNICAMP_PROVAS\     # PDFs do vestibular UNICAMP (2015–2026 sem 2025)
│   ├── FUVEST_PROVAS\      # PDFs da 1ª fase FUVEST (2015–2026)
│   └── UNESP_PROVAS\       # PDFs da 1ª fase UNESP (2017–2025)
```

- [ ] **Step 2: Atualizar lista de ferramentas locais (scripts Python)**

Adicionar ao bloco de scripts:
```
├── extrair_unicamp.py          # Extrai 1ª fase UNICAMP → DADOS/json_unicamp/
├── extrair_fuvest.py           # Extrai 1ª fase FUVEST → DADOS/json_fuvest/
├── extrair_unesp.py            # Extrai 1ª fase UNESP → DADOS/json_unesp/
```

- [ ] **Step 3: Atualizar Totais no Banco de Dados**

Na tabela de totais, adicionar:
```
- **UNICAMP** — ~792 questões (`fonte='UNICAMP'`, `tipo='PROVA'`, `dia='dia1'`, 2015–2026) ✅ no Supabase
- **FUVEST** — ~1.080 questões (`fonte='FUVEST'`, `tipo='PROVA'`, `dia='dia1'`, 2015–2026) ✅ no Supabase
- **UNESP** — ~810 questões (`fonte='UNESP'`, `tipo='PROVA'`, `dia='dia1'`, 2017–2025) ✅ no Supabase
```

- [ ] **Step 4: Atualizar a tabela de campos do Supabase**

Na tabela "Tabela `questoes` — colunas relevantes", adicionar colunas UNICAMP/FUVEST/UNESP com os valores corretos.

- [ ] **Step 5: Atualizar convenções**

Adicionar ao bloco de convenções:
```
- **FUVEST**: filtrar por `fonte='FUVEST'`; usar `ano` (2015–2026); `area=null`; 5 alternativas A–E
- **UNICAMP**: filtrar por `fonte='UNICAMP'`; usar `ano` (2015–2026 sem 2025); `area=null`; 4 alternativas A–D
- **UNESP**: filtrar por `fonte='UNESP'`; usar `ano` (2017–2025) e `evento` (None / '1_EDICAO' / '2_EDICAO' para anos com múltiplos semestres); `area=null`; 5 alternativas A–E
```

- [ ] **Step 6: Atualizar estado do frontend**

No bloco "Frontend (novas fontes)", adicionar:
```
- `FiltroSidebar.tsx`: chips `[FUVEST]`, `[UNICAMP]`, `[UNESP]` adicionados; filtros de Ano (todos); filtro de Edição para UNESP
- `lib/provas.ts`: FUVEST/UNICAMP/UNESP com `anos` definidos
- `questoes/page.tsx`: suporte a `?fonte=FUVEST|UNICAMP|UNESP`
- `simulado/page.tsx`: FUVEST/UNICAMP/UNESP disponíveis como fontes
```

- [ ] **Step 7: Atualizar Próximos Passos**

Marcar como concluídas as tarefas de Arcos A, B e C:
- `✅ Correções UFT (C1 control chars), EXATO Provas (gabarito), PAES (re-extração)`
- `✅ Novos extratores UNICAMP/FUVEST/UNESP (~2.700 questões)`
- `✅ Frontend atualizado com UNICAMP/FUVEST/UNESP`

- [ ] **Step 8: Commit final**

```
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with UNICAMP/FUVEST/UNESP sources and all Arco A/B/C changes"
```

---

## Task C6: Deploy e verificação em produção

- [ ] **Step 1: Push e aguardar deploy Vercel**

```powershell
git push origin main
```

Aguardar o deploy no Vercel (verificar em https://vercel.com/dashboard ou via `gh workflow list`).

- [ ] **Step 2: Verificar em produção**

Acessar https://henryjr.vercel.app/questoes e verificar:
1. Chips `[FUVEST]`, `[UNICAMP]`, `[UNESP]` aparecem na sidebar
2. Clicar em FUVEST → filtro de Ano aparece
3. Clicar em UNICAMP → filtro de Ano aparece
4. Clicar em UNESP → filtro de Ano + Edição aparecem
5. Selecionar FUVEST + Ano 2024 → questões aparecem

- [ ] **Step 3: Verificar simulado**

Acessar https://henryjr.vercel.app/simulado:
1. Selecionar fonte FUVEST → ano disponível
2. Criar simulado → deve funcionar

---

## Checklist de Conclusão do Arco C

- [ ] `upload_novas_questoes.py`: UNICAMP/FUVEST/UNESP adicionados
- [ ] `frontend/lib/provas.ts`: 3 novas fontes com cores e anos
- [ ] `frontend/components/FiltroSidebar.tsx`: chips + filtros para 3 novas fontes
- [ ] `frontend/app/questoes/page.tsx`: suporta `?fonte=FUVEST|UNICAMP|UNESP`
- [ ] `frontend/app/simulado/page.tsx`: 3 novas fontes disponíveis
- [ ] `CLAUDE.md`: totalmente atualizado
- [ ] Deploy Vercel OK
- [ ] Verificação em produção OK
