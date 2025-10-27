# Importing Required Librarires
import os #for working with fileeee paths and directories

from flask import Flask, render_template, request, redirect, url_for, flash, session
# Flask modules:
# Flask: to create the web app
# render_template: to render HTML templates
# request: to get data from forms
# redirect & url_for: to navigate between pages
# flash: to show temporary messages
# session: to store user login/session data
from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy is the ORM (Object Relational Mapper)
# It allows us to interact with the database using Python classes instead of raw SQL


# 2. Flask App & Database Setup


# Create a Flask app instance
app = Flask(__name__)

# Secret key is used by Flask to handle sessions and flash messages securely
app.secret_key = "supersecretkey"

# Ensure 'instance' folder exists

# The 'instance' folder will store our SQLite database file
basedir = os.path.abspath(os.path.dirname(__file__))  # Get the current file directory
instance_path = os.path.join(basedir, 'instance')     # Path to 'instance' folder
os.makedirs(instance_path, exist_ok=True)             # Create folder if it doesn't exist

# SQLite database setup

# Define the path for the database file
db_path = os.path.join(instance_path, 'clinic.db')
print("Database path:", db_path)  # Printing the  path to check if it's correct

# Tell SQLAlchemy where the database is
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# Disable unnecessary track modifications to save memory
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy ORM with this app
db = SQLAlchemy(app)


# Database Models

#Patient Table 

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    cnic = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(100))
    contact = db.Column(db.String(20))

#Doctor Table

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    cnic = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    specialization = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    license_number = db.Column(db.String(50))
    current_hospital = db.Column(db.String(100))
    availability = db.Column(db.String(50))

#Admin Table

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    cnic = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(100))
    contact = db.Column(db.String(20))
    position = db.Column(db.String(50))
    title = db.Column(db.String(50))

# Home page
# Shows the main index page when someone visits '/'
@app.route('/')
def home():
    return render_template('index.html')


# ------------------------------
# SIGNUP ROUTES
# ------------------------------

# Helper function to clear all login sessions
# This ensures no old user is logged in when someone signs up
def clear_sessions():
    session.pop('admin', None)
    session.pop('doctor', None)
    session.pop('patient', None)

# Patient signup route
# GET: Show signup form
# POST: Save new patient to database, show success message, and go to login
@app.route('/signup/patient', methods=['GET', 'POST'])
def signup_patient():
    clear_sessions()
    if request.method == 'POST':
        patient = Patient(
            name=request.form['name'],
            age=request.form['age'],
            gender=request.form['gender'],
            cnic=request.form['cnic'],
            email=request.form['email'],
            password=request.form['password'],
            contact=request.form['contact']
        )
        db.session.add(patient)
        db.session.commit()
        flash("Patient account created successfully!", "success")
        return redirect(url_for('login_patient'))
    return render_template('PatientSignIn.html')

# Doctor signup route
# Works the same as patient signup but saves doctor details
@app.route('/signup/doctor', methods=['GET', 'POST'])
def signup_doctor():
    clear_sessions()
    if request.method == 'POST':
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
    return render_template('DoctorSignIn.html')

# Admin signup route
# Same logic, but for creating an admin account
@app.route('/signup/admin', methods=['GET', 'POST'])
def signup_admin():
    clear_sessions()
    if request.method == 'POST':
        admin = Admin(
            name=request.form['name'],
            age=request.form['age'],
            gender=request.form['gender'],
            cnic=request.form['cnic'],
            email=request.form['email'],
            password=request.form['password'],
            contact=request.form['contact'],
            position=request.form['position'],
            title=request.form['title']
        )
        db.session.add(admin)
        db.session.commit()
        flash("Admin account created successfully!", "success")
        return redirect(url_for('login_admin'))
    return render_template('AdminSignIn.html')



# ---------- LOGIN ----------
# ------------------------------
# LOGIN ROUTES
# ------------------------------

# Patient login route
# GET: Show patient login form
# POST: Check email & password, log in if valid, clear other roles
@app.route('/login/patient', methods=['GET','POST'])
def login_patient():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if a patient with this email & password exists
        patient = Patient.query.filter_by(email=email, password=password).first()
        
        if patient:
            # Clear other roles to prevent session conflicts
            session.pop('doctor', None)
            session.pop('admin', None)
            
            # Store patient's name in session
            session['patient'] = patient.name
            
            # Show welcome message
            flash(f"Welcome, {patient.name}!", "patient")
            
            # Redirect to patient dashboard
            return redirect(url_for('dashboard_patient'))
        else:
            # If login fails, show error message
            flash("Invalid email or password", "patient")
    
    # Render login page
    return render_template('PatientLogin.html')


# Doctor login route
# Works similar to patient login
@app.route('/login/doctor', methods=['GET', 'POST'])
def login_doctor():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        doctor = Doctor.query.filter_by(email=email, password=password).first()
        
        if doctor:
            # Clear other roles
            session.pop('patient', None)
            session.pop('admin', None)
            
            # Store doctor's name in session
            session['doctor'] = doctor.name
            
            # Welcome message
            flash(f"Welcome, Dr. {doctor.name}!", "doctor")
            
            # Redirect to doctor dashboard
            return redirect(url_for('dashboard_doctor'))
        else:
            flash("Invalid email or password", "doctor")
    
    return render_template('DoctorLogin.html')


# Admin login route
# Works the same as patient/doctor login
@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        admin = Admin.query.filter_by(email=email, password=password).first()
        
        if admin:
            # Clear other roles
            session.pop('patient', None)
            session.pop('doctor', None)
            
            # Store admin's name in session
            session['admin'] = admin.name
            
            # Welcome message
            flash(f"Welcome, Admin {admin.name}!", "admin")
            
            # Redirect to admin dashboard
            return redirect(url_for('dashboard_admin'))
        else:
            flash("Invalid email or password", "admin")
    
    return render_template('AdminLogin.html')



# DASHBOARD ROUTES


# Patient dashboard
# Only accessible if the patient is logged in
# If not logged in, redirect to patient login page
@app.route('/dashboard/patient')
def dashboard_patient():
    if 'patient' not in session:
        return redirect(url_for('login_patient'))
    return render_template('PatientDashboard.html')


# Doctor dashboard
# Only accessible if the doctor is logged in
# If not logged in, redirect to doctor login page
@app.route('/dashboard/doctor')
def dashboard_doctor():
    if 'doctor' not in session:
        return redirect(url_for('login_doctor'))
    return render_template('DoctorDashboard.html')


# Admin dashboard
# Only accessible if the admin is logged in
# If not logged in, redirect to admin login page
@app.route('/dashboard/admin')
def dashboard_admin():
    if 'admin' not in session:
        return redirect(url_for('login_admin'))
    return render_template('AdminDashboard.html')



# LOGOUT ROUTE
# Clears all session data for patient, doctor, and admin
# Shows a logout message and redirects to the home page
@app.route('/logout')
def logout():
    clear_sessions()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('home'))


# RUN APP


if __name__ == '__main__':
    # Ensure database tables are created before running
    with app.app_context():
        db.create_all()
        inspector = db.inspect(db.engine)
        print("Tables in DB:", inspector.get_table_names())
    # Start the Flask app in debug mode
    app.run(debug=True)# app run nahi karraha tha thats why dala tha!!
