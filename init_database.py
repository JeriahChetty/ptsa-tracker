#!/usr/bin/env python3
"""
Database initialization script for PTSA Tracker.
This script will create a new database with all required tables and columns.
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def initialize_database():
    """Initialize the database with all required tables."""
    print("🚀 PTSA Tracker Database Initialization")
    print("=" * 40)
    
    try:
        from app import create_app
        from app.extensions import db
        from app.models import User, Company, Measure, MeasureStep, MeasureAssignment, AssignmentStep, CompanyBenchmark, Notification, NotificationConfig, AssistanceRequest
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            print("📊 Creating database tables...")
            
            # Create instance directory if it doesn't exist
            instance_dir = os.path.join(os.getcwd(), 'instance')
            if not os.path.exists(instance_dir):
                os.makedirs(instance_dir)
                print(f"  ✅ Created instance directory: {instance_dir}")
            
            # Create all tables
            db.create_all()
            print("  ✅ All database tables created successfully")
            
            # Now we need to add missing columns to existing tables
            print("🔧 Checking and adding missing columns...")
            
            # Get raw database connection for SQLite operations
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            try:
                # Check companies table columns
                cursor.execute("PRAGMA table_info(companies)")
                company_columns = [row[1] for row in cursor.fetchall()]
                print(f"  📋 Companies table columns: {company_columns}")
                
                # Add missing benchmarking columns if they don't exist
                missing_columns = []
                
                if 'benchmarking_reminder_months' not in company_columns:
                    cursor.execute("ALTER TABLE companies ADD COLUMN benchmarking_reminder_months INTEGER DEFAULT 12")
                    missing_columns.append('benchmarking_reminder_months')
                
                if 'last_benchmarking_reminder' not in company_columns:
                    cursor.execute("ALTER TABLE companies ADD COLUMN last_benchmarking_reminder DATETIME")
                    missing_columns.append('last_benchmarking_reminder')
                
                if 'next_benchmarking_due' not in company_columns:
                    cursor.execute("ALTER TABLE companies ADD COLUMN next_benchmarking_due DATETIME")
                    missing_columns.append('next_benchmarking_due')
                
                if missing_columns:
                    connection.commit()
                    print(f"  ✅ Added missing columns: {', '.join(missing_columns)}")
                else:
                    print("  ✅ All columns already present")
                
            except Exception as e:
                print(f"  ⚠️  Column addition error: {str(e)}")
                connection.rollback()
            finally:
                cursor.close()
                connection.close()
            
            # Check if admin user exists
            admin_user = User.query.filter_by(email='admin@example.com').first()
            if not admin_user:
                print("👤 Creating default admin user...")
                from werkzeug.security import generate_password_hash
                
                # Check User model structure first
                user_columns = [column.name for column in User.__table__.columns]
                print(f"  📋 User model columns: {user_columns}")
                
                # Create user with only the fields that exist
                user_data = {
                    'email': 'admin@example.com',
                    'role': 'admin'
                }
                
                # Add password field if it exists
                if 'password_hash' in user_columns:
                    user_data['password_hash'] = generate_password_hash("admin123")
                elif 'password' in user_columns:
                    user_data['password'] = generate_password_hash("admin123")
                
                admin_user = User(**user_data)
                db.session.add(admin_user)
                print("  ✅ Admin user created")
                print("  📧 Email: admin@example.com")
                print("  🔑 Password: admin123")
            else:
                print("👤 Admin user already exists")
            
            # Create sample companies if none exist
            if Company.query.count() == 0:
                print("🏢 Creating sample companies...")
                
                sample_companies = [
                    {
                        'name': 'Precision Tool Manufacturing Ltd.',
                        'region': 'North',
                        'industry_category': 'Tool & Die Manufacturing',
                        'tech_resources': 'Advanced',
                        'human_resources': '100-200',
                        'membership': 'Gold',
                        'phone': '+27 11 234-5678',
                        'benchmarking_reminder_months': 12
                    },
                    {
                        'name': 'Elite Automotive Components',
                        'region': 'Gauteng',
                        'industry_category': 'Automotive Parts',
                        'tech_resources': 'Intermediate',
                        'human_resources': '50-100',
                        'membership': 'Silver',
                        'phone': '+27 11 345-6789',
                        'benchmarking_reminder_months': 6
                    },
                    {
                        'name': 'Advanced Machining Solutions',
                        'region': 'Western Cape',
                        'industry_category': 'CNC Machining',
                        'tech_resources': 'Advanced',
                        'human_resources': '200-500',
                        'membership': 'Platinum',
                        'phone': '+27 21 456-7890',
                        'benchmarking_reminder_months': 12
                    },
                    {
                        'name': 'Industrial Fabricators SA',
                        'region': 'KwaZulu-Natal',
                        'industry_category': 'Metal Fabrication',
                        'tech_resources': 'Basic',
                        'human_resources': '20-50',
                        'membership': 'Bronze',
                        'phone': '+27 31 567-8901',
                        'benchmarking_reminder_months': 3
                    },
                    {
                        'name': 'Techno Plastics Manufacturing',
                        'region': 'Eastern Cape',
                        'industry_category': 'Injection Molding',
                        'tech_resources': 'Intermediate',
                        'human_resources': '100-200',
                        'membership': 'Gold',
                        'phone': '+27 41 678-9012',
                        'benchmarking_reminder_months': 12
                    },
                    {
                        'name': 'Quality Steel Works',
                        'region': 'Free State',
                        'industry_category': 'Steel Manufacturing',
                        'tech_resources': 'Advanced',
                        'human_resources': '500+',
                        'membership': 'Platinum',
                        'phone': '+27 51 789-0123',
                        'benchmarking_reminder_months': 6
                    }
                ]
                
                for company_data in sample_companies:
                    company = Company(**company_data)
                    db.session.add(company)
                
                print(f"  ✅ Created {len(sample_companies)} sample companies")
            
            # Create sample measures if none exist
            if Measure.query.count() == 0:
                print("📋 Creating sample measures...")
                
                sample_measures = [
                    {
                        'name': '5S Workplace Organization',
                        'measure_detail': 'Systematic approach to workplace organization and standardization using Sort, Set in Order, Shine, Standardize, and Sustain methodology',
                        'target': 'Achieve 95% 5S audit score within 6 months',
                        'departments': 'Production, Maintenance, Quality',
                        'responsible': 'Production Manager',
                        'participants': 'All shop floor employees',
                        'default_duration_days': 180,
                        'default_urgency': 2,
                        'steps': [
                            {'title': 'Sort (Seiri)', 'description': 'Remove unnecessary items from the workplace'},
                            {'title': 'Set in Order (Seiton)', 'description': 'Organize remaining items for easy access'},
                            {'title': 'Shine (Seiso)', 'description': 'Clean the workplace thoroughly'},
                            {'title': 'Standardize (Seiketsu)', 'description': 'Create standards for maintaining organization'},
                            {'title': 'Sustain (Shitsuke)', 'description': 'Maintain and improve the system continuously'}
                        ]
                    },
                    {
                        'name': 'Lean Manufacturing Implementation',
                        'measure_detail': 'Comprehensive lean manufacturing program to eliminate waste, improve flow, and increase productivity through value stream mapping and continuous improvement',
                        'target': 'Reduce lead time by 40% and increase productivity by 25%',
                        'departments': 'Production, Engineering, Planning',
                        'responsible': 'Operations Director',
                        'participants': 'Cross-functional teams',
                        'default_duration_days': 365,
                        'default_urgency': 3,
                        'steps': [
                            {'title': 'Current State Mapping', 'description': 'Map current value streams and identify waste'},
                            {'title': 'Future State Design', 'description': 'Design ideal future state with lean principles'},
                            {'title': 'Gap Analysis', 'description': 'Identify gaps between current and future state'},
                            {'title': 'Implementation Plan', 'description': 'Create detailed implementation roadmap'},
                            {'title': 'Pilot Implementation', 'description': 'Run pilot programs in selected areas'},
                            {'title': 'Full Rollout', 'description': 'Deploy lean practices across all operations'},
                            {'title': 'Sustain & Improve', 'description': 'Monitor progress and continuous improvement'}
                        ]
                    },
                    {
                        'name': 'Statistical Process Control (SPC)',
                        'measure_detail': 'Implementation of statistical methods to monitor and control manufacturing processes, ensuring consistent quality and early detection of process variations',
                        'target': 'Reduce process variation by 50% and achieve Cpk > 1.33',
                        'departments': 'Quality Assurance, Production',
                        'responsible': 'Quality Manager',
                        'participants': 'Operators, Quality technicians',
                        'default_duration_days': 120,
                        'default_urgency': 2,
                        'steps': [
                            {'title': 'Process Analysis', 'description': 'Identify critical processes for SPC implementation'},
                            {'title': 'Data Collection Setup', 'description': 'Establish measurement systems and data collection'},
                            {'title': 'Control Chart Creation', 'description': 'Develop appropriate control charts for each process'},
                            {'title': 'Training Program', 'description': 'Train operators on SPC principles and chart interpretation'},
                            {'title': 'Implementation', 'description': 'Deploy SPC across selected processes'},
                            {'title': 'Monitoring & Analysis', 'description': 'Regular review and analysis of control charts'}
                        ]
                    },
                    {
                        'name': 'Total Productive Maintenance (TPM)',
                        'measure_detail': 'Comprehensive maintenance strategy involving all employees to maximize equipment effectiveness through autonomous maintenance and planned maintenance activities',
                        'target': 'Achieve 90% Overall Equipment Effectiveness (OEE)',
                        'departments': 'Maintenance, Production, Engineering',
                        'responsible': 'Maintenance Manager',
                        'participants': 'Maintenance staff, Machine operators',
                        'default_duration_days': 270,
                        'default_urgency': 3,
                        'steps': [
                            {'title': 'Equipment Assessment', 'description': 'Evaluate current equipment condition and performance'},
                            {'title': 'Autonomous Maintenance', 'description': 'Train operators in basic maintenance tasks'},
                            {'title': 'Planned Maintenance', 'description': 'Develop preventive maintenance schedules'},
                            {'title': 'Predictive Maintenance', 'description': 'Implement condition monitoring technologies'},
                            {'title': 'Maintenance Standards', 'description': 'Create maintenance procedures and standards'},
                            {'title': 'Continuous Improvement', 'description': 'Regular assessment and improvement of maintenance practices'}
                        ]
                    },
                    {
                        'name': 'ISO 9001 Quality Management System',
                        'measure_detail': 'Implementation of ISO 9001:2015 quality management system to ensure consistent product quality and customer satisfaction through process-based approach',
                        'target': 'Achieve ISO 9001:2015 certification within 12 months',
                        'departments': 'All departments',
                        'responsible': 'Quality Director',
                        'participants': 'All employees',
                        'default_duration_days': 365,
                        'default_urgency': 2,
                        'steps': [
                            {'title': 'Gap Analysis', 'description': 'Assess current QMS against ISO 9001 requirements'},
                            {'title': 'Documentation', 'description': 'Develop quality manual and procedures'},
                            {'title': 'Process Mapping', 'description': 'Map all business processes and interactions'},
                            {'title': 'Training & Awareness', 'description': 'Train employees on QMS requirements'},
                            {'title': 'Implementation', 'description': 'Deploy QMS across all operations'},
                            {'title': 'Internal Audit', 'description': 'Conduct internal audits to verify compliance'},
                            {'title': 'Management Review', 'description': 'Review system effectiveness and improvement opportunities'},
                            {'title': 'Certification Audit', 'description': 'External certification body audit'}
                        ]
                    },
                    {
                        'name': 'Energy Efficiency Improvement',
                        'measure_detail': 'Comprehensive energy management program to reduce energy consumption, lower costs, and minimize environmental impact through efficient technologies and practices',
                        'target': 'Reduce energy consumption by 20% within 18 months',
                        'departments': 'Facilities, Production, Engineering',
                        'responsible': 'Facilities Manager',
                        'participants': 'Engineering team, Operators',
                        'default_duration_days': 540,
                        'default_urgency': 2,
                        'steps': [
                            {'title': 'Energy Audit', 'description': 'Comprehensive assessment of current energy usage'},
                            {'title': 'Baseline Establishment', 'description': 'Establish energy consumption baselines'},
                            {'title': 'Opportunity Identification', 'description': 'Identify energy saving opportunities'},
                            {'title': 'Cost-Benefit Analysis', 'description': 'Analyze ROI for energy efficiency projects'},
                            {'title': 'Implementation Planning', 'description': 'Develop implementation roadmap'},
                            {'title': 'Technology Upgrades', 'description': 'Install energy-efficient equipment and systems'},
                            {'title': 'Monitoring System', 'description': 'Implement energy monitoring and reporting'},
                            {'title': 'Continuous Monitoring', 'description': 'Regular monitoring and optimization'}
                        ]
                    },
                    {
                        'name': 'Digital Transformation Initiative',
                        'measure_detail': 'Strategic implementation of Industry 4.0 technologies including IoT sensors, data analytics, and automation to modernize manufacturing operations',
                        'target': 'Digitize 80% of manual processes and improve data visibility',
                        'departments': 'IT, Engineering, Production',
                        'responsible': 'CTO',
                        'participants': 'IT team, Engineers, Supervisors',
                        'default_duration_days': 720,
                        'default_urgency': 3,
                        'steps': [
                            {'title': 'Digital Readiness Assessment', 'description': 'Evaluate current digital maturity level'},
                            {'title': 'Technology Strategy', 'description': 'Develop digital transformation roadmap'},
                            {'title': 'Infrastructure Setup', 'description': 'Establish IT infrastructure and connectivity'},
                            {'title': 'IoT Implementation', 'description': 'Deploy sensors and data collection systems'},
                            {'title': 'Data Analytics Platform', 'description': 'Implement analytics and reporting tools'},
                            {'title': 'Process Automation', 'description': 'Automate manual processes where applicable'},
                            {'title': 'Training & Adoption', 'description': 'Train staff on new digital tools'},
                            {'title': 'Optimization', 'description': 'Continuous optimization based on data insights'}
                        ]
                    }
                ]
                
                for measure_data in sample_measures:
                    steps_data = measure_data.pop('steps')
                    measure = Measure(**measure_data)
                    db.session.add(measure)
                    db.session.flush()  # Get the measure ID
                    
                    # Add steps
                    for i, step_data in enumerate(steps_data, 1):
                        step = MeasureStep(
                            measure_id=measure.id,
                            step=i,
                            title=step_data['title'],
                            description=step_data['description']
                        )
                        db.session.add(step)
                
                print(f"  ✅ Created {len(sample_measures)} comprehensive measures with detailed steps")
                
            # Create some sample measure assignments
            companies = Company.query.all()
            measures = Measure.query.all()
            
            if companies and measures and MeasureAssignment.query.count() == 0:
                print("🔗 Creating sample measure assignments...")
                
                from datetime import datetime, timedelta
                import random
                
                # Assign some measures to companies
                assignments = [
                    # Precision Tool Manufacturing - focusing on quality and organization
                    {'company': companies[0], 'measure': measures[0], 'urgency': 2},  # 5S
                    {'company': companies[0], 'measure': measures[2], 'urgency': 3},  # SPC
                    {'company': companies[0], 'measure': measures[4], 'urgency': 2},  # ISO 9001
                    
                    # Elite Automotive Components - lean and TPM focus
                    {'company': companies[1], 'measure': measures[1], 'urgency': 3},  # Lean
                    {'company': companies[1], 'measure': measures[3], 'urgency': 2},  # TPM
                    
                    # Advanced Machining Solutions - digital transformation
                    {'company': companies[2], 'measure': measures[6], 'urgency': 3},  # Digital
                    {'company': companies[2], 'measure': measures[5], 'urgency': 2},  # Energy
                    
                    # Industrial Fabricators - starting with basics
                    {'company': companies[3], 'measure': measures[0], 'urgency': 1},  # 5S
                    
                    # Techno Plastics - quality focus
                    {'company': companies[4], 'measure': measures[4], 'urgency': 2},  # ISO 9001
                    {'company': companies[4], 'measure': measures[2], 'urgency': 2},  # SPC
                ]
                
                for assignment_data in assignments:
                    end_date = datetime.now() + timedelta(days=assignment_data['measure'].default_duration_days)
                    assignment = MeasureAssignment(
                        company_id=assignment_data['company'].id,
                        measure_id=assignment_data['measure'].id,
                        urgency=assignment_data['urgency'],
                        status='active',
                        assigned_date=datetime.now(),
                        end_date=end_date
                    )
                    db.session.add(assignment)
                
                print(f"  ✅ Created {len(assignments)} measure assignments")
                
            # Create some sample benchmarking data
            if companies and CompanyBenchmark.query.count() == 0:
                print("📊 Creating sample benchmarking data...")
                
                benchmark_data = [
                    # Precision Tool Manufacturing - 2022 & 2023 data
                    {'company_id': companies[0].id, 'data_year': 2022, 'entered_by_role': 'admin', 'turnover': 15000000, 'tools_produced': 2500, 'on_time_delivery': 92.5, 'export_percentage': 35.0, 'employees': 145, 'apprentices': 8, 'artisans': 65, 'master_artisans': 12, 'engineers': 18},
                    {'company_id': companies[0].id, 'data_year': 2023, 'entered_by_role': 'admin', 'turnover': 16800000, 'tools_produced': 2750, 'on_time_delivery': 94.2, 'export_percentage': 38.5, 'employees': 152, 'apprentices': 10, 'artisans': 68, 'master_artisans': 14, 'engineers': 20},
                    
                    # Elite Automotive Components
                    {'company_id': companies[1].id, 'data_year': 2022, 'entered_by_role': 'admin', 'turnover': 8500000, 'tools_produced': 15000, 'on_time_delivery': 88.3, 'export_percentage': 15.0, 'employees': 78, 'apprentices': 4, 'artisans': 42, 'master_artisans': 8, 'engineers': 12},
                    {'company_id': companies[1].id, 'data_year': 2023, 'entered_by_role': 'admin', 'turnover': 9200000, 'tools_produced': 16200, 'on_time_delivery': 90.7, 'export_percentage': 18.2, 'employees': 82, 'apprentices': 5, 'artisans': 44, 'master_artisans': 9, 'engineers': 14},
                    
                    # Advanced Machining Solutions
                    {'company_id': companies[2].id, 'data_year': 2022, 'entered_by_role': 'admin', 'turnover': 45000000, 'tools_produced': 8500, 'on_time_delivery': 96.1, 'export_percentage': 65.0, 'employees': 385, 'apprentices': 22, 'artisans': 185, 'master_artisans': 35, 'engineers': 58},
                    {'company_id': companies[2].id, 'data_year': 2023, 'entered_by_role': 'admin', 'turnover': 48500000, 'tools_produced': 9100, 'on_time_delivery': 97.2, 'export_percentage': 68.5, 'employees': 398, 'apprentices': 25, 'artisans': 190, 'master_artisans': 38, 'engineers': 62},
                ]
                
                for data in benchmark_data:
                    benchmark = CompanyBenchmark(**data)
                    db.session.add(benchmark)
                
                print(f"  ✅ Created {len(benchmark_data)} benchmarking records")
            
            # Commit all changes
            db.session.commit()
            print("💾 All changes committed to database")
            
            # Verify database structure
            print("\n🔍 Verifying database structure...")
            
            # Check tables
            tables = [
                ('users', User.query.count()),
                ('companies', Company.query.count()),
                ('measures', Measure.query.count()),
                ('measure_steps', MeasureStep.query.count()),
                ('measure_assignments', MeasureAssignment.query.count()),
                ('company_benchmark', CompanyBenchmark.query.count()),
            ]
            
            for table_name, count in tables:
                print(f"  ✅ {table_name}: {count} records")
            
            print("\n🎉 Database initialization completed successfully!")
            print("\n📊 Sample Data Overview:")
            print("  • 6 realistic manufacturing companies from different regions")
            print("  • 7 comprehensive improvement measures (5S, Lean, SPC, TPM, ISO 9001, Energy, Digital)")
            print("  • 40+ detailed implementation steps across all measures")
            print("  • 10 active measure assignments to companies")
            print("  • 6 benchmarking records showing 2-year performance trends")
            print("\nNext steps:")
            print("1. Start the application: flask run")
            print("2. Login with admin@example.com / admin123")
            print("3. Explore the realistic sample data and new features")
            print("4. Test drag-and-drop reordering on the Measures page")
            print("5. View benchmarking history and performance charts")
            
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure you have all required packages installed:")
        print("pip install flask flask-login flask-mail sqlalchemy")
        return False
    except Exception as e:
        print(f"❌ Initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main initialization function."""
    success = initialize_database()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())