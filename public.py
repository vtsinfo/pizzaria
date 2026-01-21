from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import Banner, Categoria, Produto
from datetime import datetime
import json
import os

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    banners = []
    try:
        banners_db = Banner.query.filter_by(ativo=True).order_by(Banner.ordem).all()
        banners = [{
            "title": b.titulo, 
            "subtitle": b.descricao, 
            "image": b.imagem_url
        } for b in banners_db]
    except Exception as e:
        print(f"Erro ao carregar banners: {e}")
        
    return render_template('index.html', title='Pizzaria Colonial', banners=banners)

@public_bp.route('/cardapio')
def cardapio():
    categorias_db = Categoria.query.filter_by(visivel=True).order_by(Categoria.ordem).all()
    menu = {}
    config = {}
    for cat in categorias_db:
        produtos_db = Produto.query.filter_by(categoria_id=cat.id, visivel=True).all()
        items_list = [{
            "id": p.id, "nome": p.nome, "desc": p.descricao,
            "preco": f"R$ {(p.preco or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "foto": p.foto_url, "visivel": p.visivel
        } for p in produtos_db]
        if items_list:
            menu[cat.nome] = items_list
            config[cat.nome] = {"visible": True, "show_price": cat.exibir_preco}
    return render_template('cardapio.html', title='Nosso Cardápio', menu=menu, config=config)

@public_bp.route('/reservas', methods=['GET', 'POST'])
def reservas():
    if request.method == 'POST':
        # Lógica de salvar reserva (Pode ser movida para o banco futuramente)
        flash('Sua solicitação de reserva foi enviada!', 'success')
        return redirect(url_for('public.reservas'))
    return render_template('reservas.html', title='Reservas')

@public_bp.route('/unidades')
def unidades():
    return render_template('unidades.html', title='Nossas Unidades')