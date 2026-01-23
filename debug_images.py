import sqlite3
import os

db_path = r'c:\vts-site-python\pizzaria\instance\pizzaria.db'
uploads_dir = r'c:\vts-site-python\pizzaria\static\uploads'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

products_to_check = [
    "Frango Assado",
    "Frango à Parmegiana",
    "Picanha Assada",
    "Filé de Merluza"
]

print("--- Database Check ---")
for p in products_to_check:
    cursor.execute("SELECT id, nome, foto_url FROM produtos WHERE nome = ?", (p,))
    row = cursor.fetchone()
    if row:
        print(f"Product: {row[1]}, Foto Path in DB: {row[2]}")
        if row[2]:
            filename = os.path.basename(row[2])
            full_path = os.path.join(uploads_dir, filename)
            exists = os.path.exists(full_path)
            print(f"  File '{filename}' exists in uploads? {exists}")
    else:
        print(f"Product '{p}' NOT FOUND in DB")

print("\n--- Listing Uploads Check ---")
try:
    files = os.listdir(uploads_dir)
    print(f"Total files in uploads: {len(files)}")
    # Print recent files
    print("Recent files:")
    for f in sorted(files, key=lambda x: os.path.getmtime(os.path.join(uploads_dir, x)), reverse=True)[:5]:
        print(f"  {f}")
except Exception as e:
    print(f"Error listing uploads: {e}")

conn.close()
