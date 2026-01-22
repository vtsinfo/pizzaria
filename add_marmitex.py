from app import app
from database import db
from models import Categoria, Produto, Ingrediente, FichaTecnica

def add_marmitex_and_beverages():
    with app.app_context():
        print("--- Cadastrando Marmitex e Verificando Bebidas ---")

        # 1. Garantir Categoria Marmitex
        cat_marmitex = Categoria.query.filter_by(nome="Marmitex").first()
        if not cat_marmitex:
            cat_marmitex = Categoria(nome="Marmitex", visivel=True, ordem=10)
            db.session.add(cat_marmitex)
            db.session.commit()
            print("Categoria 'Marmitex' criada.")

        # 2. Produtos Marmitex
        marmitex_items = [
            {
                "nome": "Churrasco Misto",
                "desc": "Arroz, feijão, batatas fritas, carne assada, linguiça assada e frango assado",
                "preco": 38.00
            },
            {
                "nome": "Frango Assado",
                "desc": "Arroz, feijão, batatas fritas, frango assado e linguiça assada",
                "preco": 32.00
            },
            {
                "nome": "Frango à Parmegiana",
                "desc": "Arroz, feijão, batatas fritas, filé de frango à parmegiana",
                "preco": 35.00
            },
            {
                "nome": "Fraldinha Assada",
                "desc": "Arroz, feijão, batatas fritas, fraldinha assada, linguiça assada e frango assado",
                "preco": 42.00
            },
            {
                "nome": "Picanha Assada",
                "desc": "Arroz, feijão, batatas fritas, picanha assada, linguiça assada e frango assado",
                "preco": 48.00
            },
            {
                "nome": "Filé de Merluza",
                "desc": "Arroz, feijão, batatas fritas, filé de merluza frito",
                "preco": 35.00
            }
        ]

        for item in marmitex_items:
            prod = Produto.query.filter_by(nome=item['nome'], categoria_id=cat_marmitex.id).first()
            if not prod:
                prod = Produto(
                    categoria_id=cat_marmitex.id,
                    nome=item['nome'],
                    descricao=item['desc'],
                    preco=item['preco'],
                    tipo='fabricado',
                    visivel=True
                )
                db.session.add(prod)
                print(f" + Marmitex criado: {item['nome']}")
            else:
                prod.descricao = item['desc'] # Atualiza descrição se já existe
                print(f" . Marmitex já existe: {item['nome']}")

        # 3. Verificar Bebidas (Revenda) e Estoque Relacionado
        cat_bebidas = Categoria.query.filter_by(nome="Bebidas").first()
        if not cat_bebidas:
            print("! Categoria Bebidas não encontrada.")
            return

        bebidas_items = [
            {"nome": "Coca-Cola 2L", "ingrediente": "Coca-Cola 2L (Estoque)", "preco": 14.00},
            {"nome": "Guaraná 2L", "ingrediente": "Guaraná Antarctica 2L (Estoque)", "preco": 12.00},
            {"nome": "Suco Del Valle", "ingrediente": "Suco Del Valle 1L", "preco": 10.00},
            {"nome": "Cerveja Lata", "ingrediente": "Cerveja Lata", "preco": 9.00}
        ]

        for beb in bebidas_items:
            # Garante Estoque
            ing = Ingrediente.query.filter_by(nome=beb['ingrediente']).first()
            if not ing:
                ing = Ingrediente(
                    nome=beb['ingrediente'],
                    unidade='un',
                    custo_unitario=5.00,
                    estoque_atual=50.0,
                    tipo='revenda'
                )
                db.session.add(ing)
                db.session.commit() # Commit para ter ID
                print(f" + Ingrediente de revenda criado: {beb['ingrediente']}")
            
            # Garante Produto e Link
            prod = Produto.query.filter_by(nome=beb['nome'], categoria_id=cat_bebidas.id).first()
            if not prod:
                prod = Produto(
                    categoria_id=cat_bebidas.id,
                    nome=beb['nome'],
                    descricao=beb.get('desc', 'Bebida Gelada'),
                    preco=beb['preco'],
                    tipo='revenda',
                    ingrediente_id=ing.id, # Link direto para baixa de estoque
                    visivel=True
                )
                db.session.add(prod)
                print(f" + Bebida criada: {beb['nome']}")
            else:
                # Atualiza link se estiver faltando
                if not prod.ingrediente_id:
                    prod.ingrediente_id = ing.id
                    prod.tipo = 'revenda'
                    print(f" > Bebida atualizada (vínculo estoque): {beb['nome']}")

        db.session.commit()
        print("--- Concluído ---")

if __name__ == "__main__":
    add_marmitex_and_beverages()
