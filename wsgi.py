#!/usr/bin/env python3
"""
WSGI entry point for PTSA Tracker
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment to production
os.environ.setdefault('FLASK_ENV', 'production')

# Import the Flask application factory
from app import create_app
from app.extensions import db

# Create the Flask application instance
app = create_app('production')

# Initialize database on startup
with app.app_context():
    try:
        # First, run migrations
        from flask_migrate import upgrade as flask_upgrade
        import os
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        try:
            logger.info(f"Running migrations from: {migrations_dir}")
            flask_upgrade(directory=migrations_dir)
            logger.info("✓ Database migrations applied")
        except Exception as migrate_error:
            logger.error(f"Migration error: {migrate_error}")
            # Don't continue if migrations fail
            raise
            
        # Verify critical schema changes
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        
        # Check if measure_assignments table exists
        if 'measure_assignments' not in inspector.get_table_names():
            logger.error("❌ 'measure_assignments' table does not exist")
            raise Exception("Database schema is incomplete. Please check migrations.")
            
        # Check if deleted_at column exists
        columns = [col['name'] for col in inspector.get_columns('measure_assignments')]
        if 'deleted_at' not in columns:
            logger.error("❌ 'deleted_at' column is missing from measure_assignments table")
            raise Exception("Database schema is out of date. Please check migrations.")
        
        # Ensure order column exists (fallback for migration issues)
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('measure_assignments')]
            if 'order' not in columns:
                logger.warning("⚠️  'order' column missing from measure_assignments, adding it now...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE measure_assignments ADD COLUMN \"order\" INTEGER DEFAULT 0"))
                    conn.commit()
                logger.info("✓ Added 'order' column to measure_assignments")
            else:
                logger.info("✓ 'order' column exists in measure_assignments")
        except Exception as col_error:
            logger.error(f"Error checking/adding order column: {col_error}")
        
        # Backfill missing dates for existing assignments
        try:
            from app.models import MeasureAssignment
            from datetime import timedelta
            from sqlalchemy import or_
            
            assignments_without_dates = MeasureAssignment.query.filter(
                or_(MeasureAssignment.start_date == None, MeasureAssignment.end_date == None)
            ).all()
            
            if assignments_without_dates:
                logger.info(f"⚠️  Found {len(assignments_without_dates)} assignments with missing dates, backfilling...")
                updated_count = 0
                for assignment in assignments_without_dates:
                    updated = False
                    if not assignment.start_date:
                        assignment.start_date = assignment.created_at.date() if assignment.created_at else datetime.utcnow().date()
                        logger.info(f"  - Assignment {assignment.id}: Set start_date to {assignment.start_date}")
                        updated = True
                    if not assignment.end_date:
                        base_date = assignment.start_date if assignment.start_date else datetime.utcnow().date()
                        assignment.end_date = base_date + timedelta(days=30)
                        logger.info(f"  - Assignment {assignment.id}: Set end_date to {assignment.end_date}")
                        updated = True
                    if not assignment.due_at and assignment.end_date:
                        try:
                            assignment.due_at = datetime.combine(assignment.end_date, datetime.max.time())
                            logger.info(f"  - Assignment {assignment.id}: Set due_at to {assignment.due_at}")
                            updated = True
                        except Exception as e:
                            logger.warning(f"  - Assignment {assignment.id}: Could not set due_at: {e}")
                    if updated:
                        updated_count += 1
                
                db.session.commit()
                logger.info(f"✓ Successfully backfilled dates for {updated_count} assignments")
            else:
                logger.info("✓ All assignments already have complete dates")
        except Exception as backfill_error:
            logger.error(f"❌ Error backfilling assignment dates: {backfill_error}", exc_info=True)
            db.session.rollback()
        
        # Backfill missing steps for existing assignments
        try:
            from app.models import MeasureAssignment, MeasureStep, AssignmentStep
            
            all_assignments = MeasureAssignment.query.all()
            assignments_without_steps = [a for a in all_assignments if len(a.steps) == 0]
            
            if assignments_without_steps:
                logger.info(f"⚠️  Found {len(assignments_without_steps)} assignments without steps, backfilling...")
                updated_count = 0
                for assignment in assignments_without_steps:
                    # Get default steps from the measure
                    default_steps = MeasureStep.query.filter_by(
                        measure_id=assignment.measure_id
                    ).order_by(MeasureStep.step.asc()).all()
                    
                    if default_steps:
                        logger.info(f"  - Assignment {assignment.id}: Copying {len(default_steps)} steps from measure {assignment.measure_id}")
                        for idx, measure_step in enumerate(default_steps):
                            assignment_step = AssignmentStep(
                                assignment_id=assignment.id,
                                title=measure_step.title,
                                step=idx,
                                order_index=idx,
                                is_completed=False
                            )
                            db.session.add(assignment_step)
                        updated_count += 1
                    else:
                        logger.info(f"  - Assignment {assignment.id}: No default steps found on measure {assignment.measure_id}")
                
                db.session.commit()
                logger.info(f"✓ Successfully backfilled steps for {updated_count} assignments")
            else:
                logger.info("✓ All assignments already have steps")
        except Exception as backfill_steps_error:
            logger.error(f"❌ Error backfilling assignment steps: {backfill_steps_error}", exc_info=True)
            db.session.rollback()
        
        # Clean up company-specific details that were incorrectly copied from other companies
        # This is a ONE-TIME cleanup for existing assignments created before the fix
        try:
            from app.models import MeasureAssignment, Measure, Company
            
            # Get all assignments where company-specific fields match the measure template
            # (indicating they were copied instead of being company-specific)
            assignments_to_clean = []
            for assignment in MeasureAssignment.query.all():
                measure = assignment.measure
                # If assignment has same responsible/participants/departments as the measure template,
                # it was likely copied and should be cleared for the company to fill in their own
                if (assignment.responsible and assignment.responsible == measure.responsible) or \
                   (assignment.participants and assignment.participants == measure.participants) or \
                   (assignment.departments and assignment.departments == measure.departments):
                    assignments_to_clean.append(assignment)
            
            if assignments_to_clean:
                logger.info(f"⚠️  Found {len(assignments_to_clean)} assignments with copied company-specific details, cleaning...")
                for assignment in assignments_to_clean:
                    logger.info(f"  - Assignment {assignment.id} (Company: {assignment.company_id}, Measure: {assignment.measure_id})")
                    assignment.responsible = None
                    assignment.participants = None
                    assignment.departments = None
                db.session.commit()
                logger.info(f"✓ Successfully cleaned {len(assignments_to_clean)} assignments - admins must now fill in company-specific details")
            else:
                logger.info("✓ No assignments found with incorrectly copied company details")
        except Exception as cleanup_error:
            logger.error(f"❌ Error cleaning up assignment company details: {cleanup_error}", exc_info=True)
            db.session.rollback()
        
        # Create default admin if needed
        from app.models import User
        from werkzeug.security import generate_password_hash
        
        # Create default admin user if none exists
        admin = User.query.filter_by(email='info@ptsa.co.za').first()
        if not admin:
            admin = User(
                email='info@ptsa.co.za',
                password=generate_password_hash('info123'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("✓ Default admin user created: info@ptsa.co.za")
        else:
            logger.info(f"✓ Admin user exists: {admin.email}")
            
    except Exception as e:
        logger.error(f"✗ Database initialization error: {e}")
        # Don't crash - let the app try to run anyway

# Make sure the app is available for gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

