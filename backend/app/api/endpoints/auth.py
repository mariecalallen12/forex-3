"""
Authentication Endpoints - Migration từ Next.js API
Bao gồm: login, register, logout, refresh token, verify token
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from typing import Optional
import asyncio

# Import schemas
from ...schemas.auth import (
    LoginRequest,
    RegisterRequest,
    LoginResponse,
    RegisterResponse,
    LogoutResponse,
    RefreshTokenResponse,
    VerifyTokenResponse,
    AuthErrorResponse,
    ValidationErrorResponse,
    UserData
)

# Import middleware functions
from ...middleware.auth import (
    get_client_ip,
    rate_limit,
    verify_token,
    sign_in_with_email_and_password,
    create_user_with_email_and_password,
    sign_out,
    revoke_refresh_token,
    send_email,
    extract_referral_token,
    get_error_message,
    create_access_token,
    AuthenticationError,
    TokenValidationError,
    RateLimitError
)

# Import placeholder services (sẽ được migrate sau)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

router = APIRouter(tags=["authentication"])

# ========== LOGIN ENDPOINT ==========

@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {"model": LoginResponse, "description": "Đăng nhập thành công"},
        400: {"model": ValidationErrorResponse, "description": "Dữ liệu đầu vào không hợp lệ"},
        401: {"model": AuthErrorResponse, "description": "Đăng nhập thất bại"},
        429: {"model": AuthErrorResponse, "description": "Quá nhiều yêu cầu"}
    }
)
async def login(request: Request, login_data: LoginRequest):
    """
    Đăng nhập người dùng - tương tự Next.js POST /api/auth/login
    Bao gồm cả GET /api/auth/login (verify token) trong cùng endpoint
    """
    
    # Handle GET request for token verification
    if request.method == "GET":
        return await verify_token_endpoint(request)
    
    # Handle POST request for login
    try:
        # Apply rate limiting
        client_ip = get_client_ip(request)
        await rate_limit(client_ip, "login")

        # Sign in with Firebase Auth equivalent
        user_credential = await sign_in_with_email_and_password(
            login_data.email, 
            login_data.password
        )
        
        # Create custom token (equivalent to Firebase ID token)
        user_data = {
            "uid": user_credential["user"]["uid"],
            "email": user_credential["user"]["email"],
            "email_verified": user_credential["user"]["emailVerified"],
            "display_name": user_credential["user"]["displayName"],
            "photo_url": user_credential["user"]["photoURL"],
            "disabled": user_credential["user"]["disabled"],
        }
        
        # Generate JWT token
        id_token = create_access_token(user_data)

        # TODO: Update last login in database (equivalent to Firebase updateUser)
        # await update_user_last_login(user_credential["user"]["uid"])

        return LoginResponse(
            success=True,
            message="Đăng nhập thành công",
            data={
                "user": UserData(
                    uid=user_data["uid"],
                    email=user_data["email"],
                    emailVerified=user_data["email_verified"],
                    displayName=user_data["display_name"],
                    photoURL=user_data["photo_url"],
                    disabled=user_data["disabled"],
                ),
                "token": id_token,
                "expiresIn": "1h",
            }
        )

    except RateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    
    except AuthenticationError as e:
        # Handle specific Firebase auth errors
        error_message = get_error_message(e, "auth")
        
        # Apply additional rate limiting for failed login attempts
        client_ip = get_client_ip(request)
        await rate_limit(client_ip, "login-failed")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        print(f"Login error: {e}")
        
        # Handle validation errors (equivalent to Zod errors)
        if "validation" in str(e).lower() or "invalid" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dữ liệu đầu vào không hợp lệ"
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Đăng nhập thất bại"
        )

# ========== VERIFY TOKEN ENDPOINT (GET /api/auth/login) ==========

async def verify_token_endpoint(request: Request) -> VerifyTokenResponse:
    """
    Verify current token - tương tự Next.js GET /api/auth/login
    """
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        
        # TODO: Get user details from database (equivalent to Firebase getUser)
        # user_doc = await get_user_from_database(decoded_token["uid"])
        
        # Placeholder user data (will be replaced with database query)
        user_data = {
            "uid": decoded_token["uid"],
            "email": decoded_token["email"],
            "email_verified": decoded_token.get("email_verified", False),
            "display_name": decoded_token.get("display_name"),
            "photo_url": decoded_token.get("photo_url"),
            "disabled": decoded_token.get("disabled", False),
        }

        return VerifyTokenResponse(
            success=True,
            data={
                "user": UserData(
                    uid=user_data["uid"],
                    email=user_data["email"],
                    emailVerified=user_data["email_verified"],
                    displayName=user_data["display_name"],
                    photoURL=user_data["photo_url"],
                    disabled=user_data["disabled"],
                ),
            }
        )

    except TokenValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )

# ========== REGISTER ENDPOINT ==========

@router.post(
    "/register",
    response_model=RegisterResponse,
    responses={
        201: {"model": RegisterResponse, "description": "Đăng ký thành công"},
        400: {"model": ValidationErrorResponse, "description": "Dữ liệu đầu vào không hợp lệ"},
        429: {"model": AuthErrorResponse, "description": "Quá nhiều yêu cầu"}
    }
)
async def register(request: Request, register_data: RegisterRequest):
    """
    Đăng ký tài khoản mới - tương tự Next.js POST /api/auth/register
    Bao gồm referral system validation
    """
    
    try:
        # Apply rate limiting
        client_ip = get_client_ip(request)
        await rate_limit(client_ip, "register")

        # Check referral requirement
        ref_token = extract_referral_token(request)
        
        # Validate referral requirement
        if not register_data.referralCode and not ref_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn cần Mã giới thiệu hoặc truy cập từ Link giới thiệu của nhân viên hỗ trợ để đăng ký. Vui lòng liên hệ nhân viên chăm sóc để nhận thông tin.",
                headers={
                    "X-Requires-Referral": "true",
                    "X-Referral-Error": "true"
                }
            )

        # Get user agent for tracking
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # TODO: Process registration with referral tracking
        # registration_record = await referralSystem.processRegistration(...)
        
        # Placeholder referral processing result
        registration_record = {
            "id": "reg_" + str(int(asyncio.get_event_loop().time())),
            "sourceRefType": "MANUAL" if register_data.referralCode else "LINK",
            "sourceRefCode": register_data.referralCode or ref_token,
            "sourceRefStaffId": "staff_123",
            "sourceRefStaffName": "Nhân viên hỗ trợ",
            "conflictDetected": False
        }

        # Create user - equivalent to Firebase createUserWithEmailAndPassword
        user_credential = await create_user_with_email_and_password(
            register_data.email,
            register_data.password,
            register_data.displayName
        )
        
        # TODO: Update user profile (equivalent to Firebase updateUser)
        # await firebase_auth.updateUser(user_credential["user"]["uid"], {
        #     displayName=register_data.displayName,
        #     emailVerified=False,
        #     lastLoginAt=datetime.now().isoformat(),
        # })

        # TODO: Create user document in database (equivalent to Firestore)
        # await create_user_document(user_credential["user"]["uid"], user_data)

        # Send verification email
        verification_link = f"https://digital-utopia.app/verify-email?token=placeholder_token"
        
        await send_email({
            "to": register_data.email,
            "template": "registration_pending",
            "subject": "Đăng ký thành công - Chờ phê duyệt từ quản trị viên",
            "data": {
                "displayName": register_data.displayName,
                "verificationLink": verification_link,
                "staffName": registration_record["sourceRefStaffName"],
                "referralSource": "Link giới thiệu" if registration_record["sourceRefType"] == "LINK" else "Mã giới thiệu",
            }
        })

        # TODO: Disable user until approved (equivalent to Firebase disabled: true)
        # await firebase_auth.updateUser(user_credential["user"]["uid"], {
        #     disabled: True,  # Disable until owner approves
        # })

        return RegisterResponse(
            success=True,
            message="Đăng ký thành công. Tài khoản của bạn đang chờ phê duyệt từ quản trị viên. Chúng tôi sẽ thông báo khi tài khoản được kích hoạt.",
            data={
                "user": {
                    "uid": user_credential["user"]["uid"],
                    "email": register_data.email,
                    "displayName": register_data.displayName,
                    "approvalStatus": "pending",
                    "registrationId": registration_record["id"],
                    "staffName": registration_record["sourceRefStaffName"],
                },
                "needsApproval": True,
            },
            needsApproval=True
        )

    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Register error: {e}")
        
        # Handle validation errors
        if "validation" in str(e).lower() or "invalid" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dữ liệu đầu vào không hợp lệ"
            )
        
        # Handle Firebase auth errors
        error_message = get_error_message(e, "auth")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

# ========== LOGOUT ENDPOINT ==========

@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={
        200: {"model": LogoutResponse, "description": "Đăng xuất thành công"},
        401: {"model": AuthErrorResponse, "description": "Không tìm thấy token xác thực"}
    }
)
async def logout(request: Request):
    """
    Đăng xuất người dùng - tương tự Next.js POST /api/auth/logout
    """
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        
        # Verify token before logout
        decoded_token = verify_token(token)
        
        # Sign out from system (equivalent to Firebase signOut)
        await sign_out()

        # Revoke refresh token to ensure complete logout (equivalent to Firebase revokeRefreshToken)
        try:
            await revoke_refresh_token(decoded_token["uid"])
        except Exception as revoke_error:
            # Continue logout even if token revocation fails
            print(f"Warning: Token revocation failed: {revoke_error}")

        return LogoutResponse(
            success=True,
            message="Đăng xuất thành công"
        )

    except TokenValidationError as e:
        # Even if token validation fails, consider logout successful
        # This matches Next.js behavior
        return LogoutResponse(
            success=True,
            message="Đăng xuất thành công"
        )
    
    except HTTPException:
        # Even if token is missing, consider logout successful
        # This matches Next.js behavior
        return LogoutResponse(
            success=True,
            message="Đăng xuất thành công"
        )
    
    except Exception as e:
        print(f"Logout error: {e}")
        
        # Even if logout fails, return success to match Next.js behavior
        return LogoutResponse(
            success=True,
            message="Đăng xuất thành công"
        )

# ========== REFRESH TOKEN ENDPOINT ==========

@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    responses={
        200: {"model": RefreshTokenResponse, "description": "Token đã được làm mới"},
        401: {"model": AuthErrorResponse, "description": "Không thể làm mới token"}
    }
)
async def refresh_token(request: Request):
    """
    Làm mới access token - tương tự Next.js POST /api/auth/refresh
    """
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        current_token = auth_header.split(" ")[1]
        
        # Verify current token
        decoded_token = verify_token(current_token)
        
        # Create new token with updated expiration
        new_token = create_access_token({
            "uid": decoded_token["uid"],
            "email": decoded_token["email"],
            "email_verified": decoded_token.get("email_verified", False),
            "display_name": decoded_token.get("display_name"),
            "photo_url": decoded_token.get("photo_url"),
            "disabled": decoded_token.get("disabled", False),
        })

        return RefreshTokenResponse(
            success=True,
            message="Token đã được làm mới",
            data={
                "token": new_token,
                "expiresIn": "1h",
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

    except TokenValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không thể làm mới token. Vui lòng đăng nhập lại"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không thể làm mới token. Vui lòng đăng nhập lại"
        )

# ========== ADDITIONAL UTILITY ENDPOINTS ==========

@router.get("/verify")
async def verify_token_get(request: Request) -> VerifyTokenResponse:
    """
    Standalone token verification endpoint (alternative to GET /login)
    """
    return await verify_token_endpoint(request)

@router.get("/rate-limit/{endpoint}")
async def check_rate_limit_status(endpoint: str, request: Request):
    """
    Check current rate limit status for an endpoint
    """
    from ...middleware.auth import check_rate_limit
    
    client_ip = get_client_ip(request)
    status = await check_rate_limit(client_ip, endpoint)
    
    return {
        "endpoint": endpoint,
        "client_ip": client_ip,
        "status": status
    }
