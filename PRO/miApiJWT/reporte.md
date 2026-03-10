# Reporte de Implementación JWT en FastAPI

Este documento detalla los pasos realizados para migrar el proyecto de `HTTP Basic Auth` al estándar **OAuth2 usando JWT (JSON Web Tokens)**.

## a. Configuraciones OAuth2

Para poder implementar JWT en FastAPI, primero se realizaron las importaciones requeridas (`OAuth2PasswordBearer`, `OAuth2PasswordRequestForm`, `jwt`, y excepciones de validación) tras instalar las librerías necesarias (`PyJWT` y `python-multipart`). 

Se implementó la configuración principal que dicta las reglas de creación y lectura de los tokens:

```python
# Configuraciones OAuth2
SECRET_KEY = "tu_clave_secreta_muy_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```
- Se definió el string seguro para firmar los tokens (`SECRET_KEY`).
- Se definió el algoritmo base `HS256`.
- Se configuró el tiempo máximo de vida del token a `30` minutos tal como se solicitó.
- Se configuró la ruta general para obtener el token `tokenUrl="token"`.

## b. Generación de Tokens

Se implementó la lógica para generar el JWT, tomando como base el diccionario de datos del usuario y aplicando la expiración matemática (en UTC):

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```
De manera adicional, se expuso el endpoint `POST /token` (usando `OAuth2PasswordRequestForm`) para intercambiar el usuario y contraseña ("Cesar", "2254412") por el token generado con un **límite máximo de vida de 30 minutos** establecido en `access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)`.

## c. Implementación y validación de tokens

Para asegurar que al recibir un token éste proceda de manera correcta, se hizo un inyector de dependencias (Dependency Injection) usando `Depends()`.

```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no validas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    return username
```
Esta función descodifica el token en cada petición segura, revisa la firma y su tiempo de vigencia. Si el token está caducado o está mal firmado, rechaza la solicitud retornando un error `401 Unauthorized`.

## d. Protección de endpoints (PUT y DELETE)

Una vez creada la función y dependencia validadora, ésta se integró a los endpoints `PUT` y `DELETE` que requerían la nueva capa de seguridad, utilizando `Depends(get_current_user)` en los argumentos de la función de los endpoints:

```python
@app.put("/v1/usuarios/{id}", tags=['HTTP CRUD'])
async def actualizar_usuario(id: int, usuario_actualizado: dict, usuarioAuth: str = Depends(get_current_user)):
    ... # lógica interna igual
```

```python
@app.delete("/v1/usuarios/{id}", tags=['HTTP CRUD'], status_code=status.HTTP_200_OK)
async def eliminar_usuario(id: int, usuarioAuth: str = Depends(get_current_user)):
    ... # lógica interna igual
```

## e. Pruebas Obligatorias

Se automatizó una prueba integral para evidenciar que las reglas de negocio en la capa de seguridad están operando como se requiere. 

A continuación el registro de la consola luego de correr las peticiones del programa probador:

```text
--- e. Pruebas Obligatorias ---

1. Intentando obtener token (Credenciales validas)...
 -> EXITO: Token obtenido. (Primeros caracteres: eyJhbGciOiJIUzI...)

2. Probando Token Expirado...
 -> Respuesta: HTTP 401 - {'detail': 'Credenciales no validas'}

3. Probando Acceso Autorizado (con Token valido)...
 -> Respuesta DELETE /v1/usuarios/1: HTTP 200 - {'mensaje': 'Usuario eliminado por Cesar'}

4. Probando Acceso No Autorizado (Token manipulado/falso)...
 -> Respuesta: HTTP 401 - {'detail': 'Credenciales no validas'}

5. Probando Peticion sin Token...
 -> Respuesta: HTTP 401 - {'detail': 'Not authenticated'}
```

### Explicación a profundidad de las pruebas:
- **i. Token exitoso**: La petición `/token` respondió un código 200 enviando un JWT correctamente construido.
- **i. Token expirado**: Se forzó un JWT firmado con expiración atrasada a un minuto, la API respondió `401` argumentando problemas durante la decodificación.
- **ii. Acceso autorizado**: Al mandar el `Bearer` original generado para César, la API aceptó la orden `DELETE` exitosamente devolviendo un StatusCode `200`.
- **ii. Acceso no autorizado**: Al manipular maliciosamente la estructura o el cifrado de un JWT o mandando una firma errónea, la API no lo aceptó retornando un StatusCode `401`.
- **iii. No cuenta con un token**: Tratar de ejecutar una ruta protegida limpia sin headers `Authorization: Bearer` da también como resultado un rebote limpio indicando que está desautenticado (`401`).
