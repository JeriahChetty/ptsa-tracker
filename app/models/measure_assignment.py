from .. import db

class MeasureAssignment(db.Model):
    __tablename__ = 'measure_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    # ...existing code...
    
    # Add the missing urgency column
    urgency = db.Column(db.String(20), default='normal')
    
    # ...existing code...