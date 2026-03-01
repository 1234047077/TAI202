from datetime import datetime
from typing import Dict, List, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator

app = FastAPI(title="Biblioteca Digital API")

# Almacenamiento en memoria para el ejemplo académico (sin base de datos)
libros: Dict[int, "Libro"] = {}
prestamos: Dict[int, "Prestamo"] = {}
contador_libros = 1
contador_prestamos = 1


class Usuario(BaseModel):
    # Modelo del usuario que solicita un préstamo
    nombre: str = Field(..., min_length=2, max_length=100)
    correo: EmailStr


class LibroCrear(BaseModel):
    # Modelo de entrada para registrar libros
    nombre: str = Field(..., min_length=2, max_length=100)
    autor: str = Field(..., min_length=2, max_length=100)
    anio: int = Field(..., gt=1450)
    paginas: int = Field(..., gt=1)
    estado: Literal["disponible", "prestado"] = "disponible"

    @field_validator("anio")
    def validar_anio(cls, valor: int) -> int:
        # Validación extra: no permitir años futuros
        anio_actual = datetime.now().year
        if valor > anio_actual:
            raise ValueError("El año del libro no puede ser futuro")
        return valor


class Libro(BaseModel):
    # Modelo que se devuelve al cliente
    id: int
    nombre: str
    autor: str
    anio: int
    paginas: int
    estado: Literal["disponible", "prestado"]


class PrestamoCrear(BaseModel):
    # Modelo de entrada para registrar un préstamo
    libro_id: int
    usuario: Usuario


class Prestamo(BaseModel):
    # Modelo que representa un préstamo registrado
    id: int
    libro_id: int
    usuario: Usuario
    estado: Literal["activo", "devuelto"]


@app.exception_handler(RequestValidationError)
async def manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Respuesta uniforme cuando faltan datos o son inválidos
    return JSONResponse(
        status_code=400,
        content={"detalle": "Datos inválidos o incompletos", "errores": exc.errors()},
    )


@app.post("/libros", status_code=201, response_model=Libro)
def registrar_libro(libro: LibroCrear) -> Libro:
    global contador_libros

    # Crear el registro del libro con ID interno
    nuevo_libro = Libro(
        id=contador_libros,
        nombre=libro.nombre,
        autor=libro.autor,
        anio=libro.anio,
        paginas=libro.paginas,
        estado=libro.estado,
    )
    libros[nuevo_libro.id] = nuevo_libro
    contador_libros += 1
    return nuevo_libro


@app.get("/libros", response_model=List[Libro])
def listar_libros() -> List[Libro]:
    # Retornar todos los libros disponibles en memoria
    return list(libros.values())


@app.get("/libros/buscar", response_model=List[Libro])
def buscar_libro(nombre: str = Query(..., min_length=2, max_length=100)) -> List[Libro]:
    # Buscar por coincidencia parcial en el nombre
    nombre_normalizado = nombre.strip().lower()
    return [
        libro
        for libro in libros.values()
        if nombre_normalizado in libro.nombre.lower()
    ]


@app.post("/prestamos", status_code=201, response_model=Prestamo)
def registrar_prestamo(prestamo: PrestamoCrear) -> Prestamo:
    global contador_prestamos

    libro = libros.get(prestamo.libro_id)
    if not libro:
        # Libro inexistente
        raise HTTPException(status_code=400, detail="El libro no existe")
    if libro.estado == "prestado":
        # Conflicto: el libro ya está prestado
        raise HTTPException(status_code=409, detail="El libro ya está prestado")

    # Registrar préstamo y cambiar estado del libro
    nuevo_prestamo = Prestamo(
        id=contador_prestamos,
        libro_id=prestamo.libro_id,
        usuario=prestamo.usuario,
        estado="activo",
    )
    prestamos[nuevo_prestamo.id] = nuevo_prestamo
    contador_prestamos += 1

    libros[libro.id] = libro.model_copy(update={"estado": "prestado"})
    return nuevo_prestamo


@app.put("/prestamos/{prestamo_id}/devolver")
def devolver_libro(prestamo_id: int) -> Dict[str, str]:
    prestamo = prestamos.get(prestamo_id)
    if not prestamo:
        # Conflicto: el préstamo ya fue eliminado o no existe
        raise HTTPException(
            status_code=409, detail="El registro de préstamo ya no existe"
        )

    libro = libros.get(prestamo.libro_id)
    if libro:
        libros[libro.id] = libro.model_copy(update={"estado": "disponible"})

    # Marcar el préstamo como devuelto
    prestamos[prestamo_id] = prestamo.model_copy(update={"estado": "devuelto"})
    return {"mensaje": "Libro devuelto correctamente"}


@app.delete("/prestamos/{prestamo_id}")
def eliminar_prestamo(prestamo_id: int) -> Dict[str, str]:
    prestamo = prestamos.get(prestamo_id)
    if not prestamo:
        # Conflicto: el préstamo ya fue eliminado o no existe
        raise HTTPException(
            status_code=409, detail="El registro de préstamo ya no existe"
        )

    libro = libros.get(prestamo.libro_id)
    if libro:
        libros[libro.id] = libro.model_copy(update={"estado": "disponible"})

    # Eliminar el registro de préstamo
    del prestamos[prestamo_id]
    return {"mensaje": "Préstamo eliminado correctamente"}
