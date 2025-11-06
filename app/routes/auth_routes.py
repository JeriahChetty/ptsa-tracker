# app/routes/auth_routes.py
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _is_safe_next(next_url: str) -> bool:
    """Only allow local relative URLs for `next` to avoid open-redirects."""
    if not next_url:
        return False
    p = urlparse(next_url)
    return (not p.scheme) and (not p.netloc) and next_url.startswith("/")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Redirect authenticated users to their dashboard
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'company':
            return redirect(url_for('company.dashboard'))
        return redirect(url_for('main.index'))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password_input = request.form.get("password", "").strip()

        if not email or not password_input:
            flash("Please enter both email and password.", "danger")
            return render_template("auth/login.html")

        try:
            # Find user by email (case insensitive)
            user = User.query.filter(db.func.lower(User.email) == email).first()

            if user and user.is_active and check_password_hash(user.password, password_input):
                try:
                    login_user(user, remember=True)
                    
                    # Initialize session for middleware
                    session['last_activity'] = datetime.utcnow().isoformat()
                    session.permanent = True
                    
                    current_app.logger.info(f"User {email} logged in successfully with role {user.role}")
                    
                    # Log activity
                    try:
                        from app.utils.activity_logger import log_login
                        log_login(email)
                    except:
                        pass  # Don't let logging break login
                    
                    # Redirect based on role
                    next_page = request.args.get("next")
                    if next_page:
                        return redirect(next_page)
                    elif user.role == "admin":
                        return redirect(url_for("admin.dashboard"))
                    elif user.role == "company":
                        return redirect(url_for("company.dashboard"))
                    else:
                        return redirect(url_for("main.index"))
                except Exception as redirect_error:
                    current_app.logger.error(f"Post-login redirect error for {email}: {str(redirect_error)}")
                    db.session.rollback()
                    flash("Login successful but redirect failed. Please contact support.", "warning")
                    return render_template("auth/login.html")
            else:
                # Debug info (remove in production)
                if user:
                    current_app.logger.info(
                        f"Login failed for {email}: active={user.is_active}, role={user.role}"
                    )
                else:
                    current_app.logger.info(f"No user found for email: {email}")

                flash("Invalid email or password.", "danger")
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}", exc_info=True)
            db.session.rollback()
            flash("An error occurred during login. Please try again.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    # Log activity before logout
    try:
        from app.utils.activity_logger import log_logout
        log_logout(current_user.email)
    except:
        pass  # Don't let logging break logout
    
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # This is typically admin-only functionality, but included for completeness
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Basic validation
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.", "danger")
            return render_template("auth/register.html")

        # Create new user
        user = User(
            email=email,
            password=generate_password_hash(password),
            role="company",  # Default role
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")





