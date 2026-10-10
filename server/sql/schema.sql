-- =============================================================
-- 校园失物招领信息平台  数据库结构（论文附录）
-- 由 ORM 模型生成后经 mysqldump 导出，结构与 app/models/ 完全一致
-- MySQL 8.0 / utf8mb4_unicode_ci
-- =============================================================
CREATE DATABASE IF NOT EXISTS campus_lostfound
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campus_lostfound;

/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_attachment` (
  `entity_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `entity_id` int DEFAULT NULL,
  `uploader_id` int DEFAULT NULL,
  `original_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `saved_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rel_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mime` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `size` int NOT NULL,
  `checksum` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `saved_name` (`saved_name`),
  KEY `uploader_id` (`uploader_id`),
  KEY `ix_t_attachment_created_at` (`created_at`),
  CONSTRAINT `t_attachment_ibfk_1` FOREIGN KEY (`uploader_id`) REFERENCES `t_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_category` (
  `name` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parent_id` int DEFAULT NULL,
  `icon` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sort_order` int DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `description` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`),
  KEY `parent_id` (`parent_id`),
  KEY `ix_t_category_created_at` (`created_at`),
  CONSTRAINT `t_category_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `t_category` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_claim` (
  `claim_no` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `found_item_id` int NOT NULL,
  `lost_item_id` int DEFAULT NULL,
  `claimant_id` int NOT NULL,
  `claim_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reason` text COLLATE utf8mb4_unicode_ci,
  `evidence` text COLLATE utf8mb4_unicode_ci,
  `contact` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `handler_id` int DEFAULT NULL,
  `handle_comment` text COLLATE utf8mb4_unicode_ci,
  `handled_at` datetime DEFAULT NULL,
  `archived_at` datetime DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_t_claim_claim_no` (`claim_no`),
  KEY `lost_item_id` (`lost_item_id`),
  KEY `claimant_id` (`claimant_id`),
  KEY `handler_id` (`handler_id`),
  KEY `idx_claim_item` (`found_item_id`,`status`),
  KEY `ix_t_claim_created_at` (`created_at`),
  KEY `idx_claim_status` (`status`),
  CONSTRAINT `t_claim_ibfk_1` FOREIGN KEY (`found_item_id`) REFERENCES `t_found_item` (`id`) ON DELETE CASCADE,
  CONSTRAINT `t_claim_ibfk_2` FOREIGN KEY (`lost_item_id`) REFERENCES `t_lost_item` (`id`) ON DELETE SET NULL,
  CONSTRAINT `t_claim_ibfk_3` FOREIGN KEY (`claimant_id`) REFERENCES `t_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `t_claim_ibfk_4` FOREIGN KEY (`handler_id`) REFERENCES `t_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_found_item` (
  `code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `founder_id` int NOT NULL,
  `category_id` int NOT NULL,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `features` text COLLATE utf8mb4_unicode_ci,
  `keywords` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `found_place` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `found_zone` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `found_time` datetime NOT NULL,
  `storage_place` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `images` text COLLATE utf8mb4_unicode_ci,
  `is_sensitive` tinyint(1) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `view_count` int NOT NULL,
  `claimed_by` int DEFAULT NULL,
  `claimed_at` datetime DEFAULT NULL,
  `archived_at` datetime DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_t_found_item_code` (`code`),
  KEY `founder_id` (`founder_id`),
  KEY `claimed_by` (`claimed_by`),
  KEY `idx_found_cat_status` (`category_id`,`status`),
  KEY `ix_t_found_item_found_zone` (`found_zone`),
  KEY `ix_t_found_item_created_at` (`created_at`),
  KEY `ix_t_found_item_found_time` (`found_time`),
  KEY `idx_found_status_time` (`status`,`found_time`),
  KEY `ix_t_found_item_status` (`status`),
  CONSTRAINT `t_found_item_ibfk_1` FOREIGN KEY (`founder_id`) REFERENCES `t_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `t_found_item_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `t_category` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `t_found_item_ibfk_3` FOREIGN KEY (`claimed_by`) REFERENCES `t_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_login_attempt` (
  `username` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `success` tinyint(1) NOT NULL,
  `locked_until` datetime DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_t_login_attempt_created_at` (`created_at`),
  KEY `ix_t_login_attempt_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_lost_item` (
  `code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `owner_id` int NOT NULL,
  `category_id` int NOT NULL,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `features` text COLLATE utf8mb4_unicode_ci,
  `keywords` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `lost_place` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `lost_zone` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `lost_time` datetime NOT NULL,
  `images` text COLLATE utf8mb4_unicode_ci,
  `reward` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_urgent` tinyint(1) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `view_count` int NOT NULL,
  `matched_found_id` int DEFAULT NULL,
  `archived_at` datetime DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_t_lost_item_code` (`code`),
  KEY `owner_id` (`owner_id`),
  KEY `matched_found_id` (`matched_found_id`),
  KEY `ix_t_lost_item_status` (`status`),
  KEY `ix_t_lost_item_created_at` (`created_at`),
  KEY `idx_lost_cat_status` (`category_id`,`status`),
  KEY `ix_t_lost_item_lost_time` (`lost_time`),
  KEY `idx_lost_status_time` (`status`,`lost_time`),
  KEY `ix_t_lost_item_lost_zone` (`lost_zone`),
  CONSTRAINT `t_lost_item_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `t_user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `t_lost_item_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `t_category` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `t_lost_item_ibfk_3` FOREIGN KEY (`matched_found_id`) REFERENCES `t_found_item` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_match_record` (
  `found_item_id` int NOT NULL,
  `lost_item_id` int NOT NULL,
  `score` float NOT NULL,
  `detail` text COLLATE utf8mb4_unicode_ci,
  `level` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `notified_at` datetime DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_match_pair` (`found_item_id`,`lost_item_id`),
  KEY `lost_item_id` (`lost_item_id`),
  KEY `ix_t_match_record_created_at` (`created_at`),
  KEY `idx_match_score` (`score`),
  CONSTRAINT `t_match_record_ibfk_1` FOREIGN KEY (`found_item_id`) REFERENCES `t_found_item` (`id`) ON DELETE CASCADE,
  CONSTRAINT `t_match_record_ibfk_2` FOREIGN KEY (`lost_item_id`) REFERENCES `t_lost_item` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_notification` (
  `user_id` int NOT NULL,
  `type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `related_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `related_id` int DEFAULT NULL,
  `link` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL,
  `read_at` datetime DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_t_notification_is_read` (`is_read`),
  KEY `idx_notify_user_read` (`user_id`,`is_read`),
  KEY `ix_t_notification_created_at` (`created_at`),
  CONSTRAINT `t_notification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_operation_log` (
  `user_id` int DEFAULT NULL,
  `username` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_type` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `target_id` int DEFAULT NULL,
  `detail` text COLLATE utf8mb4_unicode_ci,
  `ip` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `result` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `ix_t_operation_log_action` (`action`),
  KEY `ix_t_operation_log_created_at` (`created_at`),
  KEY `idx_log_target` (`target_type`,`target_id`),
  CONSTRAINT `t_operation_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_system_setting` (
  `key` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  `remark` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `ix_t_system_setting_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_user` (
  `username` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `student_no` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `real_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `college` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password_hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `salt` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `credit_score` int NOT NULL,
  `verified` tinyint(1) NOT NULL,
  `last_login_at` datetime DEFAULT NULL,
  `last_login_ip` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_t_user_username` (`username`),
  UNIQUE KEY `ix_t_user_email` (`email`),
  UNIQUE KEY `ix_t_user_student_no` (`student_no`),
  KEY `ix_t_user_role` (`role`),
  KEY `ix_t_user_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

