-- ============================================================
-- BGCGW Student Management System — Database Schema
-- Run: mysql -u root -p < database/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS attendance_system
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE attendance_system;

CREATE TABLE IF NOT EXISTS `login_credentials` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(150) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `role` VARCHAR(50) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_email_role` (`email`, `role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `student_biodata` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `full_name` VARCHAR(100) NOT NULL,
  `roll_no` INT NOT NULL,
  `exam_reg` VARCHAR(100) DEFAULT NULL,
  `class_sec` VARCHAR(50) NOT NULL DEFAULT '',
  `dob` DATE DEFAULT NULL,
  `mother_name` VARCHAR(100) NOT NULL DEFAULT '',
  `mother_occ` VARCHAR(100) DEFAULT NULL,
  `father_name` VARCHAR(100) NOT NULL DEFAULT '',
  `father_occ` VARCHAR(100) DEFAULT NULL,
  `res_address` TEXT,
  `bus_address` TEXT,
  `primary_phone` VARCHAR(15) DEFAULT NULL,
  `alt_phone` VARCHAR(15) DEFAULT NULL,
  `school_name` VARCHAR(150) DEFAULT NULL,
  `category` ENUM('FC','BC','SC','ST') DEFAULT NULL,
  `group_studied` VARCHAR(50) DEFAULT NULL,
  `scholarship` VARCHAR(150) DEFAULT NULL,
  `add_qual` VARCHAR(150) DEFAULT NULL,
  `extra_curric` VARCHAR(150) DEFAULT NULL,
  `ncc_sports` VARCHAR(150) DEFAULT NULL,
  `achievements` TEXT,
  `hobbies` VARCHAR(255) DEFAULT NULL,
  `blood_group` VARCHAR(5) DEFAULT NULL,
  `hostel` TINYINT(1) NOT NULL DEFAULT 0,
  `photo` VARCHAR(255) DEFAULT NULL,
  `hsc_marks` VARCHAR(10) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_roll_no` (`roll_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `attendance` (
  `attendance_id` INT AUTO_INCREMENT PRIMARY KEY,
  `roll_number` VARCHAR(20) DEFAULT NULL,
  `student_name` VARCHAR(100) DEFAULT NULL,
  `date` DATE DEFAULT NULL,
  `month` VARCHAR(20) DEFAULT NULL,
  `year` INT DEFAULT NULL,
  `semester_number` INT DEFAULT NULL,
  `h1` ENUM('P','A','L') DEFAULT 'A',
  `h2` ENUM('P','A','L') DEFAULT 'A',
  `h3` ENUM('P','A','L') DEFAULT 'A',
  `h4` ENUM('P','A','L') DEFAULT 'A',
  `h5` ENUM('P','A','L') DEFAULT 'A',
  `h6` ENUM('P','A','L') DEFAULT 'A',
  `total_present` INT DEFAULT 0,
  `total_absent` INT DEFAULT 0,
  `total_late` INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `semester` (
  `semester_id` INT AUTO_INCREMENT PRIMARY KEY,
  `semester_no` INT NOT NULL DEFAULT 1,
  `academic_year` VARCHAR(20) NOT NULL DEFAULT 'N/A'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `subject` (
  `subject_id` VARCHAR(20) NOT NULL PRIMARY KEY,
  `subject_name` VARCHAR(100) DEFAULT NULL,
  `semester_id` INT DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `marks` (
  `marks_id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` VARCHAR(20) DEFAULT NULL,
  `subject_id` VARCHAR(20) DEFAULT NULL,
  `semester_id` INT DEFAULT NULL,
  `total_marks` INT DEFAULT NULL,
  `marks_obtained_external` INT DEFAULT NULL,
  `marks_obtained_internal` INT DEFAULT NULL,
  `cumulative_marks` INT DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `semester_result` (
  `result_id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` VARCHAR(20) DEFAULT NULL,
  `semester_id` INT DEFAULT NULL,
  `percentage` DECIMAL(5,2) DEFAULT NULL,
  `grade` CHAR(2) DEFAULT NULL,
  `sgpa` DECIMAL(4,2) DEFAULT NULL,
  `cgpa` DECIMAL(4,2) DEFAULT NULL,
  `attendance_mark` DECIMAL(4,2) DEFAULT NULL,
  KEY `idx_student` (`student_id`),
  KEY `idx_semester` (`semester_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
