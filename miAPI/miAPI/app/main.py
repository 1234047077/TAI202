from fastapi import FastAPI
from app.router.usuario import usuario, misc

app = FastAPI()

app.include_router(usuario.router)
app.include_router(misc.misc)