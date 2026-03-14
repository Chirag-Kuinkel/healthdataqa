-- Insert sample data with intentional errors for QA testing
USE healthcare_qa;

-- Insert Patients (with some data issues)
INSERT INTO patients (first_name, last_name, date_of_birth, gender, ssn, city, state, zip_code, insurance_provider, insurance_id) VALUES
('John', 'Smith', '1980-05-15', 'M', '123-45-6789', 'New York', 'NY', '10001', 'Blue Cross', 'BC123456'),
('Jane', 'Doe', '1990-08-22', 'F', '234-56-7890', 'Los Angeles', 'CA', '90001', 'Aetna', 'AE789012'),
('Robert', 'Johnson', '1975-03-10', 'M', '345-67-8901', 'Chicago', 'IL', '60601', 'UnitedHealth', 'UH345678'),
('Mary', 'Williams', '1985-11-30', 'F', '456-78-9012', 'Houston', 'TX', '77001', 'Cigna', 'CI901234'),
('James', 'Brown', '2000-07-25', 'M', '567-89-0123', 'Phoenix', 'AZ', '85001', 'Humana', 'HU567890'),
('Patricia', 'Jones', '1965-09-18', 'F', '678-90-1234', 'Philadelphia', 'PA', '19101', 'Medicare', 'MC789012'),
('Michael', 'Garcia', '2025-01-15', 'M', '789-01-2345', 'San Antonio', 'TX', '78201', NULL, NULL), -- Future DOB (error)
('Linda', 'Martinez', '1970-04-05', NULL, '890-12-3456', 'San Diego', 'CA', '92101', 'Kaiser', 'KA123890'), -- NULL gender
('William', 'Robinson', '1982-12-10', 'M', '901-23-4567', 'Dallas', 'TX', '75201', 'Blue Cross', 'BC901234'),
('Elizabeth', 'Clark', '1995-06-20', 'F', '012-34-5678', 'San Jose', 'CA', '95101', 'Aetna', 'AE567890'),
('David', 'Rodriguez', '1978-09-03', 'M', '123-45-6780', 'Austin', 'TX', '78701', NULL, NULL), -- No insurance
('Susan', 'Lewis', '1988-02-28', 'F', '234-56-7891', 'Jacksonville', 'FL', '32099', 'Cigna', 'CI789123'),
('Joseph', 'Lee', '1992-07-12', 'M', '345-67-8902', 'Fort Worth', 'TX', '76101', 'UnitedHealth', 'UH456789'),
('Margaret', 'Walker', '1972-10-08', 'F', '456-78-9013', 'Columbus', 'OH', '43085', 'Humana', 'HU123456'),
('Thomas', 'Hall', '1968-01-19', 'M', '567-89-0124', 'Charlotte', 'NC', '28201', 'Blue Cross', 'BC567890');

-- Insert Providers
INSERT INTO providers (provider_name, provider_type, npi_number, tax_id, city, state, specialty, is_active) VALUES
('Memorial Hospital', 'Hospital', '1234567890', '12-3456789', 'New York', 'NY', 'General Hospital', TRUE),
('City Medical Clinic', 'Clinic', '2345678901', '23-4567890', 'Los Angeles', 'CA', 'Primary Care', TRUE),
('Dr. Sarah Johnson', 'Individual', '3456789012', '34-5678901', 'Chicago', 'IL', 'Cardiology', TRUE),
('Wellness Pharmacy', 'Pharmacy', '4567890123', '45-6789012', 'Houston', 'TX', 'Retail Pharmacy', TRUE),
('Regional Lab Corp', 'Lab', '5678901234', '56-7890123', 'Phoenix', 'AZ', 'Diagnostic Lab', TRUE),
('Community Hospital', 'Hospital', '6789012345', '67-8901234', 'Philadelphia', 'PA', 'General Hospital', TRUE),
('Dr. Michael Chen', 'Individual', '7890123456', '78-9012345', 'San Antonio', 'TX', 'Pediatrics', TRUE),
('Quick Care Clinic', 'Clinic', '8901234567', '89-0123456', 'San Diego', 'CA', 'Urgent Care', TRUE),
('University Medical Center', 'Hospital', '9012345678', '90-1234567', 'Dallas', 'TX', 'Teaching Hospital', TRUE),
('Dr. Emily White', 'Individual', '0123456789', '01-2345678', 'San Jose', 'CA', 'Dermatology', TRUE),
('Invalid Provider', 'Hospital', NULL, NULL, NULL, NULL, NULL, TRUE); -- Missing NPI (error)

-- Insert Claims (with intentional errors for QA testing)
INSERT INTO claims (claim_number, patient_id, provider_id, claim_type, service_start_date, service_end_date, submitted_date, claim_amount, paid_amount, status, diagnosis_codes) VALUES
('CLM-2024-001', 1, 1, 'Professional', '2024-01-15', '2024-01-15', '2024-01-20', 1500.00, 1200.00, 'Paid', 'J20.9,J45.909'),
('CLM-2024-002', 2, 2, 'Institutional', '2024-01-10', '2024-01-12', '2024-01-15', 5000.00, 4000.00, 'Paid', 'I10,E11.9'),
('CLM-2024-003', 3, 3, 'Professional', '2024-01-05', '2024-01-05', '2024-01-08', 800.00, 640.00, 'Paid', 'M54.5'),
('CLM-2024-004', 4, 4, 'Pharmacy', '2024-01-20', '2024-01-20', '2024-01-22', 250.00, 200.00, 'Paid', NULL),
('CLM-2024-005', 5, 5, 'Professional', '2024-01-25', '2024-01-25', '2024-01-28', 3500.00, 2800.00, 'Approved', 'Z00.00'),
('CLM-2024-006', 7, 1, 'Professional', '2024-02-01', '2024-02-01', '2024-02-05', 1200.00, NULL, 'Submitted', 'O20.0'), -- Male patient with pregnancy code (error)
('CLM-2024-007', 2, 2, 'Institutional', '2024-02-10', '2024-02-15', '2024-02-18', 7500.00, NULL, 'Denied', 'S72.0'),
('CLM-2024-008', 8, 3, 'Professional', '2024-02-12', '2024-02-12', '2024-02-14', 600.00, NULL, 'Submitted', NULL),
('CLM-2024-009', 1, 1, 'Professional', '2024-01-15', '2024-01-15', '2024-01-20', 1500.00, NULL, 'Submitted', 'J20.9'), -- Duplicate of claim 1 (error)
('CLM-2024-010', 99, 3, 'Professional', '2024-02-20', '2024-02-20', '2024-02-22', 900.00, NULL, 'Submitted', 'J06.9'), -- Invalid patient_id (error)
('CLM-2024-011', 3, 99, 'Professional', '2024-02-25', '2024-02-25', '2024-02-28', 1100.00, NULL, 'Submitted', 'I10'), -- Invalid provider_id (error)
('CLM-2025-001', 6, 6, 'Institutional', '2025-06-01', '2025-06-05', '2024-03-01', 10000.00, NULL, 'Submitted', 'I63.9'), -- Future service date (error)
('CLM-2024-012', 9, 7, 'Professional', '2024-03-05', '2024-03-04', '2024-03-08', -500.00, NULL, 'Submitted', 'R10.9'), -- Negative amount (error)
('CLM-2024-013', 4, 4, 'Pharmacy', '2024-03-10', '2024-03-10', '2024-03-12', 0.00, 0.00, 'Approved', NULL), -- Zero amount
('CLM-2024-014', 10, 8, 'Professional', '2024-03-15', '2024-03-15', '2024-03-18', NULL, NULL, 'Submitted', 'L23.9'); -- NULL amount (error)

-- Insert Claim Lines (with intentional calculation errors)
INSERT INTO claim_lines (claim_id, line_number, procedure_code, procedure_description, service_date, units, unit_price, line_total, paid_amount) VALUES
(1, 1, '99213', 'Office Visit', '2024-01-15', 1, 1500.00, 1500.00, 1200.00),
(2, 1, '99221', 'Initial Hospital Care', '2024-01-10', 1, 3000.00, 3000.00, 2500.00),
(2, 2, '80048', 'Blood Tests', '2024-01-11', 2, 1000.00, 2000.00, 1500.00),
(3, 1, '97110', 'Therapeutic Exercise', '2024-01-05', 8, 100.00, 800.00, 640.00),
(4, 1, 'J3490', 'Prescription Drug', '2024-01-20', 30, 8.33, 250.00, 200.00),
(5, 1, '93000', 'EKG', '2024-01-25', 1, 500.00, 500.00, 400.00),
(5, 2, '80053', 'Comprehensive Metabolic Panel', '2024-01-25', 1, 3000.00, 3000.00, 2400.00), -- Mismatch with claim total (error)
(6, 1, '59400', 'Obstetric Care', '2024-02-01', 1, 1200.00, 1200.00, NULL), -- Male patient issue
(7, 1, '27447', 'Total Knee Arthroplasty', '2024-02-10', 1, 7500.00, 7500.00, NULL),
(8, 1, '99214', 'Office Visit', '2024-02-12', 1, 600.00, 600.00, NULL),
(9, 1, '99213', 'Office Visit', '2024-01-15', 1, 1500.00, 1500.00, NULL), -- Duplicate
(11, 1, '93005', 'EKG Tracing', '2024-02-25', 1, 1100.00, 1100.00, NULL), -- Invalid provider
(12, 1, '70450', 'Head CT', '2025-06-01', 1, 10000.00, 10000.00, NULL), -- Future date
(13, 1, '99213', 'Office Visit', '2024-03-04', 1, 500.00, 500.00, NULL), -- Mismatch: 500 vs -500 claim total
(13, 2, '80048', 'Blood Tests', '2024-03-05', 1, 1000.00, -1000.00, NULL), -- Negative line total (error)
(14, 1, 'J7030', 'IV Solution', '2024-03-10', 1, 0.00, 0.00, 0.00),
(15, 1, '11100', 'Skin Biopsy', '2024-03-15', 1, 500.00, 500.00, NULL); -- Claim total is NULL

-- Insert Diagnosis Codes Reference
INSERT INTO diagnosis_codes (diagnosis_code, description, category, is_chronic, is_preventable) VALUES
('I10', 'Essential Hypertension', 'Circulatory', TRUE, TRUE),
('E11.9', 'Type 2 Diabetes without complications', 'Endocrine', TRUE, TRUE),
('J20.9', 'Acute bronchitis', 'Respiratory', FALSE, TRUE),
('J45.909', 'Unspecified asthma', 'Respiratory', TRUE, TRUE),
('M54.5', 'Low back pain', 'Musculoskeletal', FALSE, FALSE),
('Z00.00', 'General medical examination', 'Preventive', FALSE, TRUE),
('O20.0', 'Threatened abortion', 'Pregnancy', FALSE, FALSE),
('S72.0', 'Fracture of femoral head', 'Injury', FALSE, FALSE),
('I63.9', 'Cerebral infarction', 'Circulatory', FALSE, TRUE),
('R10.9', 'Unspecified abdominal pain', 'Symptoms', FALSE, FALSE),
('L23.9', 'Allergic contact dermatitis', 'Skin', FALSE, FALSE),
('J06.9', 'Acute upper respiratory infection', 'Respiratory', FALSE, TRUE);

-- Insert Procedure Codes Reference
INSERT INTO procedure_codes (procedure_code, description, category, typical_cost) VALUES
('99213', 'Office/outpatient visit established', 'Evaluation', 150.00),
('99214', 'Office/outpatient visit established', 'Evaluation', 200.00),
('99221', 'Initial hospital care', 'Hospital', 300.00),
('97110', 'Therapeutic exercise', 'Therapy', 100.00),
('93000', 'Electrocardiogram complete', 'Cardiology', 150.00),
('93005', 'Electrocardiogram tracing', 'Cardiology', 100.00),
('80048', 'Basic metabolic panel', 'Lab', 50.00),
('80053', 'Comprehensive metabolic panel', 'Lab', 100.00),
('27447', 'Total knee arthroplasty', 'Surgery', 5000.00),
('59400', 'Obstetric care', 'Maternity', 2000.00),
('70450', 'Head/brain CT without contrast', 'Radiology', 1000.00),
('11100', 'Skin biopsy', 'Dermatology', 200.00),
('J3490', 'Unclassified drugs', 'Pharmacy', 50.00),
('J7030', 'Infusion of normal saline', 'Pharmacy', 25.00);

-- Insert initial QA log
CALL sp_run_daily_qa_checks();

-- Create a view for QA reporting
CREATE VIEW vw_qa_summary_report AS
SELECT 
    d.check_date,
    d.check_name,
    d.table_name,
    d.issue_count,
    d.severity,
    d.is_resolved,
    CASE 
        WHEN d.severity = 'Critical' AND d.issue_count > 0 THEN 'Immediate Action Required'
        WHEN d.severity = 'High' AND d.issue_count > 0 THEN 'Needs Review'
        WHEN d.issue_count = 0 THEN 'Passed'
        ELSE 'Monitor'
    END as action_required
FROM data_quality_log d
ORDER BY d.check_date DESC, FIELD(d.severity, 'Critical', 'High', 'Medium', 'Low');