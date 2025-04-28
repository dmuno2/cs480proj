from flask import Flask, request, redirect, render_template, url_for, session, flash
from db_conn import get_db_connection
import psycopg2

app = Flask(__name__)
app.secret_key = "dev"  # Needed for login sessions

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# ------------- Manager -------------
@app.route('/manager/login', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        ssn = request.form['ssn']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Manager WHERE ssn = %s;", (ssn,))
        manager = cur.fetchone()
        cur.close()
        conn.close()

        if manager:
            session['manager_ssn'] = ssn
            return redirect(url_for('manager_dashboard'))
        else:
            flash('Invalid SSN. Please try again.')
            return redirect(url_for('manager_login'))
    return render_template('loginM.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        ssn = request.form['ssn']
        email = request.form['email']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO manager (name, ssn, email) VALUES (%s, %s, %s)", (name, ssn, email))
            conn.commit()
            return redirect(url_for('loginM'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return "SSN already registered."
        finally:
            cur.close()
            conn.close()
    return render_template('registerM.html')

@app.route('/manager/dashboard')
def manager_dashboard():
    if 'manager_ssn' not in session:
        return redirect(url_for('manager_login'))
    return render_template('manager_dashboard.html')

# ------------- Client -------------
@app.route('/client/register', methods=['GET', 'POST'])
def client_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Client (name, email) VALUES (%s, %s);", (name, email))
        conn.commit()
        cur.close()
        conn.close()

        flash('Registration successful. Please login.')
        return redirect(url_for('client_login'))

    return render_template('client_register.html')

@app.route('/client/login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Client WHERE email = %s;", (email,))
        client = cur.fetchone()
        cur.close()
        conn.close()

        if client:
            session['client_email'] = email
            return redirect(url_for('client_dashboard'))
        else:
            flash('Invalid email. Please try again.')
            return redirect(url_for('client_login'))
    return render_template('client_login.html')

@app.route('/client/dashboard')
def client_dashboard():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))
    return render_template('client_dashboard.html')

# ------------- Driver -------------
@app.route('/driver/login', methods=['GET', 'POST'])
def driver_login():
    if request.method == 'POST':
        name = request.form['name']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Driver WHERE name = %s;", (name,))
        driver = cur.fetchone()
        cur.close()
        conn.close()

        if driver:
            session['driver_name'] = name
            return redirect(url_for('driver_dashboard'))
        else:
            flash('Invalid name. Please try again.')
            return redirect(url_for('driver_login'))
    return render_template('driver_login.html')

@app.route('/driver/dashboard')
def driver_dashboard():
    if 'driver_name' not in session:
        return redirect(url_for('driver_login'))
    return render_template('driver_dashboard.html')

# ------------- Logout -------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Run app
if __name__ == '__main__':
    app.run(debug=True, port=5001)
