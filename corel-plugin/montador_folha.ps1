Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# Janela Principal Flutuante (Always-on-Top / Dark Theme)
$form = New-Object System.Windows.Forms.Form
$form.Text = "Order Separator - Montador de Folha (Gang Sheet)"
$form.Size = New-Object System.Drawing.Size(460, 680)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.TopMost = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(11, 15, 25) # Dark Blue/Black
$form.ForeColor = [System.Drawing.Color]::White
$iconPath = "E:\estamparia-manager\build\icon.ico"
if (Test-Path $iconPath) {
  $form.Icon = New-Object System.Drawing.Icon($iconPath)
}

# Fonte Padrão
$fontTitle = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$fontLabel = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$fontInput = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontStats = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Regular)
$fontBtn = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)

# Header
$lblHeader = New-Object System.Windows.Forms.Label
$lblHeader.Text = "⚡ Montador de Folha / Bobina"
$lblHeader.Font = $fontTitle
$lblHeader.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248) # Indigo
$lblHeader.Location = New-Object System.Drawing.Point(20, 15)
$lblHeader.Size = New-Object System.Drawing.Size(400, 25)
$form.Controls.Add($lblHeader)

$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Selecione a arte no CorelDRAW e clique em Montar"
$lblSub.Font = $fontStats
$lblSub.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblSub.Location = New-Object System.Drawing.Point(20, 42)
$lblSub.Size = New-Object System.Drawing.Size(400, 20)
$form.Controls.Add($lblSub)

# Grupo de Pedidos do Order Separator
$lblPedido = New-Object System.Windows.Forms.Label
$lblPedido.Text = "Puxar Quantidade de Pedido Cadastrado (Opcional):"
$lblPedido.Font = $fontLabel
$lblPedido.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblPedido.Location = New-Object System.Drawing.Point(20, 75)
$lblPedido.Size = New-Object System.Drawing.Size(400, 18)
$form.Controls.Add($lblPedido)

$cboPedidos = New-Object System.Windows.Forms.ComboBox
$cboPedidos.Location = New-Object System.Drawing.Point(20, 96)
$cboPedidos.Size = New-Object System.Drawing.Size(405, 26)
$cboPedidos.DropDownStyle = "DropDownList"
$cboPedidos.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$cboPedidos.ForeColor = [System.Drawing.Color]::White
$cboPedidos.Font = $fontInput
$form.Controls.Add($cboPedidos)

# Carrega pedidos do banco local
$dbPath = "$env:APPDATA\estamparia-manager\db_estamparia.json"
if (-not (Test-Path $dbPath)) {
  $dbPath = "$env:APPDATA\Order Separator\db_estamparia.json"
}

$cboPedidos.Items.Add("-- Digitar Quantidade Manualmente --") | Out-Null
$pedidosCarregados = @()
if (Test-Path $dbPath) {
  try {
    $dbJson = Get-Content -Path $dbPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($p in $dbJson.pedidos) {
      $pedidosCarregados += $p
      $cboPedidos.Items.Add("#$($p.numeroPedido) - $($p.clienteNome) ($($p.totalPecas) pcs - $($p.descricaoEstampa))") | Out-Null
    }
  } catch {}
}
$cboPedidos.SelectedIndex = 0

# Campo Quantidade de Estampas
$lblQtd = New-Object System.Windows.Forms.Label
$lblQtd.Text = "Quantidade Total de Estampas:"
$lblQtd.Font = $fontLabel
$lblQtd.Location = New-Object System.Drawing.Point(20, 135)
$lblQtd.Size = New-Object System.Drawing.Size(400, 18)
$form.Controls.Add($lblQtd)

$numQtd = New-Object System.Windows.Forms.NumericUpDown
$numQtd.Location = New-Object System.Drawing.Point(20, 156)
$numQtd.Size = New-Object System.Drawing.Size(190, 26)
$numQtd.Minimum = 1
$numQtd.Maximum = 10000
$numQtd.Value = 24
$numQtd.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numQtd.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
$numQtd.Font = $fontInput
$form.Controls.Add($numQtd)

# Campo Largura da Folha (mm)
$lblLargura = New-Object System.Windows.Forms.Label
$lblLargura.Text = "Largura da Folha / Bobina (mm):"
$lblLargura.Font = $fontLabel
$lblLargura.Location = New-Object System.Drawing.Point(235, 135)
$lblLargura.Size = New-Object System.Drawing.Size(190, 18)
$form.Controls.Add($lblLargura)

$numLargura = New-Object System.Windows.Forms.NumericUpDown
$numLargura.Location = New-Object System.Drawing.Point(235, 156)
$numLargura.Size = New-Object System.Drawing.Size(190, 26)
$numLargura.Minimum = 50
$numLargura.Maximum = 5000
$numLargura.Value = 580
$numLargura.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numLargura.ForeColor = [System.Drawing.Color]::White
$numLargura.Font = $fontInput
$form.Controls.Add($numLargura)

# Botões Rápidos de Largura Padrão
$pnlPresets = New-Object System.Windows.Forms.FlowLayoutPanel
$pnlPresets.Location = New-Object System.Drawing.Point(20, 190)
$pnlPresets.Size = New-Object System.Drawing.Size(405, 32)
$form.Controls.Add($pnlPresets)

$presets = @(
  @{ Nome = "DTF 60cm (580mm)"; Val = 580 },
  @{ Nome = "Bobina 30cm (290mm)"; Val = 290 },
  @{ Nome = "A3 (297mm)"; Val = 297 },
  @{ Nome = "A4 (210mm)"; Val = 210 }
)
foreach ($preset in $presets) {
  $btnPreset = New-Object System.Windows.Forms.Button
  $btnPreset.Text = $preset.Nome
  $btnPreset.Size = New-Object System.Drawing.Size(95, 26)
  $btnPreset.Font = New-Object System.Drawing.Font("Segoe UI", 7.5, [System.Drawing.FontStyle]::Bold)
  $btnPreset.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
  $btnPreset.ForeColor = [System.Drawing.Color]::FromArgb(226, 232, 240)
  $btnPreset.FlatStyle = "Flat"
  $btnPreset.FlatAppearance.BorderSize = 0
  $val = $preset.Val
  $btnPreset.Add_Click({ $numLargura.Value = $val; AtualizarCalculo })
  $pnlPresets.Controls.Add($btnPreset)
}

# Campo Espaçamento (mm) e Margem (mm)
$lblEspaco = New-Object System.Windows.Forms.Label
$lblEspaco.Text = "Espaço entre artes (mm):"
$lblEspaco.Font = $fontLabel
$lblEspaco.Location = New-Object System.Drawing.Point(20, 232)
$lblEspaco.Size = New-Object System.Drawing.Size(190, 18)
$form.Controls.Add($lblEspaco)

$numEspaco = New-Object System.Windows.Forms.NumericUpDown
$numEspaco.Location = New-Object System.Drawing.Point(20, 253)
$numEspaco.Size = New-Object System.Drawing.Size(190, 26)
$numEspaco.Minimum = 0
$numEspaco.Maximum = 100
$numEspaco.Value = 5
$numEspaco.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numEspaco.ForeColor = [System.Drawing.Color]::White
$numEspaco.Font = $fontInput
$form.Controls.Add($numEspaco)

$lblMargem = New-Object System.Windows.Forms.Label
$lblMargem.Text = "Margem nas bordas (mm):"
$lblMargem.Font = $fontLabel
$lblMargem.Location = New-Object System.Drawing.Point(235, 232)
$lblMargem.Size = New-Object System.Drawing.Size(190, 18)
$form.Controls.Add($lblMargem)

$numMargem = New-Object System.Windows.Forms.NumericUpDown
$numMargem.Location = New-Object System.Drawing.Point(235, 253)
$numMargem.Size = New-Object System.Drawing.Size(190, 26)
$numMargem.Minimum = 0
$numMargem.Maximum = 100
$numMargem.Value = 8
$numMargem.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numMargem.ForeColor = [System.Drawing.Color]::White
$numMargem.Font = $fontInput
$form.Controls.Add($numMargem)

# Opções de Giro e Carimbo
$chkCarimbo = New-Object System.Windows.Forms.CheckBox
$chkCarimbo.Text = "Carimbar Ficha Técnica com Grade de Tamanhos no Topo"
$chkCarimbo.Font = $fontLabel
$chkCarimbo.ForeColor = [System.Drawing.Color]::FromArgb(167, 139, 250)
$chkCarimbo.Location = New-Object System.Drawing.Point(20, 292)
$chkCarimbo.Size = New-Object System.Drawing.Size(400, 24)
$chkCarimbo.Checked = $true
$form.Controls.Add($chkCarimbo)

# Caixa de Resumo / Estimativa
$pnlResumo = New-Object System.Windows.Forms.Panel
$pnlResumo.Location = New-Object System.Drawing.Point(20, 328)
$pnlResumo.Size = New-Object System.Drawing.Size(405, 115)
$pnlResumo.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlResumo.BorderStyle = "FixedSingle"
$form.Controls.Add($pnlResumo)

$lblInfoArte = New-Object System.Windows.Forms.Label
$lblInfoArte.Text = "Arte no Corel: Clique em 'Detectar Seleção' abaixo"
$lblInfoArte.Font = $fontStats
$lblInfoArte.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblInfoArte.Location = New-Object System.Drawing.Point(12, 10)
$lblInfoArte.Size = New-Object System.Drawing.Size(380, 20)
$pnlResumo.Controls.Add($lblInfoArte)

$lblColunasInfo = New-Object System.Windows.Forms.Label
$lblColunasInfo.Text = "Colunas por Linha: --"
$lblColunasInfo.Font = $fontLabel
$lblColunasInfo.ForeColor = [System.Drawing.Color]::White
$lblColunasInfo.Location = New-Object System.Drawing.Point(12, 35)
$lblColunasInfo.Size = New-Object System.Drawing.Size(380, 20)
$pnlResumo.Controls.Add($lblColunasInfo)

$lblLinhasInfo = New-Object System.Windows.Forms.Label
$lblLinhasInfo.Text = "Linhas Necessárias: --"
$lblLinhasInfo.Font = $fontLabel
$lblLinhasInfo.ForeColor = [System.Drawing.Color]::White
$lblLinhasInfo.Location = New-Object System.Drawing.Point(12, 60)
$lblLinhasInfo.Size = New-Object System.Drawing.Size(380, 20)
$pnlResumo.Controls.Add($lblLinhasInfo)

$lblMetragemInfo = New-Object System.Windows.Forms.Label
$lblMetragemInfo.Text = "Metragem Estimada da Bobina: --"
$lblMetragemInfo.Font = $fontTitle
$lblMetragemInfo.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153) # Emerald
$lblMetragemInfo.Location = New-Object System.Drawing.Point(12, 83)
$lblMetragemInfo.Size = New-Object System.Drawing.Size(380, 25)
$pnlResumo.Controls.Add($lblMetragemInfo)

# Variável de dimensões da arte detectada
$global:arteDetectadaW = 0
$global:arteDetectadaH = 0

function AtualizarCalculo {
  if ($global:arteDetectadaW -gt 0 -and $global:arteDetectadaH -gt 0) {
    $larguraFolha = [double]$numLargura.Value
    $margem = [double]$numMargem.Value
    $espaco = [double]$numEspaco.Value
    $qtd = [int]$numQtd.Value

    $larguraUtil = $larguraFolha - (2 * $margem)
    $cols = [int][Math]::Floor(($larguraUtil + $espaco) / ($global:arteDetectadaW + $espaco))
    if ($cols -lt 1) { $cols = 1 }

    $rows = [int][Math]::Ceiling($qtd / $cols)
    $altura = ($rows * $global:arteDetectadaH) + (($rows - 1) * $espaco) + (2 * $margem)
    if ($chkCarimbo.Checked) { $altura += 125 } # Altura extra para o carimbo

    $lblColunasInfo.Text = "Colunas por Linha: $cols estampas lado a lado"
    $lblLinhasInfo.Text = "Linhas Necessárias: $rows linhas de repetição"
    $lblMetragemInfo.Text = "Metragem da Folha: " + [Math]::Round($altura / 10, 1) + " cm (" + [Math]::Round($altura / 1000, 2) + " metros)"
  }
}

# Botão Detectar Seleção
$btnDetectar = New-Object System.Windows.Forms.Button
$btnDetectar.Text = "🔍 1. Ler Arte Selecionada no CorelDRAW"
$btnDetectar.Font = $fontBtn
$btnDetectar.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$btnDetectar.ForeColor = [System.Drawing.Color]::White
$btnDetectar.Location = New-Object System.Drawing.Point(20, 455)
$btnDetectar.Size = New-Object System.Drawing.Size(405, 38)
$btnDetectar.FlatStyle = "Flat"
$btnDetectar.FlatAppearance.BorderSize = 0
$btnDetectar.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($btnDetectar)

$btnDetectar.Add_Click({
  try {
    $corel = New-Object -ComObject "CorelDRAW.Application.24"
    $doc = $corel.ActiveDocument
    if (-not $doc) {
      [System.Windows.Forms.MessageBox]::Show("Abra um documento com a arte no CorelDRAW primeiro!", "CorelDRAW", "OK", "Warning")
      return
    }
    $doc.Unit = 4 # mm
    $sel = $corel.ActiveSelection
    if ($sel.Shapes.Count -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Selecione a arte/estampa no CorelDRAW antes de detectar!", "Nenhuma seleção", "OK", "Information")
      return
    }

    $global:arteDetectadaW = [double]$sel.SizeWidth
    $global:arteDetectadaH = [double]$sel.SizeHeight

    $lblInfoArte.Text = "Arte Detectada: " + [Math]::Round($global:arteDetectadaW, 1) + "mm × " + [Math]::Round($global:arteDetectadaH, 1) + "mm"
    $lblInfoArte.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
    AtualizarCalculo
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro ao conectar com CorelDRAW: $($_.Exception.Message)", "Erro", "OK", "Error")
  }
})

# Botão Executar Montagem
$btnMontar = New-Object System.Windows.Forms.Button
$btnMontar.Text = "⚡ 2. MONTAR FOLHA AGORA (GANG SHEET)"
$btnMontar.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$btnMontar.BackColor = [System.Drawing.Color]::FromArgb(79, 70, 229) # Indigo 600
$btnMontar.ForeColor = [System.Drawing.Color]::White
$btnMontar.Location = New-Object System.Drawing.Point(20, 502)
$btnMontar.Size = New-Object System.Drawing.Size(405, 52)
$btnMontar.FlatStyle = "Flat"
$btnMontar.FlatAppearance.BorderSize = 0
$btnMontar.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($btnMontar)

$btnMontar.Add_Click({
  try {
    $corel = New-Object -ComObject "CorelDRAW.Application.24"
    $doc = $corel.ActiveDocument
    if (-not $doc) {
      [System.Windows.Forms.MessageBox]::Show("Abra o CorelDRAW com a arte aberta!", "Aviso", "OK", "Warning")
      return
    }
    $doc.Unit = 4
    $sel = $corel.ActiveSelection
    if ($sel.Shapes.Count -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Por favor, selecione a arte no CorelDRAW para ser duplicada na folha!", "Aviso", "OK", "Warning")
      return
    }

    # Se a seleção tiver mais de uma forma solta, agrupa antes
    if ($sel.Shapes.Count -gt 1) {
      $art = $sel.Group()
    } else {
      $art = $sel.Shapes[1]
    }

    $artW = [double]$art.SizeWidth
    $artH = [double]$art.SizeHeight

    $larguraFolha = [double]$numLargura.Value
    $margem = [double]$numMargem.Value
    $espaco = [double]$numEspaco.Value
    $quantidade = [int]$numQtd.Value

    $larguraUtil = $larguraFolha - (2 * $margem)
    $colunas = [int][Math]::Floor(($larguraUtil + $espaco) / ($artW + $espaco))
    if ($colunas -lt 1) { $colunas = 1 }

    $linhas = [int][Math]::Ceiling($quantidade / $colunas)
    $alturaArtes = ($linhas * $artH) + (($linhas - 1) * $espaco)

    $carimboH = if ($chkCarimbo.Checked) { 130 } else { 0 }
    $alturaTotal = [double]($alturaArtes + (2 * $margem) + $carimboH)

    # Redimensiona a folha do CorelDRAW
    $doc.ActivePage.SetSize([double]$larguraFolha, [double]$alturaTotal)

    # Carimbo opcional no topo da folha
    if ($chkCarimbo.Checked -and $cboPedidos.SelectedIndex -gt 0) {
      $pSel = $pedidosCarregados[$cboPedidos.SelectedIndex - 1]
      if ($pSel) {
        # Desenha o carimbo técnico no topo
        $leftC = [double]($larguraFolha / 2) - 130
        $bottomC = [double]($alturaTotal - $margem - 110)
        
        $layer = $doc.ActiveLayer
        $doc.ClearSelection()
        
        $bgC = $layer.CreateRectangle2($leftC, $bottomC, 260.0, 110.0)
        $bgC.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
        $bgC.Outline.Color.CMYKAssign(0, 0, 0, 100)
        $bgC.Outline.Width = 0.8
        $bgC.Selected = $true

        $hBg = $layer.CreateRectangle2($leftC, ($bottomC + 110 - 24), 260.0, 24.0)
        $hBg.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
        $hBg.Outline.Type = 0
        $hBg.Selected = $true

        $tH = $layer.CreateArtisticText(($leftC + 8), ($bottomC + 110 - 18), "PEDIDO #$($pSel.numeroPedido) | CLIENTE: $($pSel.clienteNome)")
        $tH.Text.Story.Font = "Arial Black"
        $tH.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
        $tH.SetSize(0, 8.5)
        $tH.CenterY = [double]($bottomC + 110 - 12)
        $tH.LeftX = [double]($leftC + 8)
        $tH.Selected = $true

        $tInf = $layer.CreateArtisticText(($leftC + 8), ($bottomC + 110 - 35), "ESTAMPA: $($pSel.descricaoEstampa) | TECIDO: $($pSel.tipoTecido) [$($pSel.corTecido)]")
        $tInf.Text.Story.Font = "Arial Black"
        $tInf.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
        $tInf.SetSize(0, 5.5)
        $tInf.LeftX = [double]($leftC + 8)
        $tInf.Selected = $true

        $corel.ActiveSelection.Group() | Out-Null
      }
    }

    # Posiciona e duplica as artes
    $startX = [double]$margem
    $startY = [double]($alturaTotal - $margem - $carimboH - $artH)

    $art.LeftX = $startX
    $art.BottomY = $startY

    $formasCriadas = @($art)

    for ($i = 1; $i -lt $quantidade; $i++) {
      $col = $i % $colunas
      $row = [Math]::Floor($i / $colunas)

      $x = [double]($startX + ($col * ($artW + $espaco)))
      $y = [double]($startY - ($row * ($artH + $espaco)))

      $copia = $art.Duplicate([double]0, [double]0)
      $copia.LeftX = $x
      $copia.BottomY = $y
      $formasCriadas += $copia
    }

    # Agrupa todas as artes montadas
    $doc.ClearSelection()
    foreach ($f in $formasCriadas) {
      $f.Selected = $true
    }
    $corel.ActiveSelection.Group() | Out-Null

    [System.Windows.Forms.MessageBox]::Show("Folha montada com sucesso no CorelDRAW!`n`n• Total de Estampas: $quantidade`n• Colunas: $colunas por linha`n• Linhas: $linhas`n• Metragem Total: " + [Math]::Round($alturaTotal / 10, 1) + " cm", "Sucesso!", "OK", "Information")
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro ao montar folha: $($_.Exception.Message)", "Erro", "OK", "Error")
  }
})

# Quando o usuário escolhe um pedido na lista, preenche a quantidade automaticamente
$cboPedidos.Add_SelectedIndexChanged({
  if ($cboPedidos.SelectedIndex -gt 0) {
    $p = $pedidosCarregados[$cboPedidos.SelectedIndex - 1]
    if ($p -and $p.totalPecas) {
      $numQtd.Value = [Math]::Max(1, [int]$p.totalPecas)
      AtualizarCalculo
    }
  }
})

$numQtd.Add_ValueChanged({ AtualizarCalculo })
$numLargura.Add_ValueChanged({ AtualizarCalculo })
$numEspaco.Add_ValueChanged({ AtualizarCalculo })
$numMargem.Add_ValueChanged({ AtualizarCalculo })
$chkCarimbo.Add_CheckedChanged({ AtualizarCalculo })

# Atalho no teclado ESC para fechar
$form.KeyPreview = $true
$form.Add_KeyDown({
  if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Escape) {
    $form.Close()
  }
})

$form.ShowDialog() | Out-Null
