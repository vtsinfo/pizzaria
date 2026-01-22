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
        cursor.execute("PRAGMA table_info(produtos)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'tipo' not in columns:
            print("🛠️  Adicionando coluna 'tipo'...")
            cursor.execute("ALTER TABLE produtos ADD COLUMN tipo VARCHAR(20) DEFAULT 'fabricado'")
        else:
            print("ℹ️  Coluna 'tipo' já existe.")

        if 'ingrediente_id' not in columns:
            print("🛠️  Adicionando coluna 'ingrediente_id'...")
            cursor.execute("ALTER TABLE produtos ADD COLUMN ingrediente_id INTEGER REFERENCES ingredientes(id)")
        else:
            print("ℹ️  Coluna 'ingrediente_id' já existe.")
            
        conn.commit()
        print("✅ Migração de produtos concluída com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
