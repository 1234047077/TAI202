from fastapi import APIRouter, status, HTTPException, Depends
from app.data.database import usuarios
from app.models.usuario import crear_usuario
from app.security.auth import verificar_peticion

router = APIRouter(
    prefix="/v1/usuarios",
    tags=['HTTP CRUD']
)

@router.get("/")
async def leer_usuarios():
    return {"total": len(usuarios), "usuarios": usuarios}

@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_usuario_endpoint(usuario: crear_usuario):
    for usr in usuarios:
        if usr["id"] == usuario.id:
            raise HTTPException(status_code=400, detail="El id ya existe")
        usuarios.append(usuario.model_dump())
        return{
            "mensaje":"Usuario Creado",
            "Usuario": usuario.model_dump()
        }
        
    usuarios.append(usuario.model_dump())
    return{
        "mensaje":"Usuario Creado",
        "Datos nuevos": usuario.model_dump(),
    }


@router.put("/{id}")
async def actualizar_usuario(id: int, usuario_actualizado: dict):
    for index, usr in enumerate(usuarios):
        if usr["id"] == id:
            usuarios[index] = usuario_actualizado
            return usuarios[index]
    raise HTTPException(status_code=404, detail="Usuario no encontrado")
 
@router.patch("/{id}")
async def actualizar_parcial_usuario(id: int, usuario_actualizado: dict):
    for index, usr in enumerate(usuarios):
        if usr["id"] == id:
            usr.update(usuario_actualizado)
            return usr
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def eliminar_usuario(id: int, usuarioAuth: str = Depends(verificar_peticion)):
    for index, usr in enumerate(usuarios):
        if usr["id"] == id:
            usuarios.pop(index)
            return {"mensaje": f"Usuario eliminado por {usuarioAuth}"}
    raise HTTPException(status_code=404, detail="Usuario no encontrado")
