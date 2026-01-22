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
        # Tabela Fornecedores
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_empresa VARCHAR(100) NOT NULL,
            cnpj VARCHAR(20),
            contato_nome VARCHAR(100),
            telefone VARCHAR(20),
            email VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ Tabela 'fornecedores' verificada/criada.")

        # Tabela Compras
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor_id INTEGER REFERENCES fornecedores(id),
            data_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
            nota_fiscal VARCHAR(50),
            total FLOAT DEFAULT 0.0,
            observacao TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ Tabela 'compras' verificada/criada.")

        # Tabela Itens Compra
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id INTEGER NOT NULL REFERENCES compras(id),
            ingrediente_id INTEGER NOT NULL REFERENCES ingredientes(id),
            quantidade FLOAT NOT NULL,
            preco_unitario FLOAT NOT NULL,
            subtotal FLOAT NOT NULL
        )
        """)
        print("✅ Tabela 'itens_compra' verificada/criada.")
            
        conn.commit()
        print("🚀 Migração de Compras concluída com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
