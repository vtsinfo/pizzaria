import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'pizzaria.db')

def inspect_burger():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Searching for 'Burguer Colonial' ---")
    cursor.execute("SELECT id, nome, tipo, ingrediente_id FROM produtos WHERE nome LIKE '%Burguer%' OR nome LIKE '%Colonial%'")
    products = cursor.fetchall()
    
    if not products:
        print("No product found with 'Burguer' or 'Colonial' in the name.")
    
    for p in products:
        print(f"Product: ID={p[0]}, Name='{p[1]}', Type='{p[2]}', LinkedIngredId={p[3]}")
        
        # Check Recipe
        print(f"  > Recipe (Ficha Técnica):")
        cursor.execute("SELECT ingredients.nome, ficha_tecnica.quantidade FROM ficha_tecnica JOIN ingredientes ON ficha_tecnica.ingrediente_id = ingredients.id WHERE produto_id = ?", (p[0],))
        recipe = cursor.fetchall()
        
        if recipe:
            for r in recipe:
                print(f"    - {r[0]}: {r[1]}")
        else:
            print("    (No ingredients linked in recipe)")
            
    conn.close()

if __name__ == "__main__":
    inspect_burger()
