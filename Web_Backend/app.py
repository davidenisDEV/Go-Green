from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import uuid
from datetime import datetime, timedelta
from PIL import Image # Requer: pip install Pillow

app = Flask(__name__)
CORS(app) 

# --- CONFIGURAÇÕES ---
# Segurança
app.config["JWT_SECRET_KEY"] = "super-secreta-chave-gogreen-2026"
jwt = JWTManager(app)

# Uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # 5MB Limite

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Banco de Dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Database", "tabacaria.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- VERIFICAÇÃO DE SESSÃO ÚNICA (SINGLE SESSION) ---
# --- VERIFICAÇÃO DE SESSÃO ÚNICA (SINGLE SESSION) ---
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    # BLINDAGEM: Se o token for antigo e não tiver 'jti' ou 'sub', bloqueia imediatamente
    if 'jti' not in jwt_payload or 'sub' not in jwt_payload:
        return True 

    jti = jwt_payload["jti"]
    user_id = jwt_payload["sub"]
    
    conn = get_db()
    try:
        user = conn.execute("SELECT token_jti FROM usuarios_web WHERE id = ?", (user_id,)).fetchone()
        conn.close()

        if user is None:
            return True # Usuário não existe mais
            
        # Se o token salvo no banco for diferente do token enviado: BLOQUEIA
        if user['token_jti'] != jti:
            return True
            
        return False # Token Válido
    except Exception as e:
        print(f"⚠️ Erro verificação token: {str(e)}")
        return True # Por segurança, bloqueia em caso de erro estranho

# --- ROTAS DE IMAGEM ---
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_image():
    if 'file' not in request.files: return jsonify({"msg": "Sem arquivo"}), 400
    file = request.files['file']
    tipo = request.form.get('tipo') # 'perfil' ou 'produto'
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            img = Image.open(file)
            if tipo == 'perfil': img = img.resize((500, 500)) # Quadrada para perfil
            elif tipo == 'produto': img.thumbnail((800, 1000)) # Otimizada para produto
            
            img.save(filepath, optimize=True, quality=85)
            full_url = f"http://localhost:5000/static/uploads/{filename}"
            return jsonify({"url": full_url}), 200
        except Exception as e:
            return jsonify({"msg": f"Erro imagem: {str(e)}"}), 500
    return jsonify({"msg": "Formato inválido"}), 400

# --- ROTAS DE PRODUTOS ---
@app.route('/api/produtos', methods=['GET'])
def get_produtos():
    conn = get_db()
    # REMOVIDO "WHERE qtd_estoque > 0". 
    # O frontend agora decide se mostra "Esgotado" ou não.
    prods = conn.execute("SELECT id, nome, preco_venda, categoria, imagem_url, destaque, qtd_estoque, observacoes FROM produtos ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in prods])

# --- ROTA DE PEDIDOS ---
@app.route('/api/pedidos/novo', methods=['POST'])
@jwt_required() # Agora exige login para pedir
def novo_pedido():
    data = request.json
    cliente = data.get('cliente') 
    carrinho = data.get('carrinho')
    pagamento = data.get('pagamento')
    total = data.get('total')
    user_id = get_jwt_identity() # Pega ID do token

    if not carrinho: return jsonify({"msg": "Carrinho vazio"}), 400

    conn = get_db()
    try:
        # Usa dados do token se o cliente não preencher, mas o frontend deve mandar
        cur = conn.execute('''INSERT INTO pedidos_web 
            (cliente_nome, cliente_contato, data_hora, total, status, metodo_pagamento) 
            VALUES (?, ?, ?, ?, 'pendente', ?)''',
            (cliente.get('nome'), cliente.get('contato'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), total, pagamento))
        
        pedido_id = cur.lastrowid

        for item in carrinho:
            conn.execute('''INSERT INTO itens_pedido_web 
                (pedido_id, produto_id, quantidade, preco_unitario) 
                VALUES (?, ?, ?, ?)''', 
                (pedido_id, item['id'], item['qtd'], item['preco_venda']))
        
        conn.commit()
        return jsonify({"msg": "Pedido recebido!", "pedido_id": pedido_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"msg": f"Erro: {str(e)}"}), 500
    finally:
        conn.close()

# --- ROTAS DE AUTENTICAÇÃO E PERFIL ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    telefone = data.get('telefone')

    if not nome or not email or not senha or not telefone:
        return jsonify({"msg": "Preencha todos os dados."}), 400

    senha_hash = generate_password_hash(senha)

    try:
        conn = get_db()
        conn.execute("INSERT INTO usuarios_web (nome, email, password_hash, telefone, data_criacao) VALUES (?, ?, ?, ?, ?)",
                     (nome, email, senha_hash, telefone, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
        conn.close()
        return jsonify({"msg": "Conta criada com sucesso!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"msg": "Email já cadastrado"}), 409

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    remember = data.get('remember', False)

    conn = get_db()
    user = conn.execute("SELECT * FROM usuarios_web WHERE email = ?", (email,)).fetchone()
    
    if user and check_password_hash(user['password_hash'], senha):
        tempo_expiracao = timedelta(days=30) if remember else timedelta(days=1)
        novo_jti = str(uuid.uuid4())
        
        token = create_access_token(
            identity=user['id'], 
            additional_claims={"jti": novo_jti, "role": user['role']}, # Adicionado ROLE no token
            expires_delta=tempo_expiracao
        )
        
        conn.execute("UPDATE usuarios_web SET token_jti = ? WHERE id = ?", (novo_jti, user['id']))
        conn.commit()
        conn.close()

        # Retorna a role para o frontend controlar o acesso
        return jsonify({
            "token": token, 
            "user": {
                "nome": user['nome'], 
                "email": user['email'], 
                "role": user['role'] # IMPORTANTE: O Frontend usa isso para liberar a página Admin
            }
        }), 200
    
    conn.close()
    return jsonify({"msg": "Email ou senha incorretos"}), 401

@app.route('/api/minha-conta', methods=['GET'])
@jwt_required()
def get_dados_conta():
    user_id = get_jwt_identity()
    conn = get_db()
    
    # Busca dados completos + transações
    user = conn.execute("SELECT id, nome, email, telefone, data_criacao, saldo, foto_perfil, newsletter FROM usuarios_web WHERE id = ?", (user_id,)).fetchone()
    transacoes = conn.execute("SELECT * FROM transacoes_carteira WHERE usuario_id = ? ORDER BY id DESC LIMIT 5", (user_id,)).fetchall()
    
    conn.close()
    
    if not user: return jsonify({"msg": "Erro"}), 404
    
    dados = dict(user)
    dados['transacoes'] = [dict(t) for t in transacoes]
    return jsonify(dados), 200

@app.route('/api/minha-conta/update', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.json
    conn = get_db()
    if 'foto_perfil' in data:
        conn.execute("UPDATE usuarios_web SET foto_perfil = ? WHERE id = ?", (data['foto_perfil'], user_id))
    if 'newsletter' in data:
        conn.execute("UPDATE usuarios_web SET newsletter = ? WHERE id = ?", (data['newsletter'], user_id))
    conn.commit()
    conn.close()
    return jsonify({"msg": "Atualizado"}), 200

# --- ROTAS ADMINISTRATIVAS (NOVO) ---

# 1. EDITAR PRODUTO (PUT) - BLINDADO
@app.route('/api/produtos/<int:id_prod>', methods=['PUT'])
@jwt_required()
def update_produto(id_prod):
    # Log para debug no terminal
    print(f"Tentativa de update produto {id_prod}")
    
    # Verifica se o payload é JSON
    if not request.is_json:
        return jsonify({"msg": "Formato inválido, esperado JSON"}), 422

    data = request.json
    
    # Validação simples
    if 'nome' not in data or 'preco_venda' not in data:
        return jsonify({"msg": "Dados incompletos"}), 400

    conn = get_db()
    try:
        # Usa .get() para evitar erro de chave se o campo não vier
        conn.execute("""
            UPDATE produtos 
            SET nome=?, preco_venda=?, qtd_estoque=?, categoria=?, observacoes=?, destaque=?, imagem_url=?
            WHERE id=?
        """, (
            data.get('nome'), 
            data.get('preco_venda'), 
            data.get('qtd_estoque'), 
            data.get('categoria'), 
            data.get('observacoes', ''), 
            data.get('destaque', 0),
            data.get('imagem_url', ''), # Se não vier url, salva vazio (não quebra)
            id_prod
        ))
        conn.commit()
        return jsonify({"msg": "Produto atualizado com sucesso"}), 200
    except Exception as e:
        print(f"Erro no Update: {str(e)}") # Mostra erro no terminal
        return jsonify({"msg": f"Erro ao atualizar: {str(e)}"}), 500
    finally:
        conn.close()

# 2. EXCLUIR PRODUTO (DELETE)
@app.route('/api/produtos/<int:id_prod>', methods=['DELETE'])
@jwt_required()
def delete_produto(id_prod):
    conn = get_db()
    try:
        conn.execute("DELETE FROM produtos WHERE id = ?", (id_prod,))
        conn.commit()
        return jsonify({"msg": "Produto excluído"}), 200
    except Exception as e:
        return jsonify({"msg": f"Erro ao excluir: {str(e)}"}), 500
    finally:
        conn.close()

# 3. CRIAR NOVO PRODUTO (POST) - Caso queira criar pelo site também
@app.route('/api/produtos', methods=['POST'])
@jwt_required()
def create_produto():
    data = request.json
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO produtos (nome, preco_venda, qtd_estoque, categoria, observacoes, destaque, imagem_url, custo_unitario)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            data['nome'], 
            data['preco_venda'], 
            data['qtd_estoque'], 
            data['categoria'], 
            data['observacoes'], 
            data.get('destaque', 0),
            data.get('imagem_url', '')
        ))
        conn.commit()
        return jsonify({"msg": "Produto criado com sucesso"}), 201
    except Exception as e:
        return jsonify({"msg": f"Erro ao criar: {str(e)}"}), 500
    finally:
        conn.close()

# --- CARTEIRA E FAVORITOS ---
@app.route('/api/carteira/depositar', methods=['POST'])
@jwt_required()
def depositar():
    user_id = get_jwt_identity()
    valor = float(request.json.get('valor', 0))
    if valor <= 0: return jsonify({"msg": "Valor inválido"}), 400
    conn = get_db()
    conn.execute("UPDATE usuarios_web SET saldo = saldo + ? WHERE id = ?", (valor, user_id))
    conn.execute("INSERT INTO transacoes_carteira (usuario_id, tipo, valor, data_hora, descricao) VALUES (?, ?, ?, ?, ?)",
                 (user_id, 'deposito', valor, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Depósito via Pix'))
    conn.commit()
    conn.close()
    return jsonify({"msg": "Sucesso"}), 200

@app.route('/api/favoritos', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def handle_favoritos():
    user_id = get_jwt_identity()
    conn = get_db()
    if request.method == 'GET':
        res = conn.execute('SELECT p.* FROM favoritos f JOIN produtos p ON f.produto_id = p.id WHERE f.usuario_id = ?', (user_id,)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in res])
    
    prod_id = request.json.get('produto_id')
    if request.method == 'POST':
        try:
            conn.execute("INSERT INTO favoritos (usuario_id, produto_id) VALUES (?, ?)", (user_id, prod_id))
            conn.commit()
        except: pass
    elif request.method == 'DELETE':
        conn.execute("DELETE FROM favoritos WHERE usuario_id = ? AND produto_id = ?", (user_id, prod_id))
        conn.commit()
    
    conn.close()
    return jsonify({"msg": "Ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)