@echo off
chcp 65001 > nul
title Removedor de Fundo IA - Order Separator

echo ===================================================
echo   Order Separator - Removedor de Fundo IA
echo   Recorte Inteligente Local para CorelDRAW e DTF
echo ===================================================
echo.
echo Iniciando plugin no CorelDRAW...
echo.

where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  start "" pythonw "%~dp0corel-plugin\removedor_fundo_app.py"
) else (
  if exist "C:\Python314\pythonw.exe" (
    start "" "C:\Python314\pythonw.exe" "%~dp0corel-plugin\removedor_fundo_app.py"
  ) else (
    start "" python "%~dp0corel-plugin\removedor_fundo_app.py"
  )
)
