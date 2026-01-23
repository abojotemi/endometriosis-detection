from flask_login import UserMixin
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patients = db.relationship('Patient', backref='doctor', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    id = db.Column(db.String(20), primary_key=True, default=lambda: f"PAT-{str(uuid.uuid4())[:8].upper()}")
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False, default='Female')
    contact = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Key
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'age': self.age,
            'gender': self.gender,
            'contact': self.contact,
            'email': self.email,
            'address': self.address,
            'medical_history': self.medical_history,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'created_by': self.doctor.full_name if self.doctor else 'Unknown'
        }

        
    
class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Prediction features (matching your ML model)
    menstrual_irregularity = db.Column(db.Integer, nullable=False)  # 0 or 1
    hormone_level = db.Column(db.Integer, nullable=False)           # 0 or 1
    infertility = db.Column(db.Integer, nullable=False)             # 0 or 1
    family_history = db.Column(db.Integer, nullable=False)          # 0 or 1
    ovulation_dysfunction = db.Column(db.Integer, nullable=False)   # 0 or 1
    prior_surgery = db.Column(db.Integer, nullable=False)           # 0 or 1
    
    # Prediction results
    prediction_result = db.Column(db.Integer, nullable=False)  # 0 or 1
    probability_no_endo = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    probability_endo = db.Column(db.Float, nullable=False)     # 0.0 to 1.0
    diagnosis = db.Column(db.String(50), nullable=False)       # "Endometriosis Detected" or "Endometriosis Not Detected"
    confidence = db.Column(db.Float, nullable=False)           # 0.0 to 100.0
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref='predictions')
    doctor = db.relationship('User', backref='predictions')
    diagnosis_records = db.relationship('DiagnosisRecord', backref='prediction', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.full_name if self.patient else '',
            'prediction_result': self.prediction_result,
            'probability_no_endo': self.probability_no_endo,
            'probability_endo': self.probability_endo,
            'diagnosis': self.diagnosis,
            'confidence': self.confidence,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'doctor_name': self.doctor.full_name if self.doctor else ''
        }


class DiagnosisRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey('prediction.id'), nullable=False)
    patient_id = db.Column(db.String(20), db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Diagnosis information
    diagnosis_text = db.Column(db.String(100), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    probability_positive = db.Column(db.Float, nullable=False)
    probability_negative = db.Column(db.Float, nullable=False)
    
    # Clinical notes
    clinical_notes = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    
    # Status tracking
    status = db.Column(db.String(20), default='Active', nullable=False)  # Active, Archived, Reviewed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref='diagnosis_records')
    doctor = db.relationship('User', backref='diagnosis_records')
    
    def to_dict(self):
        # Get patient name safely
        try:
            patient_name = ''
            if self.patient:
                patient_name = self.patient.full_name
        except:
            patient_name = ''
        
        # Get doctor name safely
        try:
            doctor_name = ''
            if self.doctor:
                doctor_name = self.doctor.full_name
        except:
            doctor_name = ''
        
        return {
            'id': self.id,
            'prediction_id': self.prediction_id,
            'patient_id': self.patient_id,
            'patient_name': patient_name,
            'doctor_name': doctor_name,
            'diagnosis_text': self.diagnosis_text,
            'confidence_score': self.confidence_score,
            'probability_positive': self.probability_positive,
            'probability_negative': self.probability_negative,
            'clinical_notes': self.clinical_notes,
            'recommendations': self.recommendations,
            'status': self.status,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else '',
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else ''
        }
    