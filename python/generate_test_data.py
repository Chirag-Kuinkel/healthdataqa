import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import mysql.connector
import os

# Initialize Faker
fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

class HealthcareDataGenerator:
    def __init__(self):
        self.patients = []
        self.providers = []
        self.claims = []
        self.claim_lines = []
        
        # Diagnosis codes (ICD-10)
        self.diagnosis_codes = [
            ('I10', 'Essential Hypertension', 'Circulatory', True),
            ('E11.9', 'Type 2 Diabetes', 'Endocrine', True),
            ('J45.909', 'Asthma', 'Respiratory', True),
            ('M54.5', 'Low Back Pain', 'Musculoskeletal', False),
            ('J20.9', 'Acute Bronchitis', 'Respiratory', False),
            ('N39.0', 'UTI', 'Urinary', False),
            ('Z00.00', 'General Exam', 'Preventive', False),
            ('O20.0', 'Threatened Abortion', 'Pregnancy', False),
            ('S72.0', 'Femur Fracture', 'Injury', False),
            ('F41.9', 'Anxiety', 'Mental Health', True)
        ]
        
        # Procedure codes (CPT)
        self.procedure_codes = [
            ('99213', 'Office Visit', 150.00),
            ('99214', 'Office Visit', 200.00),
            ('99221', 'Hospital Care', 300.00),
            ('97110', 'Physical Therapy', 100.00),
            ('93000', 'EKG', 150.00),
            ('80048', 'Basic Metabolic Panel', 50.00),
            ('80053', 'Comprehensive Metabolic Panel', 100.00),
            ('27447', 'Total Knee Replacement', 5000.00),
            ('59400', 'Obstetric Care', 2000.00),
            ('J3490', 'Prescription Drug', 50.00)
        ]
        
    def generate_patients(self, n=50):
        """Generate patient records with some intentional errors"""
        print(f"Generating {n} patients...")
        
        for i in range(n):
            # Introduce some data quality issues
            if i % 10 == 0:  # Every 10th patient has missing data
                first_name = None
            else:
                first_name = fake.first_name()
                
            if i % 15 == 0:  # Every 15th patient has future DOB (error)
                dob = fake.date_between(start_date='+1y', end_date='+5y')
            else:
                dob = fake.date_of_birth(minimum_age=0, maximum_age=90)
                
            if i % 20 == 0:  # Every 20th patient has invalid gender
                gender = None
            else:
                gender = random.choice(['M', 'F'])
                
            patient = {
                'patient_id': i + 1,
                'first_name': first_name,
                'last_name': fake.last_name() if first_name else None,
                'date_of_birth': dob,
                'gender': gender,
                'ssn': fake.ssn(),
                'address': fake.address().replace('\n', ', '),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode(),
                'phone': fake.phone_number(),
                'email': fake.email(),
                'insurance_provider': random.choice(['Blue Cross', 'Aetna', 'UnitedHealth', 'Cigna', 'Humana', None]),
                'insurance_id': fake.bothify(text='???######') if random.random() > 0.2 else None
            }
            self.patients.append(patient)
            
        return pd.DataFrame(self.patients)
    
    def generate_providers(self, n=20):
        """Generate provider records"""
        print(f"Generating {n} providers...")
        
        provider_types = ['Hospital', 'Clinic', 'Individual', 'Pharmacy', 'Lab']
        specialties = ['Cardiology', 'Pediatrics', 'Orthopedics', 'Dermatology', 'Primary Care', 
                      'Neurology', 'Oncology', 'Radiology', 'Emergency Medicine']
        
        for i in range(n):
            # Introduce some errors
            if i % 25 == 0:  # Every 25th provider has missing NPI (error)
                npi = None
            else:
                npi = fake.npi() if hasattr(fake, 'npi') else str(random.randint(1000000000, 9999999999))
                
            provider = {
                'provider_id': i + 1,
                'provider_name': fake.company() if i % 3 != 0 else f"Dr. {fake.last_name()}",
                'provider_type': random.choice(provider_types),
                'npi_number': npi,
                'tax_id': fake.bothify(text='##-#######'),
                'address': fake.address().replace('\n', ', '),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode(),
                'phone': fake.phone_number(),
                'email': fake.email(),
                'specialty': random.choice(specialties) if random.random() > 0.2 else None,
                'is_active': random.random() > 0.1  # 90% active
            }
            self.providers.append(provider)
            
        return pd.DataFrame(self.providers)
    
    def generate_claims(self, n=100):
        """Generate claims with intentional errors"""
        print(f"Generating {n} claims...")
        
        claim_types = ['Professional', 'Institutional', 'Pharmacy']
        statuses = ['Submitted', 'In-Process', 'Approved', 'Denied', 'Paid', 'Rejected']
        
        for i in range(n):
            # Randomly select valid or invalid patient/provider
            if i % 20 == 0:  # 5% chance of invalid references
                patient_id = random.randint(1000, 2000)  # Non-existent patient
            else:
                patient_id = random.randint(1, len(self.patients))
                
            if i % 15 == 0:  # ~7% chance of invalid provider
                provider_id = random.randint(1000, 2000)
            else:
                provider_id = random.randint(1, len(self.providers))
            
            # Service dates
            if i % 30 == 0:  # Future dates (error)
                service_start = fake.date_between(start_date='+1d', end_date='+1y')
            else:
                service_start = fake.date_between(start_date='-1y', end_date='today')
                
            if i % 25 == 0:  # End date before start date (error)
                service_end = service_start - timedelta(days=random.randint(1, 10))
            else:
                service_end = service_start + timedelta(days=random.randint(0, 30))
            
            # Claim amount
            if i % 40 == 0:  # Negative amount (error)
                claim_amount = -random.uniform(100, 10000)
            elif i % 50 == 0:  # Zero amount
                claim_amount = 0
            else:
                claim_amount = round(random.uniform(50, 15000), 2)
            
            # Status and payment
            status = random.choice(statuses)
            if status == 'Paid':
                paid_amount = round(claim_amount * random.uniform(0.7, 1.0), 2) if claim_amount > 0 else 0
            else:
                paid_amount = None
                
            # Diagnosis codes (maybe multiple)
            num_diag = random.randint(0, 3)
            if num_diag > 0:
                diag_codes = ','.join([code[0] for code in random.sample(self.diagnosis_codes, num_diag)])
            else:
                diag_codes = None
                
            # Gender-specific diagnoses (introduce errors)
            if i % 8 == 0:  # Male with pregnancy code (error)
                diag_codes = 'O20.0'
            
            claim = {
                'claim_id': i + 1,
                'claim_number': f"CLM-{datetime.now().year}-{str(i+1).zfill(5)}",
                'patient_id': patient_id,
                'provider_id': provider_id,
                'claim_type': random.choice(claim_types),
                'service_start_date': service_start,
                'service_end_date': service_end,
                'submitted_date': service_start + timedelta(days=random.randint(1, 15)),
                'received_date': service_start + timedelta(days=random.randint(2, 20)) if random.random() > 0.2 else None,
                'processed_date': service_start + timedelta(days=random.randint(10, 45)) if status in ['Approved', 'Denied', 'Paid'] else None,
                'claim_amount': claim_amount,
                'paid_amount': paid_amount,
                'patient_responsibility': round(claim_amount * random.uniform(0, 0.2), 2) if claim_amount > 0 else 0,
                'status': status,
                'denial_reason': "Service not covered" if status == 'Denied' else None,
                'diagnosis_codes': diag_codes
            }
            self.claims.append(claim)
            
        return pd.DataFrame(self.claims)
    
    def generate_claim_lines(self):
        """Generate line items for claims"""
        print("Generating claim lines...")
        
        line_id = 1
        for claim in self.claims:
            claim_id = claim['claim_id']
            num_lines = random.randint(1, 5)
            calculated_total = 0
            
            for line_num in range(num_lines):
                proc_code, proc_desc, base_price = random.choice(self.procedure_codes)
                units = random.randint(1, 10) if 'J' not in proc_code else random.randint(1, 30)  # Drugs have higher units
                
                # Unit price with some variation
                unit_price = round(base_price * random.uniform(0.8, 1.5), 2)
                
                # Introduce calculation errors
                if line_id % 50 == 0:  # Line total calculation error
                    line_total = round(units * unit_price * 1.1, 2)  # 10% over
                elif line_id % 75 == 0:  # Negative line total
                    line_total = -round(units * unit_price, 2)
                else:
                    line_total = round(units * unit_price, 2)
                    
                calculated_total += line_total
                
                # Service date within claim range
                if isinstance(claim['service_start_date'], str):
                    start_date = datetime.strptime(claim['service_start_date'], '%Y-%m-%d').date()
                else:
                    start_date = claim['service_start_date']
                 # Calculate days between dates
                date_diff = (claim['service_end_date'] - claim['service_start_date']).days

                # Handle negative or zero date differences
                if date_diff <= 0:
                    # If end date is before or equal to start date, just use start date
                    service_date = start_date
                else:
                    # Otherwise pick random day in range
                    service_date = start_date + timedelta(days=random.randint(0, date_diff))
                                
                claim_line = {
                    'line_id': line_id,
                    'claim_id': claim_id,
                    'line_number': line_num + 1,
                    'procedure_code': proc_code,
                    'procedure_description': proc_desc,
                    'diagnosis_pointer': '1' if claim['diagnosis_codes'] else None,
                    'service_date': service_date,
                    'units': units,
                    'unit_price': unit_price,
                    'line_total': line_total,
                    'allowed_amount': round(line_total * random.uniform(0.7, 0.9), 2) if claim['status'] == 'Paid' else None,
                    'paid_amount': round(line_total * random.uniform(0.7, 0.9), 2) if claim['status'] == 'Paid' else None
                }
                self.claim_lines.append(claim_line)
                line_id += 1
                
            # If claim total doesn't match lines, adjust one line to create discrepancy
            if claim['claim_id'] % 10 == 0 and abs(claim['claim_amount'] - calculated_total) < 0.01:
                # Find a line to adjust
                for line in self.claim_lines:
                    if line['claim_id'] == claim_id:
                        line['line_total'] = line['line_total'] * 1.05
                        break
                        
        return pd.DataFrame(self.claim_lines)
    
    def save_to_csv(self):
        """Save all data to CSV files"""
        output_dir = '../data'
        os.makedirs(output_dir, exist_ok=True)
        
        pd.DataFrame(self.patients).to_csv(f'{output_dir}/patients.csv', index=False)
        pd.DataFrame(self.providers).to_csv(f'{output_dir}/providers.csv', index=False)
        pd.DataFrame(self.claims).to_csv(f'{output_dir}/claims.csv', index=False)
        pd.DataFrame(self.claim_lines).to_csv(f'{output_dir}/claim_lines.csv', index=False)
        
        # Save reference data
        pd.DataFrame(self.diagnosis_codes, columns=['code', 'description', 'category', 'is_chronic'])\
            .to_csv(f'{output_dir}/diagnosis_codes.csv', index=False)
        pd.DataFrame(self.procedure_codes, columns=['code', 'description', 'typical_cost'])\
            .to_csv(f'{output_dir}/procedure_codes.csv', index=False)
        
        print(f"Data saved to {output_dir}/")
        
    def connect_to_mysql(self):
        """Connect to MySQL database"""
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',  
                password='Root1234*',  
                database='healthcare_qa'
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            return None
    
    def load_to_mysql(self):
        conn = self.connect_to_mysql()
        if not conn:
            print("Skipping MySQL load - continuing with CSV only")
            return
            
        cursor = conn.cursor()
        
        try:
            # Clear existing data
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE claim_lines")
            cursor.execute("TRUNCATE TABLE claims")
            cursor.execute("TRUNCATE TABLE patients")
            cursor.execute("TRUNCATE TABLE providers")
            cursor.execute("TRUNCATE TABLE diagnosis_codes")
            cursor.execute("TRUNCATE TABLE procedure_codes")
            
            
            # Convert DataFrames to lists and handle NaN values
            def clean_nan(value):
                """Convert NaN to None (which becomes NULL in MySQL)"""
                if pd.isna(value) or (isinstance(value, float) and np.isnan(value)):
                    return None
                return value
            
            # Insert patients (with NaN handling)
            print("Loading patients...")
            patients_df = pd.DataFrame(self.patients)
            for _, row in patients_df.iterrows():
                # Clean all values in the row
                cleaned_row = [clean_nan(val) for val in row]
                try:
                    cursor.execute("""
                        INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender, 
                                            ssn, address, city, state, zip_code, phone, email, 
                                            insurance_provider, insurance_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, cleaned_row)
                except mysql.connector.Error as err:
                    print(f"Error inserting patient {row['patient_id']}: {err}")
                    print(f"Row data: {row.to_dict()}")
                    raise
            
            # Insert providers (with NaN handling)
            print("Loading providers...")
            providers_df = pd.DataFrame(self.providers)
            for _, row in providers_df.iterrows():
                cleaned_row = [clean_nan(val) for val in row]
                try:
                    cursor.execute("""
                        INSERT INTO providers (provider_id, provider_name, provider_type, npi_number,
                                            tax_id, address, city, state, zip_code, phone, email,
                                            specialty, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, cleaned_row)
                except mysql.connector.Error as err:
                    print(f"Error inserting provider {row['provider_id']}: {err}")
                    print(f"Row data: {row.to_dict()}")
                    raise
            
            # Insert claims (with NaN handling)
            print("Loading claims...")
            claims_df = pd.DataFrame(self.claims)
            for _, row in claims_df.iterrows():
                cleaned_row = [clean_nan(val) for val in row]
                try:
                    cursor.execute("""
                        INSERT INTO claims (claim_id, claim_number, patient_id, provider_id, claim_type,
                                        service_start_date, service_end_date, submitted_date, received_date,
                                        processed_date, claim_amount, paid_amount, patient_responsibility,
                                        status, denial_reason, diagnosis_codes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, cleaned_row)
                except mysql.connector.Error as err:
                    print(f"Error inserting claim {row['claim_id']}: {err}")
                    print(f"Row data: {row.to_dict()}")
                    raise
            
            # Insert claim lines (with NaN handling)
            print("Loading claim lines...")
            claim_lines_df = pd.DataFrame(self.claim_lines)
            for _, row in claim_lines_df.iterrows():
                cleaned_row = [clean_nan(val) for val in row]
                try:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    cursor.execute("""
                        INSERT INTO claim_lines (line_id, claim_id, line_number, procedure_code,
                                            procedure_description, diagnosis_pointer, service_date,
                                            units, unit_price, line_total, allowed_amount, paid_amount)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, cleaned_row)
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                except mysql.connector.Error as err:
                    print(f"Error inserting claim line {row['line_id']}: {err}")
                    print(f"Row data: {row.to_dict()}")
                    raise
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.commit()
            print("✅ Data successfully loaded to MySQL!")
            
        except mysql.connector.Error as err:
            print(f"❌ Error loading data to MySQL: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def main():
    """Main function to generate and save test data"""
    print("=" * 60)
    print("HEALTHCARE TEST DATA GENERATOR")
    print("=" * 60)
    
    generator = HealthcareDataGenerator()
    
    # Generate data
    generator.generate_patients(50)
    generator.generate_providers(15)
    generator.generate_claims(100)
    generator.generate_claim_lines()
    
    # Save to CSV
    generator.save_to_csv()
    
    # Ask if user wants to load to MySQL
    response = input("\nDo you want to load data to MySQL? (y/n): ")
    if response.lower() == 'y':
        generator.load_to_mysql()
    
    print("\n" + "=" * 60)
    print("DATA GENERATION COMPLETE!")
    print(f"Patients: {len(generator.patients)}")
    print(f"Providers: {len(generator.providers)}")
    print(f"Claims: {len(generator.claims)}")
    print(f"Claim Lines: {len(generator.claim_lines)}")
    print("=" * 60)

if __name__ == "__main__":
    main()