@echo off
echo ============================================
echo   BUILD — CORRETOR - HenryJr
echo ============================================
echo.

REM Limpar builds anteriores
if exist dist\CORRETOR-HENRYJR rmdir /s /q dist\CORRETOR-HENRYJR
if exist build rmdir /s /q build

REM Gerar .exe
pyinstaller corretor.spec --clean

echo.
if exist dist\CORRETOR-HENRYJR\CORRETOR-HENRYJR.exe (
    echo [OK] Build concluido!
    echo Arquivo: dist\CORRETOR-HENRYJR\CORRETOR-HENRYJR.exe
    echo.
    echo Para distribuir, copie a pasta dist\CORRETOR-HENRYJR\ completa.
) else (
    echo [ERRO] Build falhou. Verifique os logs acima.
)
pause
