Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# =========================================================================
# Order Separator - Montador de Folha Inteligente (Gang Sheet / Imposicao)
# Suporte a Multi-Artes, Otimizacao de Bobina e Corredores de Corte p/ Tesoura
# =========================================================================

$form = New-Object System.Windows.Forms.Form
$form.Text = "Order Separator - Montador de Folha Otimizado"
$form.Size = New-Object System.Drawing.Size(510, 760)
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
$lblHeader.Location = New-Object System.Drawing.Point(20, 12)
$lblHeader.Size = New-Object System.Drawing.Size(450, 24)
$form.Controls.Add($lblHeader)

$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Encaixe inteligente com economia de bobina e espaco para tesoura"
$lblSub.Font = $fontStats
$lblSub.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblSub.Location = New-Object System.Drawing.Point(20, 36)
$lblSub.Size = New-Object System.Drawing.Size(450, 18)
$form.Controls.Add($lblSub)

# --- PEDIDOS CADASTRADOS ---
$lblPedido = New-Object System.Windows.Forms.Label
$lblPedido.Text = "Puxar Pedido Cadastrado (Opcional):"
$lblPedido.Font = $fontLabel
$lblPedido.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblPedido.Location = New-Object System.Drawing.Point(20, 58)
$lblPedido.Size = New-Object System.Drawing.Size(450, 16)
$form.Controls.Add($lblPedido)

$cboPedidos = New-Object System.Windows.Forms.ComboBox
$cboPedidos.Location = New-Object System.Drawing.Point(20, 76)
$cboPedidos.Size = New-Object System.Drawing.Size(455, 25)
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
$pnlUnidade.Location = New-Object System.Drawing.Point(20, 108)
$pnlUnidade.Size = New-Object System.Drawing.Size(455, 26)
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
$rbCm.Size = New-Object System.Drawing.Size(140, 22)
$rbCm.Checked = $true
$rbCm.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlUnidade.Controls.Add($rbCm)

$rbMm = New-Object System.Windows.Forms.RadioButton
$rbMm.Text = "Milimetros (mm)"
$rbMm.Font = $fontLabel
$rbMm.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$rbMm.Location = New-Object System.Drawing.Point(300, 2)
$rbMm.Size = New-Object System.Drawing.Size(140, 22)
$rbMm.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlUnidade.Controls.Add($rbMm)

# --- CONFIGURACOES DA FOLHA ---
$lblLargura = New-Object System.Windows.Forms.Label
$lblLargura.Text = "Largura da Folha / Bobina (cm):"
$lblLargura.Font = $fontLabel
$lblLargura.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblLargura.Location = New-Object System.Drawing.Point(20, 138)
$lblLargura.Size = New-Object System.Drawing.Size(220, 16)
$form.Controls.Add($lblLargura)

$numLargura = New-Object System.Windows.Forms.NumericUpDown
$numLargura.Location = New-Object System.Drawing.Point(20, 156)
$numLargura.Size = New-Object System.Drawing.Size(215, 26)
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
$lblEspaco.Location = New-Object System.Drawing.Point(260, 138)
$lblEspaco.Size = New-Object System.Drawing.Size(215, 16)
$form.Controls.Add($lblEspaco)

$numEspaco = New-Object System.Windows.Forms.NumericUpDown
$numEspaco.Location = New-Object System.Drawing.Point(260, 156)
$numEspaco.Size = New-Object System.Drawing.Size(215, 26)
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
$pnlPresets.Location = New-Object System.Drawing.Point(20, 188)
$pnlPresets.Size = New-Object System.Drawing.Size(455, 28)
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
    $btn.Size = New-Object System.Drawing.Size(108, 25)
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

# Margem das Bordas
$lblMargem = New-Object System.Windows.Forms.Label
$lblMargem.Text = "Margem nas bordas da folha (cm):"
$lblMargem.Font = $fontLabel
$lblMargem.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblMargem.Location = New-Object System.Drawing.Point(20, 222)
$lblMargem.Size = New-Object System.Drawing.Size(220, 16)
$form.Controls.Add($lblMargem)

$numMargem = New-Object System.Windows.Forms.NumericUpDown
$numMargem.Location = New-Object System.Drawing.Point(20, 240)
$numMargem.Size = New-Object System.Drawing.Size(215, 26)
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
$chkGiro.Location = New-Object System.Drawing.Point(260, 225)
$chkGiro.Size = New-Object System.Drawing.Size(220, 22)
$chkGiro.Checked = $true
$chkGiro.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($chkGiro)

$chkLinhasCorte = New-Object System.Windows.Forms.CheckBox
$chkLinhasCorte.Text = "Tracar linhas-guia para corte reto com tesoura"
$chkLinhasCorte.Font = $fontLabel
$chkLinhasCorte.ForeColor = [System.Drawing.Color]::FromArgb(147, 197, 253) # Light Blue
$chkLinhasCorte.Location = New-Object System.Drawing.Point(260, 246)
$chkLinhasCorte.Size = New-Object System.Drawing.Size(220, 22)
$chkLinhasCorte.Checked = $true
$chkLinhasCorte.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($chkLinhasCorte)

$chkCarimbo = New-Object System.Windows.Forms.CheckBox
$chkCarimbo.Text = "Carimbar Ficha Tecnica com Grade no Topo"
$chkCarimbo.Font = $fontLabel
$chkCarimbo.ForeColor = [System.Drawing.Color]::FromArgb(167, 139, 250)
$chkCarimbo.Location = New-Object System.Drawing.Point(20, 272)
$chkCarimbo.Size = New-Object System.Drawing.Size(450, 20)
$chkCarimbo.Checked = $true
$chkCarimbo.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($chkCarimbo)

# --- BOTAO 1: LER SELECAO DO CORELDRAW ---
$btnDetectar = New-Object System.Windows.Forms.Button
$btnDetectar.Text = "1. Ler Arte(s) Selecionada(s) no CorelDRAW"
$btnDetectar.Font = $fontBtn
$btnDetectar.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$btnDetectar.ForeColor = [System.Drawing.Color]::White
$btnDetectar.Location = New-Object System.Drawing.Point(20, 298)
$btnDetectar.Size = New-Object System.Drawing.Size(455, 36)
$btnDetectar.FlatStyle = "Flat"
$btnDetectar.FlatAppearance.BorderSize = 0
$btnDetectar.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($btnDetectar)

# --- LISTA / GRID DE ARTES DETECTADAS ---
$pnlArtes = New-Object System.Windows.Forms.Panel
$pnlArtes.Location = New-Object System.Drawing.Point(20, 340)
$pnlArtes.Size = New-Object System.Drawing.Size(455, 140)
$pnlArtes.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlArtes.BorderStyle = "FixedSingle"
$pnlArtes.AutoScroll = $true
$form.Controls.Add($pnlArtes)

# Painel de Resumo / Estimativa de Economia
$pnlResumo = New-Object System.Windows.Forms.Panel
$pnlResumo.Location = New-Object System.Drawing.Point(20, 488)
$pnlResumo.Size = New-Object System.Drawing.Size(455, 105)
$pnlResumo.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlResumo.BorderStyle = "FixedSingle"
$form.Controls.Add($pnlResumo)

$lblStatusSelecao = New-Object System.Windows.Forms.Label
$lblStatusSelecao.Text = "Nenhuma arte lida ainda. Selecione 1 ou mais desenhos no Corel."
$lblStatusSelecao.Font = $fontStats
$lblStatusSelecao.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblStatusSelecao.Location = New-Object System.Drawing.Point(12, 8)
$lblStatusSelecao.Size = New-Object System.Drawing.Size(430, 18)
$pnlResumo.Controls.Add($lblStatusSelecao)

$lblOtimizacaoInfo = New-Object System.Windows.Forms.Label
$lblOtimizacaoInfo.Text = "Otimizacao: --"
$lblOtimizacaoInfo.Font = $fontLabel
$lblOtimizacaoInfo.ForeColor = [System.Drawing.Color]::White
$lblOtimizacaoInfo.Location = New-Object System.Drawing.Point(12, 30)
$lblOtimizacaoInfo.Size = New-Object System.Drawing.Size(430, 18)
$pnlResumo.Controls.Add($lblOtimizacaoInfo)

$lblCorredoresInfo = New-Object System.Windows.Forms.Label
$lblCorredoresInfo.Text = "Corte com Tesoura: Alinhamento retangular continuo"
$lblCorredoresInfo.Font = $fontSmall
$lblCorredoresInfo.ForeColor = [System.Drawing.Color]::FromArgb(147, 197, 253)
$lblCorredoresInfo.Location = New-Object System.Drawing.Point(12, 52)
$lblCorredoresInfo.Size = New-Object System.Drawing.Size(430, 18)
$pnlResumo.Controls.Add($lblCorredoresInfo)

$lblMetragemInfo = New-Object System.Windows.Forms.Label
$lblMetragemInfo.Text = "Metragem Estimada da Bobina: --"
$lblMetragemInfo.Font = $fontTitle
$lblMetragemInfo.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153) # Emerald
$lblMetragemInfo.Location = New-Object System.Drawing.Point(12, 73)
$lblMetragemInfo.Size = New-Object System.Drawing.Size(430, 24)
$pnlResumo.Controls.Add($lblMetragemInfo)

# --- BOTAO 2: MONTAR FOLHA ---
$btnMontar = New-Object System.Windows.Forms.Button
$btnMontar.Text = "2. MONTAR FOLHA OTIMIZADA (GANG SHEET)"
$btnMontar.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$btnMontar.BackColor = [System.Drawing.Color]::FromArgb(79, 70, 229) # Indigo 600
$btnMontar.ForeColor = [System.Drawing.Color]::White
$btnMontar.Location = New-Object System.Drawing.Point(20, 602)
$btnMontar.Size = New-Object System.Drawing.Size(455, 48)
$btnMontar.FlatStyle = "Flat"
$btnMontar.FlatAppearance.BorderSize = 0
$btnMontar.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($btnMontar)

# --- ESTRUTURA DE DADOS DAS ARTES DETECTADAS ---
$global:artesDetectadas = @()

function ObterValoresMm {
  $fator = if ($rbCm.Checked) { 10.0 } else { 1.0 }
  return @{
    Largura = ([double]$numLargura.Value * $fator)
    Espaco  = ([double]$numEspaco.Value * $fator)
    Margem  = ([double]$numMargem.Value * $fator)
  }
}

# Atualiza a exibicao da lista de artes na interface
function RenderizarListaArtes {
  $pnlArtes.Controls.Clear()

  if ($global:artesDetectadas.Count -eq 0) {
    $lblVazio = New-Object System.Windows.Forms.Label
    $lblVazio.Text = "Nenhuma arte carregada. Selecione os desenhos no Corel e clique acima."
    $lblVazio.ForeColor = [System.Drawing.Color]::FromArgb(100, 116, 139)
    $lblVazio.Font = $fontStats
    $lblVazio.Location = New-Object System.Drawing.Point(15, 55)
    $lblVazio.Size = New-Object System.Drawing.Size(420, 30)
    $pnlArtes.Controls.Add($lblVazio)
    return
  }

  $yPos = 8
  for ($idx = 0; $idx -lt $global:artesDetectadas.Count; $idx++) {
    $item = $global:artesDetectadas[$idx]
    
    # Caixa de cada item
    $pnlItem = New-Object System.Windows.Forms.Panel
    $pnlItem.Location = New-Object System.Drawing.Point(10, $yPos)
    $pnlItem.Size = New-Object System.Drawing.Size(415, 38)
    $pnlItem.BackColor = [System.Drawing.Color]::FromArgb(24, 33, 56)
    $pnlItem.BorderStyle = "None"
    $pnlArtes.Controls.Add($pnlItem)

    $wTxt = if ($rbCm.Checked) { "$([Math]::Round($item.W / 10, 1)) cm" } else { "$([Math]::Round($item.W, 0)) mm" }
    $hTxt = if ($rbCm.Checked) { "$([Math]::Round($item.H / 10, 1)) cm" } else { "$([Math]::Round($item.H, 0)) mm" }

    $lblNome = New-Object System.Windows.Forms.Label
    $lblNome.Text = "Desenho #$($idx + 1) ($wTxt x $hTxt)"
    $lblNome.ForeColor = [System.Drawing.Color]::White
    $lblNome.Font = $fontLabel
    $lblNome.Location = New-Object System.Drawing.Point(8, 10)
    $lblNome.Size = New-Object System.Drawing.Size(220, 20)
    $pnlItem.Controls.Add($lblNome)

    $lblQtdItem = New-Object System.Windows.Forms.Label
    $lblQtdItem.Text = "Qtd:"
    $lblQtdItem.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
    $lblQtdItem.Font = $fontLabel
    $lblQtdItem.Location = New-Object System.Drawing.Point(235, 10)
    $lblQtdItem.Size = New-Object System.Drawing.Size(35, 20)
    $pnlItem.Controls.Add($lblQtdItem)

    $numQtdItem = New-Object System.Windows.Forms.NumericUpDown
    $numQtdItem.Location = New-Object System.Drawing.Point(275, 7)
    $numQtdItem.Size = New-Object System.Drawing.Size(70, 24)
    $numQtdItem.Minimum = 1
    $numQtdItem.Maximum = 10000
    $numQtdItem.Value = [decimal]$item.Qtd
    $numQtdItem.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
    $numQtdItem.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
    $numQtdItem.Font = $fontInput
    $itemRef = $item
    $numQtdItem.Add_ValueChanged({
      $itemRef.Qtd = [int]$numQtdItem.Value
      AtualizarCalculo
    })
    $pnlItem.Controls.Add($numQtdItem)

    $yPos += 44
  }
}

function AtualizarCalculo {
  if ($global:artesDetectadas.Count -eq 0) { return }

  $vals = ObterValoresMm
  $larguraFolhaMm = $vals.Largura
  $margemMm = $vals.Margem
  $espacoMm = $vals.Espaco
  $larguraUtilMm = $larguraFolhaMm - (2 * $margemMm)
  $otimizarGiro = $chkGiro.Checked

  # Coleta todos os blocos individuais a serem posicionados
  $blocos = @()
  $totalPecas = 0
  foreach ($arte in $global:artesDetectadas) {
    for ($k = 0; $k -lt $arte.Qtd; $k++) {
      $blocos += [PSCustomObject]@{
        IdOrig = $arte.Id
        Shape = $arte.Shape
        W = $arte.W
        H = $arte.H
      }
      $totalPecas++
    }
  }

  if ($blocos.Count -eq 0) { return }

  # Teste de Melhor Encaixe com Giro
  # Algoritmo de Prateleiras (Guillotine Shelf Packing)
  function SimularEncaixe($listaBlocos, $permitirGiro) {
    # Ordena por maior dimensao decrescente para preencher com solidez
    $ordenados = $listaBlocos | Sort-Object { [Math]::Max($_.W, $_.H) } -Descending

    $prateleiras = @()
    $curShelfW = 0.0
    $curShelfH = 0.0

    foreach ($b in $ordenados) {
      $w = $b.W
      $h = $b.H

      # Decide melhor orientacao
      if ($permitirGiro) {
        $cabeNormal = ($curShelfW + $w) -le $larguraUtilMm
        $cabeGirado = ($curShelfW + $h) -le $larguraUtilMm

        if ($cabeNormal -and -not $cabeGirado) {
          # Mantem normal
        } elseif (-not $cabeNormal -and $cabeGirado) {
          # Gira 90
          $w = $b.H
          $h = $b.W
        } elseif ($cabeNormal -and $cabeGirado) {
          # Se ambos cabem, escolhe o que gera menor altura da prateleira ou deixa mais espaco
          if ($h -lt $w) {
            # Se for mais largo do que alto, deixar deitado pode economizar altura
          } else {
            # Testa se virando fica mais baixo
            if ($w -lt $h -and ($curShelfW + $h) -le $larguraUtilMm) {
              $w = $b.H
              $h = $b.W
            }
          }
        } else {
          # Nao cabe na prateleira atual, testa para nova prateleira qual orientacao e mais baixa
          if ($w -le $larguraUtilMm -and $h -le $larguraUtilMm) {
            if ($w -lt $h) {
              # Virado fica com menor altura
              $w = $b.H
              $h = $b.W
            }
          } elseif ($h -le $larguraUtilMm) {
            $w = $b.H
            $h = $b.W
          }
        }
      }

      # Se ainda cabe na prateleira atual
      if ($curShelfW -eq 0.0) {
        $curShelfW = $w
        $curShelfH = $h
      } elseif (($curShelfW + $espacoMm + $w) -le $larguraUtilMm) {
        $curShelfW += ($espacoMm + $w)
        if ($h -gt $curShelfH) { $curShelfH = $h }
      } else {
        # Fecha prateleira anterior
        $prateleiras += $curShelfH
        $curShelfW = $w
        $curShelfH = $h
      }
    }

    if ($curShelfH -gt 0) {
      $prateleiras += $curShelfH
    }

    $alturaArtes = ($prateleiras | Measure-Object -Sum).Sum + ([Math]::Max(0, ($prateleiras.Count - 1)) * $espacoMm)
    return @{ Altura = $alturaArtes; Prateleiras = $prateleiras.Count }
  }

  $resSimulacao = SimularEncaixe $blocos $otimizarGiro
  $alturaArtesMm = $resSimulacao.Altura
  $totalLinhas = $resSimulacao.Prateleiras

  $carimboH = if ($chkCarimbo.Checked) { 130.0 } else { 0.0 }
  $alturaTotalMm = $alturaArtesMm + (2 * $margemMm) + $carimboH

  $cmTotal = [Math]::Round($alturaTotalMm / 10, 1)
  $mTotal = [Math]::Round($alturaTotalMm / 1000, 2)

  $lblStatusSelecao.Text = "Total de Desenhos no Projeto: $totalPecas pecas em $totalLinhas faixas de corte"
  $lblStatusSelecao.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)

  if ($otimizarGiro) {
    $lblOtimizacaoInfo.Text = "Otimizacao Ativa: Auto-Giro aplicado para minimo consumo de bobina"
    $lblOtimizacaoInfo.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
  } else {
    $lblOtimizacaoInfo.Text = "Otimizacao: Mantendo orientacao original das artes (0 graus)"
    $lblOtimizacaoInfo.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
  }

  $lblMetragemInfo.Text = "Metragem Estimada: $cmTotal cm ($mTotal metros)"
}

# --- EVENTOS DE TROCA DE UNIDADE (cm / mm) ---
$rbCm.Add_CheckedChanged({
  if ($rbCm.Checked) {
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

    AtualizarBotoesPresets
    RenderizarListaArtes
    AtualizarCalculo
  }
})

$rbMm.Add_CheckedChanged({
  if ($rbMm.Checked) {
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

    AtualizarBotoesPresets
    RenderizarListaArtes
    AtualizarCalculo
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
    $doc.Unit = 4 # mm
    $sel = $corel.ActiveSelection
    if ($sel.Shapes.Count -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Selecione a(s) arte(s) no CorelDRAW antes de detectar!", "Nenhuma selecao", "OK", "Information")
      return
    }

    $global:artesDetectadas = @()

    # Se tiver apenas 1 objeto selecionado
    if ($sel.Shapes.Count -eq 1) {
      $s = $sel.Shapes[1]
      $qtdInicial = if ($cboPedidos.SelectedIndex -gt 0) {
        $p = $pedidosCarregados[$cboPedidos.SelectedIndex - 1]
        [Math]::Max(1, [int]$p.totalPecas)
      } else { 24 }

      $global:artesDetectadas += [PSCustomObject]@{
        Id = 1
        Shape = $s
        W = [double]$s.SizeWidth
        H = [double]$s.SizeHeight
        Qtd = $qtdInicial
      }
    } else {
      # Multi-Artes selecionadas (ex: 3 desenhos diferentes)
      for ($i = 1; $i -le $sel.Shapes.Count; $i++) {
        $s = $sel.Shapes[$i]
        $global:artesDetectadas += [PSCustomObject]@{
          Id = $i
          Shape = $s
          W = [double]$s.SizeWidth
          H = [double]$s.SizeHeight
          Qtd = 1
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
    $doc.Unit = 4 # Milimetros para operacoes internas
    if ($global:artesDetectadas.Count -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Por favor, clique em '1. Ler Arte(s)' primeiro para detectar as artes no Corel!", "Aviso", "OK", "Warning")
      return
    }

    $vals = ObterValoresMm
    $larguraFolha = [double]$vals.Largura
    $margem = [double]$vals.Margem
    $espaco = [double]$vals.Espaco
    $larguraUtil = $larguraFolha - (2 * $margem)
    $otimizarGiro = $chkGiro.Checked
    $criarLinhasCorte = $chkLinhasCorte.Checked

    # Prepara a lista expandida de blocos
    $blocosParaPosicionar = @()
    foreach ($a in $global:artesDetectadas) {
      for ($c = 0; $c -lt $a.Qtd; $c++) {
        $blocosParaPosicionar += [PSCustomObject]@{
          OrigShape = $a.Shape
          IsFirst = ($c -eq 0)
          W = [double]$a.W
          H = [double]$a.H
          Rotated = $false
        }
      }
    }

    if ($blocosParaPosicionar.Count -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Informe ao menos 1 peca na quantidade!", "Aviso", "OK", "Warning")
      return
    }

    # Ordena decrescente por altura para estruturar prateleiras perfeitas (BFDH)
    $blocosOrdenados = $blocosParaPosicionar | Sort-Object { [Math]::Max($_.W, $_.H) } -Descending

    # Agrupa em prateleiras (linhas guilhotinadas)
    $prateleiras = @()
    $curPratItens = @()
    $curPratW = 0.0
    $curPratH = 0.0

    foreach ($b in $blocosOrdenados) {
      $w = $b.W
      $h = $b.H
      $rot = $false

      if ($otimizarGiro) {
        $cabeNormal = ($curPratW + $w) -le $larguraUtil
        $cabeGirado = ($curPratW + $h) -le $larguraUtil

        if ($cabeNormal -and -not $cabeGirado) {
          # Normal
        } elseif (-not $cabeNormal -and $cabeGirado) {
          $w = $b.H
          $h = $b.W
          $rot = $true
        } elseif ($cabeNormal -and $cabeGirado) {
          if ($b.H -lt $b.W -and ($curPratW + $b.W) -le $larguraUtil) {
            # Se já é horizontal, mantém
          } else {
            # Testa se girado fica mais baixo economizando altura
            if ($b.W -lt $b.H -and ($curPratW + $b.H) -le $larguraUtil) {
              $w = $b.H
              $h = $b.W
              $rot = $true
            }
          }
        } else {
          # Prateleira nova: escolhe orientacao mais baixa se couber na folha
          if ($b.H -le $larguraUtil -and ($b.W -gt $b.H -or $b.W -gt $larguraUtil)) {
            $w = $b.H
            $h = $b.W
            $rot = $true
          }
        }
      }

      $itemPos = [PSCustomObject]@{
        Bloco = $b
        W = $w
        H = $h
        Rot = $rot
      }

      if ($curPratW -eq 0.0) {
        $curPratItens += $itemPos
        $curPratW = $w
        $curPratH = $h
      } elseif (($curPratW + $espaco + $w) -le $larguraUtil) {
        $curPratItens += $itemPos
        $curPratW += ($espaco + $w)
        if ($h -gt $curPratH) { $curPratH = $h }
      } else {
        # Fecha prateleira
        $prateleiras += [PSCustomObject]@{
          Itens = $curPratItens
          Altura = $curPratH
        }
        $curPratItens = @($itemPos)
        $curPratW = $w
        $curPratH = $h
      }
    }

    if ($curPratItens.Count -gt 0) {
      $prateleiras += [PSCustomObject]@{
        Itens = $curPratItens
        Altura = $curPratH
      }
    }

    # Calcula altura total das prateleiras
    $alturaArtesTotal = 0.0
    for ($pIdx = 0; $pIdx -lt $prateleiras.Count; $pIdx++) {
      $alturaArtesTotal += $prateleiras[$pIdx].Altura
      if ($pIdx -lt ($prateleiras.Count - 1)) {
        $alturaArtesTotal += $espaco
      }
    }

    $carimboH = if ($chkCarimbo.Checked) { 130.0 } else { 0.0 }
    $alturaTotalFolha = [double]($alturaArtesTotal + (2 * $margem) + $carimboH)

    # Redimensiona a pagina do CorelDRAW
    $doc.ActivePage.SetSize([double]$larguraFolha, [double]$alturaTotalFolha)

    $layer = $doc.ActivePage.ActiveLayer

    # Carimbo Tecnico no Topo
    if ($chkCarimbo.Checked) {
      $pSel = if ($cboPedidos.SelectedIndex -gt 0) { $pedidosCarregados[$cboPedidos.SelectedIndex - 1] } else { $null }
      $leftC = [double]$margem
      $bottomC = [double]($alturaTotalFolha - $margem - 120.0)

      $bgC = $layer.CreateRectangle2($leftC, $bottomC, 260.0, 110.0)
      $bgC.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
      $bgC.Outline.Color.CMYKAssign(0, 0, 0, 100)
      $bgC.Outline.Width = 0.5
      $bgC.Selected = $true

      $hBg = $layer.CreateRectangle2($leftC, ($bottomC + 110.0 - 24.0), 260.0, 24.0)
      $hBg.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
      $hBg.Outline.Type = 0
      $hBg.Selected = $true

      $pedNum = if ($pSel) { $pSel.numeroPedido } else { "LOTE MULTI-ARTES" }
      $cliNome = if ($pSel) { $pSel.clienteNome } else { "GANG SHEET" }
      $tH = $layer.CreateArtisticText(($leftC + 8.0), ($bottomC + 110.0 - 18.0), "PEDIDO #$pedNum | CLIENTE: $cliNome")
      $tH.Text.Story.Font = "Arial Black"
      $tH.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
      $tH.SetSize(0, 8.5)
      $tH.CenterY = [double]($bottomC + 110.0 - 12.0)
      $tH.LeftX = [double]($leftC + 8.0)
      $tH.Selected = $true

      $descEst = if ($pSel) { $pSel.descricaoEstampa } else { "$($blocosParaPosicionar.Count) Pecas Otimizadas" }
      $tInf = $layer.CreateArtisticText(($leftC + 8.0), ($bottomC + 110.0 - 35.0), "ESTAMPA: $descEst | BOBINA: $([Math]::Round($larguraFolha/10,1))cm")
      $tInf.Text.Story.Font = "Arial Black"
      $tInf.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
      $tInf.SetSize(0, 5.5)
      $tInf.LeftX = [double]($leftC + 8.0)
      $tInf.Selected = $true

      $corel.ActiveSelection.Group() | Out-Null
    }

    # Posicionamento fisico e duplicacao dos blocos
    $curY = [double]($alturaTotalFolha - $margem - $carimboH)
    $formasCriadas = @()
    $linhasCorteY = @()

    foreach ($prat in $prateleiras) {
      $curX = [double]$margem
      $pratH = $prat.Altura

      foreach ($it in $prat.Itens) {
        $orig = $it.Bloco.OrigShape
        
        # Duplica
        $novaForma = $orig.Duplicate([double]0, [double]0)
        
        # Gira 90 graus se necessario
        if ($it.Rot) {
          $novaForma.Rotate([double]90.0)
        }

        # Alinha na grade com espaco uniforme de tesoura
        $targetY = [double]($curY - $it.H)
        $novaForma.LeftX = [double]$curX
        $novaForma.BottomY = [double]$targetY

        $formasCriadas += $novaForma
        $curX += ($it.W + $espaco)
      }

      # Registra a linha divisoria horizontal para tesoura
      $linhasCorteY += ($curY - $pratH - ($espaco / 2.0))
      $curY -= ($pratH + $espaco)
    }

    # Cria Linhas-Guia de Corte para Tesoura (Corte Reto Continuo)
    if ($criarLinhasCorte -and $linhasCorteY.Count -gt 1) {
      for ($lIdx = 0; $lIdx -lt ($linhasCorteY.Count - 1); $lIdx++) {
        $corteY = [double]$linhasCorteY[$lIdx]
        $lineH = $layer.CreateLineSegment([double]$margem, $corteY, [double]($larguraFolha - $margem), $corteY)
        $lineH.Outline.Width = 0.15 # Linha fina guia
        $lineH.Outline.Color.CMYKAssign(0, 0, 0, 35) # Cinza suave
        $formasCriadas += $lineH
      }
    }

    # Agrupa todo o lote montado para facil manipulacao
    $doc.ClearSelection()
    foreach ($f in $formasCriadas) {
      $f.Selected = $true
    }
    $corel.ActiveSelection.Group() | Out-Null

    $cmFim = [Math]::Round($alturaTotalFolha / 10, 1)
    $mFim = [Math]::Round($alturaTotalFolha / 1000, 2)
    [System.Windows.Forms.MessageBox]::Show("Folha montada e otimizada com sucesso no CorelDRAW!`n`n- Total de Estampas: $($blocosParaPosicionar.Count)`n- Faixas de Corte: $($prateleiras.Count) linhas`n- Metragem Total: $cmFim cm ($mFim metros)`n- Corredores de tesoura configurados com precisao!", "Sucesso!", "OK", "Information")
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro ao montar folha otimizada: $($_.Exception.Message)", "Erro", "OK", "Error")
  }
})

# Atualizacao dinamica de calculos ao alterar parametros
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
