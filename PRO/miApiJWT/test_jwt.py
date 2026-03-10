import requests
import jwt
import time
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:5000"

# Configuraciones OAuth2 copiadas del server para generar el token expirado/tampered
SECRET_KEY = "tu_clave_secreta_muy_segura"
ALGORITHM = "HS256"

print("--- e. Pruebas Obligatorias ---\n")

# 1. Obtencion de token (Exitoso)
print("1. Intentando obtener token (Credenciales validas)...")
resp_login = requests.post(f"{BASE_URL}/token", data={"username": "Cesar", "password": "2254412"})
if resp_login.status_code == 200:
    token = resp_login.json()["access_token"]
    print(f" -> EXITO: Token obtenido. (Primeros caracteres: {token[:15]}...)")
else:
    print(f" -> FALLÓ: No se pudo obtener el token. HTTP {resp_login.status_code}")
    exit(1)

# 2. Token expirado
print("\n2. Probando Token Expirado...")
# Generamos un token que expira hace 1 minuto
expire = datetime.now(timezone.utc) - timedelta(minutes=1)
to_encode = {"sub": "Cesar", "exp": expire}
expired_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

resp_expired = requests.delete(f"{BASE_URL}/v1/usuarios/1", headers={"Authorization": f"Bearer {expired_jwt}"})
print(f" -> Respuesta: HTTP {resp_expired.status_code} - {resp_expired.json()}")

# 3. Acceso Autorizado (PUT/DELETE)
print("\n3. Probando Acceso Autorizado (con Token valido)...")
resp_auth = requests.delete(f"{BASE_URL}/v1/usuarios/1", headers={"Authorization": f"Bearer {token}"})
print(f" -> Respuesta DELETE /v1/usuarios/1: HTTP {resp_auth.status_code} - {resp_auth.json()}")

# 4. Acceso No Autorizado (Token modificado/falso)
print("\n4. Probando Acceso No Autorizado (Token manipulado/falso)...")
tampered_jwt = token[:-5] + "XXXXX"
resp_unauth = requests.delete(f"{BASE_URL}/v1/usuarios/2", headers={"Authorization": f"Bearer {tampered_jwt}"})
print(f" -> Respuesta: HTTP {resp_unauth.status_code} - {resp_unauth.json()}")

# 5. Missing Token (No cuenta con token)
print("\n5. Probando Peticion sin Token...")
resp_missing = requests.delete(f"{BASE_URL}/v1/usuarios/2")
print(f" -> Respuesta: HTTP {resp_missing.status_code} - {resp_missing.json()}")
