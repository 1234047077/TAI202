from fastapi import FastAPI
from app.router.usuario import router as usuario_router
from app.router.misc import misc as misc_router

app = FastAPI(
    title="Mi primer API",
    deescription="Cesar Acosta Cortez",
    version="0.1"

)

app.include_router(usuario_router)
app.include_router(misc_router)
