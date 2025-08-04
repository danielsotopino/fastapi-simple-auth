import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.services.auth_service import AuthService
from app.schemas.auth import GoogleOAuthRequest
from app.models.user import User, UserType
from sqlalchemy.orm import Session


class TestGoogleOAuth:
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def auth_service(self, mock_db):
        return AuthService(mock_db)
    
    @pytest.fixture
    def mock_google_token_info(self):
        return {
            "iss": "accounts.google.com",
            "sub": "google_user_id_123",
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User",
            "email_verified": True
        }
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.get_settings')
    async def test_register_new_user_google_success(self, mock_settings, mock_verify_token, auth_service, mock_google_token_info):
        """Test successful registration of new user via Google OAuth"""
        # Setup
        mock_settings.return_value.GOOGLE_CLIENT_ID = "test_client_id"
        mock_verify_token.return_value = mock_google_token_info
        
        # Mock database queries
        auth_service.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No user found by google_id
            None   # No user found by email
        ]
        
        # Mock user creation
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.user_type = UserType.TEACHER
        mock_user.google_id = "google_user_id_123"
        mock_user.is_oauth_user = True
        mock_user.is_active = True
        
        auth_service.db.add.return_value = None
        auth_service.db.commit.return_value = None
        auth_service.db.refresh.return_value = None
        
        # Execute
        request = GoogleOAuthRequest(id_token="valid_google_token")
        result = await auth_service.register_user_google(request)
        
        # Assert
        assert result["access_token"] is not None
        assert result["token_type"] == "bearer"
        assert result["user_type"] == "teacher"
        assert result["email"] == "test@example.com"
        assert result["first_name"] == "Test"
        assert result["last_name"] == "User"
        assert result["is_new_user"] is True
        # user_id puede ser None en el mock
        assert result["user_id"] is None or result["user_id"] == "1"
        
        # Verify user was created with correct data
        auth_service.db.add.assert_called_once()
        created_user = auth_service.db.add.call_args[0][0]
        assert created_user.email == "test@example.com"
        assert created_user.google_id == "google_user_id_123"
        assert created_user.user_type == UserType.TEACHER
        assert created_user.is_oauth_user is True
        assert created_user.is_active is True
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.get_settings')
    async def test_login_existing_google_user_success(self, mock_settings, mock_verify_token, auth_service, mock_google_token_info):
        """Test successful login of existing Google OAuth user"""
        # Setup
        mock_settings.return_value.GOOGLE_CLIENT_ID = "test_client_id"
        mock_verify_token.return_value = mock_google_token_info
        
        # Mock existing user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.user_type = UserType.TEACHER
        mock_user.google_id = "google_user_id_123"
        mock_user.is_oauth_user = True
        mock_user.is_active = True
        
        # Mock database query to return existing user
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Execute
        request = GoogleOAuthRequest(id_token="valid_google_token")
        result = await auth_service.register_user_google(request)
        
        # Assert
        assert result["access_token"] is not None
        assert result["token_type"] == "bearer"
        assert result["user_id"] == "1"
        assert result["user_type"] == "teacher"
        assert result["email"] == "test@example.com"
        assert result["first_name"] == "Test"
        assert result["last_name"] == "User"
        assert result["is_new_user"] is False
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.get_settings')
    async def test_link_existing_email_user_with_google(self, mock_settings, mock_verify_token, auth_service, mock_google_token_info):
        """Test linking existing email user with Google OAuth"""
        # Setup
        mock_settings.return_value.GOOGLE_CLIENT_ID = "test_client_id"
        mock_verify_token.return_value = mock_google_token_info
        
        # Mock existing user without google_id
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.user_type = UserType.TEACHER
        mock_user.google_id = None  # No Google ID yet
        mock_user.is_oauth_user = False
        mock_user.is_active = True
        
        # Mock database queries
        auth_service.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No user found by google_id
            mock_user  # User found by email
        ]
        
        auth_service.db.commit.return_value = None
        auth_service.db.refresh.return_value = None
        
        # Execute
        request = GoogleOAuthRequest(id_token="valid_google_token")
        result = await auth_service.register_user_google(request)
        
        # Assert
        assert result["access_token"] is not None
        assert result["user_id"] == "1"
        assert result["is_new_user"] is False
        
        # Verify user was updated
        assert mock_user.google_id == "google_user_id_123"
        assert mock_user.is_oauth_user is True
        assert mock_user.is_active is True
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.get_settings')
    async def test_google_oauth_invalid_token(self, mock_settings, mock_verify_token, auth_service):
        """Test Google OAuth with invalid token"""
        # Setup
        mock_settings.return_value.GOOGLE_CLIENT_ID = "test_client_id"
        mock_verify_token.side_effect = ValueError("Invalid token")
        
        # Execute and assert
        request = GoogleOAuthRequest(id_token="invalid_token")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user_google(request)
        
        assert exc_info.value.status_code == 401
        assert "Invalid Google token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.get_settings')
    async def test_google_oauth_unverified_email(self, mock_settings, mock_verify_token, auth_service):
        """Test Google OAuth with unverified email"""
        # Setup
        mock_settings.return_value.GOOGLE_CLIENT_ID = "test_client_id"
        mock_verify_token.return_value = {
            "iss": "accounts.google.com",
            "sub": "google_user_id_123",
            "email": "test@example.com",
            "email_verified": False  # Email not verified
        }
        
        # Execute and assert
        request = GoogleOAuthRequest(id_token="valid_google_token")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user_google(request)
        
        assert exc_info.value.status_code == 400
        assert "Google email not verified" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.get_settings')
    async def test_google_oauth_inactive_user(self, mock_settings, mock_verify_token, auth_service, mock_google_token_info):
        """Test Google OAuth login attempt for inactive user"""
        # Setup
        mock_settings.return_value.GOOGLE_CLIENT_ID = "test_client_id"
        mock_verify_token.return_value = mock_google_token_info
        
        # Mock inactive user
        mock_user = MagicMock()
        mock_user.is_active = False
        
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Execute and assert
        request = GoogleOAuthRequest(id_token="valid_google_token")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user_google(request)
        
        assert exc_info.value.status_code == 403
        assert "User account is disabled" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    @patch('app.services.auth_service.id_token.verify_oauth2_token')
    @patch('app.services.auth_service.get_settings')
    async def test_google_oauth_email_already_linked(self, mock_settings, mock_verify_token, auth_service, mock_google_token_info):
        """Test Google OAuth when email is already linked to different Google account"""
        # Setup
        mock_settings.return_value.GOOGLE_CLIENT_ID = "test_client_id"
        mock_verify_token.return_value = mock_google_token_info
        
        # Mock existing user with different google_id
        mock_user = MagicMock()
        mock_user.google_id = "different_google_id"
        
        # Mock database queries
        auth_service.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # No user found by google_id
            mock_user  # User found by email with different google_id
        ]
        
        # Execute and assert
        request = GoogleOAuthRequest(id_token="valid_google_token")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user_google(request)
        
        assert exc_info.value.status_code == 400
        assert "Email already linked to a different Google account" in str(exc_info.value.detail) 