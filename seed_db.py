"""
Script para popular o banco de dados com dados iniciais
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import Banner, Categoria, Produto
from database import db

with app.app_context():
    print("=== Populando Banco de Dados ===\n")
    
    # Criar Banner padrão
    if Banner.query.count() == 0:
        print("Criando banner padrão...")
        banner = Banner(
            titulo="A Melhor Pizza da Região",
            descricao="A melhor massa, ingredientes selecionados e tradição desde 1998.",
            imagem_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=1920&q=80",
            ordem=0,
            ativo=True
        )
        db.session.add(banner)
        print("✓ Banner criado")
    
    # Criar categorias de exemplo
    if Categoria.query.count() == 0:
        print("\nCriando categorias...")
        categorias = [
            Categoria(nome="Pizzas Salgadas", ordem=1, visivel=True, exibir_preco=True),
            Categoria(nome="Pizzas Doces", ordem=2, visivel=True, exibir_preco=True),
            Categoria(nome="Hambúrgueres", ordem=3, visivel=True, exibir_preco=True),
            Categoria(nome="Bebidas", ordem=4, visivel=True, exibir_preco=True),
        ]
        for cat in categorias:
            db.session.add(cat)
            print(f"✓ Categoria '{cat.nome}' criada")
    
    db.session.commit()
    
    # Criar produtos de exemplo
    if Produto.query.count() == 0:
        print("\nCriando produtos de exemplo...")
        cat_pizzas = Categoria.query.filter_by(nome="Pizzas Salgadas").first()
        cat_bebidas = Categoria.query.filter_by(nome="Bebidas").first()
        
        if cat_pizzas:
            produtos = [
                Produto(
                    categoria_id=cat_pizzas.id,
                    nome="Mussarela",
                    descricao="Molho de tomate, mussarela e orégano",
                    preco=48.99,
                    foto_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80",
                    visivel=True,
                    esgotado=False
                ),
                Produto(
                    categoria_id=cat_pizzas.id,
                    nome="Calabresa",
                    descricao="Molho de tomate, mussarela, calabresa e cebola",
                    preco=52.99,
                    foto_url="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=800&q=80",
                    visivel=True,
                    esgotado=False
                ),
            ]
            for p in produtos:
                db.session.add(p)
                print(f"✓ Produto '{p.nome}' criado")
        
        if cat_bebidas:
            bebida = Produto(
                categoria_id=cat_bebidas.id,
                nome="Coca-Cola 2L",
                descricao="Refrigerante Coca-Cola 2 litros",
                preco=12.00,
                foto_url="",
                visivel=True,
                esgotado=False
            )
            db.session.add(bebida)
            print(f"✓ Produto '{bebida.nome}' criado")
    
    db.session.commit()
    
    print("\n=== Banco de Dados Populado com Sucesso! ===")
    print(f"Banners: {Banner.query.count()}")
    print(f"Categorias: {Categoria.query.count()}")
    print(f"Produtos: {Produto.query.count()}")
