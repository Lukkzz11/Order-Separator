Attribute VB_Name = "Estamparia_CorelDRAW"
' ==============================================================================
' PLUGIN CORELDRAW 2022 - ESTAMPARIA MANAGER BRIDGE
' Conecta o CorelDRAW ao seu banco de dados e arquivos de pedidos
' ==============================================================================
Option Explicit

' Caminho padrão do banco de dados local do Estamparia Manager
Private Function ObterCaminhoBanco() As String
    Dim wsh As Object
    Set wsh = CreateObject("WScript.Shell")
    ObterCaminhoBanco = wsh.ExpandEnvironmentStrings("%APPDATA%\estamparia-manager\db_estamparia.json")
    Set wsh = Nothing
End Function

' Lê o arquivo JSON do disco
Private Function LerArquivoTexto(caminho As String) As String
    Dim fso As Object, arquivo As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    
    If Not fso.FileExists(caminho) Then
        LerArquivoTexto = ""
        Set fso = Nothing
        Exit Function
    End If
    
    Set arquivo = fso.OpenTextFile(caminho, 1, False, -2) ' TristateUseDefault
    LerArquivoTexto = arquivo.ReadAll
    arquivo.Close
    
    Set arquivo = Nothing
    Set fso = Nothing
End Function

' Parser de JSON nativo usando o motor JS do Windows
Private Function ObterJsonObjeto(jsonTexto As String) As Object
    On Error Resume Next
    Dim html As Object
    Set html = CreateObject("htmlfile")
    html.parentWindow.execScript "function parseJson(str) { return JSON.parse(str); }", "JScript"
    Set ObterJsonObjeto = html.parentWindow.parseJson(jsonTexto)
    Set html = Nothing
    On Error GoTo 0
End Function

' MACRO PRINCIPAL: Consultar Pedido e Mostrar Grade de Tamanhos
Public Sub ConsultarPedidoEstamparia()
    Dim caminhoDb As String
    caminhoDb = ObterCaminhoBanco()
    
    Dim conteudoJson As String
    conteudoJson = LerArquivoTexto(caminhoDb)
    
    If Len(Trim(conteudoJson)) = 0 Then
        MsgBox "O banco de dados do Estamparia Manager ainda não foi inicializado ou não foi encontrado em:" & vbCrLf & caminhoDb, vbExclamation, "Estamparia Manager"
        Exit Sub
    End If
    
    Dim db As Object
    Set db = ObterJsonObjeto(conteudoJson)
    
    If db Is Nothing Then
        MsgBox "Não foi possível interpretar os dados do Estamparia Manager.", vbCritical, "Erro"
        Exit Sub
    End If
    
    Dim totalPedidos As Long
    totalPedidos = db.pedidos.Length
    
    If totalPedidos = 0 Then
        Dim totalClientes As Long
        totalClientes = db.clientes.Length
        
        Dim infoClientes As String
        infoClientes = "Nenhum pedido foi lançado ainda no Estamparia Manager." & vbCrLf & vbCrLf
        infoClientes = infoClientes & "Clientes cadastrados no sistema: " & totalClientes & vbCrLf
        
        Dim i As Long
        For i = 0 To totalClientes - 1
            infoClientes = infoClientes & " • " & db.clientes(i).nome
            If Len(db.clientes(i).loja) > 0 Then
                infoClientes = infoClientes & " (" & db.clientes(i).loja & ")"
            End If
            infoClientes = infoClientes & vbCrLf
        Next i
        
        infoClientes = infoClientes & vbCrLf & "Lance um pedido no seu aplicativo desktop para visualizar aqui a grade de tamanhos."
        MsgBox infoClientes, vbInformation, "Estamparia Manager - CorelDRAW"
        Exit Sub
    End If
    
    ' Lista os pedidos para consulta rápida
    Dim textoMenu As String
    textoMenu = "PEDIDOS ENCONTRADOS NO SISTEMA:" & vbCrLf & vbCrLf
    
    For i = 0 To totalPedidos - 1
        Dim ped As Object
        Set ped = db.pedidos(i)
        textoMenu = textoMenu & "[" & (i + 1) & "] Pedido #" & ped.numeroPedido & " - " & ped.clienteNome & " (" & ped.totalPecas & " peças)" & vbCrLf
    Next i
    
    textoMenu = textoMenu & vbCrLf & "Digite o número da opção (1 a " & totalPedidos & ") para ver a Grade de Tamanhos:"
    
    Dim entrada As String
    entrada = InputBox(textoMenu, "Estamparia Manager - Seleção de Pedido", "1")
    
    If Len(entrada) = 0 Or Not IsNumeric(entrada) Then Exit Sub
    
    Dim indice As Long
    indice = CLng(entrada) - 1
    
    If indice < 0 Or indice >= totalPedidos Then
        MsgBox "Opção inválida!", vbExclamation, "Estamparia Manager"
        Exit Sub
    End If
    
    Dim pedidoEscolhido As Object
    Set pedidoEscolhido = db.pedidos(indice)
    
    ' Monta a exibição detalhada da Grade de Tamanhos
    Dim relatorio As String
    relatorio = "==========================================" & vbCrLf
    relatorio = relatorio & "     ESTAMPA / FICHA TÉCNICA DO PEDIDO" & vbCrLf
    relatorio = relatorio & "==========================================" & vbCrLf
    relatorio = relatorio & "Pedido: #" & pedidoEscolhido.numeroPedido & " (" & pedidoEscolhido.status & ")" & vbCrLf
    relatorio = relatorio & "Cliente: " & pedidoEscolhido.clienteNome
    If Len(pedidoEscolhido.clienteLoja) > 0 Then
        relatorio = relatorio & " - " & pedidoEscolhido.clienteLoja
    End If
    relatorio = relatorio & vbCrLf
    relatorio = relatorio & "Estampa: " & pedidoEscolhido.descricaoEstampa & vbCrLf
    relatorio = relatorio & "Posição: " & pedidoEscolhido.posicaoEstampa & vbCrLf
    relatorio = relatorio & "Tecido: " & pedidoEscolhido.tipoTecido & " (" & pedidoEscolhido.corTecido & ")" & vbCrLf
    relatorio = relatorio & "------------------------------------------" & vbCrLf
    relatorio = relatorio & "GRADE DE QUANTIDADES:" & vbCrLf
    relatorio = relatorio & "  • Tamanho P:   " & pedidoEscolhido.grade.P & " peças" & vbCrLf
    relatorio = relatorio & "  • Tamanho M:   " & pedidoEscolhido.grade.M & " peças" & vbCrLf
    relatorio = relatorio & "  • Tamanho G:   " & pedidoEscolhido.grade.G & " peças" & vbCrLf
    relatorio = relatorio & "  • Tamanho GG:  " & pedidoEscolhido.grade.GG & " peças" & vbCrLf
    relatorio = relatorio & "  • Tamanho XGG: " & pedidoEscolhido.grade.XGG & " peças" & vbCrLf
    relatorio = relatorio & "------------------------------------------" & vbCrLf
    relatorio = relatorio & "TOTAL GERAL: " & pedidoEscolhido.totalPecas & " PEÇAS" & vbCrLf
    relatorio = relatorio & "==========================================" & vbCrLf
    If Len(pedidoEscolhido.observacoes) > 0 Then
        relatorio = relatorio & "Obs Técnicas: " & pedidoEscolhido.observacoes & vbCrLf
    End If
    
    Dim resposta As VbMsgBoxResult
    resposta = MsgBox(relatorio & vbCrLf & "Deseja inserir este carimbo/legenda técnica diretamente na página do CorelDRAW?", vbYesNoCancel + vbInformation, "Estamparia Manager - Grade do Pedido #" & pedidoEscolhido.numeroPedido)
    
    If resposta = vbYes Then
        InserirFichaNaPagina pedidoEscolhido
    End If
End Sub

' Insere carimbo com a grade de tamanhos na arte ativa do CorelDRAW
Private Sub InserirFichaNaPagina(pedido As Object)
    If ActiveDocument Is Nothing Then
        MsgBox "Abra um documento no CorelDRAW para inserir o carimbo da grade!", vbExclamation, "Aviso"
        Exit Sub
    End If
    
    Dim textoFicha As String
    textoFicha = "PEDIDO #" & pedido.numeroPedido & " | CLIENTE: " & UCase(pedido.clienteNome) & vbCrLf & _
                 "GRADE: P: " & pedido.grade.P & " | M: " & pedido.grade.M & " | G: " & pedido.grade.G & " | GG: " & pedido.grade.GG & " | XGG: " & pedido.grade.XGG & " | TOTAL: " & pedido.totalPecas & " PCS" & vbCrLf & _
                 "ESTAMPA: " & pedido.descricaoEstampa & " (" & pedido.posicaoEstampa & ") | TECIDO: " & pedido.tipoTecido & " [" & pedido.corTecido & "]"
    
    ActiveDocument.Unit = cdrMillimeter
    
    Dim s As Shape
    Set s = ActiveLayer.CreateParagraphText(10, 25, 190, 5, textoFicha)
    s.Text.Story.Font = "Arial"
    s.Text.Story.Size = 10
    s.Fill.UniformColor.CMYKAssign 0, 0, 0, 100 ' Preto puro para vegetal/filme
    
    MsgBox "Legenda da grade inserida na página ativa com sucesso!", vbInformation, "Estamparia Manager"
End Sub

' Salva o arquivo atual diretamente na pasta física do cliente
Public Sub SalvarArteNaPastaDoCliente()
    If ActiveDocument Is Nothing Then
        MsgBox "Abra um arquivo primeiro!", vbExclamation, "Estamparia"
        Exit Sub
    End If
    
    Dim caminhoDb As String
    caminhoDb = ObterCaminhoBanco()
    Dim db As Object
    Set db = ObterJsonObjeto(LerArquivoTexto(caminhoDb))
    
    If db Is Nothing Or db.clientes.Length = 0 Then
        MsgBox "Nenhum cliente com pasta cadastrada encontrado no sistema.", vbExclamation, "Estamparia"
        Exit Sub
    End If
    
    Dim lista As String, i As Long
    lista = "Selecione o cliente para salvar a arte:" & vbCrLf & vbCrLf
    For i = 0 To db.clientes.Length - 1
        lista = lista & "[" & (i + 1) & "] " & db.clientes(i).nome & " (" & db.clientes(i).pastaDiretorio & ")" & vbCrLf
    Next i
    
    Dim esc As String
    esc = InputBox(lista, "Salvar na Pasta do Cliente", "1")
    If Len(esc) = 0 Or Not IsNumeric(esc) Then Exit Sub
    
    Dim idx As Long
    idx = CLng(esc) - 1
    If idx < 0 Or idx >= db.clientes.Length Then Exit Sub
    
    Dim pastaDestino As String
    pastaDestino = db.clientes(idx).pastaDiretorio
    
    If Right(pastaDestino, 1) <> "\" Then pastaDestino = pastaDestino & "\"
    
    Dim nomeArquivo As String
    nomeArquivo = ActiveDocument.FileName
    If Len(nomeArquivo) = 0 Or nomeArquivo = "Sem título-1" Or nomeArquivo = "Untitled-1" Then
        nomeArquivo = "Arte_" & db.clientes(idx).nome & "_" & Format(Now, "yyyymmdd_hhnn") & ".cdr"
    End If
    
    ActiveDocument.SaveAs pastaDestino & nomeArquivo
    MsgBox "Arte salva com sucesso em:" & vbCrLf & pastaDestino & nomeArquivo, vbInformation, "Salvo!"
End Sub

' ==============================================================================
' 3. ABRIR FERRAMENTAS INTELIGENTES (MONTADOR, REMOVEDOR, UPSCALER, VETORIZADOR)
' ==============================================================================

Private Function ObterPythonw() As String
    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    If fso.FileExists("C:\Python314\pythonw.exe") Then
        ObterPythonw = "C:\Python314\pythonw.exe"
    Else
        ObterPythonw = "pythonw.exe"
    End If
    Set fso = Nothing
End Function

Public Sub AbrirMontadorDeFolha()
    Dim wsh As Object
    Set wsh = CreateObject("WScript.Shell")
    Dim cmd As String
    cmd = "powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File ""E:\estamparia-manager\corel-plugin\montador_folha.ps1"""
    wsh.Run cmd, 0, False
    Set wsh = Nothing
End Sub

Public Sub AbrirRemovedorIA()
    Dim wsh As Object
    Set wsh = CreateObject("WScript.Shell")
    Dim py As String, cmd As String
    py = ObterPythonw()
    cmd = """" & py & """ ""E:\estamparia-manager\corel-plugin\removedor_fundo_app.py"""
    wsh.Run cmd, 0, False
    Set wsh = Nothing
End Sub

Public Sub AbrirUpscalerIA()
    Dim wsh As Object
    Set wsh = CreateObject("WScript.Shell")
    Dim py As String, cmd As String
    py = ObterPythonw()
    cmd = """" & py & """ ""E:\estamparia-manager\corel-plugin\upscaler_ai_app.py"""
    wsh.Run cmd, 0, False
    Set wsh = Nothing
End Sub

Public Sub AbrirVetorizadorIA()
    Dim wsh As Object
    Set wsh = CreateObject("WScript.Shell")
    Dim py As String, cmd As String
    py = ObterPythonw()
    cmd = """" & py & """ ""E:\estamparia-manager\corel-plugin\vetorizador_app.py"""
    wsh.Run cmd, 0, False
    Set wsh = Nothing
End Sub
