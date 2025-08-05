# Guía de Usuario - Simple Auth API

## 🎯 Introducción

Esta guía está diseñada para usuarios finales que necesitan integrar o usar la Simple Auth API en sus aplicaciones.

## 🚀 Inicio Rápido

### 1. Verificar que el Servicio Esté Funcionando

```bash
# Health check
curl http://localhost:9000/health

# Respuesta esperada
{"status":"healthy"}
```

### 2. Acceder a la Documentación Interactiva

Abre tu navegador y ve a:
```
http://localhost:9000/docs
```

Aquí podrás:
- Ver todos los endpoints disponibles
- Probar la API directamente
- Ver ejemplos de requests y responses
- Entender los códigos de error

## 🔐 Autenticación

### Login Básico

**Endpoint:** `POST /auth/login`

**Ejemplo con curl:**
```bash
curl -X POST "http://localhost:9000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin123!"
  }'
```

**Respuesta exitosa:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "1",
  "user_type": "ADMIN"
}
```

### Usar el Token de Acceso

Una vez que tengas el `access_token`, úsalo en el header `Authorization`:

```bash
curl -X GET "http://localhost:9000/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 👤 Registro de Usuarios

### Registro con Email

**Endpoint:** `POST /auth/register/email`

**Ejemplo:**
```bash
curl -X POST "http://localhost:9000/auth/register/email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@usuario.com",
    "password": "MiContraseña123!",
    "first_name": "Juan",
    "last_name": "Pérez",
    "phone": "+1234567890",
    "user_type": "TEACHER"
  }'
```

**Notas importantes:**
- La contraseña debe cumplir requisitos de seguridad
- El usuario se crea como `is_active: false` hasta verificar email
- Se enviará un email de verificación (simulado en desarrollo)

### Requisitos de Contraseña

La contraseña debe cumplir:
- ✅ Mínimo 8 caracteres
- ✅ Al menos una letra minúscula
- ✅ Al menos una letra mayúscula
- ✅ Al menos un número
- ✅ Al menos un símbolo especial

## 📧 Verificación de Email

### Verificar Email

**Endpoint:** `GET /auth/verify-email/{token}`

```bash
curl -X GET "http://localhost:9000/auth/verify-email/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Respuesta:**
```json
{
  "message": "Email verified successfully",
  "user_id": 2
}
```

## 🔑 Reset de Contraseña

### Solicitar Reset

**Endpoint:** `POST /auth/password-reset`

```bash
curl -X POST "http://localhost:9000/auth/password-reset" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@ejemplo.com"
  }'
```

### Confirmar Reset

**Endpoint:** `POST /auth/password-reset/confirm`

```bash
curl -X POST "http://localhost:9000/auth/password-reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset_token_here",
    "new_password": "NuevaContraseña123!"
  }'
```

## 👤 Gestión de Perfil

### Obtener Información del Usuario

**Endpoint:** `GET /auth/me`

```bash
curl -X GET "http://localhost:9000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Respuesta:**
```json
{
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User",
  "user_type": "ADMIN",
  "phone": null,
  "country": null
}
```

### Actualizar Información del Usuario

**Endpoint:** `PUT /auth/me`

```bash
curl -X PUT "http://localhost:9000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Nuevo",
    "last_name": "Nombre",
    "phone": "+1234567890"
  }'
```

## 🌐 Google OAuth

### Login con Google

**Endpoint:** `POST /auth/login/google-code`

```bash
curl -X POST "http://localhost:9000/auth/login/google-code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "google_authorization_code"
  }'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "3",
  "user_type": "TEACHER",
  "email": "usuario@gmail.com",
  "first_name": "Usuario",
  "last_name": "Google",
  "is_new_user": false
}
```

## 📊 Códigos de Error

### Códigos HTTP Comunes

| Código | Significado | Solución |
|--------|-------------|----------|
| 200 | OK | Request exitoso |
| 201 | Created | Recurso creado exitosamente |
| 400 | Bad Request | Verificar formato de datos |
| 401 | Unauthorized | Token inválido o expirado |
| 403 | Forbidden | Sin permisos para la acción |
| 404 | Not Found | Recurso no encontrado |
| 422 | Validation Error | Datos de entrada inválidos |
| 500 | Internal Server Error | Error del servidor |

### Ejemplos de Errores

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "La contraseña debe tener al menos 8 caracteres.",
      "input": "123"
    }
  ]
}
```

## 🔧 Integración con Aplicaciones

### JavaScript/Node.js

```javascript
// Login
const loginResponse = await fetch('http://localhost:9000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'admin@example.com',
    password: 'Admin123!'
  })
});

const { access_token } = await loginResponse.json();

// Usar token en requests posteriores
const userResponse = await fetch('http://localhost:9000/auth/me', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### Python

```python
import requests

# Login
login_data = {
    "email": "admin@example.com",
    "password": "Admin123!"
}

response = requests.post(
    "http://localhost:9000/auth/login",
    json=login_data
)

token_data = response.json()
access_token = token_data["access_token"]

# Usar token
headers = {"Authorization": f"Bearer {access_token}"}
user_response = requests.get(
    "http://localhost:9000/auth/me",
    headers=headers
)
```

### cURL

```bash
# Login
TOKEN=$(curl -s -X POST "http://localhost:9000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin123!"}' \
  | jq -r '.access_token')

# Usar token
curl -X GET "http://localhost:9000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

## 📱 Ejemplos de Uso por Caso

### 1. Aplicación Web

```javascript
class AuthAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  async login(email, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
      const data = await response.json();
      this.token = data.access_token;
      localStorage.setItem('access_token', this.token);
      return data;
    }
    
    throw new Error('Login failed');
  }

  async getCurrentUser() {
    const response = await fetch(`${this.baseURL}/auth/me`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    return response.json();
  }
}

// Uso
const auth = new AuthAPI('http://localhost:9000');
await auth.login('admin@example.com', 'Admin123!');
const user = await auth.getCurrentUser();
```

### 2. Aplicación Móvil

```dart
// Flutter/Dart
class AuthService {
  static const String baseURL = 'http://localhost:9000';
  
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseURL/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'email': email,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    
    throw Exception('Login failed');
  }
  
  Future<Map<String, dynamic>> getCurrentUser(String token) async {
    final response = await http.get(
      Uri.parse('$baseURL/auth/me'),
      headers: {'Authorization': 'Bearer $token'},
    );
    
    return json.decode(response.body);
  }
}
```

### 3. Script de Automatización

```python
import requests
import json

class SimpleAuthClient:
    def __init__(self, base_url="http://localhost:9000"):
        self.base_url = base_url
        self.token = None
    
    def login(self, email, password):
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.token = data["access_token"]
        return data
    
    def register(self, user_data):
        response = requests.post(
            f"{self.base_url}/auth/register/email",
            json=user_data
        )
        response.raise_for_status()
        return response.json()
    
    def get_current_user(self):
        if not self.token:
            raise ValueError("Not logged in")
        
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        return response.json()

# Uso
client = SimpleAuthClient()
client.login("admin@example.com", "Admin123!")
user = client.get_current_user()
print(f"Logged in as: {user['first_name']} {user['last_name']}")
```

## 🔒 Seguridad

### Mejores Prácticas

1. **Nunca almacenes tokens en texto plano**
2. **Usa HTTPS en producción**
3. **Implementa refresh tokens para aplicaciones web**
4. **Valida siempre las respuestas del servidor**
5. **Maneja errores de red apropiadamente**

### Manejo de Tokens

```javascript
// Ejemplo de manejo seguro de tokens
class SecureAuthManager {
  constructor() {
    this.token = null;
    this.tokenExpiry = null;
  }
  
  setToken(tokenData) {
    this.token = tokenData.access_token;
    // Calcular expiración basado en el token JWT
    this.tokenExpiry = this.calculateExpiry(tokenData.access_token);
  }
  
  isTokenValid() {
    return this.token && this.tokenExpiry > Date.now();
  }
  
  getAuthHeaders() {
    if (!this.isTokenValid()) {
      throw new Error('Token expired or invalid');
    }
    return { 'Authorization': `Bearer ${this.token}` };
  }
}
```

## 📞 Soporte

### Recursos de Ayuda

1. **Documentación Interactiva:** `http://localhost:9000/docs`
2. **Health Check:** `http://localhost:9000/health`
3. **OpenAPI Schema:** `http://localhost:9000/openapi.json`

### Reportar Problemas

Cuando reportes un problema, incluye:

- **Endpoint usado**
- **Request body/headers**
- **Response completa**
- **Código de error**
- **Pasos para reproducir**

### Ejemplo de Reporte

```
Problema: Error 401 al hacer login

Endpoint: POST /auth/login
Request: {"email": "test@example.com", "password": "password123"}
Response: {"detail": "Incorrect email or password"}
Expected: Login exitoso con token JWT

Pasos:
1. Crear usuario con POST /auth/register/email
2. Intentar login con credenciales correctas
3. Recibir error 401
```

## 📚 Recursos Adicionales

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT.io](https://jwt.io/) - Para debug de tokens
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [REST API Best Practices](https://restfulapi.net/) 