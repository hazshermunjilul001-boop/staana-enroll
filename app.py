from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ====================== MODELS ======================
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lrn = db.Column(db.String(12), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(50), nullable=False)  # Will be normalized to UPPER
    birth_date = db.Column(db.String(10), nullable=False)  # MM-DD-YYYY
    sex = db.Column(db.String(10))
    address = db.Column(db.Text)
    contact = db.Column(db.String(20))
    parent_name = db.Column(db.String(150))
    parent_contact = db.Column(db.String(20))
    enrolled = db.Column(db.Boolean, default=False)
    enrolled_at = db.Column(db.DateTime)
    photo_taken = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Student {self.lrn} - {self.first_name} {self.last_name}>"

# ====================== ROUTES ======================
@app.route('/')
def home():
    return render_template('index.html')

# Public Search - Privacy Safe Preview
@app.route('/search', methods=['POST'])
def search_student():
    identifier = request.form.get('identifier', '').strip()
    
    if not identifier:
        flash("Please enter LRN or Birthday (MM-DD-YYYY)", "danger")
        return redirect(url_for('home'))
    
    # Search by LRN or Birth Date
    student = None
    if len(identifier.replace('-', '')) == 12 and identifier.replace('-', '').isdigit():
        # Likely LRN
        student = Student.query.filter_by(lrn=identifier).first()
    else:
        # Try as Birth Date
        student = Student.query.filter_by(birth_date=identifier).first()
    
    if not student:
        flash("No student found with that information. Please contact the school registrar.", "warning")
        return redirect(url_for('home'))
    
    # Privacy-safe preview (only basic info)
    preview = {
        'first_name': student.first_name,
        'last_name': student.last_name,
        'grade_level': student.grade_level,
        'section': student.section.upper(),
        'lrn': student.lrn
    }
    
    return render_template('preview.html', preview=preview, student_id=student.id)

# Confirm Preview and Show Full Update Form
@app.route('/confirm/<int:student_id>', methods=['GET', 'POST'])
def confirm_enrollment(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        # Update allowed fields
        student.address = request.form.get('address')
        student.contact = request.form.get('contact')
        student.parent_name = request.form.get('parent_name')
        student.parent_contact = request.form.get('parent_contact')
        student.enrolled = True
        student.enrolled_at = datetime.utcnow()
        
        db.session.commit()
        
        flash("Enrollment confirmed successfully! You can now proceed to the school for photo taking.", "success")
        return render_template('confirmation.html', student=student)
    
    return render_template('update_form.html', student=student)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)