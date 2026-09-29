import psycopg2
from psycopg2.extras import RealDictCursor

try:
    connection = psycopg2.connect(
        host="localhost",
        port="5432",
        database="prokat",
        user="postgres",
        password="root"
    )

    cursor = connection.cursor(cursor_factory=RealDictCursor)

    sql_query = "select id, full_name, mobile_phone from clients"
    cursor.execute(sql_query)
    result = cursor.fetchall()
    print(result)

except Exception as error:
    print("Ошибка")
finally: 
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()
    print("Закрыто")

