-- =====================================================
-- 02_create_constraints.sql
-- Database: smart_lock
-- Tạo Foreign Keys + Indexes
-- Chạy SAU khi đã chạy 01_create_tables.sql
-- =====================================================

-- ==================== FOREIGN KEYS ====================

-- devices
ALTER TABLE devices
    ADD CONSTRAINT fk_devices_device_type
        FOREIGN KEY (device_type_id) REFERENCES device_types(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE devices
    ADD CONSTRAINT fk_devices_owner
        FOREIGN KEY (owner_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

-- access_cards
ALTER TABLE access_cards
    ADD CONSTRAINT fk_access_cards_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE access_cards
    ADD CONSTRAINT fk_access_cards_device
        FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE SET NULL ON UPDATE CASCADE;

-- access_permissions
ALTER TABLE access_permissions
    ADD CONSTRAINT fk_access_permissions_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE access_permissions
    ADD CONSTRAINT fk_access_permissions_device
        FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE access_permissions
    ADD CONSTRAINT fk_access_permissions_granted_by
        FOREIGN KEY (granted_by) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

-- pin_codes
ALTER TABLE pin_codes
    ADD CONSTRAINT fk_pin_codes_device
        FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE pin_codes
    ADD CONSTRAINT fk_pin_codes_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE;

-- invites
ALTER TABLE invites
    ADD CONSTRAINT fk_invites_device
        FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE invites
    ADD CONSTRAINT fk_invites_created_by
        FOREIGN KEY (created_by) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;

-- access_logs
ALTER TABLE access_logs
    ADD CONSTRAINT fk_access_logs_device
        FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE access_logs
    ADD CONSTRAINT fk_access_logs_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE access_logs
    ADD CONSTRAINT fk_access_logs_access_card
        FOREIGN KEY (access_card_id) REFERENCES access_cards(id)
        ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE access_logs
    ADD CONSTRAINT fk_access_logs_pin_code
        FOREIGN KEY (pin_code_id) REFERENCES pin_codes(id)
        ON DELETE SET NULL ON UPDATE CASCADE;

-- device_status_logs
ALTER TABLE device_status_logs
    ADD CONSTRAINT fk_device_status_logs_device
        FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

-- notifications
ALTER TABLE notifications
    ADD CONSTRAINT fk_notifications_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE notifications
    ADD CONSTRAINT fk_notifications_device
        FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE SET NULL ON UPDATE CASCADE;

-- device_commands
ALTER TABLE device_commands
    ADD CONSTRAINT fk_device_commands_device
        FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE device_commands
    ADD CONSTRAINT fk_device_commands_issued_by
        FOREIGN KEY (issued_by) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE;


-- ==================== INDEXES ====================

-- users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- devices
CREATE INDEX idx_devices_owner_id ON devices(owner_id);
CREATE INDEX idx_devices_device_type_id ON devices(device_type_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_mac_address ON devices(mac_address);

-- access_cards
CREATE INDEX idx_access_cards_user_id ON access_cards(user_id);
CREATE INDEX idx_access_cards_device_id ON access_cards(device_id);
CREATE INDEX idx_access_cards_card_uid ON access_cards(card_uid);
CREATE INDEX idx_access_cards_is_active ON access_cards(is_active);

-- access_permissions
CREATE INDEX idx_access_permissions_user_id ON access_permissions(user_id);
CREATE INDEX idx_access_permissions_device_id ON access_permissions(device_id);
CREATE INDEX idx_access_permissions_status ON access_permissions(status);
CREATE INDEX idx_access_permissions_valid_from_to ON access_permissions(valid_from, valid_to);

-- pin_codes
CREATE INDEX idx_pin_codes_device_id ON pin_codes(device_id);
CREATE INDEX idx_pin_codes_user_id ON pin_codes(user_id);
CREATE INDEX idx_pin_codes_type ON pin_codes(type);
CREATE INDEX idx_pin_codes_expires_at ON pin_codes(expires_at);

-- invites
CREATE INDEX idx_invites_device_id ON invites(device_id);
CREATE INDEX idx_invites_code ON invites(code);
CREATE INDEX idx_invites_status ON invites(status);
CREATE INDEX idx_invites_expires_at ON invites(expires_at);

-- access_logs (quan trọng nhất để query lịch sử)
CREATE INDEX idx_access_logs_device_id ON access_logs(device_id);
CREATE INDEX idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX idx_access_logs_created_at ON access_logs(created_at DESC);
CREATE INDEX idx_access_logs_device_created ON access_logs(device_id, created_at DESC);
CREATE INDEX idx_access_logs_result ON access_logs(result);
CREATE INDEX idx_access_logs_method ON access_logs(method);

-- device_status_logs
CREATE INDEX idx_device_status_logs_device_id ON device_status_logs(device_id);
CREATE INDEX idx_device_status_logs_recorded_at ON device_status_logs(recorded_at DESC);
CREATE INDEX idx_device_status_logs_device_recorded ON device_status_logs(device_id, recorded_at DESC);

-- notifications
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_device_id ON notifications(device_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;

-- device_commands
CREATE INDEX idx_device_commands_device_id ON device_commands(device_id);
CREATE INDEX idx_device_commands_status ON device_commands(status);
CREATE INDEX idx_device_commands_issued_by ON device_commands(issued_by);
CREATE INDEX idx_device_commands_created_at ON device_commands(created_at DESC);
CREATE INDEX idx_device_commands_pending ON device_commands(device_id, status) WHERE status = 'pending';