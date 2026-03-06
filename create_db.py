from sqlalchemy import create_engine, text
from app.config import settings
import sys

def create_database_if_not_exists():
    """
    Connects to MySQL server (without selecting a DB) and creates the database if it doesn't exist.
    """
    # Extract connection info from the full URL
    # Expected format: mysql+pymysql://user:pass@host/db_name
    db_url = settings.mysql_url
    
    if "/sesamo" not in db_url and "/db" in db_url:
         # If default config is still there, warn user but try to parse
         print("Warning: Using default config URL. Make sure this is intended.")

    # Remove the database name from the URL to connect to the server root
    if "/" in db_url.split("@")[-1]:
        server_url = db_url.rsplit("/", 1)[0]
        db_name = db_url.rsplit("/", 1)[1]
    else:
        print("Error parsing database URL")
        return

    print(f"Connecting to server: {server_url}")
    print(f"Target database: {db_name}")

    engine = create_engine(server_url)

    try:
        with engine.connect() as conn:
            # Create database if not exists
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"Database '{db_name}' created or already exists.")
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    create_database_if_not_exists()
