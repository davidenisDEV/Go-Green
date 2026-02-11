import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import sqlite3
from datetime import datetime, timedelta
import csv
import os
import webbrowser
from urllib.parse import quote
import shutil
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
import matplotlib.pyplot as plt



# --- CONFIGURAÇÕES VISUAIS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# --- DEFINIÇÃO DE CAMINHOS (INTEGRAÇÃO COM WEB) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tenta achar a pasta de uploads do Flask (Backend) para salvar as imagens lá
# Ele sobe um nível (dirname) e entra em Web_Backend/static/uploads
UPLOAD_DIR = os.path.join(os.path.dirname(BASE_DIR), "Web_Backend", "static", "uploads")

# Cria a pasta se ela não existir
if not os.path.exists(UPLOAD_DIR):
    try:
        os.makedirs(UPLOAD_DIR)
    except:
        pass
# --- CONFIGURAÇÃO DE FONTE ---
# Certifique-se de ter instalado a fonte "Horizon" no Windows antes de rodar
FONT_MAIN = "Horizon" 
FONT_BODY = "Roboto" # Horizon pode ser ruim para leitura de tabelas pequenas, usei Roboto ou Arial como fallback para dados

# Paleta de Cores
COR_VERDE_NEON = "#00ff7f"
COR_VERDE_PRINCIPAL = "#2ecc71"
COR_VERDE_ESCURO = "#27ae60"
COR_VERMELHO_ERRO = "#e74c3c"
COR_AMARELO_ALERTA = "#f1c40f"
COR_FUNDO_CARD = "#212121"
COR_FUNDO_JANELA = "#1a1a1a"
COR_TEXTO_CINZA = "gray70"

# --- BACKEND (BANCO DE DADOS) ---
class Database:
    def __init__(self):
        # Caminhos
        caminho_padrao = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Database", "tabacaria.db")
        if os.path.exists(caminho_padrao):
            self.db_name = caminho_padrao
            print(f"Conectado ao banco Central: {self.db_name}")
        else:
            self.db_name = 'tabacaria.db'
            print(f"Conectado ao banco Local (Modo Teste): {self.db_name}")

        self.inicializar_banco()
        self.migrar_schema()

    def conectar(self):
        return sqlite3.connect(self.db_name)

    def inicializar_banco(self):
        conn = self.conectar()
        c = conn.cursor()
        # Tabelas
        c.execute('''CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, qtd_estoque INTEGER DEFAULT 0, custo_unitario REAL, preco_venda REAL, estoque_minimo INTEGER DEFAULT 5, observacoes TEXT, imagem_url TEXT, categoria TEXT, destaque INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, telefone TEXT, email TEXT, data_cadastro TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, data_hora TEXT, produto_id INTEGER, cliente_id INTEGER, qtd_vendida INTEGER, total_venda REAL, lucro_real REAL, pagamento TEXT, FOREIGN KEY(produto_id) REFERENCES produtos(id), FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS pedidos_web (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_nome TEXT, cliente_contato TEXT, data_hora TEXT, total REAL, status TEXT DEFAULT 'pendente', metodo_pagamento TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS itens_pedido_web (id INTEGER PRIMARY KEY AUTOINCREMENT, pedido_id INTEGER, produto_id INTEGER, quantidade INTEGER, preco_unitario REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios_web (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT UNIQUE, password_hash TEXT, role TEXT, data_criacao TEXT, telefone TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS fuzue_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_evento TEXT,
            total_vendido REAL,
            lucro_evento REAL,
            resumo_itens TEXT
        )''')
        
        conn.commit()
        conn.close()

    def migrar_schema(self):
        conn = self.conectar()
        comandos = [
            "ALTER TABLE produtos ADD COLUMN observacoes TEXT",
            "ALTER TABLE vendas ADD COLUMN cliente_id INTEGER",
            "ALTER TABLE usuarios_web ADD COLUMN telefone TEXT",
            "ALTER TABLE produtos ADD COLUMN imagem_url TEXT",
            "ALTER TABLE produtos ADD COLUMN categoria TEXT",
            "ALTER TABLE produtos ADD COLUMN destaque INTEGER DEFAULT 0",
            "ALTER TABLE clientes ADD COLUMN email TEXT"
        ]
        for cmd in comandos:
            try: conn.execute(cmd)
            except: pass
        conn.commit()
        conn.close()

    # --- DASHBOARD & BI (MÉTODOS NOVOS) ---
    def get_dashboard_avancado(self):
        c = self.conectar()
        hj = datetime.now().strftime('%Y-%m-%d')
        res_hj = c.execute("SELECT SUM(total_venda), SUM(lucro_real) FROM vendas WHERE data_hora LIKE ?", (f'{hj}%',)).fetchone()
        res_tot = c.execute("SELECT SUM(total_venda), SUM(lucro_real) FROM vendas").fetchone()
        
        venda_hj = res_hj[0] or 0.0
        lucro_hj = res_hj[1] or 0.0
        lucro_tot = res_tot[1] or 0.0
        
        ticket_medio = c.execute("SELECT AVG(total_venda) FROM vendas").fetchone()[0] or 0.0
        
        top_prod = c.execute('''SELECT p.nome, SUM(v.qtd_vendida) as qtd FROM vendas v JOIN produtos p ON v.produto_id = p.id GROUP BY p.id ORDER BY qtd DESC LIMIT 1''').fetchone()
        top_produto = f"{top_prod[0]} ({top_prod[1]})" if top_prod else "N/A"
        
        c.close()
        return venda_hj, lucro_hj, lucro_tot, ticket_medio, top_produto

    def get_dados_grafico(self, dias=7):
        """Retorna dados para o gráfico com base no período escolhido"""
        c = self.conectar()
        d, v, l = [], [], []
        hj = datetime.now()
        
        for i in range(dias-1, -1, -1):
            dt = (hj - timedelta(days=i)).strftime('%Y-%m-%d')
            r = c.execute("SELECT SUM(total_venda), SUM(lucro_real) FROM vendas WHERE data_hora LIKE ?", (f'{dt}%',)).fetchone()
            data_fmt = dt[8:10]+"/"+dt[5:7]
            d.append(data_fmt)
            v.append(r[0] or 0.0)
            l.append(r[1] or 0.0)
            
        c.close()
        return d, v, l
    
    def get_detalhe_vendas_hoje(self):
        c = self.conectar()
        hj = datetime.now().strftime('%Y-%m-%d')
        sql = '''SELECT v.data_hora, p.nome, v.qtd_vendida, v.total_venda, v.pagamento FROM vendas v JOIN produtos p ON v.produto_id = p.id WHERE v.data_hora LIKE ? ORDER BY v.data_hora DESC'''
        res = c.execute(sql, (f'{hj}%',)).fetchall()
        c.close()
        return res

    def get_resumo_lucro(self):
        c = self.conectar()
        res = c.execute("SELECT SUM(total_venda), SUM(total_venda - lucro_real), SUM(lucro_real) FROM vendas").fetchone()
        c.close()
        return res if res[0] else (0.0, 0.0, 0.0)

    def get_dados_relatorio_pdf_avancado(self):
        c = self.conectar()
        sql = '''SELECT substr(data_hora, 1, 10) as dia, SUM(total_venda), SUM(lucro_real), COUNT(id), AVG(total_venda) FROM vendas GROUP BY dia ORDER BY dia DESC LIMIT 31'''
        dados = c.execute(sql).fetchall()
        c.close()
        return dados
    
    def get_kpis(self): # Mantido para compatibilidade se algo antigo chamar
        c=self.conectar(); hj=datetime.now().strftime('%Y-%m-%d'); rh=c.execute("SELECT SUM(total_venda), SUM(lucro_real) FROM vendas WHERE data_hora LIKE ?", (f'{hj}%',)).fetchone(); rt=c.execute("SELECT SUM(total_venda), SUM(lucro_real) FROM vendas").fetchone(); c.close()
        return (rh[0]or 0, rh[1]or 0, rt[0]or 0, rt[1]or 0)

    def get_alertas_estoque(self):
        c = self.conectar()
        r = c.execute("SELECT nome, qtd_estoque FROM produtos WHERE qtd_estoque <= estoque_minimo ORDER BY qtd_estoque ASC").fetchall()
        c.close()
        return r

    # --- NOVO: MÉTODOS PARA O FUZUÊ ---
    def salvar_fuzue(self, total, lucro, resumo_texto):
        """Salva o fechamento do caixa do Fuzuê e lança vendas no sistema principal"""
        c = self.conectar()
        try:
            dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 1. Salva no histórico específico do Fuzuê
            c.execute("INSERT INTO fuzue_historico (data_evento, total_vendido, lucro_evento, resumo_itens) VALUES (?, ?, ?, ?)",
                      (dt, total, lucro, resumo_texto))
            
            # 2. Lança como uma venda consolidada no sistema principal (para KPIs)
            # Criamos um "Produto Fictício" ou lançamos item a item? 
            # Melhor lançar item a item para baixar estoque corretamente.
            # (Essa lógica será feita no frontend da PageFuzue, aqui só salvamos o histórico do evento)
            
            conn_id = c.lastrowid
            c.connection.commit()
            return True, "Fuzuê Fechado com Sucesso!"
        except Exception as e:
            return False, str(e)
        finally:
            c.close()

    def get_historico_fuzue(self):
        c = self.conectar()
        r = c.execute("SELECT * FROM fuzue_historico ORDER BY id DESC").fetchall()
        c.close()
        return r

    # --- ADICIONE ESTE MÉTODO NA CLASSE Database ---
    def get_dados_reposicao(self):
        """
        Gera dados para reposição:
        Compara Estoque Atual vs Vendas dos últimos 7 dias.
        """
        c = self.conectar()
        
        # Data de 7 dias atrás
        dt_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # SQL: Pega Produto, Estoque e soma Vendas desde a data inicio
        sql = '''
            SELECT 
                p.nome,
                p.qtd_estoque,
                IFNULL(SUM(v.qtd_vendida), 0) as vendas_7d
            FROM produtos p
            LEFT JOIN vendas v ON p.id = v.produto_id AND v.data_hora >= ?
            GROUP BY p.id
            ORDER BY vendas_7d DESC
        '''
        
        resultados = []
        rows = c.execute(sql, (dt_inicio,)).fetchall()
        
        for r in rows:
            nome = r[0]
            est_atual = r[1]
            vendas_7d = r[2]
            
            # Lógica de Sugestão:
            # Meta: Ter estoque para cobrir a venda da semana + 20% de segurança
            meta_estoque = int(vendas_7d * 1.2)
            
            # Se o estoque atual for menor que a meta, sugere a diferença
            sugestao = max(0, meta_estoque - est_atual)
            
            # Define status
            if est_atual == 0: status = "CRÍTICO (Zerado)"
            elif est_atual < vendas_7d: status = "ALERTA (Baixo)"
            else: status = "OK"
            
            # Só adiciona na lista se tiver venda ou se o estoque estiver zerado/baixo
            if vendas_7d > 0 or est_atual <= 5:
                resultados.append((nome, est_atual, vendas_7d, sugestao, status))
            
        c.close()
        return resultados

    # --- PRODUTOS ---
    def cadastrar_produto(self, n, q, c, p, o, img, cat, dest):
        con = self.conectar()
        try:
            con.execute("INSERT INTO produtos (nome, qtd_estoque, custo_unitario, preco_venda, observacoes, imagem_url, categoria, destaque) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (n, q, c, p, o, img, cat, dest))
            con.commit()
        except Exception as e: raise e
        finally: con.close()

    def editar_item(self, id_p, n, c, p, ajuste, o, img=None, cat=None, dest=0):
        con = self.conectar()
        try:
            # 1. Pega dados atuais para não perder o que não foi alterado
            # (Adicionei tratamento para caso o produto não exista)
            atual = con.execute("SELECT qtd_estoque, imagem_url, categoria FROM produtos WHERE id=?", (id_p,)).fetchone()
            
            if not atual: 
                return False, "Produto não encontrado."
            
            # 2. Calcula novo estoque e mantém dados antigos se vazio
            # (atual[0] é qtd_estoque, atual[1] é imagem_url, atual[2] é categoria)
            novo_est = max(0, atual[0] + ajuste)
            nova_img = img if img else atual[1]
            nova_cat = cat if cat else (atual[2] if len(atual) > 2 and atual[2] else "Geral")

            # 3. Executa Update
            con.execute("""
                UPDATE produtos 
                SET nome=?, qtd_estoque=?, custo_unitario=?, preco_venda=?, observacoes=?, imagem_url=?, categoria=?, destaque=? 
                WHERE id=?
            """, (n, novo_est, c, p, o, nova_img, nova_cat, dest, id_p))
            
            con.commit()
            return True, "Produto atualizado com sucesso!"
            
        except Exception as e:
            return False, f"Erro no banco: {str(e)}"
        finally:
            con.close()

    def buscar_produtos(self, termo):
        c = self.conectar()
        # Ordem fixa: 0:id, 1:nome, 2:est, 3:venda, 4:custo, 5:obs, 6:img, 7:dest, 8:cat
        sql = """
            SELECT id, nome, qtd_estoque, preco_venda, custo_unitario, observacoes, imagem_url, destaque, categoria 
            FROM produtos WHERE nome LIKE ?
        """
        r = c.execute(sql, (f'%{termo}%',)).fetchall()
        c.close()
        return r

    # [ADICIONAR] Este método faltava e é essencial para a edição com reposição funcionar
    def editar_produto_completo(self, id_p, nome, custo, venda, ajuste_qtd, obs, img, cat, dest):
        conn = self.conectar()
        try:
            # 1. Verifica estoque atual
            atual = conn.execute("SELECT qtd_estoque FROM produtos WHERE id=?", (id_p,)).fetchone()
            if not atual: return False, "Produto não encontrado."
            
            novo_estoque = max(0, atual[0] + ajuste_qtd)
            
            # 2. Registra despesa se for reposição
            if ajuste_qtd > 0:
                valor_gasto = ajuste_qtd * custo
                # Garante que tabela financeiro existe (migração pode ter falhado em bancos antigos)
                conn.execute('''CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, valor REAL, descricao TEXT, data TEXT)''')
                
                conn.execute("INSERT INTO financeiro (tipo, valor, descricao, data) VALUES (?, ?, ?, ?)", 
                             ('saida', valor_gasto, f"Reposição: {nome} ({ajuste_qtd}x)", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            # 3. Atualiza dados
            conn.execute("""
                UPDATE produtos 
                SET nome=?, custo_unitario=?, preco_venda=?, qtd_estoque=?, observacoes=?, imagem_url=?, categoria=?, destaque=?
                WHERE id=?
            """, (nome, custo, venda, novo_estoque, obs, img, cat, dest, id_p))
            
            conn.commit()
            return True, "Atualizado com sucesso."
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def excluir_produto(self, id_p):
        c = self.conectar()
        try: c.execute("DELETE FROM produtos WHERE id=?", (id_p,)); c.commit(); return True, "Ok"
        except Exception as e: return False, str(e)
        finally: c.close()

    def importar_excel(self, f):
        c=self.conectar(); s=0
        try:
            df=pd.read_excel(f); df.columns=[x.strip() for x in df.columns]
            for _,r in df.iterrows():
                n=str(r['Produto']).strip(); q=int(r['Qtd Comprada']); cu=float(r['Custo Unitário']); p=float(r['Preço de Venda Sugerido'])
                e=c.execute("SELECT id, qtd_estoque FROM produtos WHERE nome=?",(n,)).fetchone()
                if e: c.execute("UPDATE produtos SET qtd_estoque=?,custo_unitario=?,preco_venda=? WHERE id=?",(e[1]+q,cu,p,e[0]))
                else: c.execute("INSERT INTO produtos (nome,qtd_estoque,custo_unitario,preco_venda) VALUES (?,?,?,?)",(n,q,cu,p))
                s+=1
            c.commit(); return True, f"{s} importados"
        except Exception as e: return False, str(e)
        finally: c.close()

    # --- CLIENTES ---
    def buscar_clientes(self, t):
        c = self.conectar()
        r = c.execute("SELECT * FROM clientes WHERE nome LIKE ? OR telefone LIKE ? ORDER BY id DESC", (f'%{t}%', f'%{t}%')).fetchall()
        c.close()
        return r

    def cadastrar_cliente(self, n, t, e=""):
        c = self.conectar()
        try: c.execute("INSERT INTO clientes (nome, telefone, email, data_cadastro) VALUES (?,?,?,?)", (n, t, e, datetime.now().strftime('%Y-%m-%d'))); c.commit(); return True, c.lastrowid
        except: return False, None
        finally: c.close()
    
    def atualizar_cliente(self, idc, n, t, e=""):
        c = self.conectar()
        try: c.execute("UPDATE clientes SET nome=?, telefone=?, email=? WHERE id=?", (n,t,e,idc)); c.commit(); return True, "Ok"
        except: return False, "Erro"
        finally: c.close()

    def excluir_cliente(self, idc):
        c = self.conectar()
        try: 
            c.execute("UPDATE vendas SET cliente_id=NULL WHERE cliente_id=?", (idc,))
            c.execute("DELETE FROM clientes WHERE id=?", (idc,))
            c.commit(); return True, "Ok"
        except: return False, "Erro"
        finally: c.close()
    
    def get_compras_cliente(self, cliente_id):
        conn = self.conectar()
        try:
            sql = '''SELECT v.data_hora, p.nome, v.qtd_vendida, v.total_venda, v.pagamento FROM vendas v JOIN produtos p ON v.produto_id = p.id WHERE v.cliente_id = ? ORDER BY v.data_hora DESC'''
            return conn.execute(sql, (cliente_id,)).fetchall()
        finally: conn.close()

    # --- VENDAS & WEB ---
    def registrar_venda_lote(self, car, cid, pg):
        c = self.conectar()
        try:
            dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for i in car:
                c.execute("UPDATE produtos SET qtd_estoque=qtd_estoque-? WHERE id=?", (i['qtd'], i['id']))
                c.execute("INSERT INTO vendas (data_hora, produto_id, cliente_id, qtd_vendida, total_venda, lucro_real, pagamento) VALUES (?,?,?,?,?,?,?)", (dt, i['id'], cid, i['qtd'], i['total'], i['lucro'], pg))
            c.commit(); return True, "Venda Sucesso"
        except Exception as e: c.rollback(); return False, str(e)
        finally: c.close()

    def get_historico_vendas(self):
        c = self.conectar()
        sql = '''SELECT v.id, v.data_hora, IFNULL(c.nome, 'Consumidor Final'), v.total_venda, v.pagamento, p.nome || ' (Qtd: ' || v.qtd_vendida || ')' FROM vendas v LEFT JOIN clientes c ON v.cliente_id = c.id JOIN produtos p ON v.produto_id = p.id ORDER BY v.data_hora DESC LIMIT 100'''
        r = c.execute(sql).fetchall()
        c.close()
        return r

    def atualizar_venda(self, venda_id, novo_pgto):
        conn = self.conectar()
        try: conn.execute("UPDATE vendas SET pagamento = ? WHERE id = ?", (novo_pgto, venda_id)); conn.commit(); return True, "Venda atualizada!"
        except Exception as e: return False, str(e)
        finally: conn.close()

    def get_clientes_web(self):
        c=self.conectar(); r=c.execute("SELECT u.id, u.nome, u.email, u.telefone, u.data_criacao, COUNT(p.id) FROM usuarios_web u LEFT JOIN pedidos_web p ON u.nome = p.cliente_nome GROUP BY u.id ORDER BY u.id DESC").fetchall(); c.close(); return r
    def get_pedidos_pendentes(self): c=self.conectar(); r=c.execute("SELECT id, cliente_nome, total, status, metodo_pagamento, data_hora FROM pedidos_web WHERE status = 'pendente' ORDER BY id DESC").fetchall(); c.close(); return r
    def aprovar_pedido_web(self, pid):
        c=self.conectar()
        try:
            itens=c.execute("SELECT produto_id, quantidade, preco_unitario FROM itens_pedido_web WHERE pedido_id=?",(pid,)).fetchall()
            dt=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for prid, qtd, pr in itens:
                c.execute("UPDATE produtos SET qtd_estoque=qtd_estoque-? WHERE id=?",(qtd,prid))
                c.execute("INSERT INTO vendas (data_hora, produto_id, qtd_vendida, total_venda, lucro_real, pagamento) VALUES (?,?,?,?,?,?)", (dt,prid,qtd,pr*qtd,0,'WEB'))
            c.execute("UPDATE pedidos_web SET status='aprovado' WHERE id=?",(pid,)); c.commit(); return True, "Aprovado"
        except Exception as e: c.rollback(); return False, str(e)
        finally: c.close()
    def cancelar_pedido_web(self, pid): c=self.conectar(); c.execute("UPDATE pedidos_web SET status='cancelado' WHERE id=?",(pid,)); c.commit(); c.close(); return True, "Cancelado"

db = Database()


# Importações necessárias para o PDF e Gráficos
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
import matplotlib.pyplot as plt

class PageDash(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Configuração do Grid
        self.grid_columnconfigure(0, weight=3) # Coluna do Gráfico (Maior)
        self.grid_columnconfigure(1, weight=1) # Coluna Lateral (Menor)
        self.grid_rowconfigure(1, weight=1)

        # --- ÁREA SUPERIOR: KPIs (Indicadores) ---
        self.frame_kpi = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_kpi.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        for i in range(5): self.frame_kpi.grid_columnconfigure(i, weight=1)

        # Criação dos Cards de KPI
        # Note que passamos funções para os cards que possuem detalhes (clicáveis)
        self.card_venda_hj = self.criar_card(self.frame_kpi, 0, "💰 Vendas Hoje (Ver Detalhes)", COR_VERDE_NEON, self.ver_detalhes_hoje)
        self.card_lucro_hj = self.criar_card(self.frame_kpi, 1, "📈 Lucro Hoje", COR_VERDE_PRINCIPAL)
        self.card_ticket = self.criar_card(self.frame_kpi, 2, "🏷️ Ticket Médio", "#f39c12")
        self.card_top_item = self.criar_card(self.frame_kpi, 3, "🏆 Top Produto", "#9b59b6")
        self.card_lucro_tot = self.criar_card(self.frame_kpi, 4, "🏦 Lucro Global (Ver DRE)", "#3498db", self.ver_detalhes_lucro)

        # --- ESQUERDA: GRÁFICO ---
        self.frame_graph = ctk.CTkFrame(self, fg_color=COR_FUNDO_CARD, corner_radius=15)
        self.frame_graph.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        # Header do Gráfico (Filtros)
        fg_head = ctk.CTkFrame(self.frame_graph, fg_color="transparent")
        fg_head.pack(fill="x", padx=10, pady=10)
        
        self.filtro_dias = ctk.CTkSegmentedButton(fg_head, values=["7 Dias", "30 Dias"], command=self.mudar_periodo)
        self.filtro_dias.set("7 Dias")
        self.filtro_dias.pack(side="left")
        
        self.tipo_grafico = ctk.CTkSegmentedButton(fg_head, values=["Linha", "Barra"], command=self.atualizar_grafico)
        self.tipo_grafico.set("Linha")
        self.tipo_grafico.pack(side="right")

        # Área onde o gráfico será desenhado
        self.canvas_area = ctk.CTkFrame(self.frame_graph, fg_color="transparent")
        self.canvas_area.pack(fill="both", expand=True, padx=10, pady=10)

        # --- DIREITA: ALERTAS E EXPORTAÇÃO ---
        self.frame_side = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_side.grid(row=1, column=1, sticky="nsew")
        self.frame_side.grid_rowconfigure(0, weight=1) # Alerta ocupa espaço disponível
        self.frame_side.grid_rowconfigure(1, weight=0) # Botões fixos embaixo

        # Alertas de Estoque Baixo
        self.frame_alert = ctk.CTkFrame(self.frame_side, fg_color=COR_FUNDO_CARD, corner_radius=15)
        self.frame_alert.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        ctk.CTkLabel(self.frame_alert, text="⚠️ Reposição Urgente", font=("Arial", 14, "bold"), text_color=COR_AMARELO_ALERTA).pack(pady=10)
        
        self.tr = ttk.Treeview(self.frame_alert, columns=("I","Q"), show="headings", height=10)
        self.tr.heading("I", text="Produto"); self.tr.column("I", width=120)
        self.tr.heading("Q", text="Qtd"); self.tr.column("Q", width=40, anchor="center")
        self.tr.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Botões de Exportação
        self.frame_btns = ctk.CTkFrame(self.frame_side, fg_color="transparent")
        self.frame_btns.grid(row=1, column=0, sticky="ew")

        self.btn_excel = ctk.CTkButton(
            self.frame_btns, 
            text="📊 EXPORTAR XLSX (DATA)", 
            font=(FONT_MAIN, 12, "bold"), 
            fg_color="#2ecc71", 
            height=40, 
            command=self.gerar_excel
        )
        self.btn_excel.pack(fill="x", pady=(0, 5)) 

        self.btn_pdf = ctk.CTkButton(
            self.frame_btns, 
            text="📄 EXPORTAR PDF (VISUAL)", 
            font=(FONT_MAIN, 12, "bold"), 
            fg_color="#e74c3c", 
            height=40, 
            command=self.gerar_pdf
        )
        self.btn_pdf.pack(fill="x")

        # Inicializa a vista
        self.update_view()

    # --- MÉTODO DE CRIAÇÃO DE CARDS ---
    def criar_card(self, master, col, titulo, cor, comando=None):
        f = ctk.CTkFrame(master, fg_color=COR_FUNDO_CARD, corner_radius=10)
        f.grid(row=0, column=col, sticky="ew", padx=5)
        
        lbl_t = ctk.CTkLabel(f, text=titulo, font=("Arial", 11))
        lbl_t.pack(pady=(10,0))
        lbl_v = ctk.CTkLabel(f, text="-", font=("Arial", 18, "bold"), text_color=cor)
        lbl_v.pack(pady=(0,10))
        
        # Torna o card clicável se houver comando
        if comando:
            for widget in [f, lbl_t, lbl_v]:
                widget.bind("<Button-1>", lambda e: comando())
                widget.configure(cursor="hand2")
            
        return lbl_v

    # --- INTERATIVIDADE (POPUPS) ---
    def ver_detalhes_hoje(self):
        top = ctk.CTkToplevel(self)
        top.title("Vendas de Hoje")
        top.geometry("600x400")
        top.grab_set() # Foca nesta janela e bloqueia a de trás
        
        ctk.CTkLabel(top, text="Extrato Diário", font=(FONT_MAIN, 16, "bold")).pack(pady=10)
        
        cols = ("Hora", "Item", "Qtd", "Total", "Pgto")
        tr = ttk.Treeview(top, columns=cols, show="headings")
        tr.heading("Hora", text="Hora"); tr.column("Hora", width=80, anchor="center")
        tr.heading("Item", text="Produto"); tr.column("Item", width=200)
        tr.heading("Qtd", text="Q"); tr.column("Qtd", width=30, anchor="center")
        tr.heading("Total", text="$$"); tr.column("Total", width=80, anchor="e")
        tr.heading("Pgto", text="Pgto"); tr.column("Pgto", width=80, anchor="center")
        tr.pack(fill="both", expand=True, padx=10, pady=10)
        
        vendas = db.get_detalhe_vendas_hoje()
        for v in vendas:
            # v = (data_hora, nome_prod, qtd, total, pgto)
            hora = v[0].split()[1] if len(v[0]) > 10 else v[0]
            tr.insert("", "end", values=(hora, v[1], v[2], f"R$ {v[3]:.2f}", v[4]))

    def ver_detalhes_lucro(self):
        top = ctk.CTkToplevel(self)
        top.title("Raio-X Financeiro")
        top.geometry("400x300")
        top.grab_set() # Foca nesta janela
        
        fat, custo, lucro = db.get_resumo_lucro()
        margem = (lucro / fat * 100) if fat > 0 else 0
        
        ctk.CTkLabel(top, text="Análise de Lucratividade Global", font=(FONT_MAIN, 16, "bold")).pack(pady=20)
        
        f = ctk.CTkFrame(top, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=40)
        
        def linha(txt, val, cor="white"):
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=txt, text_color="gray", anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=val, text_color=cor, font=("Arial", 12, "bold"), anchor="e").pack(side="right")

        linha("Faturamento Bruto:", f"R$ {fat:.2f}", COR_VERDE_NEON)
        linha("Custo dos Produtos:", f"- R$ {custo:.2f}", COR_VERMELHO_ERRO)
        
        ctk.CTkFrame(f, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        linha("LUCRO LÍQUIDO:", f"R$ {lucro:.2f}", "#3498db")
        linha("Margem de Contribuição:", f"{margem:.1f}%", "#f39c12")

    # --- GRÁFICOS ---
    def mudar_periodo(self, valor):
        self.atualizar_grafico(self.tipo_grafico.get())

    def atualizar_grafico(self, tipo):
        # 1. Limpa o canvas anterior para economizar memória
        for w in self.canvas_area.winfo_children(): 
            w.destroy()
        
        # Fecha figuras abertas do matplotlib
        plt.close('all') 
        
        # 2. Busca dados
        dias_filtro = 30 if self.filtro_dias.get() == "30 Dias" else 7
        dias, vendas, lucros = db.get_dados_grafico(dias_filtro)
        
        # 3. Configura estilo
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor(COR_FUNDO_CARD)
        ax.set_facecolor(COR_FUNDO_CARD)
        
        # 4. Desenha
        if tipo == "Linha":
            ax.plot(dias, vendas, marker='o', color=COR_VERDE_NEON, label='Vendas', linewidth=2)
            ax.plot(dias, lucros, marker='s', color='#3498db', label='Lucro', linestyle='--', linewidth=1.5)
            ax.fill_between(dias, vendas, color=COR_VERDE_NEON, alpha=0.1)
        else:
            x = range(len(dias))
            ax.bar(x, vendas, width=0.4, label='Vendas', color=COR_VERDE_NEON, alpha=0.8)
            ax.bar(x, lucros, width=0.4, label='Lucro', color='#3498db', alpha=0.8) 
            ax.set_xticks(x)
            ax.set_xticklabels(dias)

        ax.legend()
        ax.grid(color='#444', linestyle=':', linewidth=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(colors='white', labelsize=8)
        
        # Rotaciona datas se forem muitas
        if len(dias) > 10: 
            plt.xticks(rotation=45) 
        
        # 5. Renderiza no Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # --- ATUALIZAÇÃO GERAL (MÉTODO CHAVE) ---
    def update_view(self):
        """Chamado sempre que a tela é exibida. Recarrega todos os dados."""
        
        # 1. Atualiza KPIs
        # (vh=venda_hoje, lh=lucro_hoje, lt=lucro_total, tm=ticket_medio, top=top_produto)
        vh, lh, lt, tm, top = db.get_dashboard_avancado()
        
        self.card_venda_hj.configure(text=f"R$ {vh:.2f}")
        self.card_lucro_hj.configure(text=f"R$ {lh:.2f}")
        self.card_ticket.configure(text=f"R$ {tm:.2f}")
        self.card_top_item.configure(text=top[:15] + "..." if len(top)>15 else top)
        self.card_lucro_tot.configure(text=f"R$ {lt:.2f}")

        # 2. Atualiza Alertas de Estoque
        for i in self.tr.get_children(): 
            self.tr.delete(i)
            
        alertas = db.get_alertas_estoque()
        for i in alertas: 
            # i = (Nome, Qtd)
            self.tr.insert("", "end", values=(i[0], i[1]))
        
        # 3. Atualiza Gráfico
        self.atualizar_grafico(self.tipo_grafico.get())

    # --- EXPORTAÇÃO EXCEL ---
    def gerar_excel(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx", 
                filetypes=[("Planilha Excel", "*.xlsx")],
                title="Salvar Relatório Gerencial"
            )
            if not filename: return

            # Dados Resumidos
            vh, lh, lt, tm, top = db.get_dashboard_avancado()
            df_resumo = pd.DataFrame({
                "Indicador": ["Faturamento Hoje", "Lucro Hoje", "Lucro Global", "Ticket Médio", "Top Produto", "Data Geração"],
                "Valor": [vh, lh, lt, tm, top, datetime.now().strftime("%d/%m/%Y %H:%M")]
            })

            # Dados Detalhados
            dados_brutos = db.get_dados_relatorio_pdf_avancado()
            df_detalhado = pd.DataFrame(dados_brutos, columns=["Data", "Faturamento", "Lucro", "Qtd Vendas", "Ticket Médio"])
            
            # Margem
            df_detalhado["Margem %"] = df_detalhado.apply(
                lambda x: (x["Lucro"] / x["Faturamento"] * 100) if x["Faturamento"] > 0 else 0, axis=1
            ).round(2)

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
                df_detalhado.to_excel(writer, sheet_name='Detalhamento', index=False)

            messagebox.showinfo("Sucesso", "Relatório Excel exportado!")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar Excel: {str(e)}")

    # --- PDF EXECUTIVO ---
    def gerar_pdf(self):
        try:
            filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not filename: return
            
            # Salva imagem do gráfico atual
            img_path = "temp_graph.png"
            plt.savefig(img_path, facecolor='#212121')
            
            c = canvas.Canvas(filename, pagesize=A4)
            w, h = A4
            
            # Cabeçalho Preto
            c.setFillColor(HexColor("#111111"))
            c.rect(0, h-120, w, 120, fill=True, stroke=False)
            
            c.setFillColor(HexColor("#00ff7f"))
            c.setFont("Helvetica-Bold", 26)
            c.drawString(40, h-60, "RELATÓRIO GERENCIAL")
            c.setFillColor(HexColor("#ffffff"))
            c.setFont("Helvetica", 14)
            c.drawString(40, h-85, "Go Green Tabacaria | Análise de Performance")
            c.drawRightString(w-40, h-60, datetime.now().strftime("%d/%m/%Y"))
            
            # KPIs
            y_kpi = h - 160
            vh, lh, lt, tm, top = db.get_dashboard_avancado()
            
            def draw_kpi_box(x, title, val):
                c.setStrokeColor(HexColor("#cccccc"))
                c.rect(x, y_kpi-40, 120, 50)
                c.setFillColor(HexColor("#666666")); c.setFont("Helvetica", 10); c.drawString(x+5, y_kpi-15, title)
                c.setFillColor(HexColor("#000000")); c.setFont("Helvetica-Bold", 12); c.drawString(x+5, y_kpi-35, val)

            draw_kpi_box(40, "Faturamento Hoje", f"R$ {vh:.2f}")
            draw_kpi_box(170, "Lucro Hoje", f"R$ {lh:.2f}")
            draw_kpi_box(300, "Ticket Médio", f"R$ {tm:.2f}")
            draw_kpi_box(430, "Lucro Global", f"R$ {lt:.2f}")
            
            # Imagem do Gráfico
            c.drawImage(img_path, 40, h-500, width=515, height=280)
            
            # Tabela
            y = h - 540
            c.setFillColor(HexColor("#000000")); c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Detalhamento Financeiro (Últimos 30 Dias)")
            
            y -= 30
            c.setFillColor(HexColor("#eeeeee")); c.rect(40, y-5, 515, 20, fill=True, stroke=False)
            c.setFillColor(HexColor("#000000")); c.setFont("Helvetica-Bold", 9)
            c.drawString(50, y, "DATA"); c.drawString(150, y, "FATURAMENTO"); c.drawString(250, y, "LUCRO"); c.drawString(350, y, "TICKET"); c.drawString(450, y, "QTD")
            
            y -= 20
            c.setFont("Helvetica", 9)
            dados = db.get_dados_relatorio_pdf_avancado()
            
            for row in dados:
                if y < 50: c.showPage(); y = h - 50
                c.drawString(50, y, str(row[0])) 
                c.drawString(150, y, f"R$ {row[1]:.2f}") 
                c.drawString(250, y, f"R$ {row[2]:.2f}") 
                ticket = row[4] if row[4] else 0.0
                c.drawString(350, y, f"R$ {ticket:.2f}") 
                c.drawString(450, y, str(row[3])) 
                c.setStrokeColor(HexColor("#eeeeee"))
                c.line(40, y-5, 555, y-5)
                y -= 20
                
            c.save()
            if os.path.exists(img_path): os.remove(img_path)
            messagebox.showinfo("Sucesso", "Relatório PDF gerado!")
            
        except Exception as e: 
            messagebox.showerror("Erro PDF", f"Falha: {str(e)}")


# --- INTERFACE GRÁFICA (FRONTEND DESKTOP) ---

# --- PÁGINAS WEB (Adicione ou verifique se estas classes estão no seu arquivo) ---

class PagePedidosWeb(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Pedidos Online (Sala de Espera)", font=(FONT_MAIN, 20), text_color=COR_VERDE_NEON).pack(pady=20)
        
        self.tr = ttk.Treeview(self, columns=("ID","Cli","Total","Status","Pgto","Data"), show="headings")
        cols = {"ID":50, "Cli":200, "Total":100, "Status":100, "Pgto":100, "Data":150}
        for c, w in cols.items(): self.tr.heading(c, text=c); self.tr.column(c, width=w)
        self.tr.pack(fill="both", expand=True, padx=20)
        
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(pady=20)
        ctk.CTkButton(bf, text="🔄 Atualizar Lista", command=self.load).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="✅ APROVAR PEDIDO", fg_color=COR_VERDE_PRINCIPAL, command=self.aprov).pack(side="left", padx=10)
        ctk.CTkButton(bf, text="❌ CANCELAR", fg_color=COR_VERMELHO_ERRO, command=self.canc).pack(side="left", padx=10)
        
        self.load()

    def load(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        for p in db.get_pedidos_pendentes(): self.tr.insert("", "end", values=(p[0], p[1], f"R$ {p[2]:.2f}", p[3], p[4], p[5]))

    def aprov(self):
        s = self.tr.selection()
        if not s: return messagebox.showwarning("Aviso", "Selecione um pedido")
        pid = self.tr.item(s[0], 'values')[0]
        if messagebox.askyesno("Confirmar", "Confirmar pagamento e baixar estoque?"):
            ok, m = db.aprovar_pedido_web(pid)
            if ok: messagebox.showinfo("Sucesso", m); self.load()
            else: messagebox.showerror("Erro", m)

    def canc(self):
        s = self.tr.selection()
        if not s: return
        pid = self.tr.item(s[0], 'values')[0]
        if messagebox.askyesno("Confirmar", "Cancelar este pedido?"):
            ok, m = db.cancelar_pedido_web(pid)
            if ok: messagebox.showinfo("Sucesso", "Pedido cancelado."); self.load()
            else: messagebox.showerror("Erro", m)

    def update_view(self): self.load()

class PageClientesWeb(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        # Split em 2: Lista de Clientes e Histórico do Selecionado
        self.grid_rowconfigure(1, weight=1); self.grid_columnconfigure(0, weight=1)
        
        # Tabela Clientes
        f_top = ctk.CTkFrame(self, fg_color="transparent"); f_top.grid(row=0, column=0, sticky="nsew", pady=10)
        ctk.CTkLabel(f_top, text="Clientes Cadastrados no Site", font=(FONT_MAIN, 16), text_color=COR_VERDE_NEON).pack(anchor="w")
        
        self.tr_cli = ttk.Treeview(f_top, columns=("ID","Nome","Email","Tel","Desde","Pedidos"), show="headings", height=8)
        cols = {"ID":30, "Nome":150, "Email":200, "Tel":100, "Desde":80, "Pedidos":60}
        for c, w in cols.items(): 
            self.tr_cli.heading(c, text=c)
            self.tr_cli.column(c, width=w)
        
        self.tr_cli.pack(fill="both", expand=True, padx=20)
        self.tr_cli.bind("<<TreeviewSelect>>", self.ver_historico)
        
        ctk.CTkButton(f_top, text="🔄 Atualizar Lista", command=self.load, height=30).pack(pady=5)
        
        # Histórico
        f_bot = ctk.CTkFrame(self, fg_color="transparent"); f_bot.grid(row=1, column=0, sticky="nsew", pady=10)
        self.lbl_hist = ctk.CTkLabel(f_bot, text="Selecione um cliente para ver compras", font=(FONT_MAIN, 16), text_color="white")
        self.lbl_hist.pack(anchor="w", pady=(20, 5))
        
        self.tr_hist = ttk.Treeview(f_bot, columns=("ID Pedido", "Data", "Total", "Status", "Pgto"), show="headings")
        for c in ("ID Pedido", "Data", "Total", "Status", "Pgto"): self.tr_hist.heading(c, text=c)
        self.tr_hist.pack(fill="both", expand=True, padx=20)
        
        self.load()

    def load(self):
        for i in self.tr_cli.get_children(): self.tr_cli.delete(i)
        for c in db.get_clientes_web(): self.tr_cli.insert("", "end", values=c)

    def ver_historico(self, _):
        sel = self.tr_cli.selection()
        if not sel: return
        vals = self.tr_cli.item(sel[0], 'values')
        nome = vals[1]
        self.lbl_hist.configure(text=f"Histórico de Compras: {nome}")
        
        for i in self.tr_hist.get_children(): self.tr_hist.delete(i)
        hist = db.get_historico_cliente_web(nome)
        for h in hist: self.tr_hist.insert("", "end", values=(h[0], h[1], f"R$ {h[2]:.2f}", h[3], h[4]))

    def update_view(self): self.load()

class PageVendas(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Layout Principal
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.carrinho = []
        self.cli = None
        self.todos_produtos = [] # Cache local para evitar queries repetitivas

        # --- ESQUERDA: CATÁLOGO ---
        self.frame_cat = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_cat.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Busca
        f_busca = ctk.CTkFrame(self.frame_cat, fg_color="transparent")
        f_busca.pack(fill="x", pady=(0, 10))
        
        self.busca = ctk.CTkEntry(f_busca, placeholder_text="🔍 Buscar (Nome ou ID)...", height=40, font=("Arial", 14))
        self.busca.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.busca.bind("<KeyRelease>", self.filtrar_produtos_local) # Filtro local (rápido)
        
        ctk.CTkButton(f_busca, text="🔄", width=40, height=40, command=self.recarregar_dados).pack(side="right")

        # Abas
        self.tab_view = ctk.CTkTabview(self.frame_cat, width=400, text_color=COR_VERDE_NEON)
        self.tab_view.pack(fill="both", expand=True)
        
        # --- DIREITA: CAIXA ---
        self.frame_box = ctk.CTkFrame(self, fg_color=COR_FUNDO_CARD, corner_radius=15)
        self.frame_box.grid(row=0, column=1, sticky="nsew", ipadx=10, ipady=10)
        
        # Cabeçalho
        ctk.CTkLabel(self.frame_box, text="🛒 CAIXA LIVRE", font=(FONT_MAIN, 20, "bold"), text_color=COR_VERDE_NEON).pack(pady=(15,10))
        
        # Cliente
        f_cli = ctk.CTkFrame(self.frame_box, fg_color="#2c3e50", corner_radius=6)
        f_cli.pack(fill="x", pady=5)
        self.lbl_cli = ctk.CTkLabel(f_cli, text="Consumidor Final", font=("Arial", 12, "bold"), text_color="white")
        self.lbl_cli.pack(side="left", padx=10, pady=8)
        ctk.CTkButton(f_cli, text="Alterar", width=60, height=25, fg_color="#34495e", command=self.abrir_selecao_cliente).pack(side="right", padx=5)

        # Lista de Itens
        ctk.CTkLabel(self.frame_box, text="CUPOM DE VENDA", font=("Arial", 10, "bold"), text_color="gray").pack(anchor="w", pady=(15,2))
        
        style = ttk.Style()
        style.configure("Treeview", font=('Consolas', 10), rowheight=22) # Consolas para alinhar numeros
        
        self.tr = ttk.Treeview(self.frame_box, columns=("Q", "Item", "$"), show="headings", height=14)
        self.tr.heading("Q", text="Qtd"); self.tr.column("Q", width=30, anchor="center")
        self.tr.heading("Item", text="Descrição"); self.tr.column("Item", width=160)
        self.tr.heading("$", text="Total"); self.tr.column("$", width=70, anchor="e")
        self.tr.pack(fill="both", expand=True, pady=2)
        
        ctk.CTkButton(self.frame_box, text="Remover Item", fg_color=COR_VERMELHO_ERRO, height=25, font=("Arial", 11), command=self.remover_item).pack(fill="x", pady=5)

        # Totais
        f_tot = ctk.CTkFrame(self.frame_box, fg_color="transparent")
        f_tot.pack(fill="x", pady=10)
        
        self.lbl_itens_count = ctk.CTkLabel(f_tot, text="0 volumes", text_color="gray", font=("Arial", 11))
        self.lbl_itens_count.pack(anchor="e")
        self.lt = ctk.CTkLabel(f_tot, text="R$ 0.00", font=("Arial", 36, "bold"), text_color=COR_VERDE_NEON)
        self.lt.pack(anchor="e")
        
        # Pagamento
        ctk.CTkLabel(self.frame_box, text="Forma de Pagamento:", font=("Arial", 12)).pack(anchor="w")
        self.pg = ctk.CTkOptionMenu(self.frame_box, values=["Pix", "Dinheiro", "Cartão Débito", "Cartão Crédito"], fg_color="#34495e", height=35)
        self.pg.pack(fill="x", pady=5)
        
        ctk.CTkButton(self.frame_box, text="✅ CONFIRMAR (F5)", font=(FONT_MAIN, 16, "bold"), fg_color=COR_VERDE_PRINCIPAL, height=55, command=self.finalizar).pack(fill="x", pady=20)
        
        # Atalho de teclado
        self.master.bind("<F5>", lambda e: self.finalizar())

        self.recarregar_dados()

    # --- LÓGICA OTIMIZADA DE PRODUTOS ---
    def recarregar_dados(self):
        """Busca do banco apenas uma vez e guarda em memória"""
        self.todos_produtos = db.buscar_produtos("")
        self.construir_abas()

    def construir_abas(self):
        """Recria as abas com base nos produtos em memória"""
        # Limpa abas antigas (exceto a estrutura)
        # Nota: Deletar e recriar abas é pesado, vamos fazer isso só no inicio ou reload manual
        
        # Agrupa produtos por categoria
        categorias = set()
        self.mapa_produtos = {}
        
        for p in self.todos_produtos:
            cat = p[8] if len(p) > 8 and p[8] else "Geral"
            categorias.add(cat)
            if cat not in self.mapa_produtos: self.mapa_produtos[cat] = []
            self.mapa_produtos[cat].append(p)
            
        # Recria estrutura de abas
        try:
            for aba in self.tab_view._tab_dict.keys():
                self.tab_view.delete(aba)
        except: pass

        self.tab_view.add("Todos")
        self.renderizar_grade("Todos", self.todos_produtos) # Renderiza Todos
        
        for cat in sorted(list(categorias)):
            if cat != "Todos":
                self.tab_view.add(cat)
                self.renderizar_grade(cat, self.mapa_produtos[cat])

    def renderizar_grade(self, aba, lista_produtos):
        """Desenha os cards dentro de uma aba específica"""
        scroll = ctk.CTkScrollableFrame(self.tab_view.tab(aba), fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        colunas = 3
        # Limita visualização inicial se tiver muitos itens para não travar (Paginação visual simples)
        # Mostra todos, mas cuidado com milhares de itens.
        
        for i, p in enumerate(lista_produtos):
            row = i // colunas; col = i % colunas
            
            # Layout do Card Compacto
            card = ctk.CTkFrame(scroll, fg_color=COR_FUNDO_CARD, border_width=1, border_color="#333")
            card.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            scroll.grid_columnconfigure(col, weight=1)
            
            nome = p[1][:20] + ".." if len(p[1]) > 20 else p[1]
            preco = float(p[3] or 0)
            est = int(p[2] or 0)
            
            # Conteúdo
            ctk.CTkLabel(card, text=nome, font=("Arial", 12, "bold")).pack(pady=(5,0))
            
            cor_est = COR_VERDE_NEON if est > 5 else (COR_AMARELO_ALERTA if est > 0 else COR_VERMELHO_ERRO)
            ctk.CTkLabel(card, text=f"Est: {est}   |   R$ {preco:.2f}", text_color=cor_est, font=("Arial", 11)).pack(pady=2)
            
            state = "normal" if est > 0 else "disabled"
            color = COR_VERDE_ESCURO if est > 0 else "gray"
            
            ctk.CTkButton(card, text="ADICIONAR", height=25, fg_color=color, state=state,
                          command=lambda item=p: self.add_cart(item)).pack(fill="x", padx=5, pady=5)

    def filtrar_produtos_local(self, _=None):
        """Filtra a lista em memória sem ir ao banco de dados (Muito mais rápido)"""
        termo = self.busca.get().lower()
        if not termo: return # Se vazio, não faz nada (mantém como está)
        
        # Limpa aba 'Todos'
        for w in self.tab_view.tab("Todos").winfo_children(): w.destroy()
        
        # Filtra
        if termo.isdigit():
            filtrados = [p for p in self.todos_produtos if str(p[0]) == termo]
        else:
            filtrados = [p for p in self.todos_produtos if termo in p[1].lower()]
            
        # Redesenha apenas a aba Todos (foca nela)
        self.tab_view.set("Todos")
        self.renderizar_grade("Todos", filtrados)

    # --- CARRINHO ---
    def add_cart(self, p):
        pid, pnome, pest, pvenda, pcusto = p[0], p[1], int(p[2]), float(p[3]), float(p[4])
        
        exist = next((i for i in self.carrinho if i['id'] == pid), None)
        qtd = exist['qtd'] if exist else 0
        
        if qtd + 1 > pest: return messagebox.showwarning("Estoque", f"Apenas {pest} un. disponíveis.")

        if exist:
            exist['qtd'] += 1
            exist['total'] = exist['qtd'] * pvenda
            exist['lucro'] = exist['qtd'] * (pvenda - pcusto)
        else:
            self.carrinho.append({'id': pid, 'nome': pnome, 'qtd': 1, 'preco': pvenda, 'custo': pcusto, 'total': pvenda, 'lucro': pvenda-pcusto})
        
        self.render_cart()

    def remover_item(self):
        s = self.tr.selection()
        if s:
            try:
                # Pega o nome do item na coluna 1 (Item)
                nome = self.tr.item(s[0], 'values')[1]
                self.carrinho = [i for i in self.carrinho if i['nome'] != nome]
                self.render_cart()
            except: pass

    def render_cart(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        total = 0.0
        itens = 0
        for i in self.carrinho:
            self.tr.insert("", "end", values=(f"{i['qtd']}x", i['nome'], f"{i['total']:.2f}"))
            total += i['total']
            itens += i['qtd']
        self.lt.configure(text=f"R$ {total:.2f}")
        self.lbl_itens_count.configure(text=f"{itens} itens")

    # --- CLIENTE ---
    def abrir_selecao_cliente(self):
        top = ctk.CTkToplevel(self); top.title("Cliente"); top.geometry("400x300"); top.grab_set()
        ctk.CTkLabel(top, text="Selecionar / Cadastrar", font=(FONT_MAIN, 14)).pack(pady=10)
        
        f_in = ctk.CTkFrame(top); f_in.pack(fill="x", padx=10)
        e = ctk.CTkEntry(f_in, placeholder_text="Nome do cliente..."); e.pack(side="left", fill="x", expand=True)
        
        # Botão Cadastro Rápido (Integrado)
        def novo_rapido():
            nome = e.get()
            if nome:
                ok, cid = db.cadastrar_cliente(nome, "", "") # Cadastra só com nome
                if ok: 
                    self.set_cli({'id': cid, 'nome': nome})
                    top.destroy()
                    messagebox.showinfo("Ok", "Cliente cadastrado e selecionado!")
        
        ctk.CTkButton(f_in, text="+ Novo", width=60, command=novo_rapido).pack(side="right", padx=5)

        scroll = ctk.CTkScrollableFrame(top); scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        def buscar(_=None):
            for w in scroll.winfo_children(): w.destroy()
            termo = e.get()
            # Botão Consumidor Final
            ctk.CTkButton(scroll, text="👤 Consumidor Final", fg_color="gray", command=lambda: [self.set_cli(None), top.destroy()]).pack(fill="x", pady=2)
            # Resultados do Banco
            for c in db.buscar_clientes(termo):
                ctk.CTkButton(scroll, text=f"{c[1]}", fg_color="#2c3e50", anchor="w", 
                              command=lambda x=c: [self.set_cli({'id':x[0], 'nome':x[1]}), top.destroy()]).pack(fill="x", pady=2)
        
        e.bind("<KeyRelease>", buscar); buscar()

    def set_cli(self, c):
        self.cli = c
        txt = c['nome'] if c else "Consumidor Final"
        self.lbl_cli.configure(text=txt, text_color=COR_VERDE_NEON if c else "white")

    # --- FINALIZAR ---
    def finalizar(self):
        if not self.carrinho: return messagebox.showwarning("Vazio", "Carrinho vazio.")
        if not messagebox.askyesno("Confirmar", f"Finalizar venda de {self.lt.cget('text')}?"): return
        
        cid = self.cli['id'] if self.cli else None
        ok, msg = db.registrar_venda_lote(self.carrinho, cid, self.pg.get())
        
        if ok:
            messagebox.showinfo("Sucesso", "Venda Realizada!")
            self.carrinho = []; self.set_cli(None); self.render_cart()
            self.recarregar_dados() # Recarrega estoque do banco
        else:
            messagebox.showerror("Erro", msg)

    def update_view(self): 
        # Chamado ao trocar de aba, recarrega dados para garantir estoque atualizado
        self.recarregar_dados()

class PageHistorico(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Header com Botões
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.pack(fill="x", pady=10)
        
        ctk.CTkLabel(h, text="Histórico de Vendas", font=(FONT_MAIN, 20, "bold")).pack(side="left")
        
        # --- BOTÕES DE AÇÃO ---
        
        # Botão Excel (Novo - Destaque Verde Neon)
        ctk.CTkButton(h, text="📊 Baixar Excel Completo", width=200, 
                      fg_color="#2ecc71", text_color="black", font=("Arial", 12, "bold"), 
                      command=self.exportar_excel_completo).pack(side="right", padx=5)

        # Botão PDF (Reposição)
        ctk.CTkButton(h, text="📦 Rel. Reposição (PDF)", width=180, 
                      fg_color="#9b59b6", font=("Arial", 12, "bold"), 
                      command=self.gerar_relatorio_reposicao).pack(side="right", padx=5)
        
        # Outros botões
        ctk.CTkButton(h, text="✏️ Editar Pgto", width=120, fg_color="#f39c12", text_color="black", command=self.editar_venda).pack(side="right", padx=5)
        ctk.CTkButton(h, text="🔄", width=40, command=self.update_view).pack(side="right", padx=5)

        # Tabela
        cols = ("ID", "Data", "Cliente", "Total", "Pgto", "Itens")
        self.tr = ttk.Treeview(self, columns=cols, show="headings", height=20)
        
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=50, anchor="center")
        self.tr.heading("Data", text="Data/Hora"); self.tr.column("Data", width=140, anchor="center")
        self.tr.heading("Cliente", text="Cliente"); self.tr.column("Cliente", width=150)
        self.tr.heading("Total", text="Total (R$)"); self.tr.column("Total", width=100, anchor="e") # Alinhado direita
        self.tr.heading("Pgto", text="Método"); self.tr.column("Pgto", width=100, anchor="center")
        self.tr.heading("Itens", text="Resumo do Pedido"); self.tr.column("Itens", width=400)
        
        self.tr.pack(fill="both", expand=True)
        
        self.update_view()

    def update_view(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        rows = db.get_historico_vendas()
        for r in rows:
            # Tratamento de valor para exibição
            try:
                val_str = str(r[3]) if r[3] is not None else "0"
                # Remove simbolos para garantir que seja numero, depois formata
                val_limpo = val_str.replace("R$", "").replace(" ", "").replace(",", ".")
                valor_final = float(val_limpo)
                valor_exibicao = f"R$ {valor_final:.2f}"
            except: 
                valor_final = 0.0
                valor_exibicao = "R$ 0.00"
            
            item_desc = r[5] if len(r) > 5 else "-"
            # r = (id, data, cliente, total_raw, pgto, itens)
            self.tr.insert("", "end", values=(r[0], r[1], r[2], valor_exibicao, r[4], item_desc))

    def editar_venda(self):
        s = self.tr.selection()
        if not s: return messagebox.showwarning("Aviso", "Selecione uma venda na tabela para editar.")
        item = self.tr.item(s[0], 'values')
        vid, pgto_atual = item[0], item[4]
        
        top = ctk.CTkToplevel(self); top.geometry("300x200"); top.title("Editar Pagamento"); top.grab_set()
        ctk.CTkLabel(top, text=f"Editando Venda #{vid}", font=(FONT_MAIN, 16, "bold")).pack(pady=20)
        
        opt = ctk.CTkOptionMenu(top, values=["Dinheiro", "Pix", "Cartão", "Débito", "Crédito"])
        opt.set(pgto_atual)
        opt.pack(pady=10)
        
        def salvar():
            db.atualizar_venda(vid, opt.get())
            top.destroy()
            self.update_view()
            messagebox.showinfo("Sucesso", "Método de pagamento atualizado!")
            
        ctk.CTkButton(top, text="Salvar Alteração", fg_color=COR_VERDE_PRINCIPAL, command=salvar).pack(pady=20)

    # --- NOVA EXPORTAÇÃO EXCEL ---
    def exportar_excel_completo(self):
        try:
            rows = db.get_historico_vendas()
            if not rows: return messagebox.showwarning("Vazio", "Não há vendas para exportar.")

            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx", 
                filetypes=[("Excel", "*.xlsx")],
                initialfile=f"Historico_Vendas_{datetime.now().strftime('%Y-%m-%d')}"
            )
            if not filename: return

            dados_limpos = []
            for r in rows:
                # [CORREÇÃO] Tratamento robusto de moeda
                try:
                    val_str = str(r[3])
                    # Remove R$, espaços e converte vírgula para ponto APENAS se for decimal
                    # Ex: 1.200,00 -> remove ponto milhar -> 1200,00 -> troca virgula -> 1200.00
                    val_limpo = val_str.replace("R$", "").strip().replace(".", "").replace(",", ".")
                    val_float = float(val_limpo)
                except: 
                    val_float = 0.0

                dados_limpos.append({
                    "ID": r[0],
                    "Data": r[1],
                    "Cliente": r[2],
                    "Total": val_float,
                    "Pagamento": r[4],
                    "Itens": r[5]
                })

            df = pd.DataFrame(dados_limpos)

            # Agrupa dados para insights
            df_resumo = df.groupby("Pagamento")["Total"].sum().reset_index()
            df_resumo["Total"] = df_resumo["Total"].apply(lambda x: f"R$ {x:,.2f}")

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Vendas', index=False)
                df_resumo.to_excel(writer, sheet_name='Resumo Financeiro', index=False)

            messagebox.showinfo("Sucesso", "Relatório Excel gerado com sucesso!")

        except ImportError:
            messagebox.showerror("Erro", "Instale: pip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar: {str(e)}")

    # --- RELATÓRIO DE REPOSIÇÃO (Mantido do seu código) ---
    def gerar_relatorio_reposicao(self):
        try:
            filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=f"Reposicao_Semanal_{datetime.now().strftime('%d-%m')}")
            if not filename: return
            
            dados = db.get_dados_reposicao()
            
            c = canvas.Canvas(filename, pagesize=A4)
            w, h = A4
            
            # Cabeçalho
            c.setFillColor(HexColor("#2c3e50"))
            c.rect(0, h-100, w, 100, fill=True, stroke=False)
            
            c.setFillColor(HexColor("#ffffff"))
            c.setFont("Helvetica-Bold", 22)
            c.drawString(40, h-50, "RELATÓRIO DE REPOSIÇÃO SEMANAL")
            c.setFont("Helvetica", 12)
            c.drawString(40, h-75, "Baseado na rotatividade dos últimos 7 dias")
            c.drawRightString(w-40, h-50, datetime.now().strftime("%d/%m/%Y"), )
            
            # Legenda
            c.setFillColor(HexColor("#000000"))
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(40, h-120, "Cálculo: (Vendas 7D + Margem Segurança) - Estoque Atual.")

            y = h - 150
            
            # Títulos Tabela
            c.setFillColor(HexColor("#ecf0f1"))
            c.rect(30, y-5, w-60, 20, fill=True, stroke=False)
            c.setFillColor(HexColor("#000000"))
            c.setFont("Helvetica-Bold", 9)
            
            c.drawString(40, y, "PRODUTO")
            c.drawString(280, y, "ESTOQUE ATUAL")
            c.drawString(380, y, "VENDIDOS (7D)")
            c.drawString(480, y, "SUGESTÃO COMPRA")
            
            y -= 20
            c.setFont("Helvetica", 9)
            
            for row in dados:
                if y < 50: c.showPage(); y = h - 50
                
                nome = row[0][:45]
                est = str(row[1])
                vnd = str(row[2])
                sug = str(row[3])
                status = row[4]
                
                if "CRÍTICO" in status: c.setFillColor(HexColor("#e74c3c"))
                elif "ALERTA" in status: c.setFillColor(HexColor("#f39c12"))
                else: c.setFillColor(HexColor("#000000"))
                
                c.drawString(40, y, nome)
                c.drawString(280, y, est)
                c.drawString(380, y, vnd)
                
                sug_text = f"+ {sug} un." if int(sug) > 0 else "-"
                if int(sug) > 0: c.setFont("Helvetica-Bold", 9)
                c.drawString(480, y, sug_text)
                c.setFont("Helvetica", 9)
                
                c.setStrokeColor(HexColor("#ecf0f1"))
                c.line(30, y-5, w-30, y-5)
                y -= 15
            
            c.save()
            messagebox.showinfo("Sucesso", "Relatório de Reposição gerado com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))

class PageFuzue(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Cabeçalho (Usando PACK)
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.pack(fill="x", pady=(0,10)) 
        ctk.CTkLabel(h, text="🍹 Fuzuê Friends - Gestão de Evento", font=(FONT_MAIN, 20), text_color="#ff9f43").pack(side="left")
        
        self.tab = ctk.CTkTabview(self)
        self.tab.pack(fill="both", expand=True) # Usando PACK
        
        # --- ABA 1: CAIXA DO DIA ---
        t1 = self.tab.add("Caixa do Evento")
        
        # Seleção de Produtos (Usando PACK)
        f_sel = ctk.CTkFrame(t1, fg_color=COR_FUNDO_CARD)
        f_sel.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(f_sel, text="Adicionar Item:").pack(side="left", padx=10)
        self.combo_prod = ctk.CTkComboBox(f_sel, width=300)
        self.combo_prod.pack(side="left", padx=10)
        
        ctk.CTkButton(f_sel, text="➕ Adicionar", command=self.add_item).pack(side="left", padx=5)
        
        # Tabela de Controle (Usando PACK)
        f_table = ctk.CTkFrame(t1, fg_color="transparent")
        f_table.pack(fill="both", expand=True, padx=10)
        
        self.tr = ttk.Treeview(f_table, columns=("ID", "Item", "Estoque Loja", "Preço", "VENDIDOS"), show="headings")
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=30)
        self.tr.heading("Item", text="Produto"); self.tr.column("Item", width=250)
        self.tr.heading("Estoque Loja", text="Est. Loja"); self.tr.column("Estoque Loja", width=80, anchor="center")
        self.tr.heading("Preço", text="Preço Venda"); self.tr.column("Preço", width=80)
        self.tr.heading("VENDIDOS", text="QTD VENDIDA (Clique 2x)", anchor="center"); self.tr.column("VENDIDOS", width=180, anchor="center")
        self.tr.pack(fill="both", expand=True)
        
        self.tr.bind("<Double-1>", self.editar_qtd_vendida)
        
        # Rodapé
        f_foot = ctk.CTkFrame(t1, fg_color="transparent")
        f_foot.pack(fill="x", pady=10, padx=10)
        
        self.lbl_resumo = ctk.CTkLabel(f_foot, text="Total Vendido: R$ 0.00 | Lucro: R$ 0.00", font=("Arial", 16, "bold"), text_color=COR_VERDE_NEON)
        self.lbl_resumo.pack(side="left")
        
        ctk.CTkButton(f_foot, text="✅ FECHAR CAIXA E BAIXAR ESTOQUE", fg_color=COR_VERDE_PRINCIPAL, height=40, font=("Arial", 12, "bold"), command=self.fechar_caixa).pack(side="right")

        # --- ABA 2: HISTÓRICO ---
        t2 = self.tab.add("Histórico de Eventos")
        
        f_hist = ctk.CTkFrame(t2, fg_color="transparent")
        f_hist.pack(fill="both", expand=True, padx=10, pady=10)

        self.tr_hist = ttk.Treeview(f_hist, columns=("Data", "Total", "Lucro", "Resumo"), show="headings")
        self.tr_hist.heading("Data", text="Data"); self.tr_hist.column("Data", width=120)
        self.tr_hist.heading("Total", text="Total"); self.tr_hist.column("Total", width=100)
        self.tr_hist.heading("Lucro", text="Lucro"); self.tr_hist.column("Lucro", width=100)
        self.tr_hist.heading("Resumo", text="Itens"); self.tr_hist.column("Resumo", width=500)
        self.tr_hist.pack(fill="both", expand=True)
        
        ctk.CTkButton(t2, text="🔄 Atualizar Histórico", command=self.load_hist).pack(pady=10)

        # Variáveis
        self.itens_fuzue = [] 
        self.mapa_prods = {}
        self.total_cache = (0.0, 0.0)
        
        self.carregar_produtos_combo()
        self.load_hist()

    def update_view(self):
        self.carregar_produtos_combo()
        self.load_hist()

    def carregar_produtos_combo(self):
        prods = db.buscar_produtos("")
        self.mapa_prods = {f"{p[1]} (ID: {p[0]})": p for p in prods} 
        if self.mapa_prods:
            self.combo_prod.configure(values=list(self.mapa_prods.keys()))
            self.combo_prod.set(list(self.mapa_prods.keys())[0])

    def add_item(self):
        escolha = self.combo_prod.get()
        if not escolha or escolha not in self.mapa_prods: return
        p = self.mapa_prods[escolha]
        
        # Evita duplicatas na lista
        for it in self.itens_fuzue:
            if it['id'] == p[0]: return
            
        self.itens_fuzue.append({
            'id': p[0], 'nome': p[1], 'est': p[2], 'custo': float(p[4]), 'venda': float(p[3]), 'vendidos': 0
        })
        self.render_table()

    def render_table(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        tot_v, tot_l = 0.0, 0.0
        
        for it in self.itens_fuzue:
            tag = "vendido" if it['vendidos'] > 0 else "normal" # Destaque visual
            self.tr.insert("", "end", values=(it['id'], it['nome'], it['est'], f"R$ {it['venda']:.2f}", it['vendidos']), tags=(tag,))
            tot_v += it['vendidos'] * it['venda']
            tot_l += it['vendidos'] * (it['venda'] - it['custo'])
            
        self.lbl_resumo.configure(text=f"Total Vendido: R$ {tot_v:.2f} | Lucro: R$ {tot_l:.2f}")
        self.total_cache = (tot_v, tot_l)

    def editar_qtd_vendida(self, _):
        sel = self.tr.selection()
        if not sel: return
        
        item_vals = self.tr.item(sel[0], 'values')
        pid = int(item_vals[0])
        
        for it in self.itens_fuzue:
            if it['id'] == pid:
                dialog = ctk.CTkInputDialog(text=f"Quantos '{it['nome']}' foram vendidos?", title="Qtd Vendida")
                res = dialog.get_input()
                if res and res.isdigit():
                    qtd = int(res)
                    if qtd > it['est']:
                        messagebox.showwarning("Ops", f"Estoque insuficiente ({it['est']})")
                        return
                    it['vendidos'] = qtd
                    self.render_table()
                break

    def fechar_caixa(self):
        if not self.itens_fuzue: return messagebox.showwarning("Vazio", "Adicione itens.")
        
        tot_v, tot_l = self.total_cache
        
        # Verifica se teve vendas
        itens_vendidos = [i for i in self.itens_fuzue if i['vendidos'] > 0]
        if not itens_vendidos:
             if not messagebox.askyesno("Confirmar", "Nenhuma venda registrada. Salvar zerado?"): return

        if not messagebox.askyesno("Finalizar", f"Total: R$ {tot_v:.2f}\nIsso baixará o estoque da loja. Confirmar?"): return
        
        # 1. Monta resumo
        resumo_str = ", ".join([f"{i['vendidos']}x {i['nome']}" for i in itens_vendidos])
        if not resumo_str: resumo_str = "Sem vendas"
        
        # 2. Baixa Estoque (Gera Venda no Sistema)
        carrinho_fake = []
        for i in itens_vendidos:
            carrinho_fake.append({
                'id': i['id'],
                'qtd': i['vendidos'],
                'total': i['vendidos'] * i['venda'],
                'lucro': i['vendidos'] * (i['venda'] - i['custo'])
            })
        
        if carrinho_fake:
            db.registrar_venda_lote(carrinho_fake, None, "Fuzue Bar")
            
        # 3. Salva histórico do evento
        db.salvar_fuzue(tot_v, tot_l, resumo_str)
        
        messagebox.showinfo("Sucesso", "Caixa Fechado e Estoque Atualizado!")
        self.itens_fuzue = []
        self.render_table()
        self.load_hist()

    def load_hist(self):
        for i in self.tr_hist.get_children(): self.tr_hist.delete(i)
        for h in db.get_historico_fuzue():
            # Formatação simples da data
            dt_show = h[1]
            try: dt_show = datetime.strptime(h[1], '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M')
            except: pass
            self.tr_hist.insert("", "end", values=(dt_show, f"R$ {h[2]:.2f}", f"R$ {h[3]:.2f}", h[4]))

class PageClientes(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Barra superior
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(fill="x", pady=10)
        self.b = ctk.CTkEntry(f, placeholder_text="Buscar cliente...", font=(FONT_BODY, 12))
        self.b.pack(side="left", fill="x", expand=True)
        self.b.bind("<KeyRelease>", self.l)
        
        # Botões
        ctk.CTkButton(f, text="📜 Ver Histórico", width=120, fg_color="#3498db", command=self.ver_historico).pack(side="right", padx=5)

        # Tabela
        self.tr = ttk.Treeview(self, columns=("ID","Nome","Tel"), show="headings", height=15)
        for c in ("ID","Nome","Tel"): self.tr.heading(c, text=c)
        self.tr.pack(fill="both", expand=True, pady=10)
        self.tr.bind("<<TreeviewSelect>>", self.sel)
        self.tr.bind("<Double-1>", lambda e: self.ver_historico()) 
        
        # Área de Edição
        f_edit = ctk.CTkFrame(self); f_edit.pack(fill="x")
        self.en = ctk.CTkEntry(f_edit, placeholder_text="Nome"); self.en.pack(side="left", fill="x", expand=True, padx=2)
        self.et = ctk.CTkEntry(f_edit, placeholder_text="Tel"); self.et.pack(side="left", fill="x", expand=True, padx=2)
        self.ee = ctk.CTkEntry(f_edit, placeholder_text="Email"); self.ee.pack(side="left", fill="x", expand=True, padx=2) # Novo campo email
        
        b = ctk.CTkFrame(self, fg_color="transparent"); b.pack(pady=10)
        ctk.CTkButton(b, text="Limpar", width=80, fg_color="gray", command=self.limp).pack(side="left", padx=5)
        ctk.CTkButton(b, text="Salvar", width=80, fg_color=COR_VERDE_PRINCIPAL, command=self.sv).pack(side="left", padx=5)
        ctk.CTkButton(b, text="Excluir", width=80, fg_color=COR_VERMELHO_ERRO, command=self.ex).pack(side="left", padx=5)
        
        self.sid=None
        self.l()

    def l(self, _=None):
        for i in self.tr.get_children(): self.tr.delete(i)
        for c in db.buscar_clientes(self.b.get()): self.tr.insert("", "end", values=(c[0], c[1], c[2]))
        
    def sel(self, _):
        s=self.tr.selection()
        if s: 
            v=self.tr.item(s[0],'values')
            self.sid=v[0]
            self.en.delete(0,'end'); self.en.insert(0,v[1])
            self.et.delete(0,'end'); self.et.insert(0,v[2])
            # Se tiver email na tupla (ajuste conforme seu DB)
            self.ee.delete(0,'end') 

    def limp(self): 
        self.sid=None; self.en.delete(0,'end'); self.et.delete(0,'end'); self.ee.delete(0,'end')
    
    def sv(self):
        if self.sid: db.atualizar_cliente(self.sid, self.en.get(), self.et.get(), self.ee.get())
        else: db.cadastrar_cliente(self.en.get(), self.et.get(), self.ee.get())
        self.l(); self.limp()
        
    def ex(self): 
        if self.sid and messagebox.askyesno("?","Excluir?"): db.excluir_cliente(self.sid); self.l(); self.limp()

    # SUBSTITUA O MÉTODO ver_historico NA CLASSE PageClientes
    def ver_historico(self):
        s = self.tr.selection()
        if not s: return messagebox.showwarning("Aviso", "Selecione um cliente para ver o histórico.")
        
        item = self.tr.item(s[0], 'values')
        cid = item[0]
        nome = item[1]
        
        compras = db.get_compras_cliente(cid)
        
        top = ctk.CTkToplevel(self)
        top.geometry("600x400")
        top.title(f"Histórico: {nome}")
        
        ctk.CTkLabel(top, text=f"Compras de {nome}", font=(FONT_MAIN, 16)).pack(pady=10)
        
        if not compras:
            ctk.CTkLabel(top, text="Nenhuma compra registrada.", text_color="gray").pack(pady=20)
            return

        cols = ("Data", "Produto", "Qtd", "Total", "Pgto")
        tr_h = ttk.Treeview(top, columns=cols, show="headings")
        tr_h.heading("Data", text="Data"); tr_h.column("Data", width=120)
        tr_h.heading("Produto", text="Produto"); tr_h.column("Produto", width=150)
        tr_h.heading("Qtd", text="Qtd"); tr_h.column("Qtd", width=40)
        tr_h.heading("Total", text="Total"); tr_h.column("Total", width=70)
        tr_h.heading("Pgto", text="Pgto"); tr_h.column("Pgto", width=70)
        tr_h.pack(fill="both", expand=True, padx=10, pady=10)
        
        total_gasto = 0.0
        for c in compras:
            # c = (data, produto_nome, qtd, total, pgto)
            valor = float(c[3] if c[3] else 0)
            tr_h.insert("", "end", values=(c[0], c[1], c[2], f"R$ {valor:.2f}", c[4]))
            total_gasto += valor
            
        ctk.CTkLabel(top, text=f"Total Gasto em Vida: R$ {total_gasto:.2f}", font=(FONT_MAIN, 14), text_color=COR_VERDE_NEON).pack(pady=10)

    def update_view(self): self.l()

class PageClientes(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # Barra superior
        f = ctk.CTkFrame(self, fg_color="transparent"); f.pack(fill="x", pady=10)
        self.b = ctk.CTkEntry(f, placeholder_text="Buscar cliente...", font=(FONT_BODY, 12))
        self.b.pack(side="left", fill="x", expand=True)
        self.b.bind("<KeyRelease>", self.l)
        
        # Botões
        ctk.CTkButton(f, text="📜 Ver Histórico de Compras", fg_color="#3498db", command=self.ver_historico).pack(side="right", padx=5)

        # Tabela
        self.tr = ttk.Treeview(self, columns=("ID","Nome","Tel"), show="headings", height=15)
        for c in ("ID","Nome","Tel"): self.tr.heading(c, text=c)
        self.tr.pack(fill="both", expand=True, pady=10)
        self.tr.bind("<<TreeviewSelect>>", self.sel)
        self.tr.bind("<Double-1>", lambda e: self.ver_historico()) 
        
        # Área de Edição
        f_edit = ctk.CTkFrame(self); f_edit.pack(fill="x")
        self.en = ctk.CTkEntry(f_edit, placeholder_text="Nome"); self.en.pack(side="left", fill="x", expand=True, padx=2)
        self.et = ctk.CTkEntry(f_edit, placeholder_text="Tel"); self.et.pack(side="left", fill="x", expand=True, padx=2)
        self.ee = ctk.CTkEntry(f_edit, placeholder_text="Email"); self.ee.pack(side="left", fill="x", expand=True, padx=2)
        
        b = ctk.CTkFrame(self, fg_color="transparent"); b.pack(pady=10)
        ctk.CTkButton(b, text="Limpar", width=80, fg_color="gray", command=self.limp).pack(side="left", padx=5)
        ctk.CTkButton(b, text="Salvar", width=80, fg_color=COR_VERDE_PRINCIPAL, command=self.sv).pack(side="left", padx=5)
        ctk.CTkButton(b, text="Excluir", width=80, fg_color=COR_VERMELHO_ERRO, command=self.ex).pack(side="left", padx=5)
        
        self.sid=None
        self.l()

    def l(self, _=None):
        for i in self.tr.get_children(): self.tr.delete(i)
        for c in db.buscar_clientes(self.b.get()): self.tr.insert("", "end", values=(c[0], c[1], c[2]))
        
    def sel(self, _):
        s=self.tr.selection()
        if s: 
            v=self.tr.item(s[0],'values')
            self.sid=v[0]
            self.en.delete(0,'end'); self.en.insert(0,v[1])
            self.et.delete(0,'end'); self.et.insert(0,v[2])
            self.ee.delete(0,'end') 

    def limp(self): 
        self.sid=None; self.en.delete(0,'end'); self.et.delete(0,'end'); self.ee.delete(0,'end')
    
    def sv(self):
        if self.sid: db.atualizar_cliente(self.sid, self.en.get(), self.et.get(), self.ee.get())
        else: db.cadastrar_cliente(self.en.get(), self.et.get(), self.ee.get())
        self.l(); self.limp()
        
    def ex(self): 
        if self.sid and messagebox.askyesno("?","Excluir?"): db.excluir_cliente(self.sid); self.l(); self.limp()

    # --- MÉTODO ADICIONADO QUE FALTAVA ---
    def ver_historico(self, _=None):
        s = self.tr.selection()
        if not s: return messagebox.showwarning("Aviso", "Selecione um cliente para ver o histórico.")
        
        item = self.tr.item(s[0], 'values')
        cid = item[0]
        nome = item[1]
        
        compras = db.get_compras_cliente(cid)
        
        top = ctk.CTkToplevel(self)
        top.geometry("600x400")
        top.title(f"Histórico: {nome}")
        
        ctk.CTkLabel(top, text=f"Compras de {nome}", font=(FONT_MAIN, 16)).pack(pady=10)
        
        if not compras:
            ctk.CTkLabel(top, text="Nenhuma compra registrada.", text_color="gray").pack(pady=20)
            return

        cols = ("Data", "Produto", "Qtd", "Total", "Pgto")
        tr_h = ttk.Treeview(top, columns=cols, show="headings")
        tr_h.heading("Data", text="Data"); tr_h.column("Data", width=120)
        tr_h.heading("Produto", text="Produto"); tr_h.column("Produto", width=150)
        tr_h.heading("Qtd", text="Qtd"); tr_h.column("Qtd", width=40)
        tr_h.heading("Total", text="Total"); tr_h.column("Total", width=70)
        tr_h.heading("Pgto", text="Pgto"); tr_h.column("Pgto", width=70)
        tr_h.pack(fill="both", expand=True, padx=10, pady=10)
        
        total_gasto = 0.0
        for c in compras:
            try:
                # Tratamento de erro também aqui, só por segurança
                val_limpo = str(c[3]).replace("R$", "").replace(",", ".").strip()
                val = float(val_limpo)
            except: val = 0.0
            
            tr_h.insert("", "end", values=(c[0], c[1], c[2], f"R$ {val:.2f}", c[4]))
            total_gasto += val
            
        ctk.CTkLabel(top, text=f"Total Gasto em Vida: R$ {total_gasto:.2f}", font=(FONT_MAIN, 14), text_color=COR_VERDE_NEON).pack(pady=10)

    def update_view(self): self.l()

class PageEstoque(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.tab = ctk.CTkTabview(self, text_color=COR_VERDE_NEON)
        self.tab.pack(fill="both", expand=True)
        
        t1 = self.tab.add("📦 Gerenciar Estoque")
        t2 = self.tab.add("➕ Novo Item")
        t3 = self.tab.add("🛠️ Montagem de Kits")
        
        # --- ABA 1: GERENCIAR ---
        f_top = ctk.CTkFrame(t1, fg_color="transparent"); f_top.pack(fill="x", pady=5)
        
        self.bus = ctk.CTkEntry(f_top, placeholder_text="🔍 Buscar...", width=300)
        self.bus.pack(side="left", padx=5)
        self.bus.bind("<KeyRelease>", self.lst)
        
        self.filtro_cat = ctk.CTkOptionMenu(f_top, width=150, 
                                            values=["Todas", "Sedas", "Piteiras", "Cuias", "Fumos", "Tesouras", "Dichavadores", "Acessórios", "Kits", "Outros"], 
                                            command=self.lst)
        self.filtro_cat.pack(side="left", padx=5)
        
        ctk.CTkButton(f_top, text="🔄", width=50, command=self.lst).pack(side="right", padx=5)

        cols = ("ID", "Nome", "Estoque", "Custo", "Venda", "Categoria")
        self.tr = ttk.Treeview(t1, columns=cols, show="headings", height=12)
        
        self.tr.heading("ID", text="ID"); self.tr.column("ID", width=40, anchor="center")
        self.tr.heading("Nome", text="Produto"); self.tr.column("Nome", width=250)
        self.tr.heading("Estoque", text="Qtd"); self.tr.column("Estoque", width=60, anchor="center")
        self.tr.heading("Custo", text="Custo"); self.tr.column("Custo", width=80)
        self.tr.heading("Venda", text="Venda"); self.tr.column("Venda", width=80)
        self.tr.heading("Categoria", text="Cat"); self.tr.column("Categoria", width=100, anchor="center")
        
        self.tr.pack(fill="both", expand=True, pady=5)
        
        # Rodapé Totais
        self.f_totais = ctk.CTkFrame(t1, fg_color=COR_FUNDO_CARD, corner_radius=8)
        self.f_totais.pack(fill="x", pady=10)
        self.lbl_qtd_itens = ctk.CTkLabel(self.f_totais, text="Itens: 0", font=("Arial", 12))
        self.lbl_qtd_itens.pack(side="left", padx=20)
        self.lbl_custo_total = ctk.CTkLabel(self.f_totais, text="Custo Total: R$ 0.00", font=("Arial", 12, "bold"), text_color="#f39c12")
        self.lbl_custo_total.pack(side="left", padx=20)
        self.lbl_venda_total = ctk.CTkLabel(self.f_totais, text="Venda Total: R$ 0.00", font=("Arial", 12, "bold"), text_color=COR_VERDE_NEON)
        self.lbl_venda_total.pack(side="left", padx=20)

        # BOTÕES DE AÇÃO
        f_btns = ctk.CTkFrame(t1, fg_color="transparent"); f_btns.pack(fill="x", pady=5)
        
        ctk.CTkButton(f_btns, text="✏️ Editar / Repor", fg_color="#3498db", command=self.edt).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(f_btns, text="📊 Relatório (XLSX)", fg_color="#27ae60", font=("Arial", 12, "bold"), command=self.exportar_relatorio_estoque).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(f_btns, text="🗑️ Excluir", fg_color=COR_VERMELHO_ERRO, command=self.exc).pack(side="left", fill="x", expand=True, padx=5)

        # --- ABA 2: NOVO ITEM ---
        f = ctk.CTkScrollableFrame(t2); f.pack(fill="both", expand=True, padx=50)
        ctk.CTkLabel(f, text="Cadastro", font=(FONT_MAIN, 18, "bold")).pack(pady=15)
        self.en = self.ae("Nome", f)
        f_num = ctk.CTkFrame(f, fg_color="transparent"); f_num.pack(fill="x")
        self.eq = self.ae_grid("Qtd", f_num, 0)
        self.ec = self.ae_grid("Custo", f_num, 1)
        self.ep = self.ae_grid("Venda", f_num, 2)
        ctk.CTkLabel(f, text="Categoria", font=(FONT_MAIN, 12)).pack(anchor="w", pady=(10,0))
        self.cat = ctk.CTkOptionMenu(f, values=["Sedas", "Piteiras", "Cuias", "Fumos", "Tesouras", "Dichavadores", "Acessórios", "Kits", "Outros"])
        self.cat.pack(fill="x", pady=5)
        self.eo = self.ae("Obs", f)
        self.lbl_img = ctk.CTkLabel(f, text="-", text_color="gray"); self.lbl_img.pack()
        ctk.CTkButton(f, text="Foto", command=self.sel_img, fg_color="#555").pack(fill="x", pady=5)
        self.chk_dest = ctk.CTkCheckBox(f, text="Destaque?"); self.chk_dest.pack(pady=10)
        ctk.CTkButton(f, text="SALVAR", height=45, fg_color=COR_VERDE_PRINCIPAL, command=self.sv).pack(pady=10, fill="x")
        self.novo_img_path = ""

        # --- ABA 3: MONTAGEM E CRIAÇÃO DE KITS ---
        # 1. Configuração de Kits (Dinâmico)
        # Vamos usar um dicionário em memória, mas idealmente isso iria para uma tabela 'receitas_kit'
        # Por enquanto, carregamos os hardcoded e permitimos adicionar novos na sessão.
        self.KITS_CONFIG = {
            "Kit Start": {"preco": 15.00, "itens": ["Seda", "Piteira"]},
            "Kit Fire": {"preco": 25.00, "itens": ["Seda", "Piteira", "Isqueiro"]},
            "Kit Full Green": {"preco": 40.00, "itens": ["Seda", "Piteira", "Dichavador", "Isqueiro"]},
            "Kit Session": {"preco": 55.00, "itens": ["Seda", "Piteira", "Cuia", "Tesoura", "Isqueiro", "Mocó"]}
        }

        f_kit_main = ctk.CTkFrame(t3, fg_color="transparent")
        f_kit_main.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Lado Esquerdo: Produzir Kit Existente
        f_prod = ctk.CTkFrame(f_kit_main, fg_color=COR_FUNDO_CARD)
        f_prod.pack(side="left", fill="both", expand=True, padx=(0,10))
        
        ctk.CTkLabel(f_prod, text="🛠️ Produzir Kit", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.sel_kit_menu = ctk.CTkOptionMenu(f_prod, values=list(self.KITS_CONFIG.keys()), command=self.analisar_kit)
        self.sel_kit_menu.pack(pady=5)
        
        f_q = ctk.CTkFrame(f_prod, fg_color="transparent"); f_q.pack(pady=5)
        ctk.CTkLabel(f_q, text="Qtd:").pack(side="left")
        self.qtd_kit_entry = ctk.CTkEntry(f_q, width=50); self.qtd_kit_entry.insert(0,"1"); self.qtd_kit_entry.pack(side="left", padx=5)
        self.qtd_kit_entry.bind("<KeyRelease>", lambda e: self.calcular_totais_kit())
        
        self.scroll_ingredientes = ctk.CTkScrollableFrame(f_prod, height=200)
        self.scroll_ingredientes.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.lbl_custo_total = ctk.CTkLabel(f_prod, text="Custo: R$ 0.00")
        self.lbl_custo_total.pack()
        self.lbl_lucro_previsto = ctk.CTkLabel(f_prod, text="Lucro Previsto: R$ 0.00", text_color=COR_VERDE_NEON)
        self.lbl_lucro_previsto.pack()
        
        self.btn_produzir = ctk.CTkButton(f_prod, text="PRODUZIR", state="disabled", fg_color=COR_VERDE_PRINCIPAL, command=self.salvar_producao_kit)
        self.btn_produzir.pack(pady=15, padx=20, fill="x")

        # Lado Direito: Criar Novo Kit (Simples)
        f_new_kit = ctk.CTkFrame(f_kit_main, fg_color="#2c3e50")
        f_new_kit.pack(side="right", fill="y", padx=(10,0))
        
        ctk.CTkLabel(f_new_kit, text="✨ Novo Modelo de Kit", font=("Arial", 14, "bold")).pack(pady=10)
        self.nk_nome = ctk.CTkEntry(f_new_kit, placeholder_text="Nome do Kit (Ex: Kit Praia)"); self.nk_nome.pack(padx=10, pady=5)
        self.nk_preco = ctk.CTkEntry(f_new_kit, placeholder_text="Preço Venda (R$)"); self.nk_preco.pack(padx=10, pady=5)
        self.nk_itens = ctk.CTkTextbox(f_new_kit, height=100); self.nk_itens.pack(padx=10, pady=5)
        self.nk_itens.insert("0.0", "Ex: Seda, Piteira, Isqueiro\n(Um por linha ou virgula)")
        
        ctk.CTkButton(f_new_kit, text="Salvar Receita", fg_color="#f39c12", text_color="black", command=self.criar_novo_modelo_kit).pack(pady=10, padx=10)
        
        self.ingredientes_selecionados = {}
        self.custo_unitario_final = 0.0
        
        self.lst()

    # --- UTILITÁRIOS ---
    def ae(self, t, m): ctk.CTkLabel(m, text=t).pack(anchor="w"); e = ctk.CTkEntry(m); e.pack(fill="x", pady=(0,5)); return e
    def ae_grid(self, t, m, c): f=ctk.CTkFrame(m, fg_color="transparent"); f.grid(row=0, column=c, sticky="ew", padx=2); m.grid_columnconfigure(c, weight=1); ctk.CTkLabel(f, text=t).pack(anchor="w"); e=ctk.CTkEntry(f); e.pack(fill="x"); return e

    # --- LISTAGEM ---
    def lst(self, _=None):
        for i in self.tr.get_children(): self.tr.delete(i)
        termo = self.bus.get(); cat_filtro = self.filtro_cat.get()
        prods = db.buscar_produtos(termo)
        
        ti=0; tf=0; vc=0.0; vv=0.0
        for p in prods:
            cat = p[8] if len(p) > 8 else "Geral"
            if cat_filtro != "Todas" and cat_filtro != cat: continue
            
            custo = float(p[4] or 0); venda = float(p[3] or 0); est = int(p[2] or 0)
            self.tr.insert("", "end", values=(p[0], p[1], est, f"R$ {custo:.2f}", f"R$ {venda:.2f}", cat))
            ti+=1; tf+=est; vc+=(est*custo); vv+=(est*venda)
            
        self.lbl_qtd_itens.configure(text=f"Itens: {ti}")
        self.lbl_custo_total.configure(text=f"Patrimônio: R$ {vc:.2f}")
        self.lbl_venda_total.configure(text=f"Potencial: R$ {vv:.2f}")

    # --- EDIÇÃO ---
    def edt(self):
        s = self.tr.selection()
        if not s: return messagebox.showwarning("Aviso", "Selecione um item.")
        pid = self.tr.item(s[0], 'values')[0]
        conn = db.conectar()
        # 0:id, 1:nome, 2:est, 3:venda, 4:custo, 5:obs, 6:img, 7:dest, 8:cat
        p = conn.execute("SELECT id, nome, qtd_estoque, preco_venda, custo_unitario, observacoes, imagem_url, destaque, categoria FROM produtos WHERE id=?", (pid,)).fetchone()
        conn.close()
        
        if not p: return messagebox.showerror("Erro", "Item não encontrado.")

        top = ctk.CTkToplevel(self); top.geometry("500x700"); top.title("Editar"); top.grab_set()
        ctk.CTkLabel(top, text=f"Editando: {p[1]}", font=(FONT_MAIN, 16, "bold")).pack(pady=10)
        ctk.CTkLabel(top, text="Nome:").pack(anchor="w", padx=20); en = ctk.CTkEntry(top); en.pack(fill="x", padx=20); en.insert(0, p[1])
        
        f_p = ctk.CTkFrame(top, fg_color="transparent"); f_p.pack(fill="x", padx=20, pady=5)
        # CUIDADO COM OS ÍNDICES AQUI: p[4] é custo, p[3] é venda
        ctk.CTkLabel(f_p, text="Custo:").pack(side="left"); ec = ctk.CTkEntry(f_p, width=100); ec.pack(side="left"); ec.insert(0, f"{p[4]:.2f}")
        ctk.CTkLabel(f_p, text="Venda:").pack(side="left", padx=(10,0)); ep = ctk.CTkEntry(f_p, width=100); ep.pack(side="left"); ep.insert(0, f"{p[3]:.2f}")
        
        f_r = ctk.CTkFrame(top, fg_color="#2c3e50"); f_r.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(f_r, text="Reposição de Estoque (+):", text_color="white").pack()
        ea = ctk.CTkEntry(f_r, justify="center"); ea.pack(pady=5); ea.insert(0, "0")
        
        ctk.CTkLabel(top, text="Categoria:").pack(anchor="w", padx=20)
        cat_atual = p[8] if p[8] else "Outros"
        cat_var = ctk.StringVar(value=cat_atual)
        ctk.CTkOptionMenu(top, variable=cat_var, values=["Sedas", "Piteiras", "Cuias", "Fumos", "Tesouras", "Dichavadores", "Acessórios", "Kits", "Outros"]).pack(fill="x", padx=20)

        self.edit_nova_img_path = ""
        lbl_f = ctk.CTkLabel(top, text=f"Foto: {os.path.basename(p[6]) if p[6] else '-'}", text_color="gray"); lbl_f.pack()
        ctk.CTkButton(top, text="Trocar Foto", height=30, fg_color="#555", command=lambda: self.sel_img_edit(lbl_f)).pack(pady=5)
        ctk.CTkLabel(top, text="Observação:").pack(anchor="w", padx=20); eo = ctk.CTkEntry(top); eo.pack(fill="x", padx=20); eo.insert(0, p[5] if p[5] else "")
        chk = ctk.CTkCheckBox(top, text="Destaque?"); chk.pack(pady=10)
        if p[7] == 1: chk.select()

        def salvar():
            try:
                c = float(ec.get().replace(",", ".")); v = float(ep.get().replace(",", "."))
                ajuste = int(ea.get())
                url = self.processar_img(self.edit_nova_img_path) if self.edit_nova_img_path else p[6]
                dest = 1 if chk.get() else 0
                ok, msg = db.editar_produto_completo(pid, en.get(), c, v, ajuste, eo.get(), url, cat_var.get(), dest)
                if ok: messagebox.showinfo("Sucesso", "Atualizado!"); top.destroy(); self.lst()
                else: messagebox.showerror("Erro", msg)
            except Exception as e: messagebox.showerror("Erro", str(e))
        ctk.CTkButton(top, text="SALVAR", height=40, fg_color=COR_VERDE_PRINCIPAL, command=salvar).pack(pady=20, fill="x", padx=20)

    # --- SUPORTE ---
    def sel_img(self): 
        f = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.png")])
        if f: self.novo_img_path = f; self.lbl_img.configure(text=os.path.basename(f), text_color=COR_VERDE_NEON)
    def sel_img_edit(self, lbl): 
        f = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.png")])
        if f: self.edit_nova_img_path = f; lbl.configure(text=f"Nova: {os.path.basename(f)}", text_color=COR_VERDE_NEON)
    def processar_img(self, path):
        if not path or not os.path.exists(path): return ""
        try:
            if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)
            nome = f"prod_{datetime.now().strftime('%Y%m%d%H%M%S')}{os.path.splitext(path)[1]}"
            shutil.copy(path, os.path.join(UPLOAD_DIR, nome)); return f"static/uploads/{nome}"
        except: return ""
    def sv(self):
        try:
            db.cadastrar_produto(self.en.get(), int(self.eq.get() or 0), float(self.ec.get().replace(",",".") or 0), float(self.ep.get().replace(",",".") or 0), self.eo.get(), self.processar_img(self.novo_img_path), self.cat.get(), 1 if self.chk_dest.get() else 0)
            messagebox.showinfo("Sucesso", "Salvo!"); self.lst()
        except Exception as e: messagebox.showerror("Erro", str(e))
    def exc(self):
        s = self.tr.selection(); 
        if s and messagebox.askyesno("Confirmar", "Excluir?"): db.excluir_produto(self.tr.item(s[0], 'values')[0]); self.lst()

    # --- KITS & NOVAS RECEITAS ---
    def criar_novo_modelo_kit(self):
        nome = self.nk_nome.get()
        try: preco = float(self.nk_preco.get().replace(",", "."))
        except: return messagebox.showwarning("Erro", "Preço inválido")
        itens_raw = self.nk_itens.get("1.0", "end").strip().replace("\n", ",").split(",")
        itens_limpos = [i.strip() for i in itens_raw if i.strip()]
        
        if not nome or not itens_limpos: return messagebox.showwarning("Erro", "Preencha nome e itens")
        
        # Adiciona na memória (em um app real, salvaria no DB em tabela 'receitas')
        self.KITS_CONFIG[nome] = {"preco": preco, "itens": itens_limpos}
        self.sel_kit_menu.configure(values=list(self.KITS_CONFIG.keys()))
        self.sel_kit_menu.set(nome)
        self.analisar_kit(nome)
        messagebox.showinfo("Sucesso", f"Receita '{nome}' criada!")

    def analisar_kit(self, kit_nome):
        for w in self.scroll_ingredientes.winfo_children(): w.destroy()
        self.ingredientes_selecionados = {}
        config = self.KITS_CONFIG.get(kit_nome)
        if not config: return
        
        conn = db.conectar()
        for item_key in config['itens']:
            res = conn.execute("SELECT id, nome, custo_unitario, qtd_estoque FROM produtos WHERE nome LIKE ? AND qtd_estoque > 0 ORDER BY nome ASC", (f'%{item_key}%',)).fetchall()
            row = ctk.CTkFrame(self.scroll_ingredientes, fg_color="transparent"); row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{item_key}:", width=80, anchor="w", font=("Arial", 11, "bold")).pack(side="left")
            
            if not res:
                ctk.CTkLabel(row, text="❌ Sem estoque", text_color="red").pack(side="left")
                self.ingredientes_selecionados[item_key] = None
            else:
                l = [f"{r[1]} | R$ {r[2]:.2f}" for r in res]
                mapa = {f"{r[1]} | R$ {r[2]:.2f}": {'id': r[0], 'custo': r[2], 'est': r[3]} for r in res}
                cb = ctk.CTkOptionMenu(row, values=l, width=250, command=lambda v: self.calcular_totais_kit()); cb.pack(side="left", padx=5); cb.set(l[0])
                self.ingredientes_selecionados[item_key] = {'cb': cb, 'mapa': mapa}
        conn.close(); self.calcular_totais_kit()

    def calcular_totais_kit(self):
        nome = self.sel_kit_menu.get(); config = self.KITS_CONFIG.get(nome)
        if not config: return
        try: qtd = int(self.qtd_kit_entry.get()); qtd = 1 if qtd < 1 else qtd
        except: qtd = 1
        
        custo_u = 0.0; pode = True
        for k, v in self.ingredientes_selecionados.items():
            if not v: pode = False; break
            info = v['mapa'].get(v['cb'].get())
            if info: custo_u += info['custo']; 
            if info['est'] < qtd: pode = False; v['cb'].configure(fg_color=COR_VERMELHO_ERRO)
            else: v['cb'].configure(fg_color=["#3a7ebf", "#1f538d"])
            
        custo_tot = custo_u * qtd
        lucro = (config['preco'] * qtd) - custo_tot
        
        self.lbl_custo_total.configure(text=f"Custo Unit: R$ {custo_u:.2f} (Total: R$ {custo_tot:.2f})")
        cor_lucro = COR_VERDE_NEON if lucro > 0 else "red"
        self.lbl_lucro_previsto.configure(text=f"Lucro Previsto: R$ {lucro:.2f}", text_color=cor_lucro)
        
        if pode and len(self.ingredientes_selecionados) == len(config['itens']):
            self.btn_produzir.configure(state="normal", text=f"✅ PRODUZIR {qtd}x", fg_color=COR_VERDE_PRINCIPAL)
            self.custo_unitario_final = custo_u
        else: self.btn_produzir.configure(state="disabled", text="FALTA ESTOQUE", fg_color="gray")

    def salvar_producao_kit(self):
        nome = self.sel_kit_menu.get(); qtd = int(self.qtd_kit_entry.get()); ids = []
        for k, v in self.ingredientes_selecionados.items(): ids.append((v['mapa'][v['cb'].get()]['id'],))
        
        if messagebox.askyesno("Confirmar", f"Produzir {qtd}x {nome}?\nIsso baixará o estoque dos insumos."):
            try:
                # O preço de venda vem da configuração do kit
                preco_venda = self.KITS_CONFIG[nome]['preco']
                db.registrar_producao_kit(nome, qtd, preco_venda, self.custo_unitario_final, ids)
                messagebox.showinfo("Sucesso", "Kits produzidos e adicionados ao estoque!"); self.analisar_kit(nome); self.lst()
            except Exception as e: messagebox.showerror("Erro", str(e))
    
    def exportar_relatorio_estoque(self):
        try:
            rows = db.get_estoque_completo_dataframe()
            if not rows: return messagebox.showwarning("Vazio", "Estoque vazio.")
            filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile=f"Relatorio_{datetime.now().strftime('%d-%m')}")
            if not filename: return
            
            lista = []
            for r in rows:
                lista.append({"ID":r[0], "Produto":r[1], "Cat":r[2], "Estoque":r[3], "Min":r[4], "Custo":r[5], "Venda":r[6], "Obs":r[7]})
            
            df = pd.DataFrame(lista)
            df["Patrimonio"] = df["Estoque"] * df["Custo"]
            df["Potencial Venda"] = df["Estoque"] * df["Venda"]
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer: df.to_excel(writer, index=False)
            messagebox.showinfo("Sucesso", "Excel gerado!")
        except Exception as e: messagebox.showerror("Erro", str(e))

    def update_view(self): self.lst()

class PageMarketing(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text="Envio de Promoções e Campanhas", font=("Arial", 20, "bold"), text_color=COR_VERDE_NEON).pack(pady=10)
        
        f = ctk.CTkFrame(self, fg_color=COR_FUNDO_CARD); f.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(f, text="Assunto:").pack(anchor="w", padx=20, pady=(10,0))
        self.ass = ctk.CTkEntry(f, width=400); self.ass.pack(anchor="w", padx=20)
        
        ctk.CTkLabel(f, text="Mensagem:").pack(anchor="w", padx=20, pady=(10,0))
        self.msg = ctk.CTkTextbox(f, height=150); self.msg.pack(fill="x", padx=20)
        
        self.anexo = ctk.CTkLabel(f, text="Nenhum anexo", text_color="gray"); self.anexo.pack(pady=5)
        ctk.CTkButton(f, text="📎 Anexar PDF/Img", command=self.add_anexo).pack(pady=5)
        
        ctk.CTkLabel(f, text="Enviar para:").pack(pady=(10,0))
        self.dest = ctk.CTkOptionMenu(f, values=["Todos os Clientes", "Clientes Web", "Clientes Loja"]); self.dest.pack()
        
        ctk.CTkButton(f, text="🚀 DISPARAR EMAIL", fg_color=COR_VERDE_NEON, text_color="black", height=50, font=("Arial",14,"bold"), command=self.env).pack(pady=30, fill="x", padx=50)
        self.arq = None

    def add_anexo(self):
        f = filedialog.askopenfilename(); self.arq = f
        if f: self.anexo.configure(text=os.path.basename(f), text_color=COR_VERDE_NEON)

    def env(self):
        if not self.ass.get() or not self.msg.get("1.0","end").strip(): return messagebox.showwarning("Ops", "Preencha tudo!")
        # Aqui entraria a lógica real de SMTP. Por enquanto é simulação.
        messagebox.showinfo("Sucesso", f"Campanha '{self.ass.get()}' enviada!\n(Simulação)")

    def update_view(self): pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Go Green Tabacaria - Enterprise Admin")
        self.geometry("1300x800")
        self.configure(fg_color=COR_FUNDO_JANELA)
        
        # --- TELA CHEIA (MAXIMIZADA) ---
        # "zoomed" funciona nativamente no Windows para iniciar maximizado mantendo a barra de tarefas.
        # O bloco except garante que funcione em Linux/Mac (fullscreen) caso não suporte zoomed.
        try:
            self.state('zoomed')
        except:
            self.attributes('-fullscreen', True) 

        # Configuração do Grid Principal (Menu a Esquerda, Conteúdo a Direita)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar()
        self.main_area()
        
        # Inicia na Dashboard
        self.nav("Dashboard")

    def sidebar(self):
        self.menu = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="black")
        self.menu.grid(row=0, column=0, sticky="nsew")
        
        # Logo / Título
        ctk.CTkLabel(self.menu, text="GO GREEN\nAdmin", font=("Arial Black", 20), text_color=COR_VERDE_NEON).pack(pady=(40,30))
        
        # Botões do Menu
        btns = [
            ("Dashboard", "📊"),
            ("Marketing", "📢"),
            ("Pedidos Web", "🌐"),
            ("Clientes Site", "🌍"),
            ("Caixa Loja", "💰"),
            ("Fuzue Friends", "🍹"), 
            ("Histórico", "📜"),
            ("Clientes", "👥"),
            ("Estoque", "📦")
        ]
        
        for t, i in btns:
            ctk.CTkButton(self.menu, 
                          text=f"{i}  {t}", 
                          fg_color="transparent", 
                          anchor="w", 
                          font=("Arial", 14, "bold"), 
                          hover_color="#333", 
                          command=lambda x=t: self.nav(x)).pack(fill="x", padx=10, pady=8)

    def main_area(self):
        self.cont = ctk.CTkFrame(self, fg_color="transparent")
        self.cont.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.cont.grid_columnconfigure(0, weight=1)
        self.cont.grid_rowconfigure(0, weight=1)
        
        # Instancia todas as páginas
        self.pages = {
            "Dashboard": PageDash(self.cont),
            "Pedidos Web": PagePedidosWeb(self.cont),
            "Clientes Site": PageClientesWeb(self.cont),
            "Caixa Loja": PageVendas(self.cont),
            "Marketing": PageMarketing(self.cont),
            "Histórico": PageHistorico(self.cont),
            "Fuzue Friends": PageFuzue(self.cont),
            "Clientes": PageClientes(self.cont),
            "Estoque": PageEstoque(self.cont)
        }

    def nav(self, n):
        # Esconde todas e mostra a selecionada
        for name, p in self.pages.items():
            if name == n:
                p.grid(row=0, column=0, sticky="nsew")
                p.update_view() # Chama a função de atualização da página (recarregar dados)
            else:
                p.grid_forget()


if __name__ == "__main__":
    app = App()
    app.mainloop()