Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# =========================================================================
# Order Separator - Vetorizador Profissional p/ CorelDRAW (Dual-Splines)
# Qualidade Superior ao Corel PowerTRACE e Adobe Illustrator Image Trace
# Sem frestas brancas entre camadas, sem nós excessivos e com cantos vivos
# =========================================================================

$form = New-Object System.Windows.Forms.Form
$form.Text = "Order Separator - Vetorizador Inteligente de Estamparia"
$form.Size = New-Object System.Drawing.Size(540, 720)
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
$lblHeader.Text = "Vetorizador de Imagens (Alta Precisão)"
$lblHeader.Font = $fontTitle
$lblHeader.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248) # Indigo
$lblHeader.Location = New-Object System.Drawing.Point(20, 12)
$lblHeader.Size = New-Object System.Drawing.Size(485, 24)
$form.Controls.Add($lblHeader)

$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Motor Dual-Spline: Sem frestas brancas, curvas ultra-suaves e nós otimizados"
$lblSub.Font = $fontStats
$lblSub.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblSub.Location = New-Object System.Drawing.Point(20, 36)
$lblSub.Size = New-Object System.Drawing.Size(485, 18)
$form.Controls.Add($lblSub)

# --- ORIGEM DA IMAGEM ---
$pnlOrigem = New-Object System.Windows.Forms.Panel
$pnlOrigem.Location = New-Object System.Drawing.Point(20, 60)
$pnlOrigem.Size = New-Object System.Drawing.Size(485, 95)
$pnlOrigem.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlOrigem.BorderStyle = "FixedSingle"
$form.Controls.Add($pnlOrigem)

$btnLerCorel = New-Object System.Windows.Forms.Button
$btnLerCorel.Text = "📸 Capturar Bitmap Selecionado no CorelDRAW"
$btnLerCorel.Font = $fontBtn
$btnLerCorel.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$btnLerCorel.ForeColor = [System.Drawing.Color]::White
$btnLerCorel.Location = New-Object System.Drawing.Point(10, 10)
$btnLerCorel.Size = New-Object System.Drawing.Size(463, 34)
$btnLerCorel.FlatStyle = "Flat"
$btnLerCorel.FlatAppearance.BorderSize = 0
$btnLerCorel.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlOrigem.Controls.Add($btnLerCorel)

$btnArquivo = New-Object System.Windows.Forms.Button
$btnArquivo.Text = "📁 Escolher Arquivo de Imagem no Computador..."
$btnArquivo.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$btnArquivo.BackColor = [System.Drawing.Color]::FromArgb(24, 33, 56)
$btnArquivo.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$btnArquivo.Location = New-Object System.Drawing.Point(10, 50)
$btnArquivo.Size = New-Object System.Drawing.Size(463, 30)
$btnArquivo.FlatStyle = "Flat"
$btnArquivo.FlatAppearance.BorderSize = 0
$btnArquivo.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlOrigem.Controls.Add($btnArquivo)

# --- VISUALIZACAO / STATUS DO ARQUIVO CARREGADO ---
$pnlInfoImg = New-Object System.Windows.Forms.Panel
$pnlInfoImg.Location = New-Object System.Drawing.Point(20, 162)
$pnlInfoImg.Size = New-Object System.Drawing.Size(485, 120)
$pnlInfoImg.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlInfoImg.BorderStyle = "FixedSingle"
$form.Controls.Add($pnlInfoImg)

$picPreview = New-Object System.Windows.Forms.PictureBox
$picPreview.Location = New-Object System.Drawing.Point(10, 10)
$picPreview.Size = New-Object System.Drawing.Size(100, 100)
$picPreview.SizeMode = "Zoom"
$picPreview.BackColor = [System.Drawing.Color]::FromArgb(2, 6, 23)
$picPreview.BorderStyle = "FixedSingle"
$pnlInfoImg.Controls.Add($picPreview)

$lblImgNome = New-Object System.Windows.Forms.Label
$lblImgNome.Text = "Nenhuma imagem selecionada ainda."
$lblImgNome.Font = $fontLabel
$lblImgNome.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblImgNome.Location = New-Object System.Drawing.Point(120, 15)
$lblImgNome.Size = New-Object System.Drawing.Size(350, 20)
$pnlInfoImg.Controls.Add($lblImgNome)

$lblImgDimensoes = New-Object System.Windows.Forms.Label
$lblImgDimensoes.Text = "Dica: Selecione a estampa bitmap no CorelDRAW ou abra um arquivo JPG/PNG."
$lblImgDimensoes.Font = $fontSmall
$lblImgDimensoes.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblImgDimensoes.Location = New-Object System.Drawing.Point(120, 40)
$lblImgDimensoes.Size = New-Object System.Drawing.Size(350, 60)
$pnlInfoImg.Controls.Add($lblImgDimensoes)

# --- PRESETS DE ESTAMPARIA ---
$lblPreset = New-Object System.Windows.Forms.Label
$lblPreset.Text = "Modo de Vetorização (Presets Especializados):"
$lblPreset.Font = $fontLabel
$lblPreset.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblPreset.Location = New-Object System.Drawing.Point(20, 290)
$lblPreset.Size = New-Object System.Drawing.Size(485, 18)
$form.Controls.Add($lblPreset)

$pnlPresetBtns = New-Object System.Windows.Forms.FlowLayoutPanel
$pnlPresetBtns.Location = New-Object System.Drawing.Point(20, 310)
$pnlPresetBtns.Size = New-Object System.Drawing.Size(485, 34)
$form.Controls.Add($pnlPresetBtns)

$presets = @(
  @{ Id = "dtf"; Nome = "DTF / Sublimação"; Desc = "Multicores, camadas sobrepostas sem linhas brancas no filme" },
  @{ Id = "silk"; Nome = "Silk Screen (1 Cor)"; Desc = "Preto e branco puro, curvas ultra limpas para fotolito/telas" },
  @{ Id = "logo"; Nome = "Logo & Arte Chapada"; Desc = "Cores sólidas reduzidas, cantos vivos retos e nós mínimos" },
  @{ Id = "alta_definicao"; Nome = "Alta Definição"; Desc = "Máxima fidelidade para desenhos e ilustrações complexas" }
)

$global:presetAtivo = "dtf"
$botoesPreset = @()

foreach ($p in $presets) {
  $btn = New-Object System.Windows.Forms.Button
  $btn.Text = $p.Nome
  $btn.Size = New-Object System.Drawing.Size(117, 30)
  $btn.Font = New-Object System.Drawing.Font("Segoe UI", 7.5, [System.Drawing.FontStyle]::Bold)
  $btn.FlatStyle = "Flat"
  $btn.FlatAppearance.BorderSize = 0
  $btn.Cursor = [System.Windows.Forms.Cursors]::Hand
  $btn.Tag = $p.Id
  
  if ($p.Id -eq "dtf") {
    $btn.BackColor = [System.Drawing.Color]::FromArgb(79, 70, 229) # Indigo
    $btn.ForeColor = [System.Drawing.Color]::White
  } else {
    $btn.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
    $btn.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
  }

  $btn.Add_Click({
    $global:presetAtivo = $this.Tag
    foreach ($b in $botoesPreset) {
      if ($b.Tag -eq $global:presetAtivo) {
        $b.BackColor = [System.Drawing.Color]::FromArgb(79, 70, 229)
        $b.ForeColor = [System.Drawing.Color]::White
      } else {
        $b.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
        $b.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
      }
    }
    AtualizarConfigPreset
  })

  $botoesPreset += $btn
  $pnlPresetBtns.Controls.Add($btn)
}

# --- CONTROLES AVANCADOS ---
$pnlControles = New-Object System.Windows.Forms.Panel
$pnlControles.Location = New-Object System.Drawing.Point(20, 350)
$pnlControles.Size = New-Object System.Drawing.Size(485, 175)
$pnlControles.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$pnlControles.BorderStyle = "FixedSingle"
$form.Controls.Add($pnlControles)

# 1. Filtro Anti-Ruído
$lblSpeckle = New-Object System.Windows.Forms.Label
$lblSpeckle.Text = "Filtro Anti-Ruído (elimina micropontos e poeira):"
$lblSpeckle.Font = $fontLabel
$lblSpeckle.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblSpeckle.Location = New-Object System.Drawing.Point(12, 10)
$lblSpeckle.Size = New-Object System.Drawing.Size(320, 18)
$pnlControles.Controls.Add($lblSpeckle)

$numSpeckle = New-Object System.Windows.Forms.NumericUpDown
$numSpeckle.Location = New-Object System.Drawing.Point(340, 8)
$numSpeckle.Size = New-Object System.Drawing.Size(130, 24)
$numSpeckle.Minimum = 0
$numSpeckle.Maximum = 64
$numSpeckle.Value = 4
$numSpeckle.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numSpeckle.ForeColor = [System.Drawing.Color]::White
$numSpeckle.Font = $fontInput
$pnlControles.Controls.Add($numSpeckle)

# 2. Precisão / Quantidade de Cores
$lblPrecision = New-Object System.Windows.Forms.Label
$lblPrecision.Text = "Precisão e Quantidade de Cores (1 a 8):"
$lblPrecision.Font = $fontLabel
$lblPrecision.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblPrecision.Location = New-Object System.Drawing.Point(12, 42)
$lblPrecision.Size = New-Object System.Drawing.Size(320, 18)
$pnlControles.Controls.Add($lblPrecision)

$numPrecision = New-Object System.Windows.Forms.NumericUpDown
$numPrecision.Location = New-Object System.Drawing.Point(340, 40)
$numPrecision.Size = New-Object System.Drawing.Size(130, 24)
$numPrecision.Minimum = 1
$numPrecision.Maximum = 8
$numPrecision.Value = 7
$numPrecision.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numPrecision.ForeColor = [System.Drawing.Color]::White
$numPrecision.Font = $fontInput
$pnlControles.Controls.Add($numPrecision)

# 3. Limiar de Canto Vivo (Corner Threshold)
$lblCorner = New-Object System.Windows.Forms.Label
$lblCorner.Text = "Rigidez de Cantos Vivos (20° a 90°):"
$lblCorner.Font = $fontLabel
$lblCorner.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblCorner.Location = New-Object System.Drawing.Point(12, 74)
$lblCorner.Size = New-Object System.Drawing.Size(320, 18)
$pnlControles.Controls.Add($lblCorner)

$numCorner = New-Object System.Windows.Forms.NumericUpDown
$numCorner.Location = New-Object System.Drawing.Point(340, 72)
$numCorner.Size = New-Object System.Drawing.Size(130, 24)
$numCorner.Minimum = 20
$numCorner.Maximum = 90
$numCorner.Value = 60
$numCorner.BackColor = [System.Drawing.Color]::FromArgb(20, 27, 45)
$numCorner.ForeColor = [System.Drawing.Color]::White
$numCorner.Font = $fontInput
$pnlControles.Controls.Add($numCorner)

# 4. Checkbox de Upscaling Anti-Escadinha
$chkUpscale = New-Object System.Windows.Forms.CheckBox
$chkUpscale.Text = "Super-Resolução Inteligente (elimina escadinhas de pixels em imagens pequenas)"
$chkUpscale.Font = $fontSmall
$chkUpscale.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153) # Emerald
$chkUpscale.Location = New-Object System.Drawing.Point(12, 108)
$chkUpscale.Size = New-Object System.Drawing.Size(460, 22)
$chkUpscale.Checked = $true
$chkUpscale.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlControles.Controls.Add($chkUpscale)

# 5. Checkbox de Sobreposição Sem Frestas (Hierarchical Stacked)
$chkStacked = New-Object System.Windows.Forms.CheckBox
$chkStacked.Text = "Camadas Sobrepostas (zero frestas brancas na junção de cores para estamparia)"
$chkStacked.Font = $fontSmall
$chkStacked.ForeColor = [System.Drawing.Color]::FromArgb(103, 232, 249) # Cyan
$chkStacked.Location = New-Object System.Drawing.Point(12, 134)
$chkStacked.Size = New-Object System.Drawing.Size(460, 22)
$chkStacked.Checked = $true
$chkStacked.Cursor = [System.Windows.Forms.Cursors]::Hand
$pnlControles.Controls.Add($chkStacked)

function AtualizarConfigPreset {
  switch ($global:presetAtivo) {
    "dtf" {
      $numSpeckle.Value = 4
      $numPrecision.Value = 7
      $numCorner.Value = 60
      $chkStacked.Checked = $true
    }
    "silk" {
      $numSpeckle.Value = 8
      $numPrecision.Value = 4
      $numCorner.Value = 50
      $chkStacked.Checked = $false
    }
    "logo" {
      $numSpeckle.Value = 6
      $numPrecision.Value = 6
      $numCorner.Value = 45
      $chkStacked.Checked = $true
    }
    "alta_definicao" {
      $numSpeckle.Value = 2
      $numPrecision.Value = 8
      $numCorner.Value = 70
      $chkStacked.Checked = $true
    }
  }
}

# --- STATUS E MENSAGENS ---
$lblStatusProgresso = New-Object System.Windows.Forms.Label
$lblStatusProgresso.Text = "Pronto. Carregue uma imagem para vetorizar."
$lblStatusProgresso.Font = $fontStats
$lblStatusProgresso.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$lblStatusProgresso.Location = New-Object System.Drawing.Point(20, 535)
$lblStatusProgresso.Size = New-Object System.Drawing.Size(485, 20)
$lblStatusProgresso.TextAlign = "MiddleCenter"
$form.Controls.Add($lblStatusProgresso)

# --- BOTAO PRINCIPAL DE VETORIZACAO ---
$btnVetorizar = New-Object System.Windows.Forms.Button
$btnVetorizar.Text = "⚡ VETORIZAR E ENVIAR PARA O CORELDRAW"
$btnVetorizar.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$btnVetorizar.BackColor = [System.Drawing.Color]::FromArgb(79, 70, 229) # Indigo 600
$btnVetorizar.ForeColor = [System.Drawing.Color]::White
$btnVetorizar.Location = New-Object System.Drawing.Point(20, 565)
$btnVetorizar.Size = New-Object System.Drawing.Size(485, 48)
$btnVetorizar.FlatStyle = "Flat"
$btnVetorizar.FlatAppearance.BorderSize = 0
$btnVetorizar.Cursor = [System.Windows.Forms.Cursors]::Hand
$form.Controls.Add($btnVetorizar)

$global:caminhoImagemAtual = $null
$global:origemFormaCorel = $null

# --- EVENTO: ESCOLHER ARQUIVO DO PC ---
$btnArquivo.Add_Click({
  $dlg = New-Object System.Windows.Forms.OpenFileDialog
  $dlg.Title = "Selecione uma imagem para vetorizar"
  $dlg.Filter = "Imagens (*.png;*.jpg;*.jpeg;*.webp;*.bmp)|*.png;*.jpg;*.jpeg;*.webp;*.bmp|Todos (*.*)|*.*"
  if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    CarregarImagemNoPreview $dlg.FileName
    $global:origemFormaCorel = $null
  }
})

function CarregarImagemNoPreview($caminho) {
  try {
    $global:caminhoImagemAtual = $caminho
    $img = [System.Drawing.Image]::FromFile($caminho)
    $picPreview.Image = $img

    $nome = [System.IO.Path]::GetFileName($caminho)
    $tamKb = [Math]::Round(((New-Object System.IO.FileInfo($caminho)).Length / 1024), 1)
    $lblImgNome.Text = "$nome ($($img.Width) x $($img.Height) px - $tamKb KB)"
    $lblImgNome.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)

    $lblImgDimensoes.Text = "Imagem carregada e pronta para conversão vetorial de alta fidelidade."
    $lblStatusProgresso.Text = "Imagem pronta. Escolha o preset e clique em Vetorizar!"
    $lblStatusProgresso.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro ao carregar imagem: $($_.Exception.Message)", "Erro", "OK", "Error")
  }
}

# --- EVENTO: CAPTURAR SELECAO NO CORELDRAW ---
$btnLerCorel.Add_Click({
  try {
    $corel = New-Object -ComObject "CorelDRAW.Application.24"
    if (-not $corel.ActiveDocument) {
      [System.Windows.Forms.MessageBox]::Show("Abra um documento no CorelDRAW primeiro!", "Aviso", "OK", "Warning")
      return
    }

    $sel = $corel.ActiveSelection
    if ($sel.Shapes.Count -eq 0) {
      [System.Windows.Forms.MessageBox]::Show("Selecione uma imagem bitmap ou desenho no CorelDRAW!", "Aviso", "OK", "Warning")
      return
    }

    $shape = $sel.Shapes[1]
    $global:origemFormaCorel = $shape

    # Exporta para arquivo PNG temporário de alta resolução
    $tempDir = [System.IO.Path]::GetTempPath()
    $tempPng = [System.IO.Path]::Combine($tempDir, "corel_trace_temp_$(Get-Random).png")

    # ExportFilter no CorelDRAW (cdrPNG = 778 ou export standard)
    $exp = $corel.ActiveDocument.ExportBitmap($tempPng, 778, 0, 1, 0, 0, 300, 300, 1, $false, $false, $false, $false, 0, $null)
    $exp.Finish()

    if (Test-Path $tempPng) {
      CarregarImagemNoPreview $tempPng
      $lblImgNome.Text = "Capturado da seleção do CorelDRAW"
    } else {
      [System.Windows.Forms.MessageBox]::Show("Não foi possível exportar a seleção do CorelDRAW.", "Aviso", "OK", "Warning")
    }
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro ao capturar do Corel: $($_.Exception.Message)", "Erro", "OK", "Error")
  }
})

# --- EVENTO: EXECUTAR VETORIZACAO ---
$btnVetorizar.Add_Click({
  if (-not $global:caminhoImagemAtual -or -not (Test-Path $global:caminhoImagemAtual)) {
    [System.Windows.Forms.MessageBox]::Show("Carregue uma imagem ou capture do CorelDRAW antes de vetorizar!", "Aviso", "OK", "Warning")
    return
  }

  $btnVetorizar.Enabled = $false
  $btnVetorizar.Text = "⏳ Processando Dual-Splines e Vetorizando..."
  $lblStatusProgresso.Text = "Otimizando curvas e gerando vetores limpos..."
  $lblStatusProgresso.ForeColor = [System.Drawing.Color]::FromArgb(251, 191, 36)
  $form.Refresh()

  try {
    $tempDir = [System.IO.Path]::GetTempPath()
    $outputSvg = [System.IO.Path]::Combine($tempDir, "vetor_estamparia_$(Get-Random).svg")
    $vectorizePy = "E:\estamparia-manager\corel-plugin\vectorize.py"

    $argsList = @(
      "`"$vectorizePy`"",
      "`"$($global:caminhoImagemAtual)`"",
      "`"$outputSvg`"",
      "--preset", $global:presetAtivo,
      "--speckle", [int]$numSpeckle.Value,
      "--precision", [int]$numPrecision.Value,
      "--corner", [int]$numCorner.Value
    )

    if ($chkStacked.Checked) {
      $argsList += @("--hierarchical", "stacked")
    } else {
      $argsList += @("--hierarchical", "cutout")
    }

    if ($global:presetAtivo -eq "silk") {
      $argsList += @("--colormode", "binary")
    } else {
      $argsList += @("--colormode", "color")
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = $argsList -join " "
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::Start($psi)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    if ($proc.ExitCode -ne 0 -or -not (Test-Path $outputSvg)) {
      throw "Falha na vetorização: $stderr $stdout"
    }

    # Agora importa o arquivo SVG gerado diretamente para o CorelDRAW!
    $lblStatusProgresso.Text = "Importando vetor para a página do CorelDRAW..."
    $form.Refresh()

    $corel = New-Object -ComObject "CorelDRAW.Application.24"
    $doc = $corel.ActiveDocument
    if (-not $doc) {
      $doc = $corel.CreateDocument()
    }

    $doc.BeginCommandGroup("Vetorizar Imagem com IA")
    try {
      $layer = $doc.ActiveLayer
      # Constante cdrSVG = 1358 ou importacao automatica pelo caminho .svg
      $imp = $layer.Import($outputSvg)
      $imp.Finish()

      # Seleciona e agrupa o vetor importado
      $sel = $corel.ActiveSelection
      if ($sel.Shapes.Count -gt 0) {
        $vetorGrupo = $sel.Group()
        $vetorGrupo.CenterX = $doc.ActivePage.CenterX
        $vetorGrupo.CenterY = $doc.ActivePage.CenterY
      }

      [System.Windows.Forms.MessageBox]::Show("Vetorização concluída com sucesso!`n`nO desenho em curvas foi importado e centralizado no CorelDRAW sem nós excessivos e com preenchimentos perfeitos.`n`nVocê já pode desagrupar, separar cores ou mandar para corte e impressão!", "Sucesso!", "OK", "Information")
    } finally {
      $doc.EndCommandGroup()
      $corel.Refresh()
    }

    $lblStatusProgresso.Text = "Concluído com sucesso! Vetor importado no CorelDRAW."
    $lblStatusProgresso.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
  } catch {
    [System.Windows.Forms.MessageBox]::Show("Erro na vetorização: $($_.Exception.Message)", "Erro", "OK", "Error")
    $lblStatusProgresso.Text = "Erro durante a vetorização."
    $lblStatusProgresso.ForeColor = [System.Drawing.Color]::FromArgb(239, 68, 68)
  } finally {
    $btnVetorizar.Enabled = $true
    $btnVetorizar.Text = "⚡ VETORIZAR E ENVIAR PARA O CORELDRAW"
  }
})

# Atalho ESC para fechar
$form.KeyPreview = $true
$form.Add_KeyDown({
  if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Escape) {
    $form.Close()
  }
})

$form.ShowDialog() | Out-Null
