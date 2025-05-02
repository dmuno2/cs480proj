from flask import Flask, request, redirect, render_template, url_for, session, flash
from db_conn import get_db_connection
import psycopg2
import psycopg2.errors 
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "dev"  # Needed for login sessions

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

####################### Manager ###################
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

@app.route('/manager/view_cars')
def manager_view_cars():
    if 'manager_ssn' not in session:
        return redirect(url_for('manager_login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    query = '''
        SELECT car.carid, car.brand,
               model.modelid, model.color, model.construction_year, model.transmission,
               COUNT(rent.rentid) AS rent_count
        FROM car
        JOIN model ON car.carid = model.carid
        LEFT JOIN rent ON model.modelid = rent.modelid
        GROUP BY car.carid, car.brand, model.modelid, model.color, model.construction_year, model.transmission
        ORDER BY rent_count DESC
    '''
    cursor.execute(query)
    cars = cursor.fetchall()
    conn.close()
    
    return render_template('list_carsM.html', cars=cars) 

@app.route('/manager/view_driver_stats')
def manager_view_driver_stats():
    if 'manager_ssn' not in session:
        return redirect(url_for('manager_login'))

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    query = '''
        SELECT d.name AS driver_name,
               COALESCE(rent_counts.total_rents, 0) AS total_rents,
               ROUND(avg_ratings.average_rating, 2) AS average_rating
        FROM Driver d
        LEFT JOIN (
            SELECT driver_name, COUNT(*) AS total_rents
            FROM Rent
            GROUP BY driver_name
        ) rent_counts ON d.name = rent_counts.driver_name
        LEFT JOIN (
            SELECT name AS driver_name, AVG(rating) AS average_rating
            FROM Review
            GROUP BY name
        ) avg_ratings ON d.name = avg_ratings.driver_name
        ORDER BY total_rents DESC
    '''
    cursor.execute(query)
    drivers = cursor.fetchall()
    conn.close()

    return render_template('manager_driver_stats.html', drivers=drivers)

@app.route('/manager/client_city_match', methods=['GET', 'POST'])
def client_city_match():
    results = []
    if 'manager_ssn' not in session:
        return redirect(url_for('manager_login'))

    if request.method == 'POST':
        city1 = request.form['city1']
        city2 = request.form['city2']

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = '''
            SELECT DISTINCT c.name, c.email
            FROM Client c
            JOIN LivesIn_Client lc ON c.email = lc.email
            JOIN Address ca ON lc.road_name = ca.road_name AND lc.number = ca.number AND lc.city = ca.city
            JOIN Rent r ON c.email = r.client_email
            JOIN Driver d ON r.driver_name = d.name
            JOIN Address da ON d.road_name = da.road_name AND d.number = da.number AND d.city = da.city
            WHERE ca.city = %s AND da.city = %s
        '''

        cur.execute(query, (city1, city2))
        results = cur.fetchall()
        conn.close()

    return render_template('client_city_match.html', results=results)

@app.route('/manager/top_clients', methods=['GET', 'POST'])
def top_clients():
    results = []

    if request.method == 'POST':
        k = request.form.get('k')
        if k and k.isdigit() and int(k) > 0:
            k = int(k)

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute('''
                SELECT Client.name, Client.email, COUNT(*) AS rent_count
                FROM Rent
                JOIN Client ON Rent.client_email = Client.email
                GROUP BY Client.name, Client.email
                ORDER BY rent_count DESC
                LIMIT %s
            ''', (k,))

            results = cur.fetchall()
            conn.close()

    return render_template('top_clients.html', results=results)

@app.route('/manager/problem_drivers')
def problem_drivers():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        SELECT d.name,
               (
                   SELECT ROUND(AVG(rating), 2)
                   FROM Review
                   WHERE Review.name = d.name
               ) AS avg_rating
        FROM Driver d
        WHERE d.city = 'Chicago'
        AND (
            SELECT AVG(rating)
            FROM Review
            WHERE Review.name = d.name
        ) < 2.5
        AND (
            SELECT COUNT(DISTINCT r.client_email)
            FROM Rent r
            WHERE r.driver_name = d.name
              AND r.client_email IN (
                  SELECT DISTINCT lc.email
                  FROM LivesIn_Client lc
                  WHERE lc.city = 'Chicago'
              )
        ) >= 2
    ''')

    drivers = cur.fetchall()
    conn.close()

    return render_template('problem_drivers.html', drivers=drivers)

@app.route('/manager/brand_report')
def manager_brand_report():
    if 'manager_ssn' not in session:
        return redirect(url_for('manager_login'))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = '''
        SELECT 
            c.brand,
            ROUND(AVG(avg_rating.avg_rating), 2) AS average_rating,
            COALESCE(SUM(rent_counts.total_rents), 0) AS total_rents
        FROM car c
        JOIN model m ON c.carid = m.carid

        LEFT JOIN (
            SELECT cd.modelid, AVG(rv.rating) AS avg_rating
            FROM canDrive cd
            JOIN review rv ON cd.driver_name = rv.name
            GROUP BY cd.modelid
        ) avg_rating ON m.modelid = avg_rating.modelid

        LEFT JOIN (
            SELECT modelid, COUNT(*) AS total_rents
            FROM rent
            GROUP BY modelid
        ) rent_counts ON m.modelid = rent_counts.modelid

        GROUP BY c.brand
        ORDER BY total_rents DESC
    '''

    cur.execute(query)
    report = cur.fetchall()
    conn.close()

    return render_template('brand_report.html', report=report)

################### Client #####################
@app.route('/client/register', methods=['GET', 'POST'])
def client_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        # Home address
        home_road = request.form['home_road_name']
        home_number = request.form['home_number']
        home_city = request.form['home_city']

        # Credit card & billing address
        card_num = request.form['card_num']
        bill_road = request.form['bill_road_name']
        bill_number = request.form['bill_number']
        bill_city = request.form['bill_city']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Insert both addresses if not already there
            cur.execute("""
                INSERT INTO Address (road_name, number, city)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (home_road, home_number, home_city))

            cur.execute("""
                INSERT INTO Address (road_name, number, city)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (bill_road, bill_number, bill_city))

            # Insert client
            cur.execute("INSERT INTO Client (name, email) VALUES (%s, %s);", (name, email))

            # Insert livesin relationship (if it exists)
            cur.execute("""
                INSERT INTO livesin_client (email, road_name, number, city)
                VALUES (%s, %s, %s, %s);
            """, (email, home_road, home_number, home_city))

            # Insert credit card
            cur.execute("""
                INSERT INTO CreditCard (card_num, email, road_name, number, city)
                VALUES (%s, %s, %s, %s, %s);
            """, (card_num, email, bill_road, bill_number, bill_city))

            conn.commit()
            flash("Registration complete! Please login.")
            return redirect(url_for('client_login'))
        except Exception as e:
            conn.rollback()
            flash(f"Error: {e}")
        finally:
            cur.close()
            conn.close()

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

    assigned_driver = None

    if request.method == 'POST':
        rentid = request.form['rentid']
        rent_date = request.form['rent_date']
        modelid = request.form['modelid']
        client_email = session['client_email']

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Find available driver who can drive the model and is not booked that day
            cur.execute("""
                SELECT d.name
                FROM Driver d
                JOIN CanDrive cd ON d.name = cd.driver_name
                WHERE cd.modelid = %s
                  AND d.name NOT IN (
                      SELECT driver_name FROM Rent WHERE rent_date = %s
                  )
                LIMIT 1;
            """, (modelid, rent_date))
            result = cur.fetchone()

            if result is None:
                flash('No available driver for the selected model on this date.')
                return redirect(url_for('book_rent'))

            assigned_driver = result[0]

            cur.execute("""
                INSERT INTO Rent (rentid, rent_date, client_email, driver_name, modelid)
                VALUES (%s, %s, %s, %s, %s);
            """, (rentid, rent_date, client_email, assigned_driver, modelid))

            conn.commit()
            flash(f'Driver {assigned_driver} has been assigned to your booking.')

        except Exception as e:
            conn.rollback()
            flash(f"Error booking rent: {e}")
        finally:
            cur.close()
            conn.close()

    # Populate model list for dropdown
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT modelid FROM Model;")
    models = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('book.html', models=models, assigned_driver=assigned_driver)

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

# CLIENT - ADD ADDRESS
@app.route('/client/add_address', methods=['GET', 'POST'])
def client_add_address():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))

    if request.method == 'POST':
        road_name = request.form['road_name']
        number = request.form['number']
        city = request.form['city']
        email = session['client_email']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO Address (road_name, number, city)
                VALUES (%s, %s, %s)
                ON CONFLICT (road_name, number, city) DO NOTHING;
            """, (road_name, number, city))

            cur.execute("""
                INSERT INTO LivesIn_Client (email, road_name, number, city)
                VALUES (%s, %s, %s, %s);
            """, (email, road_name, number, city))

            conn.commit()
            flash('Address added successfully!')
        except Exception as e:
            conn.rollback()
            flash(f"Error adding address: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('client_dashboard'))

    return render_template('client_address.html')

@app.route('/client/available_models', methods=['GET', 'POST'])
def available_models():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))

    available_models = []
    if request.method == 'POST':
        rent_date = request.form['rent_date']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT DISTINCT m.modelid, m.color, m.transmission, m.construction_year
                FROM model m
                JOIN candrive cd ON m.modelid = cd.modelid
                LEFT JOIN rent r_model ON m.modelid = r_model.modelid AND r_model.rent_date = %s
                LEFT JOIN rent r_driver ON cd.driver_name = r_driver.driver_name AND r_driver.rent_date = %s
                WHERE r_model.rentid IS NULL AND r_driver.rentid IS NULL;
            """, (rent_date, rent_date))

            available_models = cur.fetchall()
        finally:
            cur.close()
            conn.close()

    return render_template('available_models.html', available_models=available_models)

# CLIENT - LEAVE REVIEW
@app.route('/client/review', methods=['GET', 'POST'])
def client_leave_review():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))

    if request.method == 'POST':
        driver_name = request.form.get('driver_name', '').strip()
        message = request.form.get('message', '').strip()
        rating_raw = request.form.get('rating', '').strip()
        email = session['client_email']

        # Field validation
        if not driver_name or not message or not rating_raw:
            flash("All fields are required.")
            return redirect(url_for('client_leave_review'))

        try:
            rating = int(rating_raw)
            if rating < 0 or rating > 5:
                flash("Rating must be between 0 and 5.")
                return redirect(url_for('client_leave_review'))
        except ValueError:
            flash("Rating must be a number.")
            return redirect(url_for('client_leave_review'))

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Check if driver exists
            cur.execute("SELECT 1 FROM Driver WHERE name = %s", (driver_name,))
            if cur.fetchone() is None:
                flash("The specified driver does not exist.")
                return redirect(url_for('client_leave_review'))

            # Check if this client has rented from this driver
            cur.execute("""
                SELECT 1 FROM Rent WHERE client_email = %s AND driver_name = %s;
            """, (email, driver_name))
            if cur.fetchone() is None:
                flash('You can only review drivers you have rented from.')
                return redirect(url_for('client_leave_review'))

            # Insert into Review
            import uuid
            reviewid = str(uuid.uuid4())[:8]
            cur.execute("""
                INSERT INTO Review (reviewid, name, message, rating)
                VALUES (%s, %s, %s, %s);
            """, (reviewid, driver_name, message, rating))

            # Link to client
            cur.execute("""
                INSERT INTO Written_By (email, reviewid)
                VALUES (%s, %s);
            """, (email, reviewid))

            conn.commit()
            flash('Review submitted successfully!')
        except Exception as e:
            conn.rollback()
            flash(f"Error submitting review: {e}")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('client_dashboard'))

    return render_template('client_review.html')

@app.route('/client/book_best_driver', methods=['GET', 'POST'])
def book_best_driver():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))

    best_driver = None

    if request.method == 'POST':
        rentid = request.form['rentid']
        rent_date = request.form['rent_date']
        modelid = request.form['modelid']
        client_email = session['client_email']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT d.driver_name
                FROM CanDrive d
                LEFT JOIN Rent r ON d.driver_name = r.driver_name AND r.rent_date = %s
                LEFT JOIN Review rv ON d.driver_name = rv.name
                WHERE d.modelid = %s AND r.driver_name IS NULL
                GROUP BY d.driver_name
                ORDER BY AVG(rv.rating) DESC NULLS LAST
                LIMIT 1;
            """, (rent_date, modelid))

            best_driver_row = cur.fetchone()
            if not best_driver_row:
                flash("No available driver found for this model on that date.")
            else:
                best_driver = best_driver_row[0]
                cur.execute("""
                    INSERT INTO Rent (rentid, rent_date, client_email, driver_name, modelid)
                    VALUES (%s, %s, %s, %s, %s);
                """, (rentid, rent_date, client_email, best_driver, modelid))
                conn.commit()
                flash("Rent successfully booked!")
        except Exception as e:
            conn.rollback()
            flash(f"Booking error: {e}")
        finally:
            cur.close()
            conn.close()

    return render_template('book_best_driver.html', best_driver=best_driver)

#client check past bookings
@app.route('/client/rents', methods=['GET'])
def client_rents():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))  # Ensure client is logged in

    email = session['client_email']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        SELECT Rent.rentid, Rent.rent_date, Rent.modelid, Car.brand, Model.construction_year, Model.color, Rent.driver_name
        FROM Rent
        JOIN Model ON Rent.modelid = Model.modelid
        JOIN Car ON Model.carid = Car.carid
        WHERE Rent.client_email = %s
        ORDER BY Rent.rent_date ASC
    ''', (email,))

    rents = cur.fetchall()
    conn.close()

    return render_template('client_rents.html', rents=rents)

##################### Driver ############################
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

@app.route('/cars')
def list_cars():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor) 
    # cursor = conn.cursor()
    cursor.execute('''
        SELECT car.carid AS car_id, model.modelid AS car_modelid, car.brand AS car_brand,
               model.color, model.construction_year, model.transmission
        FROM car
        JOIN model ON car.carid = model.carid
    ''')
    # cars = [dict(row) for row in cursor.fetchall()]
    cars = cursor.fetchall()
    conn.close()
    return render_template('list_cars.html', cars=cars)


######################## Logout #######################
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Run app
if __name__ == '__main__':
    app.run(debug=True, port=5004)
