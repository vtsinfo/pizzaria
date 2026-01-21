import sys
import os
from werkzeug.security import generate_password_hash

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import User
from database import db

with app.app_context():
    print("=== Criando Usuário Admin ===\n")
    
    # Verifica se já existe
    if User.query.filter_by(username='admin').first():
        print("Usuário 'admin' já existe.")
    else:
        password = "pizza123"
        print(f"Criando usuário 'admin' com senha '{password}'...")
        
        admin = User(
            username="admin", 
            password_hash=generate_password_hash(password), 
            role="admin", 
            permissions='["all"]'
        )
        db.session.add(admin)
        db.session.commit()
        print("✓ Usuário 'admin' criado com sucesso.")

    print("\n=== Fim da Operação ===")
