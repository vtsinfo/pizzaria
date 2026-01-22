import os
import shutil
import glob
from app import app
from database import db
from models import Produto

ARTIFACT_DIR = r"C:\Users\Reset\.gemini\antigravity\brain\d8a3ca9b-ce61-45b1-900a-3d58d5fda02b"
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Mapeamento Prefix do Arquivo -> Nome do Produto (ou parte dele para busca)
image_map = {
    "pizza_mussarela": "Mussarela",
    "pizza_calabresa": "Calabresa",
    "pizza_portuguesa": "Portuguesa",
    "pizza_frango_catupiry": "Frango c/ Catupiry",
    "pizza_quatro_queijos": "Quatro Queijos",
    "pizza_bacon": "Bacon",
    "esfiha_carne": "Carne",     # Categoria Esfihas
    "esfiha_queijo": "Queijo",
    "esfiha_calabresa": "Calabresa", # Cuidado com ambiguidade (usar categoria)
    "esfiha_frango_catupiry": "Frango c/ Catupiry",
    "esfiha_bacon": "Bacon",
    "fogazza_calabresa": "Calabresa", # Fogazza
    "fogazza_mussarela": "Mussarela", # Fogazza
    "pizza_chocolate": "Chocolate",
    "pizza_prestigio": "Prestígio",
    "burger_x_salada": "X-Salada",
    "marmitex_churrasco": "Churrasco Misto",
    "marmitex_fraldinha": "Fraldinha Assada",
    "marmitex_frango_assado": "Frango Assado",
    "marmitex_parmegiana": "Frango à Parmegiana",
    "marmitex_picanha": "Picanha Assada",
    "marmitex_merluza": "Filé de Merluza"
}

# Categorias para desambiguação
category_map = {
    "esfiha_": "Esfihas",
    "fogazza_": "Fogazzas",
    "pizza_chocolate": "Pizzas Doces",
    "pizza_prestigio": "Pizzas Doces",
    "burger_": "Hambúrgueres",
    "pizza_": "Pizzas Salgadas",
    "marmitex_": "Marmitex"
}

def update_images():
    with app.app_context():
        print("--- Atualizando Imagens dos Produtos ---")
        
        for prefix, produto_nome in image_map.items():
            # Encontrar o arquivo mais recente com esse prefixo no diretório de artefatos
            pattern = os.path.join(ARTIFACT_DIR, f"{prefix}_*.png")
            files = glob.glob(pattern)
            
            if not files:
                print(f" [!] Nenhuma imagem encontrada para prefixo: {prefix}")
                continue
                
            # Pega o mais recente
            latest_file = max(files, key=os.path.getctime)
            filename = os.path.basename(latest_file)
            
            # Copia para uploads
            dest_path = os.path.join(UPLOAD_DIR, filename)
            shutil.copy2(latest_file, dest_path)
            
            # Caminho relativo para o DB
            db_path = f"/static/uploads/{filename}"
            
            # Determinar categoria para busca (para evitar que Esfiha Calabresa pegue Pizza Calabresa)
            cat_filter = None
            if prefix.startswith("esfiha_"): cat_filter = "Esfihas"
            elif prefix.startswith("fogazza_"): cat_filter = "Fogazzas"
            elif prefix.startswith("burger_"): cat_filter = "Hambúrgueres"
            elif prefix in ["pizza_chocolate", "pizza_prestigio"]: cat_filter = "Pizzas Doces"
            elif prefix.startswith("pizza_"): cat_filter = "Pizzas Salgadas"

            # Buscar produto no BD
            query = Produto.query.filter(Produto.nome == produto_nome)
            if cat_filter:
                query = query.join(Produto.categoria).filter(Produto.categoria.has(nome=cat_filter))
            
            produto = query.first()
            
            if produto:
                produto.foto_url = db_path
                print(f" [OK] Atualizado: {produto.nome} ({cat_filter}) -> {filename}")
            else:
                print(f" [X] Produto não encontrado no BD: {produto_nome} (Filtro: {cat_filter})")
        
        db.session.commit()
        print("--- Concluído ---")

if __name__ == "__main__":
    update_images()
