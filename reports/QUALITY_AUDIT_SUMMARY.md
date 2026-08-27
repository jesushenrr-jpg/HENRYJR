# Auditoria de qualidade das questões

Data da execução: 27/08/2026.

## Escopo

- 12.958 registros lidos no Supabase, sem exportar credenciais.
- 185 arquivos JSON e 590 PDFs locais inventariados.
- Regras para estrutura, gabarito, alternativas, encoding, imagens, página e duplicidade.
- Validação conservadora contra PDFs oficiais antes de qualquer reparo textual.

## Reparos aplicados

- 3 questões ENEM receberam o texto compartilhado ausente, confirmado pelo cabeçalho da página oficial.
- 12 questões ENEM tiveram cinco alternativas restauradas; cada transcrição integral foi confirmada no texto do PDF.
- 150 questões PAES tiveram cabeçalhos, rodapés, números de página, marcas do espelho e conteúdo de página seguinte removidos dos campos exibidos.
- Todas as gravações foram feitas por ID. Os dados brutos locais permanecem disponíveis para reconstrução, e os lotes finais também geraram snapshots locais para rollback.

## Barreiras de precisão

- Candidatos com alternativas gráficas foram descartados.
- Texto criptografado ou com caracteres de controle foi descartado.
- Transcrições que continham rodapé ou não apareciam integralmente no PDF foram descartadas.
- 4.678 gabaritos potenciais de simulados foram retidos porque nenhum arquivo atingiu a validação mínima de 98% contra respostas conhecidas.
- Nenhuma classificação de área foi feita por inferência automática nesta etapa.

## Pendências quantificadas

- 6.349 questões de simulados ENEM sem gabarito.
- 547 questões UFT sem gabarito.
- 1.486 questões UNICAMP/FUVEST/UNESP sem área normalizada.
- 820 registros ainda detectados com enunciado textual vazio; parte deles depende de imagem ou texto compartilhado.
- 293 registros com menos alternativas textuais do que o esperado; muitos têm alternativas gráficas.
- 8.208 registros sem referência de página do PDF, concentrados nas fontes importadas e simulados.

Esses grupos exigem revisão por lote com fontes oficiais, OCR/visão local ou autorização explícita para processamento externo. Não devem ser corrigidos por heurística sem conferência.
