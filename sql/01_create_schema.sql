DROP DATABASE IF EXISTS healthcare_qa;
CREATE DATABASE healthcare_qa;
USE healthcare_qa;

-- 1. Patients Table
CREATE TABLE patients (
    patient_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'O')),
    ssn VARCHAR(11) UNIQUE,
    address TEXT,
    city VARCHAR(50),
    state CHAR(2),
    zip_code VARCHAR(10),
    phone VARCHAR(15),
    email VARCHAR(100),
    insurance_provider VARCHAR(100),
    insurance_id VARCHAR(50),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient_name (last_name, first_name),
    INDEX idx_patient_dob (date_of_birth)
);

-- 2. Providers Table (Doctors/Hospitals)
CREATE TABLE providers (
    provider_id INT PRIMARY KEY AUTO_INCREMENT,
    provider_name VARCHAR(200) NOT NULL,
    provider_type ENUM('Hospital', 'Clinic', 'Individual', 'Pharmacy', 'Lab') NOT NULL,
    npi_number VARCHAR(20) UNIQUE NOT NULL, -- National Provider Identifier
    tax_id VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    state CHAR(2),
    zip_code VARCHAR(10),
    phone VARCHAR(15),
    email VARCHAR(100),
    specialty VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_provider_npi (npi_number)
);

-- 3. Claims Header Table
CREATE TABLE claims (
    claim_id INT PRIMARY KEY AUTO_INCREMENT,
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    patient_id INT NOT NULL,
    provider_id INT NOT NULL,
    claim_type ENUM('Professional', 'Institutional', 'Pharmacy') NOT NULL,
    service_start_date DATE NOT NULL,
    service_end_date DATE NOT NULL,
    submitted_date DATE NOT NULL,
    received_date DATE,
    processed_date DATE,
    claim_amount DECIMAL(10,2) NOT NULL,
    paid_amount DECIMAL(10,2),
    patient_responsibility DECIMAL(10,2),
    status ENUM('Submitted', 'In-Process', 'Approved', 'Denied', 'Paid', 'Rejected') DEFAULT 'Submitted',
    denial_reason TEXT,
    diagnosis_codes TEXT, -- Comma separated ICD-10 codes
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
    INDEX idx_claim_patient (patient_id),
    INDEX idx_claim_dates (service_start_date, service_end_date),
    INDEX idx_claim_status (status),
    CHECK (service_end_date >= service_start_date),
    CHECK (claim_amount >= 0)
);

-- 4. Claim Lines Table (Detailed services)
CREATE TABLE claim_lines (
    line_id INT PRIMARY KEY AUTO_INCREMENT,
    claim_id INT NOT NULL,
    line_number INT NOT NULL,
    procedure_code VARCHAR(20) NOT NULL, -- CPT/HCPCS codes
    procedure_description TEXT,
    diagnosis_pointer VARCHAR(50), -- Which diagnosis codes apply
    service_date DATE NOT NULL,
    units INT DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    allowed_amount DECIMAL(10,2),
    paid_amount DECIMAL(10,2),
    denial_reason TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    INDEX idx_claim_line (claim_id),
    CHECK (line_total = units * unit_price),
    CHECK (service_date IS NOT NULL)
);

-- 5. Diagnosis Codes Reference
CREATE TABLE diagnosis_codes (
    diagnosis_code VARCHAR(10) PRIMARY KEY,
    description TEXT NOT NULL,
    category VARCHAR(100),
    is_chronic BOOLEAN DEFAULT FALSE,
    is_preventable BOOLEAN DEFAULT FALSE
);

-- 6. Procedure Codes Reference
CREATE TABLE procedure_codes (
    procedure_code VARCHAR(20) PRIMARY KEY,
    description TEXT NOT NULL,
    category VARCHAR(100),
    typical_cost DECIMAL(10,2)
);

-- 7. Data Quality Log (Track issues found)
CREATE TABLE data_quality_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_name VARCHAR(100),
    table_name VARCHAR(50),
    issue_count INT,
    severity ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
    details TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_date TIMESTAMP NULL
);

-- Create Views for Common QA Checks
CREATE VIEW vw_claim_summary AS
SELECT 
    c.claim_id,
    c.claim_number,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    pr.provider_name,
    c.claim_amount,
    c.paid_amount,
    c.status,
    SUM(cl.line_total) as calculated_total,
    CASE 
        WHEN ABS(c.claim_amount - SUM(cl.line_total)) > 0.01 THEN 'Mismatch'
        ELSE 'Match'
    END as amount_validation
FROM claims c
JOIN patients p ON c.patient_id = p.patient_id
JOIN providers pr ON c.provider_id = pr.provider_id
LEFT JOIN claim_lines cl ON c.claim_id = cl.claim_id
GROUP BY c.claim_id;

-- Create Stored Procedure for Daily QA Checks
DELIMITER $$

CREATE PROCEDURE sp_run_daily_qa_checks()
BEGIN
    -- Log orphaned claims check
    INSERT INTO data_quality_log (check_name, table_name, issue_count, severity, details)
    SELECT 
        'Orphaned Claims Check',
        'claims',
        COUNT(*),
        'High',
        CONCAT('Found ', COUNT(*), ' claims with missing patient references')
    FROM claims c
    LEFT JOIN patients p ON c.patient_id = p.patient_id
    WHERE p.patient_id IS NULL;
    
    -- Log duplicate claims check
    INSERT INTO data_quality_log (check_name, table_name, issue_count, severity, details)
    SELECT 
        'Duplicate Claims Check',
        'claims',
        COUNT(*),
        'Medium',
        CONCAT('Found ', COUNT(*), ' potential duplicate claims')
    FROM (
        SELECT claim_number, COUNT(*) as cnt
        FROM claims
        GROUP BY claim_number
        HAVING cnt > 1
    ) as duplicates;
    
    -- Log future dates check
    INSERT INTO data_quality_log (check_name, table_name, issue_count, severity, details)
    SELECT 
        'Future Service Dates',
        'claims',
        COUNT(*),
        'Critical',
        CONCAT('Found ', COUNT(*), ' claims with service dates in the future')
    FROM claims
    WHERE service_start_date > CURDATE();
    
END$$

DELIMITER ;