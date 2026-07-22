from datetime import datetime, timezone, timedelta
import logging
from typing import Optional
import uuid
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    ACCESS_TOKEN_TYPE
)
from app.identity.models.user import User
from app.identity.repositories.user import UserRepository
from app.identity.schemas.user import UserRegister, UserLogin

logger = logging.getLogger("auth_service")

# --- Domain Exceptions (Preparation for Future Enhancements) ---
# class EmailAlreadyExistsError(ValueError): pass
# class InvalidCredentialsError(ValueError): pass
# class AccountDisabledError(ValueError): pass

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, register_data: UserRegister) -> User:
        """
        Register a new user account.
        """
        normalized_email = register_data.email.lower().strip()
        # Validate uniqueness of email
        if await self.user_repo.exists_by_email(normalized_email):
            self._log_audit_event("registration_failed", normalized_email, "Email already registered")
            # In the future, raise EmailAlreadyExistsError
            raise ValueError("Email address already registered")
        
        # Hash password and create User entity
        hashed = hash_password(register_data.password)
        new_user = User(
            email=normalized_email,
            full_name=register_data.full_name,
            hashed_password=hashed,
            is_active=True,
            is_verified=False
        )
        
        created = await self.user_repo.create(new_user)
        self._log_audit_event("registration_successful", created.email, f"User ID: {created.id}")
        return created

    async def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """
        Authenticate user credentials and update login timestamp.
        """
        normalized_email = login_data.email.lower().strip()
        user = await self.user_repo.get_by_email(normalized_email)
        if not user:
            self._log_audit_event("login_failed", normalized_email, "User not found")
            return None
        
        if not verify_password(login_data.password, user.hashed_password):
            self._log_audit_event("login_failed", normalized_email, "Invalid password")
            return None
        
        if not user.is_active:
            self._log_audit_event("login_failed", normalized_email, "Account deactivated")
            return None
            
        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        await self.user_repo.update(user)
        
        self._log_audit_event("login_successful", user.email, f"User ID: {user.id}")
        return user

    async def create_user_token(self, user: User) -> dict:
        """
        Generate access token response dictionary.
        """
        expiry = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(subject=str(user.id), expires_delta=expiry)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": int(expiry.total_seconds())
        }

    async def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Decode token, retrieve user, and verify active status.
        """
        payload = decode_access_token(token)
        if not payload:
            return None
            
        user_id_str: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")
        if not user_id_str or token_type != ACCESS_TOKEN_TYPE:
            return None
            
        try:
            user_uuid = uuid.UUID(user_id_str)
        except ValueError:
            return None
            
        user = await self.user_repo.get_by_id(user_uuid)
        
        # Security rule: Inactive accounts should not continue being authenticated by a JWT
        if not user or not user.is_active:
            self._log_audit_event("token_validation_failed", user_id_str, "User not found or is inactive")
            return None
            
        return user

    def _log_audit_event(self, event_type: str, identity: str, details: str) -> None:
        """
        Extension Point: Structured logging of authentication and security events.
        Ready to feed log aggregators (Elasticsearch, CloudWatch, Datadog).
        """
        logger.info(
            f"Auth event: {event_type} | Identity: {identity}",
            extra={
                "event_type": event_type,
                "identity": identity,
                "details": details,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
