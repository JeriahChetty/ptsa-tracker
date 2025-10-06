import click
from flask import current_app
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User, Company, Measure, MeasureAssignment, AssignmentStep
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

@click.command('seed-data')
@click.option('--users', is_flag=True, help='Seed user data')
@click.option('--companies', is_flag=True, help='Seed company data')
@click.option('--measures', is_flag=True, help='Seed measure data')
@click.option('--assignments', is_flag=True, help='Seed measure assignments')
@click.option('--all', 'seed_all', is_flag=True, help='Seed all data')
@with_appcontext
def seed_data(users, companies, measures, assignments, seed_all):
    """Seed the database with sample data."""
    if seed_all or users:
        seed_users()
    if seed_all or companies:
        seed_companies()
    if seed_all or measures:
        seed_measures()
    if seed_all or assignments:
        seed_assignments()
    
    db.session.commit()
    click.echo('Database seeded successfully!')

def seed_users():
    click.echo('Seeding users...')
    # Admin user
    admin = User.query.filter_by(email="admin@ptsa.com").first()
    if not admin:
        admin = User(
            email="admin@ptsa.com",
            password_hash=generate_password_hash("Admin123!"),
            role="admin",
            is_active=True,
            name="Administrator"
        )
        db.session.add(admin)
        click.echo("Admin user created")
    else:
        click.echo("Admin user already exists")

def seed_companies():
    click.echo('Seeding companies...')
    companies = [
        dict(
            name="Acme Tooling",
            region="Gauteng",
            industry_category="Automotive",
            tech_resources="Injection moulds, press tools, EDM, CNC machining",
            human_resources="8 toolmakers, 3 apprentices, 5 CNC operators",
            membership="Member",
            contact_person="John Smith",
            phone="555-1234",
            email="contact@acmetooling.com",
            address="123 Industry Way"
        ),
        dict(
            name="Bravo Plastics",
            region="KwaZulu-Natal",
            industry_category="Plastics",
            tech_resources="Mould maintenance, CNC turning",
            human_resources="6 toolmakers, 2 apprentices",
            membership="Non-member",
            contact_person="Jane Doe",
            phone="555-5678",
            email="info@bravoplastics.com",
            address="456 Manufacturing Blvd"
        ),
        dict(
            name="Cobalt Engineering",
            region="Western Cape",
            industry_category="General Engineering",
            tech_resources="General fabrication, jigs & fixtures",
            human_resources="4 fitters, 2 welders",
            membership="Member",
            contact_person="Sam Johnson",
            phone="555-9012",
            email="hello@cobalteng.com",
            address="789 Engineering Road"
        ),
    ]
    
    for company_data in companies:
        company = Company.query.filter_by(name=company_data["name"]).first()
        if not company:
            company = Company(**company_data)
            db.session.add(company)
            click.echo(f"Company {company_data['name']} created")
        else:
            click.echo(f"Company {company_data['name']} already exists")

def seed_measures():
    click.echo('Seeding measures...')
    measures = [
        dict(
            title="5S Implementation",
            description="Roll out 5S across the machining area.",
            order=0
        ),
        dict(
            title="Preventive Maintenance Program",
            description="Establish and execute PM schedule for critical machines.",
            order=1
        ),
        dict(
            title="Incoming Quality Inspection",
            description="Set up incoming inspection for key purchased components.",
            order=2
        ),
    ]
    
    for measure_data in measures:
        measure = Measure.query.filter_by(title=measure_data["title"]).first()
        if not measure:
            measure = Measure(**measure_data)
            db.session.add(measure)
            click.echo(f"Measure {measure_data['title']} created")
        else:
            # Update the order field
            measure.order = measure_data["order"]
            db.session.add(measure)
            click.echo(f"Measure {measure_data['title']} updated")

def register_cli_commands(app):
    app.cli.add_command(seed_data)

def get_or_create(model, **kwargs):
    """Get or create a model instance based on filters"""
    defaults = kwargs.pop('defaults', {})
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**{**kwargs, **defaults})
        db.session.add(instance)
        return instance, True

# Removing duplicate seed_measures function
    click.echo('Seeding measures...')
    measures = [
        dict(
            title="5S Implementation",
            description="Roll out 5S across the machining area.",
            target="Sustain 5S score > 85% for 3 consecutive audits.",
            departments="Operations",
            responsible="Production Manager",
            participants="All operators",
            order=0
        ),
        dict(
            title="Preventive Maintenance Program",
            description="Establish and execute PM schedule for critical machines.",
            target="Zero critical unplanned downtime for 60 days.",
            departments="Maintenance",
            responsible="Maintenance Lead",
            participants="Maintenance team",
            order=1
        ),
        dict(
            title="Incoming Quality Inspection",
            description="Set up incoming inspection for key purchased components.",
            target="Incoming defect rate < 0.5% for 90 days.",
            departments="Quality",
            responsible="QA Supervisor",
            participants="QA Technicians, Stores",
            order=2
        ),
    ]
    
    for i, measure_data in enumerate(measures):
        measure, created = get_or_create(
            Measure, 
            title=measure_data["title"], 
            defaults={**measure_data, "created_at": datetime.now()}
        )
        
        # Add steps for this measure
        if created:
            seed_steps_for_measure(measure)
    
    click.echo('Measures seeded successfully')

def seed_steps_for_measure(measure):
    """Add steps for a specific measure based on its title"""
    step_map = {
        "5S Implementation": [
            "Define pilot area and ownership",
            "Sort (red-tag) unnecessary items",
            "Set in order with labels/shadow boards",
            "Shine: deep clean and fix abnormalities",
            "Standardize audit checklist",
            "Sustain: schedule weekly audits",
        ],
        "Preventive Maintenance Program": [
            "List critical equipment",
            "Define PM tasks & intervals",
            "Create PM calendar",
            "Train technicians",
            "Execute PM on schedule",
            "Review PM effectiveness monthly",
        ],
        "Incoming Quality Inspection": [
            "Identify key incoming parts",
            "Create acceptance criteria",
            "Setup inspection workstation",
            "Train inspectors",
            "Start inspection & log defects",
            "Weekly review with suppliers",
        ],
    }
    
    # Get steps for this measure type
    steps = step_map.get(measure.title, [])
    
    # Add steps with proper ordering
    for i, step_title in enumerate(steps):
        step = AssignmentStep(
            measure_id=measure.id,
            title=step_title,
            order=i
        )
        db.session.add(step)

def seed_assignments():
    click.echo('Seeding assignments...')
    
    # Get companies and measures
    companies = Company.query.all()
    measures = Measure.query.all()
    
    # Check if we have companies and measures
    if not companies or not measures:
        click.echo('Cannot seed assignments: companies or measures missing')
        return
    
    statuses = ['Not Started', 'In Progress', 'Completed', 'Delayed']
    urgencies = ['Low', 'Normal', 'High', 'Critical']
    
    for company in companies:
        for measure in measures:
            # Check if assignment already exists
            existing = MeasureAssignment.query.filter_by(
                company_id=company.id, 
                measure_id=measure.id
            ).first()
            
            if not existing:
                status = 'Not Started' if company.name == "Bravo Plastics" else 'In Progress'
                
                start_date = datetime.today().date() - timedelta(days=random.randint(1, 10))
                end_date = start_date + timedelta(days=random.randint(30, 90))
                
                assignment = MeasureAssignment(
                    company_id=company.id,
                    measure_id=measure.id,
                    status=status,
                    urgency=random.choice(urgencies),
                    start_date=start_date,
                    end_date=end_date,
                    due_at=datetime.combine(end_date, datetime.max.time()),
                    target=measure.target,
                    departments=measure.departments,
                    responsible=measure.responsible,
                    participants=measure.participants,
                    created_at=datetime.now()
                )
                db.session.add(assignment)
    
    click.echo('Measure assignments seeded successfully')

@click.command('send-benchmarking-reminders')
@with_appcontext
def send_benchmarking_reminders():
    """Send benchmarking reminder emails to companies that are due for updates."""
    from datetime import datetime, timedelta
    from flask import current_app, request
    from flask_mail import Message
    from app.extensions import mail
    from app.models import Company, Notification
    
    try:
        # Find companies that need benchmarking reminders
        now = datetime.utcnow()
        companies_due = Company.query.filter(
            Company.next_benchmarking_due <= now
        ).all()
        
        if not companies_due:
            print("No companies due for benchmarking reminders.")
            return
        
        sent_count = 0
        for company in companies_due:
            try:
                # Get the company's primary user email
                if not company.users:
                    print(f"No users found for company {company.name}, skipping...")
                    continue
                
                primary_user = company.users[0]  # Use first user as primary contact
                
                # Create notification in database
                notification = Notification(
                    company_id=company.id,
                    user_id=primary_user.id,
                    kind="benchmarking_reminder",
                    subject="Time to Update Your Company Performance Data",
                    body=f"Dear {company.name},\n\nIt's time to update your company's performance data. Please log in to your account and update your benchmarking information to help track your progress.\n\nThis reminder is sent every {company.benchmarking_reminder_months or 12} months.",
                    notify_at=now
                )
                db.session.add(notification)
                
                # Send email (note: we'll need to handle URL generation differently in CLI)
                msg = Message(
                    subject="PTSA Tracker - Performance Data Update Reminder",
                    recipients=[primary_user.email],
                    body=f"""Dear {company.name},

It's time to update your company's performance data in the PTSA Tracker system.

Please log in to your account and navigate to your Company Profile to update your benchmarking information. This helps us track your progress and provides valuable insights into your company's growth.

If you need assistance, please contact the PTSA support team.

Best regards,
PTSA Tracker System
"""
                )
                
                mail.send(msg)
                
                # Update the reminder timestamp and next due date
                company.last_benchmarking_reminder = now
                company.next_benchmarking_due = now + timedelta(days=365 * (company.benchmarking_reminder_months or 12) // 12)
                
                notification.email_sent_at = now
                sent_count += 1
                
                print(f"Sent benchmarking reminder to {company.name} ({primary_user.email})")
                
            except Exception as e:
                print(f"Failed to send reminder to {company.name}: {str(e)}")
                continue
        
        db.session.commit()
        print(f"Successfully sent {sent_count} benchmarking reminders.")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error sending benchmarking reminders: {str(e)}")
