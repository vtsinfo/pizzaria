import os
import json
import hashlib
from app import app
from database import db
from models import Categoria, Produto, User

# Caminho do arquivo JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARDAPIO_FILE = os.path.join(BASE_DIR, 'cardapio.json')

def populate():
    with app.app_context():
        print("🔄 Iniciando configuração do Banco de Dados...")

        # 1. Criar Usuário Admin se não existir
        if User.query.filter_by(username="admin").first() is None:
            print("👤 Criando usuário admin padrão...")
            default_pass = hashlib.sha256("pizza123".encode()).hexdigest()
            admin = User(username="admin", password_hash=default_pass, role="admin", permissions='["all"]')
            db.session.add(admin)
            print("   -> Usuário criado: admin / Senha: pizza123")
        else:
            print("👤 Usuário admin já existe.")

        # 2. Popular Cardápio se estiver vazio
        if Categoria.query.first():
            print("⚠️  O cardápio já está cadastrado no banco.")
        else:
            if not os.path.exists(CARDAPIO_FILE):
                print("❌ Arquivo cardapio.json não encontrado.")
            else:
                print("📂 Lendo cardapio.json...")
                with open(CARDAPIO_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                print("🚀 Importando produtos...")
                ordem = 0
                for cat_nome, itens in data.items():
                    ordem += 1
                    # Cria Categoria
                    cat = Categoria(nome=cat_nome, ordem=ordem, visivel=True, exibir_preco=True)
                    db.session.add(cat)
                    db.session.flush() # Garante o ID da categoria
                    
                    print(f"   - Categoria: {cat_nome}")

                    for item in itens:
                        # Converte preço (R$ 20,00 -> 20.00)
                        preco_val = 0.0
                        try:
                            p_str = str(item.get('preco', '0')).replace('R$', '').replace('.', '').replace(',', '.').strip()
                            preco_val = float(p_str)
                        except: pass

                        prod = Produto(
                            categoria_id=cat.id,
                            nome=item.get('nome'),
                            descricao=item.get('desc'),
                            preco=preco_val,
                            foto_url=item.get('foto', ''),
                            visivel=item.get('visivel', True),
                            esgotado=item.get('esgotado', False)
                        )
                        db.session.add(prod)
                print("✅ Cardápio importado com sucesso!")

        db.session.commit()
        print("\n🎉 Configuração concluída! Pode rodar o site agora.")

if __name__ == "__main__":
    populate()