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

start "" pythonw "%~dp0corel-plugin\vetorizador_app.py"

if %ERRORLEVEL% NEQ 0 (
  python "%~dp0corel-plugin\vetorizador_app.py"
)
