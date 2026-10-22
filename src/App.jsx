import React, { useState, useEffect, useMemo } from 'react';
import { 
  FolderOpen, 
  PlusCircle, 
  Users, 
  Search, 
  FileText, 
  Printer, 
  CheckCircle, 
  FolderSync, 
  Layers, 
  Save, 
  Phone, 
  Calendar, 
  AlertTriangle, 
  RefreshCw,
  Clock,
  CheckCircle2,
  PackageCheck,
  Truck,
  ExternalLink,
  Trash2,
  TrendingUp,
  X,
  MessageCircle,
  Tag,
  Palette,
  Hash,
  Scissors,
  ImagePlus,
  ImageIcon,
  Eye,
  Copy,
  Edit3,
  CheckSquare,
  FolderPlus,
  Grid,
  Sparkles,
  Maximize2,
  Calculator
} from 'lucide-react';
import logoImg from './assets/logo.png';

const STATUS_OPCOES = [
  { id: 'Aguardando Produção', label: 'Aguardando', icon: Clock, bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-700/50' },
  { id: 'Em Produção', label: 'Em Produção', icon: Scissors, bg: 'bg-blue-950/60', text: 'text-blue-400', border: 'border-blue-700/50' },
  { id: 'Pronto', label: 'Pronto', icon: CheckCircle2, bg: 'bg-emerald-950/60', text: 'text-emerald-400', border: 'border-emerald-700/50' },
  { id: 'Entregue', label: 'Entregue', icon: Truck, bg: 'bg-purple-950/60', text: 'text-purple-400', border: 'border-purple-700/50' }
];

export const TAMANHOS_PADRAO = [
  'PP', 'P', 'M', 'G', 'GG',
  'G1', 'G2', 'G3', 'G4', 'G5',
  'G6', 'G7', 'G8', 'G9', 'G10'
];

export const criarGradeVazia = () => {
  const g = {};
  TAMANHOS_PADRAO.forEach(t => { g[t] = 0; });
  return g;
};

export default function App() {
  const [abaAtiva, setAbaAtiva] = useState('pedidos'); // 'pedidos' | 'novo-pedido' | 'clientes'
  const [clientes, setClientes] = useState([]);
  const [pedidos, setPedidos] = useState([]);
  const [busca, setBusca] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('Todos');
  const [notificacao, setNotificacao] = useState(null);
  const [modalConfirmacao, setModalConfirmacao] = useState(null);
  const [imagemModal, setImagemModal] = useState(null); // Preview em tela cheia da estampa
  const [modoEdicaoId, setModoEdicaoId] = useState(null);
  const [modalSeparacao, setModalSeparacao] = useState(null);
  const [itensConferidos, setItensConferidos] = useState({});
  const [modalFicha, setModalFicha] = useState(null); // Ficha de Produção / OS
  const [modalCalculadoraDTF, setModalCalculadoraDTF] = useState(false); // Calculadora DTF

  // Formulário da Calculadora de Bobina DTF
  const [dtfCalcForm, setDtfCalcForm] = useState({
    larguraBobina: 58,
    larguraEstampa: 20,
    alturaEstampa: 28,
    quantidade: 50,
    espacamento: 1,
    custoMetro: 35.0,
    margemLucro: 100,
    origemPedido: ''
  });

  // Cálculo Dinâmico de Aproveitamento na Bobina DTF
  const resultadoCalculoDTF = useMemo(() => {
    const bobina = Math.max(10, Number(dtfCalcForm.larguraBobina) || 58);
    const lEst = Math.max(1, Number(dtfCalcForm.larguraEstampa) || 20);
    const aEst = Math.max(1, Number(dtfCalcForm.alturaEstampa) || 28);
    const qtd = Math.max(1, Number(dtfCalcForm.quantidade) || 1);
    const esp = Math.max(0, Number(dtfCalcForm.espacamento) || 1);
    const cMetro = Number(dtfCalcForm.custoMetro) || 35.0;
    const margem = Number(dtfCalcForm.margemLucro) || 100;

    // Quantas artes cabem lado a lado na largura da bobina
    const porLinha = Math.max(1, Math.floor((bobina + esp) / (lEst + esp)));
    const totalLinhas = Math.ceil(qtd / porLinha);
    const metrosLineares = Number(((totalLinhas * (aEst + esp)) / 100).toFixed(2));
    const m2Total = Number(((metrosLineares * bobina) / 100).toFixed(2));
    const custoTotal = Number((metrosLineares * cMetro).toFixed(2));
    const precoSugerido = Number((custoTotal * (1 + margem / 100)).toFixed(2));
    const custoUn = Number((custoTotal / qtd).toFixed(2));
    const precoUn = Number((precoSugerido / qtd).toFixed(2));

    return {
      porLinha,
      totalLinhas,
      metrosLineares,
      m2Total,
      custoTotal,
      precoSugerido,
      custoUn,
      precoUn
    };
  }, [dtfCalcForm]);

  const abrirCalculadoraParaPedido = (pedido) => {
    let larg = 20, alt = 28;
    const pos = (pedido.posicaoEstampa || '').toLowerCase();
    if (pos.includes('peito') || pos.includes('bolso') || pos.includes('manga')) {
      larg = 10; alt = 10;
    } else if (pos.includes('costas') || pos.includes('a3') || pos.includes('grande')) {
      larg = 28; alt = 40;
    } else if (pos.includes('frente')) {
      larg = 21; alt = 30;
    }
    setDtfCalcForm(prev => ({
      ...prev,
      larguraEstampa: larg,
      alturaEstampa: alt,
      quantidade: pedido.totalPecas || 1,
      origemPedido: `#${pedido.numeroPedido} - ${pedido.clienteNome}`
    }));
    setModalCalculadoraDTF(true);
  };

  // Formulário de Clientes
  const [clienteForm, setClienteForm] = useState({
    nome: '',
    loja: '',
    telefone: '',
    pastaDiretorio: ''
  });

  // Formulário de Pedidos (Estamparia)
  const [pedidoForm, setPedidoForm] = useState({
    clienteId: '',
    numeroPedido: '',
    descricaoEstampa: '',
    tipoTecido: 'Algodão 30.1 Penteado',
    corTecido: 'Preta',
    posicaoEstampa: 'Frente + Costas',
    dataEntrega: '',
    grade: criarGradeVazia(),
    imagens: [],
    observacoes: ''
  });

  // Carrega os dados iniciais via IPC
  const carregarDados = async () => {
    if (window.electronAPI) {
      try {
        const dados = await window.electronAPI.obterDados();
        setClientes(dados.clientes || []);
        setPedidos(dados.pedidos || []);
      } catch (err) {
        console.error('Erro ao carregar dados:', err);
      }
    }
  };

  useEffect(() => {
    carregarDados();
  }, []);

  // Notificação Toast
  const avisar = (tipo, mensagem) => {
    setNotificacao({ tipo, mensagem });
    setTimeout(() => setNotificacao(null), 4500);
  };

  // Gerar número de pedido sequencial automático
  const prepararNovoPedido = () => {
    setModoEdicaoId(null);
    const proximoNumero = pedidos.length > 0 
      ? Math.max(...pedidos.map(p => Number(p.numeroPedido) || 0)) + 1 
      : 1001;

    const dataSugerida = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    setPedidoForm({
      clienteId: clientes.length > 0 ? clientes[0].id : '',
      numeroPedido: String(proximoNumero),
      descricaoEstampa: '',
      tipoTecido: 'Algodão 30.1 Penteado',
      corTecido: 'Preta',
      posicaoEstampa: 'Frente + Costas',
      dataEntrega: dataSugerida,
      grade: criarGradeVazia(),
      imagens: [],
      observacoes: ''
    });
    setAbaAtiva('novo-pedido');
  };

  // Iniciar Edição de Pedido Existente
  const iniciarEdicaoPedido = (pedido) => {
    setModoEdicaoId(pedido.id);
    setPedidoForm({
      clienteId: pedido.clienteId || '',
      numeroPedido: pedido.numeroPedido || '',
      descricaoEstampa: pedido.descricaoEstampa || '',
      tipoTecido: pedido.tipoTecido || 'Algodão 30.1 Penteado',
      corTecido: pedido.corTecido || 'Preta',
      posicaoEstampa: pedido.posicaoEstampa || 'Frente + Costas',
      dataEntrega: pedido.dataEntrega || '',
      grade: { ...criarGradeVazia(), ...(pedido.grade || {}) },
      imagens: Array.isArray(pedido.imagens) ? [...pedido.imagens] : [],
      observacoes: pedido.observacoes || ''
    });
    setAbaAtiva('novo-pedido');
    avisar('sucesso', `Editando Pedido #${pedido.numeroPedido}`);
  };

  // Duplicar Pedido existente com novo número
  const duplicarPedido = (pedido) => {
    setModoEdicaoId(null);
    const proximoNumero = pedidos.length > 0 
      ? Math.max(...pedidos.map(p => Number(p.numeroPedido) || 0)) + 1 
      : 1001;

    const dataSugerida = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

    setPedidoForm({
      clienteId: pedido.clienteId || '',
      numeroPedido: String(proximoNumero),
      descricaoEstampa: pedido.descricaoEstampa ? `${pedido.descricaoEstampa} (Cópia)` : '',
      tipoTecido: pedido.tipoTecido || 'Algodão 30.1 Penteado',
      corTecido: pedido.corTecido || 'Preta',
      posicaoEstampa: pedido.posicaoEstampa || 'Frente + Costas',
      dataEntrega: dataSugerida,
      grade: { ...criarGradeVazia(), ...(pedido.grade || {}) },
      imagens: Array.isArray(pedido.imagens) ? [...pedido.imagens] : [],
      observacoes: pedido.observacoes || ''
    });
    setAbaAtiva('novo-pedido');
    avisar('sucesso', `Pedido duplicado como rascunho com o número #${proximoNumero}!`);
  };

  // Criar Pasta Organizada do Projeto no Windows Explorer
  const criarPastaProjeto = async (pedido) => {
    if (!window.electronAPI || !window.electronAPI.criarPastaPedido) {
      avisar('erro', 'Recurso de pasta de projeto indisponível.');
      return;
    }
    avisar('sucesso', `Organizando pasta do Pedido #${pedido.numeroPedido}...`);
    try {
      const res = await window.electronAPI.criarPastaPedido(pedido);
      if (res.sucesso) {
        avisar('sucesso', `Pasta criada e aberta: ${res.caminho}`);
      } else {
        avisar('erro', `Erro ao criar pasta: ${res.erro}`);
      }
    } catch (e) {
      avisar('erro', 'Erro: ' + e.message);
    }
  };

  // Abrir Montador de Folha Flutuante CorelDRAW
  const abrirMontadorCorel = async () => {
    if (!window.electronAPI || !window.electronAPI.abrirMontadorCorel) {
      avisar('erro', 'Montador de Folhas CorelDRAW indisponível.');
      return;
    }
    avisar('sucesso', 'Abrindo janela do Montador de Folha no CorelDRAW...');
    try {
      const res = await window.electronAPI.abrirMontadorCorel();
      if (!res.sucesso) {
        avisar('erro', `Falha ao abrir montador: ${res.erro}`);
      }
    } catch (e) {
      avisar('erro', 'Erro ao abrir montador: ' + e.message);
    }
  };

  // Abrir Vetorizador Profissional CorelDRAW
  const abrirVetorizadorCorel = async (caminhoImagem = null) => {
    if (!window.electronAPI || !window.electronAPI.abrirVetorizadorCorel) {
      avisar('erro', 'Vetorizador CorelDRAW indisponível.');
      return;
    }
    avisar('sucesso', 'Abrindo janela do Vetorizador Profissional...');
    try {
      const res = await window.electronAPI.abrirVetorizadorCorel(caminhoImagem);
      if (!res.sucesso) {
        avisar('erro', `Falha ao abrir vetorizador: ${res.erro}`);
      }
    } catch (e) {
      avisar('erro', 'Erro ao abrir vetorizador: ' + e.message);
    }
  };

  // Abrir Removedor de Fundo IA CorelDRAW
  const abrirRemovedorCorel = async (caminhoImagem = null) => {
    if (!window.electronAPI || !window.electronAPI.abrirRemovedorCorel) {
      avisar('erro', 'Removedor de Fundo CorelDRAW indisponível.');
      return;
    }
    avisar('sucesso', 'Abrindo janela do Removedor de Fundo IA...');
    try {
      const res = await window.electronAPI.abrirRemovedorCorel(caminhoImagem);
      if (!res.sucesso) {
        avisar('erro', `Falha ao abrir removedor: ${res.erro}`);
      }
    } catch (e) {
      avisar('erro', 'Erro ao abrir removedor: ' + e.message);
    }
  };

  // Abrir Upscaler IA Ultra HD CorelDRAW
  const abrirUpscalerCorel = async (caminhoImagem = null) => {
    if (!window.electronAPI || !window.electronAPI.abrirUpscalerCorel) {
      avisar('erro', 'Upscaler IA CorelDRAW indisponível.');
      return;
    }
    avisar('sucesso', 'Abrindo janela do Upscaler IA Ultra HD...');
    try {
      const res = await window.electronAPI.abrirUpscalerCorel(caminhoImagem);
      if (!res.sucesso) {
        avisar('erro', `Falha ao abrir upscaler: ${res.erro}`);
      }
    } catch (e) {
      avisar('erro', 'Erro ao abrir upscaler: ' + e.message);
    }
  };

  // Funções de Checklist de Separação
  const abrirSeparacao = (pedido) => {
    setModalSeparacao(pedido);
    setItensConferidos(prev => ({
      ...prev,
      [pedido.id]: prev[pedido.id] || {}
    }));
  };

  const alternarItemSeparado = (pedidoId, tamanho) => {
    setItensConferidos(prev => {
      const checks = { ...(prev[pedidoId] || {}) };
      checks[tamanho] = !checks[tamanho];
      return {
        ...prev,
        [pedidoId]: checks
      };
    });
  };

  const concluirSeparacao = async (pedido) => {
    await mudarStatusPedido(pedido.id, 'Pronto');
    avisar('sucesso', `🎉 Separação do Pedido #${pedido.numeroPedido} concluída e marcado como Pronto!`);
    setModalSeparacao(null);
  };

  // Selecionar imagens da estampa
  const escolherImagensEstampa = async () => {
    if (!window.electronAPI) return;
    try {
      const imagensSelecionadas = await window.electronAPI.selecionarImagens();
      if (imagensSelecionadas && imagensSelecionadas.length > 0) {
        setPedidoForm(prev => ({
          ...prev,
          imagens: [...prev.imagens, ...imagensSelecionadas]
        }));
        avisar('sucesso', `${imagensSelecionadas.length} imagem(ns) da arte anexada(s)!`);
      }
    } catch (e) {
      console.error(e);
      avisar('erro', 'Erro ao carregar imagens: ' + e.message);
    }
  };

  // Remover imagem selecionada
  const removerImagemEstampa = (indexRemover) => {
    setPedidoForm(prev => ({
      ...prev,
      imagens: prev.imagens.filter((_, idx) => idx !== indexRemover)
    }));
  };

  // Selecionar Pasta Nativa do Windows para Cliente
  const escolherPastaCliente = async () => {
    if (!window.electronAPI) return;
    try {
      const caminho = await window.electronAPI.selecionarPasta();
      if (caminho) {
        setClienteForm(prev => ({ ...prev, pastaDiretorio: caminho }));
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Salvar Cliente
  const handleSalvarCliente = async (e) => {
    e.preventDefault();
    if (!clienteForm.nome.trim() || !clienteForm.pastaDiretorio.trim()) {
      avisar('erro', 'Preencha o Nome do cliente e selecione a Pasta no PC.');
      return;
    }

    const novoCliente = {
      ...clienteForm,
      nome: clienteForm.nome.trim(),
      loja: clienteForm.loja.trim(),
      telefone: clienteForm.telefone.trim(),
      id: Date.now().toString(),
      criadoEm: new Date().toISOString()
    };

    if (window.electronAPI) {
      try {
        const listaAtualizada = await window.electronAPI.salvarCliente(novoCliente);
        setClientes(listaAtualizada);
        avisar('sucesso', `Cliente "${novoCliente.nome}" cadastrado com sucesso!`);
        setClienteForm({ nome: '', loja: '', telefone: '', pastaDiretorio: '' });
      } catch (err) {
        avisar('erro', 'Erro ao salvar cliente: ' + err.message);
      }
    }
  };

  // Confirmar e Excluir Cliente
  const confirmarExcluirCliente = (cliente) => {
    setModalConfirmacao({
      titulo: 'Excluir Cliente',
      mensagem: `Deseja realmente remover o cliente "${cliente.nome}" do sistema? (Os arquivos na pasta do PC não serão excluídos).`,
      acaoConfirmar: async () => {
        if (window.electronAPI) {
          const listaAtualizada = await window.electronAPI.excluirCliente(cliente.id);
          setClientes(listaAtualizada);
          avisar('sucesso', `Cliente "${cliente.nome}" removido do catálogo.`);
        }
        setModalConfirmacao(null);
      }
    });
  };

  // Total de Peças Calculado Dinamicamente
  const totalPecas = useMemo(() => {
    return Object.values(pedidoForm.grade).reduce((acc, qtd) => acc + (Number(qtd) || 0), 0);
  }, [pedidoForm.grade]);

  // Alterar grade via botões + e -
  const alterarQtdGrade = (tamanho, delta) => {
    setPedidoForm(prev => {
      const atual = Number(prev.grade[tamanho]) || 0;
      const novo = Math.max(0, atual + delta);
      return {
        ...prev,
        grade: {
          ...prev.grade,
          [tamanho]: novo
        }
      };
    });
  };

  // Salvar Pedido (Novo ou Edição)
  const handleSalvarPedido = async (e) => {
    e.preventDefault();
    if (!pedidoForm.clienteId) {
      avisar('erro', 'Por favor, selecione um cliente para o pedido!');
      return;
    }
    if (totalPecas <= 0) {
      avisar('erro', 'Informe ao menos 1 peça na grade de tamanhos.');
      return;
    }

    const clienteSelecionado = clientes.find(c => c.id === pedidoForm.clienteId);
    const pedidoExistente = modoEdicaoId ? pedidos.find(p => p.id === modoEdicaoId) : null;

    const pedidoSalvar = {
      ...pedidoForm,
      id: modoEdicaoId || Date.now().toString(),
      clienteNome: clienteSelecionado ? clienteSelecionado.nome : 'Cliente Avulso',
      clienteLoja: clienteSelecionado ? clienteSelecionado.loja : '',
      clientePasta: clienteSelecionado ? clienteSelecionado.pastaDiretorio : '',
      totalPecas,
      dataCriacao: pedidoExistente?.dataCriacao || new Date().toISOString(),
      status: pedidoExistente?.status || 'Aguardando Produção'
    };

    if (window.electronAPI) {
      try {
        const resposta = await window.electronAPI.salvarPedido(pedidoSalvar);
        if (resposta.sucesso) {
          setPedidos(resposta.pedidos);
          avisar('sucesso', modoEdicaoId 
            ? `Pedido #${pedidoSalvar.numeroPedido} atualizado com sucesso!`
            : `Pedido #${pedidoSalvar.numeroPedido} gravado com sucesso! Arquivo JSON gerado na pasta do cliente.`
          );
          setModoEdicaoId(null);
          setAbaAtiva('pedidos');
        }
      } catch (err) {
        avisar('erro', 'Erro ao salvar pedido: ' + err.message);
      }
    }
  };

  // Mudar Status do Pedido Rapidamente
  const mudarStatusPedido = async (pedidoId, novoStatus) => {
    if (window.electronAPI) {
      try {
        const pedidosAtualizados = await window.electronAPI.atualizarStatusPedido(pedidoId, novoStatus);
        setPedidos(pedidosAtualizados);
        avisar('sucesso', `Status atualizado para: "${novoStatus}"!`);
      } catch (err) {
        avisar('erro', 'Erro ao atualizar status: ' + err.message);
      }
    }
  };

  // Confirmar e Excluir Pedido
  const confirmarExcluirPedido = (pedido) => {
    setModalConfirmacao({
      titulo: `Excluir Pedido #${pedido.numeroPedido}`,
      mensagem: `Tem certeza que deseja apagar o Pedido #${pedido.numeroPedido} (${pedido.clienteNome}) do painel de controle?`,
      acaoConfirmar: async () => {
        if (window.electronAPI) {
          const pedidosAtualizados = await window.electronAPI.excluirPedido(pedido.id);
          setPedidos(pedidosAtualizados);
          avisar('sucesso', `Pedido #${pedido.numeroPedido} excluído com sucesso.`);
        }
        setModalConfirmacao(null);
      }
    });
  };

  // Abrir pasta no Windows Explorer
  const abrirNoExplorer = async (caminho) => {
    if (!caminho) {
      avisar('erro', 'Nenhuma pasta associada a este cliente.');
      return;
    }
    if (window.electronAPI) {
      const res = await window.electronAPI.abrirPasta(caminho);
      if (!res.sucesso) {
        avisar('erro', `Não foi possível abrir o caminho: ${res.erro}`);
      } else {
        avisar('sucesso', 'Pasta aberta no Windows Explorer!');
      }
    }
  };

  // Carimbar Ficha e Grade de Tamanhos diretamente no CorelDRAW aberto
  const [enviandoCorel, setEnviandoCorel] = useState(null);

  const carimbarNoCorelDRAW = async (pedido) => {
    if (!window.electronAPI || !window.electronAPI.carimbarNoCorel) {
      avisar('erro', 'Recurso do CorelDRAW indisponível.');
      return;
    }

    setEnviandoCorel(pedido.id);
    avisar('sucesso', `Conectando ao CorelDRAW para o Pedido #${pedido.numeroPedido}...`);

    try {
      const res = await window.electronAPI.carimbarNoCorel(pedido);
      if (res.sucesso) {
        avisar('sucesso', `🎨 Ficha do Pedido #${pedido.numeroPedido} (${pedido.totalPecas} peças) carimbada no CorelDRAW!`);
      } else {
        avisar('erro', `Não foi possível carimbar no Corel: ${res.erro}`);
      }
    } catch (err) {
      avisar('erro', 'Falha ao conectar ao CorelDRAW: ' + err.message);
    } finally {
      setEnviandoCorel(null);
    }
  };

  // Formatar Data BR
  const formatarDataBR = (dataIso) => {
    if (!dataIso) return '-';
    try {
      const partes = dataIso.split('-');
      if (partes.length === 3) {
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
      }
      return new Date(dataIso).toLocaleDateString('pt-BR');
    } catch (e) {
      return dataIso;
    }
  };

  // Métricas do Topo
  const metricas = useMemo(() => {
    const total = pedidos.length;
    const aguardando = pedidos.filter(p => p.status === 'Aguardando Produção').length;
    const emProducao = pedidos.filter(p => p.status === 'Em Produção').length;
    const concluidos = pedidos.filter(p => p.status === 'Pronto' || p.status === 'Entregue').length;
    const totalPecasProducao = pedidos
      .filter(p => p.status !== 'Entregue')
      .reduce((acc, p) => acc + (Number(p.totalPecas) || 0), 0);

    return { total, aguardando, emProducao, concluidos, totalPecasProducao };
  }, [pedidos]);

  // Filtragem de Pedidos na busca rápida
  const pedidosFiltrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    return pedidos.filter(p => {
      const matchStatus = filtroStatus === 'Todos' || p.status === filtroStatus;
      if (!matchStatus) return false;

      if (!termo) return true;
      return (
        (p.numeroPedido && p.numeroPedido.toLowerCase().includes(termo)) ||
        (p.clienteNome && p.clienteNome.toLowerCase().includes(termo)) ||
        (p.clienteLoja && p.clienteLoja.toLowerCase().includes(termo)) ||
        (p.descricaoEstampa && p.descricaoEstampa.toLowerCase().includes(termo))
      );
    });
  }, [pedidos, busca, filtroStatus]);

  return (
    <div className="flex h-screen bg-[#070b13] text-slate-100 font-sans overflow-hidden">
      {/* ================= MODAL DE CONFIRMAÇÃO SEGURO ================= */}
      {modalConfirmacao && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-amber-400">
              <div className="p-2 bg-amber-950/60 rounded-xl border border-amber-800/50">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-white">{modalConfirmacao.titulo}</h3>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {modalConfirmacao.mensagem}
            </p>
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setModalConfirmacao(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold rounded-xl transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={modalConfirmacao.acaoConfirmar}
                className="px-5 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-red-600/30 transition-colors"
              >
                Confirmar Exclusão
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================= MODAL DE VISUALIZAÇÃO DE IMAGEM DA ESTAMPA ================= */}
      {imagemModal && (
        <div 
          onClick={() => setImagemModal(null)}
          className="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex flex-col items-center justify-center p-6 animate-in fade-in duration-200 cursor-pointer"
        >
          <div className="relative max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-950/80">
              <span className="text-sm font-bold text-slate-200 font-mono flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-indigo-400" />
                {imagemModal.nome || 'Arte da Estampa'}
              </span>
              <button 
                onClick={() => setImagemModal(null)}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 flex items-center justify-center overflow-auto max-h-[75vh] bg-[#050811]">
              <img 
                src={imagemModal.preview || imagemModal.caminhoSalvo || imagemModal.caminho} 
                alt="Arte da Estampa" 
                className="max-h-[70vh] max-w-full object-contain rounded-xl shadow-lg"
              />
            </div>
            <div className="p-3 bg-slate-950 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800">
              <div className="text-xs text-slate-400 font-mono truncate max-w-xs md:max-w-md">
                {imagemModal.caminho || imagemModal.caminhoSalvo || 'Arte da Estampa'}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const p = imagemModal.caminhoSalvo || imagemModal.caminho;
                    abrirRemovedorCorel(p);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 rounded-xl text-xs font-bold transition-all shadow-sm"
                  title="Abrir esta imagem diretamente no Removedor de Fundo IA"
                >
                  <Scissors className="w-3.5 h-3.5" />
                  Recortar IA
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = imagemModal.caminhoSalvo || imagemModal.caminho;
                    abrirUpscalerCorel(p);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40 rounded-xl text-xs font-bold transition-all shadow-sm"
                  title="Aumentar para Ultra HD 300 DPI com IA"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                  Upscale 4x
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = imagemModal.caminhoSalvo || imagemModal.caminho;
                    abrirVetorizadorCorel(p);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/40 rounded-xl text-xs font-bold transition-all shadow-sm"
                  title="Converter para curvas SVG com IA"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Vetorizar IA
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= MODAL DE CONFERÊNCIA DE SEPARAÇÃO ================= */}
      {modalSeparacao && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 max-w-2xl w-full shadow-2xl space-y-6">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <span className="text-indigo-400 font-mono font-black text-xl bg-indigo-950 border border-indigo-800 px-3 py-1 rounded-xl">
                    #{modalSeparacao.numeroPedido}
                  </span>
                  <h3 className="font-extrabold text-xl text-white">Checklist de Separação</h3>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Cliente: <strong className="text-slate-200">{modalSeparacao.clienteNome}</strong> • Estampa: <strong className="text-slate-200">{modalSeparacao.descricaoEstampa || 'Sem descrição'}</strong>
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  Tecido: <strong className="text-slate-200">{modalSeparacao.tipoTecido} ({modalSeparacao.corTecido})</strong> • Posição: <strong className="text-slate-200">{modalSeparacao.posicaoEstampa}</strong>
                </p>
              </div>
              <button
                onClick={() => setModalSeparacao(null)}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Progresso de Separação */}
            {(() => {
              const tamanhosComPecas = Object.entries(modalSeparacao.grade || {}).filter(([_, qtd]) => Number(qtd) > 0);
              const checksDoPedido = itensConferidos[modalSeparacao.id] || {};
              const qtdConferidos = tamanhosComPecas.filter(([tam]) => checksDoPedido[tam]).length;
              const totalTamanhos = tamanhosComPecas.length;
              const porcentagem = totalTamanhos > 0 ? Math.round((qtdConferidos / totalTamanhos) * 100) : 0;
              const todosConferidos = totalTamanhos > 0 && qtdConferidos === totalTamanhos;

              return (
                <div className="space-y-4">
                  <div className="bg-slate-950/70 p-4 rounded-2xl border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-slate-400">Progresso de Separação:</span>
                      <span className="text-indigo-400 font-mono font-bold">{qtdConferidos} de {totalTamanhos} tamanhos conferidos ({porcentagem}%)</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-300 ${todosConferidos ? 'bg-emerald-500' : 'bg-indigo-600'}`}
                        style={{ width: `${porcentagem}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Grade de Separação com Checkboxes */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 max-h-[40vh] overflow-y-auto pr-1">
                    {tamanhosComPecas.map(([tam, qtd]) => {
                      const conferido = !!checksDoPedido[tam];
                      return (
                        <button
                          key={tam}
                          type="button"
                          onClick={() => alternarItemSeparado(modalSeparacao.id, tam)}
                          className={`p-3 rounded-2xl border flex flex-col items-center justify-between gap-2 transition-all cursor-pointer ${
                            conferido 
                              ? 'bg-emerald-950/40 border-emerald-600 text-emerald-300 shadow-lg shadow-emerald-950/50' 
                              : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                          }`}
                        >
                          <div className="flex items-center justify-between w-full">
                            <span className="text-xs font-mono font-bold uppercase">{tam}</span>
                            <div className={`w-5 h-5 rounded-lg flex items-center justify-center border ${
                              conferido ? 'bg-emerald-600 border-emerald-500 text-white' : 'border-slate-700 bg-slate-900'
                            }`}>
                              {conferido && <CheckCircle className="w-3.5 h-3.5" />}
                            </div>
                          </div>
                          <span className="text-2xl font-black font-mono">{qtd}</span>
                          <span className="text-[10px] uppercase font-bold text-slate-400">peças</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Botões do Rodapé do Modal */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-800">
                    <span className="text-xs text-slate-400 font-mono">
                      Total: <strong className="text-white">{modalSeparacao.totalPecas} peças</strong>
                    </span>
                    <div className="flex gap-2 w-full sm:w-auto">
                      <button
                        type="button"
                        onClick={() => setModalSeparacao(null)}
                        className="flex-1 sm:flex-none px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-colors"
                      >
                        Fechar
                      </button>
                      <button
                        type="button"
                        onClick={() => concluirSeparacao(modalSeparacao)}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/30 transition-all cursor-pointer"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        Finalizar Separação & Marcar Pronto
                      </button>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* ================= MODAL FICHA DE PRODUÇÃO (OS IMPRESSA) ================= */}
      {modalFicha && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
          <div className="relative bg-white text-slate-900 rounded-3xl max-w-3xl w-full p-6 md:p-8 shadow-2xl space-y-6 my-auto" id="area-impressao-ficha">
            
            {/* Barra de Ações (Não sai na impressão) */}
            <div className="no-print flex items-center justify-between border-b border-slate-200 pb-4">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-lg text-slate-900">Ficha de Produção & Ordem de Serviço</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
                  title="Imprimir esta ficha em papel A4 ou salvar como PDF"
                >
                  <Printer className="w-4 h-4" />
                  Imprimir Ficha (A4)
                </button>
                <button
                  type="button"
                  onClick={() => setModalFicha(null)}
                  className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Cabeçalho Físico da Ficha */}
            <div className="flex items-start justify-between border-b-2 border-slate-900 pb-4">
              <div>
                <h1 className="text-2xl font-black text-slate-900 uppercase tracking-tight">Order Separator</h1>
                <p className="text-xs text-slate-600 font-semibold uppercase tracking-wider">Ficha de Produção & Estamparia Têxtil</p>
                <div className="mt-2 text-xs text-slate-700 space-y-0.5">
                  <p><strong>Emissão:</strong> {new Date().toLocaleDateString('pt-BR')} às {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</p>
                  {modalFicha.dataEntrega && (
                    <p className="text-red-700 font-bold"><strong>Prazo de Entrega:</strong> {formatarDataBR(modalFicha.dataEntrega)}</p>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="inline-block px-4 py-2 bg-slate-900 text-white font-mono font-black text-2xl rounded-2xl">
                  #{modalFicha.numeroPedido}
                </div>
                <div className="mt-2 text-xs font-bold text-slate-700 uppercase">
                  Status: <span className="underline">{modalFicha.status}</span>
                </div>
              </div>
            </div>

            {/* Dados do Cliente e Especificações da Peça */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] border-b border-slate-200 pb-1 flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-indigo-600" /> Dados do Cliente
                </h4>
                <p><strong>Cliente:</strong> {modalFicha.clienteNome}</p>
                {modalFicha.clienteLoja && <p><strong>Loja/Marca:</strong> {modalFicha.clienteLoja}</p>}
                {modalFicha.clienteTelefone && <p><strong>Telefone / WhatsApp:</strong> {modalFicha.clienteTelefone}</p>}
              </div>

              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] border-b border-slate-200 pb-1 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-indigo-600" /> Especificação Têxtil
                </h4>
                <p><strong>Tecido:</strong> {modalFicha.tipoTecido}</p>
                <p><strong>Cor do Tecido:</strong> <span className="font-bold uppercase px-1.5 py-0.5 bg-slate-200 rounded">{modalFicha.corTecido}</span></p>
                <p><strong>Posição da Estampa:</strong> {modalFicha.posicaoEstampa}</p>
                <p><strong>Descrição da Arte:</strong> {modalFicha.descricaoEstampa || 'Sem descrição'}</p>
              </div>
            </div>

            {/* Imagem da Arte e Grade Quantitativa */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
              {/* Imagem / Mockup */}
              <div className="border border-slate-200 rounded-2xl p-3 bg-slate-50 flex flex-col items-center justify-center text-center">
                <span className="text-[11px] font-bold text-slate-700 uppercase mb-2">Mockup / Arte</span>
                {Array.isArray(modalFicha.imagens) && modalFicha.imagens.length > 0 ? (
                  <img 
                    src={modalFicha.imagens[0].preview || modalFicha.imagens[0].caminhoSalvo || modalFicha.imagens[0].caminho} 
                    alt="Arte da Estampa" 
                    className="max-h-40 max-w-full object-contain rounded-xl border border-slate-300 shadow-sm"
                  />
                ) : (
                  <div className="h-32 w-full flex items-center justify-center text-slate-400 text-xs italic border border-dashed border-slate-300 rounded-xl">
                    Sem arte anexada
                  </div>
                )}
              </div>

              {/* Tabela de Grade de Peças */}
              <div className="md:col-span-2 border border-slate-200 rounded-2xl p-4 bg-slate-50">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] border-b border-slate-200 pb-2 mb-3 flex items-center justify-between">
                  <span>Grade de Produção & Separação</span>
                  <span className="font-mono text-sm text-indigo-700 font-black">Total: {modalFicha.totalPecas} peças</span>
                </h4>
                
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-300 text-slate-600 uppercase text-[10px]">
                      <th className="py-1 px-2">Tamanho</th>
                      <th className="py-1 px-2 font-mono text-right">Qtd</th>
                      <th className="py-1 px-3 text-center">Conferido [ ✓ ]</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(modalFicha.grade || {})
                      .filter(([_, qtd]) => Number(qtd) > 0)
                      .map(([tam, qtd]) => (
                        <tr key={tam} className="border-b border-slate-200">
                          <td className="py-1.5 px-2 font-bold font-mono text-slate-900">{tam}</td>
                          <td className="py-1.5 px-2 font-bold font-mono text-right text-indigo-700">{qtd} un</td>
                          <td className="py-1.5 px-3 text-center">
                            <span className="inline-block w-4 h-4 border-2 border-slate-400 rounded"></span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Observações e Assinaturas */}
            <div className="border-t border-slate-200 pt-3 space-y-4 text-xs">
              {modalFicha.observacoes && (
                <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900">
                  <strong>Observações Importantes:</strong> {modalFicha.observacoes}
                </div>
              )}

              <div className="grid grid-cols-2 gap-8 pt-6">
                <div className="border-t border-slate-400 text-center pt-1 text-slate-600">
                  Assinatura do Separador / Impressor
                </div>
                <div className="border-t border-slate-400 text-center pt-1 text-slate-600">
                  Assinatura da Conferência / Expedição
                </div>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* ================= MODAL CALCULADORA DE BOBINA DTF ================= */}
      {modalCalculadoraDTF && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 md:p-8 max-w-2xl w-full shadow-2xl space-y-6 my-auto">
            
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-amber-950/80 rounded-xl border border-amber-800/60">
                  <Calculator className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="font-extrabold text-lg text-white">Calculadora de Bobina DTF</h3>
                  <p className="text-xs text-slate-400">
                    {dtfCalcForm.origemPedido ? `Calculando para: ${dtfCalcForm.origemPedido}` : 'Cálculo inteligente de metragem linear, aproveitamento e custo de insumos'}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setModalCalculadoraDTF(false)}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Presets Rápidos de Estampa */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Presets de Tamanho de Estampa:</span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { label: 'Peito / Bolso', w: 10, h: 10 },
                  { label: 'Frente A4', w: 20, h: 28 },
                  { label: 'Costas A3', w: 28, h: 40 },
                  { label: 'Painel Total', w: 56, h: 40 }
                ].map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setDtfCalcForm(prev => ({ ...prev, larguraEstampa: preset.w, alturaEstampa: preset.h }))}
                    className="px-3 py-2 bg-slate-950 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/50 rounded-xl text-xs font-semibold text-slate-300 transition-all text-center"
                  >
                    <div>{preset.label}</div>
                    <div className="text-[10px] text-amber-400 font-mono mt-0.5">{preset.w} x {preset.h} cm</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Campos de Entrada */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase">Largura Bobina (cm):</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.larguraBobina}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, larguraBobina: e.target.value })}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono font-bold text-sm focus:border-amber-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase">Largura Estampa (cm):</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.larguraEstampa}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, larguraEstampa: e.target.value })}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono font-bold text-sm focus:border-amber-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase">Altura Estampa (cm):</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.alturaEstampa}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, alturaEstampa: e.target.value })}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono font-bold text-sm focus:border-amber-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase">Quantidade de Peças:</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.quantidade}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, quantidade: e.target.value })}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono font-bold text-sm focus:border-amber-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase">Custo / Metro (R$):</label>
                <input 
                  type="number" 
                  step="0.5"
                  value={dtfCalcForm.custoMetro}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, custoMetro: e.target.value })}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono font-bold text-sm focus:border-amber-500 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-slate-400 uppercase">Margem de Lucro (%):</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.margemLucro}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, margemLucro: e.target.value })}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white font-mono font-bold text-sm focus:border-amber-500 outline-none"
                />
              </div>
            </div>

            {/* Painel de Resultados */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-slate-950/70 p-3.5 rounded-2xl border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase">Aproveitamento:</span>
                <div className="font-mono text-base font-black text-amber-400">
                  {resultadoCalculoDTF.porLinha} un / linha
                </div>
                <p className="text-[10px] text-slate-500">{resultadoCalculoDTF.totalLinhas} linhas na bobina</p>
              </div>

              <div className="bg-slate-950/70 p-3.5 rounded-2xl border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase">Metragem Bobina:</span>
                <div className="font-mono text-base font-black text-sky-400">
                  {resultadoCalculoDTF.metrosLineares} m
                </div>
                <p className="text-[10px] text-slate-500">Área: {resultadoCalculoDTF.m2Total} m²</p>
              </div>

              <div className="bg-slate-950/70 p-3.5 rounded-2xl border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase">Custo Estimado:</span>
                <div className="font-mono text-base font-black text-red-400">
                  R$ {resultadoCalculoDTF.custoTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
                <p className="text-[10px] text-slate-500">R$ {resultadoCalculoDTF.custoUn.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} / un</p>
              </div>

              <div className="bg-slate-950/70 p-3.5 rounded-2xl border border-slate-800 space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase">Preço Sugerido:</span>
                <div className="font-mono text-base font-black text-emerald-400">
                  R$ {resultadoCalculoDTF.precoSugerido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
                <p className="text-[10px] text-slate-500">R$ {resultadoCalculoDTF.precoUn.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} / un</p>
              </div>
            </div>

            {/* Rodapé do Modal */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setModalCalculadoraDTF(false)}
                className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-colors"
              >
                Fechar
              </button>
            </div>

          </div>
        </div>
      )}

      {/* ================= BARRA LATERAL ================= */}
      <aside className="w-64 bg-slate-900/90 backdrop-blur border-r border-slate-800/80 flex flex-col justify-between p-4 select-none">
        <div>
          {/* Logo / Cabeçalho */}
          <div className="flex items-center gap-3 px-2 py-4 mb-6 border-b border-slate-800/80">
            <div className="w-11 h-11 rounded-2xl overflow-hidden shadow-xl shadow-indigo-950/50 border border-slate-700/80 flex items-center justify-center bg-[#070b13] shrink-0">
              <img src={logoImg} alt="Order Separator" className="w-full h-full object-cover" />
            </div>
            <div>
              <h1 className="font-extrabold text-base text-white tracking-tight leading-tight">Order Separator</h1>
              <span className="text-[10px] font-bold text-indigo-400 tracking-wider uppercase">Gestão & Separação</span>
            </div>
          </div>

          {/* Navegação por Abas */}
          <nav className="space-y-1.5">
            <button
              onClick={() => setAbaAtiva('pedidos')}
              className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-medium transition-all ${
                abaAtiva === 'pedidos'
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-lg shadow-indigo-600/30 font-semibold'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4" />
                Painel de Pedidos
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${
                abaAtiva === 'pedidos' ? 'bg-indigo-950 text-indigo-200' : 'bg-slate-800 text-slate-400'
              }`}>
                {pedidos.length}
              </span>
            </button>

            <button
              onClick={prepararNovoPedido}
              className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-medium transition-all ${
                abaAtiva === 'novo-pedido'
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-lg shadow-indigo-600/30 font-semibold'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <PlusCircle className="w-4 h-4" />
              Lançar Pedido
            </button>

            <button
              onClick={() => setAbaAtiva('clientes')}
              className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-medium transition-all ${
                abaAtiva === 'clientes'
                  ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-lg shadow-indigo-600/30 font-semibold'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-3">
                <Users className="w-4 h-4" />
                Clientes & Pastas
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${
                abaAtiva === 'clientes' ? 'bg-indigo-950 text-indigo-200' : 'bg-slate-800 text-slate-400'
              }`}>
                {clientes.length}
              </span>
            </button>

            {/* Atalho Especial: Ferramentas CorelDRAW */}
            <div className="pt-3 border-t border-slate-800/80 space-y-2">
              <span className="px-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2">Ferramentas Corel</span>
              
              <button
                type="button"
                onClick={abrirMontadorCorel}
                title="Abrir Janelinha Flutuante do Montador de Folha no CorelDRAW (Imposição / Gang Sheet Automático)"
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-amber-500/10 to-orange-500/10 hover:from-amber-500/20 hover:to-orange-500/20 text-amber-300 border border-amber-600/30 hover:border-amber-500/50 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Grid className="w-4 h-4 text-amber-400 group-hover:rotate-12 transition-transform" />
                  <span>Montador de Folha</span>
                </div>
                <span className="text-[10px] font-black uppercase bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30">
                  Janela
                </span>
              </button>

              <button
                type="button"
                onClick={abrirVetorizadorCorel}
                title="Abrir Vetorizador Profissional de Imagens (Alta Precisão / Dual-Splines / IA) no CorelDRAW"
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-500/10 to-purple-500/10 hover:from-indigo-500/20 hover:to-purple-500/20 text-indigo-300 border border-indigo-600/30 hover:border-indigo-500/50 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Sparkles className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition-transform" />
                  <span>Vetorizador IA</span>
                </div>
                <span className="text-[10px] font-black uppercase bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-500/30">
                  Curvas
                </span>
              </button>

              <button
                type="button"
                onClick={abrirRemovedorCorel}
                title="Abrir Removedor de Fundo IA (U2-Net / Chroma Key / Prancheta Branca) no CorelDRAW"
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-500/10 to-teal-500/10 hover:from-emerald-500/20 hover:to-teal-500/20 text-emerald-300 border border-emerald-600/30 hover:border-emerald-500/50 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Scissors className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                  <span>Removedor IA</span>
                </div>
                <span className="text-[10px] font-black uppercase bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-500/30">
                  Fundo
                </span>
              </button>

              <button
                type="button"
                onClick={abrirUpscalerCorel}
                title="Abrir Upscaler IA Ultra HD (Real-ESRGAN 4x/8x / 300 DPI) no CorelDRAW"
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-sky-500/10 to-blue-500/10 hover:from-sky-500/20 hover:to-blue-500/20 text-sky-300 border border-sky-600/30 hover:border-sky-500/50 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Maximize2 className="w-4 h-4 text-sky-400 group-hover:scale-110 transition-transform" />
                  <span>Upscaler IA</span>
                </div>
                <span className="text-[10px] font-black uppercase bg-sky-500/20 text-sky-300 px-1.5 py-0.5 rounded border border-sky-500/30">
                  4x/8x
                </span>
              </button>

              <button
                type="button"
                onClick={() => setModalCalculadoraDTF(true)}
                title="Abrir Calculadora de Bobina DTF, Metragem Linear e Custos"
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-amber-500/10 to-orange-500/10 hover:from-amber-500/20 hover:to-orange-500/20 text-amber-300 border border-amber-600/30 hover:border-amber-500/50 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Calculator className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                  <span>Calculadora DTF</span>
                </div>
                <span className="text-[10px] font-black uppercase bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30">
                  Bobina
                </span>
              </button>
            </div>
          </nav>
        </div>

        {/* Rodapé da Sidebar */}
        <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-slate-800/80 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 font-medium">Fila Ativa:</span>
            <span className="text-indigo-400 font-bold font-mono">{metricas.totalPecasProducao} peças</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Aceleração IA:</span>
            <span className="text-sky-400 font-mono font-bold text-[11px] flex items-center gap-1">
              ⚡ RTX DirectML
            </span>
          </div>
          <div className="flex items-center gap-2 text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>App Local Conectado</span>
          </div>
        </div>
      </aside>

      {/* ================= ÁREA DE CONTEÚDO ================= */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Toast Notificação */}
        {notificacao && (
          <div className={`absolute top-4 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 text-sm font-medium border animate-in slide-in-from-top-4 duration-200 ${
            notificacao.tipo === 'sucesso'
              ? 'bg-emerald-950/95 text-emerald-200 border-emerald-700/80'
              : 'bg-red-950/95 text-red-200 border-red-700/80'
          }`}>
            {notificacao.tipo === 'sucesso' ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <AlertTriangle className="w-5 h-5 text-red-400" />}
            <span>{notificacao.mensagem}</span>
            <button onClick={() => setNotificacao(null)} className="ml-2 hover:opacity-70">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-8">
          {/* ================= ABA: PAINEL DE PEDIDOS ================= */}
          {abaAtiva === 'pedidos' && (
            <div className="space-y-6 max-w-6xl mx-auto">
              {/* Cabeçalho do Painel */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-black text-white tracking-tight">Painel Localizador de Pedidos</h2>
                  <p className="text-sm text-slate-400">Gerencie a produção e acesse as pastas físicas dos clientes no PC com 1 clique.</p>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                  <button
                    type="button"
                    onClick={abrirMontadorCorel}
                    className="flex items-center gap-2 px-3.5 py-2.5 bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/40 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer"
                  >
                    <Grid className="w-4 h-4 text-amber-400" />
                    Montador Corel
                  </button>
                  <button
                    type="button"
                    onClick={abrirVetorizadorCorel}
                    className="flex items-center gap-2 px-3.5 py-2.5 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/40 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer"
                  >
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    Vetorizador IA
                  </button>
                  <button
                    type="button"
                    onClick={abrirRemovedorCorel}
                    className="flex items-center gap-2 px-3.5 py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer"
                  >
                    <Scissors className="w-4 h-4 text-emerald-400" />
                    Removedor IA
                  </button>
                  <button
                    type="button"
                    onClick={abrirUpscalerCorel}
                    className="flex items-center gap-2 px-3.5 py-2.5 bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer"
                  >
                    <Maximize2 className="w-4 h-4 text-sky-400" />
                    Upscaler IA
                  </button>
                  <button
                    onClick={prepararNovoPedido}
                    className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition-all whitespace-nowrap cursor-pointer"
                  >
                    <PlusCircle className="w-4 h-4" />
                    Lançar Pedido
                  </button>
                </div>
              </div>

              {/* Cards de Métricas */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total de Pedidos</span>
                  <p className="text-2xl font-black text-white mt-1 font-mono">{metricas.total}</p>
                </div>
                <div className="bg-amber-950/30 border border-amber-800/40 rounded-2xl p-4">
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Aguardando Produção</span>
                  <p className="text-2xl font-black text-amber-300 mt-1 font-mono">{metricas.aguardando}</p>
                </div>
                <div className="bg-blue-950/30 border border-blue-800/40 rounded-2xl p-4">
                  <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Em Produção</span>
                  <p className="text-2xl font-black text-blue-300 mt-1 font-mono">{metricas.emProducao}</p>
                </div>
                <div className="bg-emerald-950/30 border border-emerald-800/40 rounded-2xl p-4">
                  <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Prontos / Entregues</span>
                  <p className="text-2xl font-black text-emerald-300 mt-1 font-mono">{metricas.concluidos}</p>
                </div>
              </div>

              {/* Barra de Filtros e Busca */}
              <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-3 flex flex-col md:flex-row items-center justify-between gap-3">
                {/* Abas de Status */}
                <div className="flex flex-wrap gap-1.5 w-full md:w-auto">
                  {['Todos', 'Aguardando Produção', 'Em Produção', 'Pronto', 'Entregue'].map(st => (
                    <button
                      key={st}
                      onClick={() => setFiltroStatus(st)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        filtroStatus === st
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>

                {/* Input de Busca */}
                <div className="relative w-full md:w-72">
                  <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    value={busca}
                    onChange={(e) => setBusca(e.target.value)}
                    placeholder="Buscar pedido, cliente ou arte..."
                    className="w-full pl-9 pr-4 py-1.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                  {busca && (
                    <button onClick={() => setBusca('')} className="absolute right-2.5 top-2 text-slate-500 hover:text-slate-300">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Lista de Pedidos */}
              {pedidosFiltrados.length === 0 ? (
                <div className="border border-dashed border-slate-800 rounded-3xl p-14 text-center bg-slate-900/30">
                  <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-300 font-bold text-base">Nenhum pedido encontrado</p>
                  <p className="text-slate-500 text-sm mt-1 max-w-sm mx-auto">
                    {busca || filtroStatus !== 'Todos'
                      ? 'Nenhum resultado corresponde aos filtros aplicados.'
                      : 'Cadastre seus clientes e lance seus pedidos para acompanhar toda a estamparia.'}
                  </p>
                  {pedidos.length === 0 && (
                    <button
                      onClick={prepararNovoPedido}
                      className="mt-5 px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 transition-all"
                    >
                      Criar Primeiro Pedido
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid gap-4">
                  {pedidosFiltrados.map((pedido) => {
                    const statusInfo = STATUS_OPCOES.find(s => s.id === pedido.status) || STATUS_OPCOES[0];
                    const StatusIcon = statusInfo.icon;

                    return (
                      <div 
                        key={pedido.id}
                        className="bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 transition-all shadow-md flex flex-col md:flex-row justify-between md:items-center gap-5"
                      >
                        <div className="space-y-3 flex-1">
                          {/* Cabeçalho do Card */}
                          <div className="flex flex-wrap items-center gap-2.5">
                            <span className="text-indigo-400 font-mono font-black text-lg bg-indigo-950/80 border border-indigo-800/80 px-2.5 py-0.5 rounded-lg shadow-sm">
                              #{pedido.numeroPedido}
                            </span>
                            <span className="text-white font-bold text-base">{pedido.clienteNome}</span>
                            {pedido.clienteLoja && (
                              <span className="text-xs bg-slate-800/90 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700 font-medium">
                                {pedido.clienteLoja}
                              </span>
                            )}

                            {/* Badge Seletor Rápido de Status */}
                            <select
                              value={pedido.status || 'Aguardando Produção'}
                              onChange={(e) => mudarStatusPedido(pedido.id, e.target.value)}
                              className={`text-xs font-semibold px-2.5 py-1 rounded-lg border focus:outline-none cursor-pointer ${statusInfo.bg} ${statusInfo.text} ${statusInfo.border}`}
                            >
                              {STATUS_OPCOES.map(opt => (
                                <option key={opt.id} value={opt.id} className="bg-slate-900 text-slate-200">
                                  {opt.label}
                                </option>
                              ))}
                            </select>

                            <span className="text-xs bg-indigo-950/80 text-indigo-300 border border-indigo-800 px-2.5 py-1 rounded-full font-bold ml-auto md:ml-0">
                              {pedido.totalPecas} Peças
                            </span>
                          </div>

                          {/* Detalhes Técnicos */}
                          <div className="text-xs text-slate-300 flex flex-wrap items-center gap-y-1.5 gap-x-3.5 bg-slate-950/50 p-2.5 rounded-xl border border-slate-800/60">
                            <span className="flex items-center gap-1.5">
                              <Palette className="w-3.5 h-3.5 text-indigo-400" />
                              <strong className="text-slate-400">Estampa:</strong> {pedido.descricaoEstampa || 'Sem descrição'}
                            </span>
                            <span className="text-slate-700">•</span>
                            <span>
                              <strong className="text-slate-400">Posição:</strong> {pedido.posicaoEstampa}
                            </span>
                            <span className="text-slate-700">•</span>
                            <span>
                              <strong className="text-slate-400">Tecido:</strong> {pedido.tipoTecido} ({pedido.corTecido})
                            </span>
                            {pedido.dataEntrega && (
                              <>
                                <span className="text-slate-700">•</span>
                                <span className="flex items-center gap-1 text-slate-300">
                                  <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                                  <strong className="text-slate-400">Entrega:</strong> {formatarDataBR(pedido.dataEntrega)}
                                </span>
                              </>
                            )}
                          </div>

                          {/* Grade Quantitativa */}
                          <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider mr-1">Grade:</span>
                            {Object.entries(pedido.grade || {})
                              .filter(([_, qtd]) => Number(qtd) > 0)
                              .map(([tam, qtd]) => (
                                <div 
                                  key={tam} 
                                  className="px-2.5 py-1 rounded-lg text-xs font-mono font-bold border bg-indigo-950/80 text-indigo-300 border-indigo-700/60 shadow-sm"
                                >
                                  {tam}: {qtd}
                                </div>
                              ))}
                            {Object.values(pedido.grade || {}).every(q => Number(q) <= 0) && (
                              <span className="text-xs text-slate-500 italic">Sem peças</span>
                            )}
                          </div>

                          {/* Miniaturas das Imagens da Estampa no Card */}
                          {Array.isArray(pedido.imagens) && pedido.imagens.length > 0 && (
                            <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/60 mt-1">
                              <div className="flex items-center gap-2 overflow-x-auto py-1">
                                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mr-1 flex items-center gap-1 flex-shrink-0">
                                  <ImageIcon className="w-3.5 h-3.5 text-indigo-400" /> Artes:
                                </span>
                                {pedido.imagens.map((img, idx) => (
                                  <button
                                    key={idx}
                                    type="button"
                                    onClick={() => setImagemModal(img)}
                                    className="group relative w-12 h-12 rounded-lg overflow-hidden border border-slate-700 bg-slate-950 hover:border-indigo-500 transition-all flex-shrink-0 shadow-sm"
                                    title={`Ver arte: ${img.nome || 'Estampa'}`}
                                  >
                                    <img 
                                      src={img.preview || img.caminhoSalvo || img.caminho} 
                                      alt={img.nome || 'Estampa'} 
                                      className="w-full h-full object-cover group-hover:scale-110 transition-transform"
                                    />
                                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                      <Eye className="w-3.5 h-3.5 text-white" />
                                    </div>
                                  </button>
                                ))}
                              </div>

                              {/* Ações Rápidas de IA para a Arte deste Pedido */}
                              <div className="flex items-center gap-1.5 ml-auto">
                                <button
                                  type="button"
                                  onClick={() => {
                                    const img = pedido.imagens[0];
                                    const p = img.caminhoSalvo || img.caminho;
                                    abrirRemovedorCorel(p);
                                  }}
                                  className="flex items-center gap-1 px-2.5 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 rounded-xl text-[11px] font-bold transition-all shadow-sm"
                                  title="Recortar Fundo IA da arte deste pedido"
                                >
                                  <Scissors className="w-3 h-3" />
                                  <span>Recortar IA</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    const img = pedido.imagens[0];
                                    const p = img.caminhoSalvo || img.caminho;
                                    abrirUpscalerCorel(p);
                                  }}
                                  className="flex items-center gap-1 px-2.5 py-1.5 bg-sky-500/10 hover:bg-sky-500/25 text-sky-400 border border-sky-500/30 rounded-xl text-[11px] font-bold transition-all shadow-sm"
                                  title="Aumentar resolução (300 DPI) com IA"
                                >
                                  <Maximize2 className="w-3 h-3" />
                                  <span>Upscale 4x</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    const img = pedido.imagens[0];
                                    const p = img.caminhoSalvo || img.caminho;
                                    abrirVetorizadorCorel(p);
                                  }}
                                  className="flex items-center gap-1 px-2.5 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/25 text-indigo-400 border border-indigo-500/30 rounded-xl text-[11px] font-bold transition-all shadow-sm"
                                  title="Converter arte deste pedido em vetor SVG"
                                >
                                  <Sparkles className="w-3 h-3" />
                                  <span>Vetorizar</span>
                                </button>
                              </div>
                            </div>
                          )}

                          {pedido.observacoes && (
                            <p className="text-xs text-slate-400 italic bg-slate-950/40 px-3 py-1.5 rounded-lg border border-slate-800/60">
                              Obs: {pedido.observacoes}
                            </p>
                          )}
                        </div>

                        {/* Botões de Ação */}
                        <div className="flex flex-col items-stretch gap-2 border-t md:border-t-0 md:border-l pt-3 md:pt-0 md:pl-5 border-slate-800 shrink-0 w-full md:w-56">
                          {/* Ações CorelDRAW */}
                          <div className="grid grid-cols-1 gap-1.5">
                            <button
                              onClick={() => carimbarNoCorelDRAW(pedido)}
                              disabled={enviandoCorel === pedido.id}
                              title="Carimbar a ficha técnica e grade de tamanhos na arte aberta do CorelDRAW"
                              className="flex items-center justify-center gap-2 px-3 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white text-xs font-bold rounded-xl shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
                            >
                              <Printer className="w-3.5 h-3.5 text-emerald-200" />
                              {enviandoCorel === pedido.id ? 'Carimbando...' : 'Carimbar no Corel'}
                            </button>

                            <button
                              onClick={abrirMontadorCorel}
                              title="Abrir Janela do Montador de Folha no CorelDRAW (Imposição / Gang Sheet)"
                              className="flex items-center justify-center gap-2 px-3 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white text-xs font-bold rounded-xl shadow-md shadow-amber-600/20 transition-all cursor-pointer"
                            >
                              <Grid className="w-3.5 h-3.5 text-amber-200" />
                              Montar Folha
                            </button>
                          </div>

                          {/* Ações Operacionais */}
                          <div className="grid grid-cols-2 gap-1.5">
                            <button
                              onClick={() => setModalFicha(pedido)}
                              title="Visualizar e imprimir ficha de produção / ordem de serviço em papel A4"
                              className="flex items-center justify-center gap-1.5 px-2 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold rounded-xl border border-slate-700 transition-all cursor-pointer"
                            >
                              <FileText className="w-3.5 h-3.5 text-indigo-400" />
                              Ficha OS
                            </button>

                            <button
                              onClick={() => abrirCalculadoraParaPedido(pedido)}
                              title="Calcular metragem na bobina DTF 58cm e custo de insumos"
                              className="flex items-center justify-center gap-1.5 px-2 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold rounded-xl border border-slate-700 transition-all cursor-pointer"
                            >
                              <Calculator className="w-3.5 h-3.5 text-amber-400" />
                              Bobina DTF
                            </button>
                          </div>

                          <div className="grid grid-cols-2 gap-1.5">
                            <button
                              onClick={() => criarPastaProjeto(pedido)}
                              title="Criar pasta organizada do pedido, copiar imagens e abrir no Explorer"
                              className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 bg-indigo-950/60 hover:bg-indigo-900/80 text-indigo-300 text-[11px] font-semibold rounded-xl border border-indigo-700/50 transition-all"
                            >
                              <FolderPlus className="w-3.5 h-3.5 text-indigo-400" />
                              Pasta
                            </button>

                            <button
                              onClick={() => abrirSeparacao(pedido)}
                              title="Abrir checklist de separação das peças por tamanho"
                              className="flex items-center justify-center gap-1.5 px-2.5 py-1.5 bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 text-[11px] font-semibold rounded-xl border border-cyan-700/50 transition-all"
                            >
                              <CheckSquare className="w-3.5 h-3.5 text-cyan-400" />
                              Separar
                            </button>
                          </div>

                          {/* Barra de Ações Rápidas: Editar, Duplicar, Excluir */}
                          <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 px-1">
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => iniciarEdicaoPedido(pedido)}
                                title="Editar dados e grade deste pedido"
                                className="p-1.5 text-slate-400 hover:text-indigo-300 hover:bg-indigo-950/60 rounded-lg transition-colors"
                              >
                                <Edit3 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => duplicarPedido(pedido)}
                                title="Duplicar pedido com novo número"
                                className="p-1.5 text-slate-400 hover:text-amber-300 hover:bg-amber-950/60 rounded-lg transition-colors"
                              >
                                <Copy className="w-3.5 h-3.5" />
                              </button>
                            </div>

                            <button
                              onClick={() => confirmarExcluirPedido(pedido)}
                              title="Remover pedido do painel"
                              className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-950/40 rounded-lg transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ================= ABA: NOVO PEDIDO COM GRADE ================= */}
          {abaAtiva === 'novo-pedido' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-black text-white tracking-tight">
                      {modoEdicaoId ? `Editando Pedido #${pedidoForm.numeroPedido}` : 'Lançamento de Pedido de Estamparia'}
                    </h2>
                    {modoEdicaoId && (
                      <span className="text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2.5 py-1 rounded-lg">
                        MODO EDIÇÃO
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-400">
                    {modoEdicaoId 
                      ? 'Atualize os dados técnicos ou quantidades da grade deste pedido.' 
                      : 'Preencha os dados técnicos da arte e a grade quantitativa para produção.'}
                  </p>
                </div>
                {modoEdicaoId && (
                  <button
                    type="button"
                    onClick={prepararNovoPedido}
                    className="self-start sm:self-auto px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-colors"
                  >
                    Cancelar Edição (Novo Pedido)
                  </button>
                )}
              </div>

              {clientes.length === 0 ? (
                <div className="bg-amber-950/40 border border-amber-800/60 rounded-3xl p-8 text-center space-y-4">
                  <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto" />
                  <h3 className="font-bold text-amber-200 text-lg">Nenhum cliente cadastrado ainda!</h3>
                  <p className="text-sm text-amber-300/80 max-w-md mx-auto">
                    Para vincular a pasta física no seu computador e salvar os arquivos de pedidos, cadastre o primeiro cliente.
                  </p>
                  <button
                    onClick={() => setAbaAtiva('clientes')}
                    className="px-6 py-2.5 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-sm font-semibold transition-colors shadow-lg"
                  >
                    Cadastrar Cliente Agora
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSalvarPedido} className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-6 shadow-2xl">
                  {/* Cabeçalho */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Número do Pedido</label>
                      <div className="relative">
                        <Hash className="absolute left-3 top-3 w-4 h-4 text-indigo-400" />
                        <input
                          type="text"
                          required
                          value={pedidoForm.numeroPedido}
                          onChange={(e) => setPedidoForm({ ...pedidoForm, numeroPedido: e.target.value })}
                          className="w-full pl-9 pr-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-indigo-400 font-mono font-black focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Cliente Cadastrado</label>
                      <select
                        required
                        value={pedidoForm.clienteId}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, clienteId: e.target.value })}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                      >
                        <option value="">Selecione o Cliente...</option>
                        {clientes.map(c => (
                          <option key={c.id} value={c.id}>
                            {c.nome} {c.loja ? `(${c.loja})` : ''}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Previsão de Entrega</label>
                      <input
                        type="date"
                        value={pedidoForm.dataEntrega}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, dataEntrega: e.target.value })}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  {/* Detalhes da Estampa */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <div className="md:col-span-2">
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Nome / Descrição da Estampa</label>
                      <input
                        type="text"
                        required
                        placeholder="Ex: Estampa Caveira Surfista 3 Cores Silk Screen"
                        value={pedidoForm.descricaoEstampa}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, descricaoEstampa: e.target.value })}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Posição da Estampa</label>
                      <select
                        value={pedidoForm.posicaoEstampa}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, posicaoEstampa: e.target.value })}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                      >
                        <option value="Frente">Frente</option>
                        <option value="Costas">Costas</option>
                        <option value="Frente + Costas">Frente + Costas</option>
                        <option value="Peito Esquerdo">Peito Esquerdo</option>
                        <option value="Manga">Manga</option>
                        <option value="Personalizado">Personalizado</option>
                      </select>
                    </div>
                  </div>

                  {/* Tecido & Cor */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Tipo de Tecido / Malha</label>
                      <input
                        type="text"
                        placeholder="Ex: Algodão Fio 30.1, Poliéster, Dry-Fit..."
                        value={pedidoForm.tipoTecido}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, tipoTecido: e.target.value })}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Cor da Peça</label>
                      <input
                        type="text"
                        placeholder="Ex: Preta, Branca, Mescla..."
                        value={pedidoForm.corTecido}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, corTecido: e.target.value })}
                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  {/* Grade Quantitativa com Botões + e - */}
                  <div className="border border-slate-800 bg-slate-950/70 p-6 rounded-2xl space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Layers className="w-5 h-5 text-indigo-400" />
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Grade de Peças por Tamanho</h3>
                      </div>
                      <span className="text-sm font-black text-indigo-400 bg-indigo-950/80 px-4 py-1 rounded-full border border-indigo-800/80 font-mono">
                        Total: {totalPecas} Peças
                      </span>
                    </div>

                    <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-8 gap-2.5 pt-2">
                      {TAMANHOS_PADRAO.map((tamanho) => (
                        <div key={tamanho} className="bg-slate-900 border border-slate-700/80 rounded-2xl p-2.5 text-center transition-all focus-within:border-indigo-500">
                          <label className="block text-xs font-black text-slate-300 mb-1.5">{tamanho}</label>
                          <input
                            type="number"
                            min="0"
                            value={pedidoForm.grade[tamanho] ?? 0}
                            onChange={(e) => setPedidoForm({
                              ...pedidoForm,
                              grade: {
                                ...pedidoForm.grade,
                                [tamanho]: Math.max(0, parseInt(e.target.value, 10) || 0)
                              }
                            })}
                            className="w-full text-center bg-slate-950 border border-slate-700 rounded-xl py-1.5 text-lg font-black text-white focus:outline-none focus:border-indigo-500 font-mono"
                          />
                          <div className="flex gap-1 mt-1.5 justify-center">
                            <button
                              type="button"
                              onClick={() => alterarQtdGrade(tamanho, -1)}
                              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-bold"
                            >
                              -
                            </button>
                            <button
                              type="button"
                              onClick={() => alterarQtdGrade(tamanho, 1)}
                              className="px-2 py-0.5 bg-indigo-900/60 hover:bg-indigo-800 text-indigo-300 rounded text-xs font-bold"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Imagens da Estampa / Mockups */}
                  <div className="border border-slate-800 bg-slate-950/70 p-6 rounded-2xl space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 bg-indigo-950/80 rounded-xl border border-indigo-800/60">
                          <ImageIcon className="w-5 h-5 text-indigo-400" />
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Imagens da Estampa / Mockup da Peça</h3>
                          <p className="text-xs text-slate-400">Anexe as fotos da arte (frente, costas, manga ou simulação) para controle de produção.</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={escolherImagensEstampa}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-indigo-600/20 transition-all self-start sm:self-auto cursor-pointer"
                      >
                        <ImagePlus className="w-4 h-4" />
                        Anexar Imagens...
                      </button>
                    </div>

                    {pedidoForm.imagens.length === 0 ? (
                      <div 
                        onClick={escolherImagensEstampa}
                        className="border border-dashed border-slate-800 hover:border-slate-700/80 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-900/40 group"
                      >
                        <ImagePlus className="w-8 h-8 text-slate-600 group-hover:text-indigo-400 mx-auto mb-2 transition-colors" />
                        <p className="text-xs text-slate-300 font-semibold">Nenhuma imagem anexada ainda</p>
                        <p className="text-[11px] text-slate-500 mt-0.5">Clique aqui para selecionar arquivos de imagem do seu computador (JPG, PNG, WEBP, BMP)</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
                        {pedidoForm.imagens.map((img, idx) => (
                          <div key={idx} className="group relative bg-slate-900 border border-slate-800 hover:border-indigo-600/60 rounded-xl overflow-hidden shadow-sm flex flex-col transition-all">
                            <div className="h-32 bg-[#050811] flex items-center justify-center overflow-hidden relative">
                              <img 
                                src={img.preview || img.caminho} 
                                alt={img.nome} 
                                className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-200"
                              />
                              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => setImagemModal(img)}
                                  className="p-2 bg-slate-900/90 text-white rounded-lg hover:bg-indigo-600 transition-colors shadow"
                                  title="Visualizar em tamanho grande"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => removerImagemEstampa(idx)}
                                  className="p-2 bg-red-900/90 text-white rounded-lg hover:bg-red-600 transition-colors shadow"
                                  title="Remover imagem"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                            <span className="p-2 text-[11px] font-mono text-slate-300 truncate bg-slate-950/80 border-t border-slate-800" title={img.nome}>
                              {img.nome}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Observações */}
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Instruções de Impressão / Cores Pantone / Observações</label>
                    <textarea
                      rows="3"
                      placeholder="Instruções de tintas, telas de seda, temperatura de cura ou especificações do cliente..."
                      value={pedidoForm.observacoes}
                      onChange={(e) => setPedidoForm({ ...pedidoForm, observacoes: e.target.value })}
                      className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    ></textarea>
                  </div>

                  {/* Botões do Rodapé */}
                  <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-800">
                    <p className="text-xs text-slate-500">
                      💾 Ao clicar em salvar, um arquivo <code className="text-indigo-400 font-mono font-bold">pedido_#{pedidoForm.numeroPedido}.json</code> será gravado na pasta do cliente.
                    </p>

                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => setAbaAtiva('pedidos')}
                        className="px-5 py-2.5 bg-slate-800 text-slate-300 rounded-xl text-sm font-semibold hover:bg-slate-700 transition-colors"
                      >
                        Cancelar
                      </button>
                      <button
                        type="submit"
                        className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
                      >
                        <Save className="w-4 h-4" />
                        {modoEdicaoId ? 'Atualizar Pedido no PC' : 'Salvar Pedido & Gravar no PC'}
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </div>
          )}

          {/* ================= ABA: CLIENTES & DIRETÓRIOS ================= */}
          {abaAtiva === 'clientes' && (
            <div className="max-w-5xl mx-auto space-y-8">
              <div>
                <h2 className="text-2xl font-black text-white tracking-tight">Cadastro de Clientes e Pastas</h2>
                <p className="text-sm text-slate-400">Vincule cada cliente ao seu diretório correspondente no Windows para gravação direta de pedidos e artes.</p>
              </div>

              {/* Formulário de Novo Cliente */}
              <form onSubmit={handleSalvarCliente} className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 md:p-8 space-y-5 shadow-2xl">
                <h3 className="text-sm font-black text-slate-200 uppercase tracking-wider">Novo Cliente</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Nome do Cliente / Responsável *</label>
                    <input
                      type="text"
                      required
                      placeholder="Ex: João da Silva"
                      value={clienteForm.nome}
                      onChange={(e) => setClienteForm({ ...clienteForm, nome: e.target.value })}
                      className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">Nome da Loja / Marca</label>
                    <input
                      type="text"
                      placeholder="Ex: Streetwear Co."
                      value={clienteForm.loja}
                      onChange={(e) => setClienteForm({ ...clienteForm, loja: e.target.value })}
                      className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">WhatsApp / Telefone</label>
                    <input
                      type="text"
                      placeholder="(11) 99999-9999"
                      value={clienteForm.telefone}
                      onChange={(e) => setClienteForm({ ...clienteForm, telefone: e.target.value })}
                      className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                {/* Seleção do Diretório */}
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                    Diretório da Pasta no Computador (Onde ficam as artes e pedidos) *
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      required
                      readOnly
                      placeholder="Clique em 'Selecionar Pasta' para escolher o caminho no seu PC..."
                      value={clienteForm.pastaDiretorio}
                      onClick={escolherPastaCliente}
                      className="flex-1 px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-sm text-slate-300 font-mono focus:outline-none cursor-pointer"
                    />
                    <button
                      type="button"
                      onClick={escolherPastaCliente}
                      className="flex items-center gap-2 px-5 py-2.5 bg-indigo-950/60 hover:bg-indigo-900/80 text-indigo-300 text-sm font-semibold rounded-xl border border-indigo-700/50 transition-colors shadow-sm"
                    >
                      <FolderSync className="w-4 h-4 text-indigo-400" />
                      Selecionar Pasta...
                    </button>
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition-all"
                  >
                    <PlusCircle className="w-4 h-4" />
                    Cadastrar Cliente
                  </button>
                </div>
              </form>

              {/* Lista de Clientes Cadastrados */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-black text-slate-400 uppercase tracking-wider">
                    Clientes Cadastrados ({clientes.length})
                  </h3>
                  <button 
                    onClick={carregarDados}
                    className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1 transition-colors"
                  >
                    <RefreshCw className="w-3.5 h-3.5" /> Atualizar lista
                  </button>
                </div>

                {clientes.length === 0 ? (
                  <div className="p-10 text-center border border-dashed border-slate-800 rounded-2xl text-slate-500 text-sm">
                    Nenhum cliente cadastrado no momento.
                  </div>
                ) : (
                  <div className="grid gap-3">
                    {clientes.map(c => {
                      const pedidosDoCliente = pedidos.filter(p => p.clienteId === c.id || p.clienteNome === c.nome);
                      const iniciais = c.nome ? c.nome.slice(0, 2).toUpperCase() : 'CL';

                      return (
                        <div key={c.id} className="bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 p-5 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all shadow-sm">
                          <div className="flex items-center gap-4">
                            {/* Avatar */}
                            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-600/20 border border-indigo-700/30 flex items-center justify-center font-black text-indigo-400 text-base shadow-sm">
                              {iniciais}
                            </div>

                            <div className="space-y-1">
                              <div className="flex items-center gap-3">
                                <span className="font-bold text-white text-base">{c.nome}</span>
                                {c.loja && (
                                  <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-0.5 rounded-md border border-slate-700 font-medium">
                                    {c.loja}
                                  </span>
                                )}
                                <span className="text-xs text-slate-400 font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                                  {pedidosDoCliente.length} pedidos
                                </span>
                              </div>

                              <p className="text-xs text-slate-400 font-mono flex items-center gap-1.5 bg-slate-950/70 px-2.5 py-1 rounded-lg border border-slate-800/80">
                                <FolderOpen className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                                {c.pastaDiretorio}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 self-end md:self-center">
                            {c.telefone && (
                              <a
                                href={`https://wa.me/55${c.telefone.replace(/\D/g, '')}`}
                                target="_blank"
                                rel="noreferrer"
                                title="Conversar no WhatsApp"
                                className="flex items-center gap-1.5 px-3 py-2 bg-emerald-950/50 hover:bg-emerald-900/60 text-emerald-300 text-xs font-semibold rounded-xl border border-emerald-700/40 transition-colors"
                              >
                                <MessageCircle className="w-4 h-4 text-emerald-400" />
                                WhatsApp
                              </a>
                            )}

                            <button
                              onClick={() => abrirNoExplorer(c.pastaDiretorio)}
                              className="flex items-center gap-2 px-3.5 py-2 bg-indigo-950/50 hover:bg-indigo-900/60 text-indigo-300 hover:text-indigo-200 text-xs font-semibold rounded-xl border border-indigo-700/40 transition-colors shadow-sm"
                            >
                              <FolderOpen className="w-4 h-4 text-indigo-400" />
                              Abrir Pasta
                            </button>

                            <button
                              onClick={() => confirmarExcluirCliente(c)}
                              title="Remover cliente"
                              className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-950/40 rounded-lg transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
