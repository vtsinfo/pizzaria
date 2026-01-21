import os
import sys
import json
import hashlib

# Adiciona o diretório atual ao path para importar app e models corretamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import Categoria, Produto, User

# Caminho do arquivo JSON (garante que acha o arquivo na pasta pizzaria)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDAPIO_FILE = os.path.join(BASE_DIR, 'pizzaria', 'cardapio.json')

def populate():
    with app.app_context():
        print("🔄 Iniciando população do Banco de Dados...")
        
        # Garante que as tabelas existem
        db.create_all()

        # 1. Criar Usuário Admin
        if User.query.filter_by(username="admin").first() is None:
            print("👤 Criando usuário admin...")
            default_pass = hashlib.sha256("pizza123".encode()).hexdigest()
            admin = User(username="admin", password_hash=default_pass, role="admin", permissions='["all"]')
            db.session.add(admin)

        # 2. Popular Cardápio
        if Produto.query.count() > 0:
            print("⚠️  Produtos já existem no banco. Pulando importação.")
        else:
            # Tenta achar o arquivo json
            if not os.path.exists(CARDAPIO_FILE):
                # Tenta no diretório local do script
                CARDAPIO_FILE_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cardapio.json')
                if os.path.exists(CARDAPIO_FILE_LOCAL):
                    CARDAPIO_FILE = CARDAPIO_FILE_LOCAL
            
            if os.path.exists(CARDAPIO_FILE):
                print(f"📂 Importando de: {CARDAPIO_FILE}")
                with open(CARDAPIO_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                ordem = 0
                for cat_nome, itens in data.items():
                    ordem += 1
                    # Busca ou cria categoria
                    cat = Categoria.query.filter_by(nome=cat_nome).first()
                    if not cat:
                        cat = Categoria(nome=cat_nome, ordem=ordem, visivel=True, exibir_preco=True)
                        db.session.add(cat)
                        db.session.flush()
                    
                    for item in itens:
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
                print("✅ Produtos importados com sucesso!")
            else:
                print("❌ cardapio.json não encontrado.")

        db.session.commit()
        print("🎉 Concluído!")

if __name__ == "__main__":
    populate()