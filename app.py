
from flask import Flask, render_template, request, redirect, jsonify, url_for
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import jwt
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xyzabc'
app.config['MYSQL_HOST'] = 'byyw6dxjipn2owgrgz5z-mysql.services.clever-cloud.com'
app.config['MYSQL_USER'] = 'uqhbjgzshwljnej9'
app.config['MYSQL_PASSWORD'] = '3vNGCjMx5WpoD5g075ZU'
app.config['MYSQL_DB'] = 'byyw6dxjipn2owgrgz5z'
app.config['port']=3306

def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        port = app.config['port']

    )

def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def jwt_token_required(f):
    def decorator(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('index'))
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.username = data['username']
        except jwt.ExpiredSignatureError:
            return redirect(url_for('index'))
        except jwt.InvalidTokenError:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login')
def login():
    return render_template('login.html')
from flask import redirect, url_for, make_response

@app.route('/logout')
def logout():
    # Clear the token cookie
    response = make_response(redirect(url_for('login')))
    response.set_cookie('token', '', expires=0)
    return response


@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    message = ''
    if request.method == 'POST' and 'id' in request.form and 'password' in request.form:
        id = request.form['id']
        password = request.form['password']
        db_connection = get_db_connection()
        try:
            with db_connection.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT * FROM User WHERE userid = %s AND passwordHash = %s', (id, password))
                user = cursor.fetchone()
                role = user['Role']
                if user and role=='patient':
                    token = generate_token(id)
                    response = redirect(url_for('dashboard'))
                    response.set_cookie('token', token)
                    return response
                elif user and role =='doctor':
                    token = generate_token(id)
                    response = redirect(url_for('Ddashboard'))
                    response.set_cookie('token', token)
                    return response
                elif user and role =='staff':
                    token = generate_token(id)
                    response = redirect(url_for('SDashboard'))
                    response.set_cookie('token', token)
                    return response
                else:
                    message = 'Please enter correct email / password!'
        except Error as e:
            print(f"Error: {e}")
        finally:
            db_connection.close()
    return render_template('login.html', message=message)

@app.route('/dashboard')
@jwt_token_required
def dashboard():
    return render_template('patient.html')

@app.route('/Ddashboard')
@jwt_token_required
def Ddashboard():
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(dictionary=True) as cursor:
            # Fetch user ID from JWT token
            user_id = request.username  # Assuming you set this in jwt_token_required decorator

            cursor.execute('SELECT Name FROM Doctor WHERE DoctorID = %s', (user_id,))
            name = cursor.fetchone()

    except Error as e:
        print(f"Error fetching doctor's name: {e}")
        name = None
    finally:
        db_connection.close()

    return render_template('doctor.html', name=name)


@app.route('/SDashboard')
@jwt_token_required
def SDashboard():
    return render_template('hospital-management.html')

@app.route('/medical_records')
@jwt_token_required
def medical_records():
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(dictionary=True) as cursor:
            # Fetch user ID from JWT token
            user_id = request.username  # Assuming you set this in jwt_token_required decorator

            query = "SELECT * FROM Medicalrecord WHERE PatientID = %s"
            cursor.execute(query, (user_id,))
            records = cursor.fetchall()
            print(records)  # For debugging purposes

    except Error as e:
        print(f"Error fetching medical records: {e}")
        records = None
    finally:
        db_connection.close()

    return render_template('medical_records.html', records=records)


@app.route('/billing_info')
@jwt_token_required
def billing_info():
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(dictionary=True) as cursor:
            # Fetch user ID from JWT token
            user_id = request.username  # Assuming you set this in jwt_token_required decorator

            query = "SELECT * FROM Billing where PatientID = %s"
            cursor.execute(query, (user_id,))
            res = cursor.fetchall()
            print(res)  # For debugging purposes

    except Error as e:
        print(f"Error fetching medical records: {e}")
        res = None
    finally:
        db_connection.close()

    return render_template('/billing_info.html',billing_info=res)


@app.route('/upcoming_appointments')
@jwt_token_required
def upcoming_appointments():
    db_connection = get_db_connection()
    try:
        with db_connection.cursor(dictionary=True) as cursor:
            # Fetch user ID from JWT token
            user_id = request.username  # Assuming you set this in jwt_token_required decorator

            query = "SELECT * FROM Appointment where PatientID = %s"
            cursor.execute(query, (user_id,))
            res = cursor.fetchall()
            print(res)  # For debugging purposes

    except Error as e:
        print(f"Error fetching medical records: {e}")
        records = None
    finally:
        db_connection.close()
    return render_template('/upcoming_appointments.html',appointments=res)

@app.route('/bookAppointment')
@jwt_token_required
def book_appointment():
    return render_template('BookAppointment.html')

# Route to get doctors from the database
@app.route('/get_doctors')
@jwt_token_required
def get_doctors():
    db= get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT DoctorID, Name FROM Doctor")
    doctors = cursor.fetchall()
    print(doctors)
    cursor.close()
    return jsonify(doctors)


@app.route('/book_appointment', methods=['POST'])
@jwt_token_required
def book_appointment_post():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        data = request.form
        patient_id = data['PatientID']
        doctor_id = data['DoctorID']
        appointment_date = data['AppointmentDate']
        appointment_time = data['AppointmentTime']
        reason = data['Reason']
        
        query = """
        INSERT INTO Appointment (PatientID, DoctorID, AppointmentDate, AppointmentTime, Reason)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (patient_id, doctor_id, appointment_date, appointment_time, reason))
        db.commit()  # Commit the transaction
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error booking appointment: {e}")
        db.rollback()  # Rollback in case of error
        return jsonify({'success': False, 'error': str(e)})
    
    finally:
        cursor.close()
        db.close()


@app.route('/DocAppointment')
@jwt_token_required
def DocAppointment():
    db= get_db_connection()
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM Appointment where PatientID = %s"
    cursor.execute(query,(id,))
    res=cursor.fetchall()
    cursor.close()
    return render_template('/DocAppointment.html',appointments=res)    

@jwt_token_required
def get():
    db= get_db_connection()
    user_id = request.username
    cursor = db.cursor(dictionary=True)
    cursor.execute('''SELECT * FROM Appointment WHERE DoctorID = %s AND  CONCAT(AppointmentDate, ' ', AppointmentTime) >= NOW()
                            ORDER BY AppointmentDate, AppointmentTime                      ''', (user_id,))
    res = cursor.fetchall()
    return res

@app.route('/appointments')
@jwt_token_required
def appointment():
    res = get()
    return render_template('/DocAppointment.html',res=res)



@app.route('/delete/<int:appointment_id>', methods=['DELETE'])
@jwt_token_required
def delete_appointment(appointment_id):
    try:
        db_connection = get_db_connection()
        with db_connection.cursor(dictionary=True) as cursor:
            # Check if appointment exists
            cursor.execute('SELECT * FROM Appointment WHERE AppointmentID = %s', (appointment_id,))
            appointment = cursor.fetchone()
            if not appointment:
                return jsonify({'error': 'Appointment not found'}), 404
            
            # Delete appointment from database
            cursor.execute('DELETE FROM Appointment WHERE AppointmentID = %s', (appointment_id,))
            db_connection.commit()
            return jsonify({'message': 'Appointment deleted successfully'})
    except Error as e:
        print(f"Error deleting appointment: {e}")
        db_connection.rollback()
        return jsonify({'error': 'Failed to delete appointment'}), 500
    finally:
        db_connection.close()

    
@app.route('/appointment-management')
@jwt_token_required
def appointmentManagement():
    db= get_db_connection()
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM Appointment"
    cursor.execute(query)
    res=cursor.fetchall()
    print(res)
    cursor.close()
    return render_template('/appointment-management.html',appointment=res)

@app.route('/appointment-scheduling')
@jwt_token_required
def appointmentscheduling():
    return render_template('/BookAppointment.html')

@app.route('/patients')
@jwt_token_required
def patients():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Patient")
    patients = cursor.fetchall()
    cursor.close()
    return render_template('patient-management.html', patients=patients)

@app.route('/edit_patient/<patient_id>', methods=['GET', 'POST'])
@jwt_token_required
def edit_patient(patient_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Patient WHERE PatientID = %s', (patient_id,))
    patient = cursor.fetchone()
    if request.method == 'POST':
        name = request.form['name']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        contact_number = request.form['contact_number']
        email = request.form['email']
        address = request.form['address']
        cursor.execute('''
            UPDATE patient
            SET Name = %s, DateOfBirth = %s, Gender = %s, ContactNumber = %s, Email = %s, Address = %s
            WHERE PatientID = %s
        ''', (name, date_of_birth, gender, contact_number, email, address, patient_id))
        db.commit()
        cursor.close()
        return redirect(url_for('patients'))
    cursor.close()
    return render_template('edit.html', patient=patient)

@app.route('/delete_patient/<patient_id>', methods=['POST'])
def delete_patient(patient_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('DELETE FROM Patient WHERE PatientID = %s', (patient_id,))
    db.commit()
    cursor.close()
    return redirect(url_for('patient'))

# if __name__ == '__main__':
#     app.run(debug=True)
