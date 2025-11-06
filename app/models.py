# app/models.py
from __future__ import annotations
from datetime import datetime, date

from flask_login import UserMixin
from app.extensions import db


# ---------- Mixins ----------
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# ---------- User ----------
class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="company")  # 'admin' | 'company'
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    company = db.relationship("Company", back_populates="users")

    # attachments this user uploaded (optional)
    uploads = db.relationship(
        "Attachment",
        back_populates="uploader",
        foreign_keys="Attachment.uploaded_by",
        lazy="select",
    )

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


# ---------- Company ----------
class Company(TimestampMixin, db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, index=True, nullable=False)
    region = db.Column(db.String(120))
    industry_category = db.Column(db.String(120))
    tech_resources = db.Column(db.Text)    # NEW
    human_resources = db.Column(db.Text)   # NEW
    membership = db.Column(db.String(32))  # e.g., 'Member' / 'Non-member'
    phone = db.Column(db.String(32))  # <-- Added phone field

    # Benchmarking reminder settings
    benchmarking_reminder_months = db.Column(db.Integer, default=12)  # Remind every X months
    last_benchmarking_reminder = db.Column(db.DateTime)  # Last time reminder was sent
    next_benchmarking_due = db.Column(db.DateTime)  # When next update is due

    users = db.relationship("User", back_populates="company", lazy="select")
    assignments = db.relationship(
        "MeasureAssignment",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    # Historical benchmarking data relationship
    benchmarks = db.relationship(
        "CompanyBenchmark",
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="CompanyBenchmark.data_year.asc()",
        lazy="select",
    )

    def get_latest_benchmark(self):
        """Get the most recent benchmark data"""
        return CompanyBenchmark.query.filter_by(company_id=self.id).order_by(CompanyBenchmark.data_year.desc()).first()
    
    def get_baseline_benchmark(self):
        """Get the earliest benchmark data (baseline)"""
        return CompanyBenchmark.query.filter_by(company_id=self.id).order_by(CompanyBenchmark.data_year.asc()).first()

    def __repr__(self) -> str:
        return f"<Company {self.name}>"


# ---------- CompanyBenchmark ----------
class CompanyBenchmark(TimestampMixin, db.Model):
    """Historical benchmarking data for companies"""
    __tablename__ = "company_benchmarks"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    
    # Year this data represents
    data_year = db.Column(db.Integer, nullable=False)
    
    # Who entered this data and when
    entered_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    entered_by_role = db.Column(db.String(32), nullable=False)  # 'admin' or 'company'
    
    # Financial metrics
    turnover = db.Column(db.String(50))
    
    # Production metrics
    tools_produced = db.Column(db.Integer)
    
    # Performance metrics
    on_time_delivery = db.Column(db.String(10))  # e.g., "90%"
    export_percentage = db.Column(db.String(10))  # e.g., "15%"
    
    # Human resources metrics
    employees = db.Column(db.Integer)
    apprentices = db.Column(db.Integer)
    artisans = db.Column(db.Integer)
    master_artisans = db.Column(db.Integer)
    engineers = db.Column(db.Integer)
    
    # Additional notes/comments
    notes = db.Column(db.Text)
    
    # Relationships
    company = db.relationship("Company", back_populates="benchmarks")
    entered_by = db.relationship("User", foreign_keys=[entered_by_id])
    
    # Ensure unique year per company
    __table_args__ = (
        db.UniqueConstraint("company_id", "data_year", name="uq_company_benchmark_year"),
    )
    
    def __repr__(self) -> str:
        return f"<CompanyBenchmark {self.company_id} year={self.data_year}>"

# ---------- Measure ----------
class Measure(TimestampMixin, db.Model):
    __tablename__ = "measures"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, index=True, nullable=False)
    measure_detail = db.Column(db.Text)  # renamed from description

    target = db.Column(db.Text)
    departments = db.Column(db.String(255))
    responsible = db.Column(db.String(255))
    participants = db.Column(db.String(255))

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    order = db.Column(db.Integer, default=0)  # Add this line

    # Ensure cascades are properly set
    assignments = db.relationship(
        "MeasureAssignment",
        back_populates="measure",
        cascade="all, delete-orphan",
        lazy="select",
    )
    steps = db.relationship(
        "MeasureStep",
        back_populates="measure",
        cascade="all, delete-orphan",
        order_by="MeasureStep.step.asc()",
        lazy="select",
    )

    # Fix the Measure model's relationship to steps
    step_items = db.relationship('Step', back_populates='measure', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<Measure {self.name}>"


# ---------- MeasureStep (default step templates) ----------
class MeasureStep(TimestampMixin, db.Model):
    __tablename__ = "measure_steps"

    id = db.Column(db.Integer, primary_key=True)
    measure_id = db.Column(db.Integer, db.ForeignKey("measures.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    step = db.Column(db.Integer, default=0, nullable=False)  # renamed from order_index

    # Fix the MeasureStep model's relationship
    measure = db.relationship('Measure', back_populates='steps')

    def __repr__(self) -> str:
        return f"<MeasureStep m={self.measure_id} {self.title!r}#{self.step}>"


# ---------- MeasureAssignment ----------
class MeasureAssignment(TimestampMixin, db.Model):
    __tablename__ = "measure_assignments"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    measure_id = db.Column(db.Integer, db.ForeignKey("measures.id"), nullable=False, index=True)

    status = db.Column(db.String(32), nullable=False, default="In Progress")
    urgency = db.Column(db.Integer, default=1)  # 1=Low, 2=Medium, 3=High
    order = db.Column(db.Integer, default=0)  # For ordering assignments within a company
    
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    due_at = db.Column(db.DateTime)
    
    # snapshot of measure meta at assignment time
    target = db.Column(db.Text)
    departments = db.Column(db.String(255))
    responsible = db.Column(db.String(255))
    participants = db.Column(db.String(255))

    company = db.relationship("Company", back_populates="assignments")
    measure = db.relationship("Measure", back_populates="assignments")
    steps = db.relationship(
        "AssignmentStep",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="AssignmentStep.step.asc()",
        lazy="select",
    )
    attachments = db.relationship(
        "Attachment",
        back_populates="assignment",
        cascade="all, delete-orphan",
        lazy="select",
    )
    reports = db.relationship(
        "AssignmentReport",
        back_populates="assignment",
        cascade="all, delete-orphan",
        lazy="select",
    )
    assistance_requests = db.relationship(
        "AssistanceRequest",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="AssistanceRequest.requested_at.desc()",
        lazy="select",
    )

    @property
    def is_overdue(self):
        from datetime import datetime
        return self.due_at and self.status != "Completed" and self.due_at < datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Assignment c={self.company_id} m={self.measure_id} status={self.status}>"


# ---------- AssignmentStep (actual steps for an assignment) ----------
class AssignmentStep(TimestampMixin, db.Model):
    __tablename__ = "assignment_steps"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("measure_assignments.id"), nullable=False, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    step = db.Column(db.Integer, default=0, nullable=False)  # renamed from order_index

    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # This field is required by the sorting logic in your routes.
    order_index = db.Column(db.Integer, default=0, nullable=True)  # Changed to nullable=True for migration compatibility

    assignment = db.relationship("MeasureAssignment", back_populates="steps")
    attachments = db.relationship(
        "Attachment",
        back_populates="step",
        cascade="all, delete-orphan",
        lazy="select",
    )
    comments = db.relationship(
        "StepComment",
        back_populates="step",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Step {self.id} a={self.assignment_id} {self.title!r}>"


# ---------- Attachment ----------
class Attachment(TimestampMixin, db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)

    # links
    step_id = db.Column(db.Integer, db.ForeignKey("assignment_steps.id"), index=True, nullable=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("measure_assignments.id"), index=True, nullable=True)

    # file info
    filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(512), nullable=False)   # actual column in DB
    mimetype = db.Column(db.String(128))
    size_bytes = db.Column(db.Integer)

    # audit
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=True)

    # relationships
    step = db.relationship("AssignmentStep", back_populates="attachments")
    assignment = db.relationship("MeasureAssignment", back_populates="attachments")
    uploader = db.relationship("User", back_populates="uploads", foreign_keys=[uploaded_by])

    # alias for legacy code that references .filepath
    @property
    def filepath(self) -> str:
        return self.storage_path

    @filepath.setter
    def filepath(self, v: str) -> None:
        self.storage_path = v

    def __repr__(self) -> str:
        return f"<Attachment {self.filename}>"

# ---------- Step (new model for measure steps) ----------
class Step(TimestampMixin, db.Model):
    """Model for measure steps"""
    __tablename__ = 'steps'
    
    id = db.Column(db.Integer, primary_key=True)
    measure_id = db.Column(db.Integer, db.ForeignKey('measures.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    
    # Relationship to parent measure
    measure = db.relationship('Measure', back_populates='step_items')
    
    def __repr__(self):
        return f'<Step {self.id}: {self.title}>'

# ---------- Notification ----------
class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    company_id   = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False, index=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True,  index=True)  # optional
    assignment_id= db.Column(db.Integer, db.ForeignKey("measure_assignments.id"), nullable=True, index=True)

    kind    = db.Column(db.String(32),  nullable=False, index=True)  # e.g., 'due_7d'
    subject = db.Column(db.String(255), nullable=False)
    body    = db.Column(db.Text,        nullable=False)

    notify_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    read_at       = db.Column(db.DateTime, nullable=True)

    company    = db.relationship("Company")
    user       = db.relationship("User")
    assignment = db.relationship("MeasureAssignment")

    __table_args__ = (
        db.UniqueConstraint("assignment_id", "kind", name="uq_notification_assignment_kind"),
    )

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def __repr__(self) -> str:
        return f"<Notification {self.kind} company={self.company_id} assignment={self.assignment_id}>"

# ---------- NotificationConfig (singleton) ----------
class NotificationConfig(TimestampMixin, db.Model):
    __tablename__ = "notification_config"

    id = db.Column(db.Integer, primary_key=True)  # singleton row id=1
    lead_days = db.Column(db.Integer, nullable=False, default=7)       # how many days before due date
    send_hour_utc = db.Column(db.Integer, nullable=False, default=8)   # 0..23
    send_minute_utc = db.Column(db.Integer, nullable=False, default=0) 
    
    def __repr__(self) -> str:
        return f"<NotificationConfig days={self.lead_days} at {self.send_hour_utc:02d}:{self.send_minute_utc:02d}Z>"
    
# ---------- AssistanceRequest ----------
class AssistanceRequest(TimestampMixin, db.Model):
    __tablename__ = "assistance_requests"

    id = db.Column(db.Integer, primary_key=True)

    assignment_id = db.Column(
        db.Integer, db.ForeignKey("measure_assignments.id"), nullable=False, index=True
    )
    requested_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    prev_status = db.Column(db.String(32))  # status before switching to "Needs Assistance"
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 'open' | 'resolved' | 'not_resolved'
    decision = db.Column(db.String(16), default="open", nullable=False, index=True)
    decided_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decision_notes = db.Column(db.Text, nullable=True)

    assignment = db.relationship("MeasureAssignment", back_populates="assistance_requests")
    requested_by = db.relationship("User", foreign_keys=[requested_by_id])
    decided_by = db.relationship("User", foreign_keys=[decided_by_id])

    def is_open(self) -> bool:
        return (self.decision or "open") == "open"


# attach relationship on MeasureAssignment (add inside the class body)
MeasureAssignment.assistance_requests = db.relationship(
    "AssistanceRequest",
    back_populates="assignment",
    cascade="all, delete-orphan",
    order_by="AssistanceRequest.requested_at.desc()",
    lazy="select",
)

# ---------- StepComment ----------
class StepComment(TimestampMixin, db.Model):
    __tablename__ = "step_comments"

    id = db.Column(db.Integer, primary_key=True)
    step_id = db.Column(db.Integer, db.ForeignKey("assignment_steps.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)

    step = db.relationship("AssignmentStep", back_populates="comments")
    user = db.relationship("User")

    def __repr__(self) -> str:
        return f"<StepComment {self.id} step={self.step_id}>"


# ---------- AssignmentReport ----------
class AssignmentReport(TimestampMixin, db.Model):
    __tablename__ = "assignment_reports"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("measure_assignments.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    
    assignment = db.relationship("MeasureAssignment", back_populates="reports")
    user = db.relationship("User")
    
    def __repr__(self) -> str:
        return f"<AssignmentReport {self.id} assignment={self.assignment_id}>"

# ---------- Activity Log ----------
class ActivityLog(TimestampMixin, db.Model):
    __tablename__ = "activity_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)  # 'create', 'update', 'delete', 'login', 'logout'
    entity_type = db.Column(db.String(64), nullable=True, index=True)  # 'measure', 'company', 'user', 'assignment', etc.
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    entity_name = db.Column(db.String(255), nullable=True)  # Store name for reference even if entity deleted
    details = db.Column(db.Text, nullable=True)  # JSON or text details about the action
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    user = db.relationship("User", backref="activity_logs")
    
    def __repr__(self) -> str:
        return f"<ActivityLog {self.id} {self.user_id} {self.action} {self.entity_type}>"

# ---------- Benchmarking ----------