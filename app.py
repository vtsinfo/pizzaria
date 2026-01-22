from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session, Response, send_file
import os
import json
import csv
import io
import shutil
import functools
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime
from collections import Counter
from flask_sqlalchemy import SQLAlchemy     # Novo
from database import db, init_db   # Novo
from sqlalchemy import text
from models import User, Categoria, Produto, Pedido, ItemPedido, Ingrediente, FichaTecnica, Cupom, Fidelidade, Banner, Fornecedor, Compra, ItemCompra
app = Flask(__name__)
# Em produção, use: os.environ.get('SECRET_KEY')
app.secret_key = os.environ.get('SECRET_KEY', 'vts_pizzaria_dev_key_change_me')

# --- CONFIGURAÇÃO BANCO DE DADOS (NOVO) ---
# BASE_DIR ajustado para a pasta da aplicação
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(INSTANCE_DIR, 'pizzaria.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco de dados com a aplicação
init_db(app)

# --- REGISTRO DE BLUEPRINTS ---
from public import public_bp
from api import api_bp
from admin import admin_bp

app.register_blueprint(public_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)

# Migração de Fidelidade JSON -> SQL
with app.app_context():
    db.create_all() # Garante que TODAS as tabelas (incluindo Banner) existam

    # Migração de Schema (Adicionar colunas novas manualmente em SQLite)
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE ingredientes ADD COLUMN validade DATE"))
            conn.commit()
    except Exception:
        pass

    if os.path.exists(os.path.join(os.path.dirname(__file__), 'fidelidade.json')):
        try:
            if Fidelidade.query.count() == 0:
                with open(os.path.join(os.path.dirname(__file__), 'fidelidade.json'), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print("--> Migrando fidelidade do JSON para SQL...")
                    for phone, pts in data.items():
                        db.session.add(Fidelidade(telefone=phone, pontos=pts))
                    db.session.commit()
        except Exception as e:
            print(f"Erro na migração de fidelidade: {e}")

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
RESERVATIONS_FILE = os.path.join(os.path.dirname(__file__), 'reservas.json')
# --- Context Processor (Injeta dados em todos os templates) ---
@app.context_processor
def inject_site_config():
    default_config = {
        "nome_fantasia": "Pizzaria Colonial",
        "telefone": "(11) 91456-9028",
        "whatsapp": "5511914569028",
        "endereco_principal": "Rua Virgínia Ferni, 1758 - Itaquera, SP",
        "tempo_espera": "40-50 min",
        "logo_url": "", # Se vazio, usa texto
        "cor_primaria": "#ffc107", # Amarelo padrão
        "ai_enabled": True, # Assistente ativado por padrão
        "voice_gender": "female", # 'female' ou 'male'
        "instagram": "",
        "facebook": "",
        "tipo_forno": "Forno Especial",
        "sobre_nos": "A Pizzaria Colonial nasceu do sonho de unir tradição e qualidade em um ambiente familiar. Começamos com muita paixão e hoje somos referência na região, conhecidos pela massa crocante e ingredientes selecionados."
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                default_config.update(saved_config)
    except Exception:
        pass # Garante que falhas no arquivo de config não tirem o site do ar
    default_config['voice_gender'] = 'male' # Forçar Diovani para teste
    return dict(site_config=default_config, now=datetime.now())

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    # Cria usuário padrão (admin/pizza123) se banco estiver vazio
    if User.query.count() == 0:
        default_pass = generate_password_hash("pizza123")
        admin = User(username="admin", password_hash=default_pass, role="admin", permissions='["all"]')
        db.session.add(admin)
        db.session.commit()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Busca usuário no banco
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Verifica senha
            if check_password_hash(user.password_hash, password):
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
def pedido_to_dict(p):
    """Converte um objeto Pedido para dicionário compatível com o Front-end."""
    meta = {}
    if p.metadata_json:
        try: meta = json.loads(p.metadata_json)
        except: pass
    
    return {
        "id": p.id,
        "timestamp": p.data_hora.strftime("%d/%m/%Y %H:%M:%S") if p.data_hora else "",
        "customer": p.cliente_nome,
        "phone": p.cliente_telefone,
        "address": p.cliente_endereco,
        "status": p.status,
        "total": f"R$ {(p.total or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "items": [{"name": i.produto_nome, "price": f"R$ {(i.preco_unitario or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), "qty": i.quantidade} for i in p.itens],
        "fee": meta.get('taxa_entrega') or 'R$ 0,00',
        "method": meta.get('metodo_envio', 'Não informado'),
        "paymentMethod": p.metodo_pagamento or meta.get('paymentMethod', 'Não informado'),
        "change": meta.get('change', ''),
        "obs": meta.get('obs', ''),
        "motoboy": meta.get('motoboy', '')
    }

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

def save_json_list(filepath, new_item):
    items = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                items = json.load(f)
        except: pass
    
    items.append(new_item)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=4, ensure_ascii=False)

def check_permission(perm):
    user_perms = session.get('permissions', [])
    if 'all' in user_perms: return True
    return perm in user_perms

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
    
    # Retorna do Banco de Dados formatado como o front espera (Dict)
    cupons = Cupom.query.all()
    result = {}
    for c in cupons:
        result[c.codigo] = {
            "valor": c.valor,
            "tipo": c.tipo,
            "desc": c.descricao,
            "ativo": c.ativo,
            "id": c.id
        }
    return jsonify(result)

@app.route('/api/admin/cupons/save', methods=['POST'])
def api_admin_save_cupons():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"success": False, "message": "Dados inválidos"}), 400
        
        # Sincroniza o JSON recebido com o Banco de Dados
        # 1. Remove cupons que não estão no payload (comportamento de "Salvar Tudo")
        existing = Cupom.query.all()
        for c in existing:
            if c.codigo not in data:
                db.session.delete(c)
        
        # 2. Atualiza ou Cria
        for code, info in data.items():
            c = Cupom.query.filter_by(codigo=code).first()
            if c:
                c.tipo = info.get('tipo', 'fixo')
                c.valor = parse_price(info.get('valor', 0))
                c.descricao = info.get('desc', '')
            else:
                new_c = Cupom(
                    codigo=code,
                    tipo=info.get('tipo', 'fixo'),
                    valor=parse_price(info.get('valor', 0)),
                    descricao=info.get('desc', ''),
                    ativo=True
                )
                db.session.add(new_c)
                
        db.session.commit()
        log_activity("Atualizou lista de cupons (SQL)")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
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
        if not isinstance(price_str, str): return 0.0
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

# Rota para Upload de Imagens de Banner (Específica)
@app.route('/api/admin/upload/banner', methods=['POST'])
def upload_banner():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False}), 400
        
    # Reutiliza lógica de salvamento mas com prefixo para organização
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', file.filename)
    filename = f"banner_{int(datetime.now().timestamp())}_{safe_filename}"
    
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
        
        # Busca no Banco de Dados
        cupom = Cupom.query.filter_by(codigo=codigo, ativo=True).first()
        
        if cupom:
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

@app.route('/api/config/geral', methods=['GET', 'POST'])
def api_config_geral():
    # Helper para carregar config
    def load_cfg():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {}

    if request.method == 'GET':
        return jsonify(load_cfg())

    if request.method == 'POST':
        try:
            data = request.get_json()
            current_config = load_cfg()
            
            # Merge configs
            current_config.update(data)
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
                
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/stats')
def admin_stats():
    if not session.get('logged_in'):
        return jsonify({}), 401
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    query = Pedido.query
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59)
            query = query.filter(Pedido.data_hora.between(start_dt, end_dt))
        except: pass

    pedidos = query.all()
    dates = [p.data_hora.strftime("%d/%m/%Y") for p in pedidos if p.data_hora]
    
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
    
    # Mapeamento via Banco de Dados
    item_category_map = {}
    for p in Produto.query.all():
        cat_nome = p.categoria.nome if p.categoria else "Sem Categoria"
        item_category_map[p.nome.lower().strip()] = cat_nome

    category_counts = Counter()
    query = Pedido.query
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59)
            query = query.filter(Pedido.data_hora.between(start_dt, end_dt))
        except: pass

    for order in query.all():
        for item in order.itens:
            name = item.produto_nome.lower().strip() if item.produto_nome else ""
            cat = item_category_map.get(name, 'Outros')
            category_counts[cat] += 1
    
    return jsonify({
        "labels": list(category_counts.keys()),
        "values": list(category_counts.values())
    })

# --- Cozinha API ---

@app.route('/api/admin/pedidos')
def api_admin_pedidos_list():
    if not session.get('logged_in'):
        return jsonify([]), 401
    
    # Retorna pedidos não concluídos (Pendente, Em Preparo, Pronto)
    # Ordenados por ID (cronológico)
    pedidos = Pedido.query.filter(Pedido.status != 'concluido').order_by(Pedido.id).all()
    
    result = []
    for p in pedidos:
        meta = {}
        if p.metadata_json:
            try: meta = json.loads(p.metadata_json)
            except: pass
            
        items = []
        for i in p.itens:
            items.append({
                "name": i.produto_nome,
                "quantity": i.quantidade # Frontend espera quantity
            })
            
        result.append({
            "id": p.id,
            "timestamp": p.data_hora.strftime("%d/%m/%Y %H:%M:%S") if p.data_hora else "",
            "customer": p.cliente_nome,
            "method": meta.get('metodo_envio', 'Balcão'),
            "status": p.status, # Pendente, Em Preparo, Pronto
            "obs": meta.get('obs', ''),
            "items": items
        })
        
    return jsonify(result)

@app.route('/api/admin/pedido/status', methods=['POST'])
def api_admin_pedido_status():
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
            log_activity(f"Atualizou status do pedido #{pedido.id} para {new_status}")
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Pedido não encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/stats/clients')
def admin_stats_clients():
    if not session.get('logged_in'):
        return jsonify([]), 401
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    client_counts = Counter()
    client_names = {} 

    query = Pedido.query
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59)
            query = query.filter(Pedido.data_hora.between(start_dt, end_dt))
        except: pass

    for order in query.all():
        phone = order.cliente_telefone.strip() if order.cliente_telefone else ""
        if phone:
            client_counts[phone] += 1
            client_names[phone] = order.cliente_nome or "Desconhecido"
    
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
    
    query = Pedido.query
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59)
            query = query.filter(Pedido.data_hora.between(start_dt, end_dt))
        except: pass

    for order in query.all():
        if order.data_hora:
            hours_counts[order.data_hora.hour] += 1
    
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
        users = User.query.all()
        return jsonify([{
            "username": u.username,
            "role": u.role,
            "permissions": (
                json.loads(u.permissions) 
                if (u.permissions and u.permissions.strip()) 
                else []
            ) if isinstance(u.permissions, str) else (
                u.permissions 
                if isinstance(u.permissions, list) 
                else []
            ),
            "password": u.password_hash # Mantém compatibilidade com front (hash)
        } for u in users])
        
    if request.method == 'POST':
        data = request.get_json()
        if not isinstance(data, list): return jsonify({"success": False, "message": "Formato inválido"}), 400
        if not data: return jsonify({"success": False}), 400
        
        try:
            # Sincronização com o Banco de Dados (Garante que u tenha a chave username)
            incoming_usernames = [u.get('username') for u in data if u.get('username')]
            
            # 1. Remove usuários excluídos
            existing_users = User.query.all()
            for db_user in existing_users:
                if db_user.username not in incoming_usernames:
                    # Evita excluir o próprio usuário logado por acidente, se desejar
                    if db_user.username == session.get('username'):
                        continue
                    db.session.delete(db_user)
                    log_activity(f"Excluiu o usuário '{db_user.username}'")
            
            # 2. Atualiza ou Cria
            for u_data in data:
                username = u_data.get('username')
                pwd = u_data.get('password', '')
                role = u_data.get('role', 'editor')
                perms = json.dumps(u_data.get('permissions', []))
                
                user = User.query.filter_by(username=username).first()
                
                # Se a senha enviada não parece um hash (ex: pbkdf2:sha256...), gera um novo
                new_hash = pwd
                if pwd and not pwd.startswith(('pbkdf2:sha256:', 'scrypt:')):
                    new_hash = generate_password_hash(pwd)
                
                if user:
                    # Atualiza
                    if user.role != role or user.permissions != perms or (pwd and user.password_hash != new_hash):
                        user.role = role
                        user.permissions = perms
                        if pwd: user.password_hash = new_hash
                        log_activity(f"Editou o usuário '{username}'")
                else:
                    # Cria
                    new_user = User(username=username, password_hash=new_hash, role=role, permissions=perms)
                    db.session.add(new_user)
                    log_activity(f"Criou o usuário '{username}'")
            
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

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
    
    user = User.query.filter_by(username=username).first()
    
    if user:
        # Verifica senha atual
        if not check_password_hash(user.password_hash, current_pass):
                return jsonify({"success": False, "message": "Senha atual incorreta"}), 400
        
        # Define nova senha
        user.password_hash = generate_password_hash(new_pass)
        db.session.commit()
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
    cats = Categoria.query.order_by(Categoria.ordem).all()
    return jsonify([c.nome for c in cats])

# --- Configurações Gerais e Fidelidade ---




@app.route('/api/admin/banners', methods=['GET', 'POST'])
def api_admin_banners():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
    if request.method == 'GET':
        banners = Banner.query.order_by(Banner.ordem).all()
        return jsonify([{
            "id": b.id,
            "titulo": b.titulo,
            "descricao": b.descricao,
            "imagem": b.imagem_url,
            "ordem": b.ordem,
            "ativo": b.ativo
        } for b in banners])
        
    if request.method == 'POST':
        data = request.get_json()
        
        # Estratégia simples: Limpar e Recriar (para garantir ordem e exclusões)
        # Como banners não têm relacionamentos complexos, isso é seguro.
        try:
            Banner.query.delete()
            
            for i, item in enumerate(data):
                b = Banner(
                    titulo=item.get('titulo', ''),
                    descricao=item.get('descricao', ''),
                    imagem_url=item.get('imagem', ''),
                    ordem=i,
                    ativo=item.get('ativo', True)
                )
                db.session.add(b)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500
            
        log_activity("Atualizou banners da home")
        return jsonify({"success": True})

@app.route('/api/admin/reservas', methods=['GET', 'POST'])
def api_admin_reservas():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
        
    if request.method == 'GET':
        if os.path.exists(RESERVATIONS_FILE):
            with open(RESERVATIONS_FILE, 'r', encoding='utf-8') as f:
                # Retorna lista invertida (mais recentes primeiro)
                data = json.load(f)
                return jsonify(data[::-1])
        return jsonify([])
        
    if request.method == 'POST':
        # Para atualizar status (ex: confirmar/cancelar)
        data = request.get_json()
        if os.path.exists(RESERVATIONS_FILE):
            with open(RESERVATIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            log_activity("Atualizou lista de reservas")
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Arquivo não encontrado"}), 404

# --- Rotas da Cozinha (Adicionadas para correção) ---

@app.route('/cozinha')
def monitor_cozinha_direct():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('cozinha.html')

@app.route('/api/admin/pedido/concluir', methods=['POST'])
def concluir_pedido():
    if not session.get('logged_in'):
        return jsonify({"success": False}), 401
    
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

if __name__ == '__main__':
    app.run(debug=True)
