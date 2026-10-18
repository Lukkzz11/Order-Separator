@echo off
chcp 65001 > nul
title Vetorizador Inteligente CorelDRAW - Order Separator

echo ===================================================
echo   Order Separator - Vetorizador Profissional
echo   Motor Dual-Spline para Estamparia e DTF
echo ===================================================
echo.
echo Iniciando plugin no CorelDRAW...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0corel-plugin\vetorizador_ia.ps1"

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo Ocorreu um erro ao abrir o vetorizador.
  pause
)
