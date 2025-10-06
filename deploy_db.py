#!/usr/bin/env python3
"""
Database deployment script for PTSA Tracker
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/deploy_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def deploy_database():
    """Deploy database with initial data"""
    try:
        logger.info("Importing application modules...")
        from app import create_app
        from app.extensions import db
        from app.models import (
            User, Company, Measure, MeasureStep,
            NotificationConfig
        )
        
        # Check if CompanyBenchmark exists
        CompanyBenchmark = None
        try:
            from app.models import CompanyBenchmark
            logger.info("CompanyBenchmark model found - benchmarks will be initialized")
        except ImportError:
            logger.warning("CompanyBenchmark model not found - benchmarks won't be initialized")
        
        logger.info("Creating application context...")
        app = create_app()
        os.makedirs('instance', exist_ok=True)
        
        with app.app_context():
            logger.info("🚀 Starting database deployment...")
            
            # Create all tables
            logger.info("📋 Creating database tables...")
            db.create_all()
            logger.info("✅ Database tables created successfully")
            
            # Create initial admin user if not exists
            admin_email = "admin@ptsa.co.za"
            admin = User.query.filter_by(email=admin_email).first()
            
            if not admin:
                logger.info(f"👤 Creating admin user: {admin_email}")
                admin = User(
                    email=admin_email,
                    password=generate_password_hash("admin123"),  # Change this password!
                    role="admin",
                    is_active=True
                )
                db.session.add(admin)
                logger.info("✅ Admin user created")
            else:
                logger.info("ℹ️  Admin user already exists")
            
            # Create notification config if not exists
            config = NotificationConfig.query.get(1)
            if not config:
                logger.info("📧 Creating notification configuration...")
                config = NotificationConfig(
                    id=1,
                    lead_days=7,
                    send_hour_utc=8,
                    send_minute_utc=0
                )
                db.session.add(config)
                logger.info("✅ Notification configuration created")
            else:
                logger.info("ℹ️  Notification configuration already exists")
            
            # Create sample company for testing (optional)
            sample_company = Company.query.filter_by(name="Sample Company").first()
            if not sample_company:
                logger.info("🏢 Creating sample company...")
                sample_company = Company(
                    name="Sample Company",
                    region="Gauteng",
                    industry_category="Manufacturing",
                    tech_resources="Basic machinery and tools",
                    human_resources="Skilled technicians and engineers",
                    membership="Member"
                )
                db.session.add(sample_company)
                db.session.flush()  # Get the ID
                
                # Create a company user for the sample company
                company_user = User(
                    email="company@sample.co.za",
                    password=generate_password_hash("company123"),  # Change this password!
                    role="company",
                    is_active=True,
                    company_id=sample_company.id
                )
                db.session.add(company_user)
                logger.info("✅ Sample company and user created")
            else:
                logger.info("ℹ️  Sample company already exists")
            
            # Create sample measures
            sample_measures = [
                {
                    "name": "Implement Quality Management System",
                    "measure_detail": "Establish and implement a comprehensive quality management system",
                    "target": "Achieve ISO 9001 certification",
                    "departments": "Quality, Production",
                    "responsible": "Quality Manager",
                    "participants": "All department heads"
                },
                {
                    "name": "Employee Skills Development",
                    "measure_detail": "Develop and implement employee training programs",
                    "target": "Train 80% of workforce in new technologies",
                    "departments": "HR, Production",
                    "responsible": "HR Manager",
                    "participants": "All employees"
                },
                {
                    "name": "Process Optimization",
                    "measure_detail": "Analyze and optimize manufacturing processes",
                    "target": "Reduce waste by 25%",
                    "departments": "Production, Engineering",
                    "responsible": "Production Manager",
                    "participants": "Engineers, Operators"
                }
            ]
            
            measures_created = 0
            for i, measure_data in enumerate(sample_measures):
                existing_measure = Measure.query.filter_by(name=measure_data["name"]).first()
                if not existing_measure:
                    measure = Measure(
                        order=i,
                        **measure_data
                    )
                    db.session.add(measure)
                    db.session.flush()
                    
                    # Add sample steps for each measure
                    sample_steps = [
                        "Plan and prepare implementation",
                        "Execute the planned activities",
                        "Monitor and measure progress",
                        "Review and take corrective action"
                    ]
                    
                    for step_idx, step_title in enumerate(sample_steps):
                        step = MeasureStep(
                            measure_id=measure.id,
                            title=step_title,
                            step=step_idx
                        )
                        db.session.add(step)
                    
                    measures_created += 1
                    logger.info(f"✅ Created measure: {measure.name}")
            
            # Create sample benchmarking data if model exists
            if CompanyBenchmark and sample_company:
                logger.info("📊 Creating sample benchmarking data...")
                # Create baseline (2021) benchmarking data
                if not CompanyBenchmark.query.filter_by(company_id=sample_company.id, data_year=2021).first():
                    baseline = CompanyBenchmark(
                        company_id=sample_company.id,
                        data_year=2021,
                        entered_by_id=admin.id,
                        entered_by_role="admin",
                        turnover="R 8,550,000.00",
                        tools_produced=6,
                        on_time_delivery="78%",
                        export_percentage="0%",
                        employees=42,
                        apprentices=0,
                        artisans=3,
                        engineers=0,
                        notes="Baseline data at program start"
                    )
                    db.session.add(baseline)
                
                # Create current (2023) benchmarking data
                if not CompanyBenchmark.query.filter_by(company_id=sample_company.id, data_year=2023).first():
                    current = CompanyBenchmark(
                        company_id=sample_company.id,
                        data_year=2023,
                        entered_by_id=admin.id,
                        entered_by_role="admin",
                        turnover="R 14,500,000.00",
                        tools_produced=15,
                        on_time_delivery="95%",
                        export_percentage="12%",
                        employees=52,
                        apprentices=8,
                        artisans=12,
                        engineers=2,
                        notes="Current performance data"
                    )
                    db.session.add(current)
                
                logger.info("✅ Sample benchmarking data created")
            
            # Commit all changes
            logger.info("💾 Saving all changes to database...")
            db.session.commit()
            logger.info("✅ Database deployment completed successfully!")
            
            # Print summary
            logger.info("\n📊 Deployment Summary:")
            logger.info(f"   • Users: {User.query.count()}")
            logger.info(f"   • Companies: {Company.query.count()}")
            logger.info(f"   • Measures: {Measure.query.count()}")
            logger.info(f"   • Measure Steps: {MeasureStep.query.count()}")
            
            logger.info("\n🔐 Default Login Credentials:")
            logger.info(f"   Admin: admin@ptsa.co.za / admin123")
            logger.info(f"   Company: company@sample.co.za / company123")
            logger.info("\n⚠️  IMPORTANT: Change these passwords after first login!")
    
    except Exception as e:
        logger.error(f"❌ Database deployment failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        logger.info("Starting database deployment")
        deploy_database()
        logger.info("Database deployment completed successfully")
    except Exception as e:
        logger.error(f"Database deployment failed: {str(e)}", exc_info=True)
        sys.exit(1)
