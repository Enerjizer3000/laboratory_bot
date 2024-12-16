import mysql.connector
from mysql.connector import Error
import secrets

# Данные для добавления
workers_data = [
    ('Виталий', 'Владимиров', '89289895460', 'vityavolodya@mail.ru', 34),
    ('Стивен', 'Армстронг', '83456654129', 'stevenSigma@gmail.com', 45),
    ('Алекс', 'Бансон', '88249375160', 'alexBanson@gmail.com', 39),
    ('Адам', 'Пирс', '89166028135', 'adampirs@mail.ru', 52),
    ('Чарли', 'Эдкинсон', '83456174190', 'charlie.edkinson@google.com', 40),
    ('Билли', 'Боб', '889030812645', 'billyBob@gmail.com', 22)
]

try:
    connection = mysql.connector.connect(
        host=secrets.db_host,
        user=secrets.db_user,
        password=secrets.db_password,
        database=secrets.db
    )
    if connection.is_connected():
        cursor = connection.cursor()

        insert_query = """
            INSERT INTO Workers (Name, Last_name, Phone, Email, Age)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.executemany(insert_query, workers_data)
        connection.commit()
        print("Записи успешно добавлены.")

except Error as e:
    print(f"Произошла ошибка: {e}")
finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
