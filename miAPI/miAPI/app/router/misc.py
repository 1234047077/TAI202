import asyncio
from typing import option

from flask import app
from app.data.database import usuarios
from fastapi import APIRouter

misc=APIRouter(tags=["Miscelaneo"])

@misc.get("/")
async def holamundo(): 
    # Muestra un mensaje simple en formato JSON
    return {"mensaje": "Hola mundo FastAPI"}

# Endpoint para saludar con retraso asíncrono
@misc.get("/bienvenido")
async def bienvenido(): 
    # Detiene de forma asíncrona la ejecución durante 5 segundos
    await asyncio.sleep(5)
    # Realiza la respuesta una vez pasado el tiempo
    return {"mensaje": "Bienvenido a FastAPI"}
