# Guía de Despliegue - Simple Auth API

## 🎯 Introducción

Esta guía te ayudará a desplegar la Simple Auth API en diferentes entornos, desde desarrollo local hasta producción.

## 🏠 Desarrollo Local

### Requisitos Previos

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

# Editar variables de entorno
nano .env
```

**Configuración mínima para desarrollo:**
```env
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=dev-secret-key-change-in-production
LOG_LEVEL=DEBUG
JSON_LOGS=false
HOST=0.0.0.0
PORT=9000
RELOAD=true
```

### Ejecutar

```bash
# Opción 1: Usar script personalizado
python run.py

# Opción 2: Usar uvicorn directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000

# Opción 3: Con variables de entorno
HOST=0.0.0.0 PORT=9000 python run.py
```

### Verificar Instalación

```bash
# Health check
curl http://localhost:9000/health

# Documentación
open http://localhost:9000/docs
```

## 🐳 Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 9000

# Comando por defecto
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:9000"]
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
      - SECRET_KEY=your-production-secret-key
      - LOG_LEVEL=INFO
      - JSON_LOGS=true
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=auth_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Comandos Docker

```bash
# Construir imagen
docker build -t simple-auth .

# Ejecutar contenedor
docker run -p 9000:9000 simple-auth

# Con variables de entorno
docker run -p 9000:9000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  simple-auth

# Usar Docker Compose
docker-compose up -d
```

## ☁️ Despliegue en la Nube

### Heroku

#### 1. Preparar Aplicación

```bash
# Crear Procfile
echo "web: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:\$PORT" > Procfile

# Crear runtime.txt
echo "python-3.11.13" > runtime.txt
```

#### 2. Desplegar

```bash
# Instalar Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Crear aplicación
heroku create your-app-name

# Configurar variables de entorno
heroku config:set DATABASE_URL=postgresql://...
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set LOG_LEVEL=INFO
heroku config:set JSON_LOGS=true

# Desplegar
git push heroku main

# Verificar
heroku open
```

### AWS (EC2 + RDS)

#### 1. Configurar EC2

```bash
# Conectar a instancia EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Instalar Nginx
sudo apt install nginx -y
```

#### 2. Configurar Aplicación

```bash
# Clonar repositorio
git clone <repository-url>
cd simple-auth

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install gunicorn

# Configurar variables de entorno
cp env.example .env
nano .env
```

#### 3. Configurar Nginx

```nginx
# /etc/nginx/sites-available/simple-auth
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/simple-auth /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Configurar Systemd

```ini
# /etc/systemd/system/simple-auth.service
[Unit]
Description=Simple Auth API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/simple-auth
Environment=PATH=/home/ubuntu/simple-auth/venv/bin
ExecStart=/home/ubuntu/simple-auth/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:9000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar servicio
sudo systemctl enable simple-auth
sudo systemctl start simple-auth
sudo systemctl status simple-auth
```

### Google Cloud Platform (GCP)

#### 1. App Engine

```yaml
# app.yaml
runtime: python311
entrypoint: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT

env_variables:
  DATABASE_URL: "your-database-url"
  SECRET_KEY: "your-secret-key"
  LOG_LEVEL: "INFO"
  JSON_LOGS: "true"
```

```bash
# Desplegar
gcloud app deploy
```

#### 2. Cloud Run

```bash
# Construir y desplegar
gcloud run deploy simple-auth \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="your-database-url",SECRET_KEY="your-secret-key"
```

### DigitalOcean

#### 1. Droplet

```bash
# Conectar a droplet
ssh root@your-droplet-ip

# Seguir pasos similares a AWS EC2
# Instalar Python, Nginx, configurar aplicación
```

#### 2. App Platform

```yaml
# .do/app.yaml
name: simple-auth
services:
- name: api
  source_dir: /
  github:
    repo: your-username/simple-auth
    branch: main
  run_command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
  - key: SECRET_KEY
    value: your-secret-key
```

## 🗄️ Configuración de Base de Datos

### PostgreSQL

#### Instalación Local

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Crear base de datos
sudo -u postgres createdb auth_db
sudo -u postgres createuser auth_user
sudo -u postgres psql -c "ALTER USER auth_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;"
```

#### Configuración de Variables

```env
DATABASE_URL=postgresql://auth_user:password@localhost:5432/auth_db
```

### Migraciones

```bash
# Instalar Alembic
pip install alembic

# Inicializar
alembic init alembic

# Configurar alembic.ini
# sqlalchemy.url = postgresql://auth_user:password@localhost:5432/auth_db

# Crear migración
alembic revision --autogenerate -m "Initial migration"

# Aplicar migraciones
alembic upgrade head
```

## 🔒 Configuración de Seguridad

### Variables de Entorno de Producción

```env
# Base de datos
DATABASE_URL=postgresql://user:password@host:5432/db

# JWT
SECRET_KEY=your-very-secure-secret-key-at-least-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
JSON_LOGS=true

# Email (para producción)
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Frontend
FRONTEND_URL=https://your-frontend-domain.com
```

### Generar Secret Key Seguro

```python
import secrets

# Generar secret key de 32 bytes
secret_key = secrets.token_urlsafe(32)
print(secret_key)
```

### Configurar HTTPS

#### Con Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d your-domain.com

# Renovar automáticamente
sudo crontab -e
# Agregar: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Con Nginx

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoreo y Logs

### Configuración de Logs

```python
# En producción, usar logging estructurado
configure_logging(
    log_level="INFO",
    json_logs=True
)
```

### Health Checks

```bash
# Verificar estado del servicio
curl https://your-domain.com/health

# Verificar logs
sudo journalctl -u simple-auth -f

# Verificar nginx
sudo nginx -t
sudo systemctl status nginx
```

### Métricas Básicas

```bash
# Ver uso de memoria
free -h

# Ver uso de CPU
htop

# Ver logs en tiempo real
tail -f /var/log/nginx/access.log
```

## 🔄 CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pip install pytest
        pytest
    
    - name: Deploy to server
      run: |
        # Comandos de despliegue
        ssh user@server "cd /path/to/app && git pull && sudo systemctl restart simple-auth"
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pip install pytest
    - pytest

deploy:
  stage: deploy
  script:
    - ssh user@server "cd /path/to/app && git pull && sudo systemctl restart simple-auth"
  only:
    - main
```

## 🚨 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a Base de Datos

```bash
# Verificar conexión
psql $DATABASE_URL -c "SELECT 1;"

# Verificar variables de entorno
echo $DATABASE_URL
```

#### 2. Error de Permisos

```bash
# Verificar permisos de archivos
ls -la /path/to/app

# Corregir permisos
chmod +x /path/to/app/run.py
chown -R user:user /path/to/app
```

#### 3. Puerto en Uso

```bash
# Verificar puertos en uso
sudo netstat -tlnp | grep :9000

# Matar proceso
sudo kill -9 <PID>
```

#### 4. Logs de Error

```bash
# Ver logs de la aplicación
sudo journalctl -u simple-auth -f

# Ver logs de nginx
sudo tail -f /var/log/nginx/error.log
```

### Comandos de Debug

```bash
# Verificar estado del servicio
sudo systemctl status simple-auth

# Reiniciar servicio
sudo systemctl restart simple-auth

# Ver logs en tiempo real
sudo journalctl -u simple-auth -f

# Verificar configuración de nginx
sudo nginx -t

# Verificar puertos
sudo ss -tlnp
```

## 📚 Recursos Adicionales

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Heroku Documentation](https://devcenter.heroku.com/)
- [AWS Documentation](https://aws.amazon.com/documentation/)
- [Google Cloud Documentation](https://cloud.google.com/docs/) 