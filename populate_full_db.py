from app import app
from database import db
from models import Categoria, Produto, Ingrediente, FichaTecnica
from datetime import date

def populate():
    with app.app_context():
        print("--- Iniciando População do Banco de Dados ---")
        
        # 1. Limpar banco (opcional, para evitar duplicatas em testes)
        # db.drop_all()
        # db.create_all()
        
        # Verifica se já tem dados para não duplicar se rodar 2x (ou limpa tudo antes, dependendo do objetivo)
        if Produto.query.count() > 0:
            print("Banco já contém produtos. Limpando dados antigos de teste (opcional)...")
            # Descomente para forçar limpeza:
            # db.session.query(FichaTecnica).delete()
            # db.session.query(Produto).delete()
            # db.session.query(Categoria).delete()
            # db.session.query(Ingrediente).delete()
            # db.session.commit()
            pass

        # 2. Criar Ingredientes (Estoque Base)
        print("Criando Ingredientes...")
        ingredientes_data = [
            # Massas e Bases
            {"nome": "Farinha de Trigo", "un": "kg", "custo": 4.50, "estoque": 50.0},
            {"nome": "Massa de Pizza (Bola)", "un": "un", "custo": 2.00, "estoque": 100.0, "tipo": "fabricado"}, # Pré-fabricado
            {"nome": "Massa de Esfiha (Bola)", "un": "un", "custo": 0.50, "estoque": 200.0, "tipo": "fabricado"},
            {"nome": "Molho de Tomate", "un": "l", "custo": 12.00, "estoque": 20.0},
            
            # Queijos e Laticínios
            {"nome": "Mussarela", "un": "kg", "custo": 38.00, "estoque": 30.0},
            {"nome": "Catupiry Original", "un": "kg", "custo": 45.00, "estoque": 15.0},
            {"nome": "Provolone", "un": "kg", "custo": 50.00, "estoque": 10.0},
            {"nome": "Parmesão", "un": "kg", "custo": 60.00, "estoque": 5.0},
            {"nome": "Cheddar", "un": "kg", "custo": 40.00, "estoque": 10.0},
            {"nome": "Gorgonzola", "un": "kg", "custo": 55.00, "estoque": 5.0},
            
            # Carnes
            {"nome": "Calabresa Moída", "un": "kg", "custo": 28.00, "estoque": 20.0},
            {"nome": "Calabresa Fatiada", "un": "kg", "custo": 28.00, "estoque": 20.0},
            {"nome": "Carne Moída Temperada", "un": "kg", "custo": 32.00, "estoque": 25.0},
            {"nome": "Frango Desfiado Temperado", "un": "kg", "custo": 22.00, "estoque": 25.0},
            {"nome": "Bacon Cubos", "un": "kg", "custo": 35.00, "estoque": 10.0},
            {"nome": "Presunto", "un": "kg", "custo": 25.00, "estoque": 20.0},
            {"nome": "Pepperoni", "un": "kg", "custo": 60.00, "estoque": 5.0},
            {"nome": "Carne Seca Desfiada", "un": "kg", "custo": 55.00, "estoque": 8.0},
            {"nome": "Hambúrguer Artesanal 180g", "un": "un", "custo": 6.00, "estoque": 40.0},
            
            # Vegetais e Outros
            {"nome": "Cebola", "un": "kg", "custo": 5.00, "estoque": 15.0},
            {"nome": "Tomate Fatiado", "un": "kg", "custo": 8.00, "estoque": 10.0},
            {"nome": "Ervilha", "un": "kg", "custo": 10.00, "estoque": 10.0},
            {"nome": "Milho Verde", "un": "kg", "custo": 10.00, "estoque": 10.0},
            {"nome": "Palmito", "un": "kg", "custo": 45.00, "estoque": 5.0},
            {"nome": "Azeitona", "un": "kg", "custo": 20.00, "estoque": 8.0},
            {"nome": "Orégano", "un": "kg", "custo": 60.00, "estoque": 2.0},
            {"nome": "Alho Frito", "un": "kg", "custo": 80.00, "estoque": 2.0},
            
            # Doces
            {"nome": "Chocolate ao Leite", "un": "kg", "custo": 40.00, "estoque": 10.0},
            {"nome": "Chocolate Branco", "un": "kg", "custo": 45.00, "estoque": 5.0},
            {"nome": "Granulado", "un": "kg", "custo": 20.00, "estoque": 5.0},
            {"nome": "Morango", "un": "kg", "custo": 25.00, "estoque": 5.0},
            {"nome": "Leite Condensado", "un": "un", "custo": 5.00, "estoque": 20.0},
            
            # Revenda (Bebidas)
            {"nome": "Coca-Cola 2L (Estoque)", "un": "un", "custo": 8.00, "estoque": 48.0, "tipo": "revenda"},
            {"nome": "Guaraná Antarctica 2L (Estoque)", "un": "un", "custo": 7.00, "estoque": 48.0, "tipo": "revenda"},
            {"nome": "Suco Del Valle 1L", "un": "un", "custo": 5.00, "estoque": 24.0, "tipo": "revenda"},
            {"nome": "Cerveja Lata", "un": "un", "custo": 3.50, "estoque": 100.0, "tipo": "revenda"},
        ]

        ingr_objs = {}
        for item in ingredientes_data:
            i = Ingrediente.query.filter_by(nome=item["nome"]).first()
            if not i:
                i = Ingrediente(
                    nome=item["nome"],
                    unidade=item["un"],
                    custo_unitario=item["custo"],
                    estoque_atual=item["estoque"],
                    estoque_minimo=5.0,
                    tipo=item.get("tipo", "insumo"),
                    validade=date(2025, 12, 31)
                )
                db.session.add(i)
            ingr_objs[item["nome"]] = i
        
        db.session.commit()
        # Recarrega para garantir IDs
        for nome, obj in ingr_objs.items():
            ingr_objs[nome] = Ingrediente.query.filter_by(nome=nome).first()

        # 3. Criar Categorias
        print("Criando Categorias...")
        cats_data = ["Pizzas Salgadas", "Pizzas Doces", "Esfihas", "Esfihas Doces", "Fogazzas", "Fogazzas Doces", "Bebidas", "Hambúrgueres", "Marmitex"]
        cat_objs = {}
        for idx, nome in enumerate(cats_data):
            c = Categoria.query.filter_by(nome=nome).first()
            if not c:
                c = Categoria(nome=nome, ordem=idx+1, visivel=True)
                db.session.add(c)
            cat_objs[nome] = c
        db.session.commit()
        # Recarrega
        for nome in cats_data:
            cat_objs[nome] = Categoria.query.filter_by(nome=nome).first()

        # 4. Criar Produtos e Fichas Técnicas
        print("Criando Produtos e Fichas Técnicas...")
        
        def add_produto(cat_nome, nome, preco, desc, ingredientes_receita):
            cat = cat_objs.get(cat_nome)
            if not cat: return
            
            p = Produto.query.filter_by(nome=nome, categoria_id=cat.id).first()
            if not p:
                tipo = 'revenda' if cat_nome == 'Bebidas' else 'fabricado'
                ing_link = None
                
                # Se for revenda, tenta achar o item de estoque correspondente para link direto
                if tipo == 'revenda' and len(ingredientes_receita) == 1:
                     ing_nome, _ = ingredientes_receita[0]
                     ing = ingr_objs.get(ing_nome)
                     if ing: ing_link = ing.id

                p = Produto(
                    categoria_id=cat.id,
                    nome=nome,
                    descricao=desc,
                    preco=preco,
                    visivel=True,
                    tipo=tipo,
                    ingrediente_id=ing_link
                )
                db.session.add(p)
                db.session.flush() # Gera ID
                
                # Cria Ficha Técnica
                if tipo == 'fabricado':
                    for ing_nome, qtd in ingredientes_receita:
                        ing = ingr_objs.get(ing_nome)
                        if ing:
                            ft = FichaTecnica(produto_id=p.id, ingrediente_id=ing.id, quantidade=qtd)
                            db.session.add(ft)
                
                print(f" + Produto criado: {nome}")
            else:
                print(f" . Produto já existe: {nome}")

        # --- DADOS DO CARDÁPIO (Transição das Imagens) ---
        
        # PIZZAS SALGADAS (Base: Massa + Molho)
        base_pizza = [("Massa de Pizza (Bola)", 1), ("Molho de Tomate", 0.15)]
        
        add_produto("Pizzas Salgadas", "Mussarela", 49.00, "Mussarela, rodelas de tomate e orégano.", 
                    base_pizza + [("Mussarela", 0.300), ("Tomate Fatiado", 0.100), ("Orégano", 0.005)])
        
        add_produto("Pizzas Salgadas", "Calabresa", 49.00, "Calabresa fatiada e cebola.", 
                    base_pizza + [("Calabresa Fatiada", 0.250), ("Cebola", 0.100)])
                    
        add_produto("Pizzas Salgadas", "Portuguesa", 54.00, "Presunto, ovos, ervilha, cebola e mussarela.", 
                    base_pizza + [("Presunto", 0.150), ("Ervilha", 0.050), ("Cebola", 0.050), ("Mussarela", 0.150)])
                    
        add_produto("Pizzas Salgadas", "Frango c/ Catupiry", 54.00, "Frango desfiado e catupiry original.", 
                    base_pizza + [("Frango Desfiado Temperado", 0.250), ("Catupiry Original", 0.150)])
                    
        add_produto("Pizzas Salgadas", "Quatro Queijos", 57.00, "Mussarela, catupiry, provolone e parmesão.", 
                    base_pizza + [("Mussarela", 0.100), ("Catupiry Original", 0.100), ("Provolone", 0.100), ("Parmesão", 0.050)])
        
        add_produto("Pizzas Salgadas", "Bacon", 49.00, "Musarela e bacon.", 
                   base_pizza + [("Mussarela", 0.200), ("Bacon Cubos", 0.150)])

        # ESFIHAS (Base: Massa Esfiha)
        base_esfiha = [("Massa de Esfiha (Bola)", 1)]
        
        add_produto("Esfihas", "Carne", 4.00, "Carne moída temperada.", 
                    base_esfiha + [("Carne Moída Temperada", 0.060)])
                    
        add_produto("Esfihas", "Queijo", 4.00, "Mussarela.", 
                    base_esfiha + [("Mussarela", 0.050)])
                    
        add_produto("Esfihas", "Calabresa", 4.00, "Calabresa moída.", 
                    base_esfiha + [("Calabresa Moída", 0.050)])
                    
        add_produto("Esfihas", "Frango c/ Catupiry", 6.50, "Frango temperado com catupiry.", 
                    base_esfiha + [("Frango Desfiado Temperado", 0.040), ("Catupiry Original", 0.020)])
                    
        add_produto("Esfihas", "Bacon", 6.50, "Bacon picado com mussarela.", 
                    base_esfiha + [("Mussarela", 0.030), ("Bacon Cubos", 0.030)])

        # FOGAZZAS (Base: Massa Pizza Dobrada - Estimativa)
        base_fogazza = [("Massa de Pizza (Bola)", 0.6)] 
        
        add_produto("Fogazzas", "Calabresa", 25.00, "Calabresa e cebola.",
                   base_fogazza + [("Calabresa Fatiada", 0.150), ("Cebola", 0.050)])

        add_produto("Fogazzas", "Mussarela", 25.00, "Mussarela.",
                   base_fogazza + [("Mussarela", 0.200)])
                   
        # PIZZAS DOCES
        base_brotinho = [("Massa de Pizza (Bola)", 0.5)] # Meia massa
        
        add_produto("Pizzas Doces", "Chocolate", 45.00, "Chocolate ao leite.",
                   base_brotinho + [("Chocolate ao Leite", 0.200)])
                   
        add_produto("Pizzas Doces", "Prestígio", 46.90, "Chocolate e coco ralado.",
                   base_brotinho + [("Chocolate ao Leite", 0.150)]) # simplificado

        # HAMBURGUER
        add_produto("Hambúrgueres", "X-Salada", 22.00, "Hambúrguer, queijo, alface e tomate.",
                   [("Hambúrguer Artesanal 180g", 1), ("Mussarela", 0.030), ("Tomate Fatiado", 0.030)])

        # BEBIDAS (Revenda)
        add_produto("Bebidas", "Coca-Cola 2L", 14.00, "Garrafa 2 Litros", [("Coca-Cola 2L (Estoque)", 1)])
        add_produto("Bebidas", "Guaraná 2L", 12.00, "Garrafa 2 Litros", [("Guaraná Antarctica 2L (Estoque)", 1)])
        
        db.session.commit()
        print("--- População Concluída com Sucesso! ---")

if __name__ == "__main__":
    populate()
