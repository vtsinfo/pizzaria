import sqlite3

db_path = r'c:\vts-site-python\pizzaria\instance\pizzaria.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in DB:", tables)

conn.close()
