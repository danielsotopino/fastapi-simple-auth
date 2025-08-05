# Simple Auth API - Documentación Técnica

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Endpoints de la API](#endpoints-de-la-api)
4. [Autenticación](#autenticación)
5. [Modelos de Datos](#modelos-de-datos)
6. [Configuración](#configuración)
7. [Despliegue](#despliegue)
8. [Troubleshooting](#troubleshooting)

## 🎯 Descripción General

Simple Auth API es una aplicación de autenticación construida con FastAPI que proporciona:

- **Autenticación JWT** con tokens seguros
- **Registro de usuarios** con validación de contraseñas
- **Verificación de email** (simulada para desarrollo)
- **Reset de contraseña** (simulada para desarrollo)
- **Google OAuth** (preparado para integración)
- **Logging estructurado** con structlog
- **Documentación automática** con Swagger UI

## 🏗️ Arquitectura

### Estructura del Proyecto

```
simple-auth/
├── app/
│   ├── core/                    # Configuración central
│   │   ├── database.py         # Configuración de BD
│   │   ├── security.py         # JWT y hashing
│   │   └── init_db.py          # Inicialización de BD
│   ├── endpoints/               # Controladores de API
│   │   └── auth.py             # Endpoints de autenticación
│   ├── middleware/              # Middleware personalizado
│   │   └── logging_middleware.py
│   ├── models/                  # Modelos SQLAlchemy
│   │   ├── user.py
│   │   ├── country.py
│   │   ├── education_area.py
│   │   └── verification_token.py
│   ├── schemas/                 # Esquemas Pydantic
│   │   ├── auth.py
│   │   ├── base.py
│   │   ├── master_tables.py
│   │   └── subscription.py
│   ├── services/                # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── email_service.py
│   │   └── subscription_service.py
│   ├── config.py               # Configuración de la app
│   ├── dependencies.py         # Dependencias de FastAPI
│   └── main.py                 # Punto de entrada
├── tests/                      # Tests unitarios e integración
├── docs/                       # Documentación
├── requirements.txt            # Dependencias Python
├── run.py                     # Script de inicio
└── README.md                  # Documentación principal
```

### Flujo de Autenticación

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AuthService
    participant Database
    participant EmailService

    Client->>API: POST /auth/login
    API->>AuthService: authenticate_user()
    AuthService->>Database: query user
    Database-->>AuthService: user data
    AuthService->>AuthService: verify_password()
    AuthService->>AuthService: create_access_token()
    AuthService-->>API: JWT token
    API-->>Client: {access_token, user_data}

    Client->>API: POST /auth/register/email
    API->>AuthService: register_user_email()
    AuthService->>Database: create user
    AuthService->>EmailService: send_verification_email()
    EmailService-->>AuthService: email sent
    AuthService-->>API: user created
    API-->>Client: {user_data}
```

## 🔌 Endpoints de la API

### Base URL
```
http://localhost:9000
```

### Autenticación

#### POST /auth/login
**Descripción:** Autenticar usuario con email y contraseña

**Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "Admin123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "1",
  "user_type": "ADMIN"
}
```

**Response (401):**
```json
{
  "detail": "Incorrect email or password"
}
```

#### POST /auth/register/email
**Descripción:** Registrar nuevo usuario con email y contraseña

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "country_id": 1,
  "education_area_id": 1,
  "user_type": "TEACHER"
}
```

**Response (201):**
```json
{
  "id": 2,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "TEACHER",
  "is_active": false,
  "is_oauth_user": false,
  "phone": "+1234567890",
  "country": null,
  "education_area": null,
  "created_at": "2025-08-04T23:35:05",
  "updated_at": "2025-08-04T23:35:05"
}
```

#### POST /auth/register/google
**Descripción:** Registrar/login con Google OAuth

**Request Body:**
```json
{
  "id_token": "google_id_token_here"
}
```

#### POST /auth/login/google-code
**Descripción:** Login con código de autorización de Google

**Request Body:**
```json
{
  "code": "google_authorization_code"
}
```

#### POST /auth/password-reset
**Descripción:** Solicitar reset de contraseña

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

#### POST /auth/password-reset/confirm
**Descripción:** Confirmar reset de contraseña

**Request Body:**
```json
{
  "token": "reset_token_here",
  "new_password": "NewSecurePass123!"
}
```

#### GET /auth/verify-email/{token}
**Descripción:** Verificar email con token

**Path Parameters:**
- `token`: Token de verificación

**Response (200):**
```json
{
  "message": "Email verified successfully",
  "user_id": 2
}
```

### Gestión de Usuario

#### GET /auth/me
**Descripción:** Obtener información del usuario autenticado

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User",
  "user_type": "ADMIN",
  "phone": null,
  "country": null,
  "education_area": null
}
```

#### PUT /auth/me
**Descripción:** Actualizar información del usuario autenticado

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "first_name": "Updated",
  "last_name": "Name",
  "phone": "+1234567890",
  "country_id": 1,
  "education_area_id": 1
}
```

### Utilidades

#### GET /health
**Descripción:** Health check del servicio

**Response (200):**
```json
{
  "status": "healthy"
}
```

## 🔐 Autenticación

### JWT Tokens

La API utiliza JWT (JSON Web Tokens) para autenticación:

**Estructura del Token:**
```json
{
  "sub": "user_id",
  "user_type": "ADMIN|TEACHER",
  "email": "user@example.com",
  "exp": 1754352610
}
```

**Configuración:**
- **Algoritmo:** HS256
- **Duración:** 30 minutos (configurable)
- **Secreto:** Configurable via `SECRET_KEY`

### Headers de Autenticación

Para endpoints protegidos, incluir:
```
Authorization: Bearer <access_token>
```

### Códigos de Error

| Código | Descripción |
|--------|-------------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

## 📊 Modelos de Datos

### User
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    user_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    google_id = Column(String(255), unique=True, nullable=True)
    is_oauth_user = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    education_area_id = Column(Integer, ForeignKey("education_areas.id"), nullable=True)
```

### VerificationToken
```python
class VerificationToken(Base):
    __tablename__ = "verification_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    purpose = Column(String(50), nullable=False)  # email_verification, password_reset
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## ⚙️ Configuración

### Variables de Entorno

Crear archivo `.env`:

```env
# Database
DATABASE_URL=sqlite:///./test.db

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS=24
FRONTEND_URL=http://localhost:3000

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Logging
LOG_LEVEL=DEBUG
JSON_LOGS=false

# Server
HOST=0.0.0.0
PORT=9000
RELOAD=true
```

### Configuración de Base de Datos

**SQLite (Desarrollo):**
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
```

**PostgreSQL (Producción):**
```python
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

### Logging

La aplicación utiliza structlog para logging estructurado:

**Configuración de Desarrollo:**
```python
configure_logging(
    log_level="DEBUG",
    json_logs=False  # Formato legible
)
```

**Configuración de Producción:**
```python
configure_logging(
    log_level="INFO",
    json_logs=True   # Formato JSON
)
```

## 🚀 Despliegue

### Desarrollo Local

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar variables de entorno:**
```bash
cp env.example .env
# Editar .env con tus configuraciones
```

3. **Ejecutar aplicación:**
```bash
python run.py
```

### Producción

1. **Usar Gunicorn:**
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:9000
```

2. **Docker (opcional):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 9000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:9000"]
```

3. **Variables de producción:**
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-very-secure-secret-key
LOG_LEVEL=INFO
JSON_LOGS=true
```

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Error de Importación de Google OAuth
**Síntoma:** `ModuleNotFoundError: No module named 'google'`

**Solución:**
```bash
pip install google-auth requests
```

#### 2. Error de Base de Datos
**Síntoma:** `NameError: name 'user' is not defined`

**Solución:** Verificar que todos los modelos estén importados en `init_db.py`

#### 3. Error de Autenticación
**Síntoma:** `401 Unauthorized`

**Solución:**
- Verificar que el token JWT sea válido
- Verificar que el token no haya expirado
- Verificar el formato del header: `Authorization: Bearer <token>`

#### 4. Error de Validación de Contraseña
**Síntoma:** `422 Validation Error`

**Solución:** La contraseña debe cumplir:
- Mínimo 8 caracteres
- Al menos una letra minúscula
- Al menos una letra mayúscula
- Al menos un número
- Al menos un símbolo especial

### Logs de Debug

Para habilitar logs detallados:

```bash
export LOG_LEVEL=DEBUG
export JSON_LOGS=false
python run.py
```

### Verificar Estado del Servicio

```bash
# Health check
curl http://localhost:9000/health

# Verificar documentación
curl http://localhost:9000/docs
```

## 📚 Recursos Adicionales

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [JWT.io](https://jwt.io/) - Para debug de tokens JWT
- [Structlog Documentation](https://www.structlog.org/)

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 