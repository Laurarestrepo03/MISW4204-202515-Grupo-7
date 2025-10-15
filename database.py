from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# URL de conexión a PostgreSQL LOCAL (Windows)
# Usuario: postgres
# Password: Hecuba33!
# Database: anb (se creará automáticamente si no existe)
URL_DATABASE = 'postgresql+psycopg://postgres:Hecuba33!@localhost:5432/anb'

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
