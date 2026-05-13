-- =====================================================
-- HOW TO RESTORE THIS DATABASE BACKUP
-- =====================================================
-- SYSTEM REQUIREMENTS:
-- 1. XAMPP installed and running
-- 2. Apache and MySQL services started
-- 3. MySQL Workbench installed
-------------------------------

## -- RESTORATION STEPS:

-- STEP 1:
-- Open XAMPP Control Panel and start:
-- • Apache
-- • MySQL
----------

-- STEP 2:
-- Open MySQL Workbench and connect to your local server.
---------------------------------------------------------

-- STEP 3:
-- Create a new database/schema if it does not exist.
-- Example:
-- CREATE DATABASE alias_db;
----------------------------

-- STEP 4:
-- In MySQL Workbench, go to:
-- Server → Data Import
-----------------------

-- STEP 5:
-- Choose:
-- “Import from Self-Contained File”
-- Then select this SQL backup file.
------------------------------------

-- STEP 6:
-- Under “Default Target Schema”, select:
-- alias_db
-----------

-- STEP 7:
-- Click “Start Import” and wait until the import is completed.
---------------------------------------------------------------

-- STEP 8:
-- Open your browser and run the system:
-- [http://localhost/your_project_folder](http://localhost/your_project_folder)
-------------------------------------------------------------------------------

-- =====================================================
-- END OF RESTORE INSTRUCTIONS
-- =====================================================

## -- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)

-- Host: 127.0.0.1    Database: alias_db

---

-- Server version	5.5.5-10.4.32-MariaDB

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

## -- Dumping data for table `audit_logs`

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (208,1,1,'CREATE',NULL,'Heavy Duty First Aid Kit','Initial stock','2026-05-04 15:01:24');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

-- Dump completed on 2026-05-13 16:51:13
