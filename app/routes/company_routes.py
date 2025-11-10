# app/routes/company_routes.py
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory,
    abort,
)
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import MeasureAssignment, AssignmentStep, Attachment, Measure, Company, Step
from app.utils.notification_helpers import get_overdue_measures_for_company, create_overdue_notifications

# Optional/soft imports (routes guard if models are missing)
try:
    from app.models import StepComment, AssignmentReport  # type: ignore
except Exception:
    StepComment = None  # type: ignore
    AssignmentReport = None  # type: ignore

try:
    from app.models import Notification  # type: ignore
except Exception:
    Notification = None  # type: ignore

try:
    from app.models import AssistanceRequest  # type: ignore
except Exception:
    AssistanceRequest = None  # type: ignore

company_bp = Blueprint("company", __name__, url_prefix="/company")

# Accepted file types (matches your templates)
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp", "doc", "docx", "xls", "xlsx"}


# ----------------- Helpers -----------------
def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _uploads_dir() -> str:
    """Base uploads dir under app root (configurable via UPLOAD_FOLDER)."""
    base = Path(current_app.root_path)
    folder = Path(current_app.config.get("UPLOAD_FOLDER", "uploads"))
    full = base / folder
    full.mkdir(parents=True, exist_ok=True)
    return str(full)


def _owns_assignment(a: MeasureAssignment) -> bool:
    """Admin can access any; company users only their company's assignments."""
    if getattr(current_user, "role", None) == "admin":
        return True
    return a.company_id == getattr(current_user, "company_id", None)


def _recalc_assignment_status(a: MeasureAssignment) -> None:
    """
    Derive status from steps, BUT never override special states
    that must persist until admin intervention.
    """
    if (a.status or "").strip().lower() in {"needs assistance", "blocked", "on hold"}:
        return  # preserve special state

    steps = a.steps or []
    if not steps:
        a.status = "Not Started"
        return

    total = len(steps)
    done = sum(1 for s in steps if s.is_completed)
    if done == 0:
        a.status = "Not Started"
    elif done < total:
        a.status = "In Progress"
    else:
        a.status = "Completed"


# ----------------- Views -----------------
def get_overdue_assignments_for_company(company_id):
    """Get all overdue assignments for a company"""
    from datetime import datetime
    current_time = datetime.utcnow()
    
    overdue = MeasureAssignment.query.filter(
        MeasureAssignment.company_id == company_id,
        MeasureAssignment.due_at < current_time,
        MeasureAssignment.status.in_(['Not Started', 'In Progress', 'Needs Assistance'])
    ).order_by(MeasureAssignment.due_at.asc()).all()
    
    return overdue
@company_bp.route("/profile", methods=["GET", "POST"])
@login_required
def company_profile():
    try:
        company = getattr(current_user, "company", None)
        if not company:
            flash("No company profile found.", "warning")
            return redirect(url_for("company.dashboard"))
            
        # Handle form submission for editing
        if request.method == "POST":
            # Only allow editing certain fields
            company.region = request.form.get("region", "").strip() or None
            company.industry_category = request.form.get("industry_category", "").strip() or None
            company.tech_resources = request.form.get("tech_resources", "").strip() or None
            company.human_resources = request.form.get("human_resources", "").strip() or None
            company.phone = request.form.get("phone", "").strip() or None
            db.session.commit()
            flash("Company profile updated successfully.", "success")
            return redirect(url_for("company.company_profile"))
        
        # Check if edit mode is requested
        editing = request.args.get('edit', '0') == '1'
            
        assignments = MeasureAssignment.query.filter_by(company_id=current_user.company_id).all()
        return render_template("company/company_profile.html", company=company, assignments=assignments, editing=editing)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Company profile error: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("company.dashboard"))


@company_bp.route("/completed")
@login_required
def completed_measures():
    if getattr(current_user, "role", "") != "company":
        return redirect(url_for("admin.dashboard"))
    assignments = (
        MeasureAssignment.query.options(
            joinedload(MeasureAssignment.measure),
            joinedload(MeasureAssignment.steps),
            joinedload(MeasureAssignment.reports),
        )
        .filter_by(company_id=current_user.company_id, status="Completed")
        .order_by(MeasureAssignment.created_at.desc())
        .all()
    )
    return render_template("company/completed_measures.html", assignments=assignments)


@company_bp.route("/toggle_step/<int:step_id>", methods=["POST"])
@login_required
def toggle_step(step_id: int):
    try:
        step = AssignmentStep.query.get_or_404(step_id)
        a = step.assignment
        if not _owns_assignment(a):
            abort(403)

        step.is_completed = not step.is_completed
        step.completed_at = datetime.utcnow() if step.is_completed else None

        # Do NOT override Needs Assistance (admin will resolve)
        if (a.status or "").strip().lower() != "needs assistance":
            _recalc_assignment_status(a)

        db.session.commit()
        
        # Log activity
        from app.utils.activity_logger import log_update
        log_update('step', step.id, step.title, {
            'assignment_id': a.id,
            'company': a.company.name if a.company else None,
            'measure': a.measure.name if a.measure else None,
            'completed': step.is_completed
        })
        
        flash(f"Step '{step.title}' updated.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle step error: {str(e)}")
        flash(f"An error occurred while updating the step. Please try again.", "danger")
    
    return redirect(request.referrer or url_for("company.dashboard"))


@company_bp.route("/upload_attachment", methods=["POST"])
@login_required
def upload_attachment():
    try:
        assignment_id = request.form.get("assignment_id", type=int)
        step_id = request.form.get("step_id", type=int)

        a = MeasureAssignment.query.get_or_404(assignment_id)
        if not _owns_assignment(a):
            abort(403)

        file = request.files.get("file")
        if not file or not file.filename:
            flash("No file selected.", "warning")
            return redirect(url_for("company.dashboard"))

        if not _allowed_file(file.filename):
            flash("Unsupported file type. Allowed: pdf, png, jpg, jpeg, webp, doc, docx, xls, xlsx.", "danger")
            return redirect(url_for("company.dashboard"))

        safe_name = secure_filename(file.filename)
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        token = f"a{assignment_id}_{('s'+str(step_id)) if step_id else 'a'}_{ts}"
        unique_name = f"{token}_{safe_name}"

        upload_dir = _uploads_dir()
        file_path = os.path.join(upload_dir, unique_name)
        file.save(file_path)

        att = Attachment(
            assignment_id=a.id,
            step_id=step_id if step_id else None,
            filename=safe_name,
            filepath=file_path,
            uploaded_by=getattr(current_user, "id", None),
            uploaded_at=datetime.utcnow(),
        )
        db.session.add(att)
        db.session.commit()

        flash("Attachment uploaded.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload attachment error: {str(e)}")
        flash("An error occurred while uploading the attachment. Please try again.", "danger")
    
    return redirect(url_for("company.dashboard"))


@company_bp.route("/attachment/<int:attachment_id>/download")
@login_required
def download_attachment(attachment_id: int):
    att = Attachment.query.get_or_404(attachment_id)
    if not _owns_assignment(att.assignment):
        abort(403)

    fullpath = att.filepath
    if not fullpath or not os.path.exists(fullpath):
        flash("File not found on server.", "danger")
        return redirect(url_for("company.dashboard"))

    directory, fname = os.path.dirname(fullpath), os.path.basename(fullpath)
    return send_from_directory(directory, fname, as_attachment=True, download_name=att.filename)


@company_bp.route("/attachment/<int:attachment_id>/delete", methods=["POST"])
@login_required
def delete_attachment(attachment_id: int):
    att = Attachment.query.get_or_404(attachment_id)
    if not _owns_assignment(att.assignment):
        abort(403)

    # Companies cannot delete files uploaded by an admin
    if getattr(current_user, "role", "") == "company":
        if att.uploader and getattr(att.uploader, "role", "") == "admin":
            flash("You cannot delete files uploaded by an administrator.", "warning")
            return redirect(url_for("company.dashboard"))

    try:
        if att.filepath and os.path.exists(att.filepath):
            os.remove(att.filepath)
    except Exception:
        pass

    db.session.delete(att)
    db.session.commit()
    flash("Attachment deleted.", "success")
    return redirect(url_for("company.dashboard"))


# ---------- Optional: comments & reports ----------
@company_bp.route("/step/<int:step_id>/comment", methods=["POST"])
@login_required
def add_step_comment(step_id: int):
    if StepComment is None:
        flash("Comments are not enabled yet. Ask an admin to add StepComment model.", "warning")
        return redirect(url_for("company.dashboard"))

    body = (request.form.get("body") or "").strip()
    step = AssignmentStep.query.get_or_404(step_id)
    if not _owns_assignment(step.assignment):
        abort(403)
    if not body:
        flash("Comment cannot be empty.", "warning")
        return redirect(url_for("company.dashboard"))

    c = StepComment(step_id=step.id, user_id=current_user.id, body=body)  # type: ignore
    db.session.add(c)
    db.session.commit()
    flash("Comment added.", "success")
    return redirect(url_for("company.dashboard"))


@company_bp.route("/assignment/<int:assignment_id>/report", methods=["POST"])
@login_required
def add_assignment_report(assignment_id: int):
    if AssignmentReport is None:
        flash("Reports are not enabled yet. Ask an admin to add AssignmentReport model.", "warning")
        return redirect(url_for("company.dashboard"))

    body = (request.form.get("body") or "").strip()
    a = MeasureAssignment.query.get_or_404(assignment_id)
    if not _owns_assignment(a):
        abort(403)
    if not body:
        flash("Report cannot be empty.", "warning")
        return redirect(url_for("company.dashboard"))

    r = AssignmentReport(assignment_id=a.id, user_id=current_user.id, body=body)  # type: ignore
    db.session.add(r)
    db.session.commit()
    flash("Report submitted.", "success")
    return redirect(url_for("company.dashboard"))


# ----------------- Needs Assistance -----------------
# app/routes/company_routes.py (snippet)
@company_bp.post("/assignment/<int:assignment_id>/request-assistance")
@login_required
def request_assistance(assignment_id: int):
    from app.models import AssistanceRequest  # local import

    a = MeasureAssignment.query.get_or_404(assignment_id)
    if not _owns_assignment(a):
        abort(403)

    # Ignore if already flagged
    if (a.status or "").lower() == "needs assistance":
        flash("Already marked as 'Needs Assistance'.", "info")
        return redirect(url_for("company.dashboard"))

    prev = a.status or "Not Started"
    a.status = "Needs Assistance"

    req = AssistanceRequest(
        assignment_id=a.id,
        requested_by_id=getattr(current_user, "id", None),
        prev_status=prev,
        requested_at=datetime.utcnow(),
        decision="open",
    )
    db.session.add(req)

    # Create a company-visible notification confirming the request
    if Notification is not None:
        subject = f"Assistance requested: {a.measure.name if a.measure else 'Measure'}"
        body = (
            f"You requested assistance for '{a.measure.name if a.measure else 'Measure'}'. "
            f"An administrator has been notified."
        )
        db.session.add(Notification(
            company_id=a.company_id,
            user_id=None,
            assignment_id=a.id,
            kind="assistance_open",
            subject=subject,
            body=body,
            notify_at=datetime.utcnow(),
        ))

    db.session.commit()
    
    # Log activity
    from app.utils.activity_logger import log_create
    log_create('assistance_request', req.id, f"Assistance: {a.measure.name if a.measure else 'Measure'}", {
        'assignment_id': a.id,
        'company': a.company.name if a.company else None,
        'measure': a.measure.name if a.measure else None,
        'prev_status': prev
    })
    
    flash("Marked as 'Needs Assistance' and notified admin.", "success")
    return redirect(url_for("company.dashboard"))




# ----------------- Notifications (company view) -----------------
@company_bp.route("/notifications")
@login_required
def notifications():
    """Show company notifications including benchmarking reminders."""
    from datetime import datetime, timedelta
    from app.models import Notification
    
    if not current_user.company_id:
        flash("No company associated with your account.", "danger")
        return redirect(url_for("company.dashboard"))
    
    # Get notifications for this company
    notifications = Notification.query.filter_by(
        company_id=current_user.company_id
    ).filter(
        Notification.read_at.is_(None)  # Only unread
    ).order_by(Notification.notify_at.desc()).all()
    
    # Get overdue assignments for notifications
    now = datetime.utcnow()
    overdue_assignments = MeasureAssignment.query.filter_by(
        company_id=current_user.company_id
    ).filter(
        MeasureAssignment.due_at < now,
        MeasureAssignment.status != "Completed"
    ).all()
    
    # Create notification-like objects for overdue assignments
    overdue_notifications = []
    for assignment in overdue_assignments:
        overdue_notifications.append({
            'id': None,  # No database notification
            'assignment': assignment,
            'title': f"{assignment.measure.name} - Overdue",
            'due_at': assignment.due_at,
            'created_at': assignment.due_at
        })
    
    # Combine all notifications
    all_notifications = list(notifications) + overdue_notifications
    
    return render_template(
        "company/notifications.html",
        notifications=all_notifications,
        overdue_count=len(overdue_notifications)
    )

@company_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    from app.models import Notification
    from datetime import datetime
    
    notification = Notification.query.get_or_404(notification_id)
    
    # Ensure user can only mark their company's notifications as read
    if notification.company_id != current_user.company_id:
        abort(403)
    
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    flash("Notification marked as read.", "success")
    return redirect(url_for("company.notifications"))


@company_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    if Notification is None:
        flash("Notifications are not enabled yet.", "warning")
        return redirect(url_for("company.dashboard"))

    if getattr(current_user, "role", "") != "company":
        return redirect(url_for("admin.dashboard"))

    updated = (
        Notification.query
        .filter_by(company_id=current_user.company_id)
        .filter(Notification.read_at.is_(None))
        .update({"read_at": datetime.utcnow()}, synchronize_session=False)
    )
    db.session.commit()
    flash(f"Marked {updated} notification(s) as read.", "success")
    return redirect(url_for("company.notifications"))


@company_bp.route("/dashboard", endpoint="dashboard")
@login_required
def dashboard():
    from datetime import datetime
    try:
        assignments = MeasureAssignment.query.filter_by(company_id=current_user.company_id).all()
        return render_template("company/dashboard.html", assignments=assignments, now=datetime.utcnow())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Dashboard error: {str(e)}")
        flash("An error occurred while loading the dashboard. Please try again.", "danger")
        return render_template("company/dashboard.html", assignments=[], now=datetime.utcnow())


@company_bp.route('/measures')
@login_required
def view_measures():
    sort_by = request.args.get('sort_by', 'order')
    direction = request.args.get('direction', 'asc')
    
    # Get assigned measures for the company
    company = Company.query.get(current_user.company_id)
    
    query = db.session.query(Measure)\
        .join(MeasureAssignment, MeasureAssignment.measure_id == Measure.id)\
        .filter(MeasureAssignment.company_id == current_user.company_id)
    
    # Apply sorting
    if sort_by == 'priority':
        if direction == 'desc':
            query = query.order_by(MeasureAssignment.urgency.desc())
        else:
            query = query.order_by(MeasureAssignment.urgency)
    elif sort_by == 'start_date':
        if direction == 'desc':
            query = query.order_by(MeasureAssignment.start_date.desc())
        else:
            query = query.order_by(MeasureAssignment.start_date)
    elif sort_by == 'end_date':
        if direction == 'desc':
            query = query.order_by(MeasureAssignment.end_date.desc())
        else:
            query = query.order_by(MeasureAssignment.end_date)
    else:  # Default to admin-defined order
        if direction == 'desc':
            query = query.order_by(Measure.order.desc())
        else:
            query = query.order_by(Measure.order)
    
    measures = query.all()
    
    # Fetch assignments for these measures for the current company and attach to measures
    try:
        measure_ids = [m.id for m in measures]
        if measure_ids:
            assignments = (
                MeasureAssignment.query
                .filter(MeasureAssignment.company_id == current_user.company_id)
                .filter(MeasureAssignment.measure_id.in_(measure_ids))
                .all()
            )
        else:
            assignments = []

        assign_map = {a.measure_id: a for a in assignments}
        for m in measures:
            a = assign_map.get(m.id)
            # Attach useful assignment fields that templates can use without changes.
            setattr(m, "assignment_id", getattr(a, "id", None))
            setattr(m, "assignment_urgency", getattr(a, "urgency", None))
            setattr(m, "assignment_status", getattr(a, "status", None))
            setattr(m, "_assignment", a)  # full object if template needs more
    except Exception:
        # don't break the view if something goes wrong attaching assignments
        current_app.logger.exception("Failed to attach assignment metadata to measures")

    return render_template('company/measures.html', 
                          measures=measures,
                          company=company,
                          sort_by=sort_by,
                          direction=direction)


@company_bp.route('/measures/<int:measure_id>')
@login_required
def view_measure(measure_id):
    measure = Measure.query.get_or_404(measure_id)
    assignment = MeasureAssignment.query.filter_by(
        company_id=current_user.company_id,
        measure_id=measure_id
    ).options(
        joinedload(MeasureAssignment.steps).joinedload(AssignmentStep.comments),
        joinedload(MeasureAssignment.steps).joinedload(AssignmentStep.attachments),
        joinedload(MeasureAssignment.reports)
    ).first_or_404()
    
    # Get steps from the assignment, ordered by their position (safely handling None values)
    steps = sorted(assignment.steps, key=lambda s: getattr(s, 'step', 0) or 0)
    
    return render_template('company/measure_detail.html', 
                          measure=measure,
                          assignment=assignment,
                          steps=steps)


@company_bp.route("/update-benchmarking", methods=["POST"])
@login_required
def update_benchmarking():
    """Update company benchmarking data (company side)."""
    from app.models import CompanyBenchmark
    from datetime import datetime, timedelta
    
    try:
        if not current_user.company:
            flash("No company associated with your account.", "danger")
            return redirect(url_for("company.company_profile"))
        
        company = current_user.company
        
        # Get form data
        data_year = request.form.get("data_year", type=int)
        if not data_year:
            flash("Data year is required.", "danger")
            return redirect(url_for("company.company_profile", edit_benchmarking=1))
        
        # Check if benchmark for this year already exists
        existing_benchmark = CompanyBenchmark.query.filter_by(
            company_id=company.id, 
            data_year=data_year
        ).first()
        
        if existing_benchmark:
            flash(f"Performance data for year {data_year} already exists. Please choose a different year.", "warning")
            return redirect(url_for("company.company_profile", edit_benchmarking=1))
        
        # Create new benchmark record
        benchmark = CompanyBenchmark(
            company_id=company.id,
            data_year=data_year,
            entered_by_id=current_user.id,
            entered_by_role=current_user.role,
            
            # Financial metrics
            turnover=request.form.get("turnover", "").strip() or None,
            
            # Production metrics
            tools_produced=request.form.get("tools_produced", type=int),
            
            # Performance metrics
            on_time_delivery=request.form.get("on_time_delivery", "").strip() or None,
            export_percentage=request.form.get("export_percentage", "").strip() or None,
            
            # Human resources metrics
            employees=request.form.get("employees", type=int),
            apprentices=request.form.get("apprentices", type=int),
            artisans=request.form.get("artisans", type=int),
            master_artisans=request.form.get("master_artisans", type=int),
            engineers=request.form.get("engineers", type=int),
            
            # Notes
            notes=request.form.get("notes", "").strip() or None
        )
        
        db.session.add(benchmark)
        
        # Update next benchmarking due date
        if company.benchmarking_reminder_months:
            company.next_benchmarking_due = datetime.utcnow() + timedelta(days=365 * company.benchmarking_reminder_months // 12)
        
        # Create a notification for admin
        from app.models import Notification
        notification = Notification(
            company_id=company.id,
            kind="benchmarking_updated",
            subject=f"Performance data updated by {company.name}",
            body=f"{company.name} has updated their performance data for {data_year}.",
            notify_at=datetime.utcnow()
        )
        db.session.add(notification)
        
        db.session.commit()
        flash(f"Performance data for {data_year} has been saved successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating benchmarking data: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for("company.company_profile"))



