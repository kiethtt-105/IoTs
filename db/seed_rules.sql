-- Vi du 3 luat mac dinh (dap ung yeu cau Lop 3: >=3 luat cau hinh duoc)
-- Chay sau khi da co device_id = 1 (esp32-demo-01) trong bang devices

INSERT INTO rules (name, device_id, condition, action, enabled) VALUES
('Bat quat khi nong', 1, '{"metric":"temperature","operator":">","value":30}', '{"target":"fan","command":"ON"}', true),
('Tat quat khi mat', 1, '{"metric":"temperature","operator":"<","value":26}', '{"target":"fan","command":"OFF"}', true),
('Canh bao khi gas', 1, '{"metric":"gas_level","operator":">","value":300}', '{"target":"buzzer","command":"ALERT"}', true),
('Bat den khi co chuyen dong', 1, '{"metric":"motion","operator":"==","value":true}', '{"target":"light","command":"ON"}', true);
