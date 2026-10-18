' ==============================================================================
' ESTAMPARIA MANAGER - BRIDGE CORELDRAW
' Executa o painel nativo com leitura completa dos pedidos e grade de tamanhos
' ==============================================================================
Option Explicit

Dim objShell, scriptDir, cmd

Set objShell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

cmd = "powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File """ & scriptDir & "\painel_corel.ps1"""

objShell.Run cmd, 0, False

Set objShell = Nothing
