"""
Admin Endpoints - Migration từ Next.js API
Bao gồm: users, customers, deposits, platform stats, referrals, subaccounts, trading adjustments, user performance
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status, Query, Path
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime, timedelta
from enum import Enum

# Import schemas
from ...schemas.admin import (
    # User management
    GetUsersRequest,
    UpdateUserRequest,
    UsersResponse,
    UserResponse,
    AdminUser,
    
    # Customer management
    GetCustomersRequest,
    CustomersResponse,
    AdminCustomer,
    
    # Deposit management
    DepositDetailRequest,
    DepositDetailResponse,
    AdminDeposit,
    
    # Platform statistics
    PlatformStatsResponse,
    PlatformStats,
    
    # Referral management
    GetReferralsRequest,
    ReferralsResponse,
    ReferralRecord,
    
    # Subaccount management
    GetSubaccountsRequest,
    SubaccountsResponse,
    Subaccount,
    
    # Trading adjustments
    GetTradingAdjustmentsRequest,
    TradingAdjustmentsResponse,
    TradingAdjustment,
    
    # User performance
    UserPerformanceRequest,
    UserPerformanceResponse,
    UserPerformance,
    
    # Error schemas
    AdminErrorResponse,
    AdminValidationErrorResponse,
    
    # Enums
    UserRole,
    UserStatus,
    KYCStatus
)

# Import middleware functions
from ...middleware.auth import (
    verify_token,
    TokenValidationError,
    get_client_ip,
    rate_limit,
    require_admin_role
)

router = APIRouter(tags=["admin"])

# ========== ADMIN USER MANAGEMENT ENDPOINTS ==========

@router.get(
    "/users",
    response_model=UsersResponse,
    responses={
        200: {"model": UsersResponse, "description": "Lấy danh sách users thành công"},
        401: {"model": AdminErrorResponse, "description": "Không có quyền truy cập"},
        403: {"model": AdminErrorResponse, "description": "Cần quyền admin"},
        500: {"model": AdminErrorResponse, "description": "Lỗi hệ thống"}
    }
)
async def get_users(
    request: Request,
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo email"),
    role: Optional[UserRole] = Query(None, description="Lọc theo role"),
    status: Optional[UserStatus] = Query(None, description="Lọc theo status"),
    kyc_status: Optional[KYCStatus] = Query(None, alias="kycStatus", description="Lọc theo KYC status"),
    sort_by: str = Query("createdAt", alias="sortBy", description="Sắp xếp theo"),
    sort_order: str = Query("desc", alias="sortOrder", description="Thứ tự sắp xếp")
):
    """
    Lấy danh sách users - tương tự Next.js GET /api/admin/users
    Hỗ trợ filtering, pagination và sorting
    """
    
    try:
        # Verify authentication and admin role
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        
        # Check admin role
        if not require_admin_role(decoded_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cần quyền admin để truy cập"
            )

        # TODO: Replace with actual database query
        # Simulate database query with filtering and pagination
        all_users = [
            AdminUser(
                id="user_001",
                email="user1@example.com",
                displayName="Nguyễn Văn A",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                kycStatus=KYCStatus.VERIFIED,
                isActive=True,
                phoneNumber="+84123456789",
                emailVerified=True,
                phoneVerified=True,
                balance={"usdt": 1000.50, "btc": 0.05, "eth": 0.1},
                lastLoginAt=datetime.now() - timedelta(hours=2),
                createdAt=datetime.now() - timedelta(days=30),
                updatedAt=datetime.now() - timedelta(days=1)
            ),
            AdminUser(
                id="user_002",
                email="user2@example.com",
                displayName="Trần Thị B",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                kycStatus=KYCStatus.PENDING,
                isActive=True,
                phoneNumber="+84987654321",
                emailVerified=True,
                phoneVerified=False,
                balance={"usdt": 500.25, "btc": 0.02},
                lastLoginAt=datetime.now() - timedelta(days=1),
                createdAt=datetime.now() - timedelta(days=15),
                updatedAt=datetime.now() - timedelta(days=2)
            ),
            AdminUser(
                id="admin_001",
                email="admin@example.com",
                displayName="Quản trị viên",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                kycStatus=KYCStatus.VERIFIED,
                isActive=True,
                phoneNumber="+85512345678",
                emailVerified=True,
                phoneVerified=True,
                balance={"usdt": 0, "btc": 0, "eth": 0},
                lastLoginAt=datetime.now(),
                createdAt=datetime.now() - timedelta(days=60),
                updatedAt=datetime.now() - timedelta(hours=1)
            )
        ]

        # Apply filters
        filtered_users = all_users
        
        if search:
            filtered_users = [u for u in filtered_users if search.lower() in u.email.lower()]
        
        if role:
            filtered_users = [u for u in filtered_users if u.role == role]
        
        if status:
            filtered_users = [u for u in filtered_users if u.status == status]
        
        if kyc_status:
            filtered_users = [u for u in filtered_users if u.kyc_status == kyc_status]

        # Sort users
        reverse_sort = sort_order.lower() == "desc"
        if sort_by in ["email", "displayName"]:
            filtered_users.sort(key=lambda x: getattr(x, sort_by, "") or "", reverse=reverse_sort)
        else:
            filtered_users.sort(key=lambda x: getattr(x, sort_by, datetime.min), reverse=reverse_sort)

        # Apply pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_users = filtered_users[start_index:end_index]

        # Convert to dict format (matching Next.js response)
        users_data = []
        for user in paginated_users:
            user_dict = user.dict()
            user_dict["createdAt"] = user.createdAt.isoformat()
            user_dict["updatedAt"] = user.updatedAt.isoformat() if user.updatedAt else None
            user_dict["lastLoginAt"] = user.lastLoginAt.isoformat() if user.lastLoginAt else None
            users_data.append(user_dict)

        # Calculate pagination info
        total_users = len(filtered_users)
        total_pages = (total_users + limit - 1) // limit

        response_data = {
            "users": users_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_users,
                "totalPages": total_pages
            }
        }

        return UsersResponse(
            success=True,
            data=response_data
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Get users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy danh sách người dùng"
        )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        200: {"model": UserResponse, "description": "Cập nhật user thành công"},
        400: {"model": AdminValidationErrorResponse, "description": "Dữ liệu đầu vào không hợp lệ"},
        401: {"model": AdminErrorResponse, "description": "Không có quyền truy cập"},
        403: {"model": AdminErrorResponse, "description": "Cần quyền admin"},
        404: {"model": AdminErrorResponse, "description": "Không tìm thấy user"},
        500: {"model": AdminErrorResponse, "description": "Lỗi hệ thống"}
    }
)
async def update_user(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    update_data: UpdateUserRequest = None
):
    """
    Cập nhật thông tin user - tương tự Next.js PUT /api/admin/users/:userId
    Hỗ trợ cập nhật role, status, KYC status, balance
    """
    
    try:
        # Verify authentication and admin role
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        
        # Check admin role
        if not require_admin_role(decoded_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cần quyền admin để truy cập"
            )

        # For PUT requests with body
        if request.method == "PUT":
            if not update_data:
                update_data = await request.json()
                update_data = UpdateUserRequest(**update_data)

        # TODO: Check if user exists in database
        # user_doc = await get_user_from_database(user_id)
        # if not user_doc:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Không tìm thấy người dùng"
        #     )

        # Simulate user not found for invalid IDs
        if user_id not in ["user_001", "user_002", "admin_001"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng"
            )

        # Simulate user data
        user_data = {
            "id": user_id,
            "email": f"user_{user_id}@example.com",
            "kycStatus": KYCStatus.PENDING
        }

        # TODO: Update user data in database
        # await update_user_in_database(user_id, update_data.dict())

        # TODO: Send KYC status change notifications
        if update_data.kycStatus and update_data.kycStatus != user_data["kycStatus"]:
            # Send email notification based on KYC status
            # await sendKYCNotificationEmail(user_id, update_data.kycStatus)
            pass

        # Determine which fields were updated
        updated_fields = []
        if update_data.role is not None:
            updated_fields.append("role")
        if update_data.status is not None:
            updated_fields.append("status")
        if update_data.kycStatus is not None:
            updated_fields.append("kycStatus")
        if update_data.isActive is not None:
            updated_fields.append("isActive")
        if update_data.balance is not None:
            updated_fields.append("balance")

        return UserResponse(
            success=True,
            message="Cập nhật thông tin người dùng thành công",
            data={
                "updatedFields": updated_fields
            },
            updatedFields=updated_fields
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể cập nhật thông tin người dùng"
        )


@router.delete(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        200: {"model": UserResponse, "description": "Xóa user thành công"},
        400: {"model": AdminErrorResponse, "description": "Không thể xóa user có giao dịch đang chờ"},
        401: {"model": AdminErrorResponse, "description": "Không có quyền truy cập"},
        403: {"model": AdminErrorResponse, "description": "Cần quyền admin"},
        404: {"model": AdminErrorResponse, "description": "Không tìm thấy user"},
        500: {"model": AdminErrorResponse, "description": "Lỗi hệ thống"}
    }
)
async def delete_user(
    request: Request,
    user_id: str = Path(..., description="User ID")
):
    """
    Xóa user (soft delete) - tương tự Next.js DELETE /api/admin/users/:userId
    Kiểm tra giao dịch đang chờ trước khi xóa
    """
    
    try:
        # Verify authentication and admin role
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        
        # Check admin role
        if not require_admin_role(decoded_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cần quyền admin để truy cập"
            )

        # TODO: Check if user exists
        # user_doc = await get_user_from_database(user_id)
        # if not user_doc:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Không tìm thấy người dùng"
        #     )

        # Simulate user not found for invalid IDs
        if user_id not in ["user_001", "user_002", "admin_001"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng"
            )

        # TODO: Check for active trades or pending transactions
        # active_trades = await get_active_trades_for_user(user_id)
        # if active_trades:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Không thể xóa người dùng khi còn giao dịch chưa hoàn tất"
        #     )

        # Simulate check for invalid user IDs
        if user_id == "user_with_pending_trades":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa người dùng khi còn giao dịch chưa hoàn tất"
            )

        # TODO: Soft delete user (update status instead of actual deletion)
        # await soft_delete_user(user_id)
        # await disable_firebase_user(user_id)

        return UserResponse(
            success=True,
            message="Đã xóa người dùng thành công"
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể xóa người dùng"
        )


# ========== ADMIN CUSTOMERS ENDPOINT ==========

@router.get(
    "/customers",
    response_model=CustomersResponse,
    responses={
        200: {"model": CustomersResponse, "description": "Lấy danh sách customers thành công"},
        401: {"model": AdminErrorResponse, "description": "Không có quyền truy cập"},
        403: {"model": AdminErrorResponse, "description": "Cần quyền admin"}
    }
)
async def get_customers(
    request: Request,
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo email hoặc tên"),
    kyc_status: Optional[KYCStatus] = Query(None, alias="kycStatus", description="Lọc theo KYC status"),
    is_active: Optional[bool] = Query(None, alias="isActive", description="Lọc theo trạng thái hoạt động"),
    sort_by: str = Query("registrationDate", alias="sortBy", description="Sắp xếp theo"),
    sort_order: str = Query("desc", alias="sortOrder", description="Thứ tự sắp xếp")
):
    """
    Lấy danh sách customers - tương tự Next.js GET /api/admin/customers
    """
    
    try:
        # Verify authentication and admin role
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        
        if not require_admin_role(decoded_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cần quyền admin để truy cập"
            )

        # TODO: Replace with actual database query
        all_customers = [
            AdminCustomer(
                id="cust_001",
                userId="user_001",
                email="customer1@example.com",
                displayName="Nguyễn Văn Khách hàng",
                phoneNumber="+84123456789",
                totalDeposits=5000.00,
                totalWithdrawals=1000.00,
                kycStatus=KYCStatus.VERIFIED,
                isActive=True,
                referralSource="staff_001",
                lastActivity=datetime.now() - timedelta(hours=2)
            ),
            AdminCustomer(
                id="cust_002",
                userId="user_002",
                email="customer2@example.com",
                displayName="Trần Thị Khách hàng",
                phoneNumber="+84987654321",
                totalDeposits=2000.00,
                totalWithdrawals=500.00,
                kycStatus=KYCStatus.PENDING,
                isActive=True,
                referralSource="staff_002",
                lastActivity=datetime.now() - timedelta(days=1)
            )
        ]

        # Apply filters (similar to users endpoint)
        filtered_customers = all_customers
        
        if search:
            filtered_customers = [
                c for c in filtered_customers 
                if search.lower() in c.email.lower() or 
                   (c.displayName and search.lower() in c.displayName.lower())
            ]
        
        if kyc_status:
            filtered_customers = [c for c in filtered_customers if c.kycStatus == kyc_status]
        
        if is_active is not None:
            filtered_customers = [c for c in filtered_customers if c.isActive == is_active]

        # Sort and paginate (same logic as users)
        # ... (sorting and pagination logic similar to users endpoint)

        return CustomersResponse(
            success=True,
            data=filtered_customers[:limit],  # Simplified for demo
            pagination={
                "page": page,
                "limit": limit,
                "total": len(filtered_customers),
                "totalPages": (len(filtered_customers) + limit - 1) // limit
            }
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Get customers error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy danh sách khách hàng"
        )


# ========== ADMIN PLATFORM STATISTICS ENDPOINT ==========

@router.get(
    "/platform/stats",
    response_model=PlatformStatsResponse,
    responses={
        200: {"model": PlatformStatsResponse, "description": "Lấy thống kê platform thành công"},
        401: {"model": AdminErrorResponse, "description": "Không có quyền truy cập"},
        403: {"model": AdminErrorResponse, "description": "Cần quyền admin"}
    }
)
async def get_platform_stats(request: Request):
    """
    Lấy thống kê tổng quan platform - tương tự Next.js GET /api/admin/platform/stats
    """
    
    try:
        # Verify authentication and admin role
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        
        if not require_admin_role(decoded_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cần quyền admin để truy cập"
            )

        # TODO: Replace with actual database aggregation queries
        stats_data = PlatformStats(
            totalUsers=15847,
            activeUsers=8426,
            totalDeposits=2850000.50,
            totalWithdrawals=1850000.25,
            averageDeposit=850.75,
            averageWithdrawal=1200.50,
            newUsersToday=127,
            newUsersThisMonth=2847,
            verifiedKycUsers=12356,
            pendingKycUsers=234,
            totalRevenue=85000.00,
            transactionVolume=4700000.75
        )

        return PlatformStatsResponse(
            success=True,
            data=stats_data
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Get platform stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy thống kê platform"
        )


# ========== ADMIN DEPOSIT DETAIL ENDPOINT ==========

@router.get(
    "/deposits/{deposit_id}",
    response_model=DepositDetailResponse,
    responses={
        200: {"model": DepositDetailResponse, "description": "Lấy chi tiết deposit thành công"},
        401: {"model": AdminErrorResponse, "description": "Không có quyền truy cập"},
        403: {"model": AdminErrorResponse, "description": "Cần quyền admin"},
        404: {"model": AdminErrorResponse, "description": "Không tìm thấy deposit"}
    }
)
async def get_deposit_detail(
    request: Request,
    deposit_id: str = Path(..., description="Deposit ID")
):
    """
    Lấy chi tiết deposit - tương tự Next.js GET /api/admin/deposits/[depositId]
    """
    
    try:
        # Verify authentication and admin role
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        
        if not require_admin_role(decoded_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cần quyền admin để truy cập"
            )

        # TODO: Replace with actual database query
        # deposit_doc = await get_deposit_from_database(deposit_id)
        # if not deposit_doc:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Không tìm thấy giao dịch nạp tiền"
        #     )

        # Simulate deposit not found
        if deposit_id not in ["dep_001", "dep_002"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy giao dịch nạp tiền"
            )

        # Simulate deposit data
        deposit_data = AdminDeposit(
            id=deposit_id,
            userId="user_001",
            customerEmail="customer@example.com",
            amount=1000.00,
            currency="USD",
            status="completed",
            paymentMethod="bank_transfer",
            transactionHash="tx_hash_123",
            bankReference="REF123456",
            adminNotes="Deposit approved manually",
            processedAt=datetime.now() - timedelta(hours=1),
            createdAt=datetime.now() - timedelta(hours=2)
        )

        return DepositDetailResponse(
            success=True,
            data=deposit_data
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Get deposit detail error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy chi tiết giao dịch nạp tiền"
        )


# ========== ADMIN USER PERFORMANCE ENDPOINT ==========

@router.get(
    "/users/{user_id}/performance",
    response_model=UserPerformanceResponse,
    responses={
        200: {"model": UserPerformanceResponse, "description": "Lấy hiệu suất user thành công"},
        401: {"model": AdminErrorResponse, "description": "Không có quyền truy cập"},
        403: {"model": AdminErrorResponse, "description": "Cần quyền admin"},
        404: {"model": AdminErrorResponse, "description": "Không tìm thấy user"}
    }
)
async def get_user_performance(
    request: Request,
    user_id: str = Path(..., description="User ID")
):
    """
    Lấy thống kê hiệu suất user - tương tự Next.js GET /api/admin/users/[userId]/performance
    """
    
    try:
        # Verify authentication and admin role
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        
        if not require_admin_role(decoded_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cần quyền admin để truy cập"
            )

        # TODO: Replace with actual database aggregation
        performance_data = UserPerformance(
            userId=user_id,
            email=f"user_{user_id}@example.com",
            totalTrades=156,
            successfulTrades=142,
            failedTrades=14,
            totalVolume=125000.50,
            averageTradeSize=801.28,
            profitLoss=8750.25,
            winRate=91.03,
            bestTrade=2500.00,
            worstTrade=-500.00,
            firstTradeAt=datetime.now() - timedelta(days=180),
            lastTradeAt=datetime.now() - timedelta(hours=1)
        )

        return UserPerformanceResponse(
            success=True,
            data=performance_data
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Get user performance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy thống kê hiệu suất người dùng"
        )


# ========== ADDITIONAL ADMIN ENDPOINTS (PLACEHOLDERS) ==========

# The following endpoints are included to complete the admin module
# They follow the same pattern as above but are simplified for brevity

@router.get("/referrals")
async def get_referrals(request: Request):
    """Placeholder for GET /api/admin/referrals"""
    # Implementation similar to other admin endpoints
    pass


@router.get("/subaccounts")
async def get_subaccounts(request: Request):
    """Placeholder for GET /api/admin/subaccounts"""
    # Implementation similar to other admin endpoints
    pass


@router.get("/trading-adjustments")
async def get_trading_adjustments(request: Request):
    """Placeholder for GET /api/admin/trading-adjustments"""
    # Implementation similar to other admin endpoints
    pass