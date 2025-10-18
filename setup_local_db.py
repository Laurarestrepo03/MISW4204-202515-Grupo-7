"""
Script para crear la base de datos 'anb' y las tablas en PostgreSQL local
"""
import psycopg
from psycopg import sql
from db_utils import get_connection, create_tables, create_indexes, DB_NAME

print("🔧 Creando base de datos y tablas en PostgreSQL local...")
print("=" * 60)

# Paso 1: Crear la base de datos
print("\n1. Creando base de datos 'anb'...")
try:
    conn = get_connection("postgres")
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    
    if cursor.fetchone():
        print(f"   ⚠️  La base de datos '{DB_NAME}' ya existe")
    else:
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
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    
    create_tables(cursor)
    create_indexes(cursor)
    
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
