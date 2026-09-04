-- =====================================================
-- 01_create_tables.sql
-- Database: smart_lock
-- Tạo ENUM types + tất cả các bảng
-- =====================================================

-- ==================== ENUM TYPES ====================

CREATE TYPE user_role AS ENUM ('owner', 'member', 'guest');

CREATE TYPE device_status AS ENUM ('locked', 'unlocked', 'offline', 'tamper');

CREATE TYPE schedule_type AS ENUM ('always', 'time_range', 'recurring');

CREATE TYPE permission_status AS ENUM ('active', 'revoked', 'expired');

CREATE TYPE pin_type AS ENUM ('permanent', 'one_time', 'duress');

CREATE TYPE invite_status AS ENUM ('pending', 'accepted', 'expired', 'revoked');

CREATE TYPE access_method AS ENUM ('app_ble', 'app_remote', 'nfc_card', 'pin', 'auto');

CREATE TYPE access_result AS ENUM ('success', 'failed', 'denied');

CREATE TYPE door_status AS ENUM ('closed', 'open');

CREATE TYPE notification_type AS ENUM ('unlock_success', 'unlock_failed', 'tamper', 'low_battery', 'offline');

CREATE TYPE command_type AS ENUM ('lock', 'unlock', 'reboot', 'ota_update', 'enroll_card');

CREATE TYPE command_status AS ENUM ('pending', 'sent', 'acked', 'failed');


-- ==================== 1. users ====================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    phone           VARCHAR(20),
    password_hash   VARCHAR(255) NOT NULL,
    role            user_role NOT NULL DEFAULT 'member',
    avatar_url      VARCHAR(255),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==================== 2. device_types ====================

CREATE TABLE device_types (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(50) NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL,
    capabilities    JSONB,
    sensor_schema   JSONB
);


-- ==================== 3. devices ====================

CREATE TABLE devices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_type_id      UUID NOT NULL,
    owner_id            UUID NOT NULL,
    name                VARCHAR(100) NOT NULL,
    mac_address         VARCHAR(50) NOT NULL UNIQUE,
    firmware_version    VARCHAR(20),
    status              device_status NOT NULL DEFAULT 'offline',
    battery_level       INT CHECK (battery_level BETWEEN 0 AND 100),
    location            VARCHAR(100),
    paired_at           TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==================== 4. access_cards ====================

CREATE TABLE access_cards (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    device_id       UUID,                           -- nullable: có thể dùng chung nhiều khóa qua permission
    card_uid        VARCHAR(50) NOT NULL UNIQUE,
    label           VARCHAR(50),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    issued_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at      TIMESTAMP
);


-- ==================== 5. access_permissions ====================

CREATE TABLE access_permissions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL,
    device_id               UUID NOT NULL,
    granted_by              UUID NOT NULL,
    schedule_type           schedule_type NOT NULL DEFAULT 'always',
    valid_from              TIMESTAMP,
    valid_to                TIMESTAMP,
    recurring_days          JSONB,                  -- ví dụ: ["mon","tue","wed"]
    recurring_start_time    TIME,
    recurring_end_time      TIME,
    status                  permission_status NOT NULL DEFAULT 'active',
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==================== 6. pin_codes ====================

CREATE TABLE pin_codes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       UUID NOT NULL,
    user_id         UUID,                           -- nullable nếu là mã khách
    pin_hash        VARCHAR(255) NOT NULL,
    type            pin_type NOT NULL DEFAULT 'permanent',
    is_used         BOOLEAN NOT NULL DEFAULT FALSE,  -- cho one_time
    expires_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==================== 7. invites ====================

CREATE TABLE invites (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       UUID NOT NULL,
    created_by      UUID NOT NULL,
    code            VARCHAR(20) NOT NULL UNIQUE,
    max_uses        INT NOT NULL DEFAULT 1,
    used_count      INT NOT NULL DEFAULT 0,
    expires_at      TIMESTAMP NOT NULL,
    status          invite_status NOT NULL DEFAULT 'pending'
);


-- ==================== 8. access_logs ====================

CREATE TABLE access_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id           UUID NOT NULL,
    user_id             UUID,                       -- nullable nếu không xác định được
    access_card_id      UUID,                       -- nullable
    pin_code_id         UUID,                       -- nullable
    method              access_method NOT NULL,
    result              access_result NOT NULL,
    failure_reason      VARCHAR(100),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==================== 9. device_status_logs ====================

CREATE TABLE device_status_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id           UUID NOT NULL,
    battery_level       INT CHECK (battery_level BETWEEN 0 AND 100),
    rssi                INT,
    door_status         door_status,
    tamper_detected     BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==================== 10. notifications ====================

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    device_id       UUID,                           -- nullable
    type            notification_type NOT NULL,
    message         TEXT NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==================== 11. device_commands ====================

CREATE TABLE device_commands (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       UUID NOT NULL,
    command         command_type NOT NULL,
    status          command_status NOT NULL DEFAULT 'pending',
    issued_by       UUID NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acked_at        TIMESTAMP
);