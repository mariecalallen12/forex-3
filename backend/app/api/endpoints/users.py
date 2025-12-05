"""
User Management API Endpoints
User profile management và account operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.schemas.users import (
    UserProfileResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    DeleteAccountResponse,
    UserProfile,
    UserStatus,
    get_mock_user_profile,
    get_mock_user_preferences,
    get_mock_user_activity
)

router = APIRouter()
security = HTTPBearer()

# In-memory storage cho development
user_profiles_storage = {}
user_activity_storage = {}
user_preferences_storage = {}


async def verify_user_session(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Verify user session từ token
    Trong production sẽ verify JWT/Firebase token
    """
    token = credentials.credentials
    
    # Mock verification - trong production sẽ verify JWT/Firebase token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy token xác thực",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mock user session
    return {
        "uid": "user_001",
        "email": "user@example.com",
        "displayName": "Nguyễn Văn A",
        "role": "user"
    }


async def get_user_profile(user_id: str) -> UserProfile:
    """
    Lấy user profile từ storage
    Trong production sẽ query database
    """
    storage_key = f"user_{user_id}_profile"
    
    # Check if profile exists in storage, if not create default
    if storage_key not in user_profiles_storage:
        profile = get_mock_user_profile()
        profile.id = user_id
        user_profiles_storage[storage_key] = profile
    else:
        profile = user_profiles_storage[storage_key]
    
    return profile


async def check_user_trades(user_id: str) -> bool:
    """
    Kiểm tra user có active trades không
    Trong production sẽ query database
    """
    # Mock check - assume no active trades in development
    return False


@router.get(
    "/api/users",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin user profile",
    tags=["users"]
)
async def get_user_profile_endpoint(
    request: Request,
    user_session: dict = Depends(verify_user_session)
):
    """
    Lấy thông tin profile của user hiện tại
    
    Bao gồm:
    - Thông tin cá nhân
    - Trạng thái tài khoản
    - Preferences
    - Activity history
    """
    try:
        user_id = user_session["uid"]
        
        # Get user profile
        profile = await get_user_profile(user_id)
        
        # Check if user account is active
        if profile.status == UserStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tài khoản đã bị xóa"
            )
        
        if profile.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị tạm dừng"
            )
        
        # Update last login
        profile.lastLoginAt = datetime.utcnow()
        
        return UserProfileResponse(
            success=True,
            data=profile
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Get user profile error:", error)
        
        error_message = str(error) if error else "Không thể lấy thông tin người dùng"
        
        if "Unauthorized" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )


@router.put(
    "/api/users",
    response_model=UpdateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật user profile",
    tags=["users"]
)
async def update_user_profile_endpoint(
    request: Request,
    update_request: UpdateProfileRequest,
    user_session: dict = Depends(verify_user_session)
):
    """
    Cập nhật thông tin profile của user
    
    Args:
        displayName: Tên hiển thị (2-50 ký tự)
        phoneNumber: Số điện thoại
        avatar: URL ảnh đại diện
        firstName: Tên
        lastName: Họ
        address: Địa chỉ
        city: Thành phố
        country: Quốc gia
    
    Returns:
        Danh sách fields đã được cập nhật
    """
    try:
        user_id = user_session["uid"]
        
        # Get current profile
        profile = await get_user_profile(user_id)
        
        # Check if user account is active
        if profile.status == UserStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tài kản đã bị xóa"
            )
        
        if profile.status == UserStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản đã bị tạm dừng"
            )
        
        # Update fields
        updated_fields = []
        
        if update_request.displayName is not None:
            profile.displayName = update_request.displayName
            updated_fields.append("displayName")
        
        if update_request.phoneNumber is not None:
            profile.phoneNumber = update_request.phoneNumber
            updated_fields.append("phoneNumber")
        
        if update_request.avatar is not None:
            profile.avatar = update_request.avatar
            updated_fields.append("avatar")
        
        if update_request.firstName is not None:
            profile.firstName = update_request.firstName
            updated_fields.append("firstName")
        
        if update_request.lastName is not None:
            profile.lastName = update_request.lastName
            updated_fields.append("lastName")
        
        if update_request.address is not None:
            profile.address = update_request.address
            updated_fields.append("address")
        
        if update_request.city is not None:
            profile.city = update_request.city
            updated_fields.append("city")
        
        if update_request.country is not None:
            profile.country = update_request.country
            updated_fields.append("country")
        
        # Update timestamp
        profile.updatedAt = datetime.utcnow()
        
        # Save to storage
        storage_key = f"user_{user_id}_profile"
        user_profiles_storage[storage_key] = profile
        
        # Log activity
        activity_key = f"user_{user_id}_activity"
        if activity_key not in user_activity_storage:
            user_activity_storage[activity_key] = []
        
        user_activity_storage[activity_key].append({
            "action": "profile_updated",
            "timestamp": datetime.utcnow(),
            "details": {"fields": updated_fields},
            "ipAddress": request.client.host if request.client else None,
            "userAgent": request.headers.get("user-agent")
        })
        
        return UpdateProfileResponse(
            success=True,
            message="Cập nhật thông tin thành công",
            data={
                "updatedFields": updated_fields,
                "updatedAt": profile.updatedAt.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dữ liệu đầu vào không hợp lệ",
            headers={"X-Error": str(error)}
        )
    except Exception as error:
        print("Update user profile error:", error)
        
        error_message = str(error) if error else "Không thể cập nhật thông tin"
        
        if "Unauthorized" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )


@router.delete(
    "/api/users",
    response_model=DeleteAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Xóa tài khoản người dùng",
    tags=["users"]
)
async def delete_user_account_endpoint(
    request: Request,
    user_session: dict = Depends(verify_user_session)
):
    """
    Xóa tài khoản người dùng (soft delete)
    
    Kiểm tra:
    - Không có giao dịch đang chờ xử lý
    - Tài khoản đang active
    
    Returns:
        Thông báo xóa thành công
    """
    try:
        user_id = user_session["uid"]
        
        # Get current profile
        profile = await get_user_profile(user_id)
        
        # Check if user account is already deleted
        if profile.status == UserStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tài khoản đã bị xóa trước đó"
            )
        
        # Check if user has active trades
        has_active_trades = await check_user_trades(user_id)
        if has_active_trades:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa tài khoản khi còn giao dịch chưa hoàn tất"
            )
        
        # Soft delete - update status instead of actually deleting
        profile.status = UserStatus.DELETED
        profile.isActive = False
        profile.deletedAt = datetime.utcnow()
        profile.updatedAt = datetime.utcnow()
        
        # Save to storage
        storage_key = f"user_{user_id}_profile"
        user_profiles_storage[storage_key] = profile
        
        # Log activity
        activity_key = f"user_{user_id}_activity"
        if activity_key not in user_activity_storage:
            user_activity_storage[activity_key] = []
        
        user_activity_storage[activity_key].append({
            "action": "account_deleted",
            "timestamp": datetime.utcnow(),
            "details": {"method": "soft_delete"},
            "ipAddress": request.client.host if request.client else None,
            "userAgent": request.headers.get("user-agent")
        })
        
        return DeleteAccountResponse(
            success=True,
            message="Tài khoản đã được xóa thành công"
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Delete user account error:", error)
        
        error_message = str(error) if error else "Không thể xóa tài khoản"
        
        if "Unauthorized" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )


@router.get(
    "/api/users/preferences",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Lấy user preferences",
    tags=["users"]
)
async def get_user_preferences_endpoint(
    request: Request,
    user_session: dict = Depends(verify_user_session)
):
    """
    Lấy preferences và settings của user
    """
    try:
        user_id = user_session["uid"]
        
        # Check if user account is active
        profile = await get_user_profile(user_id)
        if profile.status == UserStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tài khoản đã bị xóa"
            )
        
        # Get or create preferences
        storage_key = f"user_{user_id}_preferences"
        if storage_key not in user_preferences_storage:
            user_preferences_storage[storage_key] = get_mock_user_preferences()
        
        return user_preferences_storage[storage_key]
        
    except Exception as error:
        print("Get user preferences error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy preferences"
        )


@router.get(
    "/api/users/activity",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Lấy user activity history",
    tags=["users"]
)
async def get_user_activity_endpoint(
    request: Request,
    limit: Optional[int] = Query(50, ge=1, le=100, description="Số lượng records"),
    user_session: dict = Depends(verify_user_session)
):
    """
    Lấy lịch sử hoạt động của user
    """
    try:
        user_id = user_session["uid"]
        
        # Check if user account is active
        profile = await get_user_profile(user_id)
        if profile.status == UserStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tài khoản đã bị xóa"
            )
        
        # Get activity history
        activity_key = f"user_{user_id}_activity"
        if activity_key in user_activity_storage:
            activities = user_activity_storage[activity_key]
            # Return most recent activities limited by parameter
            return activities[-limit:] if limit < len(activities) else activities
        else:
            return []
        
    except Exception as error:
        print("Get user activity error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy lịch sử hoạt động"
        )