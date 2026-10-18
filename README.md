# Order Separator (OS) 👕📦

Sistema desktop profissional para **Gestão de Pedidos de Estamparia, Organização de Pastas de Clientes no PC e Integração Direta com CorelDRAW Graphics Suite 2022**.

---

## 🚀 Principais Recursos

- **Gestão de Clientes & Pastas Físicas**: Vinculação direta com as pastas locais dos clientes no Windows Explorer. Toda gravação de pedido salva automaticamente uma ficha física JSON dentro da pasta do cliente.
- **Grade Completa do PP ao G10**: Suporte total a tamanhos `PP`, `P`, `M`, `G`, `GG`, `G1`, `G2`, `G3`, `G4`, `G5`, `G6`, `G7`, `G8`, `G9` e `G10` com cálculo automático do total de peças.
- **Upload de Artes e Mockups**: Anexo e pré-visualização em alta resolução das artes da estampa (frente, costas, manga).
- **Carimbo Vetorial em 1 Clique no CorelDRAW**:
  - Gera automaticamente a ficha técnica completa dentro do arquivo aberto no **CorelDRAW**.
  - Tabela vetorial proporcional com números grandes em negrito (**18mm de altura real**) e letras legíveis (**7,5mm de altura real**).
  - Todos os elementos são gerados e agrupados em um único bloco móvel.
- **Desktop Nativo (.exe)**: Construído com Electron, React, Vite e Tailwind CSS, empacotado para Windows com ícone personalizado.

---

## 🛠️ Tecnologias Utilizadas

- **Frontend**: React 18, Tailwind CSS, Lucide Icons
- **Desktop**: Electron 33, Electron Builder
- **Build**: Vite 6
- **Integração Gráfica**: CorelDRAW COM Automation (VBA / PowerShell Bridge)

---

## 📦 Como Rodar Localmente

1. Clone o repositório:
```bash
git clone <URL_DO_REPOSITORIO>
cd estamparia-manager
```

2. Instale as dependências:
```bash
npm install
```

3. Execute em modo de desenvolvimento:
```bash
npm run start
```

4. Para gerar o executável (.exe):
```bash
npm run pack
```
