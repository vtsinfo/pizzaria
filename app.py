from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session, Response, send_file
import os
import json
import csv
import io
import shutil
import functools
import hashlib
import re
from datetime import datetime
from collections import Counter
from flask_sqlalchemy import SQLAlchemy     # Novo
from database import db, init_db   # Novo
from models import User, Categoria, Produto, Pedido, ItemPedido, Ingrediente, FichaTecnica, Reserva, Depoimento # Novo

# --- API DE ESTOQUE (FASE 2) ---



app = Flask(__name__)
app.secret_key = 'vts_pizzaria_secret_key'

# --- CONFIGURAÇÃO BANCO DE DADOS (NOVO) ---
# BASE_DIR será a raiz do projeto (c:\vts-site-python)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(INSTANCE_DIR, 'pizzaria.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o Banco
init_db(app)

# --- API DE ESTOQUE (FASE 2) ---

@app.route('/api/admin/ingredientes', methods=['GET', 'POST', 'DELETE'])
def api_ingredientes():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401

    if request.method == 'GET':
        ingredientes = Ingrediente.query.all()
        return jsonify([{
            "id": i.id,
            "nome": i.nome,
            "unidade": i.unidade,
            "tipo": i.tipo,
            "estoque_atual": i.estoque_atual,
            "estoque_minimo": i.estoque_minimo,
            "custo": i.custo_unitario
        } for i in ingredientes])

    if request.method == 'POST':
        data = request.get_json()
        
        # Se tem ID, edita. Se não, cria.
        if data.get('id'):
            ing = Ingrediente.query.get(data.get('id'))
            if ing:
                ing.nome = data.get('nome')
                ing.unidade = data.get('unidade')
                ing.tipo = data.get('tipo', 'insumo')
                ing.estoque_atual = float(data.get('estoque_atual', 0))
                ing.estoque_minimo = float(data.get('estoque_minimo', 0))
                ing.custo_unitario = float(data.get('custo', 0))
        else:
            new_ing = Ingrediente(
                nome=data.get('nome'),
                unidade=data.get('unidade'),
                tipo=data.get('tipo', 'insumo'),
                estoque_atual=float(data.get('estoque_atual', 0)),
                estoque_minimo=float(data.get('estoque_minimo', 0)),
                custo_unitario=float(data.get('custo', 0))
            )
            db.session.add(new_ing)
        
        try:
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    if request.method == 'DELETE':
        data = request.get_json()
        ing = Ingrediente.query.get(data.get('id'))
        if ing:
            db.session.delete(ing)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Ingrediente não encontrado"}), 404

@app.route('/api/admin/estoque/baixo', methods=['GET'])
def api_estoque_baixo():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401

    # Busca ingredientes com estoque abaixo ou igual ao mínimo
    ingredientes = Ingrediente.query.filter(Ingrediente.estoque_atual <= Ingrediente.estoque_minimo).all()
    
    return jsonify([{
        "id": i.id,
        "nome": i.nome,
        "unidade": i.unidade,
        "estoque_atual": i.estoque_atual,
        "estoque_minimo": i.estoque_minimo,
        "tipo": i.tipo
    } for i in ingredientes])

@app.route('/api/admin/receita/<int:produto_id>', methods=['GET'])
def get_receita(produto_id):
    if not session.get('logged_in'):
        return jsonify([]), 401
    
    # Retorna ingredientes vinculados a este produto
    receita = FichaTecnica.query.filter_by(produto_id=produto_id).all()
    return jsonify([{
        "id": item.id,
        "ingrediente_id": item.ingrediente_id,
        "nome_ingrediente": item.ingrediente.nome,
        "unidade": item.ingrediente.unidade,
        "quantidade": item.quantidade
    } for item in receita])

@app.route('/api/admin/receita', methods=['POST'])
def save_receita():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    try:
        produto_id = int(data.get('produto_id'))
        ingrediente_id = int(data.get('ingrediente_id'))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "IDs inválidos"}), 400
        
    quantidade = float(data.get('quantidade', 0))
    action = data.get('action') # 'add' or 'remove'
    
    if action == 'add':
        # Verifica se já existe
        item = FichaTecnica.query.filter_by(produto_id=produto_id, ingrediente_id=ingrediente_id).first()
        if item:
            item.quantidade = quantidade # Atualiza
        else:
            new_item = FichaTecnica(produto_id=produto_id, ingrediente_id=ingrediente_id, quantidade=quantidade)
            db.session.add(new_item)
            
    elif action == 'remove':
        item = FichaTecnica.query.filter_by(produto_id=produto_id, ingrediente_id=ingrediente_id).first()
        if item:
            db.session.delete(item)
            
    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Caminhos Legados (Mantidos por enquanto para fallback se necessário, mas o objetivo é remover)
CARDAPIO_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'cardapio_config.json')
CARDAPIO_FILE = os.path.join(os.path.dirname(__file__), 'cardapio.json')
ORDERS_FILE = os.path.join(os.path.dirname(__file__), 'pedidos.json')
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'pedidos_historico.json')
COUPONS_FILE = os.path.join(os.path.dirname(__file__), 'cupons.json')
BACKUP_FILE = os.path.join(os.path.dirname(__file__), 'cardapio_backup.json')
USERS_FILE = os.path.join(os.path.dirname(__file__), 'usuarios.json')
LOGS_FILE = os.path.join(os.path.dirname(__file__), 'logs.json')
PROMOS_FILE = os.path.join(os.path.dirname(__file__), 'promocoes.json')
LOYALTY_FILE = os.path.join(os.path.dirname(__file__), 'fidelidade.json')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
BANNERS_FILE = os.path.join(os.path.dirname(__file__), 'banners.json')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

@app.route('/')
def index():
    banners = []
    if os.path.exists(BANNERS_FILE):
        with open(BANNERS_FILE, 'r', encoding='utf-8') as f:
            banners = json.load(f)
            
    # Busca depoimentos aprovados (limitado a 3 mais recentes)
    depoimentos = Depoimento.query.filter_by(aprovado=True).order_by(Depoimento.data.desc()).limit(3).all()
    
    return render_template('index.html', title='Pizzaria Colonial — Pizzas, Churrasco e Lanches', banners=banners, depoimentos=depoimentos)

@app.route('/cardapio')
def cardapio():
    # NOVO: Carrega do Banco de Dados
    categorias_db = Categoria.query.filter_by(visivel=True).order_by(Categoria.ordem).all()
    
    menu = {}
    config = {}
    
    for cat in categorias_db:
        # Carrega produtos visíveis
        produtos_db = Produto.query.filter_by(categoria_id=cat.id, visivel=True).all()
        
        items_list = []
        for p in produtos_db:
            items_list.append({
                "id": p.id,
                "nome": p.nome,
                "desc": p.descricao,
                "preco": f"R$ {p.preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), # Formata R$ 1.200,50
                "foto": p.foto_url,
                "visivel": p.visivel
            })
        
        if items_list:
            menu[cat.nome] = items_list
            config[cat.nome] = {
                "visible": True, 
                "show_price": cat.exibir_preco
            }
            
    return render_template('cardapio.html', title='Nosso Cardápio — Pizzaria Colonial', menu=menu, config=config)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html', title='Sobre Nós — Pizzaria Colonial')

@app.route('/api/depoimento/novo', methods=['POST'])
def novo_depoimento():
    try:
        data = request.get_json()
        depoimento = Depoimento(
            nome=data.get('nome'),
            texto=data.get('texto'),
            nota=int(data.get('nota', 5))
        )
        db.session.add(depoimento)
        db.session.commit()
        return jsonify({"success": True, "message": "Obrigado! Seu depoimento foi enviado para aprovação."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/reservas', methods=['GET', 'POST'])
def reservas():
    if request.method == 'POST':
        try:
            # Captura dados do formulário
            nova_reserva = Reserva(
                nome_cliente=request.form.get('nome'),
                telefone=request.form.get('telefone'),
                data_reserva=datetime.strptime(request.form.get('data'), '%Y-%m-%d').date(),
                hora_reserva=datetime.strptime(request.form.get('hora'), '%H:%M').time(),
                num_pessoas=int(request.form.get('pessoas')),
                observacao=request.form.get('obs'),
                status='Pendente'
            )
            db.session.add(nova_reserva)
            db.session.commit()
            flash('Sua solicitação de reserva foi enviada com sucesso! Entraremos em contato para confirmar.', 'success')
            return redirect(url_for('reservas'))
        except Exception as e:
            flash(f'Erro ao processar reserva: {str(e)}', 'danger')
            
    return render_template('reservas.html', title='Reservas — Pizzaria Colonial')

@app.route('/unidades')
def unidades():
    return render_template('unidades.html', title='Nossas Unidades')

# --- Context Processor (Injeta dados em todos os templates) ---
@app.context_processor
def inject_site_config():
    default_config = {
        "nome_fantasia": "Pizzaria Colonial",
        "telefone": "(11) 91456-9028",
        "whatsapp": "5511914569028",
        "endereco_principal": "Rua Virgínia Ferni, 1758 - Itaquera, SP",
        "tempo_espera": "40-50 min",
        "logo_url": "", 
        "cor_primaria": "#ffc107", 
        "ai_enabled": True,
        "theme": "dark", # Novo padrão: Escuro
        "instagram": "",
        "facebook": "",
        "online_ordering_enabled": False,
        "manual_payment_confirm": True,
        "sobre_nos": "A Pizzaria Colonial nasceu do sonho de trazer o verdadeiro sabor da pizza artesanal para a nossa região. Desde a nossa fundação, trabalhamos com ingredientes selecionados e muito carinho em cada receita.\n\nNossa missão é proporcionar momentos felizes e saborosos para você e sua família."
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
            default_config.update(saved_config)
    return dict(site_config=default_config)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/api/cardapio')
def api_cardapio():
    # NOVO: API via Banco de Dados
    menu = {}
    try:
        categorias_db = Categoria.query.order_by(Categoria.ordem).all()
        
        # Carrega promoções (ainda via JSON por enquanto ou migra depois)
        # Por simplificação, mantemos a lógica de promoção separada ou desativada neste refactor inicial
        # Idealmente, Promocoes virariam tabela.
        
        for cat in categorias_db:
            produtos_db = Produto.query.filter_by(categoria_id=cat.id).all()
            items_list = []
            for p in produtos_db:
                items_list.append({
                    "id": p.id,
                    "nome": p.nome,
                    "desc": p.descricao,
                    "preco": f"R$ {p.preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "foto": p.foto_url,
                    "visivel": p.visivel
                })
            
            if items_list:
                menu[cat.nome] = items_list
                
        return jsonify(menu)
    except Exception as e:
        print(f"Erro na API Cardapio SQL: {e}")
        return jsonify({})

# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    # Cria usuário padrão (admin/pizza123) se banco estiver vazio
    if User.query.count() == 0:
        default_pass = hashlib.sha256("pizza123".encode()).hexdigest()
        admin = User(username="admin", password_hash=default_pass, role="admin", permissions='["all"]')
        db.session.add(admin)
        db.session.commit()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Busca usuário no banco
        user = User.query.filter_by(username=username).first()
        
        if user:
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            # Verifica senha
            if user.password_hash == input_hash:
                session['logged_in'] = True
                session['username'] = user.username
                session['role'] = user.role
                try:
                    session['permissions'] = json.loads(user.permissions)
                except:
                    session['permissions'] = []
                
                log_activity(f"Login realizado com sucesso: {username}")
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Usuário ou senha incorretos.'
        else:
            error = 'Usuário ou senha incorretos.'
            
    return render_template('login.html', title='Login — Pizzaria Colonial', error=error)

# Rota de Logout
@app.route('/logout')
def logout():
    if session.get('logged_in'):
        log_activity("Logout realizado")
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# --- Helpers ---
def log_activity(action):
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
    
    logs.insert(0, entry) # Mais recente primeiro
    # Mantém apenas os últimos 1000 logs
    logs = logs[:1000]
    
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)

def check_permission(perm):
    user_perms = session.get('permissions', [])
    if 'all' in user_perms: return True
    return perm in user_perms

# Rota para o Monitor de Cozinha (KDS)
@app.route('/cozinha')
def cozinha_monitor():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('cozinha.html')

# Rota para a interface administrativa
@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if not check_permission('manage_menu'):
        return """
        <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h1>🚫 Acesso Negado</h1>
            <p>Você não tem permissão para acessar esta página ou sua sessão expirou.</p>
            <a href="/logout" style="background: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Sair e Tentar Novamente</a>
        </div>
        """, 403
        
    return render_template('admin_cardapio.html', title='Cardápio — Admin Colonial')

@app.route('/admin/pedidos')
def admin_pedidos():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin_pedidos.html', title='Pedidos em Tempo Real — Pizzaria Colonial')

@app.route('/admin/reservas')
def admin_reservas():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin_reservas.html', title='Gestão de Reservas — Admin Colonial')

@app.route('/admin/cupons')
def admin_cupons():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin_cupons.html', title='Cupons — Admin Colonial')

@app.route('/admin/usuarios')
def admin_usuarios():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        return "Acesso restrito a administradores", 403
    return render_template('admin_usuarios.html', title='Usuários — Admin Colonial')

@app.route('/admin/promocoes')
def admin_promocoes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin_promocoes.html', title='Promoções — Admin Colonial')

@app.route('/admin/depoimentos')
def admin_depoimentos():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin_depoimentos.html', title='Moderação de Depoimentos — Admin Colonial')

@app.route('/admin/logs')
def admin_logs():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    logs = []
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            
    return render_template('admin_logs.html', title='Logs de Atividade — Admin Colonial', logs=logs)

@app.route('/api/admin/cupons', methods=['GET'])
def api_admin_cupons():
    if not session.get('logged_in'):
        return jsonify({}), 401
    if os.path.exists(COUPONS_FILE):
        with open(COUPONS_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify({})

@app.route('/api/admin/cupons/save', methods=['POST'])
def api_admin_save_cupons():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    try:
        data = request.get_json()
        with open(COUPONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        log_activity("Atualizou lista de cupons")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Rota para Gerar PDF do Cardápio
@app.route('/api/cardapio/pdf')
def cardapio_pdf():
    try:
        from fpdf import FPDF
    except ImportError:
        return "Biblioteca FPDF não instalada. Instale com 'pip install fpdf'", 500

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'Cardápio - Pizzaria Colonial', 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        if os.path.exists(CARDAPIO_FILE):
            with open(CARDAPIO_FILE, 'r', encoding='utf-8') as f:
                menu = json.load(f)
                
            for category, items in menu.items():
                # Título da Categoria
                pdf.set_font("Arial", 'B', 14)
                pdf.set_fill_color(240, 240, 240)
                # Decodifica para latin-1 para compatibilidade do FPDF padrão
                cat_text = category.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 10, cat_text, 1, 1, 'L', 1)
                
                # Itens
                pdf.set_font("Arial", size=11)
                for item in items:
                    name = item['nome'].encode('latin-1', 'replace').decode('latin-1')
                    price = item['preco'].encode('latin-1', 'replace').decode('latin-1')
                    desc = item['desc'].encode('latin-1', 'replace').decode('latin-1')
                    
                    pdf.cell(140, 8, name, 0, 0)
                    pdf.cell(50, 8, price, 0, 1, 'R')
                    pdf.set_font("Arial", 'I', 9)
                    pdf.multi_cell(0, 5, desc)
                    pdf.set_font("Arial", size=11)
                    pdf.ln(2)
                pdf.ln(5)

        # Salva em memória ou arquivo temporário
        pdf_output = os.path.join(os.path.dirname(__file__), 'cardapio_temp.pdf')
        pdf.output(pdf_output)
        
        return send_file(pdf_output, as_attachment=True, download_name='cardapio_colonial.pdf')
    except Exception as e:
        return f"Erro ao gerar PDF: {str(e)}", 500

def parse_price(price_str):
    if not price_str: return 0.0
    try:
        if isinstance(price_str, (int, float)): return float(price_str)
        clean = str(price_str).replace('R$', '').replace('.', '').replace(',', '.').strip()
        clean = clean.replace('\xa0', '') 
        return float(clean)
    except:
        return 0.0

# Rota para salvar alterações (POST)
@app.route('/api/admin/save', methods=['POST'])
def save_cardapio():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 401
    try:
        data = request.get_json() # Formato: { "Categoria": [ {itens...} ] }
        
        # Rastreamento para identificar exclusões (Simples não deleta categorias por enquanto para segurança)
        # processed_cats = [] 
        
        cat_order = 0
        for cat_name, items in data.items():
            cat_order += 1
            
            # Busca ou Cria Categoria
            cat = Categoria.query.filter_by(nome=cat_name).first()
            if not cat:
                cat = Categoria(nome=cat_name, ordem=cat_order)
                db.session.add(cat)
                db.session.flush() # ID
            else:
                cat.ordem = cat_order
            
            # Processa Itens
            # processed_items = []
            
            for item in items:
                p_id = item.get('id')
                # Se item tem ID, tenta buscar. Se não, tenta buscar por nome e categoria (fallback)
                prod = None
                if p_id:
                    prod = Produto.query.get(p_id)
                
                # Fallback por nome se ID não bater ou não existir (casos de cardápios antigos cacheados)
                if not prod and item.get('nome'):
                     prod = Produto.query.filter_by(categoria_id=cat.id, nome=item['nome']).first()

                if prod:
                    # Atualiza
                    prod.nome = item.get('nome')
                    prod.descricao = item.get('desc')
                    prod.preco = parse_price(item.get('preco'))
                    prod.foto_url = item.get('foto')
                    prod.visivel = item.get('visivel', True)
                    prod.esgotado = item.get('esgotado', False)
                    prod.categoria_id = cat.id # Garante que está na cat certa (caso tenha movido)
                else:
                    # Cria Novo
                    prod = Produto(
                        categoria_id=cat.id,
                        nome=item.get('nome'),
                        descricao=item.get('desc'),
                        preco=parse_price(item.get('preco')),
                        foto_url=item.get('foto'),
                        visivel=item.get('visivel', True),
                        esgotado=item.get('esgotado', False)
                    )
                    db.session.add(prod)
            
            # TODO: Lógica de exclusão de itens removidos no front (comparar IDs)
            # Para V1, itens removidos no front não são deletados no banco explicitamente aqui
            # para evitar acidentes, mas idealmente deveriam.
            # Se o usuário deletou no front, o item não vem no JSON.
            
        db.session.commit()
        log_activity("Salvou alterações no cardápio (SQL)")
        return jsonify({"success": True, "message": "Cardápio atualizado com sucesso!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/config/cardapio', methods=['GET', 'POST'])
def api_cardapio_config():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
        
    if request.method == 'GET':
        # Retorna config do banco
        cats = Categoria.query.all()
        config = {}
        for c in cats:
            config[c.nome] = {"visible": c.visivel, "show_price": c.exibir_preco}
        return jsonify(config)
        
    if request.method == 'POST':
        try:
            data = request.get_json()
            for cat_name, cfg in data.items():
                cat = Categoria.query.filter_by(nome=cat_name).first()
                if cat:
                    cat.visivel = cfg.get('visible', True)
                    cat.exibir_preco = cfg.get('show_price', True)
            
            db.session.commit()
            log_activity("Atualizou configurações de visibilidade (SQL)")
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

# Rota para baixar modelo CSV
@app.route('/admin/cardapio/template')
def download_template():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Cria CSV em memória
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Categoria', 'Nome', 'Descricao', 'Preco', 'Foto'])
    writer.writerow(['Pizzas Salgadas', 'Mussarela', 'Molho, mussarela e orégano', 'R$ 48,99', 'https://exemplo.com/foto.jpg'])
    
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'), # BOM para compatibilidade com Excel
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=modelo_cardapio.csv"}
    )

# Rota para upload de CSV
@app.route('/api/admin/cardapio/upload', methods=['POST'])
def upload_cardapio():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "Não autorizado"}), 401
        
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Nenhum arquivo selecionado"}), 400

    mode = request.form.get('mode', 'merge') # 'merge' ou 'replace'

    try:
        # Cria backup automático antes de qualquer alteração
        if os.path.exists(CARDAPIO_FILE):
            shutil.copy2(CARDAPIO_FILE, BACKUP_FILE)

        # Lê e decodifica o arquivo
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        reader = csv.DictReader(stream, delimiter=';')
        
        # Carrega menu atual
        current_menu = {}
        if mode == 'merge' and os.path.exists(CARDAPIO_FILE):
            with open(CARDAPIO_FILE, 'r', encoding='utf-8') as f:
                current_menu = json.load(f)
        
        # Processa linhas
        for row in reader:
            category = row.get('Categoria', '').strip()
            name = row.get('Nome', '').strip()
            desc = row.get('Descricao', '').strip()
            price = row.get('Preco', '').strip()
            photo = row.get('Foto', '').strip()
            
            if not category or not name:
                continue
                
            if category not in current_menu:
                current_menu[category] = []
            
            # Verifica se item já existe para atualizar
            found = False
            for item in current_menu[category]:
                if item['nome'].lower() == name.lower():
                    item['desc'] = desc
                    item['preco'] = price
                    if photo: item['foto'] = photo
                    found = True
                    break
            
            # Se não existe, cria novo
            if not found:
                new_item = {"nome": name, "desc": desc, "preco": price}
                if photo: new_item['foto'] = photo
                current_menu[category].append(new_item)
        
        # Salva alterações
        with open(CARDAPIO_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_menu, f, indent=4, ensure_ascii=False)
        
        log_activity(f"Importou cardápio via CSV (Modo: {mode})")
            
        return jsonify({"success": True, "message": "Cardápio atualizado com sucesso!"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao processar arquivo: {str(e)}"}), 500

# Rota para Upload de Imagens do Cardápio
@app.route('/api/admin/upload/image', methods=['POST'])
def upload_image():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False}), 400
        
    # Validação de extensão segura
    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "message": "Tipo de arquivo não permitido"}), 400

    # Sanitização básica do nome do arquivo
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', file.filename)
    filename = f"{int(datetime.now().timestamp())}_{safe_filename}"
    
    try:
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return jsonify({"success": True, "url": url_for('static', filename=f'uploads/{filename}')})
    except Exception as e:
        return jsonify({"success": False, "message": "Erro ao salvar arquivo"}), 500

# Rota para restaurar backup
@app.route('/api/admin/cardapio/restore', methods=['POST'])
def restore_cardapio():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "Não autorizado"}), 401
        
    if os.path.exists(BACKUP_FILE):
        shutil.copy2(BACKUP_FILE, CARDAPIO_FILE)
        log_activity("Restaurou backup do cardápio")
        return jsonify({"success": True, "message": "Backup restaurado com sucesso!"})
    
    return jsonify({"success": False, "message": "Nenhum backup encontrado."}), 404

# Rota para validação de cupons
@app.route('/api/cupom/validar', methods=['POST'])
def validar_cupom():
    try:
        data = request.get_json()
        codigo = data.get('codigo', '').upper().strip()
        
        if not os.path.exists(COUPONS_FILE):
            # Cria cupons padrão se o arquivo não existir
            default_coupons = {
                "PIZZA10": {"valor": 10, "tipo": "porcentagem", "desc": "10% OFF"},
                "BEMVINDO": {"valor": 5.00, "tipo": "fixo", "desc": "R$ 5,00 de desconto"}
            }
            with open(COUPONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_coupons, f, indent=4, ensure_ascii=False)
        
        with open(COUPONS_FILE, 'r', encoding='utf-8') as f:
            coupons = json.load(f)
            
        if codigo in coupons:
            return jsonify({"valid": True, "codigo": codigo, **coupons[codigo]})
        
        return jsonify({"valid": False, "message": "Cupom inválido ou expirado."})
    except Exception as e:
        return jsonify({"valid": False, "message": "Erro ao processar cupom."}), 500


def parse_price(price_input):
    if not price_input: return 0.0
    if isinstance(price_input, (int, float)): return float(price_input)
    try:
        # Remove R$, spaces, convert , to .
        clean = str(price_input).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(clean)
    except:
        return 0.0

# --- API DE PEDIDOS ---

# Helper para converter Pedido SQL -> Dict (Compatibilidade Legada)
def pedido_to_dict(p):
    # Recupera metadados
    meta = {}
    if p.metadata_json:
        try: meta = json.loads(p.metadata_json)
        except: pass
    
    items_list = []
    for i in p.itens:
        items_list.append({
            "name": i.produto_nome,
            "price": f"R$ {i.preco_unitario:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        })
    
    return {
        "id": p.id,
        "customer": p.cliente_nome,
        "phone": p.cliente_telefone,
        "method": meta.get('metodo_envio', ''),
        "address": p.cliente_endereco,
        "total": f"R$ {p.total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "items": items_list,
        "obs": meta.get('obs', ''), # Assumindo que obs está no meta ou criar campo
        "coupon": meta.get('coupon'),
        "fee": f"R$ {meta.get('taxa_entrega', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "timestamp": p.data_hora.strftime("%d/%m/%Y %H:%M:%S"),
        "status": p.status,
        "motoboy": meta.get('motoboy'),
        "payment_info": {
            "method": p.metodo_pagamento or "Não informado",
            "change": meta.get('troco_para')
        }
    }

@app.route('/api/pedido/novo', methods=['POST'])
def novo_pedido():
    try:
        data = request.get_json()
        
        # Validação: Valor Total > 0
        total_str = data.get('total', '0').replace('R$', '').replace('.', '').replace(',', '.').strip()
        try:
            total_val = float(total_str)
            if total_val <= 0:
                pass 
                # return jsonify({"success": False, "message": "O valor total do pedido deve ser maior que zero."}), 400
        except ValueError:
            return jsonify({"success": False, "message": "Valor total inválido."}), 400

        # Recupera taxa de entrega
        fee_str = data.get('fee', '0').replace('R$ ', '').replace('R$', '').replace('.', '').replace(',', '.').strip()
        try: fee_val = float(fee_str)
        except: fee_val = 0.0

        meta = {
            "taxa_entrega": fee_val,
            "coupon": data.get('coupon'),
            "metodo_envio": data.get('method'),
            "obs": data.get('obs', ''),
            "motoboy": None,
            "troco_para": data.get('change')
        }

        # Cria Pedido SQL
        pedido = Pedido(
            data_hora=datetime.now(),
            cliente_nome=data.get('customer'),
            cliente_telefone=data.get('phone'),
            cliente_endereco=data.get('address'),
            status='Pendente', # Status inicial
            metodo_pagamento=data.get('paymentMethod', 'Site'),
            total=total_val,
            metadata_json=json.dumps(meta)
        )
        db.session.add(pedido)
        db.session.flush() # Gerar ID (necessário para itens)
        
        # Cria Itens
        for item in data.get('items', []):
            # Parse preço unitario
            i_price = parse_price(item.get('price'))
            
            # Tenta linkar com produto existente
            prod = Produto.query.filter_by(nome=item.get('name')).first()
            
            item_obj = ItemPedido(
                pedido_id=pedido.id,
                produto_nome=item.get('name'),
                produto_id=prod.id if prod else None,
                quantidade=1, 
                preco_unitario=i_price,
                observacao=""
            )
            db.session.add(item_obj)
            
        db.session.commit()
            
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar pedido: {e}")
        return jsonify({"success": False, "message": "Erro ao processar pedido."}), 500

@app.route('/api/pedido/online', methods=['POST'])
def novo_pedido_online():
    try:
        data = request.get_json()
        
        # 1. Config Check
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f: config = json.load(f)
        
        if not config.get('online_ordering_enabled', False):
            return jsonify({"success": False, "message": "Pedidos online estão temporariamente desativados."}), 403

        # 2. Dados Basicos
        cliente = data.get('cliente', {})
        items = data.get('items', [])
        pagamento = data.get('pagamento', {})
        
        if not items:
            return jsonify({"success": False, "message": "O carrinho está vazio."}), 400

        # 3. Define Status Inicial
        manual_confirm = config.get('manual_payment_confirm', True)
        initial_status = 'Aguardando Confirmação' if manual_confirm else 'Pendente'

        # 4. Calcula Totais
        total_items = 0.0
        # Re-confirma precos do banco para seguranca (Simplificado aqui, confia no front por enqto ou TODO)
        total_items = float(data.get('total', 0)) # TODO: Validar server-side
        
        # 5. Metadata (Pagamento e Endereco)
        meta = {
            "metodo_envio": data.get('tipo_entrega', 'Retirada'), # Entrega ou Retirada
            "taxa_entrega": data.get('taxa_entrega', 0),
            "obs": data.get('obs', ''),
            "forma_pagamento": pagamento.get('metodo'), # 'maquina_cartao', 'maquina_pix', 'dinheiro'
            "troco_para": pagamento.get('troco_para'),
            "endereco_completo": f"{cliente.get('rua')}, {cliente.get('numero')} - {cliente.get('bairro')}" if data.get('tipo_entrega') == 'Entrega' else 'Retirada no Balcão'
        }

        # 6. Cria Pedido
        novo_pedido = Pedido(
            cliente_nome=cliente.get('nome'),
            cliente_telefone=cliente.get('telefone'),
            cliente_endereco=meta['endereco_completo'],
            status=initial_status,
            metodo_pagamento=pagamento.get('metodo_label'), # Texto legivel: "Cartão (Maquininha)"
            total=total_items,
            metadata_json=json.dumps(meta, ensure_ascii=False)
        )
        db.session.add(novo_pedido)
        db.session.flush() # ID

        # 7. Itens
        for item in items:
            item_db = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_nome=item.get('nome'),
                produto_id=item.get('id'), # Pode ser None
                quantidade=int(item.get('qtd', 1)),
                preco_unitario=float(item.get('preco', 0)),
                observacao=item.get('obs', '')
            )
            db.session.add(item_db)

        db.session.commit()
        
        # Log (Opcional)
        # log_activity(f"Novo pedido online #{novo_pedido.id} - {novo_pedido.status}")

        return jsonify({
            "success": True, 
            "id": novo_pedido.id, 
            "message": "Pedido recebido com sucesso!",
            "status": initial_status
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500



@app.route('/api/admin/pedidos')
def get_pedidos():
    if not session.get('logged_in'):
        return jsonify([]), 401
    
    # Busca pedidos que NÃO estão concluídos (fila ativa)
    # Assumindo que 'concluido' sai da tela principal
    pedidos = Pedido.query.filter(Pedido.status != 'concluido').order_by(Pedido.data_hora.desc()).all()
    
    return jsonify([pedido_to_dict(p) for p in pedidos])

@app.route('/api/admin/pedido/concluir', methods=['POST'])
def concluir_pedido():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    order_id = data.get('id')
    
    try:
        pedido = Pedido.query.get(order_id)
        if pedido:
            # --- Lógica de Estoque (Fase 2) ---
            # Carrega Config
            config = {}
            if os.path.exists(CONFIG_FILE):
                try: 
                    with open(CONFIG_FILE, 'r') as f: 
                        config = json.load(f)
                except: pass
            
            print(f"DEBUG: Concluding Order {order_id}. Config Inventory: {config.get('inventory_enabled')}")
            
            if config.get('inventory_enabled', False):
                allow_negative = config.get('allow_negative_stock', True)
                print(f"DEBUG: Allow Negative: {allow_negative}")
                
                # Verifica Estoque Primeiro (se não permitir negativo)
                if not allow_negative:
                    for item in pedido.itens:
                        if not item.produto_id: 
                            print(f"DEBUG: Item {item.produto_nome} has no Product ID")
                            continue
                        receita = FichaTecnica.query.filter_by(produto_id=item.produto_id).all()
                        if not receita: print(f"DEBUG: No recipe for Product {item.produto_id}")
                        for r in receita:
                            qtd_necessaria = r.quantidade * item.quantidade
                            if r.ingrediente.estoque_atual < qtd_necessaria:
                                return jsonify({"success": False, "message": f"Estoque insuficiente de {r.ingrediente.nome}. Necessário: {qtd_necessaria}, Atual: {r.ingrediente.estoque_atual}"}), 400
                
                # Baixa o Estoque
                print("DEBUG: Deducting Stock...")
                for item in pedido.itens:
                    if not item.produto_id: continue
                    receita = FichaTecnica.query.filter_by(produto_id=item.produto_id).all()
                    for r in receita:
                        qtd_necessaria = r.quantidade * item.quantidade
                        r.ingrediente.estoque_atual -= qtd_necessaria
                        print(f"DEBUG: Deducted {qtd_necessaria} from {r.ingrediente.nome}. New Stock: {r.ingrediente.estoque_atual}")
                        db.session.add(r.ingrediente) # Marca para update

            pedido.status = 'concluido'
            
            # --- Lógica de Fidelidade (Híbrida: Mantendo JSON por enquanto) ---
            try:
                # Extrai apenas números do telefone
                phone = ''.join(filter(str.isdigit, pedido.cliente_telefone or ''))
                points = int(pedido.total) # 1 ponto por real
                
                if phone and points > 0:
                    loyalty = {}
                    if os.path.exists(LOYALTY_FILE):
                        with open(LOYALTY_FILE, 'r', encoding='utf-8') as lf:
                            loyalty = json.load(lf)
                    
                    loyalty[phone] = loyalty.get(phone, 0) + points
                    
                    with open(LOYALTY_FILE, 'w', encoding='utf-8') as lf:
                        json.dump(loyalty, lf, indent=4)
            except Exception as e: print(f"Erro fidelidade: {e}")
            
            db.session.commit()
            log_activity(f"Concluiu pedido #{order_id} (SQL)")
            return jsonify({"success": True})
            
        return jsonify({"success": False, "message": "Pedido não encontrado"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/pedido/status', methods=['POST'])
def update_pedido_status():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    order_id = data.get('id')
    new_status = data.get('status')
    
    try:
        pedido = Pedido.query.get(order_id)
        if pedido:
            pedido.status = new_status
            db.session.commit()
            log_activity(f"Alterou status do pedido #{order_id} para {new_status} (SQL)")
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Pedido não encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/pedido/update_total', methods=['POST'])
def update_pedido_total():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    order_id = data.get('id')
    new_total_str = data.get('total')
    
    try:
        total_val = parse_price(new_total_str)
        if total_val <= 0:
            return jsonify({"success": False, "message": "Valor inválido"}), 400
            
        pedido = Pedido.query.get(order_id)
        if pedido:
            pedido.total = total_val
            db.session.commit()
            log_activity(f"Atualizou total do pedido #{order_id} (SQL)")
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Pedido não encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/pedido/motoboy', methods=['POST'])
def update_pedido_motoboy():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    order_id = data.get('id')
    motoboy = data.get('motoboy')
    
    try:
        pedido = Pedido.query.get(order_id)
        if pedido:
            # Motoboy geralmente fica no metadata se não tiver coluna
            # Mas vamos checar se tem coluna? Não tem. Metadata it is.
            # Precisa ler metadata, update, save
            meta = {}
            if pedido.metadata_json:
                try: meta = json.loads(pedido.metadata_json)
                except: pass
            
            meta['motoboy'] = motoboy
            pedido.metadata_json = json.dumps(meta)
            
            db.session.commit()
            log_activity(f"Definiu motoboy {motoboy} para pedido #{order_id} (SQL)")
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Pedido não encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/pedidos/count')
def api_pedidos_count():
    if not session.get('logged_in'):
        return jsonify({"count": 0}), 401
    
    # Conta apenas pedidos não concluídos (ativos)
    count = Pedido.query.filter(Pedido.status != 'concluido').count()
    return jsonify({"count": count})

@app.route('/api/admin/historico')
def get_historico():
    if not session.get('logged_in'):
        return jsonify([]), 401
    
    # Busca pedidos CONCLUÍDOS
    pedidos = Pedido.query.filter_by(status='concluido').order_by(Pedido.data_hora.desc()).all()
    return jsonify([pedido_to_dict(p) for p in pedidos])

@app.route('/api/admin/historico/csv')
def export_historico_csv():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    query = Pedido.query.filter_by(status='concluido')
    
    if start_date and end_date:
        try:
            # Ajusta para cobrir o dia inteiro
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            e_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(Pedido.data_hora >= s_dt, Pedido.data_hora <= e_dt)
        except: pass
        
    pedidos = query.order_by(Pedido.data_hora.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['ID', 'Data', 'Cliente', 'Telefone', 'Metodo', 'Endereco', 'Total', 'Itens', 'Obs', 'Motoboy', 'Status Final'])
    
    for p in pedidos:
        # Recupera meta
        meta = {}
        if p.metadata_json:
            try: meta = json.loads(p.metadata_json)
            except: pass
            
        # Formata itens
        item_str = " | ".join([f"{i.produto_nome} (R$ {i.preco_unitario:.2f})" for i in p.itens])
        
        writer.writerow([
            p.id,
            p.data_hora.strftime("%d/%m/%Y %H:%M:%S"),
            p.cliente_nome,
            p.cliente_telefone,
            meta.get('metodo_envio', ''),
            p.cliente_endereco,
            f"R$ {p.total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            item_str,
            meta.get('obs', ''),
            meta.get('motoboy', ''),
            p.status
        ])
        
    output.seek(0)
    filename = f"historico_pedidos_{start_date}_a_{end_date}.csv" if start_date and end_date else "historico_pedidos_geral.csv"
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    inventory_enabled = False
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                inventory_enabled = cfg.get('inventory_enabled', False)
        except: pass
        
    return render_template('admin_dashboard.html', title='Dashboard — Pizzaria Colonial', inventory_enabled=inventory_enabled)

@app.route('/admin/estoque')
def admin_estoque():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    # Checa se está habilitado
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except: pass
        
    if not config.get('inventory_enabled', False):
         flash('O módulo de estoque está desativado.', 'warning')
         return redirect(url_for('admin_dashboard'))

    # Carrega produtos para o dropdown de ficha técnica
    produtos = Produto.query.order_by(Produto.nome).all()
    return render_template('admin_estoque.html', title='Gestão de Estoque — Pizzaria Colonial', produtos=produtos)

@app.route('/admin/estoque/baixo')
def admin_estoque_baixo():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    # Checa se está habilitado
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except: pass
        
    if not config.get('inventory_enabled', False):
         flash('O módulo de estoque está desativado.', 'warning')
         return redirect(url_for('admin_dashboard'))

    return render_template('admin_estoque_baixo.html', title='Relatório de Baixo Estoque — Pizzaria Colonial')

@app.route('/api/admin/reservas', methods=['GET'])
def api_admin_reservas():
    if not session.get('logged_in'):
        return jsonify([]), 401
    
    # Busca reservas futuras ou recentes (últimos 7 dias)
    # Para simplificar, trazemos todas ordenadas por data desc
    reservas = Reserva.query.order_by(Reserva.data_reserva.desc(), Reserva.hora_reserva.desc()).all()
    
    return jsonify([{
        "id": r.id,
        "nome": r.nome_cliente,
        "telefone": r.telefone,
        "data": r.data_reserva.strftime('%d/%m/%Y'),
        "hora": r.hora_reserva.strftime('%H:%M'),
        "pessoas": r.num_pessoas,
        "obs": r.observacao,
        "status": r.status
    } for r in reservas])

@app.route('/api/admin/reservas/status', methods=['POST'])
def api_admin_reservas_status():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
        
    data = request.get_json()
    reserva = Reserva.query.get(data.get('id'))
    if reserva:
        reserva.status = data.get('status')
        db.session.commit()
        log_activity(f"Alterou status da reserva #{reserva.id} para {reserva.status}")
        return jsonify({"success": True})
        
    return jsonify({"success": False, "message": "Reserva não encontrada"}), 404

@app.route('/api/admin/depoimentos', methods=['GET'])
def api_admin_depoimentos():
    if not session.get('logged_in'):
        return jsonify([]), 401
    
    # Lista depoimentos ordenados por data (mais recentes primeiro)
    depoimentos = Depoimento.query.order_by(Depoimento.data.desc()).all()
    
    return jsonify([{
        "id": d.id,
        "nome": d.nome,
        "texto": d.texto,
        "nota": d.nota,
        "data": d.data.strftime('%d/%m/%Y %H:%M'),
        "aprovado": d.aprovado
    } for d in depoimentos])

@app.route('/api/admin/depoimento/status', methods=['POST'])
def api_admin_depoimento_status():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    d_id = data.get('id')
    aprovado = data.get('aprovado')
    
    depoimento = Depoimento.query.get(d_id)
    if depoimento:
        depoimento.aprovado = aprovado
        db.session.commit()
        log_activity(f"{'Aprovou' if aprovado else 'Ocultou'} depoimento #{d_id}")
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Depoimento não encontrado"}), 404

@app.route('/api/admin/depoimento', methods=['DELETE'])
def api_admin_depoimento_delete():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    data = request.get_json()
    d_id = data.get('id')
    
    depoimento = Depoimento.query.get(d_id)
    if depoimento:
        db.session.delete(depoimento)
        db.session.commit()
        log_activity(f"Excluiu depoimento #{d_id}")
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Depoimento não encontrado"}), 404

@app.route('/admin/config', methods=['GET', 'POST'])
def admin_config():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        try:
            # Carrega config atual
            current_config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
            
            # Atualiza com dados do form
            data = request.form
            
            # Checkbox html: se não marcado, não vem no form.
            current_config['inventory_enabled'] = 'inventory_enabled' in data
            current_config['allow_negative_stock'] = 'allow_negative_stock' in data
            current_config['ai_enabled'] = 'ai_enabled' in data
            current_config['self_service_enabled'] = 'self_service_enabled' in data
            current_config['rodizio_pizza_enabled'] = 'rodizio_pizza_enabled' in data
            current_config['rodizio_carne_enabled'] = 'rodizio_carne_enabled' in data
            
            # Campos de texto
            current_config['tempo_espera'] = data.get('tempo_espera')
            current_config['telefone'] = data.get('telefone')
            current_config['whatsapp'] = data.get('whatsapp')
            current_config['endereco_principal'] = data.get('endereco_principal')
            current_config['theme'] = data.get('theme')
            current_config['sobre_nos'] = data.get('sobre_nos')
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
                
            flash('Configurações salvas com sucesso!', 'success')
            return redirect(url_for('admin_config'))
            
        except Exception as e:
            flash(f'Erro ao salvar: {str(e)}', 'danger')
    
    # GET: Carrega config para exibir
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except: pass
        
    return render_template('admin_config.html', title='Configurações — Pizzaria Colonial', config=config)

@app.route('/api/admin/stats')
def admin_stats():
    if not session.get('logged_in'):
        return jsonify({}), 401
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    dates = []
    
    def extract_dates(file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        if 'timestamp' in item:
                            # Extrai data (dd/mm/yyyy)
                            date_str = item['timestamp'].split(' ')[0]
                            
                            # Filtro de Data
                            if start_date and end_date:
                                try:
                                    item_dt = datetime.strptime(date_str, "%d/%m/%Y").date()
                                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                                    if not (start_dt <= item_dt <= end_dt):
                                        continue
                                except: pass
                            
                            dates.append(date_str)
            except: pass

    # Coleta datas de pedidos ativos e do histórico
    extract_dates(ORDERS_FILE)
    extract_dates(HISTORY_FILE)
    
    counts = Counter(dates)
    # Ordena cronologicamente
    sorted_dates = sorted(counts.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
    
    return jsonify({
        "labels": sorted_dates,
        "values": [counts[d] for d in sorted_dates]
    })

@app.route('/api/admin/stats/categories')
def admin_stats_categories():
    if not session.get('logged_in'):
        return jsonify({}), 401
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    # Carrega mapeamento de itens -> categorias para saber a qual categoria o item pertence
    item_category_map = {}
    if os.path.exists(CARDAPIO_FILE):
        try:
            with open(CARDAPIO_FILE, 'r', encoding='utf-8') as f:
                menu = json.load(f)
                for category, items in menu.items():
                    for item in items:
                        item_category_map[item['nome'].lower().strip()] = category
        except: pass
        
    category_counts = Counter()
    
    def process_orders(file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for order in data:
                        # Filtro de Data
                        if start_date and end_date and 'timestamp' in order:
                            try:
                                order_dt = datetime.strptime(order['timestamp'].split(' ')[0], "%d/%m/%Y").date()
                                s_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                                e_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                                if not (s_dt <= order_dt <= e_dt):
                                    continue
                            except: pass
                        
                        for item in order.get('items', []):
                            name = item['name'].lower().strip()
                            cat = item_category_map.get(name, 'Outros')
                            category_counts[cat] += 1
            except: pass

    process_orders(ORDERS_FILE)
    process_orders(HISTORY_FILE)
    
    return jsonify({
        "labels": list(category_counts.keys()),
        "values": list(category_counts.values())
    })

@app.route('/api/admin/stats/clients')
def admin_stats_clients():
    if not session.get('logged_in'):
        return jsonify([]), 401
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    client_counts = Counter()
    client_names = {} 

    def process_orders(file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for order in data:
                        # Filtro de Data
                        if start_date and end_date and 'timestamp' in order:
                            try:
                                order_dt = datetime.strptime(order['timestamp'].split(' ')[0], "%d/%m/%Y").date()
                                s_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                                e_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                                if not (s_dt <= order_dt <= e_dt):
                                    continue
                            except: pass
                        
                        phone = order.get('phone', '').strip()
                        name = order.get('customer', 'Desconhecido').strip()
                        
                        if phone:
                            client_counts[phone] += 1
                            client_names[phone] = name 
            except: pass

    process_orders(ORDERS_FILE)
    process_orders(HISTORY_FILE)
    
    top_5 = client_counts.most_common(5)
    
    result = []
    for phone, count in top_5:
        result.append({
            "name": client_names.get(phone, "Desconhecido"),
            "phone": phone,
            "count": count
        })
        
    return jsonify(result)

@app.route('/api/admin/stats/peak_hours')
def admin_stats_peak_hours():
    if not session.get('logged_in'):
        return jsonify({}), 401
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    hours_counts = Counter()
    
    def process_orders(file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for order in data:
                        if 'timestamp' in order:
                            try:
                                # timestamp format: "dd/mm/yyyy HH:MM:SS"
                                dt_str = order['timestamp']
                                dt_obj = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                                
                                # Date filtering
                                if start_date and end_date:
                                    s_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                                    e_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                                    if not (s_dt <= dt_obj.date() <= e_dt):
                                        continue
                                
                                hours_counts[dt_obj.hour] += 1
                            except: pass
            except: pass

    process_orders(ORDERS_FILE)
    process_orders(HISTORY_FILE)
    
    # Garante que todas as horas 00-23 existam no gráfico
    labels = [f"{h:02d}h" for h in range(24)]
    values = [hours_counts.get(h, 0) for h in range(24)]
    
    return jsonify({
        "labels": labels,
        "values": values
    })

MOTOBOYS_FILE = os.path.join(os.path.dirname(__file__), 'motoboys.json')

@app.route('/admin/motoboys')
def admin_motoboys():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin_motoboys.html', title='Motoboys — Admin Colonial')

@app.route('/api/admin/motoboys', methods=['GET', 'POST'])
def api_motoboys():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
        
    if request.method == 'GET':
        if os.path.exists(MOTOBOYS_FILE):
            with open(MOTOBOYS_FILE, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify([])

    if request.method == 'POST':
        data = request.get_json()
        with open(MOTOBOYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        log_activity("Atualizou lista de motoboys")
        return jsonify({"success": True})

# --- API Usuários e Promoções ---

@app.route('/api/admin/usuarios', methods=['GET', 'POST'])
def api_usuarios():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({"success": False}), 403
        
    if request.method == 'GET':
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify([])
        
    if request.method == 'POST':
        data = request.get_json()
        # Validação básica
        if not data: return jsonify({"success": False}), 400
        
        # --- Lógica de Log de Alterações ---
        try:
            old_users = []
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    old_users = json.load(f)
            
            old_map = {u['username']: u for u in old_users}
            new_map = {u['username']: u for u in data}
            
            # Verifica criados e editados
            for u in data:
                uname = u['username']
                if uname not in old_map:
                    log_activity(f"Criou o usuário '{uname}'")
                elif u.get('password') != old_map[uname].get('password') or u.get('role') != old_map[uname].get('role'):
                    log_activity(f"Editou o usuário '{uname}'")
            
            # Verifica excluídos
            for uname in old_map:
                if uname not in new_map:
                    log_activity(f"Excluiu o usuário '{uname}'")
        except Exception as e: print(f"Erro ao gerar logs de usuário: {e}")
        
        # Aplica hash nas senhas que não estiverem hashadas (novas ou editadas)
        for u in data:
            pwd = u.get('password', '')
            # Se não for um hash SHA256 válido (64 chars hex), gera o hash
            if not re.match(r'^[a-fA-F0-9]{64}$', pwd):
                u['password'] = hashlib.sha256(pwd.encode()).hexdigest()

        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        return jsonify({"success": True})

@app.route('/api/admin/change_password', methods=['POST'])
def change_own_password():
    if not session.get('logged_in'):
        return jsonify({"success": False, "message": "Não logado"}), 401
    
    data = request.get_json()
    current_pass = data.get('current_password')
    new_pass = data.get('new_password')
    
    if not current_pass or not new_pass:
        return jsonify({"success": False, "message": "Preencha todos os campos"}), 400
        
    username = session.get('username')
    
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
            
        for u in users:
            if u['username'] == username:
                # Verifica senha atual (Hash)
                curr_hash = hashlib.sha256(current_pass.encode()).hexdigest()
                if u['password'] != curr_hash:
                     return jsonify({"success": False, "message": "Senha atual incorreta"}), 400
                
                # Define nova senha
                u['password'] = hashlib.sha256(new_pass.encode()).hexdigest()
                with open(USERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(users, f, indent=4)
                log_activity(f"Alterou a própria senha")
                return jsonify({"success": True})
            
    return jsonify({"success": False, "message": "Usuário não encontrado"}), 404

@app.route('/api/admin/promocoes', methods=['GET', 'POST'])
def api_promocoes():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 403
        
    if request.method == 'GET':
        if os.path.exists(PROMOS_FILE):
            with open(PROMOS_FILE, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify([])
        
    if request.method == 'POST':
        data = request.get_json()
        with open(PROMOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        log_activity("Atualizou promoções agendadas")
        return jsonify({"success": True})

@app.route('/api/admin/categorias')
def api_categorias():
    if os.path.exists(CARDAPIO_FILE):
        with open(CARDAPIO_FILE, 'r', encoding='utf-8') as f:
            return jsonify(list(json.load(f).keys()))
    return jsonify([])

# --- Configurações Gerais e Fidelidade ---

@app.route('/api/config/geral', methods=['GET', 'POST'])
def api_config_geral():
    # Endpoint unificado para configurações da loja
    if request.method == 'POST':
        if not session.get('logged_in'):
            return jsonify({"success": False}), 401
        data = request.get_json()
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        config.update(data) # Atualiza/Mescla com os dados novos
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return jsonify({"success": True})
    
    # GET
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify({})

@app.route('/api/fidelidade/pontos', methods=['POST'])
def api_fidelidade_pontos():
    data = request.get_json()
    phone = ''.join(filter(str.isdigit, data.get('phone', '')))
    
    if os.path.exists(LOYALTY_FILE):
        with open(LOYALTY_FILE, 'r', encoding='utf-8') as f:
            loyalty = json.load(f)
            return jsonify({"pontos": loyalty.get(phone, 0)})
            
    return jsonify({"pontos": 0})

@app.route('/api/admin/banners', methods=['GET', 'POST'])
def api_admin_banners():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    if request.method == 'GET':
        if os.path.exists(BANNERS_FILE):
            with open(BANNERS_FILE, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify([])
        
    if request.method == 'POST':
        data = request.get_json()
        with open(BANNERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        log_activity("Atualizou banners da home")
        return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)
