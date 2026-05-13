import psycopg2

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="user",
        password="password",
        host="localhost",
        port="5432"
    )

    print("1234")
    conn.close
except Exception as e:
    print("error: {e}")