CREATE DATABASE IF NOT EXISTS ehr_db;
USE ehr_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('doctor','patient') NOT NULL
);

-- Initial doctor account
INSERT INTO users (name, email, password, role) VALUES 
('Dr. John Doe', 'doctor@example.com', 
PASSWORD('doctor123'), 'doctor');
