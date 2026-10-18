const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selecionarPasta: () => ipcRenderer.invoke('dialog:selecionarPasta'),
  selecionarImagens: () => ipcRenderer.invoke('dialog:selecionarImagens'),
  abrirPasta: (caminho) => ipcRenderer.invoke('shell:abrirPasta', caminho),
  verificarPasta: (caminho) => ipcRenderer.invoke('fs:verificarPasta', caminho),
  obterDados: () => ipcRenderer.invoke('db:obterDados'),
  salvarCliente: (cliente) => ipcRenderer.invoke('db:salvarCliente', cliente),
  excluirCliente: (clienteId) => ipcRenderer.invoke('db:excluirCliente', clienteId),
  salvarPedido: (pedido) => ipcRenderer.invoke('db:salvarPedido', pedido),
  atualizarStatusPedido: (pedidoId, novoStatus) => ipcRenderer.invoke('db:atualizarStatusPedido', { pedidoId, novoStatus }),
  excluirPedido: (pedidoId) => ipcRenderer.invoke('db:excluirPedido', pedidoId),
  carimbarNoCorel: (pedido) => ipcRenderer.invoke('corel:carimbarPedido', pedido),
  abrirMontadorCorel: () => ipcRenderer.invoke('corel:abrirMontador'),
  abrirVetorizadorCorel: () => ipcRenderer.invoke('corel:abrirVetorizador'),
  criarPastaPedido: (pedido) => ipcRenderer.invoke('pastas:criarPastaPedido', pedido)
});
