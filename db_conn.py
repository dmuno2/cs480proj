import psycopg2

database = 'cs480_proj'
username = 'postgres'
pwd = 'Database2003@'
port_id = 5432

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="cs480_proj",
        user="postgres",
        password="Database2003@"
    )
    return conn