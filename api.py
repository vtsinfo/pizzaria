from flask import Blueprint, jsonify, request, session, current_app
from models import Fidelidade, db, Pedido, ItemPedido, Produto, FichaTecnica, Ingrediente, Categoria
from models import Fidelidade, db, Pedido, ItemPedido, Produto, FichaTecnica, Ingrediente, Categoria, Cupom, CupomUso
import re
import json
import os
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

def parse_price(price_str):
    if not price_str: return 0.0
    try:
        if isinstance(price_str, (int, float)): return float(price_str)
        clean = str(price_str).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return float(clean)
    except: return 0.0

@api_bp.route('/fidelidade/pontos', methods=['POST'])
def get_pontos():
    data = request.get_json()
    phone = ''.join(filter(str.isdigit, data.get('phone', '')))
    
    registro = Fidelidade.query.filter_by(telefone=phone).first()
    return jsonify({"pontos": registro.pontos if registro else 0})

@api_bp.route('/admin/fidelidade/update', methods=['POST'])
def update_pontos():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({"success": False}), 403
        
    data = request.get_json()
    phone = ''.join(filter(str.isdigit, data.get('phone', '')))
    pontos_adicionais = int(data.get('pontos', 0))
    
    registro = Fidelidade.query.filter_by(telefone=phone).first()
    if registro:
        registro.pontos += pontos_adicionais
    else:
        registro = Fidelidade(telefone=phone, pontos=pontos_adicionais)
        db.session.add(registro)
    
    try:
        db.session.commit()
        return jsonify({"success": True, "novo_total": registro.pontos})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/pedido/novo', methods=['POST'])
def novo_pedido():
    try:
        data = request.get_json()
        total_val = parse_price(data.get('total', '0'))
        
        if total_val <= 0:
            return jsonify({"success": False, "message": "Valor total inválido."}), 400

        # Validação de Estoque
        config_path = os.path.join(current_app.root_path, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                cfg = json.load(f)
                if cfg.get('inventory_enabled') and not cfg.get('allow_negative_stock'):
                    for item in data.get('items', []):
                        prod = Produto.query.filter_by(nome=item.get('name')).first()
                        if prod and prod.tipo == 'revenda' and prod.ingrediente_id:
                            ing = Ingrediente.query.get(prod.ingrediente_id)
                            if ing and ing.estoque_atual < 1:
                                return jsonify({"success": False, "message": f"Estoque insuficiente: {prod.nome}"}), 400

        # Lógica de Cupom (Server-Side Validation)
        cupom_codigo = data.get('coupon')
        desconto_val = 0.0
        cupom_id = None
        
        if cupom_codigo:
            cupom = Cupom.query.filter_by(codigo=cupom_codigo, ativo=True).first()
            if cupom:
                now = datetime.now()
                valido = True
                if cupom.validade_inicio and now < cupom.validade_inicio: valido = False
                if cupom.validade_fim and now > cupom.validade_fim: valido = False
                
                if valido:
                    cupom_id = cupom.id
                    if cupom.tipo == 'porcentagem':
                        desconto_val = (total_val * cupom.valor) / 100
                    else:
                        desconto_val = cupom.valor
                    
                    if desconto_val > total_val: desconto_val = total_val
                    total_val -= desconto_val

        meta = {
            "taxa_entrega": parse_price(data.get('fee', '0')),
            "coupon": cupom_codigo,
            "discount": desconto_val,
            "metodo_envio": data.get('method'),
            "obs": data.get('obs', '')
        }
        
        # Geração do Hash Seguro
        order_hash = str(uuid.uuid4())
        
        pedido = Pedido(
            data_hora=datetime.now(),
            cliente_nome=data.get('customer'),
            cliente_telefone=data.get('phone'),
            cliente_endereco=data.get('address'),
            status='novo',
            total=total_val, 
            metadata_json=json.dumps(meta),
            hash_id=order_hash
        )
        db.session.add(pedido)
        db.session.flush()
        
        # Registra Uso do Cupom
        if cupom_id and desconto_val > 0:
            uso = CupomUso(
                cupom_id=cupom_id,
                pedido_id=pedido.id,
                valor_desconto=desconto_val
            )
            db.session.add(uso)
        
        for item in data.get('items', []):
            prod = Produto.query.filter_by(nome=item.get('name')).first()
            item_obj = ItemPedido(
                pedido_id=pedido.id,
                produto_nome=item.get('name'),
                produto_id=prod.id if prod else None,
                quantidade=1,
                preco_unitario=parse_price(item.get('price'))
            )
            db.session.add(item_obj)
            
        db.session.commit()
        
        # Link Público para Validação
        order_link = url_for('public.ver_pedido', hash_id=pedido.hash_id, _external=True)
        
        return jsonify({"success": True, "order_id": pedido.id, "order_link": order_link})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/cardapio', methods=['GET'])
def api_cardapio():
    """Retorna o cardápio completo processando regras de estoque."""
    menu = {}
    CONFIG_FILE = os.path.join(current_app.root_path, 'config.json')
    try:
        categorias_db = Categoria.query.order_by(Categoria.ordem).all()
        
        inventory_enabled = False
        allow_negative = True
        if os.path.exists(CONFIG_FILE):
            try: 
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f: 
                     cfg = json.load(f)
                     inventory_enabled = cfg.get('inventory_enabled', False)
                     allow_negative = cfg.get('allow_negative_stock', True)
            except: pass

        for cat in categorias_db:
            if not cat.visivel: continue
            
            produtos_db = Produto.query.filter_by(categoria_id=cat.id).all()
            items_list = []

            for p in produtos_db:
                is_sold_out = p.esgotado
                should_display = True
                
                if inventory_enabled and not allow_negative:
                    if p.tipo == 'revenda' and p.ingrediente_id:
                         ing = Ingrediente.query.get(p.ingrediente_id)
                         if ing and ing.estoque_atual <= 0:
                             should_display = False
                    
                    elif p.tipo == 'fabricado':
                        receita = FichaTecnica.query.filter_by(produto_id=p.id).all()
                        for r in receita:
                            if r.ingrediente.estoque_atual <= 0:
                                is_sold_out = True
                                break
                
                if not should_display: continue

                items_list.append({
                    "id": p.id,
                    "nome": p.nome,
                    "desc": p.descricao,
                    "preco": f"R$ {(p.preco or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "foto": p.foto_url,
                    "visivel": p.visivel,
                    "esgotado": is_sold_out
                })
            
            if items_list:
                menu[cat.nome] = items_list
                
        return jsonify(menu)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/cupom/validar', methods=['POST'])
def validar_cupom():
    try:
        data = request.get_json()
        codigo = data.get('codigo', '').upper().strip()
        
        cupom = Cupom.query.filter_by(codigo=codigo, ativo=True).first()
        
        if cupom:
            now = datetime.now()
            # Validação de Data
            if cupom.validade_inicio and now < cupom.validade_inicio:
                return jsonify({"valid": False, "message": "Cupom ainda não está válido."})
            
            if cupom.validade_fim and now > cupom.validade_fim:
                return jsonify({"valid": False, "message": "Cupom expirado."})

            return jsonify({
                "valid": True, 
                "codigo": cupom.codigo, 
                "valor": cupom.valor, 
                "tipo": cupom.tipo, 
                "desc": cupom.descricao
            })
        
        return jsonify({"valid": False, "message": "Cupom inválido ou expirado."})
    except Exception as e:
        return jsonify({"valid": False, "message": "Erro ao processar cupom."}), 500