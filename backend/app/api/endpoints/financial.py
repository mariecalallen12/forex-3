"""
Financial Endpoints - Migration từ Next.js API
Bao gồm: deposits, withdrawals với đầy đủ validation logic
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime, timedelta
import secrets
import string

# Import schemas
from ...schemas.financial import (
    # Deposit schemas
    CreateDepositRequest,
    DepositRecord,
    Invoice,
    DepositResponse,
    DepositsListResponse,
    
    # Withdrawal schemas
    CreateWithdrawalRequest,
    WithdrawalRecord,
    WithdrawalLimits,
    WithdrawalResponse,
    WithdrawalsListResponse,
    
    # Error schemas
    FinancialErrorResponse,
    FinancialValidationErrorResponse
)

# Import middleware functions
from ...middleware.auth import (
    verify_token,
    TokenValidationError,
    get_client_ip,
    rate_limit
)

router = APIRouter(tags=["financial"])

# ========== FINANCIAL DEPOSITS ENDPOINTS ==========

@router.post(
    "/deposits",
    response_model=DepositResponse,
    responses={
        201: {"model": DepositResponse, "description": "Tạo deposit request thành công"},
        400: {"model": FinancialValidationErrorResponse, "description": "Dữ liệu đầu vào không hợp lệ"},
        401: {"model": FinancialErrorResponse, "description": "Không tìm thấy token xác thực"},
        404: {"model": FinancialErrorResponse, "description": "Không tìm thấy thông tin người dùng"},
        500: {"model": FinancialErrorResponse, "description": "Lỗi hệ thống"}
    }
)
async def create_deposit(request: Request, deposit_data: CreateDepositRequest):
    """
    Tạo yêu cầu nạp tiền - tương tự Next.js POST /api/financial/deposits
    Bao gồm tạo deposit record và invoice
    """
    
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        user_id = decoded_token["uid"]

        # TODO: Get user data from database
        # user_doc = await get_user_from_database(user_id)
        # if not user_doc.exists:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Không tìm thấy thông tin người dùng"
        #     )

        # Simulate user data
        user_data = {
            "email": f"user_{user_id}@example.com",
            "isActive": True
        }

        # Create unique deposit ID
        deposit_id = f"deposit_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"
        
        # Create deposit record (matching Next.js structure)
        deposit_record = {
            "id": deposit_id,
            "userId": user_id,
            "userEmail": user_data["email"],
            "amount": deposit_data.amount,
            "currency": deposit_data.currency.value,
            "method": deposit_data.method.value,
            "status": "pending",
            "fees": 0,
            "netAmount": deposit_data.amount,
            "bankAccount": deposit_data.bankAccount.dict() if deposit_data.bankAccount else None,
            "walletAddress": deposit_data.walletAddress,
            "transactionId": deposit_data.transactionId,
            "notes": deposit_data.notes,
            "processedBy": None,
            "processedAt": None,
            "rejectReason": None,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

        # TODO: Save deposit to database
        # await save_deposit_to_database(deposit_record)

        # Create invoice for the deposit
        invoice_id = f"invoice_{deposit_id}"
        invoice_record = {
            "id": invoice_id,
            "userId": user_id,
            "userEmail": user_data["email"],
            "type": "deposit",
            "status": "pending",
            "amount": deposit_data.amount,
            "currency": deposit_data.currency.value,
            "description": f"Nạp tiền {deposit_data.currency.value.upper()} {deposit_data.amount}",
            "depositId": deposit_id,
            "dueDate": (datetime.now() + timedelta(days=7)).isoformat(),
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

        # TODO: Save invoice to database
        # await save_invoice_to_database(invoice_record)

        return DepositResponse(
            success=True,
            message="Tạo yêu cầu nạp tiền thành công",
            data={
                "deposit": {
                    "id": deposit_record["id"],
                    "amount": deposit_record["amount"],
                    "currency": deposit_record["currency"],
                    "method": deposit_record["method"],
                    "status": deposit_record["status"],
                },
                "invoice": {
                    "id": invoice_record["id"],
                    "dueDate": invoice_record["dueDate"],
                },
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
        print(f"Create deposit error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo yêu cầu nạp tiền"
        )


@router.get(
    "/deposits",
    response_model=DepositsListResponse,
    responses={
        200: {"model": DepositsListResponse, "description": "Lấy danh sách deposits thành công"},
        401: {"model": FinancialErrorResponse, "description": "Không tìm thấy token xác thực"}
    }
)
async def get_deposits(
    request: Request,
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    currency: Optional[str] = Query(None, description="Lọc theo đơn vị tiền tệ")
):
    """
    Lấy danh sách deposits - tương tự Next.js GET /api/financial/deposits
    Hỗ trợ phân trang và filtering
    """
    
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        user_id = decoded_token["uid"]

        # TODO: Replace with actual database query
        all_deposits = [
            DepositRecord(
                id="dep_001",
                userId=user_id,
                userEmail=f"user_{user_id}@example.com",
                amount=1000.00,
                currency="usdt",
                method="crypto_deposit",
                status="completed",
                fees=0,
                netAmount=1000.00,
                walletAddress="0x1234...5678",
                createdAt=datetime.now() - timedelta(days=1)
            ),
            DepositRecord(
                id="dep_002",
                userId=user_id,
                userEmail=f"user_{user_id}@example.com",
                amount=500.00,
                currency="btc",
                method="crypto_deposit",
                status="pending",
                fees=0,
                netAmount=500.00,
                walletAddress="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                createdAt=datetime.now() - timedelta(hours=2)
            ),
            DepositRecord(
                id="dep_003",
                userId=user_id,
                userEmail=f"user_{user_id}@example.com",
                amount=5000.00,
                currency="usdt",
                method="bank_transfer",
                status="processing",
                fees=25.00,
                netAmount=4975.00,
                bankAccount={
                    "accountNumber": "123456789",
                    "accountName": "Nguyễn Văn A",
                    "bankName": "Vietcombank"
                },
                createdAt=datetime.now() - timedelta(hours=6)
            )
        ]

        # Apply filters
        filtered_deposits = all_deposits
        
        if status:
            filtered_deposits = [d for d in filtered_deposits if d.status == status]
        
        if currency:
            filtered_deposits = [d for d in filtered_deposits if d.currency == currency]

        # Apply pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_deposits = filtered_deposits[start_index:end_index]

        # Convert to dict format
        deposits_data = []
        for deposit in paginated_deposits:
            deposit_dict = deposit.dict()
            # Convert datetime fields to ISO strings
            for field in ["createdAt", "updatedAt", "processedAt"]:
                if deposit_dict.get(field):
                    deposit_dict[field] = deposit_dict[field].isoformat()
            deposits_data.append(deposit_dict)

        return DepositsListResponse(
            success=True,
            data={
                "deposits": deposits_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": len(filtered_deposits),
                    "totalPages": (len(filtered_deposits) + limit - 1) // limit
                }
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
        print(f"Get deposits error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy danh sách nạp tiền"
        )


# ========== FINANCIAL WITHDRAWALS ENDPOINTS ==========

@router.post(
    "/withdrawals",
    response_model=WithdrawalResponse,
    responses={
        201: {"model": WithdrawalResponse, "description": "Tạo withdrawal request thành công"},
        400: {"model": FinancialValidationErrorResponse, "description": "Dữ liệu đầu vào không hợp lệ"},
        401: {"model": FinancialErrorResponse, "description": "Không tìm thấy token xác thực"},
        403: {"model": FinancialErrorResponse, "description": "Cần xác minh KYC hoặc tài khoản không hoạt động"},
        404: {"model": FinancialErrorResponse, "description": "Không tìm thấy thông tin người dùng"},
        500: {"model": FinancialErrorResponse, "description": "Lỗi hệ thống"}
    }
)
async def create_withdrawal(request: Request, withdrawal_data: CreateWithdrawalRequest):
    """
    Tạo yêu cầu rút tiền - tương tự Next.js POST /api/financial/withdrawals
    Bao gồm đầy đủ validations: KYC, balance, limits
    """
    
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        user_id = decoded_token["uid"]

        # TODO: Get user data from database
        # user_doc = await get_user_from_database(user_id)
        # if not user_doc.exists:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Không tìm thấy thông tin người dùng"
        #     )

        # Simulate user data
        user_data = {
            "email": f"user_{user_id}@example.com",
            "kycStatus": "verified",
            "isActive": True,
            "balance": {
                "usdt": 5000.00,
                "btc": 0.5,
                "eth": 2.0
            }
        }

        # Check KYC status (matching Next.js logic)
        if user_data["kycStatus"] != "verified":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vui lòng xác minh KYC trước khi rút tiền"
            )

        # Check if user is active
        if not user_data["isActive"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản không hoạt động"
            )

        # Check available balance
        currency = withdrawal_data.currency.value
        available_balance = user_data["balance"].get(currency, 0)
        
        # Calculate fees (2% for withdrawals - matching Next.js)
        fee_rate = 0.02
        fee = withdrawal_data.amount * fee_rate
        required_amount = withdrawal_data.amount + fee

        if available_balance < required_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số dư {currency.upper()} không đủ để rút tiền (cần {required_amount} bao gồm phí)"
            )

        # Check withdrawal limits (matching Next.js logic)
        withdrawal_limits = WithdrawalLimits(daily=10000, monthly=100000)

        # Get user's withdrawals for current period
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # TODO: Replace with actual database queries
        # monthly_withdrawals = await get_user_withdrawals_for_period(user_id, currency, "completed", start_of_month)
        # daily_withdrawals = await get_user_withdrawals_for_period(user_id, currency, "completed", start_of_day)

        # Simulate withdrawal history
        monthly_total = 2500.00  # Placeholder
        daily_total = 500.00     # Placeholder

        if monthly_total + withdrawal_data.amount > withdrawal_limits.monthly:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vượt quá hạn mức rút tiền hàng tháng"
            )

        if daily_total + withdrawal_data.amount > withdrawal_limits.daily:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vượt quá hạn mức rút tiền hàng ngày"
            )

        # Create unique withdrawal ID
        withdrawal_id = f"withdraw_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"
        
        # Create withdrawal record (matching Next.js structure)
        withdrawal_record = {
            "id": withdrawal_id,
            "userId": user_id,
            "userEmail": user_data["email"],
            "amount": withdrawal_data.amount,
            "currency": currency,
            "method": withdrawal_data.method.value,
            "fee": fee,
            "netAmount": withdrawal_data.amount,
            "status": "pending",
            "bankAccount": withdrawal_data.bankAccount.dict() if withdrawal_data.bankAccount else None,
            "walletAddress": withdrawal_data.walletAddress,
            "notes": withdrawal_data.notes,
            "processedBy": None,
            "processedAt": None,
            "rejectReason": None,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

        # TODO: Save withdrawal to database
        # await save_withdrawal_to_database(withdrawal_record)

        # Create invoice for the withdrawal
        invoice_id = f"invoice_{withdrawal_id}"
        invoice_record = {
            "id": invoice_id,
            "userId": user_id,
            "userEmail": user_data["email"],
            "type": "withdrawal",
            "status": "pending",
            "amount": withdrawal_data.amount,
            "currency": currency,
            "description": f"Rút tiền {currency.upper()} {withdrawal_data.amount}",
            "withdrawalId": withdrawal_id,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        }

        # TODO: Save invoice to database
        # await save_invoice_to_database(invoice_record)

        return WithdrawalResponse(
            success=True,
            message="Tạo yêu cầu rút tiền thành công",
            data={
                "withdrawal": {
                    "id": withdrawal_record["id"],
                    "amount": withdrawal_record["amount"],
                    "currency": withdrawal_record["currency"],
                    "fee": withdrawal_record["fee"],
                    "netAmount": withdrawal_record["netAmount"],
                    "status": withdrawal_record["status"],
                },
                "invoice": {
                    "id": invoice_record["id"],
                },
                "limits": {
                    "remainingDaily": withdrawal_limits.daily - (daily_total + withdrawal_data.amount),
                    "remainingMonthly": withdrawal_limits.monthly - (monthly_total + withdrawal_data.amount),
                },
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
        print(f"Create withdrawal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo yêu cầu rút tiền"
        )


@router.get(
    "/withdrawals",
    response_model=WithdrawalsListResponse,
    responses={
        200: {"model": WithdrawalsListResponse, "description": "Lấy danh sách withdrawals thành công"},
        401: {"model": FinancialErrorResponse, "description": "Không tìm thấy token xác thực"}
    }
)
async def get_withdrawals(
    request: Request,
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    currency: Optional[str] = Query(None, description="Lọc theo đơn vị tiền tệ")
):
    """
    Lấy danh sách withdrawals - tương tự Next.js GET /api/financial/withdrawals
    Hỗ trợ phân trang và filtering
    """
    
    try:
        # Verify authentication
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Không tìm thấy token xác thực"
            )

        token = auth_header.split(" ")[1]
        decoded_token = verify_token(token)
        user_id = decoded_token["uid"]

        # TODO: Replace with actual database query
        all_withdrawals = [
            WithdrawalRecord(
                id="wd_001",
                userId=user_id,
                userEmail=f"user_{user_id}@example.com",
                amount=500.00,
                currency="usdt",
                method="bank_transfer",
                fee=10.00,
                netAmount=490.00,
                status="completed",
                bankAccount={
                    "accountNumber": "987654321",
                    "accountName": "Nguyễn Văn A",
                    "bankName": "Techcombank"
                },
                processedAt=datetime.now() - timedelta(hours=4),
                createdAt=datetime.now() - timedelta(days=2)
            ),
            WithdrawalRecord(
                id="wd_002",
                userId=user_id,
                userEmail=f"user_{user_id}@example.com",
                amount=0.1,
                currency="btc",
                fee=0.002,
                netAmount=0.098,
                status="pending",
                walletAddress="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                createdAt=datetime.now() - timedelta(hours=1)
            ),
            WithdrawalRecord(
                id="wd_003",
                userId=user_id,
                userEmail=f"user_{user_id}@example.com",
                amount=1000.00,
                currency="usdt",
                method="crypto_withdraw",
                fee=20.00,
                netAmount=980.00,
                status="processing",
                walletAddress="0x8765...4321",
                createdAt=datetime.now() - timedelta(hours=8)
            )
        ]

        # Apply filters
        filtered_withdrawals = all_withdrawals
        
        if status:
            filtered_withdrawals = [w for w in filtered_withdrawals if w.status == status]
        
        if currency:
            filtered_withdrawals = [w for w in filtered_withdrawals if w.currency == currency]

        # Apply pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_withdrawals = filtered_withdrawals[start_index:end_index]

        # Convert to dict format
        withdrawals_data = []
        for withdrawal in paginated_withdrawals:
            withdrawal_dict = withdrawal.dict()
            # Convert datetime fields to ISO strings
            for field in ["createdAt", "updatedAt", "processedAt"]:
                if withdrawal_dict.get(field):
                    withdrawal_dict[field] = withdrawal_dict[field].isoformat()
            withdrawals_data.append(withdrawal_dict)

        return WithdrawalsListResponse(
            success=True,
            data={
                "withdrawals": withdrawals_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": len(filtered_withdrawals),
                    "totalPages": (len(filtered_withdrawals) + limit - 1) // limit
                }
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
        print(f"Get withdrawals error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy danh sách rút tiền"
        )