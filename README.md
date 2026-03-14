# Healthcare Claims Data Quality Assurance Framework

##  Project Overview
This project demonstrates a comprehensive Data Quality Assurance framework for healthcare claims data, specifically designed for a Data QA Trainee role at Cedar Gate Technologies. It simulates real-world scenarios in healthcare data management, focusing on data validation, integrity checks, and automated quality reporting.

###  Key Features
- **Complete Healthcare Data Model**: Patients, Providers, Claims, and Claim Lines with referential integrity
- **Intentional Data Issues**: Strategically placed errors to demonstrate QA detection capabilities
- **30+ SQL Validation Queries**: Comprehensive data quality checks
- **Python Automation Framework**: Automated QA checks with report generation
- **Visual Analytics**: Data quality dashboards and visualizations
- **HTML/CSV Reports**: Professional, actionable reports



##  Technologies Used
- **Database**: MySQL (compatible with RedShift, MSSQL syntax)
- **Languages**: SQL, Python 3.8+
- **Python Libraries**: 
  - `mysql-connector-python` - Database connectivity
  - `pandas` - Data manipulation
  - `numpy` - Numerical operations
  - `matplotlib` / `seaborn` - Visualizations
  - `faker` - Test data generation
  - `tabulate` - Pretty printing

## 🔧 Setup Instructions

### Prerequisites
1. Install MySQL Community Server
2. Install Python 3.8 or higher
3. Install Git (optional)

### Step 1: Clone/Download Project
```bash
git clone <your-repo-url>
cd healthcare-data-qa-project

### Step 2: Install Python Dependencies
bash
pip install -r requirements.txt

### Step 3: Configure Database
Start MySQL server

Update database credentials in:

python/generate_test_data.py (line ~250)

python/data_qa_automation.py (line ~308)

### Step 4: Create Database Schema
bash
mysql -u root -p < sql/01_create_schema.sql

###Step 5: Generate and Load Test Data
bash
cd python
python generate_test_data.py
Follow the prompt to load data into MySQL.

###Step 6: Run QA Automation
bash
python data_qa_automation.py
