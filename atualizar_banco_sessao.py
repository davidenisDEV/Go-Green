import sqlite3
import os

# Garante que encontra o banco na pasta Database, independente de onde o script é rodado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "Database", "tabacaria.db")

def atualizar_sessao():
    print(f"Conectando ao banco em: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ ERRO: O arquivo do banco de dados não foi encontrado neste caminho.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Tenta adicionar a coluna para controle de sessão única
        c.execute("ALTER TABLE usuarios_web ADD COLUMN token_jti TEXT")
        print("✅ Coluna 'token_jti' adicionada com sucesso!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ A coluna 'token_jti' já existia. Nenhuma alteração necessária.")
        else:
            print(f"❌ Erro ao alterar tabela: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    atualizar_sessao()