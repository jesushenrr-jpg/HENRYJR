@echo off
REM ============================================================
REM  HenryJr — Setup em novo computador
REM  Execute como Administrador na primeira vez
REM ============================================================

echo === HenryJr Setup ===
echo.

REM 1. Instalar dependencias Python
echo [1/3] Instalando dependencias Python...
pip install -r requirements.txt
echo.

REM 2. Restaurar memorias do Claude
echo [2/3] Restaurando memorias do Claude...
for /d %%i in ("%APPDATA%\..\Local\Programs\Claude\*") do echo Pasta Claude: %%i

REM Copiar arquivos de memoria para o local padrao do Claude Code
set CLAUDE_MEM=%USERPROFILE%\.claude\projects
if not exist "%CLAUDE_MEM%" mkdir "%CLAUDE_MEM%"

REM Detectar o hash do projeto (baseado no caminho)
REM O Claude Code usa o caminho absoluto codificado como nome da pasta
REM Verificar em: %USERPROFILE%\.claude\projects\
echo    Memorias disponíveis em: docs\claude-memory\
echo    Copie manualmente para: %USERPROFILE%\.claude\projects\<hash-projeto>\memory\
echo    O hash corresponde ao caminho do projeto clonado.
echo.

REM 3. Verificar Tesseract (necessario apenas para re-extracao OCR)
echo [3/3] Verificando Tesseract OCR...
where tesseract >nul 2>&1
if %errorlevel% == 0 (
    echo    Tesseract encontrado.
) else (
    echo    AVISO: Tesseract nao encontrado.
    echo    Para re-extracao OCR, baixe em:
    echo    https://github.com/UB-Mannheim/tesseract/wiki
    echo    Instale em C:\Program Files\Tesseract-OCR\
    echo    Baixe por.traineddata de:
    echo    https://github.com/tesseract-ocr/tessdata
    echo    Salve em: C:\PROJETOS\HENRYJR\tessdata\
)

echo.
echo === Setup concluido ===
echo Para abrir o gerenciador: python gerenciar_imagens.py
pause
