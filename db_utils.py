"""
Utilidades comunes para gestión de base de datos PostgreSQL
"""
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

# Credenciales desde variables de entorno
ADMIN_USER = os.getenv('POSTGRES_USER', 'postgres')
ADMIN_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
DB_NAME = os.getenv('POSTGRES_DB', 'anb')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')


def get_connection(dbname="postgres"):
    """Crea una conexión a PostgreSQL"""
    return psycopg.connect(
        host=POSTGRES_HOST,
        port=int(POSTGRES_PORT),
        dbname=dbname,
        user=ADMIN_USER,
        password=ADMIN_PASSWORD
    )


def create_tables(cursor):
    """Crea las tablas users y videos con sus índices"""
    
    # Tabla users
    print("   - Creando tabla 'users'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            city VARCHAR(100) NOT NULL,
            country VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✅ Tabla 'users' creada")
    
    # Tabla videos
    print("   - Creando tabla 'videos'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'uploaded',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            original_url TEXT,
            processed_url TEXT,
            votes INTEGER DEFAULT 0,
            task_id VARCHAR(255),
            user_id INTEGER NOT NULL,
            player_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    print("   ✅ Tabla 'videos' creada")


def create_indexes(cursor):
    """Crea los índices necesarios"""
    print("   - Creando índices...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
    print("   ✅ Índices creados")
