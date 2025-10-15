"""
Script para crear la base de datos 'anb' y las tablas en PostgreSQL local
"""
import psycopg
from psycopg import sql

# Credenciales
ADMIN_USER = "postgres"
ADMIN_PASSWORD = "Hecuba33!"
DB_NAME = "anb"

print("🔧 Creando base de datos y tablas en PostgreSQL local...")
print("=" * 60)

# Paso 1: Crear la base de datos
print("\n1. Creando base de datos 'anb'...")
try:
    # Conectarse a la base de datos 'postgres' (siempre existe)
    conn = psycopg.connect(
        host="localhost",
        port=5432,
        dbname="postgres",
        user=ADMIN_USER,
        password=ADMIN_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Verificar si la base de datos ya existe
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    
    if cursor.fetchone():
        print(f"   ⚠️  La base de datos '{DB_NAME}' ya existe")
    else:
        # Crear la base de datos
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
        print(f"   ✅ Base de datos '{DB_NAME}' creada exitosamente")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Paso 2: Crear las tablas
print("\n2. Creando tablas...")
try:
    # Conectarse a la nueva base de datos
    conn = psycopg.connect(
        host="localhost",
        port=5432,
        dbname=DB_NAME,
        user=ADMIN_USER,
        password=ADMIN_PASSWORD
    )
    cursor = conn.cursor()
    
    # Crear tabla users
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
    
    # Crear tabla videos
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
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    print("   ✅ Tabla 'videos' creada")
    
    # Crear índices
    print("   - Creando índices...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
    print("   ✅ Índices creados")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 ¡TODO CONFIGURADO EXITOSAMENTE!")
    print("=" * 60)
    print("\n✅ Base de datos: anb")
    print("✅ Tablas creadas: users, videos")
    print("✅ Índices creados")
    print("\n🚀 Ahora puedes iniciar el servidor:")
    print("   uvicorn main:app --reload")
    print("\n📝 Y probar en Postman:")
    print("   POST http://localhost:8000/api/auth/signup")
    print("=" * 60)
    
except Exception as e:
    print(f"   ❌ Error creando tablas: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
