from datetime import datetime, time
from enum import Enum
from typing import Dict
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="API de Reservas")
security = HTTPBasic()


class EstadoReserva(str, Enum):
    pendiente = "pendiente"
    confirmada = "confirmada"
    cancelada = "cancelada"


class ReservaCreate(BaseModel):
    nombre_cliente: str = Field(min_length=6)
    fecha_reserva: datetime
    numero_personas: int = Field(ge=1, le=10)

    @field_validator("fecha_reserva")
    @classmethod
    def validar_fecha_reserva(cls, value: datetime) -> datetime:
        ahora = datetime.now(value.tzinfo)
        if value <= ahora:
            raise ValueError("La fecha de reserva debe ser futura")
        if value.weekday() == 6:
            raise ValueError("No se permiten reservas en domingo")
        hora = value.time()
        inicio = time(8, 0)
        fin = time(22, 0)
        if not (inicio <= hora <= fin):
            raise ValueError("La reserva debe ser entre las 08:00 y las 22:00")
        return value


class ReservaResponse(BaseModel):
    id: UUID
    nombre_cliente: str
    fecha_reserva: datetime
    numero_personas: int
    estado: EstadoReserva


reservas: Dict[UUID, ReservaResponse] = {}


def auth_basica(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if credentials.username != "admin" or credentials.password != "rest123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.post("/reservas", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
def crear_reserva(payload: ReservaCreate) -> ReservaResponse:
    reserva = ReservaResponse(
        id=uuid4(),
        nombre_cliente=payload.nombre_cliente,
        fecha_reserva=payload.fecha_reserva,
        numero_personas=payload.numero_personas,
        estado=EstadoReserva.pendiente,
    )
    reservas[reserva.id] = reserva
    return reserva


@app.get("/reservas", response_model=list[ReservaResponse])
def listar_reservas(_: str = Depends(auth_basica)) -> list[ReservaResponse]:
    return list(reservas.values())


@app.get("/reservas/{reserva_id}", response_model=ReservaResponse)
def obtener_reserva(reserva_id: UUID) -> ReservaResponse:
    reserva = reservas.get(reserva_id)
    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada")
    return reserva


@app.patch("/reservas/{reserva_id}/confirmar", response_model=ReservaResponse)
def confirmar_reserva(reserva_id: UUID) -> ReservaResponse:
    reserva = reservas.get(reserva_id)
    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada")
    if reserva.estado == EstadoReserva.cancelada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede confirmar una reserva cancelada",
        )
    reserva.estado = EstadoReserva.confirmada
    return reserva


@app.patch("/reservas/{reserva_id}/cancelar", response_model=ReservaResponse)
def cancelar_reserva(reserva_id: UUID, _: str = Depends(auth_basica)) -> ReservaResponse:
    reserva = reservas.get(reserva_id)
    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva no encontrada")
    reserva.estado = EstadoReserva.cancelada
    return reserva
