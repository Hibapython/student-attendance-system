USE railway;
-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: railway
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `attendance`
--

DROP TABLE IF EXISTS `attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance` (
  `attendance_id` int NOT NULL AUTO_INCREMENT,
  `roll_number` int DEFAULT NULL,
  `student_name` varchar(100) DEFAULT NULL,
  `h1` enum('A','L','P') DEFAULT 'A',
  `h2` enum('A','L','P') DEFAULT 'A',
  `h3` enum('A','L','P') DEFAULT 'A',
  `h4` enum('A','L','P') DEFAULT 'A',
  `h5` enum('A','L','P') DEFAULT 'A',
  `h6` enum('A','L','P') DEFAULT 'A',
  `total_present` int DEFAULT '0',
  `total_absent` int DEFAULT '0',
  `total_late` int DEFAULT '0',
  `date` date DEFAULT NULL,
  `month` varchar(20) DEFAULT NULL,
  `year` int DEFAULT NULL,
  `semester_number` int DEFAULT NULL,
  PRIMARY KEY (`attendance_id`),
  KEY `roll_number` (`roll_number`),
  KEY `student_name` (`student_name`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`roll_number`) REFERENCES `student_biodata` (`roll_no`),
  CONSTRAINT `attendance_ibfk_2` FOREIGN KEY (`student_name`) REFERENCES `student_biodata` (`full_name`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attendance`
--

LOCK TABLES `attendance` WRITE;
/*!40000 ALTER TABLE `attendance` DISABLE KEYS */;
INSERT INTO `attendance` VALUES (3,2230663,'Fahadhia','P','L','P','A','L','A',2,2,2,'2026-03-01','March',2026,6),(4,1001,'Hiba','P','P','A','P','P','A',4,2,0,'2026-03-01','March',2026,6),(5,2230670,'Ruvaitha','P','A','P','P','L','A',3,2,1,'2026-03-01','March',2026,6),(8,2230663,'Fahadhia','P','P','P','A','L','A',3,2,1,'2026-03-02','March',2026,6),(9,1001,'Hiba','P','P','P','A','P','A',4,2,0,'2026-03-02','March',2026,6),(10,2230670,'Ruvaitha','P','P','A','P','A','A',3,3,0,'2026-03-02','March',2026,6),(11,1001,'Hiba','P','P','A','L','P','P',4,1,1,'2026-04-01','April',2026,2),(14,2230663,'Fahadhia','P','L','P','L','P','P',4,0,2,'2026-04-01','April',2026,2),(15,2230665,'Jivitha','P','L','L','P','L','A',2,1,3,'2026-04-01','April',2026,2),(16,2230670,'Ruvaitha','P','P','L','A','L','L',2,1,3,'2026-04-01','April',2026,2),(17,1001,'Hiba','P','P','P','P','L','P',5,0,1,'2026-04-01','April',2026,6),(20,2230663,'Fahadhia','P','P','L','L','P','P',4,0,2,'2026-04-01','April',2026,6),(21,2230665,'Jivitha','L','A','P','P','P','P',4,1,1,'2026-04-01','April',2026,6),(23,2230670,'Ruvaitha','P','L','L','P','P','P',4,0,2,'2026-04-01','April',2026,6),(24,2230608,'Zaira','A','A','A','A','A','A',0,6,0,'2026-04-01','April',2026,6),(25,2230671,'Enwoo','L','P','P','P','L','P',4,0,2,'2026-04-01','April',2026,6),(26,2230672,'Baek Dowha','P','P','P','P','P','L',5,0,1,'2026-04-01','April',2026,6);
/*!40000 ALTER TABLE `attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `login_credentials`
--

DROP TABLE IF EXISTS `login_credentials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `login_credentials` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_email_role` (`email`,`role`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `login_credentials`
--

LOCK TABLES `login_credentials` WRITE;
/*!40000 ALTER TABLE `login_credentials` DISABLE KEYS */;
INSERT INTO `login_credentials` VALUES (10,'dwubf@gmail.com','abcdefg','Teacher','2026-04-10 15:06:57'),(11,'ruvaitharuvaitha1@gmail.com','ruvai','CR','2026-04-10 16:13:12'),(12,'enjin633@gmail.com','Gachiakuta001','CR','2026-04-10 16:46:45'),(13,'enjin633@gmail.com','Gachiakuta001','Teacher','2026-04-10 16:50:26'),(14,'hibavdul@gmail.com','jjkik','HOD','2026-04-10 16:55:29'),(15,'hibabdul2005@gmail.com','fdhh','Teacher','2026-04-11 14:20:56'),(16,'fahadhiafahadhia@gmail.com','fjjjjjjjjjjjj','HOD','2026-04-11 14:22:12'),(17,'ruvaitharuvaitha1@gmail.com','hnbvv','HOD','2026-04-11 14:39:48'),(18,'dwubf@gmail.com','fdhh','HOD','2026-04-11 15:16:34'),(19,'hibabdul2005@gmail.com','hdjsjnsd','HOD','2026-04-12 16:39:09'),(20,'hibavdul@gmail.com','hfdhghhfhd','CR','2026-04-12 16:44:48'),(21,'hibabdul2005@gmail.com','sggggs','CR','2026-04-12 17:03:49'),(22,'fahadhiafahadhia@gmail.com','vkfllkgkldlkfd','Teacher','2026-04-12 17:21:23'),(23,'dwubf@gmail.com','gmjjjjjjjjjj','CR','2026-04-12 17:53:15'),(24,'ruvaitharuvaitha1@gmail.com','sgvvvvv','Teacher','2026-04-12 18:01:52'),(25,'ggdgfh@gmail.com','ffgvfgfdh','Teacher','2026-04-12 18:02:37'),(26,'hgsdd@gmail.com','sgfgfgdagagf','Teacher','2026-04-12 18:12:53'),(27,'hello@gmail.com','helloworld','Teacher','2026-04-12 18:17:00'),(28,'hello@gmail.com','helloworld','CR','2026-04-12 18:48:33');
/*!40000 ALTER TABLE `login_credentials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `marks`
--

DROP TABLE IF EXISTS `marks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `marks` (
  `marks_id` int NOT NULL AUTO_INCREMENT,
  `student_id` varchar(20) DEFAULT NULL,
  `subject_id` varchar(20) DEFAULT NULL,
  `semester_id` int DEFAULT NULL,
  `total_marks` int DEFAULT NULL,
  `marks_obtained_external` int DEFAULT NULL,
  `marks_obtained_internal` int DEFAULT NULL,
  `cumulative_marks` int DEFAULT NULL,
  PRIMARY KEY (`marks_id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `marks`
--

LOCK TABLES `marks` WRITE;
/*!40000 ALTER TABLE `marks` DISABLE KEYS */;
INSERT INTO `marks` VALUES (16,'2230665','234',6,93,72,21,93),(17,'2230665','345',6,67,45,22,67),(18,'2230665','456',6,77,54,23,77),(19,'2230670','cs0001',2,92,67,25,92),(20,'2230670','cs0002',2,96,75,21,96),(21,'2230670','ABC01',6,95,72,23,95),(22,'2230670','ABC02',6,92,71,21,92),(23,'2230670','TEST101',6,90,70,20,30),(27,'2230671','E9001',6,94,74,20,89),(28,'2230671','D0901',6,99,75,24,99),(29,'2230671','CS6001',6,98,75,23,98),(30,'2230672','E001',6,89,69,20,89),(31,'2230672','ES002',6,89,70,19,89),(32,'2230672','CS001',6,85,60,25,85);
/*!40000 ALTER TABLE `marks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `semester`
--

DROP TABLE IF EXISTS `semester`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `semester` (
  `semester_id` int NOT NULL,
  `semester_no` int NOT NULL,
  `academic_year` varchar(20) NOT NULL,
  PRIMARY KEY (`semester_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `semester`
--

LOCK TABLES `semester` WRITE;
/*!40000 ALTER TABLE `semester` DISABLE KEYS */;
INSERT INTO `semester` VALUES (2,2,'N/A'),(6,0,'');
/*!40000 ALTER TABLE `semester` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `semester_result`
--

DROP TABLE IF EXISTS `semester_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `semester_result` (
  `result_id` int NOT NULL AUTO_INCREMENT,
  `student_id` varchar(20) DEFAULT NULL,
  `semester_id` int DEFAULT NULL,
  `percentage` decimal(5,2) DEFAULT NULL,
  `grade` char(2) DEFAULT NULL,
  `sgpa` decimal(4,2) DEFAULT NULL,
  `cgpa` decimal(4,2) DEFAULT NULL,
  `attendance_mark` int DEFAULT NULL,
  PRIMARY KEY (`result_id`),
  KEY `student_id` (`student_id`),
  KEY `semester_id` (`semester_id`),
  CONSTRAINT `semester_result_ibfk_2` FOREIGN KEY (`semester_id`) REFERENCES `semester` (`semester_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `semester_result`
--

LOCK TABLES `semester_result` WRITE;
/*!40000 ALTER TABLE `semester_result` DISABLE KEYS */;
INSERT INTO `semester_result` VALUES (3,'2230665',6,79.00,'A',4.88,4.88,67),(4,'2230670',2,94.00,'A+',3.87,3.87,0),(5,'2230670',6,93.50,'A+',3.85,3.86,56),(7,'2230671',6,95.33,'A+',5.88,5.88,67),(8,'2230672',6,87.67,'A+',5.41,5.41,83);
/*!40000 ALTER TABLE `semester_result` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student_biodata`
--

DROP TABLE IF EXISTS `student_biodata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student_biodata` (
  `student_id` varchar(100) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `roll_no` int NOT NULL,
  `exam_reg` varchar(100) DEFAULT NULL,
  `class_sec` varchar(50) NOT NULL,
  `dob` date DEFAULT NULL,
  `mother_name` varchar(100) NOT NULL,
  `mother_occ` varchar(100) DEFAULT NULL,
  `father_name` varchar(100) NOT NULL,
  `father_occ` varchar(100) DEFAULT NULL,
  `res_address` text,
  `bus_address` text NOT NULL,
  `primary_phone` varchar(15) DEFAULT NULL,
  `alt_phone` varchar(15) DEFAULT NULL,
  `school_name` varchar(150) DEFAULT NULL,
  `category` enum('FC','BC','SC','ST') DEFAULT NULL,
  `group_studied` varchar(50) DEFAULT NULL,
  `scholarship` varchar(150) DEFAULT NULL,
  `add_qual` varchar(150) DEFAULT NULL,
  `extra_curric` varchar(150) DEFAULT NULL,
  `ncc_sports` varchar(150) DEFAULT NULL,
  `achievements` text,
  `hobbies` varchar(255) DEFAULT NULL,
  `blood_group` varchar(5) DEFAULT NULL,
  `hostel` tinyint(1) NOT NULL,
  `photo` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `hsc_marks` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`student_id`),
  UNIQUE KEY `id` (`student_id`),
  UNIQUE KEY `roll_no` (`roll_no`),
  UNIQUE KEY `roll_no_2` (`roll_no`),
  UNIQUE KEY `roll_no_3` (`roll_no`),
  KEY `full_name` (`full_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_biodata`
--

LOCK TABLES `student_biodata` WRITE;
/*!40000 ALTER TABLE `student_biodata` DISABLE KEYS */;
INSERT INTO `student_biodata` VALUES ('2023UCS605','Jivitha',2230665,'2023UCS605','3rd year','2026-03-18','Sarasu','House Wife','Ravi Randon','Labour','No. 12, 5th cross , Annai sathiya nagar, puducherry-12','No. 2 , Cazy Street , puducherry-01','82200692104','9876543210','immaculate','SC','Computer Science','idk','NIL','Cricket','Tennis','never','Watching TV','A+ve',0,'Lilium_candidum_1.jpg','2026-03-20 06:09:39','582'),('2023UCS608','Zaira',2230608,'2023UCS608','3rd year','2022-02-09','Parveen Begum','House-wife','Haja ','Labour','no.10 M.G Road ','no.10 M.G Road ','979898665432','9866543456','Ar Rahmaan ','BC','Computer Science','-NIL-','-NIL-','Cricket','badmiton','soon','Internet Surfing','B-ve',0,'FAHA.jpeg','2026-04-10 15:14:38','550'),('2023UCS611','Enwoo',2230671,'2023UCS611','3rd year','2005-01-11','IU','Solo Artist','Lee Jong Suk','Actor','Seoul ','South Korea','6374829174','2516274829','Seoul University','BC','Computer Science','-NIL-','Working at an entertainment','Model','Basketball','MAMA Award','Travel','O-ve',0,'Enwoo.jpeg','2026-04-12 18:24:06','600'),('2023UCS612','Baek Dowha',2230672,'2023UCS612','3rd year','2005-02-11','Ruvaitha','IT Analyst','Jungkook','Kpop Idol','Puducherry India','Seoul South Korea','647372836487','7382746365','Seoul University','BC','Computer Science','-NIL-','Working at an entertainment','Model','Football','MAMA Award','Surfing','O-ve',0,'Dowha.jpeg','2026-04-12 18:53:26','599'),('5','Hiba',1001,'2001','2AB','2005-05-11','Amma','Islamic Teacher','Bappu','IT Analyst','muwhqg','fsgfgn','9677451820','9791385582','AR RAHMAAN','BC','Computer Science','idk','HUH','i draw','Chess','soon Inshallah','draw, cook, bake, watch anime','O+ve',0,'download (2).jpeg','2026-02-10 21:01:58','559'),('7','Ruvaitha',2230670,'2023UCS610','3 rd year','2006-02-22','Ummul kubra','House wife','Hameed','Labour','No. 11b, Ramaraja Street, Opposite to Railway Station,\nWhite Town , Puducherry-01.','No. 70, Ellaiamman Koil Street, Opposite to Railway Station, \nWhite Town , Puducherry-01.','8807922955','9876543210','Immaculate Hr. Sec. School','BC','Computer Science','-NIL-','-NIL-','-NIL-','-NIL-','later','Internet Surfing','O+ve',0,'PIC.jpeg','2026-02-13 04:07:39','551'),('8','Fahadhia',2230663,'2023UCS610','3 rd year','2006-01-28','Aisha Bee','House wife','Mohammed Farool','Food business','No. 28, V.O.C street, puducherry-01.','No. 28, V.O.C Street , puducherry-01.','8807196997','7708264953','Immaculate hr. Sec. School','BC','Computer Science','-NIL-','-NIL-','-NIL-','-NIL-','-NIL-','Henna Designs','B+ve',0,'FAHA.jpeg','2026-02-19 05:45:46','475');
/*!40000 ALTER TABLE `student_biodata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students`
--

DROP TABLE IF EXISTS `students`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students` (
  `student_id` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students`
--

LOCK TABLES `students` WRITE;
/*!40000 ALTER TABLE `students` DISABLE KEYS */;
INSERT INTO `students` VALUES ('S001','Aarthi'),('S002','Divya'),('S003','Nivetha');
/*!40000 ALTER TABLE `students` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subject`
--

DROP TABLE IF EXISTS `subject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subject` (
  `subject_id` varchar(20) NOT NULL,
  `subject_name` varchar(100) DEFAULT NULL,
  `semester_id` int DEFAULT NULL,
  PRIMARY KEY (`subject_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subject`
--

LOCK TABLES `subject` WRITE;
/*!40000 ALTER TABLE `subject` DISABLE KEYS */;
INSERT INTO `subject` VALUES ('234','CN',6),('345','OS',6),('456','DBMS',6),('ABC01','Microprocessor',6),('ABC02','Digital Electronics',6),('cs0001','cn',2),('cs0002','dbms',2),('CS001','Python',6),('CS6001','Microprocessor',6),('D0901','DBMS',6),('E001','SE',6),('E9001','CN',6),('ES002','Java',6);
/*!40000 ALTER TABLE `subject` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-13 11:37:09
