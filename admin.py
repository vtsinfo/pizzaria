from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, Response, send_file, current_app
from models import Fidelidade, db, Pedido, ItemPedido, Ingrediente, FichaTecnica, Produto, User, Cupom, Banner
from functools import wraps
import os
import json
import csv
import io
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helpers necessários movidos do app.py
def parse_price(price_str):
    if not price_str: return 0.0
    try:
        if isinstance(price_str, (int, float)): return float(price_str)
        clean = str(price_str).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(clean)
    except: return 0.0

def log_activity(action):
    LOGS_FILE = os.path.join(current_app.root_path, 'logs.json')
    entry = {
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "user": session.get('username', 'Sistema'),
        "action": action
    }
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except: pass
    logs.insert(0, entry)
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs[:1000], f, indent=4, ensure_ascii=False)

@admin_bp.route('/fidelidade')
@login_required
def fidelidade_list():
    """Lista todos os clientes e seus pontos de fidelidade."""
    search = request.args.get('q', '')
    query = Fidelidade.query
    if search:
        # Filtra por telefone contendo a string de busca
        query = query.filter(Fidelidade.telefone.contains(search))
    
    clientes = query.order_by(Fidelidade.pontos.desc()).all()
    return render_template('admin_fidelidade.html', title='Gestão de Fidelidade', clientes=clientes)

@admin_bp.route('/fidelidade/edit/<int:id>', methods=['POST'])
@login_required
def fidelidade_edit(id):
    """Edita os pontos de um cliente específico."""
    cliente = Fidelidade.query.get_or_404(id)
    try:
        novos_pontos = int(request.form.get('pontos', 0))
        cliente.pontos = novos_pontos
        db.session.commit()
        flash(f'Pontos de {cliente.telefone} atualizados com sucesso!', 'success')
    except (ValueError, TypeError):
        flash('Por favor, insira um número válido para os pontos.', 'danger')
    return redirect(url_for('admin.fidelidade_list'))

@admin_bp.route('/fidelidade/delete/<int:id>', methods=['POST'])
@login_required
def fidelidade_delete(id):
    """Remove um registro de fidelidade."""
    cliente = Fidelidade.query.get_or_404(id)
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash(f'Registro de {cliente.telefone} removido.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover registro: {str(e)}', 'danger')
    return redirect(url_for('admin.fidelidade_list'))

# --- GESTÃO DE RECEITAS (FICHA TÉCNICA) ---

@admin_bp.route('/api/receita/<int:produto_id>', methods=['GET'])
@login_required
def get_receita(produto_id):
    receita = FichaTecnica.query.filter_by(produto_id=produto_id).all()
    return jsonify([{
        "id": item.id,
        "ingrediente_id": item.ingrediente_id,
        "nome_ingrediente": item.ingrediente.nome,
        "unidade": item.ingrediente.unidade,
        "quantidade": item.quantidade
    } for item in receita])

@admin_bp.route('/api/receita', methods=['POST'])
@login_required
def save_receita():
    data = request.get_json()
    try:
        produto_id = int(data.get('produto_id'))
        ingrediente_id = int(data.get('ingrediente_id'))
        quantidade = float(data.get('quantidade', 0))
        action = data.get('action')
        
        if action == 'add':
            item = FichaTecnica.query.filter_by(produto_id=produto_id, ingrediente_id=ingrediente_id).first()
            if item:
                item.quantidade = quantidade
            else:
                db.session.add(FichaTecnica(produto_id=produto_id, ingrediente_id=ingrediente_id, quantidade=quantidade))
        elif action == 'remove':
            item = FichaTecnica.query.filter_by(produto_id=produto_id, ingrediente_id=ingrediente_id).first()
            if item:
                db.session.delete(item)
                
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

# --- ROTAS DE ESTOQUE MOVIDAS ---

@admin_bp.route('/estoque')
@login_required
def admin_estoque():
    produtos = Produto.query.order_by(Produto.nome).all()
    return render_template('admin_estoque.html', title='Gestão de Estoque', produtos=produtos)

@admin_bp.route('/api/ingredientes', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_ingredientes():
    if request.method == 'GET':
        ingredientes = Ingrediente.query.all()
        return jsonify([{
            "id": i.id, "nome": i.nome, "unidade": i.unidade,
            "estoque_atual": i.estoque_atual, "custo": i.custo_unitario
        } for i in ingredientes])

    data = request.get_json()
    if request.method == 'POST':
        if data.get('id'):
            ing = Ingrediente.query.get(data.get('id'))
            if ing:
                ing.nome = data.get('nome')
                ing.estoque_atual = float(data.get('estoque_atual', 0))
        else:
            new_ing = Ingrediente(nome=data.get('nome'), unidade=data.get('unidade'), 
                                  estoque_atual=float(data.get('estoque_atual', 0)))
            db.session.add(new_ing)
        db.session.commit()
        return jsonify({"success": True})

    if request.method == 'DELETE':
        ing = Ingrediente.query.get(data.get('id'))
        if ing:
            db.session.delete(ing)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Não encontrado"}), 404

# --- ROTAS DE PEDIDOS MOVIDAS ---

@admin_bp.route('/pedidos')
@login_required
def admin_pedidos():
    return render_template('admin_pedidos.html', title='Pedidos em Tempo Real')

@admin_bp.route('/')
@login_required
def admin_painel():
    return render_template('admin_cardapio.html', title='Cardápio — Admin Colonial')

@admin_bp.route('/banners')
@login_required
def admin_banners():
    return render_template('admin_banners.html', title='Banners — Admin Colonial')

@admin_bp.route('/cozinha')
@login_required
def monitor_cozinha():
    return render_template('monitor_cozinha.html')

@admin_bp.route('/api/pedidos')
@login_required
def get_pedidos():
    # Ordena pelos mais antigos primeiro (FIFO) para a cozinha
    pedidos = Pedido.query.filter(Pedido.status != 'concluido').order_by(Pedido.data_hora.asc()).all()
    
    result = []
    for p in pedidos:
        items = []
        for i in p.itens:
            items.append({
                "name": i.produto_nome,
                "qty": i.quantidade
            })
        
        meta = {}
        if p.metadata_json:
            try: meta = json.loads(p.metadata_json)
            except: pass

        result.append({
            "id": p.id,
            "timestamp": p.data_hora.strftime("%H:%M"),
            "customer": p.cliente_nome,
            "items": items,
            "obs": meta.get('obs', '')
        })
    return jsonify(result)

@admin_bp.route('/api/pedido/concluir', methods=['POST'])
@login_required
def concluir_pedido():
    data = request.get_json()
    pedido = Pedido.query.get(data.get('id'))
    if pedido:
        pedido.status = 'concluido'
        # Lógica de fidelidade SQL
        phone = ''.join(filter(str.isdigit, pedido.cliente_telefone or ''))
        if phone:
            fid = Fidelidade.query.filter_by(telefone=phone).first()
            pontos = int(pedido.total)
            if fid: fid.pontos += pontos
            else: db.session.add(Fidelidade(telefone=phone, pontos=pontos))
        
        db.session.commit()
        log_activity(f"Concluiu pedido #{pedido.id}")
        return jsonify({"success": True})
    return jsonify({"success": False}, 404)

@admin_bp.route('/historico/csv')
@login_required
def export_historico_csv():
    pedidos = Pedido.query.filter_by(status='concluido').all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['ID', 'Data', 'Cliente', 'Total'])
    for p in pedidos:
        writer.writerow([p.id, p.data_hora, p.cliente_nome, p.total])
    
    output.seek(0)
    return Response(output.getvalue().encode('utf-8-sig'), mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename=historico.csv"})