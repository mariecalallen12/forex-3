"""
Middleware Package
Authentication, rate limiting, and other middleware functions
"""

from .auth import (
    rate_limit,
    check_rate_limit,
    verify_token,
    create_access_token,
    get_current_user,
    get_current_user_optional,
    get_client_ip,
    extract_referral_token,
    sign_in_with_email_and_password,
    create_user_with_email_and_password,
    sign_out,
    revoke_refresh_token,
    send_email,
    AuthenticationError,
    TokenValidationError,
    RateLimitError,
    get_error_message
)

__all__ = [
    # Middleware functions
    "rate_limit", "check_rate_limit", "verify_token", "create_access_token",
    "get_current_user", "get_current_user_optional", "get_client_ip",
    "extract_referral_token", "sign_in_with_email_and_password",
    "create_user_with_email_and_password", "sign_out", "revoke_refresh_token",
    "send_email", "get_error_message",
    # Exception classes
    "AuthenticationError", "TokenValidationError", "RateLimitError"
]
