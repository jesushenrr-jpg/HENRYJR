# Diagnóstico — ENEM 2010 (json_v2)

## Causa raiz

O PDF do ENEM 2010 usa uma **fonte customizada** que impede o PyMuPDF de extrair
texto com encoding correto. Isso gerou dois problemas no `extrair_v2.py`:

### Problema 1 — Enunciado linha-por-linha
O extrator produzia cada linha da passagem como um item separado em `enunciado[]`,
em vez de parágrafos. O `normalizar_comandos.py` fez a mesclagem (merge de linhas),
mas captou apenas o trecho que estava em `enunciado` — o restante do texto ficou
nas alternativas (ver Problema 2).

### Problema 2 — Alternativas completamente erradas (CRÍTICO)
O `extrair_v2.py` usa a detecção de spans com `'A\t'` em negrito para localizar o
início das alternativas. A fonte customizada destrói esses marcadores, então o
extrator nunca encontrou o início correto das alternativas. O resultado foi:

- **155 de 180 questões (86%)** com alternativas erradas
- Conteúdo incorreto nas alternativas (em ordem no campo alts A→E):
  1. Continuação da passagem de texto
  2. Citação bibliográfica
  3. Texto do comando real da questão
  4. 1ª alternativa real (às vezes com espaços removidos, ex: "dosimpactos")
  5. 2ª–5ª alternativas reais **fundidas** em um único campo, separadas por " O "
     (o "O" é o marcador de bolinha do PDF, lido como letra "O")

### Problema 3 — Enunciado incompleto
Como o extrator parava ao detectar (erroneamente) o início das alternativas, apenas
parte da passagem foi salva em `enunciado`. O restante ia para as alternativas erradas.

### Problema 4 — Caracteres substituídos (U+FFFD)
A fonte customizada faz letras acentuadas do português virarem `�` (replacement
character). Exemplo: `imp�rio` em vez de `império`.
Não é corrigível sem OCR ou a tabela interna da fonte.

---

## Padrão das alternativas no PDF (visualizado via OCR)

As alternativas do 2010 usam **bolinhas** (○) antes de cada letra. O Tesseract lê
essas bolinhas como `O` ou `OQ`. Exemplos:

```
O  a maior ocorrência de enchentes...      ← alt A
O  a contaminação da população...          ← alt B
O  o desgaste do solo...                   ← alt C
O  amaior facilidade de captação...        ← alt D (espaço comido pelo OCR)
O  o aumento da incidência...              ← alt E
```

A função `_limpar_alt()` do `reextrair_ocr.py` lida com esses prefixos.

---

## Solução aplicada

**Re-extração via OCR** com Tesseract 5.4.0 + tessdata `por.traineddata`.
Script: `reextrair_ocr.py` (generalizado para qualquer ano).

Parâmetros Tesseract: `--psm 1 --oem 1` (layout automático, LSTM engine).
Resolução: 300 DPI (ZOOM = 300/72).

---

## Aplicabilidade em outros anos

Este diagnóstico é relevante para qualquer ano ENEM cujo PDF apresente:

| Sinal | Diagnóstico provável |
|---|---|
| `json_v2` com `alternativas` contendo passagem/citação | Detecção de alternativas falhou (fonte customizada) |
| Muitas questões com `enunciado=[]` + `comando` muito longo | Extração linha-por-linha sem paragrafação |
| Caracteres `�` massivos no texto | Fonte sem tabela ToUnicode → OCR necessário |
| `extrair_v2.py` retornou 0 questões para o ano | Padrão `'A\t'` não encontrado → re-fazer via OCR |

**Anos com risco similar:** 2010, 2021 (confirmados). Verificar 2019 se houver
reclamação similar durante validação manual.

---

## Estatísticas pós-correção (após reextrair_ocr.py)

| Métrica | Valor |
|---|---|
| Total de questões | 185 |
| Com alternativas | 184/185 |
| Com comando | 183/185 |
| Com enunciado | 177/185 |
| Gabaritos preservados do v1 | 185/185 |
| Questões não localizadas no OCR | 1 (Q108 dia2) |
| Alternativas com fragmento (qualidade baixa) | 77/185 |
| — desses, com imagem (OCR prejudicado) | 60/77 |
| — desses, sem imagem (OCR falhou bolinhas) | 17/77 |

**Comparação com v1 original:** 155/180 (86%) com alternativas completamente erradas → 77/185 (42%) com qualidade reduzida (porém não erradas da mesma forma catastrófica).

## Estratégia de detecção de alternativas (reextrair_ocr.py v2)

Híbrida — tenta em sequência:

1. **Bolinhas em parágrafos** (primária): após `agrupar_paragrafos`, busca o último grupo de 5 parágrafos consecutivos iniciando com padrão `^O[Q]?\s+[A-Za-z]`. Cobre alternativas multi-linha separadas por linhas em branco.

2. **Últimas 5 linhas de conteúdo** (fallback): cobre alternativas de 1 linha sem bolinha detectada pelo OCR.

Casos ainda problemáticos:
- Alternativas 2+ linhas SEM linha em branco entre elas na saída OCR → `agrupar_paragrafos` mescla várias alternativas em 1 parágrafo → fallback de linha captura fragmentos
- Lixo OCR (barcodes, selos) após as alternativas → pode contaminar fallback
