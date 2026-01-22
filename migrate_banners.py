from app import app, db
from sqlalchemy import text

def migrate_banners():
    with app.app_context():
        # Check if columns exist
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(banners)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'link_url' not in columns:
                print("Adding link_url to banners...")
                conn.execute(text("ALTER TABLE banners ADD COLUMN link_url VARCHAR(255)"))
                print("Added link_url.")
                
            if 'link_text' not in columns:
                print("Adding link_text to banners...")
                conn.execute(text("ALTER TABLE banners ADD COLUMN link_text VARCHAR(50)"))
                print("Added link_text.")
                
            conn.commit()
            print("Migration complete!")

if __name__ == '__main__':
    migrate_banners()
