import sys
import os
from werkzeug.security import check_password_hash

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import User
from database import db

with app.app_context():
    print("=== Verificando Usuário Admin ===\n")
    
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("✓ Usuário 'admin' encontrado.")
        if check_password_hash(admin.password_hash, 'pizza123'):
            print("✓ Senha 'pizza123' CORRETA.")
        else:
            print("❌ Senha 'pizza123' INCORRETA.")
    else:
        print("❌ Usuário 'admin' NÃO encontrado.")
    
    print("\n=== Fim da Verificação ===")