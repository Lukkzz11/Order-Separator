Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# =========================================================================
# Order Separator - Montador de Folha Inteligente (Gang Sheet / Imposicao)
# Suporte a Multi-Artes, Otimizacao de Bobina e Corredores de Corte p/ Tesoura
# =========================================================================

$form = New-Object System.Windows.Forms.Form
$form.Text = "Order Separator - Montador de Folha Otimizado"
$form.Size = New-Object System.Drawing.Size(520, 780)
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

# Fontes
$fontTitle  = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$fontLabel  = New-Object System.Drawing.Font("Segoe UI", 8.5, [System.Drawing.FontStyle]::Bold)
$fontInput  = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
$fontStats  = New-Object System.Drawing.Font("Segoe UI", 8.5, [System.Drawing.FontStyle]::Regular)
$fontBtn    = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fontSmall  = New-Object System.Drawing.Font("Segoe UI", 8, [System.Drawing.FontStyle]::Regular)

# --- CABECALHO ---
$lblHeader = New-Object System.Windows.Forms.Label
$lblHeader.Text = "Montador de Folha / Bobina (Gang Sheet)"
$lblHeader.Font = $fontTitle
$lblHeader.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248) # Indigo
$lblHeader.Location = New-Object System.Drawing.Point(20, 10)
$lblHeader.Size = New-Object System.Drawing.Size(465, 24)
$form.Controls.Add($lblHeader)

$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Encaixe inteligente com economia de bobina e espaco para tesoura"
$lblSub.Font = $fontStats
$lblSub.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblSub.Location = New-Object System.Drawing.Point(20, 34)
$lblSub.Size = New-Object System.Drawing.Size(465, 18)
$form.Controls.Add($lblSub)

# --- PEDIDOS CADASTRADOS ---
$lblPedido = New-Object System.Windows.Forms.Label
$lblPedido.Text = "Puxar Pedido Cadastrado (Opcional):"
$lblPedido.Font = $fontLabel
$lblPedido.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblPedido.Location = New-Object System.Drawing.Point(20, 56)
$lblPedido.Size = New-Object System.Drawing.Size(465, 16)
$form.Controls.Add($lblPedido)

$cboPedidos = New-Object System.Windows.Forms.ComboBox
$cboPedidos.Location = New-Object System.Drawing.Point(20, 74)
$cboPedidos.Size = New-Object System.Drawing.Size(465, 25)
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

$cboPedidos.Items.Add("-- Digitar Quantidades Manualmente --") | Out-Null
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
$pnlUnidade.Location = New-Object System.Drawing.Point(20, 104)
$pnlUnidade.Size = New-Object System.Drawing.Size(465, 26)
$form.Controls.Add($pnlUnidade)

$lblUnidade = New-Object System.Windows.Forms.Label
$lblUnidade.Text = "Unidade de Medida:"
$lblUnidade.Font = $fontLabel
$lblUnidade.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblUnidade.Location = New-Object System.Drawing.Point(0, 4)
$lblUnidade.Size = New-Object System.Drawing.Size(140, 20)
$pnlUnidade.Controls.Add($lblUnidade)

$rbCm = New-Object System.Windows.Forms.RadioButton
$rbCm.Text = "Centimetros (cm)"
$rbCm.Font = $fontLabel
$rbCm.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248) # Indigo
$rbCm.Location = New-Object System.Drawing.Point(145, 2)
$rbCm.Size = New-Object System.Drawing.Size(145, 22)
$rbCm.Checked = $true
$rbCm.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlUnidade.Controls.Add($rbCm)

$rbMm = New-Object System.Windows.Forms.RadioButton
$rbMm.Text = "Milimetros (mm)"
$rbMm.Font = $fontLabel
$rbMm.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$rbMm.Location = New-Object System.Drawing.Point(305, 2)
$rbMm.Size = New-Object System.Drawing.Size(145, 22)
$rbMm.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlUnidade.Controls.Add($rbMm)

# --- CONFIGURACOES DA FOLHA ---
$lblLargura = New-Object System.Windows.Forms.Label
$lblLargura.Text = "Largura da Folha / Bobina (cm):"
$lblLargura.Font = $fontLabel
$lblLargura.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblLargura.Location = New-Object System.Drawing.Point(20, 134)
$lblLargura.Size = New-Object System.Drawing.Size(225, 16)
$form.Controls.Add($lblLargura)

$numLargura = New-Object System.Windows.Forms.NumericUpDown
$numLargura.Location = New-Object System.Drawing.Point(20, 152)
$numLargura.Size = New-Object System.Drawing.Size(220, 26)
$numLargura.DecimalPlaces = 1
$numLargura.Minimum = 5
$numLargura.Maximum = 500
$numLargura.Value = 58.0
$numLargura.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numLargura.ForeColor = [System.Drawing.Color]::White
$numLargura.Font = $fontInput
$form.Controls.Add($numLargura)

$lblEspaco = New-Object System.Windows.Forms.Label
$lblEspaco.Text = "Espaco p/ Tesoura entre artes (cm):"
$lblEspaco.Font = $fontLabel
$lblEspaco.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblEspaco.Location = New-Object System.Drawing.Point(265, 134)
$lblEspaco.Size = New-Object System.Drawing.Size(220, 16)
$form.Controls.Add($lblEspaco)

$numEspaco = New-Object System.Windows.Forms.NumericUpDown
$numEspaco.Location = New-Object System.Drawing.Point(265, 152)
$numEspaco.Size = New-Object System.Drawing.Size(220, 26)
$numEspaco.DecimalPlaces = 2
$numEspaco.Minimum = 0
$numEspaco.Maximum = 10
$numEspaco.Value = 0.50
$numEspaco.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numEspaco.ForeColor = [System.Drawing.Color]::White
$numEspaco.Font = $fontInput
$form.Controls.Add($numEspaco)

# Presets de Largura
$pnlPresets = New-Object System.Windows.Forms.FlowLayoutPanel
$pnlPresets.Location = New-Object System.Drawing.Point(20, 184)
$pnlPresets.Size = New-Object System.Drawing.Size(465, 28)
$form.Controls.Add($pnlPresets)

function AtualizarBotoesPresets {
  $pnlPresets.Controls.Clear()
  $lista = if ($rbCm.Checked) {
    @(
      @{ Nome = "DTF (58 cm)"; Val = 58.0 },
      @{ Nome = "Bobina (30 cm)"; Val = 30.0 },
      @{ Nome = "A3 (29.7 cm)"; Val = 29.7 },
      @{ Nome = "A4 (21 cm)"; Val = 21.0 }
    )
  } else {
    @(
      @{ Nome = "DTF (580 mm)"; Val = 580 },
      @{ Nome = "Bobina (300 mm)"; Val = 300 },
      @{ Nome = "A3 (297 mm)"; Val = 297 },
      @{ Nome = "A4 (210 mm)"; Val = 210 }
    )
  }

  foreach ($p in $lista) {
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = $p.Nome
    $btn.Size = New-Object System.Drawing.Size(110, 25)
    $btn.Font = New-Object System.Drawing.Font("Segoe UI", 7.5, [System.Drawing.FontStyle]::Bold)
    $btn.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
    $btn.ForeColor = [System.Drawing.Color]::FromArgb(226, 232, 240)
    $btn.FlatStyle = "Flat"
    $btn.FlatAppearance.BorderSize = 0
    $btn.Cursor = [System.Windows.Forms.Cursors]::Hand
    $btn.Tag = [decimal]$p.Val
    $btn.Add_Click({
      $numLargura.Value = [decimal]$this.Tag
      AtualizarCalculo
    })
    $pnlPresets.Controls.Add($btn)
  }
}
AtualizarBotoesPresets

# Margem das Bordas
$lblMargem = New-Object System.Windows.Forms.Label
$lblMargem.Text = "Margem nas bordas da folha (cm):"
$lblMargem.Font = $fontLabel
$lblMargem.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblMargem.Location = New-Object System.Drawing.Point(20, 216)
$lblMargem.Size = New-Object System.Drawing.Size(225, 16)
$form.Controls.Add($lblMargem)

$numMargem = New-Object System.Windows.Forms.NumericUpDown
$numMargem.Location = New-Object System.Drawing.Point(20, 234)
$numMargem.Size = New-Object System.Drawing.Size(220, 26)
$numMargem.DecimalPlaces = 2
$numMargem.Minimum = 0
$numMargem.Maximum = 10
$numMargem.Value = 0.80
$numMargem.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numMargem.ForeColor = [System.Drawing.Color]::White
$numMargem.Font = $fontInput
$form.Controls.Add($numMargem)

# Opcoes Inteligentes de Encaixe e Corte
$chkGiro = New-Object System.Windows.Forms.CheckBox
$chkGiro.Text = "Otimizar Encaixe: Girar artes para economizar bobina"
$chkGiro.Font = $fontLabel
$chkGiro.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153) # Emerald
$chkGiro.Location = New-Object System.Drawing.Point(265, 218)
$chkGiro.Size = New-Object System.Drawing.Size(225, 20)
$chkGiro.Checked = $true
$chkGiro.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($chkGiro)

$chkLinhasCorte = New-Object System.Windows.Forms.CheckBox
$chkLinhasCorte.Text = "Tracar linhas-guia para corte reto com tesoura"
$chkLinhasCorte.Font = $fontLabel
$chkLinhasCorte.ForeColor = [System.Drawing.Color]::FromArgb(147, 197, 253) # Light Blue
$chkLinhasCorte.Location = New-Object System.Drawing.Point(265, 240)
$chkLinhasCorte.Size = New-Object System.Drawing.Size(225, 20)
$chkLinhasCorte.Checked = $true
$chkLinhasCorte.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($chkLinhasCorte)

# Opcao de Agrupar Selecao em 1 Unica Arte
$chkAgrupar = New-Object System.Windows.Forms.CheckBox
$chkAgrupar.Text = "Agrupar selecao em 1 unica arte (se a estampa tiver varias partes soltas)"
$chkAgrupar.Font = $fontLabel
$chkAgrupar.ForeColor = [System.Drawing.Color]::FromArgb(251, 191, 36) # Amber
$chkAgrupar.Location = New-Object System.Drawing.Point(20, 266)
$chkAgrupar.Size = New-Object System.Drawing.Size(465, 20)
$chkAgrupar.Checked = $false
$chkAgrupar.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($chkAgrupar)

$chkCarimbo = New-Object System.Windows.Forms.CheckBox
$chkCarimbo.Text = "Carimbar Ficha Tecnica com Grade no Topo"
$chkCarimbo.Font = $fontLabel
$chkCarimbo.ForeColor = [System.Drawing.Color]::FromArgb(167, 139, 250)
$chkCarimbo.Location = New-Object System.Drawing.Point(20, 288)
$chkCarimbo.Size = New-Object System.Drawing.Size(465, 20)
$chkCarimbo.Checked = $false
$chkCarimbo.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($chkCarimbo)

# --- BOTAO 1: LER SELECAO DO CORELDRAW ---
$btnDetectar = New-Object System.Windows.Forms.Button
$btnDetectar.Text = "1. Ler Arte(s) Selecionada(s) no CorelDRAW"
$btnDetectar.Font = $fontBtn
$btnDetectar.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$btnDetectar.ForeColor = [System.Drawing.Color]::White
$btnDetectar.Location = New-Object System.Drawing.Point(20, 314)
$btnDetectar.Size = New-Object System.Drawing.Size(465, 36)
$btnDetectar.FlatStyle = "Flat"
$btnDetectar.FlatAppearance.BorderSize = 0
$btnDetectar.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($btnDetectar)

# --- BARRA DE QUANTIDADE GLOBAL RAPIDA ---
$pnlQtdGlobal = New-Object System.Windows.Forms.Panel
$pnlQtdGlobal.Location = New-Object System.Drawing.Point(20, 356)
$pnlQtdGlobal.Size = New-Object System.Drawing.Size(465, 30)
$form.Controls.Add($pnlQtdGlobal)

$lblQtdGlobal = New-Object System.Windows.Forms.Label
$lblQtdGlobal.Text = "Qtd de Copias:"
$lblQtdGlobal.Font = $fontLabel
$lblQtdGlobal.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblQtdGlobal.Location = New-Object System.Drawing.Point(0, 6)
$lblQtdGlobal.Size = New-Object System.Drawing.Size(100, 20)
$pnlQtdGlobal.Controls.Add($lblQtdGlobal)

$numQtdGlobal = New-Object System.Windows.Forms.NumericUpDown
$numQtdGlobal.Location = New-Object System.Drawing.Point(105, 3)
$numQtdGlobal.Size = New-Object System.Drawing.Size(80, 24)
$numQtdGlobal.Minimum = 1
$numQtdGlobal.Maximum = 10000
$numQtdGlobal.Value = 26
$numQtdGlobal.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numQtdGlobal.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
$numQtdGlobal.Font = $fontInput
$pnlQtdGlobal.Controls.Add($numQtdGlobal)

$numQtdGlobal.Add_ValueChanged({
  $novaQtd = [int]$numQtdGlobal.Value
  foreach ($a in $global:artesDetectadas) {
    $a.Qtd = $novaQtd
    if ($a.Control) {
      $a.Control.Value = [decimal]$novaQtd
    }
  }
  AtualizarCalculo
})

$btnAplicarTodas = New-Object System.Windows.Forms.Button
$btnAplicarTodas.Text = "Aplicar esta Quantidade a Todas as Artes"
$btnAplicarTodas.Font = New-Object System.Drawing.Font("Segoe UI", 8, [System.Drawing.FontStyle]::Bold)
$btnAplicarTodas.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$btnAplicarTodas.ForeColor = [System.Drawing.Color]::FromArgb(226, 232, 240)
$btnAplicarTodas.Location = New-Object System.Drawing.Point(195, 2)
$btnAplicarTodas.Size = New-Object System.Drawing.Size(270, 26)
$btnAplicarTodas.FlatStyle = "Flat"
$btnAplicarTodas.FlatAppearance.BorderSize = 0
$btnAplicarTodas.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnAplicarTodas.Add_Click({
  $novaQtd = [int]$numQtdGlobal.Value
  foreach ($a in $global:artesDetectadas) {
    $a.Qtd = $novaQtd
    if ($a.Control) {
      $a.Control.Value = [decimal]$novaQtd
    }
  }
  AtualizarCalculo
})
$pnlQtdGlobal.Controls.Add($btnAplicarTodas)

# --- LISTA / GRID DE ARTES DETECTADAS ---
$pnlArtes = New-Object System.Windows.Forms.Panel
$pnlArtes.Location = New-Object System.Drawing.Point(20, 392)
$pnlArtes.Size = New-Object System.Drawing.Size(465, 125)
$pnlArtes.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlArtes.BorderStyle = "FixedSingle"
$pnlArtes.AutoScroll = $true
$form.Controls.Add($pnlArtes)

# Painel de Resumo / Estimativa de Economia
$pnlResumo = New-Object System.Windows.Forms.Panel
$pnlResumo.Location = New-Object System.Drawing.Point(20, 524)
$pnlResumo.Size = New-Object System.Drawing.Size(465, 100)
$pnlResumo.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlResumo.BorderStyle = "FixedSingle"
$form.Controls.Add($pnlResumo)

$lblStatusSelecao = New-Object System.Windows.Forms.Label
$lblStatusSelecao.Text = "Nenhuma arte lida ainda. Selecione 1 ou mais desenhos no Corel."
$lblStatusSelecao.Font = $fontStats
$lblStatusSelecao.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblStatusSelecao.Location = New-Object System.Drawing.Point(12, 6)
$lblStatusSelecao.Size = New-Object System.Drawing.Size(440, 18)
$pnlResumo.Controls.Add($lblStatusSelecao)

$lblOtimizacaoInfo = New-Object System.Windows.Forms.Label
$lblOtimizacaoInfo.Text = "Otimizacao: --"
$lblOtimizacaoInfo.Font = $fontLabel
$lblOtimizacaoInfo.ForeColor = [System.Drawing.Color]::White
$lblOtimizacaoInfo.Location = New-Object System.Drawing.Point(12, 26)
$lblOtimizacaoInfo.Size = New-Object System.Drawing.Size(440, 18)
$pnlResumo.Controls.Add($lblOtimizacaoInfo)

$lblCorredoresInfo = New-Object System.Windows.Forms.Label
$lblCorredoresInfo.Text = "Corte com Tesoura: Alinhamento retangular continuo"
$lblCorredoresInfo.Font = $fontSmall
$lblCorredoresInfo.ForeColor = [System.Drawing.Color]::FromArgb(147, 197, 253)
$lblCorredoresInfo.Location = New-Object System.Drawing.Point(12, 46)
$lblCorredoresInfo.Size = New-Object System.Drawing.Size(440, 18)
$pnlResumo.Controls.Add($lblCorredoresInfo)

$lblMetragemInfo = New-Object System.Windows.Forms.Label
$lblMetragemInfo.Text = "Metragem Estimada da Bobina: --"
$lblMetragemInfo.Font = $fontTitle
$lblMetragemInfo.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153) # Emerald
$lblMetragemInfo.Location = New-Object System.Drawing.Point(12, 66)
$lblMetragemInfo.Size = New-Object System.Drawing.Size(440, 24)
$pnlResumo.Controls.Add($lblMetragemInfo)

# --- BOTAO 2: MONTAR FOLHA ---
$btnMontar = New-Object System.Windows.Forms.Button
$btnMontar.Text = "2. MONTAR FOLHA OTIMIZADA (GANG SHEET)"
$btnMontar.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$btnMontar.BackColor = [System.Drawing.Color]::FromArgb(79, 70, 229) # Indigo 600
$btnMontar.ForeColor = [System.Drawing.Color]::White
$btnMontar.Location = New-Object System.Drawing.Point(20, 632)
$btnMontar.Size = New-Object System.Drawing.Size(465, 48)
$btnMontar.FlatStyle = "Flat"
$btnMontar.FlatAppearance.BorderSize = 0
$btnMontar.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($btnMontar)

# --- ESTRUTURA DE DADOS DAS ARTES DETECTADAS ---
$global:artesDetectadas = @()

# Atualiza a exibicao da lista de artes na interface
function RenderizarListaArtes {
  $pnlArtes.Controls.Clear()

  if ($global:artesDetectadas.Count -eq 0) {
    $lblVazio = New-Object System.Windows.Forms.Label
    $lblVazio.Text = "Nenhuma arte carregada. Selecione os desenhos no Corel e clique acima."
    $lblVazio.ForeColor = [System.Drawing.Color]::FromArgb(100, 116, 139)
    $lblVazio.Font = $fontStats
    $lblVazio.Location = New-Object System.Drawing.Point(15, 48)
    $lblVazio.Size = New-Object System.Drawing.Size(430, 30)
    $pnlArtes.Controls.Add($lblVazio)
    return
  }

  $yPos = 8
  for ($idx = 0; $idx -lt $global:artesDetectadas.Count; $idx++) {
    $item = $global:artesDetectadas[$idx]
    
    # Painel do item
    $pnlItem = New-Object System.Windows.Forms.Panel
    $pnlItem.Location = New-Object System.Drawing.Point(8, $yPos)
    $pnlItem.Size = New-Object System.Drawing.Size(430, 36)
    $pnlItem.BackColor = [System.Drawing.Color]::FromArgb(24, 33, 56)
    $pnlArtes.Controls.Add($pnlItem)

    $unitTxt = if ($rbCm.Checked) { "cm" } else { "mm" }
    $wDisp = [Math]::Round($item.W, 1)
    $hDisp = [Math]::Round($item.H, 1)

    $lblNome = New-Object System.Windows.Forms.Label
    $lblNome.Text = "Desenho #$($idx + 1) ($wDisp x $hDisp $unitTxt)"
    $lblNome.ForeColor = [System.Drawing.Color]::White
    $lblNome.Font = $fontLabel
    $lblNome.Location = New-Object System.Drawing.Point(8, 9)
    $lblNome.Size = New-Object System.Drawing.Size(235, 20)
    $pnlItem.Controls.Add($lblNome)

    $lblQtdItem = New-Object System.Windows.Forms.Label
    $lblQtdItem.Text = "Qtd:"
    $lblQtdItem.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
    $lblQtdItem.Font = $fontLabel
    $lblQtdItem.Location = New-Object System.Drawing.Point(245, 9)
    $lblQtdItem.Size = New-Object System.Drawing.Size(35, 20)
    $pnlItem.Controls.Add($lblQtdItem)

    $numQtdItem = New-Object System.Windows.Forms.NumericUpDown
    $numQtdItem.Location = New-Object System.Drawing.Point(285, 6)
    $numQtdItem.Size = New-Object System.Drawing.Size(80, 24)
    $numQtdItem.Minimum = 1
    $numQtdItem.Maximum = 10000
    $numQtdItem.Value = [decimal]$item.Qtd
    $numQtdItem.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
    $numQtdItem.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
    $numQtdItem.Font = $fontInput
    
    # Guarda o controle diretamente no objeto para leitura 100% garantida
    $item.Control = $numQtdItem
    
    $numQtdItem.Add_ValueChanged({
      $item.Qtd = [int]$this.Value
      AtualizarCalculo
    })
    $pnlItem.Controls.Add($numQtdItem)

    $yPos += 42
  }
}

# --- FUNCAO UNIFICADA DE ENCAIXE INTELIGENTE (GANG SHEET PACKING) ---
function ExecutarPacking {
  param(
    $artes,
    [double]$larguraFolha,
    [double]$margem,
    [double]$espaco,
    [bool]$otimizarGiro
  )

  $larguraUtil = [Math]::Max(1.0, ($larguraFolha - (2.0 * $margem)))
  $blocos = @()

  foreach ($a in $artes) {
    $w = [double]$a.W
    $h = [double]$a.H
    $qtd = [int]$a.Qtd
    if ($qtd -le 0) { continue }
    $rot = $false

    if ($otimizarGiro) {
      $cabeNorm = ($w -le $larguraUtil)
      $cabeRot = ($h -le $larguraUtil)

      if ($cabeRot -and -not $cabeNorm) {
        $rot = $true
      } elseif ($cabeNorm -and $cabeRot) {
        $nNorm = [Math]::Max(1.0, [Math]::Floor(($larguraUtil + $espaco) / ($w + $espaco)))
        $nRot = [Math]::Max(1.0, [Math]::Floor(($larguraUtil + $espaco) / ($h + $espaco)))
        $rNorm = [Math]::Ceiling($qtd / $nNorm)
        $rRot = [Math]::Ceiling($qtd / $nRot)
        $totHNorm = ($rNorm * $h) + (($rNorm - 1.0) * $espaco)
        $totHRot = ($rRot * $w) + (($rRot - 1.0) * $espaco)
        if ($totHRot -lt $totHNorm) {
          $rot = $true
        }
      }
    }

    $effW = if ($rot) { $h } else { $w }
    $effH = if ($rot) { $w } else { $h }

    for ($i = 0; $i -lt $qtd; $i++) {
      $blocos += [PSCustomObject]@{
        OrigShape = $a.Shape
        Id = $a.Id
        W = $effW
        H = $effH
        Rot = $rot
      }
    }
  }

  if ($blocos.Count -eq 0) { return $null }

  # Ordena decrescente por altura para criar faixas de corte uniformes (Guillotine Shelf)
  $ordenados = $blocos | Sort-Object { $_.H } -Descending

  $prateleiras = @()
  foreach ($b in $ordenados) {
    $melhorPrat = $null
    $menorDiffH = 999999.0

    foreach ($p in $prateleiras) {
      $disp = $larguraUtil - $p.LarguraOcupada
      if ($disp -ge ($espaco + $b.W)) {
        $diffH = [Math]::Abs($p.Altura - $b.H)
        if ($diffH -lt $menorDiffH) {
          $menorDiffH = $diffH
          $melhorPrat = $p
        }
      }
    }

    if ($melhorPrat) {
      $melhorPrat.Itens.Add($b)
      $melhorPrat.LarguraOcupada += ($espaco + $b.W)
      if ($b.H -gt $melhorPrat.Altura) {
        $melhorPrat.Altura = $b.H
      }
    } else {
      $novaPrat = [PSCustomObject]@{
        Altura = $b.H
        LarguraOcupada = $b.W
        Itens = New-Object 'System.Collections.Generic.List[PSCustomObject]'
      }
      $novaPrat.Itens.Add($b)
      $prateleiras += $novaPrat
    }
  }

  $altArtesTotal = 0.0
  for ($i = 0; $i -lt $prateleiras.Count; $i++) {
    $altArtesTotal += $prateleiras[$i].Altura
    if ($i -lt ($prateleiras.Count - 1)) {
      $altArtesTotal += $espaco
    }
  }

  return @{
    Prateleiras = $prateleiras
    TotalPecas = $blocos.Count
    TotalLinhas = $prateleiras.Count
    AlturaArtesTotal = $altArtesTotal
  }
}

function AtualizarCalculo {
  if ($global:artesDetectadas.Count -eq 0) { return }

  foreach ($a in $global:artesDetectadas) {
    if ($a.Control) {
      $a.Qtd = [int]$a.Control.Value
    }
  }

  $larguraFolha = [double]$numLargura.Value
  $margem = [double]$numMargem.Value
  $espaco = [double]$numEspaco.Value
  $otimizarGiro = $chkGiro.Checked

  $res = ExecutarPacking -artes $global:artesDetectadas -larguraFolha $larguraFolha -margem $margem -espaco $espaco -otimizarGiro $otimizarGiro
  if (-not $res) { return }

  $carimboH = if ($chkCarimbo.Checked) {
    if ($rbCm.Checked) { 13.0 } else { 130.0 }
  } else { 0.0 }

  $alturaTotal = $res.AlturaArtesTotal + (2.0 * $margem) + $carimboH

  $lblStatusSelecao.Text = "Total de Desenhos no Projeto: $($res.TotalPecas) pecas em $($res.TotalLinhas) faixas de corte"
  $lblStatusSelecao.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)

  if ($otimizarGiro) {
    $lblOtimizacaoInfo.Text = "Otimizacao Ativa: Auto-Giro aplicado para minimo consumo de bobina"
    $lblOtimizacaoInfo.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
  } else {
    $lblOtimizacaoInfo.Text = "Otimizacao: Mantendo orientacao original das artes (0 graus)"
    $lblOtimizacaoInfo.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
  }

  if ($rbCm.Checked) {
    $cmTotal = [Math]::Round($alturaTotal, 1)
    $mTotal = [Math]::Round(($alturaTotal / 100.0), 2)
    $lblMetragemInfo.Text = "Metragem Estimada: $cmTotal cm ($mTotal metros)"
  } else {
    $mmTotal = [Math]::Round($alturaTotal, 0)
    $mTotal = [Math]::Round(($alturaTotal / 1000.0), 2)
    $lblMetragemInfo.Text = "Metragem Estimada: $mmTotal mm ($mTotal metros)"
  }
}

# --- CONTROLE DE ESTADO DA UNIDADE (cm / mm) ---
$global:unidadeAtual = "cm"

$rbCm.Add_CheckedChanged({
  if ($rbCm.Checked -and $global:unidadeAtual -ne "cm") {
    $global:unidadeAtual = "cm"
    $rbCm.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
    $rbMm.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)

    $lblLargura.Text = "Largura da Folha / Bobina (cm):"
    $lblEspaco.Text = "Espaco p/ Tesoura entre artes (cm):"
    $lblMargem.Text = "Margem nas bordas da folha (cm):"

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

    # Converte dimensoes internas das artes
    foreach ($a in $global:artesDetectadas) {
      $a.W = ($a.W / 10.0)
      $a.H = ($a.H / 10.0)
    }

    AtualizarBotoesPresets
    RenderizarListaArtes
    AtualizarCalculo
  }
})

$rbMm.Add_CheckedChanged({
  if ($rbMm.Checked -and $global:unidadeAtual -ne "mm") {
    $global:unidadeAtual = "mm"
    $rbMm.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
    $rbCm.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)

    $lblLargura.Text = "Largura da Folha / Bobina (mm):"
    $lblEspaco.Text = "Espaco p/ Tesoura entre artes (mm):"
    $lblMargem.Text = "Margem nas bordas da folha (mm):"

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

    # Converte dimensoes internas das artes
    foreach ($a in $global:artesDetectadas) {
      $a.W = ($a.W * 10.0)
      $a.H = ($a.H * 10.0)
    }

    AtualizarBotoesPresets
    RenderizarListaArtes
    AtualizarCalculo
  }
})

# Quando escolhe pedido no combo, atualiza quantidade global
$cboPedidos.Add_SelectedIndexChanged({
  if ($cboPedidos.SelectedIndex -gt 0) {
    $p = $pedidosCarregados[$cboPedidos.SelectedIndex - 1]
    if ($p -and $p.totalPecas) {
      $novaQtd = [int]$p.totalPecas
      $numQtdGlobal.Value = [decimal]$novaQtd
      foreach ($a in $global:artesDetectadas) {
        $a.Qtd = $novaQtd
        if ($a.Control) {
          $a.Control.Value = [decimal]$novaQtd
        }
      }
      AtualizarCalculo
    }
  }
})

# --- EVENTO DO BOTAO 1: LER SELECAO DO CORELDRAW ---
$btnDetectar.Add_Click({
  try {
    $corel = New-Object -ComObject "CorelDRAW.Application.24"
    $doc = $corel.ActiveDocument
    if (-not $doc) {
      [System.Windows.Forms.MessageBox]::Show("Abra um documento com a arte no CorelDRAW primeiro!", "CorelDRAW", "OK", "Warning")
      return
    }

    # Define unidade do CorelDRAW exatamente igual a unidade da nossa janela
    # Constantes do CorelDRAW: cdrMillimeter = 3, cdrCentimeter = 4
    if ($rbCm.Checked) {
      $doc.Unit = 4 # Centimetros (cdrCentimeter = 4)
    } else {
      $doc.Unit = 3 # Milimetros (cdrMillimeter = 3)
    }

    $sel = $corel.ActiveSelection
    if ($sel.Shapes.Count -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Selecione a(s) arte(s) no CorelDRAW antes de detectar!", "Nenhuma selecao", "OK", "Information")
      return
    }

    $global:artesDetectadas = @()
    
    # Determina a quantidade inicial: se tiver pedido selecionado, usa total de pecas do pedido
    $qtdPadrao = [int]$numQtdGlobal.Value
    if ($cboPedidos.SelectedIndex -gt 0 -and $pedidosCarregados) {
      $pSel = $pedidosCarregados[$cboPedidos.SelectedIndex - 1]
      if ($pSel -and $pSel.totalPecas -and $pSel.totalPecas -gt 0) {
        $qtdPadrao = [int]$pSel.totalPecas
        $numQtdGlobal.Value = [decimal]$qtdPadrao
      }
    }

    # Se a opcao de agrupar estiver ativa ou for 1 unico objeto
    if ($chkAgrupar.Checked -and $sel.Shapes.Count -gt 1) {
      $s = $sel.Group()
      $global:artesDetectadas += [PSCustomObject]@{
        Id = 1
        Shape = $s
        W = [double]$s.SizeWidth
        H = [double]$s.SizeHeight
        Qtd = $qtdPadrao
        Control = $null
      }
    } elseif ($sel.Shapes.Count -eq 1) {
      $s = $sel.Shapes[1]
      $global:artesDetectadas += [PSCustomObject]@{
        Id = 1
        Shape = $s
        W = [double]$s.SizeWidth
        H = [double]$s.SizeHeight
        Qtd = $qtdPadrao
        Control = $null
      }
    } else {
      # Múltiplas artes soltas (ex: 3 desenhos diferentes)
      for ($i = 1; $i -le $sel.Shapes.Count; $i++) {
        $s = $sel.Shapes[$i]
        $global:artesDetectadas += [PSCustomObject]@{
          Id = $i
          Shape = $s
          W = [double]$s.SizeWidth
          H = [double]$s.SizeHeight
          Qtd = $qtdPadrao
          Control = $null
        }
      }
    }

    RenderizarListaArtes
    AtualizarCalculo
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro ao conectar com CorelDRAW: $($_.Exception.Message)", "Erro", "OK", "Error")
  }
})

# --- EVENTO DO BOTAO 2: MONTAR FOLHA OTIMIZADA ---
$btnMontar.Add_Click({
  try {
    $corel = New-Object -ComObject "CorelDRAW.Application.24"
    $doc = $corel.ActiveDocument
    if (-not $doc) {
      [System.Windows.Forms.MessageBox]::Show("Abra o CorelDRAW com as artes abertas!", "Aviso", "OK", "Warning")
      return
    }

    # Constantes do CorelDRAW: cdrMillimeter = 3, cdrCentimeter = 4
    if ($rbCm.Checked) {
      $doc.Unit = 4 # Centimetros (cdrCentimeter = 4)
    } else {
      $doc.Unit = 3 # Milimetros (cdrMillimeter = 3)
    }

    if ($global:artesDetectadas.Count -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Por favor, clique em '1. Ler Arte(s)' primeiro para detectar as artes no Corel!", "Aviso", "OK", "Warning")
      return
    }

    # Sincroniza quantidades digitadas na tela nos campos
    foreach ($a in $global:artesDetectadas) {
      if ($a.Control) {
        $a.Qtd = [int]$a.Control.Value
      }
    }

    $larguraFolha = [double]$numLargura.Value
    $margem = [double]$numMargem.Value
    $espaco = [double]$numEspaco.Value
    $otimizarGiro = $chkGiro.Checked
    $criarLinhasCorte = $chkLinhasCorte.Checked

    $res = ExecutarPacking -artes $global:artesDetectadas -larguraFolha $larguraFolha -margem $margem -espaco $espaco -otimizarGiro $otimizarGiro
    if (-not $res -or $res.TotalPecas -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Informe ao menos 1 peca na quantidade!", "Aviso", "OK", "Warning")
      return
    }

    $prateleiras = $res.Prateleiras

    # Altura do carimbo na unidade ativa (13 cm ou 130 mm)
    $carimboH = if ($chkCarimbo.Checked) {
      if ($rbCm.Checked) { 13.0 } else { 130.0 }
    } else { 0.0 }

    $alturaTotalFolha = [double]($res.AlturaArtesTotal + (2.0 * $margem) + $carimboH)

    # Inicia grupo de comando e otimizacao para execucao ultra-rapida e 1 unico Ctrl+Z
    $doc.BeginCommandGroup("Montar Gang Sheet")
    $corel.Optimization = $true

    try {
      # Redimensiona a pagina do CorelDRAW com exatidao na unidade do documento (cm ou mm)
      $doc.ActivePage.SetSize([double]$larguraFolha, [double]$alturaTotalFolha)

      $layer = $doc.ActivePage.ActiveLayer

      # Carimbo Tecnico no Topo
      if ($chkCarimbo.Checked) {
        $pSel = if ($cboPedidos.SelectedIndex -gt 0) { $pedidosCarregados[$cboPedidos.SelectedIndex - 1] } else { $null }
        $leftC = [double]$margem
        
        $fundoW = if ($rbCm.Checked) { 26.0 } else { 260.0 }
        $fundoH = if ($rbCm.Checked) { 11.0 } else { 110.0 }
        $topoH  = if ($rbCm.Checked) { 2.4 } else { 24.0 }
        $txtH1  = if ($rbCm.Checked) { 0.85 } else { 8.5 }
        $txtH2  = if ($rbCm.Checked) { 0.55 } else { 5.5 }
        $gap1   = if ($rbCm.Checked) { 0.8 } else { 8.0 }
        $gap2   = if ($rbCm.Checked) { 1.2 } else { 12.0 }
        $gap3   = if ($rbCm.Checked) { 3.5 } else { 35.0 }

        $bottomC = [double]($alturaTotalFolha - $margem - ($fundoH + 1.0))

        $bgC = $layer.CreateRectangle2($leftC, $bottomC, $fundoW, $fundoH)
        $bgC.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
        $bgC.Outline.Color.CMYKAssign(0, 0, 0, 100)
        $bgC.Outline.Width = 0.5
        $bgC.Selected = $true

        $hBg = $layer.CreateRectangle2($leftC, ($bottomC + $fundoH - $topoH), $fundoW, $topoH)
        $hBg.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
        $hBg.Outline.Type = 0
        $hBg.Selected = $true

        $pedNum = if ($pSel) { $pSel.numeroPedido } else { "LOTE MULTI-ARTES" }
        $cliNome = if ($pSel) { $pSel.clienteNome } else { "GANG SHEET" }
        $tH = $layer.CreateArtisticText(($leftC + $gap1), ($bottomC + $fundoH - ($topoH * 0.75)), "PEDIDO #$pedNum | CLIENTE: $cliNome")
        $tH.Text.Story.Font = "Arial Black"
        $tH.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
        $tH.SetSize(0, $txtH1)
        $tH.CenterY = [double]($bottomC + $fundoH - ($topoH / 2.0))
        $tH.LeftX = [double]($leftC + $gap1)
        $tH.Selected = $true

        $descEst = if ($pSel) { $pSel.descricaoEstampa } else { "$($res.TotalPecas) Pecas" }
        $uNome = if ($rbCm.Checked) { "cm" } else { "mm" }
        $tInf = $layer.CreateArtisticText(($leftC + $gap1), ($bottomC + $fundoH - $gap3), "ESTAMPA: $descEst | BOBINA: $larguraFolha $uNome")
        $tInf.Text.Story.Font = "Arial Black"
        $tInf.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
        $tInf.SetSize(0, $txtH2)
        $tInf.LeftX = [double]($leftC + $gap1)
        $tInf.Selected = $true

        $corel.ActiveSelection.Group() | Out-Null
      }

      # Posicionamento fisico e duplicacao limpa dos blocos
      $curY = [double]($alturaTotalFolha - $margem - $carimboH)
      $formasCriadas = @()
      $linhasCorteY = @()

      foreach ($prat in $prateleiras) {
        $curX = [double]$margem
        $pratH = [double]$prat.Altura

        foreach ($it in $prat.Itens) {
          $orig = $it.OrigShape
          
          # Duplica a partir do objeto original limpo (sem nunca alterar o original)
          $novaForma = $orig.Duplicate([double]0, [double]0)
          
          # Gira 90 graus na copia se a otimizacao definiu giro
          if ($it.Rot) {
            $novaForma.Rotate([double]90.0)
          }

          # Alinha na grade com corredor de tesoura perfeito
          $targetY = [double]($curY - $it.H)
          $novaForma.LeftX = [double]$curX
          $novaForma.BottomY = [double]$targetY

          $formasCriadas += $novaForma
          $curX += ($it.W + $espaco)
        }

        # Ponto médio do vão entre prateleiras para a linha de corte de tesoura
        $linhasCorteY += ($curY - $pratH - ($espaco / 2.0))
        $curY -= ($pratH + $espaco)
      }

      # Cria Linhas-Guia Discretas para Corte com Tesoura
      if ($criarLinhasCorte -and $linhasCorteY.Count -gt 1) {
        $tamLinha = if ($rbCm.Checked) { 0.02 } else { 0.2 }
        for ($lIdx = 0; $lIdx -lt ($linhasCorteY.Count - 1); $lIdx++) {
          $corteY = [double]$linhasCorteY[$lIdx]
          $lineH = $layer.CreateLineSegment([double]$margem, $corteY, [double]($larguraFolha - $margem), $corteY)
          $lineH.Outline.Width = $tamLinha
          $lineH.Outline.Color.CMYKAssign(0, 0, 0, 30) # Cinza suave
          $formasCriadas += $lineH
        }
      }

      # Remove as formas originais para que fiquem apenas as copias montadas na folha
      foreach ($a in $global:artesDetectadas) {
        if ($a.Shape) {
          try { $a.Shape.Delete() } catch {}
        }
      }

      # Agrupa todo o lote montado para facilitar mover se quiser
      $doc.ClearSelection()
      foreach ($f in $formasCriadas) {
        $f.Selected = $true
      }
      $corel.ActiveSelection.Group() | Out-Null

      $uExt = if ($rbCm.Checked) { "cm" } else { "mm" }
      $mFim = if ($rbCm.Checked) { [Math]::Round(($alturaTotalFolha / 100.0), 2) } else { [Math]::Round(($alturaTotalFolha / 1000.0), 2) }
      
      [System.Windows.Forms.MessageBox]::Show("Folha montada e otimizada com sucesso no CorelDRAW!`n`n- Total de Estampas: $($res.TotalPecas) pecas`n- Faixas de Corte: $($prateleiras.Count) linhas retas`n- Largura da Folha: $larguraFolha $uExt`n- Metragem Total da Bobina: $alturaTotalFolha $uExt ($mFim metros)`n- Corredores de tesoura aplicados com precisao!`n`nDica: Caso queira desfazer a montagem, basta teclar Ctrl+Z no CorelDRAW.", "Sucesso!", "OK", "Information")
    } finally {
      $corel.Optimization = $false
      $doc.EndCommandGroup()
      $corel.Refresh()
    }
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro ao montar folha otimizada: $($_.Exception.Message)", "Erro", "OK", "Error")
  }
})

# Atualizacao dinamica
$numLargura.Add_ValueChanged({ AtualizarCalculo })
$numEspaco.Add_ValueChanged({ AtualizarCalculo })
$numMargem.Add_ValueChanged({ AtualizarCalculo })
$chkGiro.Add_CheckedChanged({ AtualizarCalculo })
$chkCarimbo.Add_CheckedChanged({ AtualizarCalculo })
$chkLinhasCorte.Add_CheckedChanged({ AtualizarCalculo })

# Atalho ESC para fechar
$form.KeyPreview = $true
$form.Add_KeyDown({
  if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Escape) {
    $form.Close()
  }
})

$form.ShowDialog() | Out-Null
