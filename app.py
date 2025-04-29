from flask import Flask, request, redirect, render_template, url_for, session, flash
from db_conn import get_db_connection
import psycopg2
import psycopg2.errors 

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
            return redirect(url_for('manager_login'))
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

@app.route('/manager/add_driver', methods=['GET', 'POST'])
def add_driver():
    if request.method == 'POST':
        name = request.form['name']
        road_name = request.form['road_name']
        number = request.form['number']
        city = request.form['city']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # First, insert the address if it doesn't exist
            cur.execute("""
                INSERT INTO Address (road_name, number, city)
                VALUES (%s, %s, %s)
                ON CONFLICT (road_name, number, city) DO NOTHING;
            """, (road_name, number, city))

            # Now, insert the driver
            cur.execute(
                "INSERT INTO Driver (name, road_name, number, city) VALUES (%s, %s, %s, %s);",
                (name, road_name, number, city)
            )
            conn.commit()
            flash('Driver added successfully!')
        except Exception as e:
            conn.rollback()
            flash(f"Error adding driver: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('manager_dashboard'))

    return render_template('add_driver.html')

@app.route('/manager/add_car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        carid = request.form['carid']
        brand = request.form['brand']

        conn = get_db_connection()
        cur = conn.cursor()
        try:

            # Now, insert the driver
            cur.execute(
                "INSERT INTO Car (carid, brand) VALUES (%s, %s);",
                (carid, brand)
            )
            conn.commit()
            flash('Car added successfully!')
        except Exception as e:
            conn.rollback()
            flash(f"Error adding car: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('manager_dashboard'))

    return render_template('add_car.html')

@app.route('/manager/add_model', methods=['GET', 'POST'])
def add_model():
    if request.method == 'POST':
        modelid = request.form['modelid']
        carid = request.form['carid']
        color = request.form['color']
        #construction_year = int(request.form['construction_year'])
        construction_year = request.form['construction_year']
        transmission = request.form['transmission']

        conn = get_db_connection()
        cur = conn.cursor()
        try:

            # Now, insert the driver
            cur.execute(
                "INSERT INTO model (modelid, carid, color, construction_year, transmission) VALUES (%s, %s, %s, %s, %s);",
                (modelid, carid, color, construction_year, transmission)
            )
            conn.commit()
            flash('Model added successfully!')
        except Exception as e:
            conn.rollback()
            flash(f"Error adding model: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('manager_dashboard'))

    return render_template('add_model.html')

@app.route('/manager/delete_driver', methods=['GET', 'POST'])
def delete_driver():
    if request.method == 'POST':
        driver_name = request.form['name']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM Driver WHERE name = %s;", (driver_name,))
            conn.commit()
            flash('Driver deleted successfully!')
        except Exception as e:
            conn.rollback()
            flash(f"Error deleting driver: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('manager_dashboard'))

    return render_template('delete_driver.html')


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

#lets clients search by car brand
#search is case-insensitive because of ILIKE.
@app.route('/client/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        brand = request.form['brand']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM Car WHERE brand ILIKE %s;",
            ('%' + brand + '%',)
        )
        results = cur.fetchall()
        cur.close()
        conn.close()

    return render_template('search.html', results=results)

@app.route('/client/book', methods=['GET', 'POST'])
def book_rent():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))

    if request.method == 'POST':
        rentid = request.form['rentid']
        rent_date = request.form['rent_date']
        driver_name = request.form['driver_name']
        modelid = request.form['modelid']
        client_email = session['client_email']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO Rent (rentid, rent_date, client_email, driver_name, modelid) VALUES (%s, %s, %s, %s, %s);",
                (rentid, rent_date, client_email, driver_name, modelid)
            )
            conn.commit()
            flash('Rent booked successfully!')
        except Exception as e:
            conn.rollback()
            flash(f"Error booking rent: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('client_dashboard'))

    return render_template('book.html')

@app.route('/client/add_creditcard', methods=['GET', 'POST'])
def add_creditcard():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))

    if request.method == 'POST':
        card_num = request.form['card_num']
        road_name = request.form['road_name']
        number = request.form['number']
        city = request.form['city']
        email = session['client_email']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # First, insert the address if it's not already there
            cur.execute("""
                INSERT INTO Address (road_name, number, city)
                VALUES (%s, %s, %s)
                ON CONFLICT (road_name, number, city) DO NOTHING;
            """, (road_name, number, city))

            # Then insert credit card
            cur.execute("""
                INSERT INTO CreditCard (card_num, email, road_name, number, city)
                VALUES (%s, %s, %s, %s, %s);
            """, (card_num, email, road_name, number, city))

            conn.commit()
            flash("Credit card added successfully!")
        except Exception as e:
            conn.rollback()
            flash(f"Error adding credit card: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('client_dashboard'))

    return render_template('add_creditcard.html')



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

@app.route('/driver/add_address', methods=['GET', 'POST'])
def add_driver_address():
    if 'driver_name' not in session:
        return redirect(url_for('driver_login'))

    if request.method == 'POST':
        road_name = request.form['road_name']
        number = request.form['number']
        city = request.form['city']
        driver_name = session['driver_name']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # First insert the address if it doesn't exist
            cur.execute("""
                INSERT INTO Address (road_name, number, city)
                VALUES (%s, %s, %s)
                ON CONFLICT (road_name, number, city) DO NOTHING;
            """, (road_name, number, city))

            # Then update Driver's address
            cur.execute("""
                UPDATE Driver
                SET road_name = %s, number = %s, city = %s
                WHERE name = %s;
            """, (road_name, number, city, driver_name))

            conn.commit()
            flash('Address added/updated successfully!')
        except Exception as e:
            conn.rollback()
            flash(f"Error adding address: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('driver_dashboard'))

    return render_template('add_driver_address.html')


@app.route('/driver/add_car', methods=['GET', 'POST'])
def add_car_driver():
    if 'driver_name' not in session:
        return redirect(url_for('driver_login'))

    if request.method == 'POST':
        modelid = request.form['modelid']
        driver_name = session['driver_name']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO CanDrive (driver_name, modelid)
                VALUES (%s, %s);
            """, (driver_name, modelid))
            conn.commit()
            flash('Car model added successfully for you!')
        except Exception as e:
            conn.rollback()
            flash(f"Error adding car model: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('driver_dashboard'))

    return render_template('add_car_driver.html')


# ------------- Logout -------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Run app
if __name__ == '__main__':
    app.run(debug=True, port=5001)
