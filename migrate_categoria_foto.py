import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'pizzaria.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado em: {DB_PATH}")
        return

    print(f"📂 Abrindo banco de dados: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verifica colunas existentes na tabela categorias
        cursor.execute("PRAGMA table_info(categorias)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'foto_url' not in columns:
            print("🛠️  Adicionando coluna 'foto_url' na tabela 'categorias'...")
            cursor.execute("ALTER TABLE categorias ADD COLUMN foto_url VARCHAR(255)")
        else:
            print("ℹ️  Coluna 'foto_url' já existe.")
            
        conn.commit()
        print("✅ Migração de categorias concluída com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
