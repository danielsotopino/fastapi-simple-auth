from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    GoogleLoginResponse,
    PasswordResetRequest,
    UserCreateRequest,
    UserResponse,
    GoogleOAuthRequest,
    GoogleAuthCodeRequest,
    PasswordResetConfirm,
    UserMeResponse,
    UserMeUpdateRequest
)
from app.schemas.subscription import CustomerCreate
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.services.subscription_service import SubscriptionService
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint for admin users
    
    - **email**: Admin user email
    - **password**: User password
    
    Returns access token and user information
    """
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(request)

@router.post("/password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset for a user
    
    - **email**: User email for password reset
    """
    auth_service = AuthService(db)
    return await auth_service.send_password_reset_email(request.email)


@router.post("/register/email", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_email(
    request: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password.

    A verification email will be sent to the provided email address.
    The account will need to be verified before login is possible for non-OAuth accounts.
    """
    auth_service = AuthService(db)
    # The service method register_user_email returns a User ORM model.
    # FastAPI will automatically convert it to UserResponse due to response_model.
    user = await auth_service.register_user_email(request)
    return user

@router.post("/register/google", response_model=LoginResponse)
async def register_google(
    request: GoogleOAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Register or login a user using a Google ID token.

    If the user is new, an account will be created.
    If the user exists (by Google ID or by email for linking), they will be logged in.
    Returns access token and user information.
    """
    auth_service = AuthService(db)
    token_data = await auth_service.register_user_google(request)
    return token_data

@router.post("/login/google-code", response_model=GoogleLoginResponse)
async def login_google_code(
    request: GoogleAuthCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Login endpoint for teachers using Google Authorization Code Flow.
    
    This endpoint exchanges the authorization code for tokens and processes the login.
    It will either:
    1. Create a new teacher account if the user doesn't exist
    2. Login an existing teacher account
    
    - **code**: Google authorization code from the frontend OAuth flow
    
    Returns access token and user information
    """
    

    logger.info("Starting Google code login process")
    auth_service = AuthService(db)
    token_data = await auth_service.exchange_google_code(request.code)
    logger.info(f"Google code exchanged. Token data: {token_data}")

    subscription_service = SubscriptionService(db)
    logger.info(f"Checking if customer exists for user_id: {token_data.get('user_id')}")
    customer = await subscription_service.get_customer(token_data.get("user_id"))
    logger.info(f"Customer lookup result: {customer}")

    if not customer or not getattr(customer, "success", True):
        logger.info("Customer not found, creating new customer in subscription service")
        customer_data = CustomerCreate(
            external_user_id=token_data.get("user_id"),
            email=token_data.get("email")
        )
        create_result = await subscription_service.create_customer(customer_data)
        logger.info(f"Customer creation result: {create_result}")
    else:
        logger.info("Customer already exists in subscription service")

    logger.info("Returning GoogleLoginResponse")
    return GoogleLoginResponse(**token_data)

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Confirm password reset using a valid token and new password.
    - **token**: Password reset token
    - **new_password**: New password to set
    """
    auth_service = AuthService(db)
    return await auth_service.reset_password(request.token, request.new_password)

@router.get("/verify-email/{token}", response_model=dict) # Simple dict response for message
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify a user's email address using a verification token.

    This token is typically sent to the user's email after registration.
    """
    auth_service = AuthService(db)
    result = await auth_service.verify_email_for_user(token)
    return result

@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user = Depends(get_current_user)):
    """Obtener los datos del usuario autenticado (sin campos sensibles)."""
    return UserMeResponse.model_validate(current_user, from_attributes=True)

@router.put("/me", response_model=UserMeResponse)
async def update_me(
    update_data: UserMeUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualizar los datos del usuario autenticado (excepto email)."""
    user_to_update = current_user
    if update_data.first_name is not None:
        user_to_update.first_name = update_data.first_name
    if update_data.last_name is not None:
        user_to_update.last_name = update_data.last_name
    if update_data.phone is not None:
        user_to_update.phone = update_data.phone
    if update_data.country_id is not None:
        user_to_update.country_id = update_data.country_id
    db.commit()
    db.refresh(user_to_update)
    return UserMeResponse.model_validate(user_to_update, from_attributes=True)