# Importing Required Libraries
import os
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
except ImportError:
    print("Warning: reportlab not installed. PDF features will not work.")

# # ==================== FLASK APP SETUP ====================

# app = Flask(__name__)
# app.secret_key = "supersecretkey"

# # Database setup
# basedir = os.path.abspath(os.path.dirname(__file__))
# instance_path = os.path.join(basedir, 'instance')
# os.makedirs(instance_path, exist_ok=True)

# # Upload folder setup
# UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
# PATIENT_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'patients')
# os.makedirs(PATIENT_UPLOAD_FOLDER, exist_ok=True)

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# db_path = os.path.join(instance_path, 'clinic.db')
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)

# ==================== FLASK APP SETUP ====================

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database setup
basedir = os.path.abspath(os.path.dirname(__file__))

# Upload folder setup
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
PATIENT_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'patients')
os.makedirs(PATIENT_UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# 🔹 IMPORTANT: Point directly to the edited DB file
db_path = os.path.join(basedir, 'clinic.db')  # changed from instance_path
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ==================== DATABASE MODELS ====================

# Patient Table (ENHANCED)
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    cnic = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    
    # NEW FIELDS for patient portal
    address = db.Column(db.String(200))
    blood_group = db.Column(db.String(5))
    profile_picture = db.Column(db.String(200))
    emergency_contact = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True, cascade='all, delete-orphan')
    vitals = db.relationship('Vitals', backref='patient', lazy=True, cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True, cascade='all, delete-orphan')

# Doctor Table (ENHANCED)
class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    cnic = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    current_hospital = db.Column(db.String(100))
    availability = db.Column(db.String(50))
    
    # NEW FIELD
    consultation_fee = db.Column(db.Float, default=2000.0)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    medical_records = db.relationship('MedicalRecord', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)

# Admin Table (Keep as is)
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    cnic = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(50))

# NEW MODELS FOR PATIENT PORTAL

class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    symptoms = db.Column(db.Text)
    priority = db.Column(db.String(20), default='normal')  # emergency, urgent, normal
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MedicalRecord(db.Model):
    __tablename__ = 'medical_record'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment = db.Column(db.Text)
    prescription = db.Column(db.Text)
    vitals = db.Column(db.Text)  # JSON string
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)

class Vitals(db.Model):
    __tablename__ = 'vitals'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    heart_rate = db.Column(db.Integer)  # bpm
    blood_pressure_systolic = db.Column(db.Integer)  # mmHg
    blood_pressure_diastolic = db.Column(db.Integer)  # mmHg
    temperature = db.Column(db.Float)  # °F
    oxygen_saturation = db.Column(db.Integer)  # %
    weight = db.Column(db.Float)  # kg
    height = db.Column(db.Float)  # cm
    bmi = db.Column(db.Float)
    notes = db.Column(db.Text)

class Prescription(db.Model):
    __tablename__ = 'prescription'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    medication = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text)
    refills = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

# ==================== HELPER FUNCTIONS ====================

def clear_sessions():
    """Clear all login sessions"""
    session.pop('admin', None)
    session.pop('doctor', None)
    session.pop('patient', None)
    session.pop('patient_id', None)
    session.pop('user_type', None)

def patient_login_required(f):
    """Decorator to require patient login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'patient' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login_patient'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_bmi(weight, height):
    """Calculate BMI from weight (kg) and height (cm)"""
    if weight and height and height > 0:
        height_m = height / 100
        return round(weight / (height_m ** 2), 2)
    return None

def check_vital_alerts(vitals):
    """Check if any vitals are in abnormal range"""
    alerts = []
    
    if vitals.heart_rate:
        if vitals.heart_rate < 60:
            alerts.append(('Heart Rate', 'Low', vitals.heart_rate))
        elif vitals.heart_rate > 100:
            alerts.append(('Heart Rate', 'High', vitals.heart_rate))
    
    if vitals.blood_pressure_systolic and vitals.blood_pressure_diastolic:
        if vitals.blood_pressure_systolic > 140 or vitals.blood_pressure_diastolic > 90:
            alerts.append(('Blood Pressure', 'High', f"{vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic}"))
        elif vitals.blood_pressure_systolic < 90 or vitals.blood_pressure_diastolic < 60:
            alerts.append(('Blood Pressure', 'Low', f"{vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic}"))
    
    if vitals.temperature:
        if vitals.temperature > 100.4:
            alerts.append(('Temperature', 'Fever', vitals.temperature))
        elif vitals.temperature < 97:
            alerts.append(('Temperature', 'Low', vitals.temperature))
    
    if vitals.oxygen_saturation:
        if vitals.oxygen_saturation < 95:
            alerts.append(('Oxygen Saturation', 'Low', vitals.oxygen_saturation))
    
    return alerts

# ==================== EXISTING ROUTES (Keep as is) ====================

@app.route('/')
def home():
    return render_template('index.html')

# Patient Signup (KEEP ORIGINAL)
@app.route('/signup/patient', methods=['GET', 'POST'])
def signup_patient():
    clear_sessions()
    if request.method == 'POST':
        try:
            patient = Patient(
                name=request.form['name'],
                age=request.form['age'],
                gender=request.form['gender'],
                cnic=request.form['cnic'],
                email=request.form['email'],
                password=request.form['password'],  # In production, use hashing
                contact=request.form['contact']
            )
            db.session.add(patient)
            db.session.commit()
            flash("Patient account created successfully!", "success")
            return redirect(url_for('login_patient'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "error")
    return render_template('PatientSignIn.html')

# Doctor Signup (KEEP ORIGINAL)
@app.route('/signup/doctor', methods=['GET', 'POST'])
def signup_doctor():
    clear_sessions()
    if request.method == 'POST':
        try:
            doctor = Doctor(
                name=request.form['name'],
                age=request.form['age'],
                gender=request.form['gender'],
                cnic=request.form['cnic'],
                email=request.form['email'],
                password=request.form['password'],
                contact=request.form['contact'],
                specialization=request.form['specialization'],
                qualification=request.form['qualification'],
                experience_years=request.form['experience_years'],
                license_number=request.form['license_number'],
                current_hospital=request.form['current_hospital'],
                availability=request.form['availability']
            )
            db.session.add(doctor)
            db.session.commit()
            flash("Doctor account created successfully!", "success")
            return redirect(url_for('login_doctor'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "error")
    return render_template('DoctorSignIn.html')

# Admin Signup (KEEP ORIGINAL)
@app.route('/signup/admin', methods=['GET', 'POST'])
def signup_admin():
    clear_sessions()
    if request.method == 'POST':
        try:
            admin = Admin(
                name=request.form['name'],
                age=request.form['age'],
                gender=request.form['gender'],
                cnic=request.form['cnic'],
                email=request.form['email'],
                password=request.form['password'],
                contact=request.form['contact'],
                position=request.form['position'],
                title=request.form.get('title', '')
            )
            db.session.add(admin)
            db.session.commit()
            flash("Admin account created successfully!", "success")
            return redirect(url_for('login_admin'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "error")
    return render_template('AdminSignIn.html')

# Patient Login (ENHANCED)
@app.route('/login/patient', methods=['GET','POST'])
def login_patient():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        patient = Patient.query.filter_by(email=email, password=password).first()
        
        if patient:
            session.pop('doctor', None)
            session.pop('admin', None)
            session['patient'] = patient.name
            session['patient_id'] = patient.id
            session['user_type'] = 'patient'
            
            flash(f"Welcome, {patient.name}!", "success")
            return redirect(url_for('patient_dashboard'))
        else:
            flash("Invalid email or password", "error")
    
    return render_template('PatientLogin.html')

# Doctor Login (KEEP ORIGINAL)
@app.route('/login/doctor', methods=['GET', 'POST'])
def login_doctor():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        doctor = Doctor.query.filter_by(email=email, password=password).first()
        
        if doctor:
            session.pop('patient', None)
            session.pop('admin', None)
            session['doctor'] = doctor.name
            session['doctor_id'] = doctor.id
            session['user_type'] = 'doctor'
            
            flash(f"Welcome, Dr. {doctor.name}!", "success")
            return redirect(url_for('dashboard_doctor'))
        else:
            flash("Invalid email or password", "error")
    
    return render_template('DoctorLogin.html')

# Admin Login (KEEP ORIGINAL)
@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        admin = Admin.query.filter_by(email=email, password=password).first()
        
        if admin:
            session.pop('patient', None)
            session.pop('doctor', None)
            session['admin'] = admin.name
            session['admin_id'] = admin.id
            session['user_type'] = 'admin'
            
            flash(f"Welcome, Admin {admin.name}!", "success")
            return redirect(url_for('dashboard_admin'))
        else:
            flash("Invalid email or password", "error")
    
    return render_template('AdminLogin.html')

# Old Dashboards (KEEP for backward compatibility)
@app.route('/dashboard/patient')
def dashboard_patient_old():
    if 'patient' not in session:
        return redirect(url_for('login_patient'))
    return redirect(url_for('patient_dashboard'))

@app.route('/dashboard/doctor')
def dashboard_doctor():
    if 'doctor' not in session:
        return redirect(url_for('login_doctor'))
    return render_template('DoctorDashboard.html')

@app.route('/dashboard/admin')
def dashboard_admin():
    if 'admin' not in session:
        return redirect(url_for('login_admin'))
    return render_template('AdminDashboard.html')

@app.route('/logout')
def logout():
    clear_sessions()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('home'))

# ==================== NEW PATIENT PORTAL ROUTES ====================

@app.route('/patient/dashboard')
@patient_login_required
def patient_dashboard():
    patient_id = session.get('patient_id')
    patient = Patient.query.get_or_404(patient_id)
    
    # Get upcoming appointments
    today = datetime.now().date()
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.date >= today,
        Appointment.status == 'scheduled'
    ).order_by(Appointment.date, Appointment.time).limit(5).all()
    
    # Get recent medical records
    recent_records = MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.visit_date.desc()).limit(5).all()
    
    # Get latest vitals
    latest_vitals = Vitals.query.filter_by(
        patient_id=patient_id
    ).order_by(Vitals.date.desc()).first()
    
    # Get active prescriptions
    active_prescriptions = Prescription.query.filter_by(
        patient_id=patient_id,
        active=True
    ).order_by(Prescription.date.desc()).limit(5).all()
    
    # Check for vital alerts
    vital_alerts = []
    if latest_vitals:
        vital_alerts = check_vital_alerts(latest_vitals)
    
    return render_template('patient/dashboard.html',
                         patient=patient,
                         upcoming_appointments=upcoming_appointments,
                         recent_records=recent_records,
                         latest_vitals=latest_vitals,
                         active_prescriptions=active_prescriptions,
                         vital_alerts=vital_alerts,
                         now=datetime.now())

@app.route('/patient/book-appointment', methods=['GET', 'POST'])
@patient_login_required
def book_appointment():
    patient_id = session.get('patient_id')
    
    if request.method == 'POST':
        try:
            doctor_id = request.form.get('doctor_id')
            date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            time = request.form.get('time')
            symptoms = request.form.get('symptoms')
            priority = request.form.get('priority', 'normal')
            
            # Check if slot is available
            existing = Appointment.query.filter_by(
                doctor_id=doctor_id,
                date=date,
                time=time,
                status='scheduled'
            ).first()
            
            if existing:
                flash('This time slot is already booked. Please choose another time.', 'error')
                return redirect(url_for('book_appointment'))
            
            appointment = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                date=date,
                time=time,
                symptoms=symptoms,
                priority=priority,
                status='scheduled'
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('view_appointments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error booking appointment: {str(e)}', 'error')
    
    # GET request
    doctors = Doctor.query.all()
    specializations = db.session.query(Doctor.specialization).distinct().all()
    specializations = [s[0] for s in specializations]
    
    return render_template('patient/book-appointment.html',
                         doctors=doctors,
                         specializations=specializations,
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/patient/appointments')
@patient_login_required
def view_appointments():
    patient_id = session.get('patient_id')
    
    all_appointments = Appointment.query.filter_by(
        patient_id=patient_id
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    
    today = datetime.now().date()
    
    upcoming = [a for a in all_appointments if a.date >= today and a.status == 'scheduled']
    past = [a for a in all_appointments if a.date < today or a.status in ['completed', 'cancelled']]
    
    return render_template('patient/view-appointments.html',
                         upcoming_appointments=upcoming,
                         past_appointments=past)

@app.route('/patient/appointment/<int:appointment_id>/cancel', methods=['POST'])
@patient_login_required
def cancel_appointment(appointment_id):
    patient_id = session.get('patient_id')
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient_id
    ).first_or_404()
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('view_appointments'))

@app.route('/patient/medical-records')
@patient_login_required
def medical_records():
    patient_id = session.get('patient_id')
    
    records = MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.visit_date.desc()).all()
    
    return render_template('patient/medical-records.html', records=records)

@app.route('/patient/vitals', methods=['GET', 'POST'])
@patient_login_required
def patient_vitals():
    patient_id = session.get('patient_id')
    
    if request.method == 'POST':
        try:
            weight = float(request.form.get('weight')) if request.form.get('weight') else None
            height = float(request.form.get('height')) if request.form.get('height') else None
            
            bmi = calculate_bmi(weight, height) if weight and height else None
            
            vitals = Vitals(
                patient_id=patient_id,
                heart_rate=int(request.form.get('heart_rate')) if request.form.get('heart_rate') else None,
                blood_pressure_systolic=int(request.form.get('bp_systolic')) if request.form.get('bp_systolic') else None,
                blood_pressure_diastolic=int(request.form.get('bp_diastolic')) if request.form.get('bp_diastolic') else None,
                temperature=float(request.form.get('temperature')) if request.form.get('temperature') else None,
                oxygen_saturation=int(request.form.get('oxygen_saturation')) if request.form.get('oxygen_saturation') else None,
                weight=weight,
                height=height,
                bmi=bmi,
                notes=request.form.get('notes')
            )
            
            db.session.add(vitals)
            db.session.commit()
            
            # Check for alerts
            alerts = check_vital_alerts(vitals)
            if alerts:
                alert_msg = "Warning: " + ", ".join([f"{a[0]} is {a[1]}" for a in alerts])
                flash(alert_msg, 'warning')
            else:
                flash('Vitals recorded successfully!', 'success')
            
            return redirect(url_for('patient_vitals'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording vitals: {str(e)}', 'error')
    
    # GET request
    all_vitals = Vitals.query.filter_by(
        patient_id=patient_id
    ).order_by(Vitals.date.desc()).all()
    
    return render_template('patient/vitals.html', vitals_list=all_vitals)

@app.route('/patient/prescriptions')
@patient_login_required
def prescriptions():
    patient_id = session.get('patient_id')
    
    active = Prescription.query.filter_by(
        patient_id=patient_id,
        active=True
    ).order_by(Prescription.date.desc()).all()
    
    past = Prescription.query.filter_by(
        patient_id=patient_id,
        active=False
    ).order_by(Prescription.date.desc()).all()
    
    return render_template('patient/prescriptions.html',
                         active_prescriptions=active,
                         past_prescriptions=past)

@app.route('/patient/profile', methods=['GET', 'POST'])
@patient_login_required
def patient_profile():
    patient_id = session.get('patient_id')
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        try:
            patient.name = request.form.get('name')
            patient.age = int(request.form.get('age'))
            patient.gender = request.form.get('gender')
            patient.contact = request.form.get('contact')
            patient.address = request.form.get('address')
            patient.blood_group = request.form.get('blood_group')
            patient.emergency_contact = request.form.get('emergency_contact')
            
            # Handle profile picture
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename:
                    filename = secure_filename(f"patient_{patient_id}_{file.filename}")
                    file.save(os.path.join(PATIENT_UPLOAD_FOLDER, filename))
                    patient.profile_picture = filename
            
            # Change password
            if request.form.get('new_password'):
                patient.password = request.form.get('new_password')
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('patient_profile'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('patient/profile.html', patient=patient)

# ==================== API ROUTES ====================

@app.route('/api/doctors/available')
@patient_login_required
def available_doctors():
    date_str = request.args.get('date')
    specialization = request.args.get('specialization')
    
    query = Doctor.query
    
    if specialization:
        query = query.filter_by(specialization=specialization)
    
    doctors = query.all()
    
    result = []
    for doctor in doctors:
        booked_slots = []
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appointments = Appointment.query.filter_by(
                doctor_id=doctor.id,
                date=date,
                status='scheduled'
            ).all()
            booked_slots = [a.time for a in appointments]
        
        result.append({
            'id': doctor.id,
            'name': doctor.name,
            'specialization': doctor.specialization,
            'qualification': doctor.qualification,
            'experience_years': doctor.experience_years,
            'consultation_fee': doctor.consultation_fee,
            'booked_slots': booked_slots
        })
    
    return jsonify(result)

@app.route('/api/patient/vitals')
@patient_login_required
def vitals_api():
    patient_id = session.get('patient_id')
    days = request.args.get('days', 30, type=int)
    
    start_date = datetime.now() - timedelta(days=days)
    vitals = Vitals.query.filter(
        Vitals.patient_id == patient_id,
        Vitals.date >= start_date
    ).order_by(Vitals.date).all()
    
    data = {
        'dates': [],
        'heart_rate': [],
        'bp_systolic': [],
        'bp_diastolic': [],
        'temperature': [],
        'oxygen_saturation': [],
        'weight': [],
        'bmi': []
    }
    
    for v in vitals:
        data['dates'].append(v.date.strftime('%Y-%m-%d'))
        data['heart_rate'].append(v.heart_rate)
        data['bp_systolic'].append(v.blood_pressure_systolic)
        data['bp_diastolic'].append(v.blood_pressure_diastolic)
        data['temperature'].append(v.temperature)
        data['oxygen_saturation'].append(v.oxygen_saturation)
        data['weight'].append(v.weight)
        data['bmi'].append(v.bmi)
    
    return jsonify(data)

@app.route('/api/patient/appointments')
@patient_login_required
def appointments_api():
    patient_id = session.get('patient_id')
    
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        status='scheduled'
    ).order_by(Appointment.date, Appointment.time).all()
    
    data = []
    priority_order = {'emergency': 1, 'urgent': 2, 'normal': 3}
    
    for a in appointments:
        data.append({
            'id': a.id,
            'doctor': a.doctor.name,
            'date': a.date.strftime('%Y-%m-%d'),
            'time': a.time,
            'priority': a.priority,
            'priority_value': priority_order.get(a.priority, 3),
            'symptoms': a.symptoms
        })
    
    data.sort(key=lambda x: (x['date'], x['priority_value'], x['time']))
    
    return jsonify(data)

# ==================== PDF GENERATION ====================

@app.route('/patient/download-medical-summary')
@patient_login_required
def download_medical_summary():
    try:
        patient_id = session.get('patient_id')
        patient = Patient.query.get_or_404(patient_id)
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        p.setFont("Helvetica-Bold", 20)
        p.drawString(1*inch, height - 1*inch, "Medical Summary Report")
        
        # Patient Info
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, height - 1.5*inch, "Patient Information")
        p.setFont("Helvetica", 10)
        y = height - 1.8*inch
        p.drawString(1*inch, y, f"Name: {patient.name}")
        y -= 0.2*inch
        p.drawString(1*inch, y, f"Age: {patient.age} | Gender: {patient.gender}")
        y -= 0.2*inch
        p.drawString(1*inch, y, f"Blood Group: {patient.blood_group or 'N/A'}")
        
        # Recent Records
        y -= 0.5*inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, y, "Recent Medical Records")
        p.setFont("Helvetica", 9)
        
        records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(
            MedicalRecord.visit_date.desc()
        ).limit(5).all()
        
        y -= 0.3*inch
        for record in records:
            if y < 2*inch:
                p.showPage()
                y = height - 1*inch
            
            p.drawString(1*inch, y, f"Date: {record.visit_date.strftime('%Y-%m-%d')}")
            y -= 0.15*inch
            p.drawString(1*inch, y, f"Diagnosis: {record.diagnosis[:60]}")
            y -= 0.15*inch
            p.drawString(1*inch, y, f"Doctor: {record.doctor.name}")
            y -= 0.3*inch
        
        p.save()
        buffer.seek(0)
        
        return send_file(buffer, as_attachment=True, download_name='medical_summary.pdf',
                        mimetype='application/pdf')
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('patient_dashboard'))

@app.route('/patient/download-prescription/<int:prescription_id>')
@patient_login_required
def download_prescription(prescription_id):
    try:
        patient_id = session.get('patient_id')
        prescription = Prescription.query.filter_by(
            id=prescription_id,
            patient_id=patient_id
        ).first_or_404()
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        p.setFont("Helvetica-Bold", 18)
        p.drawString(1*inch, height - 1*inch, "Prescription")
        
        # Doctor Info
        p.setFont("Helvetica-Bold", 11)
        p.drawString(1*inch, height - 1.5*inch, f"Dr. {prescription.doctor.name}")
        p.setFont("Helvetica", 9)
        p.drawString(1*inch, height - 1.7*inch, f"{prescription.doctor.specialization}")
        p.drawString(1*inch, height - 1.9*inch, f"License: {prescription.doctor.license_number}")
        
        # Patient Info
        p.setFont("Helvetica-Bold", 11)
        p.drawString(1*inch, height - 2.3*inch, "Patient Information")
        p.setFont("Helvetica", 9)
        p.drawString(1*inch, height - 2.5*inch, f"Name: {prescription.patient.name}")
        p.drawString(1*inch, height - 2.7*inch, f"Age: {prescription.patient.age}")
        p.drawString(1*inch, height - 2.9*inch, f"Date: {prescription.date.strftime('%Y-%m-%d')}")
        
        # Prescription Details
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1*inch, height - 3.4*inch, "Medication")
        p.setFont("Helvetica", 10)
        y = height - 3.7*inch
        p.drawString(1*inch, y, f"Medication: {prescription.medication}")
        y -= 0.2*inch
        p.drawString(1*inch, y, f"Dosage: {prescription.dosage}")
        y -= 0.2*inch
        p.drawString(1*inch, y, f"Frequency: {prescription.frequency}")
        y -= 0.2*inch
        p.drawString(1*inch, y, f"Duration: {prescription.duration}")
        
        if prescription.instructions:
            y -= 0.3*inch
            p.setFont("Helvetica-Bold", 10)
            p.drawString(1*inch, y, "Instructions:")
            p.setFont("Helvetica", 9)
            y -= 0.2*inch
            p.drawString(1*inch, y, prescription.instructions[:100])
        
        p.save()
        buffer.seek(0)
        
        return send_file(buffer, as_attachment=True, 
                        download_name=f'prescription_{prescription_id}.pdf',
                        mimetype='application/pdf')
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('prescriptions'))

# ==================== DATABASE INITIALIZATION ====================

def init_sample_data():
    """Initialize sample data for testing"""
    with app.app_context():
        # Create sample doctors if none exist
        if Doctor.query.count() == 0:
            doctors_data = [
                {
                    'name': 'Dr. Sarah Ahmed',
                    'age': 42,
                    'gender': 'Female',
                    'cnic': '42301-1234567-8',
                    'email': 'sarah.ahmed@clinic.com',
                    'password': 'doctor123',
                    'contact': '0300-1234567',
                    'specialization': 'Cardiology',
                    'qualification': 'MBBS, FCPS (Cardiology)',
                    'experience_years': 15,
                    'license_number': 'PMC-12345',
                    'current_hospital': 'City General Hospital',
                    'availability': 'Mon-Fri: 9AM-5PM',
                    'consultation_fee': 2500.0
                },
                {
                    'name': 'Dr. Ali Hassan',
                    'age': 38,
                    'gender': 'Male',
                    'cnic': '42301-7654321-9',
                    'email': 'ali.hassan@clinic.com',
                    'password': 'doctor123',
                    'contact': '0300-7654321',
                    'specialization': 'Neurology',
                    'qualification': 'MBBS, FCPS (Neurology)',
                    'experience_years': 12,
                    'license_number': 'PMC-12346',
                    'current_hospital': 'City General Hospital',
                    'availability': 'Mon-Fri: 10AM-6PM',
                    'consultation_fee': 3000.0
                },
                {
                    'name': 'Dr. Fatima Khan',
                    'age': 35,
                    'gender': 'Female',
                    'cnic': '42301-1111111-1',
                    'email': 'fatima.khan@clinic.com',
                    'password': 'doctor123',
                    'contact': '0300-1111111',
                    'specialization': 'Pediatrics',
                    'qualification': 'MBBS, DCH, FCPS (Pediatrics)',
                    'experience_years': 10,
                    'license_number': 'PMC-12347',
                    'current_hospital': 'Children Hospital',
                    'availability': 'Mon-Sat: 8AM-4PM',
                    'consultation_fee': 2000.0
                },
                {
                    'name': 'Dr. Ahmed Raza',
                    'age': 45,
                    'gender': 'Male',
                    'cnic': '42301-2222222-2',
                    'email': 'ahmed.raza@clinic.com',
                    'password': 'doctor123',
                    'contact': '0300-2222222',
                    'specialization': 'Orthopedics',
                    'qualification': 'MBBS, MS (Orthopedics)',
                    'experience_years': 18,
                    'license_number': 'PMC-12348',
                    'current_hospital': 'Orthopedic Center',
                    'availability': 'Mon-Fri: 2PM-8PM',
                    'consultation_fee': 2800.0
                },
                {
                    'name': 'Dr. Ayesha Malik',
                    'age': 33,
                    'gender': 'Female',
                    'cnic': '42301-3333333-3',
                    'email': 'ayesha.malik@clinic.com',
                    'password': 'doctor123',
                    'contact': '0300-3333333',
                    'specialization': 'Dermatology',
                    'qualification': 'MBBS, FCPS (Dermatology)',
                    'experience_years': 8,
                    'license_number': 'PMC-12349',
                    'current_hospital': 'Skin Care Clinic',
                    'availability': 'Tue-Sat: 11AM-7PM',
                    'consultation_fee': 2200.0
                }
            ]
            
            for doc_data in doctors_data:
                doctor = Doctor(**doc_data)
                db.session.add(doctor)
            
            db.session.commit()
            print("✅ Sample doctors created")

# ==================== RUN APP ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_sample_data()
        
        inspector = db.inspect(db.engine)
        print("📊 Tables in DB:", inspector.get_table_names())
        print("🏥 Total Doctors:", Doctor.query.count())
        print("👥 Total Patients:", Patient.query.count())
    
    app.run(debug=True)
