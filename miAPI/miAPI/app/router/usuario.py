
from fastapi import FastAPI, status, HTTPException, Depends, APIRouter
from flask import app
from app.models.usuario import crear_usuario    
from app.data.database import usuarios
from app.security.auth import verificar_peticion

router = APIRouter(
    prefix="/v1/usuarios", 
    tags=["HTTP CRUD"]
)

@router.get("/")
async def leer_usuarios():
    # Devuelve el arreglo completo y el tamaño de la lista
    return {"total": len(usuarios), "usuarios": usuarios}
# POST para registrar un nuevo usuario (Create), con código 201 en caso de éxito

@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_usuario(usuario: crear_usuario):
    # Se itera sobre todos los diccionarios de usuarios
    for usr in usuarios:
        # Se verifica que no exista previamente el ID a insertar
        if usr["id"] == usuario.id:
            raise HTTPException(status_code=400, detail="El id ya existe")
        
        # En esta iteración de prueba se inserta y devuelve una respuesta de éxito de inmediato
        usuarios.append(usuario)
        return{
            "mensaje":"Usuario Creado",
            "Usuario": usuario
        }
        
    usuarios.append(usuario)
    return{
        "mensaje":"Usuario Creado",
        "Datos nuevos": usuario,
    }


# PUT para sobreescribir todos los datos de un usuario dado su Id (Update)
@router.put("/")
async def actualizar_usuario(id: int, usuario_actualizado: dict):
    # Itera tomando posición del índice y elemento de la lista
    for index, usr in enumerate(usuarios):
        # Valida que sea el objeto solicitado por su Id
        if usr["id"] == id:
            # Reemplaza todo el contenido existente en la misma posición de la lista
            usuarios[index] = usuario_actualizado
            return usuarios[index]
    # Arroja 404 No Encontrado si recorre todo y no encaja ningún Id
    raise HTTPException(status_code=404, detail="Usuario no encontrado")
# PATCH para combinar/fusionar ciertos datos en un usuario dada si Id (Update parcial)

@router.patch("/", status_code=status.HTTP_200_OK)
async def actualizar_parcial_usuario(id: int, usuario_actualizado: dict):
    for index, usr in enumerate(usuarios):
        if usr["id"] == id:
            # Utiliza la función nativa update de dicts de python para pisar solo lo que haya llegado de parametro
            usr.update(usuario_actualizado)
            return usr
    # Si no localiza la id, retorna 404
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

# DELETE para quitar por completo a un usuario. Requiere que se pase el sistema de `Depends(verificar_peticion)` dictado anteriormente, lo que pide Basic Auth.
@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def eliminar_usuario(id: int, usuarioAuth: str = Depends(verificar_peticion)):
    # Recorrer buscando posición a quitar
    for index, usr in enumerate(usuarios):
        if usr["id"] == id:
            # Elimina en el índice encontrado de la lista
            usuarios.pop(index)
            # Emite un informe confirmando la eliminación, e inyectando la variable `usuarioAuth` (que sería "Fernando" si salió bien la auth)
            return {"mensaje": f"Usuario eliminado por {usuarioAuth}"}
    # En caso de no existir, se emite excepción
    raise HTTPException(status_code=404, detail="Usuario no encontrado")