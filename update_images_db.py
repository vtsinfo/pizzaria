import json
import sqlite3
import shutil
import os

# Map filenames to Product Names (Database) and JSON keys
image_map = {
    "Coca-Cola 2L": "coca_cola_2l_1769135764358.png",
    "Guaraná 2L": "guarana_2l_1769135778016.png",
    "Suco Del Valle": "suco_del_valle_uva_1769135790950.png",
    "Cervejas Variadas": "cervejas_variadas_1769135805453.png",
    "Frango Assado": "marmitex_frango_assado_1769136134136.png",
    "Frango à Parmegiana": "marmitex_parmegiana_1769136177408.png",
    "Picanha Assada": "marmitex_picanha_assada_1769136227520.png",
    "Filé de Merluza": "marmitex_merluza_PENDING.png" # Will need to update this after generation
}

# Copy images first (re-run copy to be sure)
source_dir = r"C:\Users\Tercio\.gemini\antigravity\brain\0342571e-17c9-4b83-9de5-060d3959b052"
dest_dir = r"c:\vts-site-python\pizzaria\static\uploads"

# Update DB
conn = sqlite3.connect(r'c:\vts-site-python\pizzaria\instance\pizzaria.db')
cursor = conn.cursor()

print("Updating Database...")
for produto, img_file in image_map.items():
    if "PENDING" in img_file: continue
    
    img_path = f"/static/uploads/{img_file}"
    cursor.execute("UPDATE produtos SET foto_url = ? WHERE nome = ?", (img_path, produto))
    if cursor.rowcount > 0:
        print(f"Updated DB: {produto} -> {img_path}")
    else:
        print(f"Product not found in DB: {produto}")

conn.commit()
conn.close()

# Update JSON (just Drinks for now as Marmitex names in JSON mismatch DB)
json_path = r"c:\vts-site-python\pizzaria\cardapio.json"
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data.get("Bebidas", []):
        if item["nome"] in image_map:
            item["foto"] = f"/static/uploads/{image_map[item['nome']]}"
            print(f"Updated JSON: {item['nome']}")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("cardapio.json updated.")

except Exception as e:
    print(f"Error updating JSON: {e}")
