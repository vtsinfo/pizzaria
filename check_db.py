import sys
import os

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import Banner, Categoria, Produto
from database import db

with app.app_context():
    print("=== Verificando Banco de Dados ===\n")
    
    print(f"Banners: {Banner.query.count()}")
    for b in Banner.query.all():
        print(f"  - {b.titulo} | {b.descricao} | {b.imagem_url} | Ativo: {b.ativo}")
    
    print(f"\nCategorias: {Categoria.query.count()}")
    for c in Categoria.query.all():
        print(f"  - {c.nome} | Ordem: {c.ordem} | Visível: {c.visivel}")
    
    print(f"\nProdutos: {Produto.query.count()}")
    for p in Produto.query.limit(5).all():
        print(f"  - {p.nome} | Preço: {p.preco} | Categoria: {p.categoria.nome if p.categoria else 'N/A'}")
    
    print("\n=== Fim da Verificação ===")
