"""
Security module for VolexSwarm Phase 7: Production Security
Implements JWT authentication, RBAC, and security utilities.
"""

import os
import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Security Configuration
SECURITY_CONFIG = {
    "jwt_secret": os.getenv("JWT_SECRET", "volexswarm-jwt-secret-2024"),
    "jwt_algorithm": "HS256",
    "jwt_expiration": 3600,  # 1 hour
    "jwt_refresh_expiration": 604800,  # 7 days
    "rate_limit": 100,  # requests per minute
    "max_login_attempts": 5,
    "session_timeout": 1800,  # 30 minutes
    "password_min_length": 8,
    "password_require_special": True,
    "password_require_numbers": True,
    "password_require_uppercase": True,
}

class UserRole(Enum):
    """User roles for RBAC system."""
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SYSTEM = "system"

class Permission(Enum):
    """System permissions for RBAC."""
    # Trading permissions
    TRADE_READ = "trade:read"
    TRADE_WRITE = "trade:write"
    TRADE_EXECUTE = "trade:execute"
    
    # Strategy permissions
    STRATEGY_READ = "strategy:read"
    STRATEGY_WRITE = "strategy:write"
    STRATEGY_EXECUTE = "strategy:execute"
    
    # System permissions
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    SYSTEM_ADMIN = "system:admin"
    
    # Agent permissions
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    AGENT_CONTROL = "agent:control"
    
    # Compliance permissions
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_WRITE = "compliance:write"
    COMPLIANCE_ADMIN = "compliance:admin"
    
    # Audit permissions
    AUDIT_READ = "audit:read"
    AUDIT_WRITE = "audit:write"
    AUDIT_ADMIN = "audit:admin"

@dataclass
class User:
    """User model for authentication and authorization."""
    id: str
    username: str
    email: str
    role: UserRole
    permissions: List[Permission] = field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class JWTToken:
    """JWT token model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = SECURITY_CONFIG["jwt_expiration"]
    refresh_expires_in: int = SECURITY_CONFIG["jwt_refresh_expiration"]

@dataclass
class SecurityEvent:
    """Security event for audit logging."""
    event_id: str
    event_type: str
    user_id: Optional[str]
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"

class SecurityManager:
    """Main security manager for authentication and authorization."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
        self.rate_limit_store: Dict[str, List[datetime]] = {}
        self.security_events: List[SecurityEvent] = []
        self.role_permissions = self._initialize_role_permissions()
        
    def _initialize_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize role-based permissions."""
        return {
            UserRole.ADMIN: list(Permission),  # All permissions
            UserRole.TRADER: [
                Permission.TRADE_READ, Permission.TRADE_WRITE, Permission.TRADE_EXECUTE,
                Permission.STRATEGY_READ, Permission.STRATEGY_WRITE,
                Permission.AGENT_READ, Permission.AGENT_CONTROL,
                Permission.COMPLIANCE_READ, Permission.AUDIT_READ
            ],
            UserRole.ANALYST: [
                Permission.TRADE_READ, Permission.STRATEGY_READ, Permission.STRATEGY_WRITE,
                Permission.AGENT_READ, Permission.SYSTEM_READ,
                Permission.COMPLIANCE_READ, Permission.AUDIT_READ
            ],
            UserRole.VIEWER: [
                Permission.TRADE_READ, Permission.STRATEGY_READ,
                Permission.AGENT_READ, Permission.SYSTEM_READ,
                Permission.COMPLIANCE_READ
            ],
            UserRole.SYSTEM: [
                Permission.SYSTEM_READ, Permission.SYSTEM_WRITE,
                Permission.AGENT_READ, Permission.AGENT_WRITE, Permission.AGENT_CONTROL
            ]
        }
    
    def create_user(self, username: str, email: str, password: str, 
                   role: UserRole = UserRole.VIEWER) -> User:
        """Create a new user with hashed password."""
        if not self._validate_password(password):
            raise ValueError("Password does not meet security requirements")
        
        user_id = secrets.token_urlsafe(16)
        hashed_password = self._hash_password(password)
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=self.role_permissions[role]
        )
        
        # Store user with hashed password
        self.users[user_id] = user
        self.users[user_id].metadata["hashed_password"] = hashed_password
        
        self._log_security_event(
            "user_created",
            user_id,
            {"username": username, "email": email, "role": role.value}
        )
        
        return user
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: Optional[str] = None) -> Optional[JWTToken]:
        """Authenticate user and return JWT tokens."""
        # Find user by username
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            self._log_security_event("login_failed", None, {"username": username, "reason": "user_not_found"})
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now():
            self._log_security_event("login_failed", user.id, {"reason": "account_locked"})
            return None
        
        # Verify password
        hashed_password = user.metadata.get("hashed_password")
        if not hashed_password or not self._verify_password(password, hashed_password):
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= SECURITY_CONFIG["max_login_attempts"]:
                user.locked_until = datetime.now() + timedelta(minutes=30)
                self._log_security_event("account_locked", user.id, {"reason": "too_many_failed_attempts"})
            
            self._log_security_event("login_failed", user.id, {"reason": "invalid_password"})
            return None
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.now()
        
        # Generate tokens
        tokens = self._generate_tokens(user)
        
        self._log_security_event("login_success", user.id, {"ip_address": ip_address})
        
        return tokens
    
    def refresh_token(self, refresh_token: str) -> Optional[JWTToken]:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(
                refresh_token,
                SECURITY_CONFIG["jwt_secret"],
                algorithms=[SECURITY_CONFIG["jwt_algorithm"]]
            )
            
            user_id = payload.get("sub")
            token_id = payload.get("jti")
            
            if not user_id or user_id not in self.users:
                return None
            
            # Check if refresh token exists and is valid
            if token_id not in self.refresh_tokens:
                return None
            
            user = self.users[user_id]
            if not user.is_active:
                return None
            
            # Generate new tokens
            tokens = self._generate_tokens(user)
            
            # Remove old refresh token
            if token_id in self.refresh_tokens:
                del self.refresh_tokens[token_id]
            
            self._log_security_event("token_refreshed", user.id, {})
            
            return tokens
            
        except jwt.ExpiredSignatureError:
            self._log_security_event("token_refresh_failed", None, {"reason": "refresh_token_expired"})
            return None
        except jwt.InvalidTokenError:
            self._log_security_event("token_refresh_failed", None, {"reason": "invalid_refresh_token"})
            return None
    
    def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user."""
        try:
            payload = jwt.decode(
                token,
                SECURITY_CONFIG["jwt_secret"],
                algorithms=[SECURITY_CONFIG["jwt_algorithm"]]
            )
            
            user_id = payload.get("sub")
            if not user_id or user_id not in self.users:
                return None
            
            user = self.users[user_id]
            if not user.is_active:
                return None
            
            return user
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def check_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in user.permissions
    
    def check_role(self, user: User, role: UserRole) -> bool:
        """Check if user has specific role."""
        return user.role == role
    
    def revoke_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token."""
        try:
            payload = jwt.decode(
                refresh_token,
                SECURITY_CONFIG["jwt_secret"],
                algorithms=[SECURITY_CONFIG["jwt_algorithm"]]
            )
            
            token_id = payload.get("jti")
            if token_id in self.refresh_tokens:
                del self.refresh_tokens[token_id]
                self._log_security_event("token_revoked", payload.get("sub"), {"token_id": token_id})
                return True
            
            return False
            
        except jwt.InvalidTokenError:
            return False
    
    def _generate_tokens(self, user: User) -> JWTToken:
        """Generate access and refresh tokens for user."""
        now = datetime.utcnow()
        
        # Generate unique IDs for tokens
        access_token_id = secrets.token_urlsafe(8)
        refresh_token_id = secrets.token_urlsafe(16)
        
        # Access token payload
        access_payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "jti": access_token_id,  # Add unique ID to access token
            "iat": now,
            "exp": now + timedelta(seconds=SECURITY_CONFIG["jwt_expiration"])
        }
        
        # Refresh token payload
        refresh_payload = {
            "sub": user.id,
            "jti": refresh_token_id,
            "iat": now,
            "exp": now + timedelta(seconds=SECURITY_CONFIG["jwt_refresh_expiration"])
        }
        
        # Generate tokens
        access_token = jwt.encode(
            access_payload,
            SECURITY_CONFIG["jwt_secret"],
            algorithm=SECURITY_CONFIG["jwt_algorithm"]
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            SECURITY_CONFIG["jwt_secret"],
            algorithm=SECURITY_CONFIG["jwt_algorithm"]
        )
        
        # Store refresh token
        self.refresh_tokens[refresh_token_id] = {
            "user_id": user.id,
            "created_at": now,
            "expires_at": now + timedelta(seconds=SECURITY_CONFIG["jwt_refresh_expiration"])
        }
        
        return JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength."""
        if len(password) < SECURITY_CONFIG["password_min_length"]:
            return False
        
        if SECURITY_CONFIG["password_require_special"] and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False
        
        if SECURITY_CONFIG["password_require_numbers"] and not any(c.isdigit() for c in password):
            return False
        
        if SECURITY_CONFIG["password_require_uppercase"] and not any(c.isupper() for c in password):
            return False
        
        return True
    
    @property
    def SECURITY_CONFIG(self):
        """Get security configuration."""
        return SECURITY_CONFIG
    
    def _log_security_event(self, event_type: str, user_id: Optional[str], details: Dict[str, Any]):
        """Log security event."""
        event = SecurityEvent(
            event_id=secrets.token_urlsafe(16),
            event_type=event_type,
            user_id=user_id,
            timestamp=datetime.now(),
            details=details
        )
        
        self.security_events.append(event)
        logger.info(f"Security event: {event_type} - User: {user_id} - Details: {details}")
    
    def get_security_events(self, user_id: Optional[str] = None, 
                          event_type: Optional[str] = None,
                          limit: int = 100) -> List[SecurityEvent]:
        """Get security events with optional filtering."""
        events = self.security_events
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def cleanup_expired_tokens(self):
        """Clean up expired refresh tokens."""
        now = datetime.utcnow()
        expired_tokens = [
            token_id for token_id, token_data in self.refresh_tokens.items()
            if token_data["expires_at"] < now
        ]
        
        for token_id in expired_tokens:
            del self.refresh_tokens[token_id]

# Global security manager instance
security_manager = SecurityManager()

# Security decorators
def require_auth(permission: Optional[Permission] = None, role: Optional[UserRole] = None):
    """Decorator to require authentication and optional permission/role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be implemented in the actual API layer
            # For now, we'll just pass through
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(max_requests: int = SECURITY_CONFIG["rate_limit"], 
              window_seconds: int = 60):
    """Decorator to implement rate limiting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be implemented in the actual API layer
            # For now, we'll just pass through
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Security utilities
def generate_secure_password(length: int = 16) -> str:
    """Generate a secure random password."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Ensure password meets requirements
    if not any(c.isupper() for c in password):
        password = password[:-1] + 'A'
    if not any(c.isdigit() for c in password):
        password = password[:-1] + '1'
    if not any(c in "!@#$%^&*" for c in password):
        password = password[:-1] + '!'
    
    return password

def validate_input(input_str: str, max_length: int = 1000) -> bool:
    """Validate and sanitize input."""
    if not input_str or len(input_str) > max_length:
        return False
    
    # Check for potentially dangerous patterns
    dangerous_patterns = [
        "<script", "javascript:", "onload=", "onerror=",
        "eval(", "document.cookie", "window.location"
    ]
    
    input_lower = input_str.lower()
    for pattern in dangerous_patterns:
        if pattern in input_lower:
            return False
    
    return True

def sanitize_input(input_str: str) -> str:
    """Sanitize input string."""
    import html
    
    # HTML escape
    sanitized = html.escape(input_str)
    
    # Remove potentially dangerous characters
    sanitized = sanitized.replace("'", "&#39;")
    sanitized = sanitized.replace('"', "&#34;")
    
    return sanitized

# Initialize default admin user
def initialize_default_admin():
    """Initialize default admin user if no users exist."""
    if not security_manager.users:
        try:
            admin_user = security_manager.create_user(
                username="admin",
                email="admin@volexswarm.com",
                password="Admin123!",
                role=UserRole.ADMIN
            )
            logger.info(f"Created default admin user: {admin_user.username}")
        except Exception as e:
            logger.error(f"Failed to create default admin user: {e}")

# Initialize security system
initialize_default_admin() 