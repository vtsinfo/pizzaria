import sqlite3
import os

db_path = os.path.join('instance', 'pizzaria.db')
if not os.path.exists(db_path):
    print("DB nao encontrado")
else:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("SELECT id, nome, categoria_id, foto_url FROM produtos")
        rows = c.fetchall()
        print("--- PRODUTOS NO BANCO ---")
        for r in rows:
            print(r)
            
        c.execute("SELECT id, nome FROM categorias")
        rows_cat = c.fetchall()
        print("\n--- CATEGORIAS ---")
        for r in rows_cat:
            print(r)
            
    except Exception as e:
        print(e)
    finally:
        conn.close()
