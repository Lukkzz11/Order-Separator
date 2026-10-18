' ==============================================================================
' Script de Manutenção, Limpeza de Cache e Reinicialização sem Bugs
' ==============================================================================
Option Explicit

Dim objShell, objFSO, appDataDir, cacheDir, gpuCacheDir, appExeName, targetCmd

Set objShell = CreateObject("WScript.Shell")
Set objFSO   = CreateObject("Scripting.FileSystemObject")

appExeName = "Estamparia Manager.exe"

' 1. Finaliza processos travados em segundo plano
On Error Resume Next
objShell.Run "taskkill /f /im """ & appExeName & """", 0, True
objShell.Run "taskkill /f /im electron.exe", 0, True
WScript.Sleep 1500 ' Aguarda liberação dos locks de arquivos
On Error GoTo 0

' 2. Limpeza segura apenas dos diretórios de cache temporário
' (Garante que db_estamparia.json e preferências em AppData NÃO sejam apagados)
appDataDir = objShell.ExpandEnvironmentStrings("%APPDATA%\estamparia-manager")

If objFSO.FolderExists(appDataDir) Then
    cacheDir = appDataDir & "\Cache"
    gpuCacheDir = appDataDir & "\GPUCache"
    
    If objFSO.FolderExists(cacheDir) Then
        On Error Resume Next
        objFSO.DeleteFolder cacheDir, True
        On Error GoTo 0
    End If
    
    If objFSO.FolderExists(gpuCacheDir) Then
        On Error Resume Next
        objFSO.DeleteFolder gpuCacheDir, True
        On Error GoTo 0
    End If
End If

' 3. Reinicia a aplicação de forma limpa
Dim unpackedExePath
unpackedExePath = "dist-electron\win-unpacked\" & appExeName

If objFSO.FileExists(appExeName) Then
    objShell.Run """" & appExeName & """", 1, False
ElseIf objFSO.FileExists(unpackedExePath) Then
    objShell.Run """" & unpackedExePath & """", 1, False
Else
    ' Modo de desenvolvimento local
    objShell.Run "cmd /c npm.cmd run start", 0, False
End If

Set objShell = Nothing
Set objFSO = Nothing
