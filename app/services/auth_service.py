from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.user import User, UserType
from app.models.verification_token import VerificationToken
from app.core.security import (
    verify_password,
    create_access_token,
    get_password_hash,
    create_verification_token,
    verify_verification_token
)
from app.schemas.auth import LoginRequest, UserCreateRequest, GoogleOAuthRequest # UserResponse is for return type hinting, TokenData not directly used in service
from datetime import datetime, timedelta, timezone
import httpx # For Google OAuth, will be mocked
from google.oauth2 import id_token # For Google OAuth, will be mocked
from google.auth.transport import requests as google_requests # For Google OAuth, will be mocked
from app.config import get_settings
import structlog
import uuid
from app.services.email_service import EmailService

logger = structlog.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    async def authenticate_user(self, login_request: LoginRequest):
        """Authenticate user and return access token"""
        logger.info(f"Authenticating user: {login_request.email}")
        try:
            user = self.db.query(User).filter(
                User.email == login_request.email
            ).first()
            
            if not user:
                logger.warning(f"Login attempt with non-existent email: {login_request.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            if not verify_password(login_request.password, user.password_hash):
                logger.warning(f"Failed login attempt for user: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            if not user.is_active:
                logger.warning(f"Login attempt with disabled account: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is disabled"
                )
            
            access_token = create_access_token(data={"sub": str(user.id), "user_type": user.user_type, "email": user.email})
            logger.info(f"Successful login for user: {user.email}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": str(user.id),
                "user_type": user.user_type
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def send_password_reset_email(self, email: str):
        """Send password reset email"""
        logger.info(f"Requesting password reset for email: {email}")
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if user:
                from app.core.security import create_verification_token
                from app.services.email_service import EmailService
                settings = get_settings()
                token_expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS)
                reset_jwt = create_verification_token(email=str(user.email))
                # Guardar token con propósito password_reset
                verification_entry = VerificationToken(
                    user_id=user.id,
                    token=reset_jwt,
                    expires_at=token_expires_at,
                    purpose="password_reset"
                )
                self.db.add(verification_entry)
                self.db.commit()
                reset_link = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/auth/reset-password/{user.email}/{reset_jwt}"
                subject = "Restablece tu contraseña en Caracolito"
                html = f"""
                    <p>Hola {getattr(user, 'first_name', '')},</p>
                    <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
                    <p><a href='{reset_link}'>Restablecer contraseña</a></p>
                    <p>Si no solicitaste este cambio, puedes ignorar este correo.</p>
                """
                email_service = EmailService()
                email_service.send_email(
                    to=str(user.email),
                    subject=subject,
                    body=html,
                    html=True
                )
                logger.info(f"Password reset email sent to {user.email}")
            else:
                logger.warning(f"Password reset requested for non-existent email: {email}")
            # Always return success to prevent email enumeration
            return {"message": "Password reset email sent if user exists"}
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    async def reset_password(self, token: str, new_password: str) -> dict:
        """Reset user password using a valid password_reset token"""
        logger.info(f"Attempting password reset with token: {token[:20]}...")
        from app.core.security import verify_verification_token, get_password_hash
        email_from_token = verify_verification_token(token)
        if not email_from_token:
            logger.warning("Password reset failed: Invalid or expired token.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token.")
        token_entry = self.db.query(VerificationToken).filter(VerificationToken.token == token).first()
        if not token_entry:
            logger.warning(f"Password reset token not found in DB or already used: {token[:20]}...")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset token not found or already used.")
        if token_entry.purpose != "password_reset":
            logger.warning(f"Password reset token purpose invalid: {token_entry.purpose}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset token purpose.")
        # Asegurar que expires_at sea aware para comparar correctamente
        expires_at = token_entry.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            logger.warning(f"Password reset token expired (checked from DB): {token[:20]}...")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset token has expired.")
        user = self.db.query(User).filter(User.id == token_entry.user_id, User.email == email_from_token).first()
        if not user:
            logger.error(f"User not found for password reset: {email_from_token} from token ID {token_entry.user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for this password reset token.")
        user.password_hash = get_password_hash(new_password)
        self.db.delete(token_entry)
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Password successfully reset for user {user.email}.")
        return {"message": f"Password successfully reset for user {user.email}."}

    async def register_user_email(self, user_create_data: UserCreateRequest) -> User:
        logger.info(f"Attempting to register new user with email: {user_create_data.email}")
        # Al buscar usuario existente
        existing_user = self.db.query(User).filter(User.email == str(user_create_data.email)).first()
        if existing_user:
            logger.warning(f"Registration attempt for existing email: {user_create_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered."
            )

        hashed_password = get_password_hash(user_create_data.password)

        new_user = User(
            email=str(user_create_data.email),
            password_hash=hashed_password,
            first_name=user_create_data.first_name,
            last_name=user_create_data.last_name,
            phone=user_create_data.phone,
            user_type=UserType.TEACHER, # Defaulting to TEACHER
            is_active=False, # User will be activated after email verification
            is_oauth_user=False,
            country_id=user_create_data.country_id
        )
        self.db.add(new_user)
        self.db.flush() # To get new_user.id for the verification token

        verification_jwt = create_verification_token(email=str(new_user.email))

        settings = get_settings()
        token_expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS)

        verification_entry = VerificationToken(
            user_id=new_user.id,
            token=verification_jwt, # Storing the JWT itself
            expires_at=token_expires_at,
            purpose="account_activation"
        )
        self.db.add(verification_entry)
        self.db.commit()
        self.db.refresh(new_user)
        # Refrescar la relación country
        if getattr(new_user, 'country_id', None) is not None:
            self.db.refresh(new_user, attribute_names=["country"])

        logger.info(f"User {new_user.email} registered successfully. Verification email to be sent.")
        # Enviar correo de activación
        try:
            email_service = EmailService()
            settings = get_settings()
            verification_link = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3001')}/auth/activate/{new_user.email if hasattr(new_user, 'email') else ''}/{verification_jwt}"
            subject = "Activa tu cuenta en Caracolito"
            html = f"""
                <p>Hola {getattr(new_user, 'first_name', '')},</p>
                <p>Gracias por registrarte. Para activar tu cuenta, haz clic en el siguiente enlace:</p>
                <p><a href='{verification_link}'>Activar cuenta</a></p>
                <p>Si no creaste esta cuenta, puedes ignorar este correo.</p>
            """
            email_service.send_email(
                to=str(new_user.email),
                subject=subject,
                body=html,
                html=True
            )
            logger.info(f"Verification email sent to {new_user.email}")
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
        # TODO: Implement actual email sending logic here
        logger.info(f"Verification token for {new_user.email}: {verification_jwt}")
        # Example verification link: f"http://yourapi.com/api/v1/auth/verify-email/{verification_jwt}"

        return new_user

    async def exchange_google_code(self, auth_code: str) -> dict:
        """Exchange Google authorization code for tokens and login user"""
        settings = get_settings()
        logger.info(f"Attempting Google authorization code exchange.")
        
        try:
            # Intercambiar código por tokens
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "code": auth_code,
                        "grant_type": "authorization_code",
                        "redirect_uri": "postmessage"
                    }
                )
                
                token_data = token_response.json()
                
                if "error" in token_data:
                    logger.error(f"Google token exchange error: {token_data}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to exchange authorization code"
                    )
                
                # Obtener información del usuario usando el access token
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {token_data['access_token']}"}
                )
                
                user_info = user_response.json()
                
                # Procesar usuario
                email = user_info["email"]
                first_name = user_info.get("given_name", "")
                last_name = user_info.get("family_name", "")
                google_id = user_info.get("id", "")
                
                # Buscar o crear usuario
                user = self.db.query(User).filter(User.email == email).first()
                
                if not user:
                    # Crear nuevo usuario
                    logger.info(f"Creating new user from Google OAuth: {email}")
                    placeholder_password = get_password_hash(str(uuid.uuid4()))
                    user = User(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        google_id=google_id,
                        is_oauth_user=True,
                        is_active=True,
                        user_type=UserType.TEACHER,
                        password_hash=placeholder_password
                    )
                    self.db.add(user)
                    self.db.commit()
                    self.db.refresh(user)
                    is_new_user = True
                else:
                    # Usuario existente
                    logger.info(f"Google user {user.email} logged in successfully.")
                    is_new_user = False
                
                # Generar token de acceso
                access_token = create_access_token(
                    data={"sub": str(user.id), "user_type": user.user_type, "email": user.email}
                )
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user_id": str(user.id),
                    "user_type": user.user_type,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_new_user": is_new_user
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in Google code exchange: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during Google authentication"
            )

    async def verify_email_for_user(self, verification_jwt: str) -> dict:
        logger.info(f"Attempting to verify email with token: {verification_jwt[:20]}...")

        email_from_token = verify_verification_token(verification_jwt)
        if not email_from_token:
            logger.warning("Email verification failed: Invalid or expired token.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token.")

        token_entry = self.db.query(VerificationToken).filter(VerificationToken.token == verification_jwt).first()
        if not token_entry:
            logger.warning(f"Verification token not found in DB or already used: {verification_jwt[:20]}...")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token not found or already used.")

        if token_entry.purpose != "account_activation":
            logger.warning(f"Verification token purpose invalid: {token_entry.purpose}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token purpose.")

        if token_entry.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Verification token expired (checked from DB): {verification_jwt[:20]}...")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired.")

        user = self.db.query(User).filter(User.id == token_entry.user_id, User.email == email_from_token).first()
        if not user:
            logger.error(f"User not found for email verification: {email_from_token} from token ID {token_entry.user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for this verification token.")

        if user.is_active:
            logger.info(f"User {user.email} is already active.")
            return {"message": "User account is already active."}

        user.is_active = True

        self.db.delete(token_entry)
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"User account {user.email} successfully activated.")
        return {"message": f"User account {user.email} successfully activated."}