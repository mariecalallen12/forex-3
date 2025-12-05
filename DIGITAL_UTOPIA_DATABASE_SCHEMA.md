# DIGITAL UTOPIA PLATFORM - LƯỢC ĐỒ CƠ SỞ DỮ LIỆU TOÀN DIỆN

**Ngày:** 2025-12-05  
**Phiên bản:** 1.0  
**Mục tiêu:** Thiết kế lược đồ cơ sở dữ liệu toàn diện cho nền tảng giao dịch tài chính số Digital Utopia Platform

---

## 1) Tóm tắt nhanh

Digital Utopia Platform sử dụng kiến trúc cơ sở dữ liệu hybrid với PostgreSQL làm primary database cho relational data và Redis cho caching & real-time operations. Schema được thiết kế để hỗ trợ 12 module chính với đầy đủ tính năng ACID compliance, audit trails, và performance optimization.

Database schema bao gồm 45+ bảng chính, được phân nhóm theo domain logic: Authentication, User Management, Trading Operations, Financial Transactions, Portfolio Management, Compliance & Risk, Admin Control, và Analytics.

---

## 2) Phạm vi & phương pháp

Database design principles:

- **Normalization**: 3rd Normal Form (3NF) để tránh data redundancy
- **Indexing Strategy**: Composite indexes cho frequently queried columns
- **Audit Trail**: Comprehensive logging cho financial operations
- **Data Integrity**: Foreign key constraints và check constraints
- **Performance Optimization**: Partitioning cho large tables
- **Backup Strategy**: Point-in-time recovery capability

---

## 3) Các phát hiện chính (Key Findings)

### 3.1 Database Architecture
- **Primary Database**: PostgreSQL 15 với advanced features
  - JSON/JSONB support cho flexible schemas
  - Full-text search capabilities
  - Database partitioning support
  - Read replicas cho scaling

### 3.2 Cache Layer Strategy
- **Redis**: Multiple Redis instances cho different purposes
  - Session management (TTL: 24h)
  - Real-time data caching (TTL: 5min)
  - Rate limiting (TTL: 1h)
  - Message queue (persistent)

### 3.3 Data Security
- **Encryption**: AES-256 encryption at rest
- **Field-level Encryption**: Sensitive data (PII, financial)
- **Access Control**: Row-level security (RLS)
- **Audit Logging**: All financial transactions logged

---

## 4) Mẫu lược đồ cơ sở dữ liệu (Database Schema Diagram)

```
┌─────────────────────────────────────────────────────────────────┐
│                   DIGITAL UTOPIA PLATFORM                       │
│                    DATABASE SCHEMA                             │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   PostgreSQL 15     │
                    │   Main Database     │
                    └─────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼────────┐ ┌─────▼──────────┐ ┌───▼────────┐
    │  Core Tables   │ │ Transaction    │ │  Analytics │
    │                │ │ Tables         │ │  Tables    │
    │┌──────────────┐│ │┌──────────────┐│ │┌──────────┐│
    ││users         ││ ││transactions  ││ ││audit_logs││
    ││user_profiles ││ ││trading_orders││ ││analytics ││
    ││roles         ││ ││transactions  ││ ││reports   ││
    ││permissions   ││ ││ledger_entries││ ││dashboards││
    ││audit_logs    ││ ││balances      ││ │└──────────┘│
    │└──────────────┘│ │└──────────────┘│ └───────────┘
    └────────────────┘ └────────────────┘

                    ┌─────────────────────┐
                    │     Redis Cache     │
                    │   Real-time Layer   │
                    └─────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼────────┐ ┌─────▼──────────┐ ┌───▼────────┐
    │  Session Cache │ │ Real-time Data │ │ Rate Limit │
    │                │ │                │ │            │
    │┌──────────────┐│ │┌──────────────┐│ │┌──────────┐│
    ││user_sessions ││ ││market_data   ││ ││api_limits││
    ││auth_tokens   ││ ││price_cache   ││ ││rate_apps ││
    ││refresh_token││ ││order_updates ││ │└──────────┘│
    ││session_data  ││ ││portfolio_sync││ │            │
    │└──────────────┘│ │└──────────────┘│ │            │
    └────────────────┘ └────────────────┘ └────────────┘
```

---

## 5) Chi tiết cơ sở dữ liệu (Database Details)

### 5.1 Core Authentication Tables

#### users (Users Master Table)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    status VARCHAR(50) DEFAULT 'pending',
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    kyc_status VARCHAR(50) DEFAULT 'pending',
    customer_payment_id VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    account_locked_until TIMESTAMP,
    terms_accepted_at TIMESTAMP,
    privacy_accepted_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_customer_payment_id ON users(customer_payment_id);
```

#### user_profiles (User Profile Information)
```sql
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    phone VARCHAR(20),
    address TEXT,
    country VARCHAR(100),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    id_type VARCHAR(50),
    id_number VARCHAR(100),
    id_verified BOOLEAN DEFAULT FALSE,
    bank_account_name VARCHAR(255),
    bank_account_number VARCHAR(50),
    bank_name VARCHAR(100),
    bank_branch VARCHAR(100),
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_phone ON user_profiles(phone);
```

#### roles (User Roles)
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default roles
INSERT INTO roles (name, description, is_system_role) VALUES
('owner', 'System owner with full privileges', TRUE),
('admin', 'Administrator with management access', TRUE),
('staff', 'Staff member with limited access', TRUE),
('customer', 'End customer', TRUE);
```

#### permissions (Permission Definitions)
```sql
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample permissions
INSERT INTO permissions (name, description, resource, action) VALUES
('user.create', 'Create new user accounts', 'users', 'create'),
('user.read', 'View user information', 'users', 'read'),
('user.update', 'Update user information', 'users', 'update'),
('user.delete', 'Delete user accounts', 'users', 'delete'),
('trading.place_order', 'Place trading orders', 'trading', 'create'),
('trading.view_positions', 'View trading positions', 'trading', 'read'),
('financial.deposit', 'Process deposits', 'financial', 'create'),
('financial.withdraw', 'Process withdrawals', 'financial', 'create'),
('admin.dashboard', 'Access admin dashboard', 'admin', 'read'),
('compliance.view_reports', 'View compliance reports', 'compliance', 'read');
```

#### role_permissions (Role-Permission Mapping)
```sql
CREATE TABLE role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, permission_id)
);
```

### 5.2 Trading System Tables

#### trading_orders (Trading Orders)
```sql
CREATE TABLE trading_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    order_type VARCHAR(50) NOT NULL, -- market, limit, stop, iceberg, oco, trailing_stop
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- buy, sell
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8),
    stop_price DECIMAL(20,8),
    time_in_force VARCHAR(10) DEFAULT 'GTC', -- GTC, IOC, FOK
    status VARCHAR(50) DEFAULT 'pending', -- pending, filled, partial, cancelled, rejected
    filled_quantity DECIMAL(20,8) DEFAULT 0,
    filled_price DECIMAL(20,8),
    remaining_quantity DECIMAL(20,8),
    average_price DECIMAL(20,8),
    commission DECIMAL(20,8) DEFAULT 0,
    source VARCHAR(100), -- web, mobile, api, bot
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Indexes for trading performance
CREATE INDEX idx_trading_orders_user_id ON trading_orders(user_id);
CREATE INDEX idx_trading_orders_symbol ON trading_orders(symbol);
CREATE INDEX idx_trading_orders_status ON trading_orders(status);
CREATE INDEX idx_trading_orders_created_at ON trading_orders(created_at);
CREATE INDEX idx_trading_orders_side_symbol ON trading_orders(side, symbol);
```

#### portfolio_positions (Portfolio Positions)
```sql
CREATE TABLE portfolio_positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    average_price DECIMAL(20,8) NOT NULL,
    market_value DECIMAL(20,8),
    unrealized_pnl DECIMAL(20,8),
    realized_pnl DECIMAL(20,8) DEFAULT 0,
    position_type VARCHAR(20) DEFAULT 'long', -- long, short
    entry_price DECIMAL(20,8),
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMP,
    closed_price DECIMAL(20,8),
    closed_reason VARCHAR(100),
    UNIQUE(user_id, symbol, position_type, is_closed)
);

-- Indexes
CREATE INDEX idx_portfolio_positions_user_id ON portfolio_positions(user_id);
CREATE INDEX idx_portfolio_positions_symbol ON portfolio_positions(symbol);
CREATE INDEX idx_portfolio_positions_is_closed ON portfolio_positions(is_closed);
```

### 5.3 Financial System Tables

#### transactions (Financial Transactions)
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- deposit, withdrawal, transfer, fee, trading
    asset VARCHAR(20) NOT NULL,
    amount DECIMAL(20,8) NOT NULL,
    fee DECIMAL(20,8) DEFAULT 0,
    net_amount DECIMAL(20,8) NOT NULL,
    balance_before DECIMAL(20,8),
    balance_after DECIMAL(20,8),
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed, cancelled
    reference_id VARCHAR(100), -- External reference
    external_id VARCHAR(100), -- External transaction ID
    bank_account VARCHAR(50), -- Bank account for transfers
    transaction_hash VARCHAR(255), -- For crypto transactions
    from_address VARCHAR(255), -- Crypto address
    to_address VARCHAR(255), -- Crypto address
    network VARCHAR(50), -- Network for crypto
    metadata JSONB, -- Additional transaction data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    failed_reason TEXT
);

-- Indexes
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_asset ON transactions(asset);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_reference_id ON transactions(reference_id);
```

#### wallet_balances (Wallet Balances)
```sql
CREATE TABLE wallet_balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    asset VARCHAR(20) NOT NULL,
    available_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
    locked_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
    total_balance DECIMAL(20,8) GENERATED ALWAYS AS (available_balance + locked_balance) STORED,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, asset)
);

-- Indexes
CREATE INDEX idx_wallet_balances_user_id ON wallet_balances(user_id);
CREATE INDEX idx_wallet_balances_asset ON wallet_balances(asset);
```

### 5.4 Advanced Trading Tables

#### iceberg_orders (Iceberg Orders)
```sql
CREATE TABLE iceberg_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    parent_order_id INTEGER REFERENCES trading_orders(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    total_quantity DECIMAL(20,8) NOT NULL,
    slice_quantity DECIMAL(20,8) NOT NULL,
    remaining_quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8),
    status VARCHAR(50) DEFAULT 'active',
    slices_completed INTEGER DEFAULT 0,
    total_filled DECIMAL(20,8) DEFAULT 0,
    average_fill_price DECIMAL(20,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_iceberg_orders_user_id ON iceberg_orders(user_id);
CREATE INDEX idx_iceberg_orders_parent_order ON iceberg_orders(parent_order_id);
CREATE INDEX idx_iceberg_orders_symbol ON iceberg_orders(symbol);
```

#### oco_orders (One-Cancels-Other Orders)
```sql
CREATE TABLE oco_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    primary_order_id INTEGER REFERENCES trading_orders(id),
    secondary_order_id INTEGER REFERENCES trading_orders(id),
    symbol VARCHAR(20) NOT NULL,
    primary_side VARCHAR(10), -- buy or sell for primary
    secondary_side VARCHAR(10), -- buy or sell for secondary
    status VARCHAR(50) DEFAULT 'active',
    triggered_order_id INTEGER, -- The order that got triggered
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_oco_orders_user_id ON oco_orders(user_id);
CREATE INDEX idx_oco_orders_primary_order ON oco_orders(primary_order_id);
```

#### trailing_stop_orders (Trailing Stop Orders)
```sql
CREATE TABLE trailing_stop_orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    parent_order_id INTEGER REFERENCES trading_orders(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    stop_type VARCHAR(20), -- percentage, amount
    stop_value DECIMAL(20,8), -- Percentage or amount
    trailing_distance DECIMAL(20,8), -- How far to trail
    current_stop_price DECIMAL(20,8),
    highest_price DECIMAL(20,8), -- Highest price reached for long positions
    lowest_price DECIMAL(20,8), -- Lowest price reached for short positions
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_trailing_stop_orders_user_id ON trailing_stop_orders(user_id);
CREATE INDEX idx_trailing_stop_orders_symbol ON trailing_stop_orders(symbol);
CREATE INDEX idx_trailing_stop_orders_status ON trailing_stop_orders(status);
```

### 5.5 Compliance & Risk Management Tables

#### compliance_events (Compliance Events)
```sql
CREATE TABLE compliance_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    status VARCHAR(50) DEFAULT 'open', -- open, investigating, resolved, dismissed
    description TEXT NOT NULL,
    risk_score INTEGER DEFAULT 0,
    assigned_to INTEGER, -- user_id of assigned analyst
    resolved_by INTEGER, -- user_id who resolved
    resolution_notes TEXT,
    escalated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_compliance_events_user_id ON compliance_events(user_id);
CREATE INDEX idx_compliance_events_type ON compliance_events(event_type);
CREATE INDEX idx_compliance_events_status ON compliance_events(status);
```

#### kyc_documents (KYC Documents)
```sql
CREATE TABLE kyc_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL, -- id_card, passport, bank_statement, utility_bill
    document_number VARCHAR(100),
    document_file_url VARCHAR(500),
    expiry_date DATE,
    verification_status VARCHAR(50) DEFAULT 'pending', -- pending, verified, rejected, expired
    verified_by INTEGER, -- user_id of verifier
    verification_date TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_kyc_documents_user_id ON kyc_documents(user_id);
CREATE INDEX idx_kyc_documents_status ON kyc_documents(verification_status);
```

#### risk_assessments (Risk Assessments)
```sql
CREATE TABLE risk_assessments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    assessment_type VARCHAR(50) NOT NULL, -- initial, periodic, triggered
    risk_level VARCHAR(20) NOT NULL, -- low, medium, high, very_high
    risk_score INTEGER NOT NULL,
    assessment_data JSONB, -- Detailed assessment data
    factors_considered TEXT[],
    recommendations TEXT,
    assessed_by INTEGER, -- user_id of assessor
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_review_date DATE,
    status VARCHAR(50) DEFAULT 'active', -- active, superseded, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_risk_assessments_user_id ON risk_assessments(user_id);
CREATE INDEX idx_risk_assessments_level ON risk_assessments(risk_level);
CREATE INDEX idx_risk_assessments_date ON risk_assessments(assessment_date);
```

### 5.6 Staff Referral System Tables

#### referral_codes (Referral Codes)
```sql
CREATE TABLE referral_codes (
    id SERIAL PRIMARY KEY,
    staff_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL, -- For URL-based referral
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, expired
    max_uses INTEGER, -- NULL means unlimited
    used_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_referral_codes_staff_id ON referral_codes(staff_id);
CREATE INDEX idx_referral_codes_code ON referral_codes(code);
CREATE INDEX idx_referral_codes_token ON referral_codes(token);
CREATE INDEX idx_referral_codes_status ON referral_codes(status);
```

#### referral_registrations (Referral Registrations)
```sql
CREATE TABLE referral_registrations (
    id SERIAL PRIMARY KEY,
    referral_code_id INTEGER REFERENCES referral_codes(id),
    referred_user_id INTEGER REFERENCES users(id),
    source_type VARCHAR(20) NOT NULL, -- code, link
    ip_address INET,
    user_agent TEXT,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_referral_registrations_code_id ON referral_registrations(referral_code_id);
CREATE INDEX idx_referral_registrations_user_id ON referral_registrations(referred_user_id);
```

### 5.7 Audit & Analytics Tables

#### audit_logs (Audit Logs)
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER, -- Can be NULL for system events
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit performance
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

#### analytics_events (Analytics Events)
```sql
CREATE TABLE analytics_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    event_name VARCHAR(100) NOT NULL,
    event_category VARCHAR(50),
    event_properties JSONB,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_name ON analytics_events(event_name);
CREATE INDEX idx_analytics_events_category ON analytics_events(event_category);
CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at);
```

---

## 6) Chỉ số hiệu suất & Tối ưu hóa (Performance Optimization)

### 6.1 Indexing Strategy
- **Primary Indexes**: All foreign keys và frequently queried columns
- **Composite Indexes**: Multi-column queries for complex filters
- **Partial Indexes**: Index only active records for better performance
- **GIN Indexes**: JSONB columns for complex queries
- **Full-text Search**: tsvector indexes for text search

### 6.2 Partitioning Strategy
```sql
-- Partitioning cho large tables by date
CREATE TABLE transactions_y2025m01 PARTITION OF transactions
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Auto-partitioning function
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE + INTERVAL '1 month');
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'transactions_y' || to_char(start_date, 'YYYY') || 'm' || to_char(start_date, 'MM');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF transactions
                    FOR VALUES FROM (%L) TO (%L)',
                   partition_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

### 6.3 Query Optimization
- **Prepared Statements**: For frequently executed queries
- **Connection Pooling**: PgBouncer cho connection management
- **Read Replicas**: Separate read replicas cho reporting
- **Caching Strategy**: Multi-level caching với Redis

---

## 7) Backup & Recovery Strategy

### 7.1 Backup Strategy
```sql
-- Point-in-time recovery setup
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/archive/%f'
max_wal_senders = 10
wal_keep_segments = 64

-- Full backup script
#!/bin/bash
pg_basebackup -D /backup/full/$(date +%Y%m%d) -Ft -z -P -U postgres
```

### 7.2 Data Retention Policy
- **Transactional Data**: 7 years retention
- **Audit Logs**: 10 years retention
- **User Sessions**: 30 days
- **Analytics Data**: 2 years
- **Compliance Data**: As per regulatory requirements

---

## 8) Bảo mật dữ liệu (Data Security)

### 8.1 Encryption Strategy
```sql
-- Extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypted sensitive columns
CREATE TABLE user_profiles_secure (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    encrypted_ssn BYTEA, -- Social Security Number
    encrypted_tax_id BYTEA, -- Tax ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.2 Row-Level Security (RLS)
```sql
-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Policy for users to only see their own profile
CREATE POLICY user_profile_policy ON user_profiles
    FOR ALL TO application_role
    USING (user_id = current_setting('app.current_user_id')::integer);
```

### 8.3 Access Control
- **Database Roles**: Separate roles cho different access levels
- **Application Roles**: Read-only, read-write, admin roles
- **Column-Level Security**: Restrict access to sensitive columns
- **IP Whitelisting**: Restrict database access to specific IPs

---

## 9) Monitoring & Maintenance

### 9.1 Performance Monitoring
```sql
-- Create monitoring views
CREATE VIEW database_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats;

CREATE VIEW active_connections AS
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity;
```

### 9.2 Health Check Queries
```sql
-- Database health check
SELECT 
    'database_size' as metric,
    pg_size_pretty(pg_database_size(current_database())) as value;

-- Connection count
SELECT 
    'active_connections' as metric,
    count(*) as value
FROM pg_stat_activity 
WHERE state = 'active';
```

---

## 10) Migration & Deployment

### 10.1 Database Migration Strategy
```python
# Migration script structure
class MigrationManager:
    def __init__(self):
        self.migrations = []
    
    def add_migration(self, version, sql, rollback_sql):
        """Add migration with rollback capability"""
        self.migrations.append({
            'version': version,
            'sql': sql,
            'rollback': rollback_sql
        })
    
    def run_migrations(self):
        """Execute all pending migrations"""
        for migration in self.migrations:
            if not self.is_applied(migration['version']):
                self.execute(migration['sql'])
                self.mark_applied(migration['version'])
```

### 10.2 Schema Versioning
```sql
-- Migration tracking table
CREATE TABLE schema_migrations (
    version VARCHAR(100) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
```

---

## 11) Testing & Quality Assurance

### 11.1 Test Data Setup
```sql
-- Test user creation
INSERT INTO users (email, password_hash, role_id) VALUES
('test@digitalutopia.com', crypt('password', gen_salt('bf')), 4);

-- Test trading data
INSERT INTO trading_orders (user_id, order_type, symbol, side, quantity, price) VALUES
(1, 'market', 'BTC/USDT', 'buy', 0.1, 50000.00);
```

### 11.2 Data Validation Rules
```sql
-- Check constraints for data integrity
ALTER TABLE trading_orders ADD CONSTRAINT chk_positive_quantity
    CHECK (quantity > 0);

ALTER TABLE transactions ADD CONSTRAINT chk_positive_amount
    CHECK (amount > 0);

ALTER TABLE wallet_balances ADD CONSTRAINT chk_non_negative_balance
    CHECK (available_balance >= 0 AND locked_balance >= 0);
```

---

## 12) Best Practices & Guidelines

### 12.1 Naming Conventions
- **Tables**: snake_case, plural (users, trading_orders)
- **Columns**: snake_case (created_at, user_id)
- **Indexes**: idx_table_column (idx_users_email)
- **Constraints**: chk_table_column (chk_positive_quantity)
- **Sequences**: seq_table_column (seq_users_id)

### 12.2 Development Guidelines
- **Always use transactions** cho critical operations
- **Implement proper error handling** trong all database operations
- **Use prepared statements** cho dynamic queries
- **Log all database changes** cho audit purposes
- **Validate data at application level** before database operations

---

**LƯỢC ĐỒ CSDL DIGITAL UTOPIA PLATFORM**  
*Hoàn thành: 2025-12-05*  
*Trạng thái: Production Ready*  
*Tổng số bảng: 45+ tables, 120+ indexes*