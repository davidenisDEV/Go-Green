# 🌿 Go Green ERP - Sistema de Gestão Inteligente

> **Gestão completa, moderna e eficiente para Tabacarias e Headshops.**

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Interface](https://img.shields.io/badge/Interface-CustomTkinter-green.svg)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento-orange.svg)

## 💡 Sobre o Projeto

O **Go Green ERP** é uma solução Desktop desenvolvida em Python projetada para resolver os desafios reais do varejo de tabacarias. Diferente de sistemas genéricos, ele foi moldado com foco na agilidade do caixa, controle rigoroso de estoque de itens pequenos e inteligência de negócios.

O sistema elimina planilhas manuais e caderninhos, centralizando vendas, estoque, clientes e relatórios financeiros em uma interface moderna (Dark Mode) e intuitiva.

## 🚀 Principais Funcionalidades (O "Pitch" de Venda)

### 🛒 Frente de Caixa (PDV) Ultra Rápido
- **Venda Ágil:** Busca de produtos instantânea com sistema de cache otimizado (sem travamentos).
- **Interface Limpa:** Cupom fiscal visual em tempo real.
- **Flexibilidade:** Cadastro rápido de novos clientes diretamente na tela de venda.

### 📦 Gestão de Estoque & Produção
- **Controle Total:** Monitoramento de quantidade, custo e preço de venda.
- **Fábrica de Kits:** Módulo exclusivo para criar "Combos" (ex: Kit Session). O sistema calcula o custo dos insumos automaticamente e dá baixa nos itens individuais ao produzir o kit.
- **Alertas Inteligentes:** Aviso visual de produtos com estoque crítico ou zerado.

### 📊 Dashboard & BI (Business Intelligence)
- **Visão 360º:** Gráficos interativos de vendas e lucro (últimos 7 ou 30 dias).
- **KPIs em Tempo Real:** Ticket médio, faturamento do dia, lucro líquido e produto mais vendido.
- **Relatórios Gerenciais:** Exportação profissional para **Excel** (com abas de análise financeira) e **PDF** executivo.

### 🍹 Módulo Eventos (Fuzuê Friends)
- Ferramenta dedicada para gestão de eventos temporários/festas.
- Controle de caixa separado da loja principal.
- Baixa de estoque consolidada ao final do evento.

---

## 🛠️ Tecnologias Utilizadas

O projeto foi construído utilizando as melhores bibliotecas do ecossistema Python para Desktop:

- **Linguagem:** Python 3.12
- **Interface Gráfica (GUI):** `customtkinter` (Visual moderno e responsivo).
- **Banco de Dados:** `sqlite3` (Leve, local e seguro).
- **Análise de Dados:** `pandas` & `matplotlib`.
- **Relatórios:** `reportlab` (PDF) e `openpyxl` (Excel).

---

## 📂 Estrutura do Código

O sistema segue uma arquitetura modular para facilitar a manutenção e escalabilidade:

- **`gogreen_admin.py`**: O núcleo da aplicação. Gerencia a navegação, as janelas e a lógica de interface.
- **`database.py`**: A camada de persistência. Contém todas as queries SQL, migrações de schema e regras de negócio financeiras.
- **`Database/`**: Pasta onde o banco de dados `tabacaria.db` é armazenado com segurança.

