from app import app
from database import db
from models import Categoria

def update_categories():
    with app.app_context():
        print("--- Atualizando Capas das Categorias ---")
        
        # Mapeamento: Nome da Categoria -> Caminho da Imagem Existente
        # Baseado nos arquivos que vi no diretório:
        # pizza_calabresa_... -> static/uploads/...
        # burger_x_salada_...
        # esfiha_carne_...
        # fogazza_calabresa_...
        # marmitex_churrasco_...
        
        # Vou usar nomes de arquivos "globais" esperando que o update_images.py já tenha movido/renomeado
        # OU buscar no banco um produto dessa categoria que tenha foto e usar.
        
        categorias = Categoria.query.all()
        
        for cat in categorias:
            # Tenta pegar a foto do primeiro produto da categoria que tenha foto
            # Isso garante que a capa seja um produto real daquela categoria
            
            # Prioridade: Produto Fabricado
            produto_capa = None
            
            if cat.nome == "Pizzas Salgadas":
                # Tenta pegar Calabresa
                produto_capa = next((p for p in cat.produtos if "Calabresa" in p.nome and p.foto_url), None)
            elif cat.nome == "Pizzas Doces":
                produto_capa = next((p for p in cat.produtos if "Chocolate" in p.nome and p.foto_url), None)
            elif cat.nome == "Hambúrgueres":
                produto_capa = next((p for p in cat.produtos if "X-Salada" in p.nome and p.foto_url), None)
            elif cat.nome == "Esfihas":
                produto_capa = next((p for p in cat.produtos if "Carne" in p.nome and p.foto_url), None)
            elif cat.nome == "Fogazzas":
                produto_capa = next((p for p in cat.produtos if "Calabresa" in p.nome and p.foto_url), None)
            elif cat.nome == "Marmitex":
                produto_capa = next((p for p in cat.produtos if "Churrasco" in p.nome and p.foto_url), None)
            
            # Fallback: Qualquer produto com foto
            if not produto_capa:
                # busca qualquer um com foto_url
                for p in cat.produtos:
                    if p.foto_url:
                        produto_capa = p
                        break
            
            if produto_capa:
                cat.foto_url = produto_capa.foto_url
                print(f" [OK] Categoria '{cat.nome}' atualizada com foto de '{produto_capa.nome}'")
            else:
                print(f" [!] Categoria '{cat.nome}' sem produto com foto adequada.")
                # Se for bebidas, talvez não tenha foto ainda, mantem a anterior ou deixa null
        
        db.session.commit()
        print("--- Concluído ---")

if __name__ == "__main__":
    update_categories()
