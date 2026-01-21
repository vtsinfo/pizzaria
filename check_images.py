import os
import json
import sqlite3

def check_json():
    print("--- Verificando cardapio.json ---")
    if not os.path.exists('cardapio.json'):
        print("cardapio.json nao encontrado.")
        return

    with open('cardapio.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for category, items in data.items():
        for item in items:
            foto = item.get('foto')
            if foto:
                # Remove leading / if present for local check
                local_path = foto.lstrip('/')
                local_path = local_path.replace('/', os.sep)
                
                if os.path.exists(local_path):
                    print(f"[OK] {foto}")
                else:
                    print(f"[ERRO] Arquivo nao encontrado: {local_path} (URL: {foto})")

def check_db():
    print("\n--- Verificando Banco de Dados ---")
    db_path = os.path.join('instance', 'pizzaria.db')
    if not os.path.exists(db_path):
        print(f"{db_path} nao encontrado.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nome, foto_url FROM produtos WHERE foto_url IS NOT NULL AND foto_url != ''")
        rows = cursor.fetchall()
        for nome, url in rows:
            # url ex: /static/uploads/arquivo.png
            # local: static/uploads/arquivo.png
            local_path = url.lstrip('/')
            local_path = local_path.replace('/', os.sep)
            
            # Ajuste: se o script roda em 'pizzaria', e 'static' está em 'pizzaria/static'
            if os.path.exists(local_path):
                print(f"[OK] DB: {nome} -> {url}")
            else:
                print(f"[ERRO] DB: {nome} -> {local_path} (URL: {url}) - Arquivo nao existe no disco")
    except Exception as e:
        print(f"Erro ao ler DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_json()
    check_db()
