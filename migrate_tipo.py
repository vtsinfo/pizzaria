import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'instance', 'pizzaria.db')

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Checking if column 'tipo' exists...")
        cursor.execute("PRAGMA table_info(ingredientes)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'tipo' not in columns:
            print("Adding column 'tipo'...")
            cursor.execute("ALTER TABLE ingredientes ADD COLUMN tipo VARCHAR(20) DEFAULT 'insumo'")
            conn.commit()
            print("Migration successful: Added 'tipo' column.")
        else:
            print("Column 'tipo' already exists. Skipping.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
