r"""
Instrucciones para ejecutar en Docker:

1. Abrir la terminal y navegar a la carpeta raíz del proyecto (donde está el Dockerfile):
   cd "C:\\Users\\cesar\\Desktop\\UNIVERSIDAD UPQ\\TAI202\\REPASO\\peliculas"

2. Construir la imagen de Docker:
   docker build -t api-peliculas .

3. Ejecutar el contenedor en el puerto 8000:
    docker run -d -p 8000:8000 --name peliculas_server api-peliculas

4. Acceder interactivamente a la documentación de la API en el navegador:
   http://localhost:8000/docs
"""

from datetime import date, datetime
from typing import Dict, List, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator

app = FastAPI(title="Video Club API (Películas)")

# Almacenamiento en memoria para el ejemplo académico
peliculas: Dict[int, "Pelicula"] = {}
rentas: Dict[int, "Renta"] = {}
contador_peliculas = 1
contador_rentas = 1

class Usuario(BaseModel):
    # Modelo del usuario que solicita una renta
    nombre: str = Field(..., min_length=2, max_length=100)
    correo: EmailStr

class PeliculaCrear(BaseModel):
    # Modelo de entrada para registrar películas
    titulo: str = Field(..., min_length=2, max_length=100)
    director: str = Field(..., min_length=2, max_length=100)
    fecha_estreno: date
    duracion_minutos: int = Field(..., gt=1)
    estado: Literal["disponible", "rentada"] = "disponible"

    @field_validator("fecha_estreno")
    def validar_fecha(cls, valor: date) -> date:
        # Validación de fecha: no puede ser en el futuro, ni antes del año de la primera película
        fecha_actual = datetime.now().date()
        if valor > fecha_actual:
            raise ValueError("La fecha de estreno no puede ser en el futuro")
        if valor.year < 1888:
            raise ValueError("La fecha de estreno debe ser un año válido (>= 1888)")
        return valor

class Pelicula(BaseModel):
    # Modelo que se devuelve al cliente
    id: int
    titulo: str
    director: str
    fecha_estreno: date
    duracion_minutos: int
    estado: Literal["disponible", "rentada"]

class RentaCrear(BaseModel):
    # Modelo de entrada para registrar una renta
    pelicula_id: int
    usuario: Usuario

class Renta(BaseModel):
    # Modelo que representa una renta registrada
    id: int
    pelicula_id: int
    usuario: Usuario
    estado: Literal["activa", "devuelta"]

@app.exception_handler(RequestValidationError)
async def manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Respuesta uniforme cuando faltan datos o son inválidos
    return JSONResponse(
        status_code=400,
        content={"detalle": "Datos inválidos o incompletos", "errores": exc.errors()},
    )

@app.post("/peliculas", status_code=201, response_model=Pelicula)
def registrar_pelicula(pelicula: PeliculaCrear) -> Pelicula:
    global contador_peliculas

    # Crear el registro de la película con ID interno
    nueva_pelicula = Pelicula(
        id=contador_peliculas,
        titulo=pelicula.titulo,
        director=pelicula.director,
        fecha_estreno=pelicula.fecha_estreno,
        duracion_minutos=pelicula.duracion_minutos,
        estado=pelicula.estado,
    )
    peliculas[nueva_pelicula.id] = nueva_pelicula
    contador_peliculas += 1
    return nueva_pelicula

@app.get("/peliculas", response_model=List[Pelicula])
def listar_peliculas() -> List[Pelicula]:
    # Retornar todas las películas disponibles en memoria
    return list(peliculas.values())

@app.get("/peliculas/buscar", response_model=List[Pelicula])
def buscar_pelicula(titulo: str = Query(..., min_length=2, max_length=100)) -> List[Pelicula]:
    # Buscar por coincidencia parcial en el título
    titulo_normalizado = titulo.strip().lower()
    return [
        pelicula
        for pelicula in peliculas.values()
        if titulo_normalizado in pelicula.titulo.lower()
    ]

@app.post("/rentas", status_code=201, response_model=Renta)
def registrar_renta(renta: RentaCrear) -> Renta:
    global contador_rentas

    pelicula = peliculas.get(renta.pelicula_id)
    if not pelicula:
        # Película inexistente
        raise HTTPException(status_code=400, detail="La película no existe")
    if pelicula.estado == "rentada":
        # Conflicto: la película ya está rentada
        raise HTTPException(status_code=409, detail="La película ya está rentada")

    # Registrar renta y cambiar estado de la película
    nueva_renta = Renta(
        id=contador_rentas,
        pelicula_id=renta.pelicula_id,
        usuario=renta.usuario,
        estado="activa",
    )
    rentas[nueva_renta.id] = nueva_renta
    contador_rentas += 1

    peliculas[pelicula.id] = pelicula.model_copy(update={"estado": "rentada"})
    return nueva_renta

@app.put("/rentas/{renta_id}/devolver")
def devolver_pelicula(renta_id: int) -> Dict[str, str]:
    renta = rentas.get(renta_id)
    if not renta:
        # Conflicto: la renta ya fue eliminada o no existe
        raise HTTPException(
            status_code=409, detail="El registro de renta ya no existe"
        )

    pelicula = peliculas.get(renta.pelicula_id)
    if pelicula:
        peliculas[pelicula.id] = pelicula.model_copy(update={"estado": "disponible"})

    # Marcar la renta como devuelta
    rentas[renta_id] = renta.model_copy(update={"estado": "devuelta"})
    return {"mensaje": "Película devuelta correctamente"}

@app.delete("/rentas/{renta_id}")
def eliminar_renta(renta_id: int) -> Dict[str, str]:
    renta = rentas.get(renta_id)
    if not renta:
        # Conflicto: la renta ya fue eliminada o no existe
        raise HTTPException(
            status_code=409, detail="El registro de renta ya no existe"
        )

    pelicula = peliculas.get(renta.pelicula_id)
    if pelicula:
        peliculas[pelicula.id] = pelicula.model_copy(update={"estado": "disponible"})

    # Eliminar el registro de la renta
    del rentas[renta_id]
    return {"mensaje": "Renta eliminada correctamente"}
