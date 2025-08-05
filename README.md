# 🔐 Simple Auth API

Una API de autenticación completa construida con FastAPI, que proporciona autenticación JWT, registro de usuarios, verificación de email y integración con Google OAuth.

## ✨ Características

- 🔐 **Autenticación JWT** con tokens seguros
- 👤 **Registro de usuarios** con validación de contraseñas
- 📧 **Verificación de email** (simulada para desarrollo)
- 🔑 **Reset de contraseña** (simulada para desarrollo)
- 🌐 **Google OAuth** (preparado para integración)
- 📊 **Logging estructurado** con structlog
- 📚 **Documentación automática** con Swagger UI
- 🗄️ **Base de datos SQLite** (desarrollo) / PostgreSQL (producción)
- 🧪 **Tests unitarios** y de integración
- 🚀 **Despliegue fácil** con Docker y múltiples plataformas

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.11+
- pip
- git

### Instalación

```bash
# Clonar repositorio
git clone <repository-url>
cd simple-auth

# Crear entorno virtual
python -m venv venv

# Activar entorno (macOS/Linux)
source venv/bin/activate

# Activar entorno (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración

```bash
# Copiar archivo de configuración
cp env.example .env

# Editar variables de entorno (opcional)
nano .env
```

### Ejecutar

```bash
# Opción 1: Usar script personalizado
python run.py

# Opción 2: Usar uvicorn directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

### Verificar Instalación

```bash
# Health check
curl http://localhost:9000/health

# Documentación interactiva
open http://localhost:9000/docs
```

## 📚 Documentación

### 📖 Documentación Completa

La documentación está organizada por audiencia:

- **[📖 Guía de Usuario](docs/USER_GUIDE.md)** - Cómo usar la API, ejemplos de integración
- **[👨‍💻 Guía del Desarrollador](docs/DEVELOPER_GUIDE.md)** - Arquitectura, patrones de código
- **[🔧 Documentación Técnica](docs/API_DOCUMENTATION.md)** - Endpoints detallados, modelos de datos
- **[🚀 Guía de Despliegue](docs/DEPLOYMENT_GUIDE.md)** - Despliegue en múltiples plataformas
- **[📋 Índice de Documentación](docs/README.md)** - Navegación completa

### 🔗 Enlaces Rápidos

- **Documentación Interactiva:** http://localhost:9000/docs
- **OpenAPI Schema:** http://localhost:9000/openapi.json
- **Health Check:** http://localhost:9000/health

## 🔌 Endpoints Principales

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/auth/login` | Login con email y contraseña |
| `POST` | `/auth/register/email` | Registro con email |
| `POST` | `/auth/register/google` | Registro con Google OAuth |
| `GET` | `/auth/me` | Obtener información del usuario |
| `PUT` | `/auth/me` | Actualizar información del usuario |

### Utilidades

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/health` | Health check del servicio |
| `GET` | `/docs` | Documentación interactiva |

### 🔐 **Usuario por Defecto**

Para desarrollo, se crea automáticamente un usuario administrador:

- **Email:** `admin@example.com`
- **Contraseña:** Configurable via `ADMIN_PASSWORD` (por defecto: `ChangeMe123!`)

> ⚠️ **IMPORTANTE:** Cambia la contraseña del admin en producción usando la variable de entorno `ADMIN_PASSWORD`

## ⚙️ Configuración

### 🔧 **Variables de Entorno**

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | URL de la base de datos | `sqlite:///./test.db` |
| `SECRET_KEY` | Clave secreta para JWT | `CHANGE_THIS_IN_PRODUCTION_USE_ENV_VAR` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración de tokens | `30` |
| `EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS` | Vida útil de tokens de email | `24` |
| `FRONTEND_URL` | URL del frontend | `http://localhost:3000` |
| `GOOGLE_CLIENT_ID` | ID de cliente de Google OAuth | `""` |
| `GOOGLE_CLIENT_SECRET` | Secreto de cliente de Google OAuth | `""` |
| `ADMIN_PASSWORD` | Contraseña del usuario admin | `ChangeMe123!` |
| `HOST` | Host del servidor | `0.0.0.0` |
| `PORT` | Puerto del servidor | `9000` |
| `RELOAD` | Recarga automática | `true` |

> ⚠️ **SEGURIDAD:** Cambia `SECRET_KEY` y `ADMIN_PASSWORD` en producción

### Ejemplo de Uso

```bash
# Login
curl -X POST http://localhost:9000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "ChangeMe123!"}'

# Usar token
curl -X GET http://localhost:9000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🏗️ Estructura del Proyecto

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
├── docs/                       # Documentación completa
├── tests/                      # Tests unitarios e integración
├── requirements.txt            # Dependencias Python
├── run.py                     # Script de inicio
├── env.example                # Ejemplo de variables de entorno
├── .gitignore                 # Archivos ignorados por Git
└── README.md                  # Este archivo
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=app

# Tests específicos
pytest tests/unit/test_auth.py
```

## 🐳 Docker

### Construir y Ejecutar

```bash
# Construir imagen
docker build -t simple-auth .

# Ejecutar contenedor
docker run -p 9000:9000 simple-auth

# Con Docker Compose
docker-compose up -d
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "9000:9000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/auth_db
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=auth_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
```

## 🚀 Despliegue

### Plataformas Soportadas

- **Heroku** - Despliegue directo desde Git
- **AWS (EC2 + RDS)** - Infraestructura escalable
- **Google Cloud Platform** - App Engine y Cloud Run
- **DigitalOcean** - Droplets y App Platform
- **Docker** - Contenedores portables

### Variables de Producción

```env
DATABASE_URL=postgresql://user:password@host:5432/db
SECRET_KEY=your-very-secure-secret-key-at-least-32-characters
LOG_LEVEL=INFO
JSON_LOGS=true
```

## 🔧 Desarrollo

### Comandos Útiles

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar con reload
python run.py

# Verificar sintaxis
python -m py_compile app/main.py

# Formatear código
black app/
isort app/

# Linting
flake8 app/
```

### Estructura de Commits

Usar [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add user registration endpoint
fix: resolve authentication token issue
docs: update API documentation
test: add unit tests for auth service
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

### Estándares de Código

- Usar **Black** para formateo
- Usar **isort** para imports
- Usar **flake8** para linting
- Escribir **tests** para nuevas funcionalidades
- Documentar **funciones y clases**

## 📊 Estado del Proyecto

| Componente | Estado | Versión |
|------------|--------|---------|
| API Core | ✅ Completo | v1.0.0 |
| Autenticación JWT | ✅ Completo | v1.0.0 |
| Registro de Usuarios | ✅ Completo | v1.0.0 |
| Google OAuth | 🔄 Preparado | v1.0.0 |
| Documentación | ✅ Completo | v1.0.0 |
| Tests | 🔄 En desarrollo | v1.0.0 |
| Docker | ✅ Completo | v1.0.0 |

## 🐛 Problemas Conocidos

### Soluciones Comunes

1. **Error de importación de Google OAuth:**
   ```bash
   pip install google-auth requests
   ```

2. **Error de base de datos:**
   ```bash
   # Verificar que la BD esté inicializada
   python -c "from app.core.init_db import init_db; init_db()"
   ```

3. **Puerto en uso:**
   ```bash
   # Cambiar puerto en .env o usar otro puerto
   PORT=9001 python run.py
   ```

## 📞 Soporte

### Recursos de Ayuda

- **Documentación:** [docs/](docs/)
- **Issues:** Reportar problemas en GitHub
- **Discussions:** Preguntas y discusiones en GitHub

### Reportar Problemas

Cuando reportes un problema, incluye:

- **Versión de Python:** `python --version`
- **Sistema operativo:** `uname -a` (Linux/Mac) o `systeminfo` (Windows)
- **Comando que falló:** El comando exacto que ejecutaste
- **Error completo:** El mensaje de error completo
- **Pasos para reproducir:** Lista paso a paso

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM para Python
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Validación de datos
- [JWT](https://jwt.io/) - Tokens de autenticación
- [Structlog](https://www.structlog.org/) - Logging estructurado

---

**¿Te gustó este proyecto?** ⭐ Considera darle una estrella si te fue útil.

**¿Encontraste un error?** 🐛 Por favor, abre un issue para que podamos mejorarlo.