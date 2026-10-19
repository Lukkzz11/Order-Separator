@echo off
chcp 65001 > nul
title Vetorizador Profissional CorelDRAW - Order Separator

echo ===================================================
echo   Order Separator - Vetorizador Profissional
echo   Motor Dual-Spline para Estamparia e DTF
echo ===================================================
echo.
echo Iniciando plugin no CorelDRAW...
echo.

where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  start "" pythonw "%~dp0corel-plugin\vetorizador_app.py"
) else (
  if exist "C:\Python314\pythonw.exe" (
    start "" "C:\Python314\pythonw.exe" "%~dp0corel-plugin\vetorizador_app.py"
  ) else (
    start "" python "%~dp0corel-plugin\vetorizador_app.py"
  )
)
