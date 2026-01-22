from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, Response, send_file, current_app
from models import Fidelidade, db, Pedido, ItemPedido, Ingrediente, FichaTecnica, Produto, User, Cupom, Banner, Reserva, Depoimento, Categoria
from functools import wraps
import os
import json
import csv
import io
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
        "quantidade": item.quantidade,
        "custo_unitario": item.ingrediente.custo_unitario,
        "custo_parcial": item.quantidade * (item.ingrediente.custo_unitario or 0)
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
    return render_template('admin_estoque.html', title='Gestão de Ingredientes')

@admin_bp.route('/produtos')
@login_required
def admin_produtos():
    return render_template('admin_produtos.html', title='Gestão de Produtos e Receitas')

@admin_bp.route('/api/cardapio')
@login_required
def api_admin_cardapio():
    # Retorna cardapio completo para o admin (sem filtro de estoque)
    try:
        menu = {}
        categorias_db = Categoria.query.order_by(Categoria.ordem).all()
        
        for cat in categorias_db:
            # Filtra produtos que são venáveis (fabricado, revenda, ou sem tipo)
            # Exclui apenas 'insumo' (matéria-prima pura)
            produtos_db = Produto.query.filter_by(categoria_id=cat.id).filter(
                (Produto.tipo != 'insumo')
            ).all()
            print(f"DEBUG: Category '{cat.nome}' (ID: {cat.id}) products found for recipes: {[f'{p.nome} (Tipo: {p.tipo})' for p in produtos_db]}")
            
            items_list = []
            for p in produtos_db:
                items_list.append({
                    "id": p.id,
                    "nome": p.nome
                })
            if items_list:
                menu[cat.nome] = items_list
        
        return jsonify(menu)
    except Exception as e:
        print(f"❌ ERRO API CARDAPIO: {e}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/ingredientes', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_ingredientes():
    if request.method == 'GET':
        try:
            ingredientes = Ingrediente.query.all()
            return jsonify([{
                "id": i.id,
                "nome": i.nome,
                "unidade": i.unidade,
                "estoque_atual": i.estoque_atual,
                "custo": i.custo_unitario,
                "tipo": getattr(i, 'tipo', 'insumo'),
                "estoque_minimo": getattr(i, 'estoque_minimo', 0),
                "fornecedor": getattr(i, 'fornecedor', ''),
                "validade": i.validade.strftime('%Y-%m-%d') if getattr(i, 'validade', None) else None
            } for i in ingredientes])
        except Exception as e:
            print(f"❌ ERRO API INGREDIENTES (GET): {e}")
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        try:
            data = request.get_json()
            if data.get('id'):
                ing = Ingrediente.query.get(data.get('id'))
                if ing:
                    ing.nome = data.get('nome')
                    ing.unidade = data.get('unidade')
                    ing.estoque_atual = float(data.get('estoque_atual', 0))
                    ing.custo_unitario = float(data.get('custo', 0))
                    if 'tipo' in data: ing.tipo = data.get('tipo')
                    if 'estoque_minimo' in data: ing.estoque_minimo = float(data.get('estoque_minimo', 0))
                    if 'fornecedor' in data and hasattr(ing, 'fornecedor'):
                        ing.fornecedor = data.get('fornecedor')
                    if 'validade' in data and hasattr(ing, 'validade'):
                        val = data.get('validade')
                        ing.validade = datetime.strptime(val, '%Y-%m-%d').date() if val else None
            else:
                val_date = None
                if data.get('validade'):
                    val_date = datetime.strptime(data.get('validade'), '%Y-%m-%d').date()
                    
                new_ing = Ingrediente(nome=data.get('nome'), unidade=data.get('unidade'),
                                      estoque_atual=float(data.get('estoque_atual', 0)),
                                      tipo=data.get('tipo', 'insumo'), custo_unitario=float(data.get('custo', 0)),
                                      estoque_minimo=float(data.get('estoque_minimo', 0)),
                                      fornecedor=data.get('fornecedor', ''), validade=val_date)
                db.session.add(new_ing)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO API INGREDIENTES (POST): {e}")
            return jsonify({"success": False, "message": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            ing = Ingrediente.query.get(data.get('id'))
            if ing:
                db.session.delete(ing)
                db.session.commit()
                return jsonify({"success": True})
            return jsonify({"success": False, "message": "Não encontrado"}), 404
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO API INGREDIENTES (DELETE): {e}")
            return jsonify({"success": False, "message": str(e)}), 500
            
    return jsonify({"success": False}), 400

@admin_bp.route('/api/ingredientes/import', methods=['POST'])
@login_required
def import_ingredientes_csv():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Nenhum arquivo selecionado"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        reader = csv.DictReader(stream, delimiter=';')
        
        count = 0
        for row in reader:
            # Limpeza de chaves e valores
            row = {k.strip(): v.strip() for k, v in row.items() if k}
            
            nome = row.get('Nome')
            if not nome: continue
            
            ing = Ingrediente.query.filter_by(nome=nome).first()
            
            def parse_float(val):
                if not val: return 0.0
                return float(val.replace('R$', '').replace('.', '').replace(',', '.').strip())

            if ing:
                if 'Tipo' in row: ing.tipo = row['Tipo']
                if 'Unidade' in row: ing.unidade = row['Unidade']
                if 'Estoque Atual' in row: ing.estoque_atual = parse_float(row['Estoque Atual'])
                if 'Fornecedor' in row: ing.fornecedor = row['Fornecedor']
                if 'Estoque Minimo' in row: ing.estoque_minimo = parse_float(row['Estoque Minimo'])
                if 'Custo Unitario' in row: ing.custo_unitario = parse_float(row['Custo Unitario'])
            else:
                new_ing = Ingrediente(
                    nome=nome,
                    tipo=row.get('Tipo', 'insumo'),
                    unidade=row.get('Unidade', 'un'),
                    estoque_atual=parse_float(row.get('Estoque Atual', '0')),
                    fornecedor=row.get('Fornecedor', ''),
                    estoque_minimo=parse_float(row.get('Estoque Minimo', '0')),
                    custo_unitario=parse_float(row.get('Custo Unitario', '0'))
                )
                db.session.add(new_ing)
            count += 1
            
        db.session.commit()
        log_activity(f"Importou {count} ingredientes via CSV")
        return jsonify({"success": True, "message": f"{count} ingredientes processados!"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao processar: {str(e)}"}), 500

@admin_bp.route('/api/ingrediente/<int:id>/historico', methods=['GET'])
@login_required
def api_ingrediente_historico(id):
    # Busca histórico de compras deste ingrediente para o gráfico
    historico = db.session.query(Compra.data_compra, ItemCompra.preco_unitario)\
        .join(ItemCompra)\
        .filter(ItemCompra.ingrediente_id == id)\
        .order_by(Compra.data_compra).all()
    
    return jsonify([{
        "data": h.data_compra.strftime('%d/%m/%Y'),
        "custo": h.preco_unitario
    } for h in historico])

@admin_bp.route('/estoque/baixo')
@login_required
def admin_estoque_baixo():
    ingredientes = Ingrediente.query.filter(Ingrediente.estoque_atual <= Ingrediente.estoque_minimo).all()
    return render_template('admin_estoque_baixo.html', title='Alerta de Estoque Baixo', ingredientes=ingredientes)

@admin_bp.route('/estoque/baixo/email', methods=['POST'])
@login_required
def email_estoque_baixo():
    ingredientes = Ingrediente.query.filter(Ingrediente.estoque_atual <= Ingrediente.estoque_minimo).all()
    
    if not ingredientes:
        return jsonify({"success": False, "message": "Sem itens com estoque baixo para enviar."})

    # Configurações de E-mail (Busca variáveis de ambiente ou usa placeholders)
    # Para funcionar, defina SMTP_USER e SMTP_PASS no seu ambiente ou .env
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASS = os.environ.get('SMTP_PASS')
    RECIPIENT = os.environ.get('RECIPIENT_EMAIL', SMTP_USER) # Envia para si mesmo se não definido

    if not SMTP_USER or not SMTP_PASS:
        return jsonify({"success": False, "message": "Configuração de e-mail não encontrada (SMTP_USER/PASS)."}), 500

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = RECIPIENT
        msg['Subject'] = f"Alerta de Estoque Baixo - {datetime.now().strftime('%d/%m/%Y')}"

        html_body = """
        <h2 style="color: #d9534f;">Relatório de Estoque Baixo</h2>
        <p>Os seguintes itens estão abaixo do nível mínimo:</p>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; border-color: #ddd;">
            <tr style="background-color: #f2f2f2;"><th>Item</th><th>Atual</th><th>Mínimo</th><th>Status</th></tr>
        """
        
        for item in ingredientes:
            status_color = "red" if item.estoque_atual <= 0 else "orange"
            status_text = "ZERADO" if item.estoque_atual <= 0 else "BAIXO"
            html_body += f"""<tr><td>{item.nome}</td><td>{item.estoque_atual} {item.unidade}</td><td>{item.estoque_minimo} {item.unidade}</td><td style="color: {status_color}; font-weight: bold;">{status_text}</td></tr>"""
        
        html_body += "</table>"
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()

        log_activity("Enviou relatório de estoque baixo por e-mail")
        return jsonify({"success": True, "message": f"E-mail enviado para {RECIPIENT}!"})

    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao enviar: {str(e)}"}), 500

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

@admin_bp.route('/api/banners', methods=['GET', 'POST'])
@login_required
def api_admin_banners():
    if request.method == 'GET':
        banners = Banner.query.order_by(Banner.ordem).all()
        return jsonify([{
            "id": b.id,
            "title": b.titulo,
            "subtitle": b.descricao,
            "link_text": b.link_text,
            "link_url": b.link_url,
            "image_url": b.imagem_url,
            "ordem": b.ordem
        } for b in banners])
        
    # POST
    try:
        data = request.form
        file = request.files.get('file')
        
        # Se for atualização de ordem (JSON array) - Frontend antigo pode usar isso
        # Mas admin_banners.html usa FormData para criar e DELETE para remover.
        # Se precisar de reordenar, teria que ver o codigo.
        # Por enquanto vamos focar no Create.
        
        # Mas espere, o código antigo do dashbord.html enviava JSON para reordenar?
        # Sim: await fetch('/api/admin/banners', { method: 'POST', body: JSON.stringify(banners) });
        # Então preciso suportar ambos: JSON (lista) e FormData (criação).
        
        if request.is_json: 
            # Reordenação / Atualização em massa
            items = request.get_json()
            if isinstance(items, list):
                for idx, item in enumerate(items):
                    b = Banner.query.get(item['id'])
                    if b:
                        b.ordem = idx
                db.session.commit()
                return jsonify({"success": True})

        # Criação Unitária (FormData)
        titulo = data.get('title')
        descricao = data.get('subtitle')
        link_text = data.get('link_text')
        link_url = data.get('link_url')
        
        if file:
            filename = f"banner_{int(datetime.now().timestamp())}_{file.filename}"
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'banners')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file.save(os.path.join(upload_folder, filename))
            image_url = url_for('static', filename=f'uploads/banners/{filename}')
            
            new_banner = Banner(
                titulo=titulo,
                descricao=descricao,
                link_text=link_text,
                link_url=link_url,
                imagem_url=image_url
            )
            db.session.add(new_banner)
            db.session.commit()
            return jsonify({"success": True})
            
        return jsonify({"success": False, "message": "Imagem obrigatória"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/api/admin/banners/<int:id>', methods=['DELETE'])
@login_required
def delete_banner(id):
    try:
        banner = Banner.query.get(id)
        if banner:
            # Opcional: deletar arquivo físico
            db.session.delete(banner)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Banner não encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/reservas')
@login_required
def admin_reservas():
    return render_template('admin_reservas.html', title='Gestão de Reservas')

@admin_bp.route('/cupons')
@login_required
def admin_cupons():
    return render_template('admin_cupons.html', title='Cupons de Desconto')

@admin_bp.route('/promocoes')
@login_required
def admin_promocoes():
    return render_template('admin_promocoes.html', title='Promoções')

@admin_bp.route('/depoimentos')
@login_required
def admin_depoimentos():
    return render_template('admin_depoimentos.html', title='Depoimentos')

@admin_bp.route('/usuarios')
@login_required
def admin_usuarios():
    return render_template('admin_usuarios.html', title='Gestão de Usuários')

@admin_bp.route('/cozinha')
@login_required
def monitor_cozinha():
    return render_template('cozinha.html')


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

@admin_bp.route('/api/admin/categoria/update', methods=['POST'])
@login_required
def api_update_categoria():
    data = request.get_json()
    cat_name = data.get('original_name') or data.get('name')
    
    if not cat_name:
        return jsonify({"success": False, "message": "Nome da categoria obrigatório"}), 400
        
    categoria = Categoria.query.filter_by(nome=cat_name).first()
    if not categoria:
        return jsonify({"success": False, "message": "Categoria não encontrada"}), 404
        
    if 'foto_url' in data:
        categoria.foto_url = data['foto_url']
        
    # Se houver mudança de nome, verificar duplicidade e atualizar
    new_name = data.get('new_name')
    if new_name and new_name != cat_name:
        if Categoria.query.filter_by(nome=new_name).first():
            return jsonify({"success": False, "message": "Já existe categoria com este nome"}), 400
        categoria.nome = new_name
        
    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/api/config/cardapio', methods=['GET', 'POST'])
@login_required
def api_config_cardapio():
    if request.method == 'GET':
        categorias = Categoria.query.all()
        config = {}
        for cat in categorias:
            config[cat.nome] = {
                "visible": cat.visivel,
                "show_price": cat.exibir_preco
            }
        return jsonify(config)
        
    try:
        data = request.get_json()
        for cat_nome, cfg in data.items():
            cat = Categoria.query.filter_by(nome=cat_nome).first()
            if cat:
                cat.visivel = cfg.get('visible', True)
                cat.exibir_preco = cfg.get('show_price', True)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/config', methods=['GET', 'POST'])
@login_required
def admin_config():
    config_path = os.path.join(current_app.root_path, 'config.json')
    if request.method == 'POST':
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            config['inventory_enabled'] = 'inventory_enabled' in request.form
            config['allow_negative_stock'] = 'allow_negative_stock' in request.form
            config['ai_enabled'] = 'ai_enabled' in request.form
            
            config['tempo_espera'] = request.form.get('tempo_espera', '')
            config['telefone'] = request.form.get('telefone', '')
            config['whatsapp'] = request.form.get('whatsapp', '')
            config['endereco_principal'] = request.form.get('endereco_principal', '')
            config['tipo_forno'] = request.form.get('tipo_forno', '')
            config['cor_primaria'] = request.form.get('cor_primaria', '#ffc107')
            config['sobre_nos'] = request.form.get('sobre_nos', '')
            
            config['self_service_enabled'] = 'self_service_enabled' in request.form
            config['rodizio_pizza_enabled'] = 'rodizio_pizza_enabled' in request.form
            config['rodizio_carne_enabled'] = 'rodizio_carne_enabled' in request.form

            if 'logo' in request.files:
                file = request.files['logo']
                if file and file.filename != '':
                    filename = f"logo_{int(datetime.now().timestamp())}_{file.filename}"
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    file.save(os.path.join(upload_folder, filename))
                    config['logo_url'] = url_for('static', filename=f'uploads/{filename}')

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
            categorias = Categoria.query.all()
            for cat in categorias:
                cat.visivel = f'cat_visible_{cat.id}' in request.form
                cat.exibir_preco = f'cat_price_{cat.id}' in request.form
            
            db.session.commit()

            flash('Configurações salvas com sucesso!', 'success')
            return redirect(url_for('admin.admin_config'))
            
        except Exception as e:
            flash(f'Erro ao salvar configurações: {str(e)}', 'danger')
            return redirect(url_for('admin.admin_config'))

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
        
    categorias = Categoria.query.order_by(Categoria.ordem).all()
    return render_template('admin_config.html', config=config, categorias=categorias)

# --- FORNECEDORES (CRUD) ---
@admin_bp.route('/api/fornecedores', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_fornecedores():
    if request.method == 'GET':
        forn = Fornecedor.query.order_by(Fornecedor.nome_empresa).all()
        return jsonify([{
            "id": f.id,
            "nome_empresa": f.nome_empresa,
            "cnpj": f.cnpj,
            "contato_nome": f.contato_nome,
            "telefone": f.telefone,
            "email": f.email
        } for f in forn])
        
    data = request.get_json()
    
    if request.method == 'DELETE':
        try:
            f = Fornecedor.query.get(data.get('id'))
            if f:
                db.session.delete(f)
                db.session.commit()
                return jsonify({"success": True})
            return jsonify({"success": False, "message": "Fornecedor não encontrado"}), 404
        except Exception as e:
             return jsonify({"success": False, "message": str(e)}), 500

    # POST (Create/Update)
    try:
        if data.get('id'):
            f = Fornecedor.query.get(data.get('id'))
            if f:
                f.nome_empresa = data.get('nome_empresa')
                f.cnpj = data.get('cnpj')
                f.contato_nome = data.get('contato_nome')
                f.telefone = data.get('telefone')
                f.email = data.get('email')
        else:
            new_f = Fornecedor(
                nome_empresa=data.get('nome_empresa'),
                cnpj=data.get('cnpj'),
                contato_nome=data.get('contato_nome'),
                telefone=data.get('telefone'),
                email=data.get('email')
            )
            db.session.add(new_f)
            
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- COMPRAS E ENTRADA DE NOTA ---
@admin_bp.route('/api/compras', methods=['GET', 'POST'])
@login_required
def api_compras():
    if request.method == 'GET':
        compras = Compra.query.order_by(Compra.data_compra.desc()).all()
        return jsonify([{
            "id": c.id,
            "data": c.data_compra.strftime('%d/%m/%Y'),
            "fornecedor": c.fornecedor.nome_empresa if c.fornecedor else "N/A",
            "nota_fiscal": c.nota_fiscal or "-",
            "total": c.total,
            "observacao": c.observacao,
            "itens": [{
                "ingrediente": i.ingrediente.nome,
                "qtd": i.quantidade,
                "un": i.ingrediente.unidade,
                "preco": i.preco_unitario,
                "subtotal": i.subtotal
            } for i in c.itens]
        } for c in compras])
        
    # POST - Nova Compra e Atualização de Estoque
    data = request.get_json()
    try:
        # 1. Cria a Compra
        compra = Compra(
            fornecedor_id=data.get('fornecedor_id'),
            data_compra=datetime.strptime(data.get('data'), '%Y-%m-%d') if data.get('data') else datetime.now(),
            nota_fiscal=data.get('nota_fiscal'),
            total=float(data.get('total', 0)),
            observacao=data.get('observacao')
        )
        db.session.add(compra)
        db.session.flush() # Para ter o ID da compra
        
        # 2. Adiciona Itens e Atualiza Estoque
        itens = data.get('itens', [])
        for item in itens:
            ing_id = item.get('ingrediente_id')
            qtd = float(item.get('quantidade', 0))
            preco = float(item.get('preco_unitario', 0))
            subtotal = float(item.get('subtotal', 0))
            
            # Salva item da compra
            novo_item = ItemCompra(
                compra_id=compra.id,
                ingrediente_id=ing_id,
                quantidade=qtd,
                preco_unitario=preco,
                subtotal=subtotal
            )
            db.session.add(novo_item)
            
            # ATUALIZA O ESTOQUE E CUSTO (Lógica de Último Preço)
            ingrediente = Ingrediente.query.get(ing_id)
            if ingrediente:
                ingrediente.estoque_atual += qtd
                if preco > 0:
                    ingrediente.custo_unitario = preco
                
                # Se veio fornecedor na compra e o ingrediente não tem fonecedor fixo, atualiza (opcional)
                if not ingrediente.fornecedor and compra.fornecedor:
                    ingrediente.fornecedor = compra.fornecedor.nome_empresa
                    
        db.session.commit()
        return jsonify({"success": True, "message": "Compra registrada e estoque atualizado!"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/admin/fornecedores')
@login_required
def admin_fornecedores():
    return render_template('admin_fornecedores.html', title='Gestão de Fornecedores')

@admin_bp.route('/admin/compras')
@login_required
def admin_compras():
    return render_template('admin_compras.html', title='Histórico de Compras')

@admin_bp.route('/admin/compras/nova')
@login_required
def admin_nova_compra():
    return render_template('admin_nova_compra.html', title='Nova Compra')

