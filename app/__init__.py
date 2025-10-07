# app/__init__.py
from datetime import datetime, timedelta
from email.message import EmailMessage
import smtplib
import logging
import os

from flask import Flask, redirect, url_for, render_template, request, flash, session
from werkzeug.routing import BuildError
from flask_login import current_user, LoginManager
from flask_migrate import Migrate

from app.extensions import db, migrate, mail
from app.middleware import setup_session_protection


# Initialize extensions globally
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name="production"):
    app = Flask(__name__)
    
    # Configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Import config classes
    from app.config import config
    app.config.from_object(config.get(config_name, config['development']))
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Add template functions
    @app.template_global()
    def safe_url_for(endpoint, **values):
        """Safe URL generation that handles missing routes gracefully"""
        try:
            from flask import url_for
            return url_for(endpoint, **values)
        except Exception:
            # Fallback to a safe default
            if endpoint == 'index':
                return '/'
            return '#'
    
    @app.template_global()
    def status_class(status):
        status_map = {
            'Not Started': 'secondary',
            'In Progress': 'primary',
            'Completed': 'success',
            'Needs Assistance': 'danger',
            'On Hold': 'warning'
        }
        return status_map.get(status, 'secondary')
    
    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.company_routes import company_bp
    from app.routes.main_routes import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(main_bp)
    
    # Register health check blueprint
    from health_check import health_bp
    app.register_blueprint(health_bp)
    
    return app


def register_cli(app: Flask) -> None:
    """Attach custom Flask CLI commands."""
    import click
    from werkzeug.security import generate_password_hash

    @click.option("--email", default="admin@ptsa.com")
    @click.option("--password", default="Admin123!")
    @app.cli.command("seed-admin")
    def seed_admin(email, password):
        """Create an initial admin user if one doesn't exist."""
        from app.models import User
        with app.app_context():
            existing = User.query.filter_by(email=email).first()
            if existing:
                click.echo(f"Admin already exists: {email}")
                return
            admin = User(
                email=email,
                password=generate_password_hash(password),
                role="admin",
                is_active=True,
                company_id=None,
            )
            db.session.add(admin)
            db.session.commit()
            click.echo(f"Created admin: {email}")

    # Put @click.option ABOVE @app.cli.command so options are recognized
    @click.option("--days", type=int, default=None,
                  help="Override lead days (defaults to DB setting).")
    @click.option("--dry-run", is_flag=True,
                  help="Print actions; do not write to DB or send email.")
    @click.option("--no-email", is_flag=True,
                  help="Create notifications only; do not send emails.")
    @click.option("--ignore-config-time", is_flag=True,
                  help="Ignore configured send time (send immediately).")
    @app.cli.command("notify-due")
    def notify_due(days: int | None, dry_run: bool, no_email: bool, ignore_config_time: bool):
        """
        Create 'due soon' notifications and optionally email company users.
        Respects NotificationConfig (lead days + daily send time in UTC) by default.
        """
        from app.models import MeasureAssignment, Notification, User, NotificationConfig

        now = datetime.utcnow()

        # Load or seed config
        cfg = NotificationConfig.query.get(1)
        if not cfg:
            cfg = NotificationConfig(id=1)  # defaults: lead_days=7, 07:00Z
            db.session.add(cfg)
            db.session.commit()

        # Enforce scheduled send time unless overridden
        if not ignore_config_time:
            if not (now.hour == cfg.send_hour_utc and now.minute == cfg.send_minute_utc):
                app.logger.info(
                    "Not the configured send time (now %sZ, configured %02d:%02dZ) — skipping.",
                    now.strftime("%H:%M"),
                    cfg.send_hour_utc or 0,
                    cfg.send_minute_utc or 0,
                )
                return

        lead_days = days if days is not None else int(cfg.lead_days or 7)
        horizon = now + timedelta(days=lead_days)
        kind = f"due_{lead_days}d"

        q = (
            MeasureAssignment.query
            .filter(MeasureAssignment.company_id.isnot(None))
            .filter(MeasureAssignment.due_at.isnot(None))
            .filter(MeasureAssignment.due_at >= now)
            .filter(MeasureAssignment.due_at < horizon)
        )

        created = 0
        email_jobs: list[tuple[str, str, str]] = []

        for a in q.all():
            if (a.status or "").lower() == "completed":
                continue

            exists = Notification.query.filter_by(assignment_id=a.id, kind=kind).first()
            if exists:
                continue

            company = a.company
            measure = a.measure
            subject = f"Measure due in {lead_days} day(s): {measure.name if measure else 'Measure'}"
            due_str = a.due_at.strftime("%Y-%m-%d %H:%M UTC") if a.due_at else "N/A"
            company_name = company.name if company else "Your company"
            body = (
                f"Hi,\n\n"
                f"{company_name} has a measure approaching its due date.\n\n"
                f"Measure: {measure.name if measure else 'N/A'}\n"
                f"Due at: {due_str}\n"
                f"Status: {a.status or 'Unknown'}\n\n"
                f"Please log in to review progress and complete any remaining steps."
            )

            if dry_run:
                click.echo(f"[DRY-RUN] Would create notification for assignment #{a.id} ({subject})")
            else:
                n = Notification(
                    company_id=a.company_id,
                    user_id=None,
                    assignment_id=a.id,
                    kind=kind,
                    subject=subject,
                    body=body,
                    notify_at=now,
                )
                db.session.add(n)
                created += 1

            if not no_email and company:
                for u in company.users:
                    if getattr(u, "role", "") == "company" and getattr(u, "is_active", False):
                        email_jobs.append((u.email, subject, body))

        if not dry_run:
            db.session.commit()

        emails_sent = 0
        if email_jobs and not dry_run and not no_email:
            emails_sent = _send_bulk_email(app, email_jobs)

            if emails_sent > 0 and not dry_run:
                # mark email_sent_at on notifications we just created
                sent_time = datetime.utcnow()
                for a in q.all():
                    n = Notification.query.filter_by(assignment_id=a.id, kind=kind).first()
                    if n and n.email_sent_at is None:
                        n.email_sent_at = sent_time
                db.session.commit()

        click.echo(
            f"{'(DRY-RUN) ' if dry_run else ''}"
            f"Notifications created: {created}. "
            f"Emails queued: {0 if (dry_run or no_email) else len(email_jobs)}. "
            f"Emails actually sent: {emails_sent}."
        )


def _send_bulk_email(app: Flask, jobs: list[tuple[str, str, str]]) -> int:
    """
    Minimal SMTP sender. If MAIL_* config is missing, we log and return 0.
    Supports TLS (587) and SSL (465).
    jobs: list of (to_email, subject, body)
    """
    server = app.config.get("MAIL_SERVER")
    sender = app.config.get("MAIL_DEFAULT_SENDER") or app.config.get("MAIL_USERNAME")
    port = int(app.config.get("MAIL_PORT") or 25)
    use_tls = bool(app.config.get("MAIL_USE_TLS"))
    use_ssl = bool(app.config.get("MAIL_USE_SSL"))
    username = app.config.get("MAIL_USERNAME")
    password = app.config.get("MAIL_PASSWORD")

    if not (server and sender):
        for to_addr, subject, _ in jobs:
            app.logger.info("Email skipped (MAIL_* not configured). Would send to %s: %s", to_addr, subject)
        return 0

    sent = 0
    smtp = None
    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=20)
        else:
            smtp = smtplib.SMTP(server, port, timeout=20)
            if use_tls:
                smtp.starttls()

        if username and password:
            smtp.login(username, password)

        for to_addr, subject, body in jobs:
            msg = EmailMessage()
            msg["From"] = sender
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.set_content(body)
            try:
                smtp.send_message(msg)
                sent += 1
            except Exception as e:
                app.logger.warning("Failed to email %s (%s): %s", to_addr, subject, e)
    except Exception as e:
        app.logger.error("SMTP error: %s", e)
    finally:
        if smtp:
            smtp.quit()
    return sent







