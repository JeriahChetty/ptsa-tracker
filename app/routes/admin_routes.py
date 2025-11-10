from __future__ import annotations

import os
from datetime import datetime, timedelta
from io import BytesIO

from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
    flash,
    redirect,
    url_for,
    abort,
    current_app,
    jsonify,
)
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import (
    User,
    Company,
    Measure,
    MeasureStep,          # default steps for a measure (templates)
    MeasureAssignment,
    AssignmentStep,
    NotificationConfig,
    AssistanceRequest,
    Notification,
    SystemSettings,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------------------------
# Admin guard (all routes require an authenticated admin)
# ---------------------------------------------------------------------------
@admin_bp.before_request
def _admins_only():
    # Allow public access to cron endpoints
    if request.endpoint and 'cron' in request.endpoint:
        return None
    
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.path))
    if getattr(current_user, "role", "") != "admin":
        abort(403)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@admin_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    now = datetime.utcnow()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    overdue_count = db.session.query(MeasureAssignment).filter(
        MeasureAssignment.due_at.isnot(None),
        MeasureAssignment.due_at < now,
        MeasureAssignment.status != "Completed"
    ).count()
    stats = {
        "companies": db.session.query(Company).count(),
        "measures": db.session.query(Measure).count(),
        "not_started": db.session.query(MeasureAssignment).filter_by(status="Not Started").count(),
        "in_progress": db.session.query(MeasureAssignment).filter_by(status="In Progress").count(),
        "needs_assistance": db.session.query(MeasureAssignment).filter_by(status="Needs Assistance").count(),
        "completed": db.session.query(MeasureAssignment).filter_by(status="Completed").count(),
        "overdue": overdue_count,
    }
    
    # Paginate recent assignments
    recent_pagination = (
        MeasureAssignment.query.options(
            joinedload(MeasureAssignment.company),
            joinedload(MeasureAssignment.measure),
            joinedload(MeasureAssignment.steps),
        )
        .order_by(MeasureAssignment.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    
    overdue = [
        a for a in recent_pagination.items if a.due_at and a.status != "Completed" and a.due_at < now
    ]
    return render_template("admin/dashboard.html", stats=stats, recent=recent_pagination, overdue=overdue, now=now)


# ---------------------------------------------------------------------------
# Measure History (filter + export)
# ---------------------------------------------------------------------------
@admin_bp.route("/measures/history", methods=["GET"])
@login_required
def measure_history():
    page = request.args.get("page", 1, type=int)
    per_page = 20  # You can make this a config variable

    company_id = request.args.get("company_id", type=int)
    measure_id = request.args.get("measure_id", type=int)
    status = request.args.get("status", type=str)
    date_from = request.args.get("date_from", type=str)
    date_to = request.args.get("date_to", type=str)

    q = (
        db.session.query(MeasureAssignment)
        .join(Company, MeasureAssignment.company_id == Company.id)
        .join(Measure, MeasureAssignment.measure_id == Measure.id)
    )

    if company_id:
        q = q.filter(MeasureAssignment.company_id == company_id)
    if measure_id:
        q = q.filter(MeasureAssignment.measure_id == measure_id)
    if status:
        q = q.filter(MeasureAssignment.status == status)

    def _parse_dt(val: str | None):
        if not val:
            return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            return None

    df = _parse_dt(date_from)
    dt = _parse_dt(date_to)

    # prefer updated_at; fall back to created_at
    date_col = getattr(MeasureAssignment, "updated_at", None) or MeasureAssignment.created_at
    if df:
        q = q.filter(date_col >= df)
    if dt:
        q = q.filter(date_col <= dt)

    pagination = q.order_by(MeasureAssignment.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    assignments = pagination.items
    companies = Company.query.order_by(Company.name.asc()).all()
    measures = Measure.query.order_by(Measure.name.asc()).all()

    return render_template(
        "admin/measure_history.html",
        assignments=assignments,
        pagination=pagination,
        companies=companies,
        measures=measures,
        selected=dict(
            company_id=company_id,
            measure_id=measure_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
        ),
    )


@admin_bp.route("/measures/history/export", methods=["GET"])
@login_required
def measure_history_export():
    company_id = request.args.get("company_id", type=int)
    measure_id = request.args.get("measure_id", type=int)
    status = request.args.get("status", type=str)
    date_from = request.args.get("date_from", type=str)
    date_to = request.args.get("date_to", type=str)

    q = (
        db.session.query(MeasureAssignment)
        .join(Company, MeasureAssignment.company_id == Company.id)
        .join(Measure, MeasureAssignment.measure_id == Measure.id)
    )
    if company_id:
        q = q.filter(MeasureAssignment.company_id == company_id)
    if measure_id:
        q = q.filter(MeasureAssignment.measure_id == measure_id)
    if status:
        q = q.filter(MeasureAssignment.status == status)

    def _parse_dt(val: str | None):
        if not val:
            return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            return None

    df = _parse_dt(date_from)
    dt = _parse_dt(date_to)

    date_col = getattr(MeasureAssignment, "updated_at", None) or MeasureAssignment.created_at
    if df:
        q = q.filter(date_col >= df)
    if dt:
        q = q.filter(date_col <= dt)

    rows = []
    for a in q.all():
        rows.append(
            {
                "Assignment ID": a.id,
                "Company": getattr(a.company, "name", ""),
                "Measure": getattr(a.measure, "name", ""),
                "Status": a.status or "",
                "Due At": a.due_at.isoformat() if a.due_at else "",
                "Created At": a.created_at.isoformat() if a.created_at else "",
                "Updated At": getattr(a, "updated_at", None).isoformat()
                if getattr(a, "updated_at", None)
                else "",
                "Completed Steps": sum(
                    1 for s in getattr(a, "steps", []) if getattr(s, "is_completed", False)
                ),
                "Total Steps": len(getattr(a, "steps", [])),
            }
        )

    # Try XLSX first
    try:
        from openpyxl import Workbook  # type: ignore

        wb = Workbook()
        ws = wb.active
        ws.title = "Measure History"
        headers = (
            list(rows[0].keys())
            if rows
            else [
                "Assignment ID",
                "Company",
                "Measure",
                "Status",
                "Due At",
                "Created At",
                "Updated At",
                "Completed Steps",
                "Total Steps",
            ]
        )
        ws.append(headers)
        for r in rows:
            ws.append([r.get(h, "") for h in headers])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return send_file(
            buf,
            as_attachment=True,
            download_name="measure_history.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception:
        # Fallback to CSV
        headers = (
            list(rows[0].keys())
            if rows
            else [
                "Assignment ID",
                "Company",
                "Measure",
                "Status",
                "Due At",
                "Created At",
                "Updated At",
                "Completed Steps",
                "Total Steps",
            ]
        )
        out_lines = [",".join(headers)]
        for r in rows:
            out_lines.append(
                ",".join(str(r.get(h, "")).replace(",", ";") for h in headers)
            )
        buf = BytesIO()
        buf.write("\n".join(out_lines).encode("utf-8"))
        buf.seek(0)
        return send_file(
            buf, as_attachment=True, download_name="measure_history.csv", mimetype="text/csv"
        )


# ---------------------------------------------------------------------------
# Companies: create + list (admin registers company login)
# ---------------------------------------------------------------------------
@admin_bp.route("/companies", methods=["GET", "POST"])
@login_required
def companies():
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            region = request.form.get("region", "").strip()
            industry = request.form.get("industry_category", "").strip()
            tech = request.form.get("tech_resources", "").strip()
            human = request.form.get("human_resources", "").strip()
            membership = request.form.get("membership", "").strip()
            phone = request.form.get("phone", "").strip()
            login_email = (request.form.get("login_email") or "").strip().lower()
            login_password = (request.form.get("login_password") or "").strip()
            login_password_confirm = (request.form.get("login_password_confirm") or "").strip()

            measure_ids = request.form.getlist("assign_measure_ids")  # optional multi-select

            # basic validation
            if not name:
                flash("Company name is required.", "warning")
                return redirect(url_for("admin.companies"))
            if not login_email or not login_password:
                flash("Login email and password are required.", "warning")
                return redirect(url_for("admin.companies"))
            if login_password != login_password_confirm:
                flash("Passwords do not match.", "warning")
                return redirect(url_for("admin.companies"))

            # duplicates
            if Company.query.filter_by(name=name).first():
                flash("A company with that name already exists.", "warning")
                return redirect(url_for("admin.companies"))
            if User.query.filter_by(email=login_email).first():
                flash("That login email is already in use.", "warning")
                return redirect(url_for("admin.companies"))

            # create company
            c = Company(
                name=name,
                region=region or None,
                industry_category=industry or None,
                tech_resources=tech or None,
                human_resources=human or None,
                membership=membership or None,
                phone=phone or None,
            )
            db.session.add(c)
            db.session.flush()  # get c.id

            # create the company user
            u = User(
                email=login_email,
                password=generate_password_hash(login_password),
                role="company",
                is_active=True,
                company_id=c.id,
            )
            db.session.add(u)

            # assign measures immediately (optional)
            for mid in measure_ids:
                m = Measure.query.get(int(mid))
                if not m:
                    current_app.logger.warning(f"Skipping invalid measure ID: {mid} during company creation")
                    continue

                # compute due_at from measure defaults (safe)
                due_at = None
                m_timeframe = getattr(m, "default_timeframe_date", None)
                m_duration = getattr(m, "default_duration_days", None)
                if m_timeframe:
                    try:
                        due_at = datetime.combine(m_timeframe, datetime.max.time())
                    except Exception:
                        due_at = None
                elif m_duration:
                    try:
                        due_at = datetime.utcnow() + timedelta(days=int(m_duration))
                    except Exception:
                        due_at = None

                a = MeasureAssignment(
                    company_id=c.id,
                    measure_id=m.id,
                    status="Not Started",  # progress only when steps begin
                    created_at=datetime.utcnow(),
                    urgency=getattr(m, "default_urgency", None) or 1,
                    target=m.target,
                    departments=m.departments,
                    responsible=m.responsible,
                    participants=m.participants,
                    due_at=due_at,
                )
                db.session.add(a)

            db.session.commit()
            
            # Log activity
            from app.utils.activity_logger import log_create
            log_create('company', c.id, c.name, {
                'user_email': u.email,
                'region': region,
                'measures_assigned': len(measure_ids)
            })
            
            msg = f"Company '{c.name}' created and login {u.email} registered."
            if measure_ids:
                msg += f" {len(measure_ids)} measure(s) assigned."
            flash(msg, "success")
            return redirect(url_for("admin.companies"))

        companies = Company.query.order_by(Company.name.asc()).all()
        measures = Measure.query.order_by(Measure.name.asc()).all()
        return render_template("admin/companies.html", companies=companies, measures=measures)
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("admin.companies"))


# Quick alias to jump to the wizard (handy for “Proceed to Measures” buttons)
@admin_bp.route("/companies/<int:company_id>/proceed", methods=["GET"])
@login_required
def proceed_to_measures(company_id: int):
    return redirect(url_for("admin.company_measures_wizard", company_id=company_id))


# ---------------------------------------------------------------------------
# Measures: list + create + assign (single)
# ---------------------------------------------------------------------------
@admin_bp.route("/measures", methods=["GET"])
@login_required
def measures():
    measures = Measure.query.order_by(Measure.name.asc()).all()
    companies = Company.query.order_by(Company.name.asc()).all()
    return render_template("admin/measures.html", measures=measures, companies=companies)


@admin_bp.route("/measures/new", methods=["POST"])
@login_required
def create_measure():
    try:
        name = request.form.get("name", "").strip()
        measure_detail = request.form.get("measure_detail", "").strip()
        target = request.form.get("target", "").strip()
        departments = request.form.get("departments", "").strip()
        responsible = request.form.get("responsible", "").strip()
        participants = request.form.get("participants", "").strip()
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        if not name:
            flash("Measure name is required.", "warning")
            return redirect(url_for("admin.measures"))

        m = Measure(
            name=name,
            measure_detail=measure_detail or None,
            target=target or None,
            departments=departments or None,
            responsible=responsible or None,
            participants=participants or None,
            start_date=datetime.fromisoformat(start_date).date() if start_date else None,
            end_date=datetime.fromisoformat(end_date).date() if end_date else None,
        )
        db.session.add(m)
        db.session.flush()

        # Handle steps from new modal format (step_titles[]) or old format (default_steps)
        step_titles = request.form.getlist("step_titles[]")
        if step_titles:
            # New format: individual step fields
            for idx, title in enumerate(step_titles):
                title = title.strip()
                if title:
                    db.session.add(MeasureStep(measure_id=m.id, title=title, step=idx))
        else:
            # Old format: textarea with one step per line (backwards compatibility)
            steps_text = request.form.get("default_steps", "").strip()
            if steps_text:
                for idx, line in enumerate([s.strip() for s in steps_text.splitlines() if s.strip()]):
                    db.session.add(MeasureStep(measure_id=m.id, title=line, step=idx))

        db.session.commit()
        
        # Log activity
        from app.utils.activity_logger import log_create
        log_create('measure', m.id, m.name, {
            'departments': departments,
            'responsible': responsible,
            'steps_count': len(step_titles) if step_titles else 0
        })
        
        flash(f"Measure '{m.name}' created.", "success")
        return redirect(url_for("admin.measures"))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("admin.measures"))


@admin_bp.route("/measures/assign", methods=["POST"])
@login_required
def assign_measure():
    """
    Assign a measure to a company.
    """
    try:
        measure_id = request.form.get("measure_id", type=int)
        company_id = request.form.get("company_id", type=int)
        urgency = request.form.get("urgency", type=int, default=1)
        
        # Get company-specific details from form
        responsible = request.form.get("responsible", "").strip() or None
        departments = request.form.get("departments", "").strip() or None
        participants = request.form.get("participants", "").strip() or None
        start_date_str = request.form.get("start_date", "").strip()
        end_date_str = request.form.get("end_date", "").strip()
        
        if not measure_id or not company_id:
            flash("Missing required fields for assignment.", "danger")
            return redirect(url_for("admin.measures"))
        
        # Check if measure is already assigned to this company (excluding soft-deleted)
        existing = MeasureAssignment.query.filter_by(
            measure_id=measure_id, company_id=company_id
        ).filter(
            MeasureAssignment.deleted_at.is_(None)
        ).first()
        if existing:
            flash(f"This measure is already assigned to this company.", "warning")
            return redirect(url_for("admin.measures"))
        
        # Create the assignment
        measure = Measure.query.get_or_404(measure_id)
        company = Company.query.get_or_404(company_id)
        
        # Parse dates
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except Exception:
                start_date = datetime.now().date()
        else:
            start_date = datetime.now().date()
        
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except Exception:
                end_date = (datetime.now() + timedelta(days=30)).date()
        else:
            end_date = (datetime.now() + timedelta(days=30)).date()
        
        assignment = MeasureAssignment(
            measure_id=measure_id,
            company_id=company_id,
            status="Not Started",
            urgency=urgency,
            start_date=start_date,
            end_date=end_date,
            due_at=datetime.combine(end_date, datetime.max.time()) if end_date else None,
            
            # Use company-specific details from form, NOT from measure template
            target=measure.target,  # Target is measure-specific, not company-specific
            departments=departments,
            responsible=responsible,
            participants=participants,
        )
        db.session.add(assignment)
        db.session.flush()  # Get assignment ID
        
        # Clone steps from measure to assignment
        from app.models import MeasureStep, AssignmentStep
        measure_steps = MeasureStep.query.filter_by(measure_id=measure_id).order_by(MeasureStep.step.asc()).all()
        for idx, step in enumerate(measure_steps):
            assignment_step = AssignmentStep(
                assignment_id=assignment.id,
                title=step.title,
                step=idx,
                is_completed=False
            )
            db.session.add(assignment_step)
        
        db.session.commit()
        
        # Log activity
        from app.utils.activity_logger import log_create
        log_create('assignment', assignment.id, f"{measure.name} → {company.name}", {
            'measure_id': measure_id,
            'measure_name': measure.name,
            'company_id': company_id,
            'company_name': company.name
        })
        
        flash(f"Measure '{measure.name}' assigned to '{company.name}'.", "success")
        return redirect(url_for("admin.measures"))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("admin.measures"))


# ---------------------------------------------------------------------------
# Company Benchmarking History
# ---------------------------------------------------------------------------
@admin_bp.route("/companies/benchmarking-history", methods=["GET"])
@login_required
def company_benchmarking_history():
    """Company benchmarking history with statistics and filtering."""
    from app.models import CompanyBenchmark
    from sqlalchemy import func, desc
    
    # Get filter parameters
    company_filter = request.args.get("company", "").strip()
    year_filter = request.args.get("year", "").strip()
    sort_by = request.args.get("sort", "year_desc")
    
    # Base query
    query = db.session.query(CompanyBenchmark).join(Company)
    
    # Apply filters
    if company_filter:
        query = query.filter(Company.name.ilike(f"%{company_filter}%"))
    
    if year_filter:
        try:
            year_int = int(year_filter)
            query = query.filter(CompanyBenchmark.data_year == year_int)
        except ValueError:
            pass
    
    # Apply sorting
    if sort_by == "company_asc":
        query = query.order_by(Company.name.asc(), CompanyBenchmark.data_year.desc())
    elif sort_by == "company_desc":
        query = query.order_by(Company.name.desc(), CompanyBenchmark.data_year.desc())
    elif sort_by == "year_asc":
        query = query.order_by(CompanyBenchmark.data_year.asc(), Company.name.asc())
    else:  # year_desc (default)
        query = query.order_by(CompanyBenchmark.data_year.desc(), Company.name.asc())
    
    # Execute query
    benchmarks = query.all()
    
    # Calculate statistics
    stats = {
        'total_companies': Company.query.count(),
        'companies_with_data': db.session.query(func.count(func.distinct(CompanyBenchmark.company_id))).scalar() or 0,
        'total_records': CompanyBenchmark.query.count(),
        'latest_year': db.session.query(func.max(CompanyBenchmark.data_year)).scalar() or 0,
        'earliest_year': db.session.query(func.min(CompanyBenchmark.data_year)).scalar() or 0,
    }
    
    # Year distribution data for charts
    year_distribution = db.session.query(
        CompanyBenchmark.data_year,
        func.count(CompanyBenchmark.id).label('count')
    ).group_by(CompanyBenchmark.data_year).order_by(CompanyBenchmark.data_year).all()
    
    # Get unique years and companies for filter dropdowns
    all_years = db.session.query(CompanyBenchmark.data_year).distinct().order_by(CompanyBenchmark.data_year.desc()).all()
    all_companies = Company.query.order_by(Company.name).all()
    
    return render_template(
        "admin/company_benchmarking_history.html",
        benchmarks=benchmarks,
        stats=stats,
        year_distribution=year_distribution,
        all_years=[y[0] for y in all_years],
        all_companies=all_companies,
        filters={
            'company': company_filter,
            'year': year_filter,
            'sort': sort_by
        }
    )

# ---------------------------------------------------------------------------
# Notification Settings
# ---------------------------------------------------------------------------
@admin_bp.route("/notifications/settings", methods=["GET", "POST"])
@login_required
def notification_settings():
    cfg = NotificationConfig.query.get(1)
    if not cfg:
        cfg = NotificationConfig(id=1)  # defaults
        db.session.add(cfg)
        db.session.commit()

    if request.method == "POST":
        lead_days = max(0, int(request.form.get("lead_days") or cfg.lead_days))
        send_time = (request.form.get("send_time") or "").strip()  # "HH:MM"
        try:
            hour_s, min_s = send_time.split(":")
            hour = max(0, min(23, int(hour_s)))
            minute = max(0, min(59, int(min_s)))
        except Exception:
            flash("Invalid time. Use HH:MM (00–23:00–59).", "warning")
            return redirect(url_for("admin.notification_settings"))

        cfg.lead_days = lead_days
        cfg.send_hour_utc = hour
        cfg.send_minute_utc = minute
        db.session.commit()
        flash("Notification settings saved.", "success")
        return redirect(url_for("admin.notification_settings"))

    current_hhmm = f"{cfg.send_hour_utc:02d}:{cfg.send_minute_utc:02d}"
    return render_template("admin/notification_settings.html", cfg=cfg, current_hhmm=current_hhmm)


# ---------------------------------------------------------------------------
# Needs Assistance queue + decision
# ---------------------------------------------------------------------------
from sqlalchemy.orm import joinedload

@admin_bp.route("/assistance")
@login_required
def assistance_queue():
    if getattr(current_user, "role", "") != "admin":
        abort(403)

    # --- Backfill once: ensure every “Needs Assistance” assignment has an open request
    needs = (MeasureAssignment.query
             .filter(MeasureAssignment.status == "Needs Assistance")
             .all())
    new_count = 0
    for a in needs:
        if not AssistanceRequest.query.filter_by(assignment_id=a.id, decision="open").first():
            db.session.add(AssistanceRequest(
                assignment_id=a.id,
                requested_by_id=None,
                prev_status=None,
                decision="open",
            ))
            new_count += 1
    if new_count:
        db.session.commit()

    # Eager-load what the template needs
    eager = [
        joinedload(AssistanceRequest.assignment)
            .joinedload(MeasureAssignment.company),
        joinedload(AssistanceRequest.assignment)
            .joinedload(MeasureAssignment.measure),
        joinedload(AssistanceRequest.requested_by),
        joinedload(AssistanceRequest.decided_by),
    ]

    open_reqs = (AssistanceRequest.query
                 .options(*eager)
                 .filter(AssistanceRequest.decision == "open")
                 .order_by(AssistanceRequest.requested_at.desc())
                 .all())

    recent = (AssistanceRequest.query
              .options(*eager)
              .filter(AssistanceRequest.decision.in_(["resolved", "not_resolved"]))
              .order_by(AssistanceRequest.decided_at.desc())
              .limit(20)
              .all())

    # Get all companies for the reminder form
    companies = Company.query.order_by(Company.name).all()

    return render_template("admin/assistance.html", open_reqs=open_reqs, recent=recent, companies=companies)



@admin_bp.route("/assistance/<int:req_id>/decide", methods=["POST"])
@login_required
def assistance_decide(req_id: int):
    # (guard is duplicated here in case before_request is changed later)
    if getattr(current_user, "role", "") != "admin":
        abort(403)

    action = (request.form.get("action") or "").strip()  # "resolved" or "not_resolved"
    notes = (request.form.get("notes") or "").strip()

    req = AssistanceRequest.query.get_or_404(req_id)
    if req.decision != "open":
        flash("This request has already been decided.", "info")
        return redirect(url_for("admin.assistance_queue"))

    a = req.assignment
    measure = getattr(a, "measure", None)
    measure_name = getattr(measure, "name", "Measure")

    notif_kind = None
    notif_subject = None
    notif_body = None

    if action == "resolved":
        # Revert assignment back to its prior status (or In Progress)
        a.status = req.prev_status or "In Progress"
        req.decision = "resolved"

        # Company-side notification: assistance resolved
        notif_kind = "assistance_resolved"
        notif_subject = f"Assistance resolved: {measure_name}"
        notif_body = (
            f"Your assistance request for '{measure_name}' has been marked as resolved by an administrator. "
            f"The measure status has been set back to '{a.status}'."
        )
    elif action == "not_resolved":
        # Keep it flagged; no “resolved” notification
        a.status = "Needs Assistance"
        req.decision = "not_resolved"
    else:
        flash("Invalid action.", "warning")
        return redirect(url_for("admin.assistance_queue"))

    req.decision_notes = notes or None
    req.decided_at = datetime.utcnow()
    req.decided_by_id = getattr(current_user, "id", None)

    # Create the notification if the model exists (and only once per assignment/kind)
    if notif_kind:
        try:
            from app.models import Notification  # lazy import; optional model
            exists = Notification.query.filter_by(
                assignment_id=a.id, kind=notif_kind
            ).first()
            if not exists:
                db.session.add(Notification(
                    company_id=a.company_id,
                    user_id=None,
                    assignment_id=a.id,
                    kind=notif_kind,
                    subject=notif_subject,
                    body=notif_body,
                    notify_at=datetime.utcnow(),
                ))
        except Exception:
            # If Notification model/table doesn't exist, skip silently
            pass

    db.session.commit()
    flash("Assistance request updated.", "success")
    return redirect(url_for("admin.assistance_queue"))


# Add the missing route alias
@admin_bp.route("/assistance-requests")
@login_required 
def assistance_requests():
    """Alias for assistance_queue for backward compatibility"""
    return assistance_queue()

@admin_bp.route("/send-measure-reminder", methods=["POST"])
@login_required
def send_measure_reminder():
    """Send email reminder to company about their measures."""
    if getattr(current_user, "role", "") != "admin":
        abort(403)
    
    try:
        company_id = request.form.get("company_id", type=int)
        measure_id = request.form.get("measure_id", type=int)  # Optional
        reminder_type = request.form.get("reminder_type", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        include_progress = request.form.get("include_progress") == "on"
        
        if not company_id or not subject or not message:
            flash("Company, subject, and message are required.", "warning")
            return redirect(url_for("admin.assistance_queue"))
        
        company = Company.query.get_or_404(company_id)
        
        # Get company users to email
        company_users = User.query.filter_by(company_id=company_id, is_active=True).all()
        if not company_users:
            flash(f"No active users found for company: {company.name}", "warning")
            return redirect(url_for("admin.assistance_queue"))
        
        # If a specific measure is selected, get its details
        measure_info = ""
        if measure_id:
            assignment = MeasureAssignment.query.filter_by(
                company_id=company_id, 
                measure_id=measure_id
            ).first()
            if assignment:
                measure = assignment.measure
                measure_info = f"\n\nMeasure: {measure.name}\nStatus: {assignment.status}"
                if assignment.due_at:
                    measure_info += f"\nDue Date: {assignment.due_at.strftime('%Y-%m-%d')}"
        
        # Add progress summary if requested
        progress_summary = ""
        if include_progress:
            # Exclude soft-deleted assignments from progress calculation
            assignments = MeasureAssignment.query.filter_by(
                company_id=company_id
            ).filter(
                MeasureAssignment.deleted_at.is_(None)
            ).all()
            total = len(assignments)
            completed = sum(1 for a in assignments if a.status == "Completed")
            in_progress = sum(1 for a in assignments if a.status == "In Progress")
            not_started = sum(1 for a in assignments if a.status == "Not Started")
            needs_assistance = sum(1 for a in assignments if a.status == "Needs Assistance")
            
            progress_summary = f"\n\nYour Current Progress:\n"
            progress_summary += f"- Total Measures: {total}\n"
            progress_summary += f"- Completed: {completed}\n"
            progress_summary += f"- In Progress: {in_progress}\n"
            progress_summary += f"- Not Started: {not_started}\n"
            if needs_assistance > 0:
                progress_summary += f"- Needs Assistance: {needs_assistance}\n"
        
        # Replace placeholders in message
        final_message = message.replace("{company_name}", company.name)
        if measure_id and assignment:
            final_message = final_message.replace("{measure_name}", measure.name)
            final_message = final_message.replace("{current_status}", assignment.status)
            if assignment.due_at:
                final_message = final_message.replace("{due_date}", assignment.due_at.strftime('%Y-%m-%d'))
        
        # Add measure info and progress summary
        final_message += measure_info + progress_summary
        
        # Replace placeholders in subject
        final_subject = subject.replace("{company_name}", company.name)
        if measure_id and assignment:
            final_subject = final_subject.replace("{measure_name}", measure.name)
        
        # Try to send email
        mail = current_app.extensions.get('mail')
        if mail:
            from flask_mail import Message as MailMessage
            
            for user in company_users:
                msg = MailMessage(
                    subject=final_subject,
                    recipients=[user.email],
                    body=final_message,
                    sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@ptsa-tracker.com')
                )
                mail.send(msg)
            
            flash(f"Reminder email sent to {len(company_users)} user(s) at {company.name}.", "success")
        else:
            # Log the email for development
            current_app.logger.info(f"SIMULATED EMAIL to {company.name} users:")
            current_app.logger.info(f"Subject: {final_subject}")
            current_app.logger.info(f"Message: {final_message}")
            current_app.logger.info(f"Recipients: {[user.email for user in company_users]}")
            
            flash(f"Email would be sent to {len(company_users)} user(s) at {company.name} (email not configured).", "info")
        
        # Create notification records
        for user in company_users:
            db.session.add(Notification(
                company_id=company_id,
                user_id=user.id,
                assignment_id=measure_id if measure_id else None,
                kind=f"reminder_{reminder_type}" if reminder_type else "reminder",
                subject=final_subject,
                body=final_message,
                notify_at=datetime.utcnow(),
            ))
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error sending reminder: {str(e)}")
        flash(f"Error sending reminder: {str(e)}", "danger")
    
    return redirect(url_for("admin.assistance_queue"))


# Also add this API endpoint to support the dynamic measure loading in the template
@admin_bp.route("/api/company/<int:company_id>/measures", methods=["GET"])
@login_required
def api_company_measures(company_id):
    """API endpoint to get measures for a specific company."""
    if getattr(current_user, "role", "") != "admin":
        return {"success": False, "error": "Unauthorized"}, 403
    
    try:
        # Exclude soft-deleted assignments from API
        assignments = MeasureAssignment.query.filter_by(
            company_id=company_id
        ).filter(
            MeasureAssignment.deleted_at.is_(None)
        ).all()
        measures = []
        for a in assignments:
            if a.measure:
                measures.append({
                    "id": a.measure_id,
                    "name": a.measure.name,
                    "status": a.status,
                    "due_date": a.due_at.strftime('%Y-%m-%d') if a.due_at else None
                })
        
        return {"success": True, "measures": measures}
    except Exception as e:
        current_app.logger.error(f"Error fetching company measures: {str(e)}")
        return {"success": False, "error": str(e)}, 500

# ---------------------------------------------------------------------------
# Company → Measures wizard (create multiple measures & assign to this company)
# ---------------------------------------------------------------------------
@admin_bp.route("/companies/<int:company_id>/wizard", methods=["GET", "POST"])
@login_required
def company_measures_wizard(company_id: int):
    company = Company.query.get_or_404(company_id)

    if request.method == "GET":
        return render_template("admin/company_measures_wizard.html", company=company)

    try:
        # Extract measures from form data - handles nested structure including steps
        measures_data = {}
        for key, value in request.form.items():
            # Parse nested field names like measures[0][name] and measures[0][steps][0][title]
            if key.startswith('measures[') and ']' in key:
                parts = key.split('[')
                if len(parts) >= 3:
                    index = parts[1].rstrip(']')
                    
                    # Initialize dict for this measure if needed
                    if index not in measures_data:
                        measures_data[index] = {}
                    
                    # Check if this is a step field (measures[0][steps][0][title])
                    if len(parts) >= 5 and parts[2].rstrip(']') == 'steps':
                        step_index = parts[3].rstrip(']')
                        step_field = parts[4].rstrip(']')
                        
                        # Initialize steps dict if needed
                        if 'steps' not in measures_data[index]:
                            measures_data[index]['steps'] = {}
                        if step_index not in measures_data[index]['steps']:
                            measures_data[index]['steps'][step_index] = {}
                        
                        # Store the step field value
                        measures_data[index]['steps'][step_index][step_field] = value
                    else:
                        # Regular field (not a step)
                        field = parts[2].rstrip(']')
                        measures_data[index][field] = value

        # Log received data for debugging
        current_app.logger.info(f"Received measures wizard data - count: {len(measures_data)}")
        
        created_count = 0
        assigned_count = 0
        created_assignment_ids = []  # Track IDs for redirect to details page

        # Process each measure in the form
        for index, data in measures_data.items():
            # Skip if required fields are missing
            if 'name' not in data or not data['name'].strip():
                continue

            name = data['name'].strip()
            current_app.logger.debug(f"Processing measure {index}: {name}")
            
            # Extract fields with defaults for missing values
            description = data.get('measure_detail', '').strip() or None
            target = data.get('target', '').strip() or None
            departments = data.get('departments', '').strip() or None
            responsible = data.get('responsible', '').strip() or None
            participants = data.get('participants', '').strip() or None

            # Parse numeric fields
            try:
                urgency = int(data.get('urgency')) if data.get('urgency') else 1
            except (ValueError, TypeError):
                urgency = 1

            # Parse date fields
            start_date = None
            if data.get('start_date'):
                try:
                    start_date = datetime.fromisoformat(data.get('start_date').strip()).date()
                except Exception:
                    start_date = None
            
            end_date = None
            if data.get('end_date'):
                try:
                    end_date = datetime.fromisoformat(data.get('end_date').strip()).date()
                except Exception:
                    end_date = None

            # Get steps (handled differently in the form)
            step_lines = []
            if 'steps' in data and isinstance(data['steps'], dict):
                for step_idx, step_data in data['steps'].items():
                    if 'title' in step_data and step_data['title'].strip():
                        step_lines.append(step_data['title'].strip())

            # Find or create measure by name
            m = Measure.query.filter_by(name=name).first()
            measure_is_new = False  # Track if we created this measure
            
            if not m:
                current_app.logger.info(f"Creating new measure: {name}")
                measure_is_new = True
                # Create measure with the fields that exist in the model
                m = Measure(
                    name=name,
                    measure_detail=description,
                    target=target,
                    departments=departments,
                    responsible=responsible,
                    participants=participants,
                    start_date=start_date,
                    end_date=end_date,
                )
                
                db.session.add(m)
                db.session.flush()  # Get the ID
                created_count += 1

                # Add default steps to the measure
                for idx, line in enumerate(step_lines):
                    db.session.add(MeasureStep(measure_id=m.id, title=line, step=idx))

            # Create assignment for this company
            current_app.logger.info(f"Creating assignment for measure: {name} (ID: {m.id}) to company: {company.name}")
            
            # For NEW measures from form data, use provided dates and company-specific details
            # For EXISTING measures, use defaults and leave company-specific fields empty
            if measure_is_new:  # New measure just created from form
                # Use the form data (already parsed above)
                assignment_start = start_date if start_date else datetime.utcnow().date()
                assignment_end = end_date if end_date else (datetime.utcnow() + timedelta(days=30)).date()
                assignment_departments = departments
                assignment_responsible = responsible
                assignment_participants = participants
            else:  # Existing measure being assigned - needs company-specific details
                # Use default dates, leave company-specific fields empty for admin to fill
                assignment_start = datetime.utcnow().date()
                assignment_end = (datetime.utcnow() + timedelta(days=30)).date()
                assignment_departments = None
                assignment_responsible = None
                assignment_participants = None
            
            a = MeasureAssignment(
                company_id=company.id,
                measure_id=m.id,
                status="Not Started",
                created_at=datetime.utcnow(),
                urgency=urgency,
                target=m.target,  # Keep target (it's measure-specific, not company-specific)
                departments=assignment_departments,
                responsible=assignment_responsible,
                participants=assignment_participants,
                start_date=assignment_start,
                end_date=assignment_end,
            )

            # Set due_at from end_date
            if assignment_end:
                try:
                    a.due_at = datetime.combine(assignment_end, datetime.max.time())
                except Exception:
                    a.due_at = None

            db.session.add(a)
            db.session.flush()  # Get the ID

            # Clone default steps from measure into this assignment
            defaults = (
                MeasureStep.query.filter_by(measure_id=m.id)
                .order_by(MeasureStep.step.asc())  # Changed from order_index to step
                .all()
            )
            for idx, s in enumerate(defaults):
                db.session.add(
                    AssignmentStep(
                        assignment_id=a.id,
                        title=s.title,
                        step=idx,
                        is_completed=False,
                    )
                )
            assigned_count += 1
            created_assignment_ids.append(a.id)  # Track this assignment
            current_app.logger.info(f"Assignment created with ID: {a.id}")

        # Always commit at the end, not inside the loop
        db.session.commit()
        current_app.logger.info(f"Wizard complete: Created {created_count} measures, assigned {assigned_count}")

        # Redirect to complete assignment details page to fill in company-specific info
        from flask import session
        session['pending_assignment_ids'] = created_assignment_ids
        session['pending_company_id'] = company.id
        
        flash(
            f"Created {created_count} new measure(s) and assigned {assigned_count} measure(s) to {company.name}. Please complete the company-specific details below.",
            "success",
        )
        return redirect(url_for("admin.complete_assignment_details"))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in company measures wizard: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("admin.measures"))


# ---------------------------------------------------------------------------
# Complete Assignment Details (after wizard)
# ---------------------------------------------------------------------------
@admin_bp.route("/complete-assignment-details", methods=["GET"])
@login_required
def complete_assignment_details():
    """Show form to complete company-specific details for newly assigned measures."""
    from flask import session
    from datetime import timedelta
    
    # Get pending assignment IDs from session
    assignment_ids = session.get('pending_assignment_ids', [])
    company_id = session.get('pending_company_id')
    
    if not assignment_ids or not company_id:
        flash("No pending assignments to complete.", "info")
        return redirect(url_for("admin.measures"))
    
    # Get the assignments and company
    company = Company.query.get_or_404(company_id)
    assignments = MeasureAssignment.query.filter(
        MeasureAssignment.id.in_(assignment_ids)
    ).all()
    
    if not assignments:
        flash("Assignments not found.", "warning")
        return redirect(url_for("admin.measures"))
    
    # Prepare default dates
    today = datetime.utcnow().date()
    default_end_date = today + timedelta(days=30)
    
    return render_template(
        "admin/complete_assignment_details.html",
        company=company,
        assignments=assignments,
        today=today.isoformat(),
        default_end_date=default_end_date.isoformat()
    )


@admin_bp.route("/save-assignment-details", methods=["POST"])
@login_required
def save_assignment_details():
    """Save company-specific details for assignments."""
    from flask import session
    
    try:
        company_id = request.form.get("company_id", type=int)
        assignment_ids = request.form.getlist("assignment_ids[]")
        
        if not company_id or not assignment_ids:
            flash("Missing required data.", "danger")
            return redirect(url_for("admin.measures"))
        
        company = Company.query.get_or_404(company_id)
        updated_count = 0
        
        # Update each assignment with its specific details
        for assignment_id in assignment_ids:
            assignment = MeasureAssignment.query.get(int(assignment_id))
            if not assignment:
                continue
            
            # Get the form data for this specific assignment
            responsible = request.form.get(f"responsible_{assignment_id}", "").strip() or None
            departments = request.form.get(f"departments_{assignment_id}", "").strip() or None
            participants = request.form.get(f"participants_{assignment_id}", "").strip() or None
            start_date_str = request.form.get(f"start_date_{assignment_id}", "").strip()
            end_date_str = request.form.get(f"end_date_{assignment_id}", "").strip()
            
            # Update assignment
            assignment.responsible = responsible
            assignment.departments = departments
            assignment.participants = participants
            
            # Parse and update dates
            if start_date_str:
                try:
                    assignment.start_date = datetime.fromisoformat(start_date_str).date()
                except Exception:
                    pass
            
            if end_date_str:
                try:
                    assignment.end_date = datetime.fromisoformat(end_date_str).date()
                    # Also update due_at
                    assignment.due_at = datetime.combine(assignment.end_date, datetime.max.time())
                except Exception:
                    pass
            
            updated_count += 1
        
        db.session.commit()
        
        # Clear session data
        session.pop('pending_assignment_ids', None)
        session.pop('pending_company_id', None)
        
        flash(
            f"Successfully updated {updated_count} assignment(s) for {company.name}.",
            "success"
        )
        return redirect(url_for("admin.measures"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving assignment details: {str(e)}")
        flash(f"Error saving details: {str(e)}", "danger")
        return redirect(url_for("admin.measures"))


# ---------------------------------------------------------------------------
# Unassign Measure (Soft Delete)
# ---------------------------------------------------------------------------
@admin_bp.route("/assignments/<int:assignment_id>/unassign", methods=["POST"])
@login_required
def unassign_measure(assignment_id):
    """Soft-delete an assignment by setting deleted_at timestamp."""
    try:
        assignment = MeasureAssignment.query.get_or_404(assignment_id)
        
        if assignment.deleted_at:
            flash("This assignment has already been unassigned.", "warning")
            return redirect(url_for("admin.measure_history"))
        
        # Soft delete by setting deleted_at and deleted_by
        assignment.deleted_at = datetime.utcnow()
        assignment.deleted_by = current_user.id
        
        db.session.commit()
        
        flash(
            f"Successfully unassigned '{assignment.measure.name}' from {assignment.company.name}. "
            f"The measure remains in history but is removed from their dashboard.",
            "success"
        )
        
        current_app.logger.info(
            f"Admin {current_user.email} unassigned assignment {assignment_id} "
            f"(Measure: {assignment.measure.name}, Company: {assignment.company.name})"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error unassigning assignment {assignment_id}: {str(e)}")
        flash(f"Error unassigning measure: {str(e)}", "danger")
    
    return redirect(url_for("admin.measure_history"))


# --- CRUD for Companies ---
@admin_bp.route("/companies/<int:company_id>", methods=["GET", "POST"])
@login_required
def company_profile(company_id):
    company = Company.query.get_or_404(company_id)
    
    # Handle edit form submission
    if request.method == "POST":
        company.name = request.form.get("name", company.name).strip()
        company.region = request.form.get("region", "").strip() or None
        company.industry_category = request.form.get("industry_category", "").strip() or None
        company.tech_resources = request.form.get("tech_resources", "").strip() or None
        company.human_resources = request.form.get("human_resources", "").strip() or None
        company.membership = request.form.get("membership", "").strip() or None
        company.phone = request.form.get("phone", "").strip() or None
        
        db.session.commit()
        
        # Log activity
        from app.utils.activity_logger import log_update
        log_update('company', company.id, company.name, {'action': 'profile_update'})
        
        flash("Company profile updated successfully.", "success")
        return redirect(url_for("admin.company_profile", company_id=company.id))
    
    # Check if we're in edit mode
    editing = request.args.get('edit', '0') == '1'
    
    # Exclude soft-deleted assignments from company profile view
    assignments = MeasureAssignment.query.filter_by(
        company_id=company.id
    ).filter(
        MeasureAssignment.deleted_at.is_(None)
    ).order_by(MeasureAssignment.order.asc()).all()
    # Get benchmarking data for this company
    from app.models import CompanyBenchmark
    benchmarks = CompanyBenchmark.query.filter_by(company_id=company.id).order_by(CompanyBenchmark.data_year).all()
    
    return render_template("admin/company_profile.html", company=company, assignments=assignments, editing=editing, benchmarks=benchmarks)

@admin_bp.route("/companies/<int:company_id>/edit", methods=["GET"])
@login_required
def edit_company(company_id):
    # Redirect to company profile with edit parameter
    return redirect(url_for("admin.company_profile", company_id=company_id, edit=1))

@admin_bp.route("/companies/<int:company_id>/delete", methods=["POST"])
@login_required
def delete_company(company_id):
    try:
        company = Company.query.get_or_404(company_id)
        company_name = company.name  # Store before deletion
        
        db.session.delete(company)
        db.session.commit()
        
        # Log activity
        from app.utils.activity_logger import log_delete
        log_delete('company', company_id, company_name)
        
        flash("Company deleted.", "success")
        return redirect(url_for("admin.companies"))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("admin.companies"))

# --- CRUD for Measures ---
@admin_bp.route("/measures/<int:measure_id>")
@login_required
def measure_profile(measure_id):
    measure = Measure.query.get_or_404(measure_id)
    return render_template("admin/measure_profile.html", measure=measure, now=datetime.utcnow())

@admin_bp.route("/measures/<int:measure_id>/edit", methods=["GET", "POST"])
@login_required
def edit_measure(measure_id):
    measure = Measure.query.get_or_404(measure_id)
    if request.method == "POST":
        try:
            # Update basic measure fields
            measure.name = request.form.get("name", "").strip() or measure.name
            measure.measure_detail = request.form.get("measure_detail", "").strip() or None
            measure.target = request.form.get("target", "").strip() or None
            measure.departments = request.form.get("departments", "").strip() or None
            measure.responsible = request.form.get("responsible", "").strip() or None
            measure.participants = request.form.get("participants", "").strip() or None
            
            # Update date fields
            start_date_str = request.form.get("start_date", "").strip()
            if start_date_str:
                measure.start_date = datetime.fromisoformat(start_date_str).date()
            
            end_date_str = request.form.get("end_date", "").strip()
            if end_date_str:
                measure.end_date = datetime.fromisoformat(end_date_str).date()
            
            # Handle steps: get arrays from form
            step_ids = request.form.getlist("step_ids[]")
            step_titles = request.form.getlist("step_titles[]")
            
            # Track which step IDs are in the form (to delete removed ones)
            submitted_step_ids = set()
            
            # Process each step from the form
            for idx, (step_id, title) in enumerate(zip(step_ids, step_titles)):
                title = title.strip()
                if not title:
                    continue  # Skip empty steps
                
                if step_id and step_id.strip():
                    # Update existing step
                    step = MeasureStep.query.get(int(step_id))
                    if step and step.measure_id == measure.id:
                        step.title = title
                        step.step = idx + 1  # Start from 1 instead of 0
                        submitted_step_ids.add(step.id)
                else:
                    # Create new step
                    new_step = MeasureStep(
                        measure_id=measure.id,
                        title=title,
                        step=idx + 1  # Start from 1 instead of 0
                    )
                    db.session.add(new_step)
                    db.session.flush()
                    submitted_step_ids.add(new_step.id)
            
            # Delete steps that were removed from the form
            for step in measure.steps:
                if step.id not in submitted_step_ids:
                    db.session.delete(step)
            
            db.session.commit()
            flash("Measure and steps updated successfully.", "success")
            return redirect(url_for("admin.measure_profile", measure_id=measure.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating measure: {str(e)}")
            flash(f"An error occurred: {str(e)}", "danger")
            return render_template("admin/edit_measure.html", measure=measure)
    return render_template("admin/edit_measure.html", measure=measure)

@admin_bp.route("/measures/<int:measure_id>/delete", methods=["POST"])
@login_required
def delete_measure(measure_id):
    """Delete a measure and all related records."""
    try:
        from flask import jsonify
        measure = Measure.query.get_or_404(measure_id)
        measure_name = measure.name  # Store name before deletion

        # Manually delete related assignments first to ensure cascades work reliably
        # This is more explicit and safer with complex relationships.
        MeasureAssignment.query.filter_by(measure_id=measure.id).delete()
        
        # Now delete the measure itself. Its own steps will be cascaded.
        db.session.delete(measure)
        
        db.session.commit()
        
        # Log activity
        from app.utils.activity_logger import log_delete
        log_delete('measure', measure_id, measure_name)
        
        return jsonify({"success": True, "message": "Measure deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting measure {measure_id}: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/steps/<int:step_id>/delete", methods=["POST"])
@login_required
def delete_step(step_id):
    """Delete a measure step."""
    try:
        from flask import jsonify
        step = MeasureStep.query.get_or_404(step_id)
        db.session.delete(step)
        db.session.commit()
        return jsonify({"success": True, "message": "Step deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting step: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@admin_bp.route("/save_measures", methods=["POST"])
@login_required
def save_measures():
    """Save all measures and their steps from the form."""
    try:
        measures_data = request.form.to_dict(flat=False)
        
        # Process all submitted measures
        for i in range(len(measures_data.get('measures[][name]', []))):
            measure_id = measures_data.get(f'measures[{i}][id]', [''])[0]
            name = measures_data.get(f'measures[{i}][name]', [''])[0]
            target = measures_data.get(f'measures[{i}][target]', [''])[0]
            measure_detail = measures_data.get(f'measures[{i}][measure_detail]', [''])[0]
            departments = measures_data.get(f'measures[{i}][departments]', [''])[0]
            responsible = measures_data.get(f'measures[{i}][responsible]', [''])[0]
            participants = measures_data.get(f'measures[{i}][participants]', [''])[0]
            
            if not name:
                current_app.logger.warning(f"Skipping measure at index {i} - missing name")
                continue  # Skip empty measures
                
            # Create or update measure
            if measure_id:
                measure = Measure.query.get(measure_id)
                if not measure:
                    current_app.logger.warning(f"Skipping measure at index {i} - ID {measure_id} not found")
                    continue
            else:
                measure = Measure()
                db.session.add(measure)
                
            # Update measure fields
            measure.name = name
            measure.target = target
            measure.measure_detail = measure_detail
            measure.departments = departments
            measure.responsible = responsible
            measure.participants = participants
            
            db.session.flush()
            
            # Process steps for this measure
            step_titles = measures_data.get(f'measures[{i}][steps][][title]', [])
            step_numbers = measures_data.get(f'measures[{i}][steps][][step]', [])
            step_ids = measures_data.get(f'measures[{i}][steps][][id]', [])
            
            # Keep track of processed steps to delete any that aren't in the form
            processed_step_ids = []
            
            for j in range(len(step_titles)):
                step_id = step_ids[j] if j < len(step_ids) else ''
                step_title = step_titles[j]
                step_number = int(step_numbers[j]) if j < len(step_numbers) and step_numbers[j].isdigit() else j
                
                if not step_title:
                    current_app.logger.warning(f"Skipping empty step at index {j} for measure {i}")
                    continue  # Skip empty steps
                    
                # Create or update step
                if step_id:
                    step = MeasureStep.query.get(step_id)
                    if not step or step.measure_id != measure.id:
                        step = MeasureStep(measure_id=measure.id)
                        db.session.add(step)
                else:
                    step = MeasureStep(measure_id=measure.id)
                    db.session.add(step)
                
                step.title = step_title
                step.step = step_number
                
                db.session.flush()
                processed_step_ids.append(step.id)
    
            # Delete steps that weren't in the form
        if measure_id:
            MeasureStep.query.filter(
                MeasureStep.measure_id == measure.id,
                ~MeasureStep.id.in_(processed_step_ids) if processed_step_ids else True
            ).delete(synchronize_session=False)
        
        db.session.commit()
        flash('Measures saved successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving measures: {str(e)}")
        flash(f'Error saving measures: {str(e)}', 'danger')
        
    return redirect(url_for('admin.measures'))


from flask import jsonify, request
from app.models import Measure, Step, db

@admin_bp.route('/measures/order', methods=['GET'])
@login_required
def manage_measure_order():
    """Page to manage the order of measures"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
        
    measures = Measure.query.order_by(Measure.order).all()
    return render_template('admin/measure_order.html', measures=measures)

@admin_bp.route('/steps/order/<int:measure_id>', methods=['GET'])
@login_required
def manage_step_order(measure_id):
    """Page to manage the order of steps for a specific measure"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
        
    measure = Measure.query.get_or_404(measure_id)
    steps = Step.query.filter_by(measure_id=measure_id).order_by(Step.order).all()
    return render_template('admin/step_order.html', measure=measure, steps=steps)

@admin_bp.route('/api/companies/<int:company_id>/update-assignment-order', methods=['POST'])
@login_required
def update_assignment_order(company_id):
    """API endpoint to update assignment order for a company"""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    try:
        data = request.get_json()
        if not data or 'assignments' not in data:
            return jsonify({"error": "Invalid data"}), 400
        
        # Update assignment orders
        for item in data['assignments']:
            assignment = MeasureAssignment.query.filter_by(
                id=item['id'],
                company_id=company_id
            ).first()
            if assignment:
                assignment.order = item['order']
        
        db.session.commit()
        return jsonify({"success": True, "message": "Assignment order updated"})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating assignment order: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/measures/update-order', methods=['POST'])
@login_required
def update_measure_order():
    """API endpoint to update measure order"""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    order_data = request.json
    
    try:
        for item in order_data:
            measure = Measure.query.get(item['id'])
            if measure:
                measure.order = item['order']
        
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/steps/update-order', methods=['POST'])
@login_required
def update_step_order():
    """API endpoint to update step order"""
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    order_data = request.json
    
    try:
        for item in order_data:
            step = Step.query.get(item['id'])
            if step:
                step.order = item['order']
        
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Email Test Notification
# ---------------------------------------------------------------------------
@admin_bp.route("/notifications/test-email", methods=["GET", "POST"])
@login_required
def test_company_email():
    """Send a test email notification to a company."""
    companies = Company.query.order_by(Company.name).all()
    
    if request.method == "POST":
        company_id = request.form.get("company_id", type=int)
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        
        if not company_id or not subject or not message:
            flash("All fields are required.", "warning")
            return render_template("admin/test_email.html", companies=companies)
        
        company = Company.query.get_or_404(company_id)
        
        # Get company users to email
        company_users = User.query.filter_by(company_id=company_id, is_active=True).all()
        if not company_users:
            flash(f"No active users found for company: {company.name}", "warning")
            return render_template("admin/test_email.html", companies=companies)
        
        # Try to send email
        try:
            # Check if Flask-Mail is configured
            mail = current_app.extensions.get('mail')
            if mail:
                # Using Flask-Mail
                from flask_mail import Message
                
                for user in company_users:
                    msg = Message(
                        subject=subject,
                        recipients=[user.email],
                        body=message,
                        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@ptsa-tracker.com')
                    )
                    mail.send(msg)
                
                flash(f"Test email sent to {len(company_users)} user(s) at {company.name}.", "success")
            else:
                # Fallback to logging the email (for development)
                current_app.logger.info(f"SIMULATED EMAIL to {company.name} users:")
                current_app.logger.info(f"Subject: {subject}")
                current_app.logger.info(f"Message: {message}")
                current_app.logger.info(f"Recipients: {[user.email for user in company_users]}")
                
                flash(f"Email would be sent to {len(company_users)} user(s) at {company.name}, but email is not configured. Check logs.", "info")
            
            # Create a notification record in the database (regardless of email config)
            if Notification is not None:
                for user in company_users:
                    db.session.add(Notification(
                        company_id=company_id,
                        user_id=user.id,
                        kind="test_email",
                        subject=subject,
                        body=message,
                        notify_at=datetime.utcnow(),
                    ))
                db.session.commit()
                flash(f"Notification added to database for {len(company_users)} user(s).", "info")
        
        except Exception as e:
            current_app.logger.error(f"Error sending test email: {str(e)}")
            flash(f"Error sending email: {str(e)}", "danger")
            
    return render_template("admin/test_email.html", companies=companies)


# ---------------------------------------------------------------------------
# Admin Notifications
# ---------------------------------------------------------------------------
@admin_bp.route("/admin-notifications")
@login_required
def admin_notifications():
    """View notifications for admin with ability to resolve assistance requests."""
    
    # Get all UNREAD notifications related to assistance requests
    assistance_notifications = (
        Notification.query
        .filter(Notification.kind == "assistance_open")
        .filter(Notification.read_at.is_(None))  # Only show unread notifications
        .order_by(Notification.notify_at.desc())
        .options(
            joinedload(Notification.assignment),
            joinedload(Notification.company)
        )
        .all()
    )
    
    # Get other admin notifications
    other_notifications = (
        Notification.query
        .filter(Notification.kind != "assistance_open")
        .order_by(Notification.notify_at.desc())
        .options(
            joinedload(Notification.assignment),
            joinedload(Notification.company)
        )
        .limit(20)
        .all()
    )
    
    return render_template(
        "admin/admin_notifications.html",
        assistance_notifications=assistance_notifications,
        other_notifications=other_notifications
    )

@admin_bp.route("/notifications/<int:notification_id>/resolve", methods=["POST"])
@login_required
def resolve_assistance_notification(notification_id):
    """Resolve a needs assistance notification directly from the notifications tab."""
    
    notification = Notification.query.get_or_404(notification_id)
    if notification.kind != "assistance_open":
        flash("This notification is not an assistance request.", "warning")
        return redirect(url_for("admin.admin_notifications"))
    
    assignment_id = notification.assignment_id
    if not assignment_id:
        flash("No assignment linked to this notification.", "warning")
        return redirect(url_for("admin.admin_notifications"))
    
    # Get the assignment directly
    assignment = MeasureAssignment.query.get_or_404(assignment_id)
    
    # Find or create the assistance request
    assistance_request = AssistanceRequest.query.filter_by(
        assignment_id=assignment_id, 
        decision="open"
    ).first()
    
    if not assistance_request:
        # Create an assistance request if one doesn't exist
        current_app.logger.info(f"Creating new assistance request for assignment {assignment_id}")
        assistance_request = AssistanceRequest(
            assignment_id=assignment_id,
            requested_by_id=None,
            prev_status=assignment.status if assignment.status != "Needs Assistance" else "In Progress",
            requested_at=notification.notify_at or datetime.utcnow(),
            decision="open"
        )
        db.session.add(assistance_request)
        db.session.flush()  # Get the ID
    
    notes = request.form.get("notes", "").strip() or "Resolved from notifications tab"
    
    # Get measure details
    measure = getattr(assignment, "measure", None)
    measure_name = getattr(measure, "name", "Measure")
    
    # Update the assistance request and assignment
    prev_status = assistance_request.prev_status or "In Progress"
    assignment.status = prev_status
    assistance_request.decision = "resolved"
    assistance_request.decision_notes = notes
    assistance_request.decided_at = datetime.utcnow()
    assistance_request.decided_by_id = current_user.id
    
    # Check if a resolution notification already exists for this assignment
    existing_notification = Notification.query.filter_by(
        assignment_id=assignment.id,
        kind="assistance_resolved"
    ).first()
    
    if existing_notification:
        # Update the existing notification instead of creating a new one
        existing_notification.subject = f"Assistance resolved: {measure_name}"
        existing_notification.body = (
            f"Your assistance request for '{measure_name}' has been marked as resolved by an administrator. "
            f"The measure status has been set back to '{prev_status}'."
        )
        existing_notification.notify_at = datetime.utcnow()
        existing_notification.read_at = None  # Mark as unread again
    else:
        # Create a resolution notification
        db.session.add(Notification(
            company_id=assignment.company_id,
            user_id=None,
            assignment_id=assignment.id,
            kind="assistance_resolved",
            subject=f"Assistance resolved: {measure_name}",
            body=(
                f"Your assistance request for '{measure_name}' has been marked as resolved by an administrator. "
                f"The measure status has been set back to '{prev_status}'."
            ),
            notify_at=datetime.utcnow(),
        ))
    
    # Mark the original notification as read
    notification.read_at = datetime.utcnow()
    
    db.session.commit()
    flash("Assistance request resolved successfully.", "success")
    return redirect(url_for("admin.admin_notifications"))


@admin_bp.route("/notifications/<int:notification_id>/mark-read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    
    notification = Notification.query.get_or_404(notification_id)
    
    # Mark as read
    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        db.session.commit()
        flash("Notification marked as read.", "success")
    
    return redirect(url_for("admin.admin_notifications"))

@admin_bp.route("/measures/<int:measure_id>/add-step", methods=["POST"])
@login_required
def add_step(measure_id):
    """Add a step to a measure."""
    try:
        measure = Measure.query.get_or_404(measure_id)
        title = request.form.get("title", "").strip()
        order_index = request.form.get("order_index", type=int)
        
        if not title:
            flash("Step title is required.", "warning")
            return redirect(url_for("admin.measure_profile", measure_id=measure_id))
            
        # Use the provided order or append to the end
        if order_index is None:
            # Get the max step number and add 1
            max_order = db.session.query(db.func.max(MeasureStep.step)).filter_by(measure_id=measure_id).scalar()
            order_index = (max_order or -1) + 1
            
        step = MeasureStep(
            measure_id=measure_id,
            title=title,
            step=order_index
        )
        db.session.add(step)
        db.session.commit()
        
        flash("Step added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding step: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        
    return redirect(url_for("admin.measure_profile", measure_id=measure_id))


@admin_bp.route("/companies/<int:company_id>/add-user", methods=["GET", "POST"])
@login_required
def add_company_user(company_id):
    company = Company.query.get_or_404(company_id)
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "company").strip()
        
        if not email or not password:
            flash("Email and password are required.", "warning")
            return render_template("admin/add_company_user.html", company=company)
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash("A user with this email already exists.", "warning")
            return render_template("admin/add_company_user.html", company=company)
        
        # Create new user
        user = User(
            email=email,
            password=generate_password_hash(password),
            role=role,
            is_active=True,
            company_id=company.id
        )
        db.session.add(user)
        db.session.commit()
        
        flash(f"User {email} has been added to {company.name}.", "success")
        return redirect(url_for("admin.company_profile", company_id=company.id))
    
    return render_template("admin/add_company_user.html", company=company)

@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Only admins can edit users
    if getattr(current_user, "role", "") != "admin":
        flash("You don't have permission to perform this action.", "danger")
        return redirect(url_for("admin.companies"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", "").strip()
        role = request.form.get("role", "company").strip()
        
        if not email:
            flash("Email is required.", "warning")
            return render_template("admin/edit_user.html", user=user)
        
        # Check if email is already taken by another user
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            flash("This email is already in use by another user.", "warning")
            return render_template("admin/edit_user.html", user=user)
        
        # Update user fields
        user.email = email
        user.role = role
        
        # Update password only if provided
        if new_password:
            user.password = generate_password_hash(new_password)
        
        db.session.commit()
        flash("User updated successfully.", "success")
        
        # Redirect back to company profile if user belongs to a company
        if user.company_id:
            return redirect(url_for("admin.company_profile", company_id=user.company_id))
        else:
            return redirect(url_for("admin.users"))
    
    return render_template("admin/edit_user.html", user=user)

@admin_bp.route("/assignments/<int:assignment_id>", methods=["GET"])
@login_required
def view_assignment(assignment_id):
    """View details of a specific assignment."""
    assignment = MeasureAssignment.query.get_or_404(assignment_id)
    return render_template("admin/view_assignment.html", assignment=assignment)

@admin_bp.route("/companies/<int:company_id>/benchmarking", methods=["POST"])
@login_required
def update_company_benchmarking(company_id):
    """Update company benchmarking data."""
    from app.models import CompanyBenchmark
    from datetime import datetime, timedelta
    
    try:
        company = Company.query.get_or_404(company_id)
        
        # Get form data
        data_year = request.form.get("data_year", type=int)
        if not data_year:
            flash("Data year is required.", "danger")
            return redirect(url_for("admin.company_profile", company_id=company_id, edit_benchmarking=1))
        
        # Check if benchmark for this year already exists
        existing_benchmark = CompanyBenchmark.query.filter_by(
            company_id=company_id, 
            data_year=data_year
        ).first()
        
        if existing_benchmark:
            flash(f"Benchmarking data for year {data_year} already exists. Please choose a different year.", "warning")
            return redirect(url_for("admin.company_profile", company_id=company_id, edit_benchmarking=1))
        
        # Create new benchmark record
        benchmark = CompanyBenchmark(
            company_id=company_id,
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
        
        # Update company's next benchmarking due date
        if not company.next_benchmarking_due:
            company.next_benchmarking_due = datetime.utcnow() + timedelta(days=365 * (company.benchmarking_reminder_months or 12) // 12)
        
        db.session.commit()
        flash(f"Benchmarking data for {data_year} has been saved successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating benchmarking data: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for("admin.company_profile", company_id=company_id))


@admin_bp.route("/seed-data", methods=["GET", "POST"])
@login_required
def seed_data_endpoint():
    """Web endpoint to seed database data remotely"""
    if request.method == "GET":
        # Show a form to confirm seeding
        return render_template("admin/seed_data_form.html")
    
    try:
        # Import and run the comprehensive seeding
        import sys
        import os
        from pathlib import Path
        
        # Add the project root to path
        project_root = Path(current_app.root_path).parent
        sys.path.insert(0, str(project_root))
        
        # Import and run seeding function
        from comprehensive_seed import comprehensive_seed
        comprehensive_seed()
        
        flash("Database seeded successfully with comprehensive data!", "success")
        return redirect(url_for("admin.dashboard"))
        
    except Exception as e:
        current_app.logger.error(f"Remote seeding failed: {str(e)}")
        flash(f"Seeding failed: {str(e)}", "danger")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/companies/export-benchmarking-data")
@login_required
def export_benchmarking_data():
    """Export benchmarking data as CSV"""
    if getattr(current_user, "role", "") != "admin":
        abort(403)
    
    from flask import Response
    import csv
    import io
    
    # Get all benchmarking data
    benchmarks = db.session.query(CompanyBenchmark).join(Company).order_by(
        CompanyBenchmark.data_year.desc(),
        Company.name
    ).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Company', 'Year', 'Turnover', 'Employees', 'Tools Produced',
        'On-Time Delivery', 'Export %', 'Created Date', 'Updated Date'
    ])
    
    # Write data
    for benchmark in benchmarks:
        writer.writerow([
            benchmark.company.name,
            benchmark.data_year,
            benchmark.turnover or '',
            benchmark.employees or '',
            benchmark.tools_produced or '',
            benchmark.on_time_delivery or '',
            benchmark.export_percentage or '',
            benchmark.created_at.strftime('%Y-%m-%d %H:%M:%S') if benchmark.created_at else '',
            benchmark.updated_at.strftime('%Y-%m-%d %H:%M:%S') if benchmark.updated_at else ''
        ])
    
    # Create response
    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=benchmarking_data.csv'}
    )
    
    return response


@admin_bp.route("/profile", methods=["GET", "POST"])
@login_required
def admin_profile():
    """Admin user profile management"""
    if getattr(current_user, "role", "") != "admin":
        abort(403)
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "update_profile":
            # Update basic profile info
            current_user.first_name = request.form.get("first_name", "").strip() or None
            current_user.last_name = request.form.get("last_name", "").strip() or None
            current_user.phone = request.form.get("phone", "").strip() or None
            
            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("admin.admin_profile"))
        
        elif action == "change_password":
            # Handle password change
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")
            
            if not current_password or not new_password:
                flash("Current password and new password are required.", "danger")
                return redirect(url_for("admin.admin_profile", edit=1))
            
            # Verify current password
            from werkzeug.security import check_password_hash, generate_password_hash
            if not check_password_hash(current_user.password, current_password):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for("admin.admin_profile", edit=1))
            
            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("admin.admin_profile", edit=1))
            
            if len(new_password) < 6:
                flash("New password must be at least 6 characters long.", "danger")
                return redirect(url_for("admin.admin_profile", edit=1))
            
            # Update password
            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("admin.admin_profile"))
    
    # Check if edit mode is requested
    editing = request.args.get('edit', '0') == '1'
    
    return render_template("admin/admin_profile.html", user=current_user, editing=editing)


# ---------------------------------------------------------------------------
# Document Parsing Route
# ---------------------------------------------------------------------------
@admin_bp.route("/parse-measure-document", methods=["POST"])
@login_required
def parse_measure_document():
    """Parse uploaded PDF or PowerPoint document to extract measure data"""
    import os
    import tempfile
    from werkzeug.utils import secure_filename
    from app.utils.document_parser import parse_measure_document as parse_doc
    
    try:
        if 'document' not in request.files:
            return {'success': False, 'error': 'No file uploaded'}, 400
        
        file = request.files['document']
        if file.filename == '':
            return {'success': False, 'error': 'No file selected'}, 400
        
        # Get file extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in ['pdf', 'ppt', 'pptx', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'webp']:
            return {'success': False, 'error': 'Unsupported file type. Please upload PDF, PowerPoint, Word, or image files.'}, 400
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
            file.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # Parse the document (AI-enabled by default if API key is available)
            result = parse_doc(tmp_path, file_ext, use_ai=True)
            
            # Convert date objects to strings for JSON serialization
            measures = result.get('measures', [])
            for measure in measures:
                if measure.get('start_date'):
                    measure['start_date'] = measure['start_date'].isoformat() if hasattr(measure['start_date'], 'isoformat') else measure['start_date']
                if measure.get('end_date'):
                    measure['end_date'] = measure['end_date'].isoformat() if hasattr(measure['end_date'], 'isoformat') else measure['end_date']
            
            return {
                'success': True, 
                'data': {
                    'measures': measures,
                    'count': len(measures),
                    'method': result.get('method', 'unknown'),
                    'error': result.get('error', None)  # Pass error message if any
                }
            }, 200
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except:
                pass
                
    except Exception as e:
        current_app.logger.error(f"Error parsing document: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@admin_bp.route("/parse-pasted-text", methods=["POST"])
@login_required
def parse_pasted_text():
    """Parse pasted text to extract measure data"""
    from app.utils.document_parser import extract_multiple_measures
    
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return {'success': False, 'error': 'No text provided'}, 400
        
        pasted_text = data['text']
        if not pasted_text.strip():
            return {'success': False, 'error': 'Empty text'}, 400
        
        # Try AI extraction first if API key is available
        if os.getenv('OPENAI_API_KEY'):
            try:
                from app.utils.document_parser import extract_with_ai
                measures = extract_with_ai(pasted_text, [])
                if measures:
                    # Convert date objects to strings for JSON
                    for measure in measures:
                        if measure.get('start_date'):
                            measure['start_date'] = measure['start_date'].isoformat() if hasattr(measure['start_date'], 'isoformat') else measure['start_date']
                        if measure.get('end_date'):
                            measure['end_date'] = measure['end_date'].isoformat() if hasattr(measure['end_date'], 'isoformat') else measure['end_date']
                    
                    return {
                        'success': True,
                        'data': {
                            'measures': measures,
                            'count': len(measures),
                            'method': 'ai_paste'
                        }
                    }, 200
            except Exception as e:
                current_app.logger.warning(f"AI extraction failed for pasted text: {e}")
        
        # Fallback to pattern matching
        measures = extract_multiple_measures(pasted_text)
        
        # Convert date objects to strings
        for measure in measures:
            if measure.get('start_date'):
                measure['start_date'] = measure['start_date'].isoformat() if hasattr(measure['start_date'], 'isoformat') else measure['start_date']
            if measure.get('end_date'):
                measure['end_date'] = measure['end_date'].isoformat() if hasattr(measure['end_date'], 'isoformat') else measure['end_date']
        
        return {
            'success': True,
            'data': {
                'measures': measures,
                'count': len(measures),
                'method': 'pattern_matching_paste'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Error parsing pasted text: {str(e)}")
        return {'success': False, 'error': str(e)}, 500



# ===================== USER MANAGEMENT & ACTIVITY LOGS =====================

@admin_bp.route("/users", methods=["GET"])
@login_required
def users():
    """User management page - admin only"""
    if not current_user.is_admin:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("admin.dashboard"))
    
    from app.models import ActivityLog
    from sqlalchemy import func
    
    # Get all users with activity counts
    all_users = db.session.query(
        User,
        func.count(ActivityLog.id).label('activity_count')
    ).outerjoin(
        ActivityLog, User.id == ActivityLog.user_id
    ).group_by(User.id).order_by(User.created_at.desc()).all()
    
    users_data = []
    for user, activity_count in all_users:
        users_data.append({
            'user': user,
            'activity_count': activity_count,
            'company_name': user.company.name if user.company else None
        })
    
    return render_template(
        "admin/users.html",
        users=users_data
    )


@admin_bp.route("/users/create", methods=["POST"])
@login_required
def create_user():
    """Create a new admin user"""
    if not current_user.is_admin:
        return {'success': False, 'error': 'Access denied'}, 403
    
    from werkzeug.security import generate_password_hash
    from app.utils.activity_logger import log_create
    
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'company').strip()
        
        if not email or not password:
            flash("Email and password are required", "error")
            return redirect(url_for('admin.users'))
        
        # Check if user exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash(f"User with email {email} already exists", "error")
            return redirect(url_for('admin.users'))
        
        # Create user
        new_user = User(
            email=email,
            password=generate_password_hash(password),
            role=role,
            is_active=True
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log activity
        log_create('user', new_user.id, email, {'role': role})
        
        flash(f"User {email} created successfully", "success")
        return redirect(url_for('admin.users'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating user: {str(e)}", "error")
        return redirect(url_for('admin.users'))


@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@login_required
def toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    if not current_user.is_admin:
        return {'success': False, 'error': 'Access denied'}, 403
    
    from app.utils.activity_logger import log_update
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow deactivating yourself
        if user.id == current_user.id:
            flash("Cannot deactivate your own account", "error")
            return redirect(url_for('admin.users'))
        
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "activated" if user.is_active else "deactivated"
        log_update('user', user.id, user.email, {'action': status})
        
        flash(f"User {user.email} {status}", "success")
        return redirect(url_for('admin.users'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating user: {str(e)}", "error")
        return redirect(url_for('admin.users'))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    """Delete a user"""
    if not current_user.is_admin:
        return {'success': False, 'error': 'Access denied'}, 403
    
    from app.utils.activity_logger import log_delete
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow deleting yourself
        if user.id == current_user.id:
            flash("Cannot delete your own account", "error")
            return redirect(url_for('admin.users'))
        
        email = user.email
        db.session.delete(user)
        db.session.commit()
        
        log_delete('user', user_id, email)
        
        flash(f"User {email} deleted", "success")
        return redirect(url_for('admin.users'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}", "error")
        return redirect(url_for('admin.users'))


@admin_bp.route("/activity-logs", methods=["GET"])
@login_required
def activity_logs():
    """View activity logs - admin only"""
    if not current_user.is_admin:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("admin.dashboard"))
    
    from app.models import ActivityLog
    from sqlalchemy import desc
    
    # Get filter parameters
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action', '').strip()
    entity_type = request.args.get('entity_type', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Build query
    query = ActivityLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter_by(action=action)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    # Paginate
    pagination = query.order_by(desc(ActivityLog.created_at)).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Get unique actions and entity types for filters
    unique_actions = db.session.query(ActivityLog.action).distinct().all()
    unique_entities = db.session.query(ActivityLog.entity_type).distinct().all()
    
    actions_list = [a[0] for a in unique_actions if a[0]]
    entities_list = [e[0] for e in unique_entities if e[0]]
    
    # Get all users for filter
    all_users = User.query.order_by(User.email).all()
    
    return render_template(
        "admin/activity_logs.html",
        logs=pagination.items,
        pagination=pagination,
        actions=actions_list,
        entity_types=entities_list,
        users=all_users,
        current_filters={
            'user_id': user_id,
            'action': action,
            'entity_type': entity_type
        }
    )


# ---------------------------------------------------------------------------
# System Settings (Email Notifications & Reports)
# ---------------------------------------------------------------------------
@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def system_settings():
    """Manage system-wide settings for email notifications and reports"""
    settings = SystemSettings.get_settings()
    
    if request.method == "POST":
        try:
            # Update progress report settings
            settings.progress_report_enabled = request.form.get('progress_report_enabled') == 'on'
            settings.progress_report_frequency = request.form.get('progress_report_frequency', 'weekly')
            settings.progress_report_day = int(request.form.get('progress_report_day', 1))
            settings.progress_report_hour = int(request.form.get('progress_report_hour', 8))
            settings.progress_report_additional_emails = request.form.get('progress_report_additional_emails', '').strip()
            
            # Update assistance settings
            settings.assistance_email_enabled = request.form.get('assistance_email_enabled') == 'on'
            settings.assistance_email_immediate = request.form.get('assistance_email_immediate') == 'on'
            
            # Update reminder settings
            settings.reminder_email_enabled = request.form.get('reminder_email_enabled') == 'on'
            settings.reminder_days_before = int(request.form.get('reminder_days_before', 7))
            
            db.session.commit()
            flash("Settings updated successfully!", "success")
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating settings: {str(e)}", "danger")
            
        return redirect(url_for('admin.system_settings'))
    
    return render_template("admin/system_settings.html", settings=settings)


@admin_bp.route("/send-progress-report", methods=["POST"])
@login_required
def send_progress_report_now():
    """Manually trigger progress report email"""
    try:
        current_app.logger.info("Starting progress report send...")
        from app.utils.email_reports import send_progress_report
        
        current_app.logger.info("Calling send_progress_report()...")
        send_progress_report()
        current_app.logger.info("Progress report sent successfully")
        flash("✅ Progress report sent successfully!", "success")
            
    except Exception as e:
        current_app.logger.error(f"Progress report failed: {type(e).__name__}: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        error_msg = str(e)
        if "MAIL_" in error_msg or "not configured" in error_msg.lower():
            flash(f"❌ Email Configuration Error: {error_msg}", "danger")
            flash("💡 Make sure MAIL_USE_TLS=true in Render environment variables!", "warning")
        elif "TLS" in error_msg or "SSL" in error_msg or "SMTP" in error_msg:
            flash(f"❌ SMTP Connection Error: {error_msg}", "danger")
            flash("💡 Check: Is MAIL_USE_TLS=true? Port should be 587 for TLS.", "warning")
        else:
            flash(f"❌ Error: {error_msg}", "danger")
    
    return redirect(url_for('admin.system_settings'))


@admin_bp.route("/send-reminders", methods=["POST"])
@login_required
def send_reminders_now():
    """Manually trigger due date reminder emails"""
    try:
        from app.utils.email_reports import send_due_date_reminders
        
        success = send_due_date_reminders()
        
        if success:
            flash("✅ Due date reminders sent successfully!", "success")
        else:
            flash("ℹ️ No reminders to send (no measures due in the configured timeframe).", "info")
            
    except Exception as e:
        error_msg = str(e)
        if "MAIL_" in error_msg or "not configured" in error_msg.lower():
            flash(f"❌ Email Configuration Error: {error_msg}", "danger")
            flash("💡 Make sure MAIL_USE_TLS=true in Render environment variables!", "warning")
        elif "TLS" in error_msg or "SSL" in error_msg or "SMTP" in error_msg:
            flash(f"❌ SMTP Connection Error: {error_msg}", "danger")
            flash("💡 Check: Is MAIL_USE_TLS=true? Port should be 587 for TLS.", "warning")
        else:
            flash(f"❌ Error: {error_msg}", "danger")
    
    return redirect(url_for('admin.system_settings'))


# Public endpoint for scheduled tasks (e.g., cron job, Render cron)
@admin_bp.route("/cron/send-progress-report", methods=["GET", "POST"])
def cron_send_progress_report():
    """
    Endpoint for scheduled progress report sending.
    Can be called by external cron service or Render cron jobs.
    No authentication required but should use a secret token in production.
    """
    # Optional: Check for a secret token to prevent unauthorized access
    token = request.args.get('token') or request.form.get('token')
    expected_token = current_app.config.get('CRON_SECRET_TOKEN')
    
    if expected_token and token != expected_token:
        abort(403, "Invalid token")
    
    try:
        from app.utils.email_reports import send_progress_report
        from app.models import SystemSettings
        
        settings = SystemSettings.get_settings()
        
        if not settings.progress_report_enabled:
            return jsonify({"status": "skipped", "message": "Progress reports are disabled"}), 200
        
        # Check if it's time to send based on frequency
        now = datetime.utcnow()
        last_sent = settings.last_progress_report_sent
        
        should_send = False
        
        if not last_sent:
            should_send = True
        elif settings.progress_report_frequency == 'daily':
            # Send if more than 23 hours since last send
            should_send = (now - last_sent).total_seconds() > 23 * 3600
        elif settings.progress_report_frequency == 'weekly':
            # Send if current day matches and more than 6 days since last send
            days_since = (now - last_sent).days
            current_day = now.isoweekday()  # 1=Monday, 7=Sunday
            should_send = days_since >= 6 and current_day == settings.progress_report_day
        elif settings.progress_report_frequency == 'monthly':
            # Send if current day of month matches and more than 28 days since last send
            days_since = (now - last_sent).days
            should_send = days_since >= 28 and now.day == settings.progress_report_day
        
        if should_send:
            success = send_progress_report()
            if success:
                return jsonify({"status": "success", "message": "Progress report sent"}), 200
            else:
                return jsonify({"status": "error", "message": "Failed to send report"}), 500
        else:
            return jsonify({"status": "skipped", "message": "Not time to send yet"}), 200
            
    except Exception as e:
        current_app.logger.error(f"Cron progress report error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route("/cron/send-reminders", methods=["GET", "POST"])
def cron_send_reminders():
    """
    Endpoint for scheduled due date reminder sending.
    Can be called by external cron service or Render cron jobs.
    Should be run daily to check for upcoming due dates.
    """
    # Optional: Check for a secret token to prevent unauthorized access
    token = request.args.get('token') or request.form.get('token')
    expected_token = current_app.config.get('CRON_SECRET_TOKEN')
    
    if expected_token and token != expected_token:
        abort(403, "Invalid token")
    
    try:
        from app.utils.email_reports import send_due_date_reminders
        from app.models import SystemSettings
        
        settings = SystemSettings.get_settings()
        
        if not settings.reminder_email_enabled:
            return jsonify({"status": "skipped", "message": "Reminder emails are disabled"}), 200
        
        # Send reminders (function checks if there are any due)
        success = send_due_date_reminders()
        
        if success:
            return jsonify({"status": "success", "message": "Reminders sent"}), 200
        else:
            return jsonify({"status": "skipped", "message": "No reminders to send"}), 200
            
    except Exception as e:
        current_app.logger.error(f"Cron reminders error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
