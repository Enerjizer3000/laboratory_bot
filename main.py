import telebot
from telebot import types
import string
import platform
import psutil
from datetime import datetime
import re
import mysql.connector
import paramiko

API_TOKEN = '7001780241:AAHSm40R8eKjdTT7zNyORizwhZm0k4voSSY'  # Замените на ваш токен


bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("Валидация по E-mail или номеру")
    btn2 = types.KeyboardButton("Проверить сложность пароля")
    btn3 = types.KeyboardButton("Информация о системе")
    btn4 = types.KeyboardButton("Информация о Linux системе")

    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Валидация по E-mail или номеру":
        bot.send_message(message.chat.id, "Укажите E-mail или номер телефона для проверки его наличия в системе:")
        bot.register_next_step_handler(message, user_validation)
    elif message.text == "Проверить сложность пароля":
        bot.send_message(message.chat.id, "Введите пароль для проверки сложности:")
        bot.register_next_step_handler(message, password_verification)
    elif message.text == "Информация о системе":
        system_info(message)
    elif message.text == "Информация о Linux системе":
        linux_info(message)

#функции для бота
def user_validation(message):
    conn = mysql.connector.connect(host='host.docker.internal', user='root', password='3000', database="mysql")
    cursor = conn.cursor()
    query = "SELECT Name, Last_name, Phone, Email, Age FROM Workers WHERE Phone = %s OR Email = %s"
    if message.text.isdigit():
        phone = message.text
        email = None
    else:
        phone = None
        email = message.text

    cursor.execute(query, (phone, email))
    result = cursor.fetchone()
    if result:
        name, last_name, phone, email, age = result
        bot.send_message(message.chat.id,f"*Найден пользователь:*\n\n*Имя:* {name} {last_name}\n*Номер телефона:* {phone}\n*E-mail:* {email}\n*Возраст:* {age}",parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Указанные данные не прошли проверку - в системе нет пользователя с таким номером телефона или E-mail'ом")
    conn.commit()
    conn.close()

def password_verification(message):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
    if re.match(pattern, message.text):
        bot.send_message(message.chat.id, "*Пароль вполне хороший*", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Пароль слабый, так как его наполнение *неразнообразное* или *короче 8* символов", parse_mode='Markdown')
    send_welcome(message)

def system_info(message):
    system_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    memory_info = psutil.virtual_memory()
    used_memory = memory_info.used / (1024 ** 2)
    total_memory = memory_info.total / (1024 ** 2)
    disk_info = psutil.disk_usage('/')
    used_disk = disk_info.used / (1024 ** 3)
    total_disk = disk_info.total / (1024 ** 3)
    cpu_info = platform.processor()

    bot.send_message(message.chat.id, f"Время системы: {system_time}\nЗагруженность ОЗУ: {used_memory:.2f}МБ / {total_memory:.2f}МБ\nЗагруженность диска: {used_disk:.2f}ГБ / {total_disk:.2f}ГБ\nТип процессора: {cpu_info}")

def linux_info(message):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Подключаемся к удаленному серверу
        #в случае VPN подключения внешний IP адрес хоста: 91.245.236.12
        #в случае удалённой версии сервера IP будет: 91.197.98.202, пароль: bzdwvqe1NEOjw50v, пользователь: root
        ssh.connect(hostname='91.197.98.202', username='root', password='bzdwvqe1NEOjw50v')
        # Получаем информацию о RAM
        stdin, stdout, stderr = ssh.exec_command("free -m | awk \'NR==2{printf \"%s/%s\", $3,$2}\'")
        ram = stdout.read().decode().strip()  # Заполненность ОЗУ/полная память ОЗУ в МБ
        ram_gb = f"{int(ram.split('/')[0]) / 1024:.2f} GB / {int(ram.split('/')[1]) / 1024:.2f} GB"

        # Получаем информацию о дисковом пространстве
        stdin, stdout, stderr = ssh.exec_command("df -h --total | grep \'total\'")
        storage = stdout.read().decode().strip().split()  # Получаем строку с информацией о диске
        storage_info = f"{storage[2]} / {storage[1]}"  # Заполненность диска / полная память диска в ГБ

        # Получаем информацию о загрузке CPU
        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep \'Cpu(s)\' | sed \'s/.*, *([0-9.]*)%* id.*/1/\' | awk \'{print 100 - $1}\'")
        cpu_load = stdout.read().decode().strip()  # Нагрузка на ЦП в процентах

        RAM = ram_gb
        Storage = storage_info + 'B'
        CPU = cpu_load + '%'

        ssh.close()

        bot.send_message(message.chat.id, f"Аппаратные показатели Linux сервера:\n\n*Заполненность ОЗУ:* {RAM}\n*Заполненность дискового хранилища:* {Storage}\n*Загруженность процессора:* {CPU}", parse_mode='Markdown')
        send_welcome(message)
    except Exception as e:
        print(f"Ошибка SSH подключения: {e}")
        bot.send_message(message.chat.id, "*Невозможно подключиться к серверу Linux*", parse_mode='Markdown')
        send_welcome(message)



if __name__ == '__main__':
    bot.polling(none_stop=True)
