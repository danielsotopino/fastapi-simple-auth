# 🔒 Guía de Seguridad

## ⚠️ **ADVERTENCIAS IMPORTANTES**

### 🚨 **Credenciales por Defecto**

Este proyecto incluye credenciales por defecto **SOLO PARA DESARROLLO**. **NUNCA** uses estas credenciales en producción.

#### Credenciales por Defecto:
- **SECRET_KEY:** `CHANGE_THIS_IN_PRODUCTION_USE_ENV_VAR`
- **Admin Password:** `ChangeMe123!`

### 🔐 **Configuración de Producción**

#### 1. **SECRET_KEY**
```bash
# Genera una clave segura (mínimo 32 caracteres)
openssl rand -base64 32
# O usa un generador de contraseñas seguro

# Configura en producción
export SECRET_KEY="tu-clave-secreta-muy-segura-aqui"
```

#### 2. **ADMIN_PASSWORD**
```bash
# Cambia la contraseña del admin
export ADMIN_PASSWORD="tu-contraseña-segura-aqui"
```

#### 3. **Base de Datos**
```bash
# Usa PostgreSQL en producción
export DATABASE_URL="postgresql://user:password@host:5432/db"
```

## 🛡️ **Mejores Prácticas de Seguridad**

### 1. **Variables de Entorno**
- ✅ Usa variables de entorno para todas las credenciales
- ✅ Nunca commits credenciales al repositorio
- ✅ Usa `.env` local para desarrollo
- ✅ Usa secretos del sistema en producción

### 2. **JWT Tokens**
- ✅ Usa SECRET_KEY fuerte (mínimo 32 caracteres)
- ✅ Configura expiración apropiada
- ✅ Valida tokens en cada request
- ✅ Usa HTTPS en producción

### 3. **Contraseñas**
- ✅ Usa contraseñas fuertes
- ✅ Cambia contraseñas por defecto
- ✅ Implementa política de contraseñas
- ✅ Usa hashing seguro (bcrypt)

### 4. **Base de Datos**
- ✅ Usa conexiones seguras
- ✅ Limita permisos de usuario
- ✅ Habilita SSL/TLS
- ✅ Usa prepared statements

### 5. **API Security**
- ✅ Implementa rate limiting
- ✅ Valida todas las entradas
- ✅ Usa HTTPS
- ✅ Implementa CORS apropiadamente

## 🚨 **Checklist de Seguridad**

### Antes de Desplegar a Producción:

- [ ] Cambiar `SECRET_KEY` por una clave segura
- [ ] Cambiar `ADMIN_PASSWORD` por una contraseña fuerte
- [ ] Configurar base de datos PostgreSQL
- [ ] Habilitar HTTPS
- [ ] Configurar CORS apropiadamente
- [ ] Implementar rate limiting
- [ ] Configurar logging de seguridad
- [ ] Revisar permisos de archivos
- [ ] Configurar firewall
- [ ] Implementar monitoreo de seguridad

### Variables Críticas a Cambiar:

```bash
# OBLIGATORIO cambiar en producción
SECRET_KEY=tu-clave-secreta-muy-segura-aqui
ADMIN_PASSWORD=tu-contraseña-segura-aqui
DATABASE_URL=postgresql://user:password@host:5432/db

# Configurar según necesidades
GOOGLE_CLIENT_ID=tu-google-client-id
GOOGLE_CLIENT_SECRET=tu-google-client-secret
```

## 📞 **Reportar Problemas de Seguridad**

Si encuentras un problema de seguridad:

1. **NO** crees un issue público
2. Contacta directamente al equipo de desarrollo
3. Proporciona detalles específicos del problema
4. Espera confirmación antes de hacer público

## 📚 **Recursos Adicionales**

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Security Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)
- [Python Security](https://python-security.readthedocs.io/)

---

**Recuerda:** La seguridad es responsabilidad de todos. Siempre revisa y actualiza las configuraciones de seguridad regularmente. 