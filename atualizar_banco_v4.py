import sqlite3
import os

db_path = os.path.join("Database", "tabacaria.db")

def atualizar():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    print("Atualizando Banco de Dados para V4...")

    # 1. Atualizar Tabela de Usuários (Carteira e Foto)
    colunas_user = [
        ("saldo", "REAL DEFAULT 0.0"),
        ("foto_perfil", "TEXT DEFAULT ''"),
        ("newsletter", "INTEGER DEFAULT 0"), # 0 = Não, 1 = Sim
        ("chave_pix_carteira", "TEXT") # Para saque futuro se quiser
    ]
    for col, tipo in colunas_user:
        try:
            c.execute(f"ALTER TABLE usuarios_web ADD COLUMN {col} {tipo}")
            print(f"Coluna '{col}' adicionada em usuarios_web.")
        except: pass

    # 2. Tabela de Favoritos
    c.execute('''CREATE TABLE IF NOT EXISTS favoritos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        produto_id INTEGER,
        FOREIGN KEY(usuario_id) REFERENCES usuarios_web(id),
        FOREIGN KEY(produto_id) REFERENCES produtos(id)
    )''')
    print("Tabela 'favoritos' verificada.")

    # 3. Tabela de Transações da Carteira (Histórico)
    c.execute('''CREATE TABLE IF NOT EXISTS transacoes_carteira (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        tipo TEXT, -- 'deposito', 'compra', 'estorno'
        valor REAL,
        data_hora TEXT,
        descricao TEXT,
        FOREIGN KEY(usuario_id) REFERENCES usuarios_web(id)
    )''')
    print("Tabela 'transacoes_carteira' verificada.")

    conn.commit()
    conn.close()
    print("✅ Banco de Dados Atualizado com Sucesso!")

if __name__ == "__main__":
    atualizar()