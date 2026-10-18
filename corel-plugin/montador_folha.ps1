Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# Janela Principal Flutuante (Always-on-Top / Dark Theme)
$form = New-Object System.Windows.Forms.Form
$form.Text = "Order Separator - Montador de Folha (Gang Sheet)"
$form.Size = New-Object System.Drawing.Size(465, 660)
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

# Fontes Padronizadas
$fontTitle = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$fontLabel = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$fontInput = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontStats = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Regular)
$fontBtn = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)

# Header
$lblHeader = New-Object System.Windows.Forms.Label
$lblHeader.Text = "Montador de Folha / Bobina (Gang Sheet)"
$lblHeader.Font = $fontTitle
$lblHeader.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248) # Indigo
$lblHeader.Location = New-Object System.Drawing.Point(20, 15)
$lblHeader.Size = New-Object System.Drawing.Size(410, 25)
$form.Controls.Add($lblHeader)

$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Selecione a arte no CorelDRAW e clique em Montar"
$lblSub.Font = $fontStats
$lblSub.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblSub.Location = New-Object System.Drawing.Point(20, 40)
$lblSub.Size = New-Object System.Drawing.Size(410, 18)
$form.Controls.Add($lblSub)

# Grupo de Pedidos do Order Separator
$lblPedido = New-Object System.Windows.Forms.Label
$lblPedido.Text = "Puxar Quantidade de Pedido Cadastrado (Opcional):"
$lblPedido.Font = $fontLabel
$lblPedido.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblPedido.Location = New-Object System.Drawing.Point(20, 68)
$lblPedido.Size = New-Object System.Drawing.Size(410, 18)
$form.Controls.Add($lblPedido)

$cboPedidos = New-Object System.Windows.Forms.ComboBox
$cboPedidos.Location = New-Object System.Drawing.Point(20, 88)
$cboPedidos.Size = New-Object System.Drawing.Size(410, 26)
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

# --- SELETOR DE UNIDADE DE MEDIDA (cm / mm) ---
$pnlUnidade = New-Object System.Windows.Forms.Panel
$pnlUnidade.Location = New-Object System.Drawing.Point(20, 122)
$pnlUnidade.Size = New-Object System.Drawing.Size(410, 26)
$form.Controls.Add($pnlUnidade)

$lblUnidade = New-Object System.Windows.Forms.Label
$lblUnidade.Text = "Unidade de Medida:"
$lblUnidade.Font = $fontLabel
$lblUnidade.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblUnidade.Location = New-Object System.Drawing.Point(0, 4)
$lblUnidade.Size = New-Object System.Drawing.Size(150, 20)
$pnlUnidade.Controls.Add($lblUnidade)

$rbCm = New-Object System.Windows.Forms.RadioButton
$rbCm.Text = "Centimetros (cm)"
$rbCm.Font = $fontLabel
$rbCm.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248) # Indigo
$rbCm.Location = New-Object System.Drawing.Point(155, 2)
$rbCm.Size = New-Object System.Drawing.Size(130, 22)
$rbCm.Checked = $true
$rbCm.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlUnidade.Controls.Add($rbCm)

$rbMm = New-Object System.Windows.Forms.RadioButton
$rbMm.Text = "Milimetros (mm)"
$rbMm.Font = $fontLabel
$rbMm.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$rbMm.Location = New-Object System.Drawing.Point(290, 2)
$rbMm.Size = New-Object System.Drawing.Size(120, 22)
$rbMm.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlUnidade.Controls.Add($rbMm)

# --- CAMPOS QUANTIDADE E LARGURA ---
$lblQtd = New-Object System.Windows.Forms.Label
$lblQtd.Text = "Quantidade de Estampas:"
$lblQtd.Font = $fontLabel
$lblQtd.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblQtd.Location = New-Object System.Drawing.Point(20, 154)
$lblQtd.Size = New-Object System.Drawing.Size(195, 18)
$form.Controls.Add($lblQtd)

$numQtd = New-Object System.Windows.Forms.NumericUpDown
$numQtd.Location = New-Object System.Drawing.Point(20, 174)
$numQtd.Size = New-Object System.Drawing.Size(195, 26)
$numQtd.Minimum = 1
$numQtd.Maximum = 10000
$numQtd.Value = 24
$numQtd.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numQtd.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
$numQtd.Font = $fontInput
$form.Controls.Add($numQtd)

# Campo Largura da Folha (com rótulo dinâmico cm/mm)
$lblLargura = New-Object System.Windows.Forms.Label
$lblLargura.Text = "Largura da Folha / Bobina (cm):"
$lblLargura.Font = $fontLabel
$lblLargura.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblLargura.Location = New-Object System.Drawing.Point(235, 154)
$lblLargura.Size = New-Object System.Drawing.Size(195, 18)
$form.Controls.Add($lblLargura)

$numLargura = New-Object System.Windows.Forms.NumericUpDown
$numLargura.Location = New-Object System.Drawing.Point(235, 174)
$numLargura.Size = New-Object System.Drawing.Size(195, 26)
$numLargura.DecimalPlaces = 1
$numLargura.Minimum = 5
$numLargura.Maximum = 500
$numLargura.Value = 58.0
$numLargura.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numLargura.ForeColor = [System.Drawing.Color]::White
$numLargura.Font = $fontInput
$form.Controls.Add($numLargura)

# Botões Rápidos de Largura Padrão
$pnlPresets = New-Object System.Windows.Forms.FlowLayoutPanel
$pnlPresets.Location = New-Object System.Drawing.Point(20, 206)
$pnlPresets.Size = New-Object System.Drawing.Size(410, 30)
$form.Controls.Add($pnlPresets)

$botoesPresets = @()
function AtualizarBotoesPresets {
  $pnlPresets.Controls.Clear()
  if ($rbCm.Checked) {
    $lista = @(
      @{ Nome = "DTF (58 cm)"; Val = 58.0 },
      @{ Nome = "Bobina (30 cm)"; Val = 30.0 },
      @{ Nome = "A3 (29.7 cm)"; Val = 29.7 },
      @{ Nome = "A4 (21 cm)"; Val = 21.0 }
    )
  } else {
    $lista = @(
      @{ Nome = "DTF (580 mm)"; Val = 580 },
      @{ Nome = "Bobina (300 mm)"; Val = 300 },
      @{ Nome = "A3 (297 mm)"; Val = 297 },
      @{ Nome = "A4 (210 mm)"; Val = 210 }
    )
  }

  foreach ($p in $lista) {
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = $p.Nome
    $btn.Size = New-Object System.Drawing.Size(97, 26)
    $btn.Font = New-Object System.Drawing.Font("Segoe UI", 7.5, [System.Drawing.FontStyle]::Bold)
    $btn.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
    $btn.ForeColor = [System.Drawing.Color]::FromArgb(226, 232, 240)
    $btn.FlatStyle = "Flat"
    $btn.FlatAppearance.BorderSize = 0
    $btn.Cursor = [System.Windows.Forms.Cursors]::Hand
    $val = $p.Val
    $btn.Add_Click({
      $numLargura.Value = [decimal]$val
      AtualizarCalculo
    })
    $pnlPresets.Controls.Add($btn)
  }
}
AtualizarBotoesPresets

# --- CAMPOS ESPACAMENTO E MARGEM ---
$lblEspaco = New-Object System.Windows.Forms.Label
$lblEspaco.Text = "Espaco entre artes (cm):"
$lblEspaco.Font = $fontLabel
$lblEspaco.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblEspaco.Location = New-Object System.Drawing.Point(20, 244)
$lblEspaco.Size = New-Object System.Drawing.Size(195, 18)
$form.Controls.Add($lblEspaco)

$numEspaco = New-Object System.Windows.Forms.NumericUpDown
$numEspaco.Location = New-Object System.Drawing.Point(20, 264)
$numEspaco.Size = New-Object System.Drawing.Size(195, 26)
$numEspaco.DecimalPlaces = 2
$numEspaco.Minimum = 0
$numEspaco.Maximum = 10
$numEspaco.Value = 0.50
$numEspaco.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numEspaco.ForeColor = [System.Drawing.Color]::White
$numEspaco.Font = $fontInput
$form.Controls.Add($numEspaco)

$lblMargem = New-Object System.Windows.Forms.Label
$lblMargem.Text = "Margem nas bordas (cm):"
$lblMargem.Font = $fontLabel
$lblMargem.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblMargem.Location = New-Object System.Drawing.Point(235, 244)
$lblMargem.Size = New-Object System.Drawing.Size(195, 18)
$form.Controls.Add($lblMargem)

$numMargem = New-Object System.Windows.Forms.NumericUpDown
$numMargem.Location = New-Object System.Drawing.Point(235, 264)
$numMargem.Size = New-Object System.Drawing.Size(195, 26)
$numMargem.DecimalPlaces = 2
$numMargem.Minimum = 0
$numMargem.Maximum = 10
$numMargem.Value = 0.80
$numMargem.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numMargem.ForeColor = [System.Drawing.Color]::White
$numMargem.Font = $fontInput
$form.Controls.Add($numMargem)

# Opcao Carimbo
$chkCarimbo = New-Object System.Windows.Forms.CheckBox
$chkCarimbo.Text = "Carimbar Ficha Tecnica com Grade de Tamanhos no Topo"
$chkCarimbo.Font = $fontLabel
$chkCarimbo.ForeColor = [System.Drawing.Color]::FromArgb(167, 139, 250)
$chkCarimbo.Location = New-Object System.Drawing.Point(20, 298)
$chkCarimbo.Size = New-Object System.Drawing.Size(410, 24)
$chkCarimbo.Checked = $true
$chkCarimbo.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($chkCarimbo)

# Caixa de Resumo / Estimativa
$pnlResumo = New-Object System.Windows.Forms.Panel
$pnlResumo.Location = New-Object System.Drawing.Point(20, 330)
$pnlResumo.Size = New-Object System.Drawing.Size(410, 115)
$pnlResumo.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlResumo.BorderStyle = "FixedSingle"
$form.Controls.Add($pnlResumo)

$lblInfoArte = New-Object System.Windows.Forms.Label
$lblInfoArte.Text = "Arte no Corel: Clique em '1. Ler Arte Selecionada' abaixo"
$lblInfoArte.Font = $fontStats
$lblInfoArte.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblInfoArte.Location = New-Object System.Drawing.Point(12, 10)
$lblInfoArte.Size = New-Object System.Drawing.Size(385, 20)
$pnlResumo.Controls.Add($lblInfoArte)

$lblColunasInfo = New-Object System.Windows.Forms.Label
$lblColunasInfo.Text = "Colunas por Linha: --"
$lblColunasInfo.Font = $fontLabel
$lblColunasInfo.ForeColor = [System.Drawing.Color]::White
$lblColunasInfo.Location = New-Object System.Drawing.Point(12, 35)
$lblColunasInfo.Size = New-Object System.Drawing.Size(385, 20)
$pnlResumo.Controls.Add($lblColunasInfo)

$lblLinhasInfo = New-Object System.Windows.Forms.Label
$lblLinhasInfo.Text = "Linhas Necessarias: --"
$lblLinhasInfo.Font = $fontLabel
$lblLinhasInfo.ForeColor = [System.Drawing.Color]::White
$lblLinhasInfo.Location = New-Object System.Drawing.Point(12, 60)
$lblLinhasInfo.Size = New-Object System.Drawing.Size(385, 20)
$pnlResumo.Controls.Add($lblLinhasInfo)

$lblMetragemInfo = New-Object System.Windows.Forms.Label
$lblMetragemInfo.Text = "Metragem Estimada da Bobina: --"
$lblMetragemInfo.Font = $fontTitle
$lblMetragemInfo.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153) # Emerald
$lblMetragemInfo.Location = New-Object System.Drawing.Point(12, 83)
$lblMetragemInfo.Size = New-Object System.Drawing.Size(385, 25)
$pnlResumo.Controls.Add($lblMetragemInfo)

# Variável de dimensões da arte detectada (sempre armazenada em milímetros)
$global:arteDetectadaW = 0.0
$global:arteDetectadaH = 0.0

function ObterValoresMm {
  $fator = if ($rbCm.Checked) { 10.0 } else { 1.0 }
  return @{
    Largura = ([double]$numLargura.Value * $fator)
    Espaco  = ([double]$numEspaco.Value * $fator)
    Margem  = ([double]$numMargem.Value * $fator)
  }
}

function AtualizarCalculo {
  if ($global:arteDetectadaW -gt 0 -and $global:arteDetectadaH -gt 0) {
    $vals = ObterValoresMm
    $larguraFolhaMm = $vals.Largura
    $margemMm = $vals.Margem
    $espacoMm = $vals.Espaco
    $qtd = [int]$numQtd.Value

    $larguraUtilMm = $larguraFolhaMm - (2 * $margemMm)
    $cols = [int][Math]::Floor(($larguraUtilMm + $espacoMm) / ($global:arteDetectadaW + $espacoMm))
    if ($cols -lt 1) { $cols = 1 }

    $rows = [int][Math]::Ceiling($qtd / $cols)
    $alturaMm = ($rows * $global:arteDetectadaH) + (($rows - 1) * $espacoMm) + (2 * $margemMm)
    if ($chkCarimbo.Checked) { $alturaMm += 130 } # Altura extra para o carimbo

    $lblColunasInfo.Text = "Colunas por Linha: $cols estampas lado a lado"
    $lblLinhasInfo.Text = "Linhas Necessarias: $rows linhas de repeticao"

    $cm = [Math]::Round($alturaMm / 10, 1)
    $metros = [Math]::Round($alturaMm / 1000, 2)
    $lblMetragemInfo.Text = "Metragem Estimada: $cm cm ($metros metros)"

    # Atualiza texto da arte detectada na unidade escolhida
    if ($rbCm.Checked) {
      $wCm = [Math]::Round($global:arteDetectadaW / 10, 1)
      $hCm = [Math]::Round($global:arteDetectadaH / 10, 1)
      $lblInfoArte.Text = "Arte Detectada: $wCm cm x $hCm cm"
    } else {
      $wMm = [Math]::Round($global:arteDetectadaW, 1)
      $hMm = [Math]::Round($global:arteDetectadaH, 1)
      $lblInfoArte.Text = "Arte Detectada: $wMm mm x $hMm mm"
    }
  }
}

# --- EVENTOS DE TROCA DE UNIDADE (cm / mm) ---
$rbCm.Add_CheckedChanged({
  if ($rbCm.Checked) {
    $rbCm.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
    $rbMm.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)

    $lblLargura.Text = "Largura da Folha / Bobina (cm):"
    $lblEspaco.Text = "Espaco entre artes (cm):"
    $lblMargem.Text = "Margem nas bordas (cm):"

    $numLargura.DecimalPlaces = 1
    $numLargura.Minimum = 5
    $numLargura.Maximum = 500
    $numLargura.Value = [decimal][Math]::Round(([double]$numLargura.Value / 10.0), 1)

    $numEspaco.DecimalPlaces = 2
    $numEspaco.Minimum = 0
    $numEspaco.Maximum = 10
    $numEspaco.Value = [decimal][Math]::Round(([double]$numEspaco.Value / 10.0), 2)

    $numMargem.DecimalPlaces = 2
    $numMargem.Minimum = 0
    $numMargem.Maximum = 10
    $numMargem.Value = [decimal][Math]::Round(([double]$numMargem.Value / 10.0), 2)

    AtualizarBotoesPresets
    AtualizarCalculo
  }
})

$rbMm.Add_CheckedChanged({
  if ($rbMm.Checked) {
    $rbMm.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
    $rbCm.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)

    $lblLargura.Text = "Largura da Folha / Bobina (mm):"
    $lblEspaco.Text = "Espaco entre artes (mm):"
    $lblMargem.Text = "Margem nas bordas (mm):"

    $numLargura.DecimalPlaces = 0
    $numLargura.Minimum = 50
    $numLargura.Maximum = 5000
    $numLargura.Value = [decimal][Math]::Round(([double]$numLargura.Value * 10.0), 0)

    $numEspaco.DecimalPlaces = 1
    $numEspaco.Minimum = 0
    $numEspaco.Maximum = 100
    $numEspaco.Value = [decimal][Math]::Round(([double]$numEspaco.Value * 10.0), 1)

    $numMargem.DecimalPlaces = 1
    $numMargem.Minimum = 0
    $numMargem.Maximum = 100
    $numMargem.Value = [decimal][Math]::Round(([double]$numMargem.Value * 10.0), 1)

    AtualizarBotoesPresets
    AtualizarCalculo
  }
})

# Botão Detectar Seleção
$btnDetectar = New-Object System.Windows.Forms.Button
$btnDetectar.Text = "1. Ler Arte Selecionada no CorelDRAW"
$btnDetectar.Font = $fontBtn
$btnDetectar.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$btnDetectar.ForeColor = [System.Drawing.Color]::White
$btnDetectar.Location = New-Object System.Drawing.Point(20, 460)
$btnDetectar.Size = New-Object System.Drawing.Size(410, 38)
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
      [System.Windows.Forms.MessageBox]::Show("Selecione a arte/estampa no CorelDRAW antes de detectar!", "Nenhuma selecao", "OK", "Information")
      return
    }

    $global:arteDetectadaW = [double]$sel.SizeWidth
    $global:arteDetectadaH = [double]$sel.SizeHeight

    $lblInfoArte.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
    AtualizarCalculo
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro ao conectar com CorelDRAW: $($_.Exception.Message)", "Erro", "OK", "Error")
  }
})

# Botão Executar Montagem
$btnMontar = New-Object System.Windows.Forms.Button
$btnMontar.Text = "2. MONTAR FOLHA AGORA (GANG SHEET)"
$btnMontar.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$btnMontar.BackColor = [System.Drawing.Color]::FromArgb(79, 70, 229) # Indigo 600
$btnMontar.ForeColor = [System.Drawing.Color]::White
$btnMontar.Location = New-Object System.Drawing.Point(20, 508)
$btnMontar.Size = New-Object System.Drawing.Size(410, 50)
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
    $doc.Unit = 4 # Mantém operações internas em mm para precisão
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

    $vals = ObterValoresMm
    $larguraFolha = [double]$vals.Largura
    $margem = [double]$vals.Margem
    $espaco = [double]$vals.Espaco
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

    # Se a opção de carimbo estiver ativa, cria carimbo técnico no topo
    if ($chkCarimbo.Checked) {
      $pSel = if ($cboPedidos.SelectedIndex -gt 0) { $pedidosCarregados[$cboPedidos.SelectedIndex - 1] } else { $null }

      if ($pSel) {
        $layer = $doc.ActivePage.ActiveLayer
        $leftC = [double]$margem
        $bottomC = [double]($alturaTotal - $margem - 120)

        # Fundo do carimbo
        $bgC = $layer.CreateRectangle2($leftC, $bottomC, 260.0, 110.0)
        $bgC.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
        $bgC.Outline.Color.CMYKAssign(0, 0, 0, 100)
        $bgC.Outline.Width = 0.5
        $bgC.Selected = $true

        # Cabeçalho do carimbo
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

    $cmTotal = [Math]::Round($alturaTotal / 10, 1)
    $mTotal = [Math]::Round($alturaTotal / 1000, 2)
    [System.Windows.Forms.MessageBox]::Show("Folha montada com sucesso no CorelDRAW!`n`n- Total de Estampas: $quantidade`n- Colunas: $colunas por linha`n- Linhas: $linhas`n- Metragem Total: $cmTotal cm ($mTotal metros)", "Sucesso!", "OK", "Information")
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
