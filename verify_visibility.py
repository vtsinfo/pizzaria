import requests
import json
import os
from app import app, db, Produto, Ingrediente, FichaTecnica, Categoria

# 1. Setup Environment
BASE_URL = "http://127.0.0.1:5000"
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def setup_config(allow_negative):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    original_allow = config.get('allow_negative_stock', True)
    config['inventory_enabled'] = True
    config['allow_negative_stock'] = allow_negative
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
        
    return original_allow

def run_test():
    print("--- Starting Menu Visibility Test ---")
    
    prod_resale_id = None
    prod_manuf_id = None
    
    with app.app_context():
        # 1. Setup Test Data
        # Create Dummy Resale Item (e.g. Can of Soda)
        ing_resale = Ingrediente(nome="Test Soda Can", unidade="un", tipo="revenda", estoque_atual=5.0)
        db.session.add(ing_resale)
        db.session.flush()
        
        cat = Categoria.query.first()
        prod_resale = Produto(nome="Test Soda", categoria_id=cat.id, preco=5.0, tipo='revenda', ingrediente_id=ing_resale.id, visivel=True)
        db.session.add(prod_resale)
        db.session.flush()
        prod_resale_id = prod_resale.id
        
        # Create Dummy Manufactured Item (e.g. Pizza)
        ing_manuf = Ingrediente(nome="Test Cheese", unidade="kg", tipo="insumo", estoque_atual=2.0)
        db.session.add(ing_manuf)
        db.session.flush()
        
        prod_manuf = Produto(nome="Test Cheese Pizza", categoria_id=cat.id, preco=40.0, tipo='fabricado', visivel=True)
        db.session.add(prod_manuf)
        db.session.flush()
        prod_manuf_id = prod_manuf.id
        
        ficha = FichaTecnica(produto_id=prod_manuf.id, ingrediente_id=ing_manuf.id, quantidade=0.2)
        db.session.add(ficha)
        
        db.session.commit()
        
        # Store Ingredient IDs for later use
        ing_resale_id = ing_resale.id
        ing_manuf_id = ing_manuf.id
        
        print(f"Test data created. Resale ID: {prod_resale_id}, Manuf ID: {prod_manuf_id}")

    # Scenario 1: Stock OK
    original_config = setup_config(False)
    
    try:
        with app.test_client() as client:
            print("\nScenario 1: Stock OK")
            res = client.get('/api/cardapio')
            menu = res.get_json()
            # Helper to find item
            def find_item(name):
                for cat, items in menu.items():
                    for item in items:
                        if item['nome'] == name: return item
                return None
            
            p1 = find_item("Test Soda")
            p2 = find_item("Test Cheese Pizza")
            
            if p1 and not p1.get('esgotado') and p2 and not p2.get('esgotado'):
                print("✅ All items visible and available.")
            else:
                print(f"❌ Failed. Soda: {p1}, Pizza: {p2}")

            # Scenario 2: Zero Stock
            print("\nScenario 2: Zero Stock (Strict Mode)")
            with app.app_context():
                i1 = Ingrediente.query.get(ing_resale_id) # Fetch by ID
                if i1:
                    i1.estoque_atual = 0
                
                i2 = Ingrediente.query.get(ing_manuf_id) # Fetch by ID
                if i2:
                    i2.estoque_atual = 0
                db.session.commit()
                
            res = client.get('/api/cardapio')
            menu = res.get_json()
            
            p1 = find_item("Test Soda") # Should be HIDDEN (None)
            p2 = find_item("Test Cheese Pizza") # Should be VISIBLE but SOLD OUT
            
            if p1 is None:
                print("✅ Resale item HIDDEN as expected.")
            else:
                print(f"❌ Resale item still visible: {p1}")
                
            if p2 and p2.get('esgotado') == True:
                print("✅ Manufactured item marked SOLD OUT as expected.")
            else:
                print(f"❌ Manufactured item status incorrect: {p2}")

    finally:
        setup_config(original_config)
        # Cleanup could go here but using temporary DB mostly
        with app.app_context():
            # Delete our test data to keep DB clean
            try:
                # Delete recipe first
                if prod_manuf_id:
                    db.session.query(FichaTecnica).filter_by(produto_id=prod_manuf_id).delete()
                # Delete products
                if prod_resale_id: db.session.query(Produto).filter_by(id=prod_resale_id).delete()
                if prod_manuf_id: db.session.query(Produto).filter_by(id=prod_manuf_id).delete()
                # Delete ingredients
                if ing_resale_id: db.session.query(Ingrediente).filter_by(id=ing_resale_id).delete()
                if ing_manuf_id: db.session.query(Ingrediente).filter_by(id=ing_manuf_id).delete()
                db.session.commit()
                print("\nCleanup complete.")
            except Exception as e:
                print(f"Cleanup error: {e}")

if __name__ == "__main__":
    run_test()
