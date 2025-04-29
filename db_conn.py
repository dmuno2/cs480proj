import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="ep-snowy-mouse-a484zcoz-pooler.us-east-1.aws.neon.tech",  # from your Neon connection screen
        database="neondb",  # your database name
        user="Shayan",  # from your env.txt, PGUSER=Shayan
        password="npg_fU8HrEaCt2TD",  # from your env.txt, PGPASSWORD=...
        port=5432,
        sslmode='require'  # Neon requires SSL
    )
    return conn