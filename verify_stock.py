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
    print("--- Starting Stock Verification Test ---")
    
    # Needs valid app context to query DB
    with app.app_context():
        # Find a suitable product (Fabricado)
        produto = Produto.query.filter_by(tipo='fabricado').first()
        if not produto:
            print("Creating dummy product for testing...")
            # Create dummy ingredient
            ingrediente = Ingrediente(nome="Test Mozzarella", unidade="kg", tipo="insumo", estoque_atual=10.0, estoque_minimo=1.0)
            db.session.add(ingrediente)
            db.session.flush()
            
            # Create dummy product
            cat = Categoria.query.first()
            if not cat:
                cat = Categoria(nome="Test Category", ordem=1)
                db.session.add(cat)
                db.session.flush()
                
            produto = Produto(nome="Test Pizza", categoria_id=cat.id, preco=50.0, tipo='fabricado', visivel=True)
            db.session.add(produto)
            db.session.flush()
            
            # Link recipe
            ficha = FichaTecnica(produto_id=produto.id, ingrediente_id=ingrediente.id, quantidade=0.2)
            db.session.add(ficha)
            db.session.commit()
            print(f"Created Product: {produto.nome} with Ingredient: {ingrediente.nome}")
            
            # Store IDs for later
            prod_id = produto.id
            prod_nome = produto.nome
            prod_preco = produto.preco
            ing_id = ingrediente.id
            ing_nome = ingrediente.nome
            
        else:
             receita = FichaTecnica.query.filter_by(produto_id=produto.id).first()
             if not receita:
                 # Add recipe to existing product if missing
                 ingrediente = Ingrediente.query.first()
                 if not ingrediente:
                     ingrediente = Ingrediente(nome="Test Ingredient", unidade="un", estoque_atual=10)
                     db.session.add(ingrediente)
                     db.session.flush()
                 
                 receita = FichaTecnica(produto_id=produto.id, ingrediente_id=ingrediente.id, quantidade=1)
                 db.session.add(receita)
                 db.session.commit()
                 
             ingrediente = receita.ingrediente
             
             # Store IDs
             prod_id = produto.id
             prod_nome = produto.nome
             prod_preco = produto.preco
             ing_id = ingrediente.id
             ing_nome = ingrediente.nome

        print(f"Testing with Product: {prod_nome}, Ingredient: {ing_nome}")
        
        # Save original stock
        # Re-fetch to be safe
        ing = Ingrediente.query.get(ing_id)
        original_stock = ing.estoque_atual
        
        # Set stock to 0
        ing.estoque_atual = 0.0
        db.session.commit()
        print(f"Set stock of {ing_nome} to 0.")

    # Temporarily enforce strict stock
    original_config_val = setup_config(False)
    
    try:
        # payload
        payload = {
            "customer": "Test User",
            "phone": "11999999999",
            "items": [
                {"name": prod_nome, "price": str(prod_preco)}
            ],
            "total": str(prod_preco)
        }
        
        print("Attempting to place order with 0 stock...")
        # We need to run the server or simulate request. 
        # Since we are in the same env, let's use app.test_client()
        with app.test_client() as client:
            response = client.post('/api/pedido/novo', json=payload)
            
            print(f"Response Status: {response.status_code}")
            # print(f"Response Body: {response.get_json()}")
            
            data = response.get_json()
            if response.status_code == 400 and "insuficiente" in (data.get("message", "") or "").lower():
                print("✅ TEST PASSED: Order rejected as expected.")
            else:
                print(f"❌ TEST FAILED: Order was not rejected correctly. Got {response.status_code} - {data}")
                
            # Test Scenario 2: Allow Negative Stock
            print("\nTesting with 'allow_negative_stock = True'...")
            setup_config(True)
            response2 = client.post('/api/pedido/novo', json=payload)
             
            if response2.status_code == 200:
                 print("✅ TEST PASSED: Order accepted when negative stock allowed.")
            else:
                 print(f"❌ TEST FAILED: Order rejected unexpectedly. Status: {response2.status_code}")

    finally:
        # Cleanup
        print("\nRestoring state...")
        setup_config(original_config_val)
        with app.app_context():
            ing = Ingrediente.query.get(ing_id)
            if ing:
                ing.estoque_atual = original_stock
                db.session.commit()
            print("Stock restored.")

if __name__ == "__main__":
    run_test()
