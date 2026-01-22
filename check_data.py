import sqlite3
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'pizzaria.db')
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

def check_db():
    if not os.path.exists(DB_PATH):
        print("❌ Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = {
        'Ingrediente': 'ingredientes',
        'Produto': 'produtos',
        'FichaTecnica': 'ficha_tecnica',
        'Fornecedor': 'fornecedores',
        'Compra': 'compras'
    }

    print("\n--- 📊 Contagem de Registros no Banco de Dados ---")
    for model, table in tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            status = "✅ OK" if count > 0 else "⚠️ VAZIO"
            print(f"{model}: {count} registos -> {status}")
        except sqlite3.OperationalError:
             print(f"{model}: Tabela '{table}' não encontrada ❌")
    
    conn.close()

def check_config():
    print("\n--- ⚙️ Configurações do Site (config.json) ---")
    if not os.path.exists(CONFIG_PATH):
        print("⚠️ Arquivo config.json não existe (Usando padrões do código).")
        return

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            keys_to_check = ['nome_fantasia', 'telefone', 'endereco_principal', 'ai_enabled']
            for k in keys_to_check:
                val = data.get(k, 'N/A')
                print(f"{k}: {val}")
    except Exception as e:
        print(f"❌ Erro ao ler config.json: {e}")

if __name__ == "__main__":
    check_db()
    check_config()
