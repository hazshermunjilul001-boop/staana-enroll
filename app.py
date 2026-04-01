from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'staana-enroll-dev-key-2026')

# Improved DATABASE_URL handling
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    if '?' not in database_url:
        database_url += '?sslmode=require'
    elif 'sslmode' not in database_url:
        database_url += '&sslmode=require'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ====================== MODELS ======================
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lrn = db.Column(db.String(12), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.String(10), nullable=False)
    sex = db.Column(db.String(10))
    address = db.Column(db.Text)
    contact = db.Column(db.String(20))
    parent_name = db.Column(db.String(150))
    parent_contact = db.Column(db.String(20))
    enrolled = db.Column(db.Boolean, default=False)
    enrolled_at = db.Column(db.DateTime)
    photo_taken = db.Column(db.Boolean, default=False)

# ====================== ROUTES ======================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_student():
    identifier = request.form.get('identifier', '').strip()
    
    if not identifier:
        flash("Please enter LRN or Birthday (MM-DD-YYYY)", "danger")
        return redirect(url_for('home'))
    
    try:
        student = None
        # Try LRN first
        if len(identifier.replace('-', '').replace(' ', '')) == 12 and identifier.replace('-', '').replace(' ', '').isdigit():
            student = Student.query.filter_by(lrn=identifier).first()
        else:
            # Try as birth date
            student = Student.query.filter_by(birth_date=identifier).first()
        
        if not student:
            flash("No student found with that information. Please contact the school registrar.", "warning")
            return redirect(url_for('home'))
        
        # Privacy-safe preview
        preview = {
            'first_name': student.first_name,
            'last_name': student.last_name,
            'grade_level': student.grade_level,
            'section': student.section.upper(),
            'lrn': student.lrn
        }
        
        return render_template('preview.html', preview=preview, student_id=student.id)
        
    except Exception as e:
        flash(f"Database connection issue: {str(e)[:100]}... Please try again later or contact admin.", "danger")
        return redirect(url_for('home'))

@app.route('/confirm/<int:student_id>', methods=['GET', 'POST'])
def confirm_enrollment(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        
        if request.method == 'POST':
            student.address = request.form.get('address')
            student.contact = request.form.get('contact')
            student.parent_name = request.form.get('parent_name')
            student.parent_contact = request.form.get('parent_contact')
            student.enrolled = True
            student.enrolled_at = datetime.utcnow()
            
            db.session.commit()
            
            flash("Enrollment confirmed successfully!", "success")
            return render_template('confirmation.html', student=student)
        
        return render_template('update_form.html', student=student)
    except Exception as e:
        flash("Error loading student details. Please try again.", "danger")
        return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)