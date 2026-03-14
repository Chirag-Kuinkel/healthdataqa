-- Comprehensive QA Validation Queries for Healthcare Claims
USE healthcare_qa;

-- =====================================================
-- 1. REFERENTIAL INTEGRITY CHECKS
-- =====================================================

-- 1.1 Orphaned Claims (Claims without patients)
SELECT '1.1 Orphaned Claims' as check_name,
       COUNT(*) as issue_count,
       'Claims without valid patient references' as description,
       'Critical' as severity
FROM claims c
LEFT JOIN patients p ON c.patient_id = p.patient_id
WHERE p.patient_id IS NULL
UNION ALL

-- 1.2 Orphaned Claim Lines
SELECT '1.2 Orphaned Claim Lines',
       COUNT(*),
       'Claim lines without valid claim references',
       'Critical'
FROM claim_lines cl
LEFT JOIN claims c ON cl.claim_id = c.claim_id
WHERE c.claim_id IS NULL
UNION ALL

-- 1.3 Invalid Provider References
SELECT '1.3 Invalid Providers',
       COUNT(*),
       'Claims with invalid provider references',
       'High'
FROM claims c
LEFT JOIN providers p ON c.provider_id = p.provider_id
WHERE p.provider_id IS NULL;

-- =====================================================
-- 2. DATA CONSISTENCY CHECKS
-- =====================================================

-- 2.1 Claim Header vs Line Items Total Mismatch
SELECT '2.1 Claim Total Mismatch' as check_name,
       COUNT(*) as issue_count,
       'Claim header amount does not match sum of line items' as description,
       'High' as severity
FROM (
    SELECT 
        c.claim_id,
        c.claim_number,
        c.claim_amount as header_amount,
        SUM(cl.line_total) as calculated_total
    FROM claims c
    JOIN claim_lines cl ON c.claim_id = cl.claim_id
    GROUP BY c.claim_id
    HAVING ABS(header_amount - calculated_total) > 0.01
) as mismatches

UNION ALL

-- 2.2 Duplicate Claim Numbers
SELECT '2.2 Duplicate Claims',
       SUM(dup_count),
       'Multiple claims with same claim number',
       'High'
FROM (
    SELECT COUNT(*) - 1 as dup_count
    FROM claims
    GROUP BY claim_number
    HAVING COUNT(*) > 1
) as duplicates

UNION ALL

-- 2.3 Line Item Calculation Errors
SELECT '2.3 Line Calculation Errors',
       COUNT(*),
       'Line total does not equal units * unit price',
       'Medium'
FROM claim_lines
WHERE ABS(line_total - (units * unit_price)) > 0.01

UNION ALL

-- 2.4 Negative Amounts
SELECT '2.4 Negative Amounts',
       COUNT(*),
       'Records with negative monetary values',
       'High'
FROM (
    SELECT claim_id FROM claims WHERE claim_amount < 0
    UNION ALL
    SELECT claim_id FROM claims WHERE paid_amount < 0
    UNION ALL
    SELECT claim_id FROM claim_lines WHERE line_total < 0
    UNION ALL
    SELECT claim_id FROM claim_lines WHERE unit_price < 0
) as negatives;

-- =====================================================
-- 3. BUSINESS LOGIC VALIDATION (Healthcare Specific)
-- =====================================================

-- 3.1 Gender-Age-Diagnosis Conflicts
SELECT '3.1 Gender-Diagnosis Conflict' as check_name,
       COUNT(*) as issue_count,
       'Male patients with pregnancy/delivery codes' as description,
       'High' as severity
FROM claims c
JOIN patients p ON c.patient_id = p.patient_id
WHERE p.gender = 'M'
  AND c.diagnosis_codes LIKE '%O%'  -- Pregnancy codes start with O

UNION ALL

-- 3.2 Age-Appropriate Services
SELECT '3.2 Age-Inappropriate Service',
       COUNT(*),
       'Patients receiving services inappropriate for age',
       'Medium'
FROM claims c
JOIN patients p ON c.patient_id = p.patient_id
JOIN claim_lines cl ON c.claim_id = cl.claim_id
WHERE 
    (TIMESTAMPDIFF(YEAR, p.date_of_birth, c.service_start_date) < 18 
     AND cl.procedure_code IN ('27447', '27486')) -- Knee replacements in minors
    OR
    (TIMESTAMPDIFF(YEAR, p.date_of_birth, c.service_start_date) > 120 
     AND cl.procedure_code IS NOT NULL) -- Patients older than 120

UNION ALL

-- 3.3 Future Service Dates
SELECT '3.3 Future Dates',
       COUNT(*),
       'Claims with service dates in the future',
       'Critical'
FROM claims
WHERE service_start_date > CURDATE()

UNION ALL

-- 3.4 Date Logic Errors
SELECT '3.4 Date Logic Errors',
       COUNT(*),
       'Service end date before start date',
       'High'
FROM claims
WHERE service_end_date < service_start_date

UNION ALL

-- 3.5 Missing Required Fields
SELECT '3.5 Missing Critical Fields',
       COUNT(*),
       'Records missing required fields',
       'Medium'
FROM (
    SELECT patient_id FROM patients WHERE first_name IS NULL OR last_name IS NULL
    UNION ALL
    SELECT claim_id FROM claims WHERE claim_number IS NULL
    UNION ALL
    SELECT provider_id FROM providers WHERE npi_number IS NULL
) as missing;

-- =====================================================
-- 4. DUPLICATE DETECTION
-- =====================================================

-- 4.1 Exact Duplicate Claims (all fields match)
SELECT '4.1 Exact Duplicate Claims' as check_name,
       COUNT(*) as issue_count,
       'Identical claims submitted multiple times' as description,
       'Medium' as severity
FROM (
    SELECT patient_id, provider_id, service_start_date, service_end_date, claim_amount, COUNT(*)
    FROM claims
    GROUP BY patient_id, provider_id, service_start_date, service_end_date, claim_amount
    HAVING COUNT(*) > 1
) as duplicates

UNION ALL

-- 4.2 Potential Duplicate Patients
SELECT '4.2 Duplicate Patients',
       COUNT(*),
       'Patients with same name and DOB',
       'Medium'
FROM (
    SELECT first_name, last_name, date_of_birth, COUNT(*)
    FROM patients
    GROUP BY first_name, last_name, date_of_birth
    HAVING COUNT(*) > 1
) as duplicates;

-- =====================================================
-- 5. DATA QUALITY METRICS
-- =====================================================

-- 5.1 Complete Data Quality Dashboard
SELECT 
    'Data Quality Dashboard' as report_name,
    CURRENT_DATE as report_date,
    COUNT(DISTINCT patient_id) as total_patients,
    COUNT(DISTINCT claim_id) as total_claims,
    SUM(CASE WHEN p.date_of_birth > CURDATE() THEN 1 ELSE 0 END) as future_dob_count,
    SUM(CASE WHEN p.gender IS NULL THEN 1 ELSE 0 END) as missing_gender_count,
    SUM(CASE WHEN c.claim_amount IS NULL OR c.claim_amount = 0 THEN 1 ELSE 0 END) as zero_claims,
    SUM(CASE WHEN c.diagnosis_codes IS NULL THEN 1 ELSE 0 END) as missing_diagnosis,
    AVG(c.claim_amount) as avg_claim_amount
FROM patients p
LEFT JOIN claims c ON p.patient_id = c.patient_id;

-- 5.2 Claims Status Distribution
SELECT 
    status,
    COUNT(*) as claim_count,
    SUM(claim_amount) as total_amount,
    AVG(claim_amount) as avg_amount,
    CONCAT(ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2), '%') as percentage
FROM claims
GROUP BY status
ORDER BY claim_count DESC;

-- 5.3 Provider Performance Summary
SELECT 
    pr.provider_name,
    pr.provider_type,
    COUNT(c.claim_id) as total_claims,
    SUM(c.claim_amount) as total_billed,
    SUM(c.paid_amount) as total_paid,
    ROUND(AVG(c.paid_amount / c.claim_amount * 100), 2) as payment_rate,
    COUNT(CASE WHEN c.status = 'Denied' THEN 1 END) as denial_count
FROM providers pr
LEFT JOIN claims c ON pr.provider_id = c.provider_id
GROUP BY pr.provider_id
ORDER BY total_billed DESC;

-- =====================================================
-- 6. ADVANCED QA CHECKS (Window Functions)
-- =====================================================

-- 6.1 Claims with Unusual Patterns (Time between submission and service)
WITH claim_timing AS (
    SELECT 
        claim_id,
        claim_number,
        service_start_date,
        submitted_date,
        DATEDIFF(submitted_date, service_start_date) as days_to_submit,
        AVG(DATEDIFF(submitted_date, service_start_date)) OVER () as avg_days,
        STDDEV(DATEDIFF(submitted_date, service_start_date)) OVER () as stddev_days
    FROM claims
    WHERE service_start_date IS NOT NULL AND submitted_date IS NOT NULL
)
SELECT '6.1 Unusual Submission Timing' as check_name,
       COUNT(*) as issue_count,
       'Claims submitted unusually late or early' as description,
       'Low' as severity
FROM claim_timing
WHERE ABS(days_to_submit - avg_days) > 2 * stddev_days;

-- 6.2 Sequential Duplicate Detection (Using LAG)
WITH ordered_claims AS (
    SELECT 
        patient_id,
        claim_id,
        claim_number,
        service_start_date,
        LAG(claim_number) OVER (PARTITION BY patient_id ORDER BY service_start_date) as prev_claim,
        LAG(service_start_date) OVER (PARTITION BY patient_id ORDER BY service_start_date) as prev_date
    FROM claims
)
SELECT '6.2 Back-to-Back Duplicates' as check_name,
       COUNT(*) as issue_count,
       'Same patient with identical service dates' as description,
       'Medium' as severity
FROM ordered_claims
WHERE service_start_date = prev_date;