import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

print("====================================")
print("  PRUEBAS DE VALIDACIÓN DE FECHAS   ")
print("====================================\n")

# 1. Prueba Correcta
print("1. Insertando una película CORRECTA (Año 1999):")
payload_correcto = {
    "titulo": "The Matrix",
    "director": "Lana Wachowski, Lilly Wachowski",
    "fecha_estreno": "1999-03-31",
    "duracion_minutos": 136
}
res = requests.post(f"{BASE_URL}/peliculas", json=payload_correcto)
print(f" -> Estatus HTTP: {res.status_code}")
if res.status_code == 201:
    print(f" -> Éxito: {res.json()}")
else:
    print(f" -> Error devuelto: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")
print("-" * 50)


# 2. Prueba Incorrecta (Fecha menor a 1888)
print("2. Insertando una película INCORRECTA (Año 1500 - Antes del cine):")
payload_viejo = {
    "titulo": "Película Imposible",
    "director": "Leonardo Da Vinci",
    "fecha_estreno": "1500-01-01",
    "duracion_minutos": 120
}
res = requests.post(f"{BASE_URL}/peliculas", json=payload_viejo)
print(f" -> Estatus HTTP: {res.status_code} (Esperado: 400 o 422)")
print(f" -> Detalles del error: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")
print("-" * 50)


# 3. Prueba Incorrecta (Fecha en el futuro)
hoy = datetime.now()
futuro = hoy + timedelta(days=365)
fecha_futura = futuro.strftime("%Y-%m-%d")

print(f"3. Insertando una película INCORRECTA (Año en el futuro: {fecha_futura}):")
payload_futuro = {
    "titulo": "Avatar 5",
    "director": "James Cameron",
    "fecha_estreno": fecha_futura,
    "duracion_minutos": 180
}
res = requests.post(f"{BASE_URL}/peliculas", json=payload_futuro)
print(f" -> Estatus HTTP: {res.status_code} (Esperado: 400 o 422)")
print(f" -> Detalles del error: {json.dumps(res.json(), indent=2, ensure_ascii=False)}")
print("====================================\n")
