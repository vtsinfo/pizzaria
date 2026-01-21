from app import app
from models import Pedido

with app.app_context():
    count = Pedido.query.count()
    pedidos = Pedido.query.all()
    print(f"--- VERIFICAÇÃO DE PEDIDOS ---")
    print(f"Total de Pedidos no Banco de Dados: {count}")
    for p in pedidos:
        print(f"ID: {p.id} | Cliente: {p.cliente_nome} | Total: R$ {p.total:.2f}")
