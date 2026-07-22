from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings
from app.identity.models.user import User
from app.identity.repositories.user import UserRepository
from app.identity.services.auth import AuthService
from app.identity.schemas.user import (
    UserRegister,
    UserLogin,
    UserRegisterResponse,
    TokenResponse,
    UserResponse
)

router = APIRouter()

# Setup HTTP Bearer Authentication flow for Swagger UI integration
security_scheme = HTTPBearer(
    description="JWT Bearer Token authentication. Input only the raw token."
)

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """
    Dependency injection provider for AuthService.
    """
    return AuthService(UserRepository(db))

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency resolver for obtaining the user instance associated with a JWT.
    """
    auth_service = AuthService(UserRepository(db))
    user = await auth_service.get_user_from_token(token.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency resolver ensuring the authenticated user account is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return current_user

@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Create a new user profile with email validation and secure password constraints."
)
async def register(
    register_data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        user = await auth_service.register_user(register_data)
        return {
            "message": "Registration successful.",
            "user": user
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate credentials",
    description="Validate user email and password credentials to obtain a secure JWT Access Token."
)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.authenticate_user(login_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await auth_service.create_user_token(user)

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve user profile",
    description="Returns the profile details of the currently authenticated active user.",
    dependencies=[Depends(get_current_active_user)]
)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    return current_user
