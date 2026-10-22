const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;

// Diretório local seguro para o banco de dados interno
const userDataPath = app.getPath('userData');
let dbFilePath = path.join(userDataPath, 'db_estamparia.json');

// Preservação absoluta dos dados existentes
const oldDbPath = path.join(app.getPath('appData'), 'estamparia-manager', 'db_estamparia.json');
if (!fs.existsSync(dbFilePath) && fs.existsSync(oldDbPath)) {
  try {
    fs.mkdirSync(userDataPath, { recursive: true });
    fs.copyFileSync(oldDbPath, dbFilePath);
  } catch (e) {
    dbFilePath = oldDbPath;
  }
}

// Carrega ou inicializa a base de dados interna
function carregarBanco() {
  if (!fs.existsSync(dbFilePath)) {
    const dadosIniciais = { clientes: [], pedidos: [] };
    try {
      fs.writeFileSync(dbFilePath, JSON.stringify(dadosIniciais, null, 2), 'utf-8');
    } catch (e) {
      console.error('Erro ao inicializar db_estamparia.json:', e);
    }
    return dadosIniciais;
  }
  try {
    const conteudo = fs.readFileSync(dbFilePath, 'utf-8');
    return JSON.parse(conteudo);
  } catch (error) {
    console.error('Erro ao ler banco local:', error);
    return { clientes: [], pedidos: [] };
  }
}

function salvarBanco(dados) {
  try {
    fs.writeFileSync(dbFilePath, JSON.stringify(dados, null, 2), 'utf-8');
    return true;
  } catch (error) {
    console.error('Erro ao gravar banco local:', error);
    return false;
  }
}

function createWindow() {
  const iconPath = path.join(__dirname, '../build/icon.png');

  mainWindow = new BrowserWindow({
    width: 1320,
    height: 860,
    minWidth: 1040,
    minHeight: 720,
    title: 'Order Separator - Gestão & Separação de Pedidos',
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    backgroundColor: '#090d16',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  const isDev = process.env.NODE_ENV !== 'production' && !app.isPackaged;

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// ======================== CANAIS IPC SEGUROS ======================== //

// 1. Selecionar pasta nativa do Windows Explorer
ipcMain.handle('dialog:selecionarPasta', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Selecione a Pasta do Cliente',
    properties: ['openDirectory', 'createDirectory']
  });
  if (result.canceled || result.filePaths.length === 0) {
    return null;
  }
  return path.normalize(result.filePaths[0]);
});

// 1.1 Selecionar imagens da estampa / mockup
ipcMain.handle('dialog:selecionarImagens', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Selecione as Imagens da Estampa / Mockup',
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'Imagens (JPG, PNG, WEBP, BMP)', extensions: ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif'] }
    ]
  });
  if (result.canceled || result.filePaths.length === 0) {
    return [];
  }

  return result.filePaths.map(caminho => {
    try {
      const ext = path.extname(caminho).replace('.', '').toLowerCase();
      const mime = ext === 'png' ? 'image/png' : ext === 'webp' ? 'image/webp' : 'image/jpeg';
      const buffer = fs.readFileSync(caminho);
      return {
        caminho: path.normalize(caminho),
        nome: path.basename(caminho),
        preview: `data:${mime};base64,${buffer.toString('base64')}`
      };
    } catch (e) {
      return {
        caminho: path.normalize(caminho),
        nome: path.basename(caminho),
        preview: ''
      };
    }
  });
});

// 2. Abrir pasta no Windows Explorer
ipcMain.handle('shell:abrirPasta', async (event, caminhoPasta) => {
  if (!caminhoPasta) return { sucesso: false, erro: 'Caminho não fornecido' };
  
  const caminhoNormalizado = path.normalize(caminhoPasta.trim());

  if (!fs.existsSync(caminhoNormalizado)) {
    try {
      fs.mkdirSync(caminhoNormalizado, { recursive: true });
    } catch (e) {
      return { sucesso: false, erro: 'A pasta não existe e não pôde ser criada no seu computador.' };
    }
  }

  const erro = await shell.openPath(caminhoNormalizado);
  if (erro) {
    return { sucesso: false, erro };
  }
  return { sucesso: true };
});

// 3. Verificar existência de pasta
ipcMain.handle('fs:verificarPasta', async (event, caminho) => {
  if (!caminho) return false;
  try {
    return fs.existsSync(path.normalize(caminho.trim()));
  } catch (e) {
    return false;
  }
});

// 4. Obter todos os dados do banco local
ipcMain.handle('db:obterDados', async () => {
  return carregarBanco();
});

// 5. Salvar / Atualizar cliente
ipcMain.handle('db:salvarCliente', async (event, cliente) => {
  const db = carregarBanco();
  
  const pastaLimpa = cliente.pastaDiretorio ? path.normalize(cliente.pastaDiretorio.trim()) : '';
  const clienteTratado = { ...cliente, pastaDiretorio: pastaLimpa };

  // Garante que a pasta física do cliente seja criada no PC
  if (pastaLimpa && !fs.existsSync(pastaLimpa)) {
    try {
      fs.mkdirSync(pastaLimpa, { recursive: true });
    } catch (e) {
      console.warn('Não foi possível criar a pasta no momento:', e.message);
    }
  }

  const index = db.clientes.findIndex(c => c.id === clienteTratado.id);
  if (index >= 0) {
    db.clientes[index] = { ...db.clientes[index], ...clienteTratado };
  } else {
    db.clientes.push(clienteTratado);
  }

  salvarBanco(db);
  return db.clientes;
});

// 6. Excluir cliente (apenas do banco, não remove a pasta do PC por segurança)
ipcMain.handle('db:excluirCliente', async (event, clienteId) => {
  const db = carregarBanco();
  db.clientes = db.clientes.filter(c => c.id !== clienteId);
  salvarBanco(db);
  return db.clientes;
});

// 7. Salvar Pedido (Grava no banco interno + Gera/Atualiza JSON na pasta do cliente)
ipcMain.handle('db:salvarPedido', async (event, pedido) => {
  const db = carregarBanco();
  
  const index = db.pedidos.findIndex(p => p.id === pedido.id);
  if (index >= 0) {
    db.pedidos[index] = { ...db.pedidos[index], ...pedido };
  } else {
    db.pedidos.push(pedido);
  }
  salvarBanco(db);

  // Salvamento físico na pasta do cliente
  let arquivoSalvoNoPC = null;
  if (pedido.clientePasta) {
    try {
      const pastaNormalizada = path.normalize(pedido.clientePasta.trim());
      if (!fs.existsSync(pastaNormalizada)) {
        fs.mkdirSync(pastaNormalizada, { recursive: true });
      }
      const dataHoje = new Date().toISOString().slice(0, 10);
      const nomeSanitizado = `pedido_${pedido.numeroPedido}_${dataHoje}.json`;
      const caminhoCompletoArquivo = path.join(pastaNormalizada, nomeSanitizado);
      
      // Copia as imagens da estampa para a pasta do cliente no PC
      if (Array.isArray(pedido.imagens)) {
        pedido.imagens.forEach((img, idx) => {
          try {
            if (img.caminho && fs.existsSync(img.caminho)) {
              const ext = path.extname(img.caminho);
              const nomeDestino = `pedido_${pedido.numeroPedido}_arte_${idx + 1}${ext}`;
              const caminhoDestino = path.join(pastaNormalizada, nomeDestino);
              if (path.normalize(img.caminho) !== caminhoDestino) {
                fs.copyFileSync(img.caminho, caminhoDestino);
              }
              img.caminhoSalvo = caminhoDestino;
            }
          } catch (eImg) {
            console.warn('Erro ao copiar imagem para a pasta do cliente:', eImg);
          }
        });
      }

      fs.writeFileSync(caminhoCompletoArquivo, JSON.stringify(pedido, null, 2), 'utf-8');
      arquivoSalvoNoPC = caminhoCompletoArquivo;
    } catch (err) {
      console.error('Erro ao gravar arquivo físico do pedido:', err);
    }
  }

  return {
    sucesso: true,
    pedidos: db.pedidos,
    caminhoArquivoPC: arquivoSalvoNoPC
  };
});

// 8. Atualizar Status do Pedido de forma rápida
ipcMain.handle('db:atualizarStatusPedido', async (event, { pedidoId, novoStatus }) => {
  const db = carregarBanco();
  const pedido = db.pedidos.find(p => p.id === pedidoId);
  
  if (pedido) {
    pedido.status = novoStatus;
    salvarBanco(db);

    // Atualiza também o arquivo físico na pasta do cliente, se existir
    if (pedido.clientePasta) {
      try {
        const pasta = path.normalize(pedido.clientePasta.trim());
        const dataHoje = new Date().toISOString().slice(0, 10);
        const nomeArquivo = `pedido_${pedido.numeroPedido}_${dataHoje}.json`;
        const caminhoCompleto = path.join(pasta, nomeArquivo);
        fs.writeFileSync(caminhoCompleto, JSON.stringify(pedido, null, 2), 'utf-8');
      } catch (err) {
        console.error('Erro ao atualizar status no arquivo físico:', err);
      }
    }
  }

  return db.pedidos;
});

// 9. Excluir Pedido (do banco)
ipcMain.handle('db:excluirPedido', async (event, pedidoId) => {
  const db = carregarBanco();
  db.pedidos = db.pedidos.filter(p => p.id !== pedidoId);
  salvarBanco(db);
  return db.pedidos;
});

// 10. Carimbar Ficha Técnica e Grade de Tamanhos diretamente no CorelDRAW
ipcMain.handle('corel:carimbarPedido', async (event, pedido) => {
  const { execFile } = require('child_process');
  
  return new Promise((resolve) => {
    const nomeLimpo = (pedido.clienteNome || '').replace(/"/g, '');
    const lojaLimpa = (pedido.clienteLoja || '').replace(/"/g, '');
    const estampaLimpa = (pedido.descricaoEstampa || '').replace(/"/g, '');
    const tecidoLimpo = (pedido.tipoTecido || '').replace(/"/g, '');
    const corLimpa = (pedido.corTecido || '').replace(/"/g, '');
    const obsLimpa = (pedido.observacoes || '').replace(/"/g, '').replace(/\r?\n/g, ' ');

    const hasObs = !!obsLimpa;
    const cardH = hasObs ? 120 : 106;

    const todosTamanhosOrdenados = [
      'PP', 'P', 'M', 'G', 'GG', 'XGG',
      'G1', 'G2', 'G3', 'G4', 'G5',
      'G6', 'G7', 'G8', 'G9', 'G10'
    ];
    const gradePedido = pedido.grade || {};

    let tamanhosComPeca = todosTamanhosOrdenados.filter(t => (Number(gradePedido[t]) || 0) > 0);
    if (tamanhosComPeca.length === 0) {
      tamanhosComPeca = ['PP', 'P', 'M', 'G', 'GG'];
    }

    const sizesItens = tamanhosComPeca.map(t => `@{ Nome = "${t}"; Qtd = ${Number(gradePedido[t]) || 0}; IsTotal = $false }`);
    sizesItens.push(`@{ Nome = "TOTAL"; Qtd = ${Number(pedido.totalPecas) || 0}; IsTotal = $true }`);
    const psSizesArray = `@(\n          ${sizesItens.join(',\n          ')}\n        )`;

    const qtdCaixas = sizesItens.length;
    const boxW = 38;
    const totalBoxW = 56;
    const gap = 4;
    const cardW = Math.max(260, ((qtdCaixas - 1) * (boxW + gap)) + totalBoxW + 24);

    const psScript = `
      try {
        $corel = New-Object -ComObject "CorelDRAW.Application.24"
        $corel.Visible = $true
        if ($corel.ActiveDocument -eq $null) {
          $doc = $corel.CreateDocument()
        } else {
          $doc = $corel.ActiveDocument
        }
        $doc.Unit = 3 # cdrMillimeter = 3
        $layer = $doc.ActiveLayer

        $cx = $doc.ActivePage.CenterX
        $cy = $doc.ActivePage.CenterY

        $doc.ClearSelection()

        $cardW = ${cardW}
        $cardH = ${cardH}
        $left = $cx - ($cardW / 2)
        $bottom = $cy - ($cardH / 2)

        # 1. Moldura Principal (Fundo Branco com contorno solido)
        $bg = $layer.CreateRectangle2($left, $bottom, $cardW, $cardH)
        $bg.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
        $bg.Outline.Color.CMYKAssign(0, 0, 0, 100)
        $bg.Outline.Width = 0.8
        $bg.Selected = $true

        # 2. Barra de Cabecalho (Fundo Preto Alto Contraste)
        $headerH = 24
        $headerY = $bottom + $cardH - $headerH
        $headerBg = $layer.CreateRectangle2($left, $headerY, $cardW, $headerH)
        $headerBg.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
        $headerBg.Outline.Type = 0
        $headerBg.Selected = $true

        # 3. Titulo do Cabecalho (8.5mm de altura real)
        $tHeader = $layer.CreateArtisticText($left + 8, $headerY + 5, "PEDIDO #${pedido.numeroPedido}  |  CLIENTE: ${nomeLimpo} ${lojaLimpa ? '- ' + lojaLimpa : ''}")
        $tHeader.Text.Story.Font = "Arial Black"
        $tHeader.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
        $tHeader.SetSize(0, 8.5)
        if ($tHeader.SizeWidth -gt ($cardW - 16)) {
          $tHeader.SetSize($cardW - 16, 0)
        }
        $tHeader.CenterY = $headerY + ($headerH / 2)
        $tHeader.LeftX = $left + 8
        $tHeader.Selected = $true

        # 4. Linha de Detalhes da Estampa e Tecido (5.5mm de altura real)
        $tInfo = $layer.CreateArtisticText($left + 8, $headerY - 11, "ESTAMPA: ${estampaLimpa} (${pedido.posicaoEstampa || 'Frente'})  |  TECIDO: ${tecidoLimpo || 'Padrao'} [${corLimpa || 'Cor Padrao'}]")
        $tInfo.Text.Story.Font = "Arial Black"
        $tInfo.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
        $tInfo.SetSize(0, 5.5)
        if ($tInfo.SizeWidth -gt ($cardW - 16)) {
          $tInfo.SetSize($cardW - 16, 0)
        }
        $tInfo.LeftX = $left + 8
        $tInfo.CenterY = $headerY - 11
        $tInfo.Selected = $true

        # 5. Caixas da Grade de Tamanhos
        $gridY = $bottom + (${hasObs ? 20 : 10})
        $boxH = 50
        $gap = 4
        $startX = $left + 8
        $curX = $startX

        $sizes = ${psSizesArray}

        for ($i = 0; $i -lt $sizes.Count; $i++) {
          $item = $sizes[$i]
          $curBoxW = if ($item.IsTotal) { 56 } else { 38 }
          $bx = $curX
          
          $box = $layer.CreateRectangle2($bx, $gridY, $curBoxW, $boxH)
          if ($item.IsTotal) {
            $box.Fill.UniformColor.CMYKAssign(0, 0, 0, 15)
            $box.Outline.Width = 1.0
          } else {
            $box.Fill.UniformColor.CMYKAssign(0, 0, 0, 0)
            $box.Outline.Width = 0.6
          }
          $box.Outline.Color.CMYKAssign(0, 0, 0, 100)
          $box.Selected = $true

          # Letra do Tamanho (7.5mm) - Auto-ajuste para NUNCA sair da caixa
          $tSize = $layer.CreateArtisticText($bx, $gridY, $item.Nome)
          $tSize.Text.Story.Font = "Arial Black"
          $tSize.Fill.UniformColor.CMYKAssign(0, 0, 0, 85)
          $tSize.SetSize(0, 7.5)
          if ($tSize.SizeWidth -gt ($curBoxW - 6)) {
            $tSize.SetSize(($curBoxW - 6), 0)
          }
          $tSize.CenterX = $bx + ($curBoxW / 2)
          $tSize.CenterY = $gridY + 38
          $tSize.Selected = $true

          # Numero da Quantidade (18mm) - Auto-ajuste para NUNCA sair da caixa
          $tQtd = $layer.CreateArtisticText($bx, $gridY, [string]$item.Qtd)
          $tQtd.Text.Story.Font = "Arial Black"
          $tQtd.Fill.UniformColor.CMYKAssign(0, 0, 0, 100)
          $tQtd.SetSize(0, 18.0)
          if ($tQtd.SizeWidth -gt ($curBoxW - 8)) {
            $tQtd.SetSize(($curBoxW - 8), 0)
          }
          $tQtd.CenterX = $bx + ($curBoxW / 2)
          $tQtd.CenterY = $gridY + 16
          $tQtd.Selected = $true

          $curX += ($curBoxW + $gap)
        }

        # 6. Observacoes se houver (4.5mm de altura real)
        ${hasObs ? `
        $tObs = $layer.CreateArtisticText($left + 8, $bottom + 6, "OBS: ${obsLimpa}")
        $tObs.Text.Story.Font = "Arial Black"
        $tObs.Fill.UniformColor.CMYKAssign(0, 0, 0, 90)
        $tObs.SetSize(0, 4.5)
        if ($tObs.SizeWidth -gt ($cardW - 16)) {
          $tObs.SetSize($cardW - 16, 0)
        }
        $tObs.LeftX = $left + 8
        $tObs.CenterY = $bottom + 7
        $tObs.Selected = $true
        ` : ''}

        # 7. Agrupa todas as formas criadas em um bloco unico
        $grupo = $corel.ActiveSelection.Group()
        if ($grupo -ne $null) {
          $grupo.CenterX = $doc.ActivePage.CenterX
          $grupo.CenterY = $doc.ActivePage.CenterY
        }

        Write-Output "SUCESSO"
      } catch {
        $msg = $_.Exception.Message
        Write-Output "ERRO: $msg"
      }
    `;

    const scriptPath = path.join(app.getPath('temp'), `corel_stamp_${Date.now()}.ps1`);
    try {
      fs.writeFileSync(scriptPath, psScript, 'utf8');
      execFile('powershell.exe', ['-ExecutionPolicy', 'Bypass', '-NoProfile', '-File', scriptPath], (error, stdout) => {
        try { fs.unlinkSync(scriptPath); } catch (e) {}
        
        const out = (stdout || '').trim();
        if (out.includes('SUCESSO')) {
          resolve({ sucesso: true });
        } else {
          resolve({ sucesso: false, erro: out || (error ? error.message : 'Falha na comunicação com o CorelDRAW') });
        }
      });
    } catch (errGeral) {
      resolve({ sucesso: false, erro: errGeral.message });
    }
  });
});

// 11. Abrir a Janelinha Flutuante do Montador de Folha (Gang Sheet)
ipcMain.handle('corel:abrirMontador', async () => {
  const { execFile } = require('child_process');

  const caminhosPossiveis = [
    process.resourcesPath ? path.join(process.resourcesPath, 'corel-plugin', 'montador_folha.ps1') : null,
    path.join(__dirname, '..', 'corel-plugin', 'montador_folha.ps1'),
    path.join(app.getAppPath(), 'corel-plugin', 'montador_folha.ps1'),
    path.join(path.dirname(app.getPath('exe')), 'resources', 'corel-plugin', 'montador_folha.ps1'),
    path.join(path.dirname(app.getPath('exe')), '..', '..', 'corel-plugin', 'montador_folha.ps1'),
    'E:\\estamparia-manager\\corel-plugin\\montador_folha.ps1',
    path.join(app.getPath('userData'), 'montador_folha.ps1')
  ].filter(Boolean);

  let scriptEncontrado = null;
  for (const c of caminhosPossiveis) {
    if (fs.existsSync(c)) {
      scriptEncontrado = c;
      break;
    }
  }

  // Se não estiver em disco acessível, copia do diretório base do projeto para userData
  if (!scriptEncontrado) {
    try {
      const fallbackOrigem = 'E:\\estamparia-manager\\corel-plugin\\montador_folha.ps1';
      const destinoUserData = path.join(app.getPath('userData'), 'montador_folha.ps1');
      if (fs.existsSync(fallbackOrigem)) {
        fs.copyFileSync(fallbackOrigem, destinoUserData);
        scriptEncontrado = destinoUserData;
      }
    } catch (eCopy) {
      console.warn('Erro ao copiar script para userData:', eCopy);
    }
  }

  if (scriptEncontrado) {
    execFile('powershell.exe', [
      '-ExecutionPolicy', 'Bypass',
      '-NoProfile',
      '-WindowStyle', 'Hidden',
      '-File', scriptEncontrado
    ], (err) => {
      if (err) {
        console.error('Erro na execução do montador:', err);
      }
    });
    return { sucesso: true, caminho: scriptEncontrado };
  }

  return { sucesso: false, erro: 'Script do montador de folha não foi encontrado nos caminhos do sistema.' };
});

// 11.1 Abrir Vetorizador Profissional CorelDRAW (Dual-Splines / IA)
ipcMain.handle('corel:abrirVetorizador', async (event, caminhoImagem) => {
  const { execFile } = require('child_process');

  const caminhosPython = [
    process.resourcesPath ? path.join(process.resourcesPath, 'corel-plugin', 'vetorizador_app.py') : null,
    path.join(__dirname, '..', 'corel-plugin', 'vetorizador_app.py'),
    path.join(app.getAppPath(), 'corel-plugin', 'vetorizador_app.py'),
    path.join(path.dirname(app.getPath('exe')), 'resources', 'corel-plugin', 'vetorizador_app.py'),
    'E:\\estamparia-manager\\corel-plugin\\vetorizador_app.py'
  ].filter(Boolean);

  let pyEncontrado = null;
  for (const c of caminhosPython) {
    if (fs.existsSync(c)) {
      pyEncontrado = c;
      break;
    }
  }

  if (pyEncontrado) {
    const pythonExe = fs.existsSync('C:\\Python314\\pythonw.exe') ? 'C:\\Python314\\pythonw.exe' : 'pythonw.exe';
    const args = caminhoImagem ? [pyEncontrado, caminhoImagem] : [pyEncontrado];
    execFile(pythonExe, args, (err) => {
      if (err) {
        const fallbackPy = fs.existsSync('C:\\Python314\\python.exe') ? 'C:\\Python314\\python.exe' : 'python.exe';
        execFile(fallbackPy, args, (err2) => {
          if (err2) console.error('Erro na execução do vetorizador python:', err2);
        });
      }
    });
    return { sucesso: true, caminho: pyEncontrado };
  }

  const caminhosPossiveis = [
    process.resourcesPath ? path.join(process.resourcesPath, 'corel-plugin', 'vetorizador.ps1') : null,
    path.join(__dirname, '..', 'corel-plugin', 'vetorizador.ps1'),
    'E:\\estamparia-manager\\corel-plugin\\vetorizador.ps1'
  ].filter(Boolean);

  let scriptEncontrado = null;
  for (const c of caminhosPossiveis) {
    if (fs.existsSync(c)) {
      scriptEncontrado = c;
      break;
    }
  }

  if (scriptEncontrado) {
    execFile('powershell.exe', [
      '-ExecutionPolicy', 'Bypass',
      '-NoProfile',
      '-WindowStyle', 'Hidden',
      '-File', scriptEncontrado
    ], (err) => {
      if (err) {
        console.error('Erro na execução do vetorizador:', err);
      }
    });
    return { sucesso: true, caminho: scriptEncontrado };
  }

  return { sucesso: false, erro: 'Script do vetorizador não foi encontrado nos caminhos do sistema.' };
});

// 11.2 Abrir Removedor de Fundo IA (U2-Net / IS-Net / BRIA / Chroma / Fundo Branco)
ipcMain.handle('corel:abrirRemovedor', async (event, caminhoImagem) => {
  const { execFile } = require('child_process');

  const caminhosPython = [
    process.resourcesPath ? path.join(process.resourcesPath, 'corel-plugin', 'removedor_fundo_app.py') : null,
    path.join(__dirname, '..', 'corel-plugin', 'removedor_fundo_app.py'),
    path.join(app.getAppPath(), 'corel-plugin', 'removedor_fundo_app.py'),
    path.join(path.dirname(app.getPath('exe')), 'resources', 'corel-plugin', 'removedor_fundo_app.py'),
    'E:\\estamparia-manager\\corel-plugin\\removedor_fundo_app.py'
  ].filter(Boolean);

  let pyEncontrado = null;
  for (const c of caminhosPython) {
    if (fs.existsSync(c)) {
      pyEncontrado = c;
      break;
    }
  }

  if (pyEncontrado) {
    const pythonExe = fs.existsSync('C:\\Python314\\pythonw.exe') 
      ? 'C:\\Python314\\pythonw.exe' 
      : 'pythonw.exe';
    const args = caminhoImagem ? [pyEncontrado, caminhoImagem] : [pyEncontrado];

    execFile(pythonExe, args, (err) => {
      if (err) {
        const fallbackPy = fs.existsSync('C:\\Python314\\python.exe') ? 'C:\\Python314\\python.exe' : 'python.exe';
        execFile(fallbackPy, args, (err2) => {
          if (err2) console.error('Erro na execução do removedor de fundo python:', err2);
        });
      }
    });
    return { sucesso: true, caminho: pyEncontrado };
  }

  return { sucesso: false, erro: 'Script do removedor de fundo não foi encontrado nos caminhos do sistema.' };
});

// 11.3 Abrir Upscaler IA Ultra HD 4x / 8x (Real-ESRGAN / DirectML RTX)
ipcMain.handle('corel:abrirUpscaler', async (event, caminhoImagem) => {
  const { execFile } = require('child_process');

  const caminhosPython = [
    process.resourcesPath ? path.join(process.resourcesPath, 'corel-plugin', 'upscaler_ai_app.py') : null,
    path.join(__dirname, '..', 'corel-plugin', 'upscaler_ai_app.py'),
    path.join(app.getAppPath(), 'corel-plugin', 'upscaler_ai_app.py'),
    path.join(path.dirname(app.getPath('exe')), 'resources', 'corel-plugin', 'upscaler_ai_app.py'),
    'E:\\estamparia-manager\\corel-plugin\\upscaler_ai_app.py'
  ].filter(Boolean);

  let pyEncontrado = null;
  for (const c of caminhosPython) {
    if (fs.existsSync(c)) {
      pyEncontrado = c;
      break;
    }
  }

  if (pyEncontrado) {
    const pythonExe = fs.existsSync('C:\\Python314\\pythonw.exe') 
      ? 'C:\\Python314\\pythonw.exe' 
      : 'pythonw.exe';
    const args = caminhoImagem ? [pyEncontrado, caminhoImagem] : [pyEncontrado];

    execFile(pythonExe, args, (err) => {
      if (err) {
        const fallbackPy = fs.existsSync('C:\\Python314\\python.exe') ? 'C:\\Python314\\python.exe' : 'python.exe';
        execFile(fallbackPy, args, (err2) => {
          if (err2) console.error('Erro na execução do upscaler de imagem python:', err2);
        });
      }
    });
    return { sucesso: true, caminho: pyEncontrado };
  }

  return { sucesso: false, erro: 'Script do upscaler de imagem não foi encontrado nos caminhos do sistema.' };
});

// 12. Criar Subpasta do Pedido no Explorer e Organizar Arquivos
ipcMain.handle('pastas:criarPastaPedido', async (event, pedido) => {
  if (!pedido || !pedido.clientePasta) {
    return { sucesso: false, erro: 'Este cliente não possui uma pasta vinculada no computador.' };
  }

  try {
    const nomeLimpoEstampa = (pedido.descricaoEstampa || 'Arte').replace(/[\\/:*?"<>|]/g, '_').trim();
    const nomeSubpasta = `PEDIDO_${pedido.numeroPedido}_${nomeLimpoEstampa}`;
    const caminhoSubpasta = path.join(path.normalize(pedido.clientePasta), nomeSubpasta);

    if (!fs.existsSync(caminhoSubpasta)) {
      fs.mkdirSync(caminhoSubpasta, { recursive: true });
    }

    // Copia as fotos/mockups da estampa para dentro da subpasta do pedido
    if (Array.isArray(pedido.imagens)) {
      pedido.imagens.forEach((img, idx) => {
        const origem = img.caminho || img.caminhoSalvo;
        if (origem && fs.existsSync(origem)) {
          const ext = path.extname(origem);
          const destino = path.join(caminhoSubpasta, `Mockup_${idx + 1}${ext}`);
          try {
            if (path.normalize(origem) !== destino) {
              fs.copyFileSync(origem, destino);
            }
          } catch (e) {}
        }
      });
    }

    // Grava a ficha técnica do pedido em JSON dentro da subpasta
    fs.writeFileSync(path.join(caminhoSubpasta, `Ficha_Pedido_${pedido.numeroPedido}.json`), JSON.stringify(pedido, null, 2), 'utf-8');

    // Abre a pasta criada diretamente no Windows Explorer
    await shell.openPath(caminhoSubpasta);

    return { sucesso: true, caminho: caminhoSubpasta };
  } catch (err) {
    return { sucesso: false, erro: err.message };
  }
});
