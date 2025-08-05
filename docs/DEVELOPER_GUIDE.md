# Guía del Desarrollador - Simple Auth API

## 🎯 Objetivo

Esta guía está diseñada para desarrolladores que quieren entender, modificar o extender la Simple Auth API.

## 🏗️ Arquitectura del Sistema

### Patrón de Diseño

La aplicación sigue el patrón **Clean Architecture** con las siguientes capas:

1. **Controllers (Endpoints)** - Manejo de requests HTTP
2. **Services** - Lógica de negocio
3. **Models** - Entidades de base de datos
4. **Schemas** - Validación de datos
5. **Core** - Configuración y utilidades

### Flujo de Datos

```
HTTP Request → Endpoint → Service → Model → Database
                ↓
HTTP Response ← Schema ← Service ← Model ← Database
```

## 🔧 Configuración del Entorno de Desarrollo

### 1. Configuración del Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (macOS/Linux)
source venv/bin/activate

# Activar entorno (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración de Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar variables según necesidad
nano .env
```

### 3. Configuración de la Base de Datos

**Para desarrollo (SQLite):**
```env
DATABASE_URL=sqlite:///./test.db
```

**Para producción (PostgreSQL):**
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## 📁 Estructura del Código

### Core Module (`app/core/`)

#### `database.py`
Configuración de SQLAlchemy y sesiones de base de datos.

```python
# Ejemplo de uso
from app.core.database import get_db, SessionLocal

# En un endpoint
def my_endpoint(db: Session = Depends(get_db)):
    # Usar db para operaciones de base de datos
    pass
```

#### `security.py`
Funciones de seguridad: JWT, hashing de contraseñas, verificación.

```python
# Ejemplo de uso
from app.core.security import create_access_token, verify_password

# Crear token
token = create_access_token(data={"sub": user.id})

# Verificar contraseña
is_valid = verify_password(plain_password, hashed_password)
```

#### `init_db.py`
Inicialización de la base de datos y datos de ejemplo.

### Models (`app/models/`)

Los modelos definen la estructura de la base de datos usando SQLAlchemy.

#### Ejemplo de Modelo

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    user_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    is_oauth_user = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    
    # Relationships
    country = relationship("Country", back_populates="users")
    verification_tokens = relationship("VerificationToken", back_populates="user", cascade="all, delete-orphan")
```

#### Convenciones de Modelos

- Usar `__tablename__` en plural
- Incluir `created_at` y `updated_at` para auditoría
- Usar `server_default=func.now()` para timestamps automáticos
- Definir relaciones con `relationship()`

### Schemas (`app/schemas/`)

Los schemas definen la validación de datos de entrada y salida usando Pydantic.

#### Ejemplo de Schema

```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    class Config:
        from_attributes = True  # Para Pydantic v2
```

#### Convenciones de Schemas

- Usar `Request` para datos de entrada
- Usar `Response` para datos de salida
- Usar `EmailStr` para emails
- Incluir validaciones con `@field_validator`

### Services (`app/services/`)

Los servicios contienen la lógica de negocio.

#### Ejemplo de Service

```python
class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    async def authenticate_user(self, login_request: LoginRequest):
        # Lógica de autenticación
        pass
```

#### Convenciones de Services

- Usar `async def` para operaciones asíncronas
- Manejar errores con `HTTPException`
- Usar logging estructurado
- Retornar datos tipados

### Endpoints (`app/endpoints/`)

Los endpoints manejan las requests HTTP.

#### Ejemplo de Endpoint

```python
@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(request)
```

#### Convenciones de Endpoints

- Usar `response_model` para validación de salida
- Usar `Depends()` para inyección de dependencias
- Manejar errores con códigos HTTP apropiados
- Documentar con docstrings

## 🔐 Autenticación y Autorización

### JWT Tokens

La aplicación usa JWT para autenticación:

```python
# Crear token
token = create_access_token(
    data={"sub": str(user.id), "user_type": user.user_type}
)

# Verificar token
payload = verify_token(token)
user_id = payload.get("sub")
```

### Middleware de Autenticación

```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    # Verificar token y obtener usuario
    pass
```

### Uso en Endpoints

```python
@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user = Depends(get_current_user)):
    return UserMeResponse.model_validate(current_user, from_attributes=True)
```

## 📊 Logging

### Configuración

La aplicación usa structlog para logging estructurado:

```python
import structlog

logger = structlog.get_logger(__name__)

# Logging con contexto
logger.info("User logged in", user_id=user.id, email=user.email)
```

### Middleware de Logging

El `LoggingMiddleware` registra automáticamente:

- Requests entrantes
- Responses salientes
- Errores
- Métricas de rendimiento

### Niveles de Log

- `DEBUG`: Información detallada para desarrollo
- `INFO`: Información general de la aplicación
- `WARNING`: Advertencias que no son errores
- `ERROR`: Errores que afectan la funcionalidad
- `CRITICAL`: Errores críticos del sistema

## 🧪 Testing

### Estructura de Tests

```
tests/
├── unit/           # Tests unitarios
│   ├── test_auth.py
│   └── test_google_oauth.py
└── integration/    # Tests de integración
    └── test_auth_api.py
```

### Ejemplo de Test

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "Admin123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/unit/test_auth.py

# Con cobertura
pytest --cov=app

# Verbose
pytest -v
```

## 🔄 Migraciones de Base de Datos

### Usando Alembic

```bash
# Crear migración
alembic revision --autogenerate -m "Add new table"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

### Configuración de Alembic

```ini
# alembic.ini
sqlalchemy.url = sqlite:///./test.db
```

## 🚀 Despliegue

### Desarrollo Local

```bash
# Con reload automático
python run.py

# Con uvicorn directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

### Producción

```bash
# Con Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:9000

# Con Docker
docker build -t simple-auth .
docker run -p 9000:9000 simple-auth
```

## 🔧 Debugging

### Logs de Debug

```bash
export LOG_LEVEL=DEBUG
export JSON_LOGS=false
python run.py
```

### Verificar Estado

```bash
# Health check
curl http://localhost:9000/health

# Documentación
curl http://localhost:9000/docs

# OpenAPI schema
curl http://localhost:9000/openapi.json
```

### Debug de JWT

```python
import jwt
from app.core.security import SECRET_KEY

# Decodificar token
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
print(payload)
```

## 📚 Mejores Prácticas

### 1. Manejo de Errores

```python
try:
    # Operación que puede fallar
    result = some_operation()
except SpecificException as e:
    logger.error("Operation failed", error=str(e))
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. Validación de Datos

```python
from pydantic import field_validator

class UserCreateRequest(BaseModel):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password too short')
        return v
```

### 3. Logging Estructurado

```python
logger.info(
    "User action",
    user_id=user.id,
    action="login",
    success=True,
    ip_address=request.client.host
)
```

### 4. Configuración

```python
from app.config import get_settings

settings = get_settings()
database_url = settings.DATABASE_URL
```

## 🐛 Troubleshooting Común

### 1. Error de Importación

**Problema:** `ModuleNotFoundError: No module named 'google'`

**Solución:**
```bash
pip install google-auth requests
```

### 2. Error de Base de Datos

**Problema:** `NameError: name 'user' is not defined`

**Solución:** Verificar imports en `init_db.py`

### 3. Error de Autenticación

**Problema:** `401 Unauthorized`

**Solución:**
- Verificar formato del token: `Bearer <token>`
- Verificar que el token no haya expirado
- Verificar que el usuario existe en la base de datos

### 4. Error de Validación

**Problema:** `422 Validation Error`

**Solución:**
- Verificar formato de email
- Verificar requisitos de contraseña
- Verificar tipos de datos

## 📖 Recursos Adicionales

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/best-practices/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Structlog Best Practices](https://www.structlog.org/en/stable/best-practices.html)

## 🤝 Contribución

### Flujo de Trabajo

1. Fork el repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Hacer cambios y commits: `git commit -m "Add nueva funcionalidad"`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Estándares de Código

- Usar **Black** para formateo
- Usar **isort** para imports
- Usar **flake8** para linting
- Escribir tests para nuevas funcionalidades
- Documentar funciones y clases

### Commits

Usar [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user registration endpoint
fix: resolve authentication token issue
docs: update API documentation
test: add unit tests for auth service
```

## 📞 Soporte

Para preguntas o problemas:

1. Revisar la documentación
2. Buscar en issues existentes
3. Crear nuevo issue con detalles completos
4. Contactar al equipo de desarrollo 