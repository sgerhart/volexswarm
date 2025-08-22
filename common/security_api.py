"""
Security API service for VolexSwarm Phase 7: Production Security
Provides authentication endpoints and security API integration.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

from .security import (
    security_manager, User, UserRole, Permission, JWTToken, 
    SecurityEvent, generate_secure_password, validate_input, sanitize_input
)
from .logging import get_logger

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer()

# API Router
security_router = APIRouter(prefix="/security", tags=["Security"])

# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int
    user: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "viewer"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    permissions: List[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class SecurityEventResponse(BaseModel):
    event_id: str
    event_type: str
    user_id: Optional[str]
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any]
    severity: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    user = security_manager.verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Dependency to check permissions
def require_permission(permission: Permission):
    """Dependency to require specific permission."""
    def permission_checker(user: User = Depends(get_current_user)):
        if not security_manager.check_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return user
    return permission_checker

# Dependency to check roles
def require_role(role: UserRole):
    """Dependency to require specific role."""
    def role_checker(user: User = Depends(get_current_user)):
        if not security_manager.check_role(user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {role.value}"
            )
        return user
    return role_checker

# Authentication endpoints
@security_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """Authenticate user and return JWT tokens."""
    # Validate input
    if not validate_input(request.username) or not validate_input(request.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data"
        )
    
    # Get client IP
    client_ip = http_request.client.host if http_request.client else None
    
    # Authenticate user
    tokens = security_manager.authenticate_user(
        username=request.username,
        password=request.password,
        ip_address=client_ip
    )
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Get user info
    user = security_manager.verify_token(tokens.access_token)
    
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_expires_in=tokens.refresh_expires_in,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions]
        }
    )

@security_router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    tokens = security_manager.refresh_token(request.refresh_token)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user info
    user = security_manager.verify_token(tokens.access_token)
    
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_expires_in=tokens.refresh_expires_in,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions]
        }
    )

@security_router.post("/logout")
async def logout(request: RefreshTokenRequest, current_user: User = Depends(get_current_user)):
    """Logout user by revoking refresh token."""
    success = security_manager.revoke_token(request.refresh_token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token"
        )
    
    return {"message": "Successfully logged out"}

@security_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        permissions=[p.value for p in current_user.permissions],
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

# User management endpoints (admin only)
@security_router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Create a new user (admin only)."""
    # Validate input
    if not validate_input(request.username) or not validate_input(request.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input data"
        )
    
    # Validate role
    try:
        role = UserRole(request.role.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
        )
    
    # Check if username already exists
    for user in security_manager.users.values():
        if user.username == request.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    # Create user
    try:
        user = security_manager.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            role=role
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        permissions=[p.value for p in user.permissions],
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )

@security_router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))):
    """List all users (admin only)."""
    users = []
    for user in security_manager.users.values():
        users.append(UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            permissions=[p.value for p in user.permissions],
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login
        ))
    
    return users

@security_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Get user by ID (admin only)."""
    if user_id not in security_manager.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = security_manager.users[user_id]
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        permissions=[p.value for p in user.permissions],
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )

@security_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Update user (admin only)."""
    if user_id not in security_manager.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = security_manager.users[user_id]
    
    # Update fields
    if request.email is not None:
        user.email = request.email
    if request.role is not None:
        try:
            role = UserRole(request.role.lower())
            user.role = role
            user.permissions = security_manager.role_permissions[role]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}"
            )
    if request.is_active is not None:
        user.is_active = request.is_active
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        permissions=[p.value for p in user.permissions],
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login
    )

@security_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))
):
    """Delete user (admin only)."""
    if user_id not in security_manager.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = security_manager.users[user_id]
    del security_manager.users[user_id]
    
    logger.info(f"User deleted: {user.username} by {current_user.username}")
    
    return {"message": f"User {user.username} deleted successfully"}

# Password management
@security_router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """Change user password."""
    # Verify current password
    hashed_password = current_user.metadata.get("hashed_password")
    if not hashed_password or not security_manager._verify_password(request.current_password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if not security_manager._validate_password(request.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password does not meet security requirements"
        )
    
    # Update password
    new_hashed_password = security_manager._hash_password(request.new_password)
    current_user.metadata["hashed_password"] = new_hashed_password
    
    logger.info(f"Password changed for user: {current_user.username}")
    
    return {"message": "Password changed successfully"}

@security_router.post("/generate-password")
async def generate_password(current_user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))):
    """Generate a secure password (admin only)."""
    password = generate_secure_password()
    
    return {"password": password}

# Security events and monitoring
@security_router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(require_permission(Permission.AUDIT_READ))
):
    """Get security events (audit permission required)."""
    events = security_manager.get_security_events(
        user_id=user_id,
        event_type=event_type,
        limit=limit
    )
    
    return [
        SecurityEventResponse(
            event_id=event.event_id,
            event_type=event.event_type,
            user_id=event.user_id,
            timestamp=event.timestamp,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            details=event.details,
            severity=event.severity
        )
        for event in events
    ]

@security_router.get("/events/{event_id}", response_model=SecurityEventResponse)
async def get_security_event(
    event_id: str,
    current_user: User = Depends(require_permission(Permission.AUDIT_READ))
):
    """Get specific security event (audit permission required)."""
    events = security_manager.get_security_events()
    
    for event in events:
        if event.event_id == event_id:
            return SecurityEventResponse(
                event_id=event.event_id,
                event_type=event.event_type,
                user_id=event.user_id,
                timestamp=event.timestamp,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                details=event.details,
                severity=event.severity
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Security event not found"
    )

# System security status
@security_router.get("/status")
async def get_security_status(current_user: User = Depends(require_permission(Permission.SYSTEM_READ))):
    """Get system security status."""
    total_users = len(security_manager.users)
    active_users = len([u for u in security_manager.users.values() if u.is_active])
    total_events = len(security_manager.security_events)
    active_tokens = len(security_manager.refresh_tokens)
    
    # Get recent security events
    recent_events = security_manager.get_security_events(limit=10)
    recent_event_types = [event.event_type for event in recent_events]
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_security_events": total_events,
        "active_refresh_tokens": active_tokens,
        "recent_event_types": recent_event_types,
        "security_config": {
            "jwt_expiration": security_manager.SECURITY_CONFIG["jwt_expiration"],
            "max_login_attempts": security_manager.SECURITY_CONFIG["max_login_attempts"],
            "rate_limit": security_manager.SECURITY_CONFIG["rate_limit"]
        }
    }

# Health check endpoint
@security_router.get("/health")
async def security_health_check():
    """Security system health check."""
    try:
        # Basic health checks
        user_count = len(security_manager.users)
        event_count = len(security_manager.security_events)
        
        return {
            "status": "healthy",
            "users_registered": user_count,
            "security_events_logged": event_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security system unhealthy"
        ) 