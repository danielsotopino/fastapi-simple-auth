import structlog
from typing import Optional

logger = structlog.get_logger(__name__)

class EmailService:
    """Basic email service for development - logs emails instead of sending them"""
    
    def __init__(self):
        self.logger = logger
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        from_email: Optional[str] = None
    ) -> bool:
        """Send an email (logs it in development)"""
        self.logger.info(
            "Email would be sent",
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            from_email=from_email
        )
        return True
    
    async def send_verification_email(self, to_email: str, token: str, user_name: str = "") -> bool:
        """Send email verification email"""
        subject = "Verifica tu cuenta en Caracolito"
        html_content = f"""
        <p>Hola {user_name},</p>
        <p>Para verificar tu cuenta, haz clic en el siguiente enlace:</p>
        <p><a href="http://localhost:3000/verify-email/{token}">Verificar cuenta</a></p>
        <p>Si no solicitaste esta verificación, puedes ignorar este email.</p>
        """
        return await self.send_email(to_email, subject, html_content)
    
    async def send_password_reset_email(self, to_email: str, token: str, user_name: str = "") -> bool:
        """Send password reset email"""
        subject = "Restablece tu contraseña en Caracolito"
        html_content = f"""
        <p>Hola {user_name},</p>
        <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
        <p><a href="http://localhost:3000/reset-password/{token}">Restablecer contraseña</a></p>
        <p>Si no solicitaste este cambio, puedes ignorar este email.</p>
        """
        return await self.send_email(to_email, subject, html_content) 