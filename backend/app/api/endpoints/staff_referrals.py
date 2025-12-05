"""
Staff Referral Management API Endpoints
Staff access to their referral codes and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from app.schemas.staff_referrals import (
    StaffReferralsResponse,
    GenerateLinkRequest,
    GenerateLinkResponse,
    ReferralStatus,
    get_mock_staff_info,
    get_mock_referral_codes,
    get_mock_referral_analytics
)

router = APIRouter()
security = HTTPBearer()

# In-memory storage cho development
referral_links_storage = {}
referral_codes_storage = {}


async def verify_staff_session(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Verify staff session từ token
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
    
    # Mock staff session
    return {
        "uid": "staff_uid",
        "email": "staff@example.com",
        "displayName": "Staff Member",
        "staffId": "STAFF001",
        "role": "staff"
    }


async def get_referral_codes_by_staff(staff_id: str) -> List[dict]:
    """
    Lấy referral codes cho staff
    Trong production sẽ query database
    """
    # Check if codes exist in storage, if not create default
    storage_key = f"staff_{staff_id}_codes"
    if storage_key not in referral_codes_storage:
        referral_codes_storage[storage_key] = get_mock_referral_codes()
    
    return referral_codes_storage[storage_key]


async def get_referral_analytics(staff_id: str) -> dict:
    """
    Lấy referral analytics cho staff
    Trong production sẽ tính toán từ database
    """
    return get_mock_referral_analytics()


async def generate_referral_link(staff_id: str, code_id: str, expiry_days: int) -> dict:
    """
    Tạo referral link với thời hạn xác định
    """
    # Mock URL generation
    base_url = "https://app.digitalutopia.com/ref"
    referral_code = "DUABC123"  # Mock code
    
    expires_at = datetime.utcnow() + timedelta(days=expiry_days)
    
    # Generate unique link ID
    link_id = str(uuid.uuid4())
    
    # Store in memory for development
    referral_links_storage[link_id] = {
        "id": link_id,
        "url": f"{base_url}/{referral_code}",
        "code": referral_code,
        "expiresAt": expires_at,
        "staffId": staff_id,
        "createdAt": datetime.utcnow(),
        "clicks": 0,
        "conversions": 0
    }
    
    return referral_links_storage[link_id]


@router.get(
    "/referrals",
    response_model=StaffReferralsResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin referrals của staff",
    tags=["staff-referrals"]
)
async def get_staff_referrals(
    request: Request,
    staff_session: dict = Depends(verify_staff_session)
):
    """
    Lấy thông tin mã giới thiệu của staff
    
    Bao gồm:
    - Referral analytics
    - Referral codes của staff  
    - Thông tin staff
    """
    try:
        staff_id = staff_session["staffId"]
        
        # Get referral analytics
        analytics = await get_referral_analytics(staff_id)
        
        # Get referral codes for this staff
        referral_codes = await get_referral_codes_by_staff(staff_id)
        
        # Get staff info
        staff_info = get_mock_staff_info()
        
        return StaffReferralsResponse(
            analytics=analytics,
            referralCodes=referral_codes,
            staffInfo=staff_info
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Get staff referrals error:", error)
        
        error_message = str(error) if error else "Không thể lấy thông tin mã giới thiệu"
        
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


@router.post(
    "/referrals/generate-link",
    response_model=GenerateLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo link giới thiệu mới",
    tags=["staff-referrals"]
)
async def generate_referral_link_endpoint(
    request: Request,
    generate_request: GenerateLinkRequest,
    staff_session: dict = Depends(verify_staff_session)
):
    """
    Tạo link giới thiệu mới cho staff
    
    Args:
        expiryDays: Số ngày hết hạn (1-365, mặc định 30)
    
    Returns:
        Link giới thiệu với URL và thời hạn hết hạn
    """
    try:
        staff_id = staff_session["staffId"]
        
        # Get active referral code for staff
        referral_codes = await get_referral_codes_by_staff(staff_id)
        active_code = None
        
        for code in referral_codes:
            if code.status == ReferralStatus.ACTIVE:
                active_code = code
                break
        
        if not active_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không có mã giới thiệu hoạt động"
            )
        
        # Generate referral link
        referral_link = await generate_referral_link(
            staff_id,
            active_code.id,
            generate_request.expiryDays
        )
        
        return GenerateLinkResponse(
            message="Tạo link giới thiệu thành công",
            data=referral_link
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
        print("Generate referral link error:", error)
        
        error_message = str(error) if error else "Không thể tạo link giới thiệu"
        
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
    "/referrals/links",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách links đã tạo",
    tags=["staff-referrals"]
)
async def get_staff_referral_links(
    request: Request,
    staff_session: dict = Depends(verify_staff_session)
):
    """
    Lấy danh sách tất cả referral links đã tạo cho staff
    """
    try:
        staff_id = staff_session["staffId"]
        
        # Filter links by staff_id
        staff_links = [
            link for link in referral_links_storage.values()
            if link["staffId"] == staff_id
        ]
        
        return staff_links
        
    except Exception as error:
        print("Get referral links error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy danh sách links giới thiệu"
        )


@router.delete(
    "/referrals/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa referral link",
    tags=["staff-referrals"]
)
async def delete_referral_link(
    link_id: str,
    request: Request,
    staff_session: dict = Depends(verify_staff_session)
):
    """
    Xóa referral link (vô hiệu hóa)
    """
    try:
        staff_id = staff_session["staffId"]
        
        # Check if link exists and belongs to staff
        if link_id not in referral_links_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link giới thiệu không tồn tại"
            )
        
        link = referral_links_storage[link_id]
        if link["staffId"] != staff_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền xóa link này"
            )
        
        # Mark as expired instead of deleting
        referral_links_storage[link_id]["expiresAt"] = datetime.utcnow()
        
        return None
        
    except HTTPException:
        raise
    except Exception as error:
        print("Delete referral link error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể xóa link giới thiệu"
        )