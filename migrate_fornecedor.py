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
        cursor.execute("PRAGMA table_info(ingredientes)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'fornecedor' not in columns:
            print("🛠️  Adicionando coluna 'fornecedor' na tabela 'ingredientes'...")
            cursor.execute("ALTER TABLE ingredientes ADD COLUMN fornecedor VARCHAR(100)")
        else:
            print("ℹ️  Coluna 'fornecedor' já existe.")
            
        conn.commit()
        print("✅ Migração de fornecedor concluída com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
