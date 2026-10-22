@echo off
chcp 65001 > nul
title Upscaler IA Ultra HD - Order Separator

echo ===================================================
echo   Order Separator - Upscaler IA Ultra HD
echo   Super-Resolucao 4x/8x 300 DPI (DirectML RTX GPU)
echo ===================================================
echo.
echo Iniciando plugin de Super-Resolucao...
echo.

where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  start "" pythonw "%~dp0corel-plugin\upscaler_ai_app.py"
) else (
  if exist "C:\Python314\pythonw.exe" (
    start "" "C:\Python314\pythonw.exe" "%~dp0corel-plugin\upscaler_ai_app.py"
  ) else (
    start "" python "%~dp0corel-plugin\upscaler_ai_app.py"
  )
)
