from app import app, db
from models import Categoria
import json

def test_api():
    with app.app_context():
        # Setup dummy request context isn't easy for full route, but we can query DB
        # Check if Categoria exists
        cats = Categoria.query.all()
        print(f"Categories found: {[c.nome for c in cats]}")
        
        # Simulate the logic of api_config_cardapio
        config = {}
        for cat in cats:
            config[cat.nome] = {
                "visible": cat.visivel,
                "show_price": cat.exibir_preco
            }
        print("Config Logic Output:")
        print(json.dumps(config, indent=2))

if __name__ == "__main__":
    test_api()
