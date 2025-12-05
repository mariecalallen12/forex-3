"""
Client Endpoints - Migration từ Next.js API
Bao gồm: dashboard, wallet-balances, transactions, exchange-rates, crypto-deposit-address, generate-vietqr
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime, timedelta

# Import schemas
from ...schemas.client import (
    DashboardResponse,
    WalletBalancesRequest,
    WalletBalanceResponse,
    TransactionsRequest,
    TransactionsResponse,
    ExchangeRatesResponse,
    CryptoDepositAddressRequest,
    CryptoDepositAddressResponse,
    GenerateVietQRRequest,
    VietQRResponse,
    ClientErrorResponse,
    ValidationErrorResponse,
    TransactionHistory,
    WalletBalance,
    ExchangeRate
)

# Import middleware functions
from ...middleware.auth import (
    verify_token,
    TokenValidationError,
    get_client_ip,
    rate_limit
)

router = APIRouter(tags=["client"])

# ========== DASHBOARD ENDPOINT ==========

@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    responses={
        200: {"model": DashboardResponse, "description": "Lấy dữ liệu dashboard thành công"},
        401: {"model": ClientErrorResponse, "description": "Không tìm thấy token xác thực"},
        404: {"model": ClientErrorResponse, "description": "Không tìm thấy thông tin người dùng"},
        500: {"model": ClientErrorResponse, "description": "Lỗi hệ thống"}
    }
)
async def get_dashboard(request: Request):
    """
    Lấy dữ liệu dashboard - tương tự Next.js GET /api/client/dashboard
    Bao gồm tổng quan tài chính, số dư ví, giao dịch gần đây và thống kê
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

        # TODO: Database queries will be implemented with PostgreSQL
        # For now, using placeholder data that matches the original Next.js structure

        # Simulate wallet balances (replacing Firestore query)
        balances = [
            WalletBalance(
                userId=user_id,
                asset="USD",
                totalBalance=12500.50,
                availableBalance=11800.25,
                lockedBalance=700.25,
                pendingBalance=0,
                reservedBalance=0,
                lastUpdated=datetime.now()
            ),
            WalletBalance(
                userId=user_id,
                asset="VND",
                totalBalance=285000000,
                availableBalance=275000000,
                lockedBalance=10000000,
                pendingBalance=0,
                reservedBalance=0,
                lastUpdated=datetime.now()
            ),
            WalletBalance(
                userId=user_id,
                asset="BTC",
                totalBalance=0.25,
                availableBalance=0.22,
                lockedBalance=0.03,
                pendingBalance=0,
                reservedBalance=0,
                lastUpdated=datetime.now()
            )
        ]

        # Simulate recent transactions (replacing Firestore query)
        recent_transactions = [
            TransactionHistory(
                id="tx_001",
                userId=user_id,
                type="deposit",
                category="crypto_deposit",
                status="completed",
                amount=500.00,
                currency="USD",
                fee=2.50,
                netAmount=497.50,
                description="Nạp tiền qua Bitcoin",
                paymentMethod="crypto",
                blockchainNetwork="Bitcoin",
                createdAt=datetime.now() - timedelta(hours=2)
            ),
            TransactionHistory(
                id="tx_002",
                userId=user_id,
                type="withdrawal",
                category="bank_transfer",
                status="pending",
                amount=250.00,
                currency="USD",
                fee=5.00,
                netAmount=245.00,
                description="Rút tiền về ngân hàng",
                paymentMethod="bank_transfer",
                createdAt=datetime.now() - timedelta(hours=6)
            ),
            TransactionHistory(
                id="tx_003",
                userId=user_id,
                type="deposit",
                category="vietqr",
                status="completed",
                amount=5000000,
                currency="VND",
                fee=0,
                netAmount=5000000,
                description="Nạp tiền qua VietQR",
                paymentMethod="vietqr",
                createdAt=datetime.now() - timedelta(days=1)
            )
        ]

        # Calculate overview data (maintaining exact Next.js logic)
        total_balance = sum(balance.availableBalance * get_conversion_rate(balance.asset) for balance in balances)
        available_balance = total_balance  # Same calculation as Next.js
        
        # Get pending deposits and withdrawals
        pending_deposits = 1250.75  # Placeholder data
        pending_withdrawals = 245.00  # From pending withdrawal above

        # Calculate wallet stats
        total_deposits = sum(tx.amount for tx in recent_transactions if tx.type == "deposit")
        total_withdrawals = sum(tx.amount for tx in recent_transactions if tx.type == "withdrawal")
        deposit_count = len([tx for tx in recent_transactions if tx.type == "deposit"])
        withdrawal_count = len([tx for tx in recent_transactions if tx.type == "withdrawal"])

        # Calculate risk score (exact same logic as Next.js)
        from ...middleware.auth import get_user_data  # Will be implemented
        # user_data = await get_user_data(user_id)  # This would include kycStatus, phoneVerified
        kyc_status = "verified"  # Placeholder
        phone_verified = True  # Placeholder
        
        risk_score = min(100, len(recent_transactions) * 10 + 
                        (20 if kyc_status == "verified" else 0) +
                        (10 if phone_verified else 0) +
                        (len(balances) * 5))

        # Exchange rates (replacing Firestore query)
        exchange_rates = {
            "USD_VND": 24250,
            "VND_USD": 1/24250,
            "USD_CNY": 1/7.23,
            "CNY_USD": 7.23,
            "USD_GBP": 1/0.79,
            "GBP_USD": 0.79,
            "USD_EUR": 1/0.92,
            "EUR_USD": 0.92
        }

        # Prepare dashboard response
        dashboard_data = {
            "userId": user_id,
            "overview": {
                "totalBalance": total_balance,
                "availableBalance": available_balance,
                "lockedBalance": total_balance - available_balance,
                "pendingDeposits": pending_deposits,
                "pendingWithdrawals": pending_withdrawals,
                "recentActivity": recent_transactions
            },
            "balances": balances,
            "recentTransactions": recent_transactions,
            "stats": {
                "totalDeposits": total_deposits,
                "totalWithdrawals": total_withdrawals,
                "netFlow": total_deposits - total_withdrawals,
                "activeAssets": len(balances),
                "largestDeposit": max([tx.amount for tx in recent_transactions if tx.type == "deposit"], default=0),
                "largestWithdrawal": max([tx.amount for tx in recent_transactions if tx.type == "withdrawal"], default=0),
                "averageDeposit": total_deposits / deposit_count if deposit_count > 0 else 0,
                "averageWithdrawal": total_withdrawals / withdrawal_count if withdrawal_count > 0 else 0,
                "depositCount": deposit_count,
                "withdrawalCount": withdrawal_count,
                "lastDepositAt": next((tx.createdAt for tx in recent_transactions if tx.type == "deposit"), None),
                "lastWithdrawalAt": next((tx.createdAt for tx in recent_transactions if tx.type == "withdrawal"), None)
            },
            "riskScore": risk_score,
            "complianceStatus": kyc_status,
            "lastUpdated": datetime.now()
        }

        return DashboardResponse(
            success=True,
            data=dashboard_data,
            exchangeRates=exchange_rates
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy dữ liệu dashboard"
        )


def get_conversion_rate(asset: str) -> float:
    """
    Helper function to get conversion rate to USD
    Matches Next.js dashboard logic
    """
    rates = {
        "USD": 1,
        "VND": 1/24250,
        "CNY": 7.23,
        "GBP": 0.79,
        "EUR": 0.92,
        "BTC": 1,  # Would need real-time BTC price
        "ETH": 1   # Would need real-time ETH price
    }
    return rates.get(asset, 1)


# ========== WALLET BALANCES ENDPOINT ==========

@router.get(
    "/wallet-balances",
    response_model=WalletBalanceResponse,
    responses={
        200: {"model": WalletBalanceResponse, "description": "Lấy số dư ví thành công"},
        401: {"model": ClientErrorResponse, "description": "Không tìm thấy token xác thực"}
    }
)
async def get_wallet_balances(request: Request, user_id: Optional[str] = Query(None)):
    """
    Lấy số dư ví - tương tự Next.js GET /api/client/wallet-balances
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
        
        # Use provided user_id or extract from token
        target_user_id = user_id or decoded_token["uid"]

        # TODO: Replace with actual database query
        # This matches the Firestore query structure from Next.js
        balances = [
            WalletBalance(
                userId=target_user_id,
                asset="USD",
                totalBalance=12500.50,
                availableBalance=11800.25,
                lockedBalance=700.25,
                pendingBalance=0,
                reservedBalance=0,
                lastUpdated=datetime.now()
            ),
            WalletBalance(
                userId=target_user_id,
                asset="VND",
                totalBalance=285000000,
                availableBalance=275000000,
                lockedBalance=10000000,
                pendingBalance=0,
                reservedBalance=0,
                lastUpdated=datetime.now()
            ),
            WalletBalance(
                userId=target_user_id,
                asset="BTC",
                totalBalance=0.25,
                availableBalance=0.22,
                lockedBalance=0.03,
                pendingBalance=0,
                reservedBalance=0,
                lastUpdated=datetime.now()
            )
        ]

        return WalletBalanceResponse(
            success=True,
            data=balances
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Wallet balances error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy số dư ví"
        )


# ========== TRANSACTIONS ENDPOINT ==========

@router.get(
    "/transactions",
    response_model=TransactionsResponse,
    responses={
        200: {"model": TransactionsResponse, "description": "Lấy danh sách giao dịch thành công"},
        401: {"model": ClientErrorResponse, "description": "Không tìm thấy token xác thực"}
    }
)
async def get_transactions(
    request: Request,
    page: int = Query(1, ge=1, description="Trang hiện tại"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    transaction_type: Optional[str] = Query(None, alias="type", description="Lọc theo loại giao dịch"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    currency: Optional[str] = Query(None, description="Lọc theo đơn vị tiền tệ")
):
    """
    Lấy danh sách giao dịch - tương tự Next.js GET /api/client/transactions
    Hỗ trợ phân trang và lọc theo các tiêu chí khác nhau
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

        # TODO: Replace with actual database query with pagination and filtering
        # This matches the Firestore query structure from Next.js
        all_transactions = [
            TransactionHistory(
                id="tx_001",
                userId=user_id,
                type="deposit",
                category="crypto_deposit",
                status="completed",
                amount=500.00,
                currency="USD",
                fee=2.50,
                netAmount=497.50,
                description="Nạp tiền qua Bitcoin",
                paymentMethod="crypto",
                blockchainNetwork="Bitcoin",
                createdAt=datetime.now() - timedelta(hours=2)
            ),
            TransactionHistory(
                id="tx_002",
                userId=user_id,
                type="withdrawal",
                category="bank_transfer",
                status="pending",
                amount=250.00,
                currency="USD",
                fee=5.00,
                netAmount=245.00,
                description="Rút tiền về ngân hàng",
                paymentMethod="bank_transfer",
                createdAt=datetime.now() - timedelta(hours=6)
            ),
            TransactionHistory(
                id="tx_003",
                userId=user_id,
                type="deposit",
                category="vietqr",
                status="completed",
                amount=5000000,
                currency="VND",
                fee=0,
                netAmount=5000000,
                description="Nạp tiền qua VietQR",
                paymentMethod="vietqr",
                createdAt=datetime.now() - timedelta(days=1)
            ),
            TransactionHistory(
                id="tx_004",
                userId=user_id,
                type="trading",
                category="buy_order",
                status="completed",
                amount=100.00,
                currency="BTC",
                fee=1.00,
                netAmount=99.00,
                description="Mua BTC",
                createdAt=datetime.now() - timedelta(days=2)
            )
        ]

        # Apply filters
        filtered_transactions = all_transactions
        
        if transaction_type:
            filtered_transactions = [tx for tx in filtered_transactions if tx.type == transaction_type]
        
        if status:
            filtered_transactions = [tx for tx in filtered_transactions if tx.status == status]
        
        if currency:
            filtered_transactions = [tx for tx in filtered_transactions if tx.currency == currency]

        # Apply pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_transactions = filtered_transactions[start_index:end_index]

        # Calculate pagination info
        total_items = len(filtered_transactions)
        total_pages = (total_items + limit - 1) // limit

        return TransactionsResponse(
            success=True,
            data=paginated_transactions,
            pagination={
                "page": page,
                "limit": limit,
                "total": total_items,
                "pages": total_pages,
                "hasNext": end_index < total_items,
                "hasPrev": page > 1
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
        print(f"Transactions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy danh sách giao dịch"
        )


# ========== EXCHANGE RATES ENDPOINT ==========

@router.get(
    "/exchange-rates",
    response_model=ExchangeRatesResponse,
    responses={
        200: {"model": ExchangeRatesResponse, "description": "Lấy tỷ giá hối đoái thành công"}
    }
)
async def get_exchange_rates():
    """
    Lấy tỷ giá hối đoái - tương tự Next.js GET /api/client/exchange-rates
    """
    
    try:
        # TODO: Replace with actual database query
        # This matches the Firestore query structure from Next.js
        exchange_rates = [
            ExchangeRate(
                id="rate_001",
                baseAsset="USD",
                targetAsset="VND",
                rate=24250.0,
                isActive=True,
                priority=1,
                lastUpdated=datetime.now()
            ),
            ExchangeRate(
                id="rate_002",
                baseAsset="VND",
                targetAsset="USD",
                rate=1/24250.0,
                isActive=True,
                priority=2,
                lastUpdated=datetime.now()
            ),
            ExchangeRate(
                id="rate_003",
                baseAsset="USD",
                targetAsset="CNY",
                rate=7.23,
                isActive=True,
                priority=3,
                lastUpdated=datetime.now()
            ),
            ExchangeRate(
                id="rate_004",
                baseAsset="CNY",
                targetAsset="USD",
                rate=1/7.23,
                isActive=True,
                priority=4,
                lastUpdated=datetime.now()
            ),
            ExchangeRate(
                id="rate_005",
                baseAsset="USD",
                targetAsset="GBP",
                rate=0.79,
                isActive=True,
                priority=5,
                lastUpdated=datetime.now()
            ),
            ExchangeRate(
                id="rate_006",
                baseAsset="GBP",
                targetAsset="USD",
                rate=1/0.79,
                isActive=True,
                priority=6,
                lastUpdated=datetime.now()
            ),
            ExchangeRate(
                id="rate_007",
                baseAsset="USD",
                targetAsset="EUR",
                rate=0.92,
                isActive=True,
                priority=7,
                lastUpdated=datetime.now()
            ),
            ExchangeRate(
                id="rate_008",
                baseAsset="EUR",
                targetAsset="USD",
                rate=1/0.92,
                isActive=True,
                priority=8,
                lastUpdated=datetime.now()
            )
        ]

        return ExchangeRatesResponse(
            success=True,
            data=exchange_rates
        )

    except Exception as e:
        print(f"Exchange rates error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy tỷ giá hối đoái"
        )


# ========== CRYPTO DEPOSIT ADDRESS ENDPOINT ==========

@router.post(
    "/crypto-deposit-address",
    response_model=CryptoDepositAddressResponse,
    responses={
        200: {"model": CryptoDepositAddressResponse, "description": "Tạo địa chỉ nạp crypto thành công"},
        400: {"model": ValidationErrorResponse, "description": "Dữ liệu đầu vào không hợp lệ"},
        401: {"model": ClientErrorResponse, "description": "Không tìm thấy token xác thực"}
    }
)
async def create_crypto_deposit_address(request: Request, crypto_request: CryptoDepositAddressRequest):
    """
    Tạo địa chỉ nạp crypto - tương tự Next.js POST /api/client/crypto-deposit-address
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

        # Validate supported currencies
        supported_currencies = ["BTC", "ETH", "USDT", "BNB", "ADA", "DOT"]
        if crypto_request.currency.upper() not in supported_currencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Loại tiền {crypto_request.currency} không được hỗ trợ"
            )

        # TODO: Replace with actual crypto address generation service
        # This would integrate with actual blockchain APIs
        import secrets
        import string
        
        # Generate a realistic-looking crypto address
        if crypto_request.currency.upper() == "BTC":
            address = "1" + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(33))
        elif crypto_request.currency.upper() == "ETH":
            address = "0x" + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(40))
        else:
            address = secrets.token_hex(32)

        # Generate QR code (placeholder)
        import base64
        qr_code = base64.b64encode(f"Address: {address}\nAmount: 0\nCurrency: {crypto_request.currency}".encode()).decode()

        # Set expiration time
        expires_at = datetime.now() + timedelta(hours=24)

        deposit_address_data = {
            "address": address,
            "currency": crypto_request.currency.upper(),
            "network": crypto_request.network or get_default_network(crypto_request.currency.upper()),
            "qrCode": qr_code,
            "memo": None,  # Would be populated for currencies like XRP, XLM
            "createdAt": datetime.now(),
            "expiresAt": expires_at
        }

        return CryptoDepositAddressResponse(
            success=True,
            data=deposit_address_data
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Crypto deposit address error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo địa chỉ nạp crypto"
        )


def get_default_network(currency: str) -> str:
    """Get default network for currency"""
    networks = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum", 
        "USDT": "Ethereum",
        "BNB": "Binance Smart Chain",
        "ADA": "Cardano",
        "DOT": "Polkadot"
    }
    return networks.get(currency, "Mainnet")


# ========== GENERATE VIETQR ENDPOINT ==========

@router.post(
    "/generate-vietqr",
    response_model=VietQRResponse,
    responses={
        200: {"model": VietQRResponse, "description": "Tạo VietQR thành công"},
        400: {"model": ValidationErrorResponse, "description": "Dữ liệu đầu vào không hợp lệ"},
        401: {"model": ClientErrorResponse, "description": "Không tìm thấy token xác thực"}
    }
)
async def generate_vietqr(request: Request, qr_request: GenerateVietQRRequest):
    """
    Tạo QR code thanh toán VietQR - tương tự Next.js POST /api/client/generate-vietqr
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

        # TODO: Replace with actual VietQR generation service
        # This would integrate with VietQR API
        import secrets
        import string
        
        # Generate unique payment ID
        payment_id = "VQR" + ''.join(secrets.choice(string.digits) for _ in range(12))
        
        # Generate QR data (VietQR format)
        qr_data = {
            "paymentId": payment_id,
            "amount": qr_request.amount,
            "description": qr_request.description,
            "orderId": qr_request.orderId,
            "bankCode": "970436",  # VietBank
            "accountNumber": "123456789",
            "accountName": "DIGITAL UTOPIA"
        }

        # Generate QR code
        import base64
        import json
        
        qr_content = json.dumps(qr_data, separators=(',', ':'))
        qr_code = base64.b64encode(qr_content.encode()).decode()
        
        # Generate payment URL
        payment_url = f"https://vietqr.net/pay/{payment_id}"

        vietqr_data = {
            **qr_data,
            "qrCode": qr_code,
            "paymentUrl": payment_url,
            "createdAt": datetime.now().isoformat(),
            "expiresAt": (datetime.now() + timedelta(hours=24)).isoformat()
        }

        return VietQRResponse(
            success=True,
            data=vietqr_data,
            qrCode=qr_code,
            paymentUrl=payment_url
        )

    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"VietQR generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo VietQR"
        )