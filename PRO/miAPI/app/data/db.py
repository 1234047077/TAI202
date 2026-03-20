from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

#1. Definimos la URL de conexión

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/miapi")

#2. Creamos el motor de conexión
engine = create_engine(DATABASE_URL)

#3. Preparamos el gestion de sesiones
SesionLocal = sessionmaker(
    autocommit= False,
    autoflush= False,
    bind= engine
)

#4. Base declativa del modelo 
Base= declarative_base()

#5. Obtener sesiones de cada peticion
def get_db():
    db = SesionLocal()
    try:
        yield db
    finally:
        db.close()