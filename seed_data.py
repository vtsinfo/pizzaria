import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'pizzaria.db')

def seed():
    if not os.path.exists(DB_PATH):
        print("❌ Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Ingredientes
        print("🌱 Semeando Ingredientes...")
        ingredientes = [
            ('Farinha de Trigo', 'kg', 'insumo', 50.0, 5.0, 4.50),
            ('Mussarela', 'kg', 'insumo', 20.0, 2.0, 35.00),
            ('Molho de Tomate', 'l', 'insumo', 30.0, 5.0, 8.00),
            ('Calabresa', 'kg', 'insumo', 15.0, 2.0, 28.00),
            ('Orégano', 'g', 'insumo', 1000.0, 200.0, 0.05),
            ('Coca-Cola 2L', 'un', 'revenda', 48.0, 12.0, 7.50)
        ]
        cursor.executemany("""
            INSERT INTO ingredientes (nome, unidade, tipo, estoque_atual, estoque_minimo, custo_unitario)
            SELECT ?, ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM ingredientes WHERE nome = ?)
        """, [i + (i[0],) for i in ingredientes])

        # 2. Fornecedores
        print("🌱 Semeando Fornecedores...")
        fornecedores = [
            ('Atacadão das Massas', '12.345.678/0001-90', 'João Silva', '(11) 99999-1234', 'contato@atacadao.com'),
            ('Distribuidora de Bebidas Fast', '98.765.432/0001-10', 'Maria Souza', '(11) 98888-5678', 'vendas@fastbebidas.com')
        ]
        cursor.executemany("""
            INSERT INTO fornecedores (nome_empresa, cnpj, contato_nome, telefone, email)
            SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM fornecedores WHERE nome_empresa = ?)
        """, [f + (f[0],) for f in fornecedores])

        # 3. Produtos (Categorias já devem existir pelo app.py, mas garantindo alguns produtos)
        print("🌱 Semeando Produtos...")
        # Assume Categoria ID 1 = Pizzas Salgadas, 2 = Bebidas (Ajustar se necessário, mas simples inserts resolvem)
        # Primeiro, garante categorias
        cursor.execute("INSERT OR IGNORE INTO categorias (id, nome, ordem) VALUES (1, 'Pizzas Tradicionais', 1)")
        cursor.execute("INSERT OR IGNORE INTO categorias (id, nome, ordem) VALUES (2, 'Bebidas', 2)")
        
        produtos = [
            (1, 'Mussarela', 'Molho, mussarela e orégano', 45.00, None, 'fabricado'),
            (1, 'Calabresa', 'Molho, mussarela, calabresa e cebola', 48.00, None, 'fabricado'),
            (2, 'Coca-Cola 2L', 'Refrigerante 2 Litros', 14.00, 6, 'revenda') # Check if ingrediente_id 6 matches coca above
        ]
        
        # Para revenda precisa linkar ID do ingrediente correto. 
        # Buscando ID da Coca
        cursor.execute("SELECT id FROM ingredientes WHERE nome = 'Coca-Cola 2L'")
        coca_id = cursor.fetchone()
        coca_id = coca_id[0] if coca_id else None

        for cat_id, nome, desc, preco, ing_id, tipo in produtos:
             real_ing_id = coca_id if nome == 'Coca-Cola 2L' else None
             cursor.execute("""
                INSERT INTO produtos (categoria_id, nome, descricao, preco, ingrediente_id, tipo)
                SELECT ?, ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM produtos WHERE nome = ?)
             """, (cat_id, nome, desc, preco, real_ing_id, tipo, nome))

        conn.commit()
        print("✅ Dados de teste inseridos com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao semear dados: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed()
