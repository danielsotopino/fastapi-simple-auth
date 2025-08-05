from pydantic import BaseModel, EmailStr, field_validator, ValidationError, constr
import re
from typing import Optional, Annotated
from datetime import datetime
from .master_tables import Country
# If UserType enum is needed for UserResponse, it should be imported
# from app.models.user import UserType # Assuming UserType is in user.py

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str

class GoogleLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str
    email: str
    first_name: str
    last_name: str
    is_new_user: bool = False

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: Annotated[str, constr(min_length=8)]

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe tener al menos una letra minúscula.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe tener al menos una letra mayúscula.')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe tener al menos un número.')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('La contraseña debe tener al menos un símbolo especial.')
        return v

from typing import Optional
from datetime import datetime
from .master_tables import Country
# If UserType enum is needed for UserResponse, it should be imported
# from app.models.user import UserType # Assuming UserType is in user.py

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, constr(min_length=8)]
    first_name: str
    last_name: str
    phone: Optional[str] = None
    country_id: Optional[int] = None
    user_type: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe tener al menos una letra minúscula.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe tener al menos una letra mayúscula.')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe tener al menos un número.')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('La contraseña debe tener al menos un símbolo especial.')
        return v

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    user_type: str # This assumes UserType enum from model is converted to str
    is_active: bool
    is_oauth_user: bool
    phone: Optional[str] = None
    country: Optional[Country] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class GoogleOAuthRequest(BaseModel):
    id_token: str

class GoogleAuthCodeRequest(BaseModel):
    code: str

class TokenData(BaseModel): # Similar to a TokenPayload, used for decoding JWTs or other tokens
    sub: Optional[str] = None # Subject (user_id or email)
    email: Optional[EmailStr] = None
    exp: Optional[int] = None # Expiry timestamp

class UserMeResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    user_type: str
    phone: Optional[str] = None
    country: Optional[Country] = None

    class Config:
        from_attributes = True

# UserMeUpdateRequest NO debe incluir password ni permitir cambiar la clave
# (ya está correcto, solo asegurando explícitamente en el comentario)
class UserMeUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    country_id: Optional[int] = None