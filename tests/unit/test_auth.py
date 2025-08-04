import pytest
from fastapi import HTTPException, status
from unittest.mock import Mock, patch
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, UserCreateRequest, GoogleOAuthRequest
from app.models.user import User, UserType
from app.models.verification_token import VerificationToken
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
import uuid
from datetime import datetime, timedelta, timezone
from jose import JWTError


class TestAuthService:
    """Unit tests for AuthService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.flush = Mock()
        db.delete = Mock()
        db.rollback = Mock()
        return db
    
    @pytest.fixture
    def auth_service(self, mock_db):
        """AuthService instance with mocked database"""
        return AuthService(mock_db)
    
    @pytest.fixture
    def valid_login_request(self):
        """Valid login request"""
        return LoginRequest(email="admin@test.com", password="testpassword123")
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "admin@test.com"
        user.password_hash = get_password_hash("testpassword123")
        user.user_type = UserType.ADMIN
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_teacher_user(self):
        """Mock teacher user"""
        user = Mock(spec=User)
        user.id = 2
        user.email = "teacher@test.com"
        user.password_hash = get_password_hash("teacherpassword")
        user.user_type = UserType.TEACHER
        user.is_active = True
        user.is_oauth_user = False
        user.google_id = None
        user.first_name = "Test"
        user.last_name = "Teacher"
        return user
    
    @pytest.fixture
    def user_create_request(self):
        """User creation request"""
        return UserCreateRequest(
            email="newuser@test.com",
            password="newpassword123",
            first_name="New",
            last_name="User",
            phone="1234567890"
        )
    
    @pytest.fixture
    def google_oauth_request(self):
        """Google OAuth request"""
        return GoogleOAuthRequest(id_token="valid_google_token_for_new_user@example.com")
    
    @pytest.fixture
    def mock_verification_token(self):
        """Mock verification token"""
        token = Mock(spec=VerificationToken)
        token.id = 1
        token.user_id = 2
        token.token = "mock_verification_jwt"
        token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return token

    # === Authentication Tests ===
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_db, valid_login_request, mock_admin_user):
        """Test successful user authentication"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_admin_user
        
        # Act
        result = await auth_service.authenticate_user(valid_login_request)
        
        # Assert
        assert result["token_type"] == "bearer"
        assert result["user_id"] == str(mock_admin_user.id)
        assert result["user_type"] == UserType.ADMIN.value
        assert result["access_token"] is not None
        
        # Verify database query was called correctly
        mock_db.query.assert_called_once_with(User)
        
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_db, valid_login_request):
        """Test authentication with non-existent user"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(valid_login_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, mock_db, mock_admin_user):
        """Test authentication with wrong password"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_admin_user
        wrong_password_request = LoginRequest(email="admin@test.com", password="wrongpassword")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(wrong_password_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect email or password" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, mock_db, valid_login_request, mock_admin_user):
        """Test authentication with inactive user"""
        # Arrange
        mock_admin_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_admin_user
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(valid_login_request)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "User account is disabled" in exc_info.value.detail

    # === Password Reset Tests ===
    @pytest.mark.asyncio
    async def test_send_password_reset_email_existing_user(self, auth_service, mock_db):
        """Test password reset for existing user"""
        # Arrange
        mock_user = Mock()
        mock_user.email = "admin@test.com"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Act
        result = await auth_service.send_password_reset_email("admin@test.com")
        
        # Assert
        assert result["message"] == "Password reset email sent if user exists"
        mock_db.query.assert_called_once_with(User)
    
    @pytest.mark.asyncio
    async def test_send_password_reset_email_non_existing_user(self, auth_service, mock_db):
        """Test password reset for non-existing user"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = await auth_service.send_password_reset_email("nonexistent@test.com")
        
        # Assert
        assert result["message"] == "Password reset email sent if user exists"
        mock_db.query.assert_called_once_with(User)

    # === Email Registration Tests ===
    @patch('app.services.auth_service.get_password_hash')
    @patch('app.services.auth_service.create_verification_token')
    @patch('app.services.auth_service.get_settings')
    @pytest.mark.asyncio
    async def test_register_user_email_success(self, mock_get_settings, mock_create_verification_token, 
                                               mock_get_password_hash, auth_service, mock_db, user_create_request):
        """Test successful email registration"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing user
        mock_get_password_hash.return_value = "hashed_password"
        mock_create_verification_token.return_value = "dummy_verification_jwt"
        
        mock_settings = Mock()
        mock_settings.EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS = 24
        mock_get_settings.return_value = mock_settings
        
        # Act
        result = await auth_service.register_user_email(user_create_request)
        
        # Assert
        assert result.email == user_create_request.email
        assert result.first_name == user_create_request.first_name
        assert result.last_name == user_create_request.last_name
        assert result.phone == user_create_request.phone
        assert result.user_type == UserType.TEACHER
        assert result.is_active is False
        assert result.is_oauth_user is False
        
        # Verify database operations
        mock_db.add.assert_called()
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify security functions were called
        mock_get_password_hash.assert_called_once_with(user_create_request.password)
        mock_create_verification_token.assert_called_once_with(email=user_create_request.email)

    @pytest.mark.asyncio
    async def test_register_user_email_existing_email(self, auth_service, mock_db, user_create_request, mock_admin_user):
        """Test registration with existing email"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_admin_user
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user_email(user_create_request)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in exc_info.value.detail

    # === Google OAuth Tests ===
    @patch('app.services.auth_service.create_access_token')
    @patch('app.services.auth_service.get_password_hash')
    @pytest.mark.asyncio
    async def test_register_google_new_user_success(self, mock_get_password_hash, mock_create_access_token,
                                                   auth_service, mock_db, google_oauth_request):
        """Test successful Google OAuth registration for new user"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing user
        mock_get_password_hash.return_value = "hashed_placeholder_password"
        mock_create_access_token.return_value = "dummy_access_token"
        
        # Act
        result = await auth_service.register_user_google(google_oauth_request)
        
        # Assert
        assert result["access_token"] == "dummy_access_token"
        assert result["token_type"] == "bearer"
        assert result["email"] == "new_google_user@example.com"
        assert "user_id" in result
        assert "user_type" in result
        
        # Verify database operations
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('app.services.auth_service.create_access_token')
    @pytest.mark.asyncio
    async def test_register_google_existing_oauth_user_login(self, mock_create_access_token, auth_service, 
                                                           mock_db, mock_teacher_user):
        """Test Google OAuth login for existing OAuth user"""
        # Arrange
        google_request = GoogleOAuthRequest(id_token="valid_google_token_for_existing_oauth_user@example.com")
        mock_teacher_user.google_id = "google_user_id_existing_789"
        mock_teacher_user.email = "existing_oauth_user@example.com"
        mock_teacher_user.is_oauth_user = True
        mock_teacher_user.is_active = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_teacher_user
        mock_create_access_token.return_value = "dummy_access_token"
        
        # Act
        result = await auth_service.register_user_google(google_request)
        
        # Assert
        assert result["access_token"] == "dummy_access_token"
        assert result["email"] == mock_teacher_user.email
        
        # Should not commit for existing user login
        mock_db.commit.assert_not_called()

    @patch('app.services.auth_service.create_access_token')
    @pytest.mark.asyncio
    async def test_register_google_link_existing_local_user(self, mock_create_access_token, auth_service,
                                                          mock_db, mock_teacher_user):
        """Test linking Google account to existing local user"""
        # Arrange
        google_request = GoogleOAuthRequest(id_token="valid_google_token_for_existing_user_to_link@example.com")
        mock_teacher_user.google_id = None
        mock_teacher_user.is_oauth_user = False
        
        # Mock database queries
        mock_db_query = Mock()
        mock_db.query.return_value = mock_db_query
        
        # First query by google_id returns None, second query by email returns user
        mock_db_query.filter.return_value.first.side_effect = [None, mock_teacher_user]
        
        mock_create_access_token.return_value = "dummy_access_token"
        
        # Act
        result = await auth_service.register_user_google(google_request)
        
        # Assert
        assert result["access_token"] == "dummy_access_token"
        assert result["email"] == mock_teacher_user.email
        assert mock_teacher_user.google_id == "google_user_id_link_456"
        assert mock_teacher_user.is_oauth_user is True
        assert mock_teacher_user.is_active is True
        
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_google_invalid_token(self, auth_service, mock_db):
        """Test Google OAuth with invalid token"""
        # Arrange
        google_request = GoogleOAuthRequest(id_token="invalid_google_token")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user_google(google_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid Google token or authentication error" in exc_info.value.detail

    # === Email Verification Tests ===
    @patch('app.services.auth_service.verify_verification_token')
    @pytest.mark.asyncio
    async def test_verify_email_success(self, mock_verify_token, auth_service, mock_db, 
                                       mock_verification_token, mock_teacher_user):
        """Test successful email verification"""
        # Arrange
        mock_verify_token.return_value = mock_teacher_user.email
        mock_teacher_user.is_active = False
        mock_verification_token.user_id = mock_teacher_user.id
        
        # Mock database queries
        mock_db_query = Mock()
        mock_db.query.return_value = mock_db_query
        mock_db_query.filter.return_value.first.side_effect = [mock_verification_token, mock_teacher_user]
        
        # Act
        result = await auth_service.verify_email_for_user("dummy_jwt")
        
        # Assert
        assert f"User account {mock_teacher_user.email} successfully activated" in result["message"]
        assert mock_teacher_user.is_active is True
        
        # Verify database operations
        mock_db.delete.assert_called_once_with(mock_verification_token)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_teacher_user)

    @patch('app.services.auth_service.verify_verification_token')
    @pytest.mark.asyncio
    async def test_verify_email_invalid_jwt(self, mock_verify_token, auth_service, mock_db):
        """Test email verification with invalid JWT"""
        # Arrange
        mock_verify_token.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_email_for_user("invalid_jwt")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid or expired verification token" in exc_info.value.detail

    @patch('app.services.auth_service.verify_verification_token')
    @pytest.mark.asyncio
    async def test_verify_email_token_not_in_db(self, mock_verify_token, auth_service, mock_db):
        """Test email verification with token not in database"""
        # Arrange
        mock_verify_token.return_value = "user@test.com"
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_email_for_user("jwt_not_in_db")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Verification token not found or already used" in exc_info.value.detail

    @patch('app.services.auth_service.verify_verification_token')
    @pytest.mark.asyncio
    async def test_verify_email_token_expired(self, mock_verify_token, auth_service, mock_db, mock_verification_token):
        """Test email verification with expired token"""
        # Arrange
        mock_verify_token.return_value = "user@test.com"
        mock_verification_token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification_token
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_email_for_user("expired_jwt")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Verification token has expired" in exc_info.value.detail

    @patch('app.services.auth_service.verify_verification_token')
    @pytest.mark.asyncio
    async def test_verify_email_user_already_active(self, mock_verify_token, auth_service, mock_db,
                                                   mock_verification_token, mock_teacher_user):
        """Test email verification for already active user"""
        # Arrange
        mock_verify_token.return_value = mock_teacher_user.email
        mock_teacher_user.is_active = True  # Already active
        mock_verification_token.user_id = mock_teacher_user.id
        
        # Mock database queries
        mock_db_query = Mock()
        mock_db.query.return_value = mock_db_query
        mock_db_query.filter.return_value.first.side_effect = [mock_verification_token, mock_teacher_user]
        
        # Act
        result = await auth_service.verify_email_for_user("jwt_for_active_user")
        
        # Assert
        assert result["message"] == "User account is already active."
        
        # Token should not be deleted for already active user
        mock_db.delete.assert_not_called()


class TestSecurityFunctions:
    """Unit tests for security functions"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        data = {"sub": "admin@test.com", "user_id": "123", "user_type": "admin"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
    
    @patch('app.core.security.jwt.decode')
    def test_decode_token_success(self, mock_decode):
        """Test successful token decoding"""
        # Arrange
        expected_payload = {"sub": "admin@test.com", "user_id": "123", "exp": 1234567890}
        mock_decode.return_value = expected_payload
        
        # Act
        result = decode_token("valid_token")
        
        # Assert
        assert result == expected_payload
        mock_decode.assert_called_once()
    
    @patch('app.core.security.jwt.decode')
    def test_decode_token_invalid(self, mock_decode):
        """Test token decoding with invalid token"""
        # Arrange
        mock_decode.side_effect = JWTError("Invalid token")
        
        # Act
        result = decode_token("invalid_token")
        
        # Assert
        assert result is None
        mock_decode.assert_called_once()