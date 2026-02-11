import sqlite3
import os

db_path = os.path.join("Database", "tabacaria.db")

def atualizar():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        # Adiciona coluna telefone na tabela de usuários do site
        c.execute("ALTER TABLE usuarios_web ADD COLUMN telefone TEXT")
        print("Coluna 'telefone' adicionada em usuarios_web.")
    except:
        print("Coluna 'telefone' já existe.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    atualizar()