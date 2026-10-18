Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# Localiza e lê o banco de dados do Estamparia Manager
$dbPath = "$env:APPDATA\estamparia-manager\db_estamparia.json"

if (-not (Test-Path $dbPath)) {
    [System.Windows.Forms.MessageBox]::Show(
        "Banco de dados do Estamparia Manager não encontrado em:`n$dbPath",
        "Estamparia Manager",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit
}

try {
    $db = Get-Content $dbPath -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    [System.Windows.Forms.MessageBox]::Show(
        "Erro ao ler banco de dados: $($_.Exception.Message)",
        "Erro",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
    exit
}

if ($db.pedidos.Count -eq 0) {
    [System.Windows.Forms.MessageBox]::Show(
        "Nenhum pedido foi cadastrado ainda no aplicativo Estamparia Manager.`nLance um pedido primeiro para carimbar no CorelDRAW.",
        "Nenhum Pedido Encontrado",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    )
    exit
}

# Cria a Janela Principal com estilo moderno escuro
$form = New-Object System.Windows.Forms.Form
$form.Text = "Estamparia Manager - Conexão CorelDRAW"
$form.Size = New-Object System.Drawing.Size(640, 560)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42) # Slate 900
$form.ForeColor = [System.Drawing.Color]::White

# Título
$lblTitulo = New-Object System.Windows.Forms.Label
$lblTitulo.Text = "Vincular Pedido à Arte do CorelDRAW"
$lblTitulo.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$lblTitulo.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248) # Indigo 400
$lblTitulo.Location = New-Object System.Drawing.Point(20, 15)
$lblTitulo.Size = New-Object System.Drawing.Size(580, 30)
$form.Controls.Add($lblTitulo)

# Subtítulo
$lblSub = New-Object System.Windows.Forms.Label
$lblSub.Text = "Selecione o pedido abaixo para visualizar a grade e carimbar a ficha de produção na folha ativa."
$lblSub.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
$lblSub.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184) # Slate 400
$lblSub.Location = New-Object System.Drawing.Point(20, 45)
$lblSub.Size = New-Object System.Drawing.Size(580, 20)
$form.Controls.Add($lblSub)

# Lista de Pedidos
$lblLista = New-Object System.Windows.Forms.Label
$lblLista.Text = "PEDIDOS CADASTRADOS NO SISTEMA:"
$lblLista.Font = New-Object System.Drawing.Font("Segoe UI", 8.5, [System.Drawing.FontStyle]::Bold)
$lblLista.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$lblLista.Location = New-Object System.Drawing.Point(20, 75)
$lblLista.Size = New-Object System.Drawing.Size(580, 18)
$form.Controls.Add($lblLista)

$listBox = New-Object System.Windows.Forms.ListBox
$listBox.Location = New-Object System.Drawing.Point(20, 95)
$listBox.Size = New-Object System.Drawing.Size(580, 110)
$listBox.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59) # Slate 800
$listBox.ForeColor = [System.Drawing.Color]::White
$listBox.Font = New-Object System.Drawing.Font("Consolas", 10, [System.Drawing.FontStyle]::Bold)
$listBox.BorderStyle = "FixedSingle"

foreach ($ped in $db.pedidos) {
    $itemTexto = "Pedido #{0,-5} | {1,-18} | {2,-18} | Total: {3} pcs" -f $ped.numeroPedido, $ped.clienteNome, $ped.descricaoEstampa, $ped.totalPecas
    [void]$listBox.Items.Add($itemTexto)
}
$listBox.SelectedIndex = 0
$form.Controls.Add($listBox)

# Painel de Detalhes da Grade
$panelDetalhes = New-Object System.Windows.Forms.Panel
$panelDetalhes.Location = New-Object System.Drawing.Point(20, 215)
$panelDetalhes.Size = New-Object System.Drawing.Size(580, 200)
$panelDetalhes.BackColor = [System.Drawing.Color]::FromArgb(8, 14, 26)
$panelDetalhes.BorderStyle = "FixedSingle"

$lblDetalhes = New-Object System.Windows.Forms.Label
$lblDetalhes.Location = New-Object System.Drawing.Point(15, 12)
$lblDetalhes.Size = New-Object System.Drawing.Size(550, 175)
$lblDetalhes.Font = New-Object System.Drawing.Font("Consolas", 9.5)
$lblDetalhes.ForeColor = [System.Drawing.Color]::FromArgb(226, 232, 240)
$panelDetalhes.Controls.Add($lblDetalhes)
$form.Controls.Add($panelDetalhes)

# Atualiza detalhes ao selecionar na lista
$atualizarPainel = {
    $idx = $listBox.SelectedIndex
    if ($idx -ge 0 -and $idx -lt $db.pedidos.Count) {
        $p = $db.pedidos[$idx]
        $texto = @"
============================================================
CLIENTE: $($p.clienteNome.ToUpper()) $(if($p.clienteLoja){"($($p.clienteLoja))"})
ESTAMPA: $($p.descricaoEstampa) ($($p.posicaoEstampa))
TECIDO:  $($p.tipoTecido) [$($p.corTecido)]
------------------------------------------------------------
GRADE DE TAMANHOS:
  [ P: $($p.grade.P) ]  [ M: $($p.grade.M) ]  [ G: $($p.grade.G) ]  [ GG: $($p.grade.GG) ]  [ XGG: $($p.grade.XGG) ]
TOTAL GERAL: $($p.totalPecas) PEÇAS
============================================================
$(if($p.observacoes){"OBS: " + $p.observacoes})
"@
        $lblDetalhes.Text = $texto
    }
}
$listBox.Add_SelectedIndexChanged($atualizarPainel)
&$atualizarPainel

# Botão: Carimbar na Folha do CorelDRAW
$btnCarimbar = New-Object System.Windows.Forms.Button
$btnCarimbar.Text = "🎨 CARIMBAR GRADE NA FOLHA DO CORELDRAW"
$btnCarimbar.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$btnCarimbar.BackColor = [System.Drawing.Color]::FromArgb(79, 70, 229) # Indigo 600
$btnCarimbar.ForeColor = [System.Drawing.Color]::White
$btnCarimbar.FlatStyle = "Flat"
$btnCarimbar.FlatAppearance.BorderSize = 0
$btnCarimbar.Location = New-Object System.Drawing.Point(20, 430)
$btnCarimbar.Size = New-Object System.Drawing.Size(370, 48)
$btnCarimbar.Cursor = [System.Windows.Forms.Cursors]::Hand

$btnCarimbar.Add_Click({
    $idx = $listBox.SelectedIndex
    if ($idx -lt 0) { return }
    $ped = $db.pedidos[$idx]

    try {
        $corel = New-Object -ComObject "CorelDRAW.Application.24"
        $corel.Visible = $true
        if ($corel.ActiveDocument -eq $null) {
            $doc = $corel.CreateDocument()
        } else {
            $doc = $corel.ActiveDocument
        }
        $doc.Unit = 4 # cdrMillimeter

        $textoFicha = @"
PEDIDO #$($ped.numeroPedido) | CLIENTE: $($ped.clienteNome.ToUpper()) $(if($ped.clienteLoja){"- " + $ped.clienteLoja.ToUpper()})
GRADE: P: $($ped.grade.P) | M: $($ped.grade.M) | G: $($ped.grade.G) | GG: $($ped.grade.GG) | XGG: $($ped.grade.XGG) | TOTAL: $($ped.totalPecas) PEÇAS
ESTAMPA: $($ped.descricaoEstampa) ($($ped.posicaoEstampa)) | TECIDO: $($ped.tipoTecido) [$($ped.corTecido)]
$(if($ped.observacoes){"OBS: " + $ped.observacoes})
"@

        $shape = $doc.ActiveLayer.CreateParagraphText(10, 40, 190, 10, $textoFicha)
        $shape.Text.Story.Font = "Consolas"
        $shape.Text.Story.Size = 9
        $shape.Fill.UniformColor.CMYKAssign(0, 0, 0, 100) # K100

        [System.Windows.Forms.MessageBox]::Show(
            "Ficha Técnica do Pedido #$($ped.numeroPedido) ($($ped.totalPecas) peças) carimbada na folha do CorelDRAW com sucesso!",
            "Sucesso",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        )
    } catch {
        [System.Windows.Forms.MessageBox]::Show(
            "Erro ao comunicar com o CorelDRAW:`n$($_.Exception.Message)",
            "Erro de Conexão",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        )
    }
})
$form.Controls.Add($btnCarimbar)

# Botão: Salvar Arte na Pasta do Cliente
$btnSalvar = New-Object System.Windows.Forms.Button
$btnSalvar.Text = "📁 ABRIR PASTA DO CLIENTE"
$btnSalvar.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$btnSalvar.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$btnSalvar.ForeColor = [System.Drawing.Color]::FromArgb(129, 140, 248)
$btnSalvar.FlatStyle = "Flat"
$btnSalvar.FlatAppearance.BorderSize = 1
$btnSalvar.FlatAppearance.BorderColor = [System.Drawing.Color]::FromArgb(79, 70, 229)
$btnSalvar.Location = New-Object System.Drawing.Point(400, 430)
$btnSalvar.Size = New-Object System.Drawing.Size(200, 48)
$btnSalvar.Cursor = [System.Windows.Forms.Cursors]::Hand

$btnSalvar.Add_Click({
    $idx = $listBox.SelectedIndex
    if ($idx -lt 0) { return }
    $ped = $db.pedidos[$idx]
    if ($ped.clientePasta -and (Test-Path $ped.clientePasta)) {
        [System.Diagnostics.Process]::Start("explorer.exe", $ped.clientePasta)
    } else {
        [System.Windows.Forms.MessageBox]::Show(
            "Nenhuma pasta vinculada a este cliente.",
            "Aviso",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        )
    }
})
$form.Controls.Add($btnSalvar)

# Exibe a janela
[void]$form.ShowDialog()
