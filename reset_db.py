"""
Script para REINICIAR la base de datos 'anb' en PostgreSQL local
⚠️ ADVERTENCIA: Este script BORRARÁ todos los datos existentes
"""
import psycopg
from psycopg import sql
from db_utils import get_connection, create_tables, create_indexes, DB_NAME

print("⚠️  ADVERTENCIA: Este script BORRARÁ la base de datos 'anb' y todos sus datos")
print("=" * 60)

# Confirmación
respuesta = input("\n¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): ")
if respuesta.upper() != "SI":
    print("\n❌ Operación cancelada")
    exit(0)

print("\n🔧 Reiniciando base de datos...")
print("=" * 60)

# Paso 1: Borrar la base de datos si existe
print("\n1. Borrando base de datos 'anb' existente...")
try:
    conn = get_connection("postgres")
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    
    if cursor.fetchone():
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{DB_NAME}'
            AND pid <> pg_backend_pid()
        """)
        
        cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(DB_NAME)))
        print(f"   ✅ Base de datos '{DB_NAME}' borrada exitosamente")
    else:
        print(f"   ℹ️  La base de datos '{DB_NAME}' no existe")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Paso 2: Crear la base de datos nuevamente
print("\n2. Creando base de datos 'anb'...")
try:
    conn = get_connection("postgres")
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
    print(f"   ✅ Base de datos '{DB_NAME}' creada exitosamente")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Paso 3: Crear las tablas
print("\n3. Creando tablas...")
try:
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    
    create_tables(cursor)
    create_indexes(cursor)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 ¡BASE DE DATOS REINICIADA EXITOSAMENTE!")
    print("=" * 60)
    print("\n✅ Base de datos: anb (NUEVA - sin datos)")
    print("✅ Tablas creadas: users, videos")
    print("✅ Índices creados")
    print("\n🚀 La base de datos está lista para usar")
    print("=" * 60)
    
except Exception as e:
    print(f"   ❌ Error creando tablas: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
