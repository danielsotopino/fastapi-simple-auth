import pytest
from fastapi import status
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserType
from app.core.security import get_password_hash, create_verification_token
from app.core.database import Base, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import get_db
from app.schemas.course import CourseCreate, CourseFeedbackCreate, CourseFeedbackUpdate
from app.models.verification_token import VerificationToken
from datetime import datetime, timedelta, timezone

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Crear todas las tablas antes de los tests
    Base.metadata.create_all(bind=engine)
    yield
    # Borrar todas las tablas después de los tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_headers_teacher():
    # Simula login y retorna headers con token para teacher
    # Debes adaptar esto a tu sistema real de autenticación
    return {"Authorization": "Bearer fake-teacher-token"}

@pytest.fixture
def auth_headers_admin():
    # Simula login y retorna headers con token para admin
    return {"Authorization": "Bearer fake-admin-token"}


class TestAuthAPI:
    """Integration tests for authentication endpoints"""
    
    def test_login_success(self, client, admin_user):
        """Test successful login"""
        # Arrange
        login_data = {
            "email": "admin@test.com",
            "password": "testpassword123"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == str(admin_user.id)
        assert data["user_type"] == UserType.ADMIN.value
    
    def test_login_invalid_email(self, client):
        """Test login with invalid email"""
        # Arrange
        login_data = {
            "email": "nonexistent@test.com",
            "password": "testpassword123"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_wrong_password(self, client, admin_user):
        """Test login with wrong password"""
        # Arrange
        login_data = {
            "email": "admin@test.com",
            "password": "wrongpassword"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client, inactive_admin_user):
        """Test login with inactive user"""
        # Arrange
        login_data = {
            "email": "inactive@test.com",
            "password": "testpassword123"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "User account is disabled" in response.json()["detail"]
    
    def test_login_teacher_user(self, client, teacher_user):
        """Test login con usuario tipo teacher (debe permitir login y retornar el tipo correcto)"""
        login_data = {
            "email": teacher_user.email,
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["user_type"] == teacher_user.user_type
    
    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format"""
        # Arrange
        login_data = {
            "email": "invalid-email",
            "password": "testpassword123"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        # Arrange
        login_data = {
            "email": "admin@test.com"
            # Missing password
        }
        
        # Act
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_password_reset_existing_user(self, client, admin_user):
        """Test password reset for existing user"""
        # Arrange
        reset_data = {
            "email": "admin@test.com"
        }
        
        # Act
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "Password reset email sent if user exists" in response.json()["message"]
    
    def test_password_reset_non_existing_user(self, client):
        """Test password reset for non-existing user"""
        # Arrange
        reset_data = {
            "email": "nonexistent@test.com"
        }
        
        # Act
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "Password reset email sent if user exists" in response.json()["message"]
    
    def test_password_reset_invalid_email_format(self, client):
        """Test password reset with invalid email format"""
        # Arrange
        reset_data = {
            "email": "invalid-email"
        }
        
        # Act
        response = client.post("/api/v1/auth/password-reset", json=reset_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_with_country(self, client):
        """Test user registration with country_id"""
        # Arrange: usar un country_id válido (por ejemplo, 1)
        register_data = {
            "email": "usercountry@test.com",
            "password": "Testpass1!",
            "first_name": "User",
            "last_name": "Country",
            "phone": "1234567890",
            "country_id": 1
        }
        # Act
        response = client.post("/api/v1/auth/register/email", json=register_data)
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "usercountry@test.com"
        assert data["country"] is not None
        assert data["country"]["id"] == 1

    def test_password_reset_confirm_success(self, client, admin_user, db_session):
        """Test successful password reset confirmation"""
        # Arrange: crear un token válido manualmente
        token = create_verification_token(admin_user.email)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        verification_entry = VerificationToken(
            user_id=admin_user.id,
            token=token,
            expires_at=expires_at,
            purpose="password_reset"
        )
        db_session.add(verification_entry)
        db_session.commit()
        # Act
        payload = {"token": token, "new_password": "Newpass1!"}
        response = client.post("/api/v1/auth/password-reset/confirm", json=payload)
        # Assert
        assert response.status_code == 200
        assert "Password successfully reset" in response.json()["message"]

    def test_password_reset_confirm_invalid_token(self, client):
        """Test password reset confirmation with invalid token"""
        payload = {"token": "invalidtoken", "new_password": "Validpass1!"}
        response = client.post("/api/v1/auth/password-reset/confirm", json=payload)
        assert response.status_code == 400
        assert "Invalid or expired password reset token" in response.json()["detail"]

    def test_password_reset_confirm_expired_token(self, client, admin_user, db_session):
        """Test password reset confirmation with expired token"""
        token = create_verification_token(admin_user.email)
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        verification_entry = VerificationToken(
            user_id=admin_user.id,
            token=token,
            expires_at=expires_at,
            purpose="password_reset"
        )
        db_session.add(verification_entry)
        db_session.commit()
        payload = {"token": token, "new_password": "Validpass1!"}
        response = client.post("/api/v1/auth/password-reset/confirm", json=payload)
        assert response.status_code == 400
        assert "Password reset token has expired" in response.json()["detail"]

    @pytest.mark.parametrize("password,expected_status", [
        ("short1A!", 201),           # 8 caracteres, cumple requisitos, debe ser válido
        ("alllowercase1!", 422),    # Sin mayúscula
        ("ALLUPPERCASE1!", 422),    # Sin minúscula
        ("NoNumber!", 422),         # Sin número
        ("NoSpecialChar1", 422),    # Sin símbolo especial
    ])
    def test_register_weak_password(self, client, password, expected_status):
        """Test user registration with weak passwords"""
        register_data = {
            "email": f"weakpass{password}@test.com",
            "password": password,
            "first_name": "Test",
            "last_name": "User",
            "phone": "1234567890",
            "country_id": 1
        }
        response = client.post("/api/v1/auth/register/email", json=register_data)
        assert response.status_code == expected_status
        if expected_status == 422:
            assert "contraseña" in response.text.lower()

    @pytest.mark.parametrize("new_password,expected_status", [
        ("short1A!", 200),           # 8 caracteres, cumple requisitos, debe ser válido
        ("alllowercase1!", 422),    # Sin mayúscula
        ("ALLUPPERCASE1!", 422),    # Sin minúscula
        ("NoNumber!", 422),         # Sin número
        ("NoSpecialChar1", 422),    # Sin símbolo especial
    ])
    def test_password_reset_confirm_weak_password(self, client, admin_user, db_session, new_password, expected_status):
        """Test password reset confirmation with weak passwords"""
        token = create_verification_token(admin_user.email)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        verification_entry = VerificationToken(
            user_id=admin_user.id,
            token=token,
            expires_at=expires_at,
            purpose="password_reset"
        )
        db_session.add(verification_entry)
        db_session.commit()
        payload = {"token": token, "new_password": new_password}
        response = client.post("/api/v1/auth/password-reset/confirm", json=payload)
        assert response.status_code == expected_status
        if expected_status == 422:
            assert "contraseña" in response.text.lower()

    def test_get_me(self, client, admin_user):
        """Test obtener datos del usuario autenticado"""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.id), "user_type": admin_user.user_type, "email": admin_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == admin_user.email
        assert data["first_name"] == admin_user.first_name
        assert data["last_name"] == admin_user.last_name
        assert data["user_type"] == admin_user.user_type
        # No debe exponer campos sensibles
        assert "id" not in data
        assert "is_active" not in data
        assert "is_oauth_user" not in data
        assert "created_at" not in data
        assert "updated_at" not in data

    def test_update_me(self, client, admin_user, db_session):
        """Test actualizar datos del usuario autenticado"""
        from app.core.security import create_access_token
        token = create_access_token({"sub": str(admin_user.id), "user_type": admin_user.user_type, "email": admin_user.email})
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {
            "first_name": "NuevoNombre",
            "last_name": "NuevoApellido",
            "phone": "9876543210",
            "country_id": 2,
            "education_area_id": 3,
            "email": "otro@email.com"  # No debe cambiar
        }
        response = client.put("/api/v1/auth/me", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "NuevoNombre"
        assert data["last_name"] == "NuevoApellido"
        assert data["phone"] == "9876543210"
        assert data["country"]["id"] == 2
        # assert data["education_area_id"] == 3  # Eliminado del modelo de respuesta
        # El email debe seguir igual
        assert data["email"] == admin_user.email


class TestAPIEndpoints:
    """Test basic API endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["message"] == "Caracolito Admin API"
        assert data["version"] == "0.1.0"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy" 

    def test_list_countries(self, client):
        """Test GET /api/v1/public/countries returns list of countries"""
        response = client.get("/api/v1/public/countries")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(c["code"] == "AR" for c in data)  # Argentina debe estar

    def test_list_education_areas(self, client):
        response = client.get("/api/v1/public/education-areas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(area["name"] == "Deseo no mencionarlo" and area["show_in_list"] is True for area in data)
        assert all("id" in area and "name" in area and "show_in_list" in area for area in data) 


def test_feedback_update_only_by_owner(client, admin_user, teacher_user):
    # Crear tokens reales
    from app.core.security import create_access_token
    
    admin_token = create_access_token({"sub": str(admin_user.id), "user_type": admin_user.user_type, "email": admin_user.email})
    teacher_token = create_access_token({"sub": str(teacher_user.id), "user_type": teacher_user.user_type, "email": teacher_user.email})
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    
    # Crear curso como admin
    course_data = {"title": "Curso Feedback", "description": "desc", "is_active": True}
    course_resp = client.post("/api/v1/courses/", json=course_data, headers=admin_headers)
    assert course_resp.status_code == 201
    course_id = course_resp.json()["id"]

    # Crear feedback como teacher
    feedback_data = {"course_id": course_id, "rating": 5, "read": False}
    feedback_resp = client.post("/api/v1/courses/feedback/", json=feedback_data, headers=teacher_headers)
    assert feedback_resp.status_code == 201
    feedback_id = feedback_resp.json()["id"]

    # El mismo usuario puede actualizar
    update_data = {"read": True}
    update_resp = client.put(f"/api/v1/courses/feedback/{feedback_id}", json=update_data, headers=teacher_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["read"] is True

    # Otro usuario (admin) no puede actualizar
    update_resp2 = client.put(f"/api/v1/courses/feedback/{feedback_id}", json=update_data, headers=admin_headers)
    assert update_resp2.status_code == 403 