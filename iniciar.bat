@echo off
title Estamparia Manager - Inicializador
cd /d "%~dp0"
echo Iniciando o Estamparia Manager...
call npm.cmd run start
pause
