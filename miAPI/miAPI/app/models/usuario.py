from pydantic import BaseModel, Field

class crear_usuario(BaseModel):
    id: int = Field(..., gt=0, description="Identificador de usuario")
    nombre: str = Field(..., min_length=1, max_length=50, example="piloi")
    edad: int = Field(..., ge=1,le=123, description="Edad del usuario entre 1 y 123 años")