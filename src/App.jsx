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
  { id: 'Aguardando Produção', label: 'Aguardando', icon: Clock, dot: 'bg-amber-400', bg: 'bg-amber-500/10', text: 'text-amber-300', border: 'border-amber-500/30' },
  { id: 'Em Produção', label: 'Em Produção', icon: Scissors, dot: 'bg-sky-400', bg: 'bg-sky-500/10', text: 'text-sky-300', border: 'border-sky-500/30' },
  { id: 'Pronto', label: 'Pronto', icon: CheckCircle2, dot: 'bg-emerald-400', bg: 'bg-emerald-500/10', text: 'text-emerald-300', border: 'border-emerald-500/30' },
  { id: 'Entregue', label: 'Entregue', icon: Truck, dot: 'bg-zinc-400', bg: 'bg-zinc-500/10', text: 'text-zinc-400', border: 'border-zinc-500/30' }
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
    const caminhoValido = typeof caminhoImagem === 'string' && caminhoImagem.trim() ? caminhoImagem.trim() : null;
    if (!window.electronAPI || !window.electronAPI.abrirVetorizadorCorel) {
      avisar('erro', 'Vetorizador CorelDRAW indisponível.');
      return;
    }
    avisar('sucesso', 'Abrindo janela do Vetorizador Profissional...');
    try {
      const res = await window.electronAPI.abrirVetorizadorCorel(caminhoValido);
      if (!res.sucesso) {
        avisar('erro', `Falha ao abrir vetorizador: ${res.erro}`);
      }
    } catch (e) {
      avisar('erro', 'Erro ao abrir vetorizador: ' + e.message);
    }
  };

  // Abrir Removedor de Fundo IA CorelDRAW
  const abrirRemovedorCorel = async (caminhoImagem = null) => {
    const caminhoValido = typeof caminhoImagem === 'string' && caminhoImagem.trim() ? caminhoImagem.trim() : null;
    if (!window.electronAPI || !window.electronAPI.abrirRemovedorCorel) {
      avisar('erro', 'Removedor de Fundo CorelDRAW indisponível.');
      return;
    }
    avisar('sucesso', 'Abrindo janela do Removedor de Fundo IA...');
    try {
      const res = await window.electronAPI.abrirRemovedorCorel(caminhoValido);
      if (!res.sucesso) {
        avisar('erro', `Falha ao abrir removedor: ${res.erro}`);
      }
    } catch (e) {
      avisar('erro', 'Erro ao abrir removedor: ' + e.message);
    }
  };

  // Abrir Upscaler IA Ultra HD CorelDRAW
  const abrirUpscalerCorel = async (caminhoImagem = null) => {
    const caminhoValido = typeof caminhoImagem === 'string' && caminhoImagem.trim() ? caminhoImagem.trim() : null;
    if (!window.electronAPI || !window.electronAPI.abrirUpscalerCorel) {
      avisar('erro', 'Upscaler IA CorelDRAW indisponível.');
      return;
    }
    avisar('sucesso', 'Abrindo janela do Upscaler IA Ultra HD...');
    try {
      const res = await window.electronAPI.abrirUpscalerCorel(caminhoValido);
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
        (p.descricaoEstampa && p.descricaoEstampa.toLowerCase().includes(termo)) ||
        (p.tipoTecido && p.tipoTecido.toLowerCase().includes(termo)) ||
        (p.corTecido && p.corTecido.toLowerCase().includes(termo)) ||
        (p.posicaoEstampa && p.posicaoEstampa.toLowerCase().includes(termo)) ||
        (p.observacoes && p.observacoes.toLowerCase().includes(termo))
      );
    });
  }, [pedidos, busca, filtroStatus]);

  return (
    <div className="flex h-screen bg-[#0b0d11] text-zinc-100 font-sans overflow-hidden">
      {/* ================= MODAL DE CONFIRMAÇÃO SEGURO ================= */}
      {modalConfirmacao && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-[#13151b] border border-zinc-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-amber-400">
              <div className="p-2 bg-amber-500/10 rounded-xl border border-amber-500/20">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-base text-zinc-100">{modalConfirmacao.titulo}</h3>
            </div>
            <p className="text-sm text-zinc-400 leading-relaxed">
              {modalConfirmacao.mensagem}
            </p>
            <div className="flex justify-end gap-2.5 pt-3 border-t border-zinc-800/80">
              <button
                onClick={() => setModalConfirmacao(null)}
                className="px-4 py-2 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 text-xs font-medium rounded-xl transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={modalConfirmacao.acaoConfirmar}
                className="px-4 py-2 bg-red-600/90 hover:bg-red-600 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors"
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
          <div className="relative max-w-4xl max-h-[90vh] bg-[#13151b] border border-zinc-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-zinc-800 bg-[#0e1015]">
              <span className="text-xs font-semibold text-zinc-200 font-mono flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-zinc-400" />
                {imagemModal.nome || 'Arte da Estampa'}
              </span>
              <button 
                onClick={() => setImagemModal(null)}
                className="p-1 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-6 flex items-center justify-center overflow-auto max-h-[72vh] bg-[#0b0d11]">
              <img 
                src={imagemModal.preview || imagemModal.caminhoSalvo || imagemModal.caminho} 
                alt="Arte da Estampa" 
                className="max-h-[68vh] max-w-full object-contain rounded-lg border border-zinc-800/80"
              />
            </div>
            <div className="px-5 py-3 bg-[#0e1015] flex flex-wrap items-center justify-between gap-3 border-t border-zinc-800">
              <div className="text-xs text-zinc-500 font-mono truncate max-w-xs md:max-w-md">
                {imagemModal.caminho || imagemModal.caminhoSalvo || 'Arte da Estampa'}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const p = imagemModal.caminhoSalvo || imagemModal.caminho;
                    abrirRemovedorCorel(p);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-200 border border-zinc-700/60 rounded-lg text-xs font-medium transition-colors"
                  title="Abrir esta imagem diretamente no Removedor de Fundo IA"
                >
                  <Scissors className="w-3.5 h-3.5 text-emerald-400" />
                  Recortar IA
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = imagemModal.caminhoSalvo || imagemModal.caminho;
                    abrirUpscalerCorel(p);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-200 border border-zinc-700/60 rounded-lg text-xs font-medium transition-colors"
                  title="Aumentar para Ultra HD 300 DPI com IA"
                >
                  <Maximize2 className="w-3.5 h-3.5 text-sky-400" />
                  Upscale 4x
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = imagemModal.caminhoSalvo || imagemModal.caminho;
                    abrirVetorizadorCorel(p);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-200 border border-zinc-700/60 rounded-lg text-xs font-medium transition-colors"
                  title="Converter para curvas SVG com IA"
                >
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
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
          <div className="bg-[#13151b] border border-zinc-800 rounded-2xl p-6 md:p-7 max-w-2xl w-full shadow-2xl space-y-5">
            <div className="flex items-start justify-between border-b border-zinc-800/80 pb-4">
              <div>
                <div className="flex items-center gap-2.5">
                  <span className="text-zinc-200 font-mono font-bold text-sm bg-zinc-900 border border-zinc-700/80 px-2.5 py-1 rounded-lg">
                    #{modalSeparacao.numeroPedido}
                  </span>
                  <h3 className="font-bold text-lg text-zinc-100">Checklist de Separação</h3>
                </div>
                <p className="text-xs text-zinc-400 mt-1.5">
                  Cliente: <strong className="text-zinc-200">{modalSeparacao.clienteNome}</strong> • Estampa: <strong className="text-zinc-200">{modalSeparacao.descricaoEstampa || 'Sem descrição'}</strong>
                </p>
                <p className="text-xs text-zinc-500 mt-0.5">
                  Tecido: <strong className="text-zinc-300">{modalSeparacao.tipoTecido} ({modalSeparacao.corTecido})</strong> • Posição: <strong className="text-zinc-300">{modalSeparacao.posicaoEstampa}</strong>
                </p>
              </div>
              <button
                onClick={() => setModalSeparacao(null)}
                className="p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
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
                  <div className="bg-zinc-950/70 p-3.5 rounded-xl border border-zinc-800/80 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-zinc-400">Progresso de Separação:</span>
                      <span className="text-zinc-200 font-mono font-semibold">{qtdConferidos} de {totalTamanhos} conferidos ({porcentagem}%)</span>
                    </div>
                    <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-300 ${todosConferidos ? 'bg-emerald-500' : 'bg-blue-600'}`}
                        style={{ width: `${porcentagem}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Grade de Separação com Checkboxes */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5 max-h-[40vh] overflow-y-auto pr-1">
                    {tamanhosComPecas.map(([tam, qtd]) => {
                      const conferido = !!checksDoPedido[tam];
                      return (
                        <button
                          key={tam}
                          type="button"
                          onClick={() => alternarItemSeparado(modalSeparacao.id, tam)}
                          className={`p-3 rounded-xl border flex flex-col items-center justify-between gap-2 transition-all cursor-pointer ${
                            conferido 
                              ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300' 
                              : 'bg-zinc-950/60 border-zinc-800 text-zinc-300 hover:border-zinc-700'
                          }`}
                        >
                          <div className="flex items-center justify-between w-full">
                            <span className="text-xs font-mono font-bold uppercase">{tam}</span>
                            <div className={`w-4 h-4 rounded flex items-center justify-center border ${
                              conferido ? 'bg-emerald-600 border-emerald-500 text-white' : 'border-zinc-700 bg-zinc-900'
                            }`}>
                              {conferido && <CheckCircle className="w-3 h-3" />}
                            </div>
                          </div>
                          <span className="text-xl font-bold font-mono">{qtd}</span>
                          <span className="text-[10px] uppercase font-medium text-zinc-500">peças</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Botões do Rodapé do Modal */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-zinc-800">
                    <span className="text-xs text-zinc-400 font-mono">
                      Total: <strong className="text-zinc-200">{modalSeparacao.totalPecas} peças</strong>
                    </span>
                    <div className="flex gap-2 w-full sm:w-auto">
                      <button
                        type="button"
                        onClick={() => setModalSeparacao(null)}
                        className="flex-1 sm:flex-none px-4 py-2 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 rounded-xl text-xs font-medium transition-colors"
                      >
                        Fechar
                      </button>
                      <button
                        type="button"
                        onClick={() => concluirSeparacao(modalSeparacao)}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-all cursor-pointer"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        Finalizar Separação
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
          <div className="relative bg-white text-slate-900 rounded-2xl max-w-3xl w-full p-6 md:p-8 shadow-2xl space-y-6 my-auto" id="area-impressao-ficha">
            
            {/* Barra de Ações (Não sai na impressão) */}
            <div className="no-print flex items-center justify-between border-b border-slate-200 pb-4">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-zinc-700" />
                <h3 className="font-bold text-base text-slate-900">Ficha de Produção & Ordem de Serviço</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="flex items-center gap-2 px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-white rounded-xl text-xs font-semibold shadow-sm transition-all cursor-pointer"
                  title="Imprimir esta ficha em papel A4 ou salvar como PDF"
                >
                  <Printer className="w-4 h-4" />
                  Imprimir Ficha (A4)
                </button>
                <button
                  type="button"
                  onClick={() => setModalFicha(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
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
                <div className="inline-block px-4 py-2 bg-slate-900 text-white font-mono font-black text-2xl rounded-xl">
                  #{modalFicha.numeroPedido}
                </div>
                <div className="mt-2 text-xs font-bold text-slate-700 uppercase">
                  Status: <span className="underline">{modalFicha.status}</span>
                </div>
              </div>
            </div>

            {/* Dados do Cliente e Especificações da Peça */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] border-b border-slate-200 pb-1 flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-slate-700" /> Dados do Cliente
                </h4>
                <p><strong>Cliente:</strong> {modalFicha.clienteNome}</p>
                {modalFicha.clienteLoja && <p><strong>Loja/Marca:</strong> {modalFicha.clienteLoja}</p>}
                {modalFicha.clienteTelefone && <p><strong>Telefone / WhatsApp:</strong> {modalFicha.clienteTelefone}</p>}
              </div>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] border-b border-slate-200 pb-1 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-slate-700" /> Especificação Têxtil
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
              <div className="border border-slate-200 rounded-xl p-3 bg-slate-50 flex flex-col items-center justify-center text-center">
                <span className="text-[11px] font-bold text-slate-700 uppercase mb-2">Mockup / Arte</span>
                {Array.isArray(modalFicha.imagens) && modalFicha.imagens.length > 0 ? (
                  <img 
                    src={modalFicha.imagens[0].preview || modalFicha.imagens[0].caminhoSalvo || modalFicha.imagens[0].caminho} 
                    alt="Arte da Estampa" 
                    className="max-h-40 max-w-full object-contain rounded-lg border border-slate-300 shadow-sm"
                  />
                ) : (
                  <div className="h-32 w-full flex items-center justify-center text-slate-400 text-xs italic border border-dashed border-slate-300 rounded-lg">
                    Sem arte anexada
                  </div>
                )}
              </div>

              {/* Tabela de Grade de Peças */}
              <div className="md:col-span-2 border border-slate-200 rounded-xl p-4 bg-slate-50">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] border-b border-slate-200 pb-2 mb-3 flex items-center justify-between">
                  <span>Grade de Produção & Separação</span>
                  <span className="font-mono text-sm text-slate-900 font-bold">Total: {modalFicha.totalPecas} peças</span>
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
                          <td className="py-1.5 px-2 font-bold font-mono text-right text-slate-800">{qtd} un</td>
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
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
          <div className="bg-[#13151b] border border-zinc-800 rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-5 my-auto">
            
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-zinc-850 rounded-xl border border-zinc-750">
                  <Calculator className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-zinc-100">Calculadora de Bobina DTF</h3>
                  <p className="text-xs text-zinc-400">
                    {dtfCalcForm.origemPedido ? `Calculando para: ${dtfCalcForm.origemPedido}` : 'Cálculo de metragem linear, aproveitamento e custo de insumos'}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setModalCalculadoraDTF(false)}
                className="p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Presets Rápidos de Estampa */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">Presets de Tamanho de Estampa:</span>
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
                    className="px-3 py-2 bg-zinc-950 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 rounded-xl text-xs font-medium text-zinc-300 transition-all text-center"
                  >
                    <div>{preset.label}</div>
                    <div className="text-[10px] text-zinc-400 font-mono mt-0.5">{preset.w} x {preset.h} cm</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Campos de Entrada */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-medium text-zinc-400 uppercase">Largura Bobina (cm):</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.larguraBobina}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, larguraBobina: e.target.value })}
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-zinc-100 font-mono font-semibold text-sm focus:border-zinc-600 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-400 uppercase">Largura Estampa (cm):</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.larguraEstampa}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, larguraEstampa: e.target.value })}
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-zinc-100 font-mono font-semibold text-sm focus:border-zinc-600 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-400 uppercase">Altura Estampa (cm):</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.alturaEstampa}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, alturaEstampa: e.target.value })}
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-zinc-100 font-mono font-semibold text-sm focus:border-zinc-600 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-400 uppercase">Quantidade de Peças:</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.quantidade}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, quantidade: e.target.value })}
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-zinc-100 font-mono font-semibold text-sm focus:border-zinc-600 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-400 uppercase">Custo / Metro (R$):</label>
                <input 
                  type="number" 
                  step="0.5"
                  value={dtfCalcForm.custoMetro}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, custoMetro: e.target.value })}
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-zinc-100 font-mono font-semibold text-sm focus:border-zinc-600 outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-zinc-400 uppercase">Margem de Lucro (%):</label>
                <input 
                  type="number" 
                  value={dtfCalcForm.margemLucro}
                  onChange={e => setDtfCalcForm({ ...dtfCalcForm, margemLucro: e.target.value })}
                  className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-zinc-100 font-mono font-semibold text-sm focus:border-zinc-600 outline-none"
                />
              </div>
            </div>

            {/* Painel de Resultados */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-zinc-950/70 p-3 rounded-xl border border-zinc-800/80 space-y-1">
                <span className="text-[10px] font-semibold text-zinc-500 uppercase">Aproveitamento:</span>
                <div className="font-mono text-base font-bold text-zinc-100">
                  {resultadoCalculoDTF.porLinha} un / linha
                </div>
                <p className="text-[10px] text-zinc-500">{resultadoCalculoDTF.totalLinhas} linhas na bobina</p>
              </div>

              <div className="bg-zinc-950/70 p-3 rounded-xl border border-zinc-800/80 space-y-1">
                <span className="text-[10px] font-semibold text-zinc-500 uppercase">Metragem Bobina:</span>
                <div className="font-mono text-base font-bold text-zinc-100">
                  {resultadoCalculoDTF.metrosLineares} m
                </div>
                <p className="text-[10px] text-zinc-500">Área: {resultadoCalculoDTF.m2Total} m²</p>
              </div>

              <div className="bg-zinc-950/70 p-3 rounded-xl border border-zinc-800/80 space-y-1">
                <span className="text-[10px] font-semibold text-zinc-500 uppercase">Custo Estimado:</span>
                <div className="font-mono text-base font-bold text-zinc-100">
                  R$ {resultadoCalculoDTF.custoTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
                <p className="text-[10px] text-zinc-500">R$ {resultadoCalculoDTF.custoUn.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} / un</p>
              </div>

              <div className="bg-zinc-950/70 p-3 rounded-xl border border-zinc-800/80 space-y-1">
                <span className="text-[10px] font-semibold text-zinc-500 uppercase">Preço Sugerido:</span>
                <div className="font-mono text-base font-bold text-emerald-400">
                  R$ {resultadoCalculoDTF.precoSugerido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </div>
                <p className="text-[10px] text-zinc-500">R$ {resultadoCalculoDTF.precoUn.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} / un</p>
              </div>
            </div>

            {/* Rodapé do Modal */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800/80">
              <button
                type="button"
                onClick={() => setModalCalculadoraDTF(false)}
                className="px-4 py-2 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 rounded-xl text-xs font-medium transition-colors"
              >
                Fechar
              </button>
            </div>

          </div>
        </div>
      )}

      {/* ================= BARRA LATERAL ================= */}
      <aside className="w-64 bg-[#0e1015] border-r border-zinc-800/80 flex flex-col justify-between p-4 select-none">
        <div>
          {/* Logo / Cabeçalho */}
          <div className="flex items-center gap-3 px-1 py-3 mb-5 border-b border-zinc-800/80">
            <div className="w-9 h-9 rounded-xl overflow-hidden border border-zinc-800 bg-zinc-900 flex items-center justify-center shrink-0">
              <img src={logoImg} alt="Order Separator" className="w-full h-full object-cover" />
            </div>
            <div>
              <h1 className="font-bold text-sm text-zinc-100 tracking-tight leading-tight">Order Separator</h1>
              <span className="text-[10px] font-semibold text-zinc-400 tracking-wider uppercase">Gestão & Estamparia</span>
            </div>
          </div>

          {/* Navegação por Abas */}
          <nav className="space-y-1">
            <button
              onClick={() => setAbaAtiva('pedidos')}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                abaAtiva === 'pedidos'
                  ? 'bg-zinc-800/90 text-white font-semibold border border-zinc-700/60 shadow-sm'
                  : 'text-zinc-400 hover:bg-zinc-850 hover:text-zinc-200'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4 text-zinc-400" />
                <span>Painel de Pedidos</span>
              </div>
              <span className={`text-[11px] px-2 py-0.5 rounded-md font-mono ${
                abaAtiva === 'pedidos' ? 'bg-zinc-900 text-zinc-200 border border-zinc-700/50' : 'bg-zinc-900/60 text-zinc-400 border border-zinc-800'
              }`}>
                {pedidos.length}
              </span>
            </button>

            <button
              onClick={prepararNovoPedido}
              className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                abaAtiva === 'novo-pedido'
                  ? 'bg-zinc-800/90 text-white font-semibold border border-zinc-700/60 shadow-sm'
                  : 'text-zinc-400 hover:bg-zinc-850 hover:text-zinc-200'
              }`}
            >
              <PlusCircle className="w-4 h-4 text-zinc-400" />
              <span>Lançar Pedido</span>
            </button>

            <button
              onClick={() => setAbaAtiva('clientes')}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                abaAtiva === 'clientes'
                  ? 'bg-zinc-800/90 text-white font-semibold border border-zinc-700/60 shadow-sm'
                  : 'text-zinc-400 hover:bg-zinc-850 hover:text-zinc-200'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Users className="w-4 h-4 text-zinc-400" />
                <span>Clientes & Pastas</span>
              </div>
              <span className={`text-[11px] px-2 py-0.5 rounded-md font-mono ${
                abaAtiva === 'clientes' ? 'bg-zinc-900 text-zinc-200 border border-zinc-700/50' : 'bg-zinc-900/60 text-zinc-400 border border-zinc-800'
              }`}>
                {clientes.length}
              </span>
            </button>

            {/* Atalho Especial: Ferramentas CorelDRAW & IA */}
            <div className="pt-3 mt-3 border-t border-zinc-800/80 space-y-1.5">
              <span className="px-1 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block mb-1.5">Ferramentas Corel & IA</span>
              
              <button
                type="button"
                onClick={abrirMontadorCorel}
                title="Abrir Janela do Montador de Folha no CorelDRAW (Imposição / Gang Sheet)"
                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium bg-zinc-900/70 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Grid className="w-3.5 h-3.5 text-amber-400" />
                  <span>Montador de Folha</span>
                </div>
                <span className="text-[10px] font-mono text-zinc-400 bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-700/50">
                  Janela
                </span>
              </button>

              <button
                type="button"
                onClick={() => abrirVetorizadorCorel()}
                title="Abrir Vetorizador Profissional de Imagens (SVG / Curvas)"
                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium bg-zinc-900/70 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Vetorizador IA</span>
                </div>
                <span className="text-[10px] font-mono text-zinc-400 bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-700/50">
                  Vetor
                </span>
              </button>

              <button
                type="button"
                onClick={() => abrirRemovedorCorel()}
                title="Abrir Removedor de Fundo IA (U2-Net / Transparência)"
                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium bg-zinc-900/70 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Scissors className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Removedor IA</span>
                </div>
                <span className="text-[10px] font-mono text-zinc-400 bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-700/50">
                  Fundo
                </span>
              </button>

              <button
                type="button"
                onClick={() => abrirUpscalerCorel()}
                title="Abrir Upscaler IA Ultra HD (300 DPI / Real-ESRGAN)"
                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium bg-zinc-900/70 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Maximize2 className="w-3.5 h-3.5 text-sky-400" />
                  <span>Upscaler IA</span>
                </div>
                <span className="text-[10px] font-mono text-zinc-400 bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-700/50">
                  4x/8x
                </span>
              </button>

              <button
                type="button"
                onClick={() => setModalCalculadoraDTF(true)}
                title="Abrir Calculadora de Bobina DTF, Metragem Linear e Custos"
                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium bg-zinc-900/70 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 transition-all shadow-sm group"
              >
                <div className="flex items-center gap-2.5">
                  <Calculator className="w-3.5 h-3.5 text-amber-400" />
                  <span>Calculadora DTF</span>
                </div>
                <span className="text-[10px] font-mono text-zinc-400 bg-zinc-800/80 px-1.5 py-0.5 rounded border border-zinc-700/50">
                  Bobina
                </span>
              </button>
            </div>
          </nav>
        </div>

        {/* Rodapé da Sidebar */}
        <div className="bg-zinc-900/60 p-3 rounded-xl border border-zinc-800/80 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400 font-medium">Fila Ativa:</span>
            <span className="text-zinc-200 font-bold font-mono">{metricas.totalPecasProducao} peças</span>
          </div>
          <div className="flex items-center justify-between text-zinc-400 text-[11px]">
            <span>Aceleração IA:</span>
            <span className="text-zinc-300 font-mono font-medium flex items-center gap-1">
              RTX DirectML
            </span>
          </div>
          <div className="flex items-center gap-2 text-emerald-400 font-medium text-[11px] pt-1 border-t border-zinc-800/60">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>App Local Conectado</span>
          </div>
        </div>
      </aside>

      {/* ================= ÁREA DE CONTEÚDO ================= */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Toast Notificação */}
        {notificacao && (
          <div className={`absolute top-4 right-6 z-50 px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-2.5 text-xs font-medium border animate-in slide-in-from-top-4 duration-200 ${
            notificacao.tipo === 'sucesso'
              ? 'bg-[#13151b] text-emerald-300 border-emerald-500/30'
              : 'bg-[#13151b] text-red-300 border-red-500/30'
          }`}>
            {notificacao.tipo === 'sucesso' ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-red-400" />}
            <span>{notificacao.mensagem}</span>
            <button onClick={() => setNotificacao(null)} className="ml-2 hover:opacity-70">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-6 md:p-8">
          {/* ================= ABA: PAINEL DE PEDIDOS ================= */}
          {abaAtiva === 'pedidos' && (
            <div className="space-y-5 max-w-6xl mx-auto">
              {/* Cabeçalho do Painel */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-zinc-100 tracking-tight">Painel de Pedidos & Produção</h2>
                  <p className="text-xs text-zinc-400 mt-0.5">Gerenciamento ágil da estamparia, integração CorelDRAW e pastas de clientes.</p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={abrirMontadorCorel}
                    className="flex items-center gap-1.5 px-3 py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-800 hover:border-zinc-700 rounded-xl text-xs font-medium transition-colors cursor-pointer"
                  >
                    <Grid className="w-3.5 h-3.5 text-amber-400" />
                    Montador Corel
                  </button>
                  <button
                    type="button"
                    onClick={() => abrirVetorizadorCorel()}
                    className="flex items-center gap-1.5 px-3 py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-800 hover:border-zinc-700 rounded-xl text-xs font-medium transition-colors cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                    Vetorizador IA
                  </button>
                  <button
                    type="button"
                    onClick={() => abrirRemovedorCorel()}
                    className="flex items-center gap-1.5 px-3 py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-800 hover:border-zinc-700 rounded-xl text-xs font-medium transition-colors cursor-pointer"
                  >
                    <Scissors className="w-3.5 h-3.5 text-emerald-400" />
                    Removedor IA
                  </button>
                  <button
                    type="button"
                    onClick={() => abrirUpscalerCorel()}
                    className="flex items-center gap-1.5 px-3 py-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-800 hover:border-zinc-700 rounded-xl text-xs font-medium transition-colors cursor-pointer"
                  >
                    <Maximize2 className="w-3.5 h-3.5 text-sky-400" />
                    Upscaler IA
                  </button>
                  <button
                    onClick={prepararNovoPedido}
                    className="flex items-center gap-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors cursor-pointer"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    Lançar Pedido
                  </button>
                </div>
              </div>

              {/* Cards de Métricas */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-[#13151b] border border-zinc-800/80 rounded-xl p-4">
                  <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">Total de Pedidos</span>
                  <p className="text-2xl font-bold text-zinc-100 mt-1 font-mono">{metricas.total}</p>
                </div>
                <div className="bg-[#13151b] border border-zinc-800/80 rounded-xl p-4">
                  <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-400"></span> Aguardando
                  </span>
                  <p className="text-2xl font-bold text-amber-300 mt-1 font-mono">{metricas.aguardando}</p>
                </div>
                <div className="bg-[#13151b] border border-zinc-800/80 rounded-xl p-4">
                  <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-sky-400"></span> Em Produção
                  </span>
                  <p className="text-2xl font-bold text-sky-300 mt-1 font-mono">{metricas.emProducao}</p>
                </div>
                <div className="bg-[#13151b] border border-zinc-800/80 rounded-xl p-4">
                  <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Prontos / Entregues
                  </span>
                  <p className="text-2xl font-bold text-emerald-300 mt-1 font-mono">{metricas.concluidos}</p>
                </div>
              </div>

              {/* Barra de Filtros e Busca */}
              <div className="bg-[#13151b] border border-zinc-800/80 rounded-xl p-2.5 flex flex-col md:flex-row items-center justify-between gap-3">
                {/* Abas de Status */}
                <div className="flex flex-wrap gap-1 w-full md:w-auto">
                  {['Todos', 'Aguardando Produção', 'Em Produção', 'Pronto', 'Entregue'].map(st => (
                    <button
                      key={st}
                      onClick={() => setFiltroStatus(st)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        filtroStatus === st
                          ? 'bg-zinc-800 text-white font-semibold shadow-sm'
                          : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-850'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>

                {/* Input de Busca */}
                <div className="relative w-full md:w-72">
                  <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-zinc-500" />
                  <input
                    type="text"
                    value={busca}
                    onChange={(e) => setBusca(e.target.value)}
                    placeholder="Buscar pedido, cliente, tecido ou arte..."
                    className="w-full pl-8 pr-7 py-1.5 bg-zinc-950 border border-zinc-800 rounded-lg text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700"
                  />
                  {busca && (
                    <button onClick={() => setBusca('')} className="absolute right-2.5 top-2 text-zinc-500 hover:text-zinc-300">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Lista de Pedidos */}
              {pedidosFiltrados.length === 0 ? (
                <div className="border border-dashed border-zinc-800 rounded-2xl p-12 text-center bg-[#13151b]/40">
                  <FileText className="w-10 h-10 text-zinc-600 mx-auto mb-2.5" />
                  <p className="text-zinc-200 font-semibold text-sm">Nenhum pedido encontrado</p>
                  <p className="text-zinc-500 text-xs mt-1 max-w-sm mx-auto">
                    {busca || filtroStatus !== 'Todos'
                      ? 'Nenhum resultado corresponde aos filtros aplicados.'
                      : 'Cadastre seus clientes e lance seus pedidos para acompanhar toda a estamparia.'}
                  </p>
                  {pedidos.length === 0 && (
                    <button
                      onClick={prepararNovoPedido}
                      className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-semibold hover:bg-blue-500 shadow-sm transition-colors"
                    >
                      Criar Primeiro Pedido
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid gap-3.5">
                  {pedidosFiltrados.map((pedido) => {
                    const statusInfo = STATUS_OPCOES.find(s => s.id === pedido.status) || STATUS_OPCOES[0];
                    const StatusIcon = statusInfo.icon;

                    return (
                      <div 
                        key={pedido.id}
                        className="bg-[#13151b] border border-zinc-800/90 hover:border-zinc-700/80 rounded-2xl p-4 md:p-5 transition-all shadow-sm flex flex-col md:flex-row justify-between md:items-center gap-4"
                      >
                        <div className="space-y-3 flex-1">
                          {/* Cabeçalho do Card */}
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-zinc-200 font-mono font-bold text-sm bg-zinc-900 border border-zinc-750 px-2.5 py-0.5 rounded-lg">
                              #{pedido.numeroPedido}
                            </span>
                            <span className="text-zinc-100 font-semibold text-sm md:text-base">{pedido.clienteNome}</span>
                            {pedido.clienteLoja && (
                              <span className="text-xs bg-zinc-900 text-zinc-400 px-2 py-0.5 rounded border border-zinc-800 font-medium">
                                {pedido.clienteLoja}
                              </span>
                            )}

                            {/* Badge Seletor Rápido de Status com Micro-dot */}
                            <div className="relative inline-flex items-center">
                              <select
                                value={pedido.status || 'Aguardando Produção'}
                                onChange={(e) => mudarStatusPedido(pedido.id, e.target.value)}
                                className={`text-xs font-medium pl-2 pr-6 py-1 rounded-lg border focus:outline-none cursor-pointer ${statusInfo.bg} ${statusInfo.text} ${statusInfo.border}`}
                              >
                                {STATUS_OPCOES.map(opt => (
                                  <option key={opt.id} value={opt.id} className="bg-zinc-900 text-zinc-200">
                                    {opt.label}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <span className="text-xs bg-zinc-900 text-zinc-300 border border-zinc-800 px-2.5 py-0.5 rounded-md font-mono font-medium ml-auto md:ml-0">
                              {pedido.totalPecas} Peças
                            </span>
                          </div>

                          {/* Detalhes Técnicos */}
                          <div className="text-xs text-zinc-300 flex flex-wrap items-center gap-y-1.5 gap-x-3 bg-zinc-950/60 p-2.5 rounded-xl border border-zinc-800/80">
                            <span className="flex items-center gap-1.5">
                              <Palette className="w-3.5 h-3.5 text-zinc-400" />
                              <strong className="text-zinc-400">Estampa:</strong> {pedido.descricaoEstampa || 'Sem descrição'}
                            </span>
                            <span className="text-zinc-700">•</span>
                            <span>
                              <strong className="text-zinc-400">Posição:</strong> {pedido.posicaoEstampa}
                            </span>
                            <span className="text-zinc-700">•</span>
                            <span>
                              <strong className="text-zinc-400">Tecido:</strong> {pedido.tipoTecido} ({pedido.corTecido})
                            </span>
                            {pedido.dataEntrega && (
                              <>
                                <span className="text-zinc-700">•</span>
                                <span className="flex items-center gap-1 text-zinc-300">
                                  <Calendar className="w-3.5 h-3.5 text-zinc-400" />
                                  <strong className="text-zinc-400">Entrega:</strong> {formatarDataBR(pedido.dataEntrega)}
                                </span>
                              </>
                            )}
                          </div>

                          {/* Grade Quantitativa */}
                          <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                            <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider mr-1">Grade:</span>
                            {Object.entries(pedido.grade || {})
                              .filter(([_, qtd]) => Number(qtd) > 0)
                              .map(([tam, qtd]) => (
                                <div 
                                  key={tam} 
                                  className="px-2 py-0.5 rounded-lg text-xs font-mono border bg-zinc-900/90 text-zinc-300 border-zinc-800 shadow-sm"
                                >
                                  <span className="text-zinc-400">{tam}:</span> <strong className="text-zinc-100">{qtd}</strong>
                                </div>
                              ))}
                            {Object.values(pedido.grade || {}).every(q => Number(q) <= 0) && (
                              <span className="text-xs text-zinc-500 italic">Sem peças</span>
                            )}
                          </div>

                          {/* Miniaturas das Imagens da Estampa no Card */}
                          {Array.isArray(pedido.imagens) && pedido.imagens.length > 0 && (
                            <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-zinc-800/80 mt-1">
                              <div className="flex items-center gap-2 overflow-x-auto py-1">
                                <span className="text-[11px] font-medium text-zinc-500 uppercase tracking-wider mr-1 flex items-center gap-1 flex-shrink-0">
                                  <ImageIcon className="w-3.5 h-3.5 text-zinc-400" /> Artes:
                                </span>
                                {pedido.imagens.map((img, idx) => (
                                  <button
                                    key={idx}
                                    type="button"
                                    onClick={() => setImagemModal(img)}
                                    className="group relative w-10 h-10 rounded-lg overflow-hidden border border-zinc-800 bg-zinc-950 hover:border-zinc-600 transition-all flex-shrink-0 shadow-sm"
                                    title={`Ver arte: ${img.nome || 'Estampa'}`}
                                  >
                                    <img 
                                      src={img.preview || img.caminhoSalvo || img.caminho} 
                                      alt={img.nome || 'Estampa'} 
                                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                                    />
                                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                      <Eye className="w-3 h-3 text-white" />
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
                                  className="flex items-center gap-1 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 rounded-lg text-[11px] font-medium transition-colors shadow-sm"
                                  title="Recortar Fundo IA da arte deste pedido"
                                >
                                  <Scissors className="w-3 h-3 text-emerald-400" />
                                  <span>Recortar IA</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    const img = pedido.imagens[0];
                                    const p = img.caminhoSalvo || img.caminho;
                                    abrirUpscalerCorel(p);
                                  }}
                                  className="flex items-center gap-1 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 rounded-lg text-[11px] font-medium transition-colors shadow-sm"
                                  title="Aumentar resolução (300 DPI) com IA"
                                >
                                  <Maximize2 className="w-3 h-3 text-sky-400" />
                                  <span>Upscale 4x</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    const img = pedido.imagens[0];
                                    const p = img.caminhoSalvo || img.caminho;
                                    abrirVetorizadorCorel(p);
                                  }}
                                  className="flex items-center gap-1 px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-800 hover:border-zinc-700 rounded-lg text-[11px] font-medium transition-colors shadow-sm"
                                  title="Converter arte deste pedido em vetor SVG"
                                >
                                  <Sparkles className="w-3 h-3 text-indigo-400" />
                                  <span>Vetorizar</span>
                                </button>
                              </div>
                            </div>
                          )}

                          {pedido.observacoes && (
                            <p className="text-xs text-zinc-400 italic bg-zinc-950/40 px-3 py-1.5 rounded-lg border border-zinc-800/60">
                              Obs: {pedido.observacoes}
                            </p>
                          )}
                        </div>

                        {/* Botões de Ação */}
                        <div className="flex flex-col items-stretch gap-2 border-t md:border-t-0 md:border-l pt-3 md:pt-0 md:pl-5 border-zinc-800/80 shrink-0 w-full md:w-52">
                          {/* Ações CorelDRAW */}
                          <div className="grid grid-cols-1 gap-1.5">
                            <button
                              onClick={() => carimbarNoCorelDRAW(pedido)}
                              disabled={enviandoCorel === pedido.id}
                              title="Carimbar a ficha técnica e grade de tamanhos na arte aberta do CorelDRAW"
                              className="flex items-center justify-center gap-2 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-sm transition-colors cursor-pointer"
                            >
                              <Printer className="w-3.5 h-3.5 text-white" />
                              {enviandoCorel === pedido.id ? 'Carimbando...' : 'Carimbar no Corel'}
                            </button>

                            <button
                              onClick={abrirMontadorCorel}
                              title="Abrir Janela do Montador de Folha no CorelDRAW (Imposição / Gang Sheet)"
                              className="flex items-center justify-center gap-2 px-3 py-2 bg-zinc-850 hover:bg-zinc-800 text-zinc-200 text-xs font-medium rounded-xl border border-zinc-750 transition-colors cursor-pointer"
                            >
                              <Grid className="w-3.5 h-3.5 text-amber-400" />
                              Montar Folha
                            </button>
                          </div>

                          {/* Ações Operacionais */}
                          <div className="grid grid-cols-2 gap-1.5">
                            <button
                              onClick={() => setModalFicha(pedido)}
                              title="Visualizar e imprimir ficha de produção / ordem de serviço em papel A4"
                              className="flex items-center justify-center gap-1.5 px-2 py-1.5 bg-zinc-900 hover:bg-zinc-850 text-zinc-300 text-[11px] font-medium rounded-xl border border-zinc-800 transition-colors cursor-pointer"
                            >
                              <FileText className="w-3.5 h-3.5 text-zinc-400" />
                              Ficha OS
                            </button>

                            <button
                              onClick={() => abrirCalculadoraParaPedido(pedido)}
                              title="Calcular metragem na bobina DTF 58cm e custo de insumos"
                              className="flex items-center justify-center gap-1.5 px-2 py-1.5 bg-zinc-900 hover:bg-zinc-850 text-zinc-300 text-[11px] font-medium rounded-xl border border-zinc-800 transition-colors cursor-pointer"
                            >
                              <Calculator className="w-3.5 h-3.5 text-amber-400" />
                              Bobina DTF
                            </button>
                          </div>

                          <div className="grid grid-cols-2 gap-1.5">
                            <button
                              onClick={() => criarPastaProjeto(pedido)}
                              title="Criar pasta organizada do pedido, copiar imagens e abrir no Explorer"
                              className="flex items-center justify-center gap-1.5 px-2 py-1.5 bg-zinc-900 hover:bg-zinc-850 text-zinc-300 text-[11px] font-medium rounded-xl border border-zinc-800 transition-colors"
                            >
                              <FolderPlus className="w-3.5 h-3.5 text-zinc-400" />
                              Pasta
                            </button>

                            <button
                              onClick={() => abrirSeparacao(pedido)}
                              title="Abrir checklist de separação das peças por tamanho"
                              className="flex items-center justify-center gap-1.5 px-2 py-1.5 bg-zinc-900 hover:bg-zinc-850 text-zinc-300 text-[11px] font-medium rounded-xl border border-zinc-800 transition-colors"
                            >
                              <CheckSquare className="w-3.5 h-3.5 text-zinc-400" />
                              Separar
                            </button>
                          </div>

                          {/* Barra de Ações Rápidas: Editar, Duplicar, Excluir */}
                          <div className="flex items-center justify-between pt-1 border-t border-zinc-800/80 px-1">
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => iniciarEdicaoPedido(pedido)}
                                title="Editar dados e grade deste pedido"
                                className="p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
                              >
                                <Edit3 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => duplicarPedido(pedido)}
                                title="Duplicar pedido com novo número"
                                className="p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
                              >
                                <Copy className="w-3.5 h-3.5" />
                              </button>
                            </div>

                            <button
                              onClick={() => confirmarExcluirPedido(pedido)}
                              title="Remover pedido do painel"
                              className="p-1.5 text-zinc-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
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
            <div className="max-w-4xl mx-auto space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h2 className="text-xl font-bold text-zinc-100 tracking-tight">
                      {modoEdicaoId ? `Editando Pedido #${pedidoForm.numeroPedido}` : 'Lançamento de Pedido de Estamparia'}
                    </h2>
                    {modoEdicaoId && (
                      <span className="text-[11px] font-mono font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded-md">
                        MODO EDIÇÃO
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    {modoEdicaoId 
                      ? 'Atualize os dados técnicos ou quantidades da grade deste pedido.' 
                      : 'Preencha os dados técnicos da arte e a grade quantitativa para produção.'}
                  </p>
                </div>
                {modoEdicaoId && (
                  <button
                    type="button"
                    onClick={prepararNovoPedido}
                    className="self-start sm:self-auto px-3.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-xs font-medium transition-colors"
                  >
                    Cancelar Edição
                  </button>
                )}
              </div>

              {clientes.length === 0 ? (
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-8 text-center space-y-3">
                  <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto" />
                  <h3 className="font-bold text-zinc-100 text-base">Nenhum cliente cadastrado ainda!</h3>
                  <p className="text-xs text-zinc-400 max-w-md mx-auto">
                    Para vincular a pasta física no seu computador e salvar os arquivos de pedidos, cadastre o primeiro cliente.
                  </p>
                  <button
                    onClick={() => setAbaAtiva('clientes')}
                    className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold transition-colors shadow-sm"
                  >
                    Cadastrar Cliente Agora
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSalvarPedido} className="bg-[#13151b] border border-zinc-800 rounded-2xl p-6 md:p-7 space-y-5 shadow-xl">
                  {/* Cabeçalho */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Número do Pedido</label>
                      <div className="relative">
                        <Hash className="absolute left-3 top-2.5 w-4 h-4 text-zinc-500" />
                        <input
                          type="text"
                          required
                          value={pedidoForm.numeroPedido}
                          onChange={(e) => setPedidoForm({ ...pedidoForm, numeroPedido: e.target.value })}
                          className="w-full pl-9 pr-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-100 font-mono font-bold focus:outline-none focus:border-zinc-700"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Cliente Cadastrado</label>
                      <select
                        required
                        value={pedidoForm.clienteId}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, clienteId: e.target.value })}
                        className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 cursor-pointer"
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
                      <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Previsão de Entrega</label>
                      <input
                        type="date"
                        value={pedidoForm.dataEntrega}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, dataEntrega: e.target.value })}
                        className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-zinc-700"
                      />
                    </div>
                  </div>

                  {/* Detalhes da Estampa */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Nome / Descrição da Estampa</label>
                      <input
                        type="text"
                        required
                        placeholder="Ex: Estampa Caveira Surfista 3 Cores Silk Screen"
                        value={pedidoForm.descricaoEstampa}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, descricaoEstampa: e.target.value })}
                        className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Posição da Estampa</label>
                      <select
                        value={pedidoForm.posicaoEstampa}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, posicaoEstampa: e.target.value })}
                        className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 cursor-pointer"
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
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Tipo de Tecido / Malha</label>
                      <input
                        type="text"
                        placeholder="Ex: Algodão Fio 30.1, Poliéster, Dry-Fit..."
                        value={pedidoForm.tipoTecido}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, tipoTecido: e.target.value })}
                        className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-zinc-700"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Cor da Peça</label>
                      <input
                        type="text"
                        placeholder="Ex: Preta, Branca, Mescla..."
                        value={pedidoForm.corTecido}
                        onChange={(e) => setPedidoForm({ ...pedidoForm, corTecido: e.target.value })}
                        className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-zinc-700"
                      />
                    </div>
                  </div>

                  {/* Grade Quantitativa com Botões + e - */}
                  <div className="border border-zinc-800 bg-zinc-950/60 p-5 rounded-2xl space-y-3.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Layers className="w-4 h-4 text-zinc-400" />
                        <h3 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Grade de Peças por Tamanho</h3>
                      </div>
                      <span className="text-xs font-mono font-bold text-zinc-200 bg-zinc-900 border border-zinc-750 px-3 py-0.5 rounded-full">
                        Total: {totalPecas} Peças
                      </span>
                    </div>

                    <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-8 gap-2 pt-1">
                      {TAMANHOS_PADRAO.map((tamanho) => (
                        <div key={tamanho} className="bg-zinc-900 border border-zinc-800 rounded-xl p-2 text-center transition-all focus-within:border-zinc-650">
                          <label className="block text-[11px] font-bold text-zinc-300 mb-1">{tamanho}</label>
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
                            className="w-full text-center bg-zinc-950 border border-zinc-800 rounded-lg py-1 text-base font-bold text-zinc-100 focus:outline-none focus:border-zinc-650 font-mono"
                          />
                          <div className="flex gap-1 mt-1 justify-center">
                            <button
                              type="button"
                              onClick={() => alterarQtdGrade(tamanho, -1)}
                              className="px-2 py-0.5 bg-zinc-800 hover:bg-zinc-750 text-zinc-300 rounded text-xs font-bold"
                            >
                              -
                            </button>
                            <button
                              type="button"
                              onClick={() => alterarQtdGrade(tamanho, 1)}
                              className="px-2 py-0.5 bg-zinc-800 hover:bg-zinc-750 text-zinc-200 rounded text-xs font-bold"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Imagens da Estampa / Mockups */}
                  <div className="border border-zinc-800 bg-zinc-950/60 p-5 rounded-2xl space-y-3.5">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 bg-zinc-900 rounded-xl border border-zinc-800">
                          <ImageIcon className="w-4 h-4 text-zinc-400" />
                        </div>
                        <div>
                          <h3 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Imagens da Estampa / Mockup da Peça</h3>
                          <p className="text-xs text-zinc-400">Anexe as fotos da arte (frente, costas, manga) para controle de produção.</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={escolherImagensEstampa}
                        className="flex items-center gap-1.5 px-3.5 py-2 bg-zinc-850 hover:bg-zinc-800 text-zinc-200 text-xs font-medium rounded-xl border border-zinc-750 transition-colors self-start sm:self-auto cursor-pointer"
                      >
                        <ImagePlus className="w-3.5 h-3.5" />
                        Anexar Imagens...
                      </button>
                    </div>

                    {pedidoForm.imagens.length === 0 ? (
                      <div 
                        onClick={escolherImagensEstampa}
                        className="border border-dashed border-zinc-800 hover:border-zinc-700 rounded-xl p-6 text-center cursor-pointer transition-colors bg-zinc-900/30 group"
                      >
                        <ImagePlus className="w-7 h-7 text-zinc-600 group-hover:text-zinc-400 mx-auto mb-1.5 transition-colors" />
                        <p className="text-xs text-zinc-300 font-medium">Nenhuma imagem anexada ainda</p>
                        <p className="text-[11px] text-zinc-500 mt-0.5">Clique para selecionar arquivos de imagem no computador (JPG, PNG, WEBP, BMP)</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
                        {pedidoForm.imagens.map((img, idx) => (
                          <div key={idx} className="group relative bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-sm flex flex-col transition-all">
                            <div className="h-28 bg-[#0b0d11] flex items-center justify-center overflow-hidden relative">
                              <img 
                                src={img.preview || img.caminho} 
                                alt={img.nome} 
                                className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-200"
                              />
                              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => setImagemModal(img)}
                                  className="p-1.5 bg-zinc-800 text-white rounded-lg hover:bg-zinc-700 transition-colors shadow"
                                  title="Visualizar em tamanho grande"
                                >
                                  <Eye className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => removerImagemEstampa(idx)}
                                  className="p-1.5 bg-red-600 text-white rounded-lg hover:bg-red-500 transition-colors shadow"
                                  title="Remover imagem"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>
                            <span className="p-2 text-[10px] font-mono text-zinc-400 truncate bg-zinc-950 border-t border-zinc-800" title={img.nome}>
                              {img.nome}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Observações */}
                  <div>
                    <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Instruções de Impressão / Observações</label>
                    <textarea
                      rows="3"
                      placeholder="Instruções de tintas, telas de seda, temperatura de cura ou especificações do cliente..."
                      value={pedidoForm.observacoes}
                      onChange={(e) => setPedidoForm({ ...pedidoForm, observacoes: e.target.value })}
                      className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700"
                    ></textarea>
                  </div>

                  {/* Botões do Rodapé */}
                  <div className="flex flex-col md:flex-row items-center justify-between gap-3 pt-3 border-t border-zinc-800">
                    <p className="text-xs text-zinc-500">
                      💾 Arquivo <code className="text-zinc-300 font-mono">pedido_#{pedidoForm.numeroPedido}.json</code> será gravado na pasta do cliente.
                    </p>

                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setAbaAtiva('pedidos')}
                        className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-xs font-medium transition-colors"
                      >
                        Cancelar
                      </button>
                      <button
                        type="submit"
                        className="flex items-center gap-1.5 px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors cursor-pointer"
                      >
                        <Save className="w-3.5 h-3.5" />
                        {modoEdicaoId ? 'Atualizar Pedido' : 'Salvar Pedido no PC'}
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </div>
          )}

          {/* ================= ABA: CLIENTES & DIRETÓRIOS ================= */}
          {abaAtiva === 'clientes' && (
            <div className="max-w-5xl mx-auto space-y-6">
              <div>
                <h2 className="text-xl font-bold text-zinc-100 tracking-tight">Cadastro de Clientes e Pastas</h2>
                <p className="text-xs text-zinc-400 mt-0.5">Vincule cada cliente ao seu diretório correspondente no Windows para gravação direta de pedidos e artes.</p>
              </div>

              {/* Formulário de Novo Cliente */}
              <form onSubmit={handleSalvarCliente} className="bg-[#13151b] border border-zinc-800 rounded-2xl p-5 md:p-6 space-y-4 shadow-xl">
                <h3 className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Novo Cliente</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Nome do Cliente *</label>
                    <input
                      type="text"
                      required
                      placeholder="Ex: João da Silva"
                      value={clienteForm.nome}
                      onChange={(e) => setClienteForm({ ...clienteForm, nome: e.target.value })}
                      className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-zinc-700"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">Nome da Loja / Marca</label>
                    <input
                      type="text"
                      placeholder="Ex: Streetwear Co."
                      value={clienteForm.loja}
                      onChange={(e) => setClienteForm({ ...clienteForm, loja: e.target.value })}
                      className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-zinc-700"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">WhatsApp / Telefone</label>
                    <input
                      type="text"
                      placeholder="(11) 99999-9999"
                      value={clienteForm.telefone}
                      onChange={(e) => setClienteForm({ ...clienteForm, telefone: e.target.value })}
                      className="w-full px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-200 focus:outline-none focus:border-zinc-700"
                    />
                  </div>
                </div>

                {/* Seleção do Diretório */}
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
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
                      className="flex-1 px-3.5 py-2 bg-zinc-950 border border-zinc-800 rounded-xl text-sm text-zinc-300 font-mono focus:outline-none cursor-pointer"
                    />
                    <button
                      type="button"
                      onClick={escolherPastaCliente}
                      className="flex items-center gap-1.5 px-4 py-2 bg-zinc-850 hover:bg-zinc-800 text-zinc-200 text-xs font-medium rounded-xl border border-zinc-750 transition-colors shadow-sm"
                    >
                      <FolderSync className="w-3.5 h-3.5 text-zinc-400" />
                      Selecionar Pasta...
                    </button>
                  </div>
                </div>

                <div className="flex justify-end pt-1">
                  <button
                    type="submit"
                    className="flex items-center gap-1.5 px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    Cadastrar Cliente
                  </button>
                </div>
              </form>

              {/* Lista de Clientes Cadastrados */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider">
                    Clientes Cadastrados ({clientes.length})
                  </h3>
                  <button 
                    onClick={carregarDados}
                    className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1 transition-colors"
                  >
                    <RefreshCw className="w-3 h-3" /> Atualizar lista
                  </button>
                </div>

                {clientes.length === 0 ? (
                  <div className="p-8 text-center border border-dashed border-zinc-800 rounded-2xl text-zinc-500 text-xs">
                    Nenhum cliente cadastrado no momento.
                  </div>
                ) : (
                  <div className="grid gap-2.5">
                    {clientes.map(c => {
                      const pedidosDoCliente = pedidos.filter(p => p.clienteId === c.id || p.clienteNome === c.nome);
                      const iniciais = c.nome ? c.nome.slice(0, 2).toUpperCase() : 'CL';

                      return (
                        <div key={c.id} className="bg-[#13151b] border border-zinc-800 hover:border-zinc-700/80 p-4 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-3 transition-all shadow-sm">
                          <div className="flex items-center gap-3.5">
                            {/* Avatar */}
                            <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-750 flex items-center justify-center font-bold text-zinc-300 text-sm shadow-sm">
                              {iniciais}
                            </div>

                            <div className="space-y-1">
                              <div className="flex items-center gap-2.5">
                                <span className="font-semibold text-zinc-100 text-sm">{c.nome}</span>
                                {c.loja && (
                                  <span className="text-xs bg-zinc-900 text-zinc-400 px-2 py-0.5 rounded border border-zinc-800 font-medium">
                                    {c.loja}
                                  </span>
                                )}
                                <span className="text-xs text-zinc-400 font-mono bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800">
                                  {pedidosDoCliente.length} pedidos
                                </span>
                              </div>

                              <p className="text-xs text-zinc-400 font-mono flex items-center gap-1.5 bg-zinc-950/70 px-2 py-0.5 rounded-lg border border-zinc-800/80">
                                <FolderOpen className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />
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
                                className="flex items-center gap-1 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 text-xs font-medium rounded-xl border border-emerald-500/30 transition-colors"
                              >
                                <MessageCircle className="w-3.5 h-3.5 text-emerald-400" />
                                WhatsApp
                              </a>
                            )}

                            <button
                              onClick={() => abrirNoExplorer(c.pastaDiretorio)}
                              className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-850 hover:bg-zinc-800 text-zinc-200 text-xs font-medium rounded-xl border border-zinc-750 transition-colors shadow-sm"
                            >
                              <FolderOpen className="w-3.5 h-3.5 text-zinc-400" />
                              Abrir Pasta
                            </button>

                            <button
                              onClick={() => confirmarExcluirCliente(c)}
                              title="Remover cliente"
                              className="p-1.5 text-zinc-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
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
