import time
from app import app
from database import db
from sqlalchemy import text

def update_schema():
    with app.app_context():
        print("Verificando schema do banco de dados...")
        engine = db.engine
        inspector = db.inspect(engine)
        
        # Unidades: Adicionar Instagram e Facebook
        columns = [col['name'] for col in inspector.get_columns('unidades')]
        print(f"Colunas existentes: {columns}")

        with engine.connect() as conn:
            if 'instagram' not in columns:
                try:
                    print("Tentando adicionar coluna 'instagram' em 'unidades'...")
                    conn.execute(text("ALTER TABLE unidades ADD COLUMN instagram VARCHAR(100)"))
                    print("Coluna 'instagram' adicionada.")
                except Exception as e:
                    print(f"Erro ao adicionar instagram: {e}")

            if 'facebook' not in columns:
                try:
                    print("Tentando adicionar coluna 'facebook' em 'unidades'...")
                    conn.execute(text("ALTER TABLE unidades ADD COLUMN facebook VARCHAR(100)"))
                    print("Coluna 'facebook' adicionada.")
                except Exception as e:
                    print(f"Erro ao adicionar facebook: {e}")
            
            conn.commit()
            
        print("Schema atualizado (ou verificado) com sucesso!")

if __name__ == "__main__":
    try:
        update_schema()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
