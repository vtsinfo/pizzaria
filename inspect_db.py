import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'pizzaria.db')

def inspect():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Categories ---")
    for row in cursor.execute("SELECT * FROM categorias"):
        print(row)
        
    print("\n--- Products ---")
    for row in cursor.execute("SELECT id, nome, tipo, ingrediente_id FROM produtos"):
        print(row)
        
    print("\n--- Ingredients ---")
    for row in cursor.execute("SELECT id, nome, estoque_atual FROM ingredientes"):
        print(row)
        
    conn.close()

if __name__ == "__main__":
    inspect()
