from sqlalchemy import Column, Integer, String
# alchemy si necesia los nombres completos de los paquetes
from app.data.db import Base

#Constructor de base

class Usuario(Base):
    __tablename__ = "tb-usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    edad= Column(Integer)