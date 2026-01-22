"""
Script para popular o banco de dados com dados iniciais
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import Banner, Categoria, Produto, Ingrediente, FichaTecnica, Cupom, Fidelidade, Depoimento, Reserva, Pedido, ItemPedido, User
from database import db
from datetime import datetime, timedelta
import json

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
            Categoria(nome="Marmitex", ordem=4, visivel=True, exibir_preco=True),
            Categoria(nome="Bebidas", ordem=5, visivel=True, exibir_preco=True),
        ]
        for cat in categorias:
            db.session.add(cat)
            print(f"✓ Categoria '{cat.nome}' criada")
    
    db.session.commit()
    
    # Criar produtos de exemplo
    if Produto.query.count() == 0:
        print("\nCriando produtos de exemplo...")
        cat_pizzas = Categoria.query.filter_by(nome="Pizzas Salgadas").first()
        cat_doces = Categoria.query.filter_by(nome="Pizzas Doces").first()
        cat_burgers = Categoria.query.filter_by(nome="Hambúrgueres").first()
        cat_marmitex = Categoria.query.filter_by(nome="Marmitex").first()
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
                    esgotado=False,
                    tipo="fabricado" # Explicitamente fabricado
                ),
                Produto(
                    categoria_id=cat_pizzas.id,
                    nome="Calabresa",
                    descricao="Molho de tomate, mussarela, calabresa e cebola",
                    preco=52.99,
                    foto_url="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=800&q=80",
                    visivel=True,
                    esgotado=False,
                    tipo="fabricado" # Explicitamente fabricado
                ),
                Produto(
                    categoria_id=cat_pizzas.id,
                    nome="Portuguesa",
                    descricao="Presunto, ovos, ervilha, cebola e mussarela",
                    preco=54.99,
                    foto_url="",
                    visivel=True,
                    esgotado=False,
                    tipo="fabricado" # Explicitamente fabricado
                ),
                Produto(
                    categoria_id=cat_pizzas.id,
                    nome="Frango com Catupiry",
                    descricao="Frango desfiado e catupiry original",
                    preco=55.90,
                    foto_url="",
                    visivel=True,
                    esgotado=False,
                    tipo="fabricado" # Explicitamente fabricado
                ),
            ]
            for p in produtos:
                db.session.add(p)
                print(f"✓ Produto '{p.nome}' criado")

        if cat_doces:
            produtos_doces = [
                Produto(categoria_id=cat_doces.id, nome="Brigadeiro", descricao="Chocolate ao leite e granulado", preco=45.90, visivel=True, tipo="fabricado"),
                Produto(categoria_id=cat_doces.id, nome="Romeu e Julieta", descricao="Goiabada e mussarela", preco=45.90, visivel=True, tipo="fabricado"),
                Produto(categoria_id=cat_doces.id, nome="Prestígio", descricao="Chocolate e coco ralado", preco=46.90, visivel=True, tipo="fabricado"),
            ]
            for p in produtos_doces:
                db.session.add(p)
            print(f"✓ {len(produtos_doces)} pizzas doces criadas")

        if cat_burgers:
            burgers = [
                Produto(categoria_id=cat_burgers.id, nome="X-Salada", descricao="Hambúrguer, queijo, alface, tomate e maionese", preco=22.00, visivel=True, tipo="fabricado"),
                Produto(categoria_id=cat_burgers.id, nome="X-Bacon", descricao="Hambúrguer, queijo, bacon crocante e maionese", preco=26.00, visivel=True, tipo="fabricado"),
                Produto(categoria_id=cat_burgers.id, nome="Colonial Burger", descricao="Duplo burger, cheddar, bacon e cebola caramelizada", preco=32.00, visivel=True, tipo="fabricado"),
            ]
            for p in burgers:
                db.session.add(p)
            print(f"✓ {len(burgers)} hambúrgueres criados")

        if cat_marmitex:
            marmitas = [
                Produto(categoria_id=cat_marmitex.id, nome="Bife Acebolado", descricao="Arroz, feijão, bife acebolado, fritas e salada", preco=28.99, visivel=True, tipo="fabricado"),
                Produto(categoria_id=cat_marmitex.id, nome="Filé de Frango", descricao="Arroz, feijão, filé de frango grelhado e legumes", preco=24.99, visivel=True, tipo="fabricado"),
                Produto(categoria_id=cat_marmitex.id, nome="Feijoada (Média)", descricao="Completa: arroz, couve, farofa e torresmo", preco=35.00, visivel=True, tipo="fabricado"),
            ]
            for p in marmitas:
                db.session.add(p)
            print(f"✓ {len(marmitas)} marmitex criados")
        
        if cat_bebidas:
            bebidas = [
                Produto(categoria_id=cat_bebidas.id, nome="Coca-Cola 2L", descricao="Garrafa", preco=14.00, visivel=True, tipo="revenda"),
                Produto(categoria_id=cat_bebidas.id, nome="Guaraná Antarctica 2L", descricao="Garrafa", preco=12.00, visivel=True, tipo="revenda"),
                Produto(categoria_id=cat_bebidas.id, nome="Suco Del Valle Uva", descricao="1 Litro", preco=10.00, visivel=True, tipo="revenda"),
                Produto(categoria_id=cat_bebidas.id, nome="Heineken Long Neck", descricao="330ml", preco=9.00, visivel=True, tipo="revenda"),
            ]
            for p in bebidas:
                db.session.add(p)
            print(f"✓ {len(bebidas)} bebidas criadas")

    # Criar Ingredientes (Estoque)
    if Ingrediente.query.count() == 0:
        print("\nCriando ingredientes...")
        ingredientes = [
            Ingrediente(nome="Farinha de Trigo", unidade="kg", tipo="insumo", estoque_atual=50.0, estoque_minimo=10.0, custo_unitario=3.50),
            Ingrediente(nome="Molho de Tomate", unidade="l", tipo="insumo", estoque_atual=20.0, estoque_minimo=5.0, custo_unitario=8.00),
            Ingrediente(nome="Queijo Mussarela", unidade="kg", tipo="insumo", estoque_atual=30.0, estoque_minimo=5.0, custo_unitario=28.00),
            Ingrediente(nome="Calabresa", unidade="kg", tipo="insumo", estoque_atual=15.0, estoque_minimo=3.0, custo_unitario=22.00),
            Ingrediente(nome="Coca-Cola 2L", unidade="un", tipo="revenda", estoque_atual=48.0, estoque_minimo=12.0, custo_unitario=7.50),
            Ingrediente(nome="Presunto", unidade="kg", tipo="insumo", estoque_atual=10.0, estoque_minimo=2.0, custo_unitario=18.00),
            Ingrediente(nome="Ovos", unidade="dz", tipo="insumo", estoque_atual=20.0, estoque_minimo=5.0, custo_unitario=8.00),
            Ingrediente(nome="Chocolate ao Leite", unidade="kg", tipo="insumo", estoque_atual=5.0, estoque_minimo=1.0, custo_unitario=35.00),
            Ingrediente(nome="Hambúrguer 180g", unidade="un", tipo="insumo", estoque_atual=40.0, estoque_minimo=10.0, custo_unitario=4.50),
            Ingrediente(nome="Pão de Hambúrguer", unidade="un", tipo="insumo", estoque_atual=40.0, estoque_minimo=10.0, custo_unitario=1.20),
            Ingrediente(nome="Arroz", unidade="kg", tipo="insumo", estoque_atual=50.0, estoque_minimo=10.0, custo_unitario=4.00),
            Ingrediente(nome="Feijão", unidade="kg", tipo="insumo", estoque_atual=30.0, estoque_minimo=5.0, custo_unitario=6.00),
            Ingrediente(nome="Guaraná 2L", unidade="un", tipo="revenda", estoque_atual=24.0, estoque_minimo=6.0, custo_unitario=6.50),
        ]
        for i in ingredientes:
            db.session.add(i)
        print(f"✓ {len(ingredientes)} ingredientes criados")
    
    # Adicionar ingredientes extras para as novas receitas (caso não existam)
    extras = [
        Ingrediente(nome="Peito de Frango", unidade="kg", tipo="insumo", estoque_atual=20.0, estoque_minimo=5.0, custo_unitario=12.00),
        Ingrediente(nome="Catupiry", unidade="kg", tipo="insumo", estoque_atual=10.0, estoque_minimo=2.0, custo_unitario=25.00),
        Ingrediente(nome="Goiabada", unidade="kg", tipo="insumo", estoque_atual=10.0, estoque_minimo=2.0, custo_unitario=15.00),
        Ingrediente(nome="Bacon", unidade="kg", tipo="insumo", estoque_atual=10.0, estoque_minimo=2.0, custo_unitario=28.00),
        Ingrediente(nome="Alface", unidade="un", tipo="insumo", estoque_atual=20.0, estoque_minimo=5.0, custo_unitario=3.00),
        Ingrediente(nome="Tomate", unidade="kg", tipo="insumo", estoque_atual=15.0, estoque_minimo=3.0, custo_unitario=6.00),
        Ingrediente(nome="Batata Frita", unidade="kg", tipo="insumo", estoque_atual=50.0, estoque_minimo=10.0, custo_unitario=10.00),
        Ingrediente(nome="Contra Filé", unidade="kg", tipo="insumo", estoque_atual=30.0, estoque_minimo=5.0, custo_unitario=35.00),
        Ingrediente(nome="Maionese", unidade="kg", tipo="insumo", estoque_atual=10.0, estoque_minimo=2.0, custo_unitario=12.00),
    ]
    for i in extras:
        if not Ingrediente.query.filter_by(nome=i.nome).first():
            db.session.add(i)
            print(f"✓ Ingrediente '{i.nome}' adicionado")

    db.session.commit()

    # Criar Fichas Técnicas (Receitas)
    print("\nVerificando fichas técnicas...")
    receitas = {
        "Mussarela": {"Farinha de Trigo": 0.350, "Molho de Tomate": 0.100, "Queijo Mussarela": 0.300},
        "Calabresa": {"Farinha de Trigo": 0.350, "Molho de Tomate": 0.100, "Queijo Mussarela": 0.100, "Calabresa": 0.250},
        "Portuguesa": {"Farinha de Trigo": 0.350, "Molho de Tomate": 0.100, "Queijo Mussarela": 0.150, "Presunto": 0.150, "Ovos": 0.100},
        "Frango com Catupiry": {"Farinha de Trigo": 0.350, "Molho de Tomate": 0.100, "Peito de Frango": 0.250, "Catupiry": 0.150},
        "Brigadeiro": {"Farinha de Trigo": 0.350, "Chocolate ao Leite": 0.300},
        "Romeu e Julieta": {"Farinha de Trigo": 0.350, "Queijo Mussarela": 0.150, "Goiabada": 0.200},
        "X-Salada": {"Pão de Hambúrguer": 1.0, "Hambúrguer 180g": 1.0, "Queijo Mussarela": 0.050, "Alface": 1.0, "Tomate": 0.050, "Maionese": 0.030},
        "X-Bacon": {"Pão de Hambúrguer": 1.0, "Hambúrguer 180g": 1.0, "Queijo Mussarela": 0.050, "Bacon": 0.080, "Maionese": 0.030},
        "Colonial Burger": {"Pão de Hambúrguer": 1.0, "Hambúrguer 180g": 2.0, "Queijo Mussarela": 0.100, "Bacon": 0.100, "Maionese": 0.050},
        "Bife Acebolado": {"Arroz": 0.200, "Feijão": 0.150, "Contra Filé": 0.200, "Batata Frita": 0.150},
        "Filé de Frango": {"Arroz": 0.200, "Feijão": 0.150, "Peito de Frango": 0.200, "Batata Frita": 0.150},
        "Feijoada (Média)": {"Arroz": 0.250, "Feijão": 0.400, "Farinha de Trigo": 0.050, "Calabresa": 0.100},
    }

    for prod_nome, ing_dict in receitas.items():
        prod = Produto.query.filter_by(nome=prod_nome).first()
        if prod and FichaTecnica.query.filter_by(produto_id=prod.id).count() == 0:
            print(f"Criando receita para {prod_nome}...")
            for ing_nome, qtd in ing_dict.items():
                ing = Ingrediente.query.filter_by(nome=ing_nome).first()
                if ing:
                    db.session.add(FichaTecnica(produto_id=prod.id, ingrediente_id=ing.id, quantidade=qtd))
    
    print("✓ Fichas técnicas atualizadas")

    # Criar Cupons
    if Cupom.query.count() == 0:
        print("\nCriando cupons...")
        db.session.add(Cupom(codigo="BEMVINDO10", tipo="porcentagem", valor=10.0, descricao="10% OFF na primeira compra"))
        db.session.add(Cupom(codigo="PIZZA20", tipo="fixo", valor=20.0, descricao="R$ 20,00 de desconto"))
        print("✓ Cupons criados")

    # Criar Fidelidade
    if Fidelidade.query.count() == 0:
        print("\nCriando pontos de fidelidade...")
        db.session.add(Fidelidade(telefone="(11) 99999-9999", pontos=150))
        print("✓ Fidelidade criada")

    # Criar Depoimentos
    if Depoimento.query.count() == 0:
        print("\nCriando depoimentos...")
        db.session.add(Depoimento(nome="Maria Silva", texto="A melhor pizza que já comi! Chegou super quente.", nota=5, aprovado=True))
        db.session.add(Depoimento(nome="João Souza", texto="Muito bom, mas demorou um pouco.", nota=4, aprovado=True))
        print("✓ Depoimentos criados")

    # Criar Reservas
    if Reserva.query.count() == 0:
        print("\nCriando reservas...")
        hoje = datetime.now().date()
        db.session.add(Reserva(nome_cliente="Carlos Oliveira", telefone="(11) 97777-7777", data_reserva=hoje, hora_reserva=datetime.strptime("20:00", "%H:%M").time(), num_pessoas=4, status="Confirmada"))
        db.session.add(Reserva(nome_cliente="Fernanda Lima", telefone="(11) 96666-6666", data_reserva=hoje + timedelta(days=1), hora_reserva=datetime.strptime("19:30", "%H:%M").time(), num_pessoas=2, status="Pendente"))
        print("✓ Reservas criadas")

    # Criar Pedidos (Histórico e Ativos)
    if Pedido.query.count() == 0:
        print("\nCriando pedidos...")
        prod1 = Produto.query.first()
        
        if prod1:
            # Pedido Concluído (Ontem)
            p1 = Pedido(
                data_hora=datetime.now() - timedelta(days=1),
                cliente_nome="Roberto Santos",
                cliente_telefone="(11) 95555-5555",
                cliente_endereco="Rua A, 123",
                status="concluido",
                metodo_pagamento="Cartão de Crédito",
                total=prod1.preco,
                metadata_json=json.dumps({"metodo_envio": "Entrega", "taxa_entrega": "R$ 5,00"})
            )
            db.session.add(p1)
            db.session.flush()
            db.session.add(ItemPedido(pedido_id=p1.id, produto_nome=prod1.nome, produto_id=prod1.id, quantidade=1, preco_unitario=prod1.preco))

            # Pedido Pendente (Hoje - KDS)
            p2 = Pedido(
                data_hora=datetime.now(),
                cliente_nome="Julia Costa",
                cliente_telefone="(11) 94444-4444",
                cliente_endereco="",
                status="Pendente",
                metodo_pagamento="Pix",
                total=prod1.preco,
                metadata_json=json.dumps({"metodo_envio": "Retirada"})
            )
            db.session.add(p2)
            db.session.flush()
            db.session.add(ItemPedido(pedido_id=p2.id, produto_nome=prod1.nome, produto_id=prod1.id, quantidade=1, preco_unitario=prod1.preco))
            
            print("✓ Pedidos criados")
    
    db.session.commit()
    
    print("\n=== Banco de Dados Populado com Sucesso! ===")
    print(f"Banners: {Banner.query.count()}")
    print(f"Categorias: {Categoria.query.count()}")
    print(f"Produtos: {Produto.query.count()}")
