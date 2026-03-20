from fastapi import FastAPI, HTTPException, Depends, status, Path
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Dict
import uuid

app = FastAPI(title="Gestión de Reservas API")

security = HTTPBasic()

# In-memory "database"
reservations_db: Dict[str, dict] = {}

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != "rest123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

class ReservationBase(BaseModel):
    cliente_nombre: str = Field(..., min_length=6, description="Nombre del cliente (mínimo 6 caracteres)", examples=["Juan Perez"])
    fecha_reserva: str = Field(..., description="Fecha de la reserva (Ejemplo: 2026-10-15 14:30)", examples=["2026-10-15 14:30"])
    numero_personas: int = Field(..., ge=1, le=10, description="Número de personas (entre 1 y 10)", examples=[4])

    @field_validator('fecha_reserva')
    @classmethod
    def validate_fecha(cls, value: str):
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError('El formato de la fecha debe ser YYYY-MM-DD HH:MM (Ejemplo: 2026-10-15 14:30)')
            
        if parsed_date <= datetime.now():
            raise ValueError('La fecha de la reserva debe ser en el futuro.')
        
        # Validar horario: 8:00 am a 10:00 pm (22:00)
        time = parsed_date.time()
        if time.hour < 8 or time.hour > 22 or (time.hour == 22 and time.minute > 0):
            raise ValueError('La reserva debe ser entre las 8:00 am y las 10:00 pm.')
        
        # Validar domingo (weekday() retorna 6 para domingo)
        if parsed_date.weekday() == 6:
            raise ValueError('No se permiten reservas en domingo.')
            
        return value

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(ReservationBase):
    pass

class ReservationResponse(ReservationBase):
    id: str
    estado: str

# 1. Crear Reserva (POST)
@app.post("/reservas", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def crear_reserva(reserva: ReservationCreate):
    reserva_id = str(uuid.uuid4())
    nueva_reserva = {
        "id": reserva_id,
        "cliente_nombre": reserva.cliente_nombre,
        "fecha_reserva": reserva.fecha_reserva,
        "numero_personas": reserva.numero_personas,
        "estado": "Pendiente"
    }
    reservations_db[reserva_id] = nueva_reserva
    return nueva_reserva

# 2. Listar Reservas (GET) - RUTAS PROTEGIDAS
@app.get("/reservas", response_model=List[ReservationResponse])
def listar_reservas(username: str = Depends(get_current_user)):
    return list(reservations_db.values())

# 3. Consultar por ID (GET)
@app.get("/reservas/{reserva_id}", response_model=ReservationResponse)
def consultar_reserva(reserva_id: str = Path(..., description="ID de la reserva")):
    if reserva_id not in reservations_db:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reservations_db[reserva_id]

# 4. Actualizar toda la Reserva (PUT)
@app.put("/reservas/{reserva_id}", response_model=ReservationResponse)
def actualizar_reserva(reserva_id: str, reserva: ReservationUpdate):
    if reserva_id not in reservations_db:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    reserva_actualizada = {
        "id": reserva_id,
        "cliente_nombre": reserva.cliente_nombre,
        "fecha_reserva": reserva.fecha_reserva,
        "numero_personas": reserva.numero_personas,
        "estado": reservations_db[reserva_id]["estado"] # Mantener el estado actual
    }
    reservations_db[reserva_id] = reserva_actualizada
    return reserva_actualizada

# 5. Confirmar Reserva (PATCH)
@app.patch("/reservas/{reserva_id}/confirmar", response_model=ReservationResponse)
def confirmar_reserva(reserva_id: str):
    if reserva_id not in reservations_db:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    reservations_db[reserva_id]["estado"] = "Confirmada"
    return reservations_db[reserva_id]

# 6. Cancelar Reserva (DELETE) - RUTAS PROTEGIDAS
@app.delete("/reservas/{reserva_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_reserva(reserva_id: str, username: str = Depends(get_current_user)):
    if reserva_id not in reservations_db:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    # Podría ser logic delete o borrarlo de verdad. Como es DELETE -> borrar.
    del reservations_db[reserva_id]
    return None
