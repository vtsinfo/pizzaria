try:
    from .database import db
except ImportError:
    from database import db
from datetime import datetime
import json

# --- TABELAS DE ADMINISTRAÇÃO E ACESSO ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='editor') # admin, editor, viewer
    permissions = db.Column(db.Text, default='[]') # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Unidade(db.Model):
    __tablename__ = 'unidades'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False) # Ex: Matriz, Filial Centro
    endereco = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))
    email = db.Column(db.String(120)) # Novo campo
    instagram = db.Column(db.String(100))
    facebook = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- TABELAS DE ESTOQUE E FICHA TÉCNICA (NOVO ERP) ---
class Ingrediente(db.Model):
    __tablename__ = 'ingredientes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.String(20), nullable=False) # kg, g, l, ml, un
    tipo = db.Column(db.String(20), default='insumo') # insumo, revenda, ambos
    estoque_atual = db.Column(db.Float, default=0.0)
    estoque_minimo = db.Column(db.Float, default=1.0) # Ponto de pedido
    custo_unitario = db.Column(db.Float, default=0.0) # Para cálculo de CMV
    fornecedor = db.Column(db.String(100))
    validade = db.Column(db.Date) # Data de validade do lote atual
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- CARDÁPIO E PRODUTOS ---
class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    ordem = db.Column(db.Integer, default=0)
    visivel = db.Column(db.Boolean, default=True)
    exibir_preco = db.Column(db.Boolean, default=True)
    foto_url = db.Column(db.String(255))
    produtos = db.relationship('Produto', backref='categoria', lazy=True)

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    foto_url = db.Column(db.String(255))
    visivel = db.Column(db.Boolean, default=True)
    esgotado = db.Column(db.Boolean, default=False)
    tipo = db.Column(db.String(20), default='fabricado') # fabricado, revenda
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingredientes.id'), nullable=True) # Para revenda direta
    
    # Relacionamento com Ingredientes (Ficha Técnica)
    receita = db.relationship('FichaTecnica', backref='produto', lazy=True)

class FichaTecnica(db.Model):
    """Liga Produto a Ingredientes (Receita)"""
    __tablename__ = 'ficha_tecnica'
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingredientes.id'), nullable=False)
    quantidade = db.Column(db.Float, nullable=False) # Quanto usa desse ingrediente
    
    # Relacionamento
    ingrediente = db.relationship('Ingrediente', backref='fichas_tecnicas')

# --- VENDAS E PEDIDOS ---
class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_nome = db.Column(db.String(100))
    cliente_telefone = db.Column(db.String(20))
    cliente_endereco = db.Column(db.Text)
    
    status = db.Column(db.String(20), default='novo') # novo, preparo, entrega, concluido, cancelado
    metodo_pagamento = db.Column(db.String(50))
    total = db.Column(db.Float, default=0.0)
    
    # JSON para armazenar dados flexíveis (ex: taxas, cupons aplicados)
    metadata_json = db.Column(db.Text) 
    
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True)

class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_nome = db.Column(db.String(100)) # Copia nome caso produto seja deletado depois
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True) # Link opcional
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.String(200))

# --- RESERVAS ---
class Reserva(db.Model):
    __tablename__ = 'reservas'
    id = db.Column(db.Integer, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    data_reserva = db.Column(db.Date, nullable=False)
    hora_reserva = db.Column(db.Time, nullable=False)
    num_pessoas = db.Column(db.Integer, nullable=False)
    observacao = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pendente') # Pendente, Confirmada, Cancelada, Concluida
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- DEPOIMENTOS ---
class Depoimento(db.Model):
    __tablename__ = 'depoimentos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    nota = db.Column(db.Integer, default=5)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    aprovado = db.Column(db.Boolean, default=False) # Para moderação futura

class Fidelidade(db.Model):
    __tablename__ = 'fidelidade'
    id = db.Column(db.Integer, primary_key=True)
    telefone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    pontos = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Cupom(db.Model):
    __tablename__ = 'cupons'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # 'porcentagem' ou 'fixo'
    valor = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.String(200))
    ativo = db.Column(db.Boolean, default=True)

class Banner(db.Model):
    __tablename__ = 'banners'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100))
    descricao = db.Column(db.String(200))
    imagem_url = db.Column(db.String(255), nullable=False)
    link_url = db.Column(db.String(255))
    link_text = db.Column(db.String(50))
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)

# --- GESTÃO DE COMPRAS E FORNECEDORES ---
class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    id = db.Column(db.Integer, primary_key=True)
    nome_empresa = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(20))
    contato_nome = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Compra(db.Model):
    __tablename__ = 'compras'
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'))
    data_compra = db.Column(db.DateTime, default=datetime.utcnow)
    nota_fiscal = db.Column(db.String(50))
    total = db.Column(db.Float, default=0.0)
    observacao = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    fornecedor = db.relationship('Fornecedor', backref='compras')
    itens = db.relationship('ItemCompra', backref='compra', lazy=True)

class ItemCompra(db.Model):
    __tablename__ = 'itens_compra'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    ingrediente_id = db.Column(db.Integer, db.ForeignKey('ingredientes.id'), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    # Relacionamentos
    ingrediente = db.relationship('Ingrediente')
