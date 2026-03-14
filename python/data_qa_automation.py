"""
Data Quality Assurance Automation Framework
Runs automated QA checks on healthcare claims data and generates reports
"""

import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate

class DataQAAutomation:
    def __init__(self, db_config, report_dir='../reports'):
        """
        Initialize QA Automation with database connection
        
        Args:
            db_config: Dictionary with database connection parameters
            report_dir: Directory to save reports
        """
        self.db_config = db_config
        self.report_dir = report_dir
        self.connection = None
        self.results = {}
        self.issue_summary = []
        
        # Create report directory if it doesn't exist
        os.makedirs(report_dir, exist_ok=True)
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            print("✓ Connected to database successfully")
            return True
        except mysql.connector.Error as err:
            print(f"✗ Database connection failed: {err}")
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ Database connection closed")
            
    def run_query(self, query, query_name):
        """
        Execute a query and return results as DataFrame
        
        Args:
            query: SQL query to execute
            query_name: Name of the query for tracking
        """
        try:
            df = pd.read_sql(query, self.connection)
            self.results[query_name] = df
            
            # Track issues found
            if 'issue_count' in df.columns and len(df) > 0:
                total_issues = df['issue_count'].sum() if 'issue_count' in df.columns else len(df)
                if total_issues > 0:
                    self.issue_summary.append({
                        'check_name': query_name,
                        'issue_count': total_issues,
                        'severity': df['severity'].iloc[0] if 'severity' in df.columns else 'Unknown'
                    })
            
            print(f"  ✓ {query_name}: Found {len(df)} issues")
            return df
        except Exception as e:
            print(f"  ✗ {query_name} failed: {e}")
            return None
            
    def run_all_qa_checks(self):
        """Run all predefined QA checks"""
        print("\n" + "=" * 60)
        print("RUNNING DATA QUALITY CHECKS")
        print("=" * 60)
        
        # Load all QA queries
        with open('../sql/03_qa_validation_queries.sql', 'r') as f:
            queries = f.read().split(';')
            
        # Run each query
        for i, query in enumerate(queries):
            if query.strip() and 'SELECT' in query.upper():
                # Extract check name from query
                lines = query.strip().split('\n')
                check_name = f"Check_{i+1}"
                for line in lines:
                    if "SELECT" in line and "'" in line:
                        parts = line.split("'")
                        if len(parts) > 1:
                            check_name = parts[1]
                            break
                            
                self.run_query(query, check_name)
                
        # Run custom advanced checks
        self.run_advanced_checks()
        
    def run_advanced_checks(self):
        """Run additional advanced QA checks"""
        print("\n" + "-" * 40)
        print("Running Advanced Analytics...")
        print("-" * 40)
        
        cursor = self.connection.cursor()
        
        # Check 1: Temporal patterns (claims by hour/day)
        query = """
        SELECT 
            HOUR(created_date) as hour_of_day,
            DAYOFWEEK(created_date) as day_of_week,
            COUNT(*) as claim_count
        FROM claims
        GROUP BY hour_of_day, day_of_week
        ORDER BY day_of_week, hour_of_day
        """
        self.results['Temporal Patterns'] = pd.read_sql(query, self.connection)
        
        # Check 2: Provider billing patterns
        query = """
        SELECT 
            p.provider_name,
            p.provider_type,
            COUNT(c.claim_id) as claim_count,
            AVG(c.claim_amount) as avg_claim,
            STDDEV(c.claim_amount) as std_dev_claim,
            MIN(c.claim_amount) as min_claim,
            MAX(c.claim_amount) as max_claim
        FROM providers p
        LEFT JOIN claims c ON p.provider_id = c.provider_id
        GROUP BY p.provider_id
        HAVING claim_count > 0
        ORDER BY avg_claim DESC
        """
        self.results['Provider Patterns'] = pd.read_sql(query, self.connection)
        
        # Check 3: Patient history analysis
        query = """
        SELECT 
            p.patient_id,
            p.first_name,
            p.last_name,
            COUNT(c.claim_id) as total_claims,
            SUM(c.claim_amount) as total_billed,
            AVG(c.claim_amount) as avg_claim,
            DATEDIFF(MAX(c.service_start_date), MIN(c.service_start_date)) as active_days
        FROM patients p
        JOIN claims c ON p.patient_id = c.patient_id
        GROUP BY p.patient_id
        ORDER BY total_billed DESC
        LIMIT 20
        """
        self.results['Top Patients'] = pd.read_sql(query, self.connection)
        
    def generate_summary_statistics(self):
        """Generate summary statistics about the data"""
        print("\n" + "=" * 60)
        print("GENERATING SUMMARY STATISTICS")
        print("=" * 60)
        
        stats = {}
        
        # Get table counts
        tables = ['patients', 'providers', 'claims', 'claim_lines']
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            df = pd.read_sql(query, self.connection)
            stats[f'{table}_count'] = df['count'].iloc[0]
            
        # Get date ranges
        query = "SELECT MIN(service_start_date) as min_date, MAX(service_start_date) as max_date FROM claims"
        df = pd.read_sql(query, self.connection)
        stats['min_claim_date'] = df['min_date'].iloc[0]
        stats['max_claim_date'] = df['max_date'].iloc[0]
        
        # Financial summary
        query = """
        SELECT 
            SUM(claim_amount) as total_billed,
            SUM(paid_amount) as total_paid,
            AVG(claim_amount) as avg_claim,
            COUNT(CASE WHEN status = 'Denied' THEN 1 END) as denied_count,
            COUNT(CASE WHEN status = 'Paid' THEN 1 END) as paid_count
        FROM claims
        """
        df = pd.read_sql(query, self.connection)
        stats.update(df.iloc[0].to_dict())
        
        # Quality score
        total_issues = sum([item['issue_count'] for item in self.issue_summary])
        total_records = stats['claims_count']
        if total_records > 0:
            quality_score = max(0, 100 - (total_issues / total_records * 100))
        else:
            quality_score = 0
            
        stats['total_issues'] = total_issues
        stats['quality_score'] = round(quality_score, 2)
        
        self.results['Summary Statistics'] = pd.DataFrame([stats])
        return stats
        
    def create_visualizations(self):
        """Create visualizations of data quality metrics"""
        print("\n" + "=" * 60)
        print("CREATING VISUALIZATIONS")
        print("=" * 60)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # 1. Issues by Severity
        if self.issue_summary:
            df_issues = pd.DataFrame(self.issue_summary)
            severity_order = ['Critical', 'High', 'Medium', 'Low']
            df_issues['severity'] = pd.Categorical(df_issues['severity'], categories=severity_order, ordered=True)
            severity_counts = df_issues.groupby('severity')['issue_count'].sum().reset_index()
            
            plt.figure(figsize=(10, 6))
            colors = {'Critical': 'red', 'High': 'orange', 'Medium': 'yellow', 'Low': 'blue'}
            bars = plt.bar(severity_counts['severity'], severity_counts['issue_count'], 
                          color=[colors.get(s, 'gray') for s in severity_counts['severity']])
            plt.title('Data Quality Issues by Severity', fontsize=16, fontweight='bold')
            plt.xlabel('Severity Level')
            plt.ylabel('Number of Issues')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
                        
            plt.tight_layout()
            plt.savefig(f'{self.report_dir}/issues_by_severity.png', dpi=100, bbox_inches='tight')
            plt.close()
            
        # 2. Claims Status Distribution
        query = "SELECT status, COUNT(*) as count FROM claims GROUP BY status"
        df_status = pd.read_sql(query, self.connection)
        
        plt.figure(figsize=(10, 6))
        colors = plt.cm.Paired(np.arange(len(df_status)))
        plt.pie(df_status['count'], labels=df_status['status'], autopct='%1.1f%%', colors=colors)
        plt.title('Claims Status Distribution', fontsize=16, fontweight='bold')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(f'{self.report_dir}/claims_status.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        # 3. Monthly Claim Volume
        query = """
        SELECT 
            DATE_FORMAT(service_start_date, '%Y-%m') as month,
            COUNT(*) as claim_count,
            SUM(claim_amount) as total_amount
        FROM claims
        GROUP BY DATE_FORMAT(service_start_date, '%Y-%m')
        ORDER BY month
        """
        df_monthly = pd.read_sql(query, self.connection)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        ax1.bar(df_monthly['month'], df_monthly['claim_count'], color='skyblue')
        ax1.set_title('Monthly Claim Volume', fontsize=14)
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Number of Claims')
        ax1.tick_params(axis='x', rotation=45)
        
        ax2.bar(df_monthly['month'], df_monthly['total_amount'], color='lightcoral')
        ax2.set_title('Monthly Claim Amount ($)', fontsize=14)
        ax2.set_xlabel('Month')
        ax2.set_ylabel('Total Amount ($)')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{self.report_dir}/monthly_trends.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Visualizations saved to {self.report_dir}/")
        
    def generate_html_report(self):
        """Generate comprehensive HTML report"""
        print("\n" + "=" * 60)
        print("GENERATING HTML REPORT")
        print("=" * 60)
        
        stats = self.results.get('Summary Statistics', pd.DataFrame()).to_dict('records')
        stats = stats[0] if stats else {}
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Healthcare Data Quality Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .critical {{ background-color: #ffebee; border-left: 5px solid #c62828; padding: 10px; margin: 10px 0; }}
                .high {{ background-color: #fff3e0; border-left: 5px solid #ef6c00; padding: 10px; margin: 10px 0; }}
                .medium {{ background-color: #fff9c4; border-left: 5px solid #fbc02d; padding: 10px; margin: 10px 0; }}
                .low {{ background-color: #e8f5e8; border-left: 5px solid #2e7d32; padding: 10px; margin: 10px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #2c3e50; color: white; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .metric {{ display: inline-block; width: 200px; margin: 10px; padding: 15px; background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .metric-label {{ color: #7f8c8d; }}
                .quality-score {{ font-size: 48px; font-weight: bold; color: #27ae60; }}
                img {{ max-width: 100%; height: auto; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Healthcare Claims Data Quality Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <div style="text-align: center;">
                    <div class="metric">
                        <div class="metric-value">{stats.get('claims_count', 0)}</div>
                        <div class="metric-label">Total Claims</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{stats.get('patients_count', 0)}</div>
                        <div class="metric-label">Total Patients</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${stats.get('total_billed', 0):,.2f}</div>
                        <div class="metric-label">Total Billed</div>
                    </div>
                    <div class="metric">
                        <div class="quality-score">{stats.get('quality_score', 0)}%</div>
                        <div class="metric-label">Data Quality Score</div>
                    </div>
                </div>
            </div>
            
            <div class="summary">
                <h2>Critical Issues Found</h2>
        """
        
        # Add critical issues
        critical_issues = [issue for issue in self.issue_summary if issue.get('severity') == 'Critical']
        if critical_issues:
            for issue in critical_issues:
                html += f"""
                <div class="critical">
                    <h3>{issue['check_name']}</h3>
                    <p><strong>Issue Count:</strong> {issue['issue_count']}</p>
                    <p><strong>Severity:</strong> Critical</p>
                    <p><strong>Action Required:</strong> Immediate investigation required</p>
                </div>
                """
        else:
            html += "<p>No critical issues found.</p>"
            
        # Add high severity issues
        high_issues = [issue for issue in self.issue_summary if issue.get('severity') == 'High']
        if high_issues:
            html += "<h2>High Severity Issues</h2>"
            for issue in high_issues:
                html += f"""
                <div class="high">
                    <h3>{issue['check_name']}</h3>
                    <p><strong>Issue Count:</strong> {issue['issue_count']}</p>
                    <p><strong>Severity:</strong> High</p>
                </div>
                """
                
        html += """
            </div>
            
            <div class="summary">
                <h2>Data Quality Visualizations</h2>
                <div style="display: flex; flex-wrap: wrap; justify-content: center;">
        """
        
        # Add images
        images = ['issues_by_severity.png', 'claims_status.png', 'monthly_trends.png']
        for img in images:
            img_path = f'{self.report_dir}/{img}'
            if os.path.exists(img_path):
                html += f'<div style="margin: 10px;"><img src="{img}" alt="{img}" style="max-width: 500px;"></div>'
                
        html += """
                </div>
            </div>
            
            <div class="summary">
                <h2>Detailed Issue List</h2>
                <table>
                    <tr>
                        <th>Check Name</th>
                        <th>Issue Count</th>
                        <th>Severity</th>
                    </tr>
        """
        
        for issue in self.issue_summary:
            html += f"""
                    <tr>
                        <td>{issue['check_name']}</td>
                        <td>{issue['issue_count']}</td>
                        <td>{issue['severity']}</td>
                    </tr>
            """
            
        html += """
                </table>
            </div>
            
            <div class="summary">
                <h2>Recommendations</h2>
                <ul>
        """
        
        # Generate recommendations based on issues
        if any(issue['severity'] == 'Critical' for issue in self.issue_summary):
            html += "<li>⚠️ Critical issues found - Stop data processing until resolved</li>"
        if any('Orphaned' in issue['check_name'] for issue in self.issue_summary):
            html += "<li>🔗 Fix referential integrity issues in claims data</li>"
        if any('Duplicate' in issue['check_name'] for issue in self.issue_summary):
            html += "<li>📋 Remove duplicate records from the database</li>"
        if any('Future' in issue['check_name'] for issue in self.issue_summary):
            html += "<li>📅 Review and correct future-dated transactions</li>"
            
        html += """
                </ul>
            </div>
            
            <div class="summary">
                <p><em>This report was automatically generated by the Data QA Automation Framework.</em></p>
            </div>
        </body>
        </html>
        """
        
        # Save HTML report
        report_path = f'{self.report_dir}/qa_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(report_path, 'w', encoding="utf-8") as f:
            f.write(html)
            
        print(f"✓ HTML report saved to {report_path}")
        return report_path
        
    def generate_csv_report(self):
        """Generate CSV reports for each check"""
        csv_dir = f'{self.report_dir}/csv_reports'
        os.makedirs(csv_dir, exist_ok=True)
        
        for name, df in self.results.items():
            if df is not None and not df.empty:
                filename = f"{csv_dir}/{name.replace(' ', '_').lower()}.csv"
                df.to_csv(filename, index=False)
                
        print(f"✓ CSV reports saved to {csv_dir}/")
        
    def send_email_report(self, recipients, smtp_config):
        """Send report via email"""
        # This is optional - implement if you want email notifications
        pass
        
    def run_complete_qa(self):
        """Run complete QA process"""
        print("\n" + "=" * 60)
        print("HEALTHCARE DATA QUALITY AUTOMATION FRAMEWORK")
        print("=" * 60)
        
        if not self.connect():
            return False
            
        try:
            # Run all QA checks
            self.run_all_qa_checks()
            
            # Generate statistics
            stats = self.generate_summary_statistics()
            
            # Create visualizations
            self.create_visualizations()
            
            # Generate reports
            self.generate_csv_report()
            html_report = self.generate_html_report()
            
            # Print summary
            print("\n" + "=" * 60)
            print("QA PROCESS COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"Total Issues Found: {stats.get('total_issues', 0)}")
            print(f"Data Quality Score: {stats.get('quality_score', 0)}%")
            print(f"Reports saved to: {self.report_dir}/")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error during QA process: {e}")
            return False
        finally:
            self.disconnect()

def main():
    """Main function to run QA automation"""
    
    # Database configuration (update with your credentials)
    db_config = {
        'host': 'localhost',
        'user': 'root',  
        'password': 'Root1234*',  
        'database': 'healthcare_qa'
    }
    
    # Create QA automation instance
    qa = DataQAAutomation(db_config, report_dir='../reports')
    
    # Run complete QA process
    success = qa.run_complete_qa()
    
    if success:
        print("\n✓ QA process completed. Check the reports folder for detailed results.")
    else:
        print("\n✗ QA process failed. Please check the errors above.")

if __name__ == "__main__":
    main()