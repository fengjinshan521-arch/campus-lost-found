-- =============================================================
-- 校园失物招领信息平台  初始化数据
-- 执行顺序：先执行 sql/schema.sql，再执行本文件
-- 说明：由 scripts/export_init_sql.py 从运行中数据库导出，与 ORM 模型一致
-- =============================================================
USE campus_lostfound;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 物品分类：7 个一级分类 + 二级分类（自引用 parent_id）
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (1, '证件卡包', 'card', NULL, 1, 1, '证件卡包类物品', NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (2, '身份证', NULL, 1, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (3, '学生证', NULL, 1, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (4, '银行卡', NULL, 1, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (5, '校园卡', NULL, 1, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (6, '电子设备', 'device', NULL, 2, 1, '电子设备类物品', NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (7, '手机', NULL, 6, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (8, '笔记本', NULL, 6, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (9, '平板', NULL, 6, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (10, '耳机', NULL, 6, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (11, '充电宝', NULL, 6, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (12, '书籍文具', 'book', NULL, 3, 1, '书籍文具类物品', NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (13, '教材', NULL, 12, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (14, '笔记', NULL, 12, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (15, '文具', NULL, 12, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (16, '书包', NULL, 12, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (17, '衣物箱包', 'clothes', NULL, 4, 1, '衣物箱包类物品', NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (18, '外套', NULL, 17, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (19, '围巾', NULL, 17, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (20, '雨伞', NULL, 17, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (21, '行李箱', NULL, 17, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (22, '钥匙', 'key', NULL, 5, 1, '钥匙类物品', NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (23, '宿舍钥匙', NULL, 22, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (24, '车钥匙', NULL, 22, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (25, '钥匙串', NULL, 22, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (26, '生活用品', 'daily', NULL, 6, 1, '生活用品类物品', NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (27, '水杯', NULL, 26, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (28, '眼镜', NULL, 26, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (29, '饰品', NULL, 26, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (30, '运动器材', NULL, 26, 0, 1, NULL, NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);
INSERT INTO t_category (id, name, code, parent_id, sort_order, is_active, description, created_at, updated_at) VALUES (31, '其他', 'other', NULL, 7, 1, '其他类物品', NOW(), NOW()) ON DUPLICATE KEY UPDATE name = VALUES(name);

-- 2. 管理员账号：admin / Admin@12345（PBKDF2-HMAC-SHA256 + 随机盐）
INSERT INTO t_user (username, student_no, real_name, password_hash, salt, role, status, college, verified, credit_score, created_at, updated_at) VALUES ('admin', NULL, '系统管理员', '2c1b38ed7232a9bb8146822b297f89dbd34ddc18120e339bfb7603c537f582aa', '80748fcb5f9a66fd197f1b9ae9396c38', 'admin', 'active', '信息化办公室', 1, 100, NOW(), NOW()) ON DUPLICATE KEY UPDATE username = username;

-- 3. 系统参数：匹配推荐六因子权重
INSERT INTO t_system_setting (`key`, value, remark, created_at, updated_at) VALUES ('match_weights', '{"category": 0.25, "keyword": 0.2, "location": 0.15, "time": 0.15, "feature": 0.15, "text": 0.1}', '匹配推荐算法六因子权重', NOW(), NOW()) ON DUPLICATE KEY UPDATE value = VALUES(value);

SET FOREIGN_KEY_CHECKS = 1;
