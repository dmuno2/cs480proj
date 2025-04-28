from flask import Flask
from db_conn import get_db_connection

app = Flask(__name__)

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    return "Hello, World!"
    # cur.execute('')
    # rows = cur.fetchall()
    cur.close()
    conn.close()
    # return str(rows)

if __name__ == '__main__':
    app.run(debug=True)