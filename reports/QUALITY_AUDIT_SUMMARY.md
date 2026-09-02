# Auditoria de qualidade das questões

Data da execução: 02/09/2026.

## Escopo

- 12.958 registros lidos no Supabase, sem exportar credenciais.
- 185 arquivos JSON e 590 PDFs locais inventariados.
- Regras para estrutura, gabarito, alternativas, encoding, imagens, página e duplicidade.
- Validação conservadora contra PDFs oficiais antes de qualquer reparo textual.

## Reparos aplicados

- 3 questões ENEM receberam o texto compartilhado ausente, confirmado pelo cabeçalho da página oficial.
- 12 questões ENEM tiveram cinco alternativas restauradas; cada transcrição integral foi confirmada no texto do PDF.
- 150 questões PAES tiveram cabeçalhos, rodapés, números de página, marcas do espelho e conteúdo de página seguinte removidos dos campos exibidos.
- 102 questões ENEM adicionais tiveram campos textuais recuperados: 3 pelos pilotos de IA, 9 pelo primeiro lote manual revisado e 90 pelos nove lotes manuais seguintes. Os dez lotes manuais também realinharam integralmente comando e alternativas de 100 registros.
- A charge compartilhada pelas questões ENEM 2011 nº 133 e 134 foi recortada da página oficial, conferida e vinculada às duas questões no Storage.
- O segundo lote restaurou os cinco gráficos da questão ENEM 2012 nº 60 como alternativas visuais independentes e vinculou os diagramas oficiais das questões 149/2012 e 136/2013.
- Todas as gravações foram feitas por ID. Os dados brutos locais permanecem disponíveis para reconstrução, e os lotes finais também geraram snapshots locais para rollback.

## Barreiras de precisão

- Alternativas exclusivamente gráficas só são aceitas quando cada opção é recortada da página oficial e vinculada à respectiva letra.
- Texto criptografado ou com caracteres de controle foi descartado.
- Transcrições que continham rodapé ou não apareciam integralmente no PDF foram descartadas.
- 4.678 gabaritos potenciais de simulados foram retidos porque nenhum arquivo atingiu a validação mínima de 98% contra respostas conhecidas.
- Nenhuma classificação de área foi feita por inferência automática nesta etapa.

## Pendências quantificadas

- 6.349 questões de simulados ENEM sem gabarito.
- 547 questões UFT sem gabarito.
- 1.486 questões UNICAMP/FUVEST/UNESP sem área normalizada.
- 718 registros ainda detectados com enunciado textual vazio; parte deles depende de imagem ou texto compartilhado.
- 288 registros com menos alternativas textuais ou visuais do que o esperado.
- 8.208 registros sem referência de página do PDF, concentrados nas fontes importadas e simulados.

Esses grupos exigem revisão por lote com fontes oficiais, OCR/visão local ou autorização explícita para processamento externo. Não devem ser corrigidos por heurística sem conferência.

## Processamento visual externo

- Autorizado pelo responsável em 27/08/2026 para páginas e textos das provas.
- O utilitário `tools/propose_ai_pdf_repairs.py` usa visão de página completa, controle de taxa, retentativas e checkpoint.
- A etapa externa somente produz propostas: não contém operação de gravação no Supabase.
- O aplicador separado só corrige campos ainda defeituosos, exige confirmação e gera backup antes do PATCH.
- O piloto confirmou bloqueio local da Groq com `urllib`, funcionamento via `curl`, chave Gemini inválida e limite `429` da Groq; por isso o intervalo padrão foi elevado para 65 segundos.
- Após a rotação da chave Gemini, um lote direcionado a `statement_missing` aprovou 2 reparos e rejeitou automaticamente 4 propostas divergentes.
- O gerador `tools/build_manual_extraction_batch.py` cria lotes ZIP com PDFs, PNGs das páginas-alvo, manifesto e prompt para revisão assistida no ChatGPT.
- O primeiro resultado manual trouxe os 10 IDs esperados sem duplicidade; todos foram conferidos nas páginas oficiais, uma flexão verbal foi corrigida e o lote foi aplicado com backup.
- O segundo resultado manual também trouxe os 10 IDs exatos. Todos foram conferidos nas páginas oficiais; 10 textos foram aplicados, sete imagens oficiais foram recortadas e vinculadas, e um novo backup foi criado antes da gravação.
- O terceiro resultado manual trouxe os 10 IDs exatos e foi conferido integralmente nas provas de 2014 e 2015. Os textos foram restaurados sem substituir os mapas, fotografias, captura de site e calendário já armazenados.
- O quarto resultado manual trouxe os 10 IDs exatos e foi conferido nas provas de 2015 e 2016. A questão 49/2016 recebeu o diagrama do enunciado e cinco alternativas gráficas oficiais recortadas separadamente.
- Os resultados manuais 005, 006 e 007 foram processados em conjunto: 30 IDs e metadados coincidiram com os manifestos, todo o conteúdo foi comparado às páginas oficiais e os 30 registros passaram na auditoria individual após a gravação.
- As figuras já armazenadas de cinco questões visuais foram preservadas. A questão 86/2016 recebeu o diagrama da onda estacionária e a questão 114/2017 recebeu a equação com fórmulas estruturais, ambos recortados das páginas oficiais.
- Os resultados manuais 008, 009 e 010 acrescentaram outros 30 registros conferidos nas provas de 2019, 2020 e 2022. Seis imagens de enunciado ausentes e dez alternativas exclusivamente gráficas foram recortadas e vinculadas por ID e letra.
- A detecção de alternativas duplicadas passou a preservar os operadores matemáticos `<`, `>` e `=`, eliminando falsos positivos em opções que diferem apenas pela relação entre grandezas.
- A auditoria deixou de classificar `EDUCAÇÃO` como mojibake e passou a aceitar alternativas oficiais de um caractere, como C, N e P.
- A auditoria agora considera uma alternativa representada quando há imagem oficial associada à letra, evitando falso positivo em questões integralmente gráficas.
