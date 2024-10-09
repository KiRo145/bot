import telebot
import base64
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
import requests

TOKEN = '7428759049:AAHj2YC7eKg8gKHT3nLzbEUZMOEUt4eJEOM'
bot = telebot.TeleBot(TOKEN)

# Словари для отслеживания состояния пользователя
user_steps = {}
user_data = {}
test_results = {}
user_messages = {}  # Хранение ID сообщений для каждого пользователя

# Словарь для сопоставления значений кнопок с их ID
request_type_mapping = {
    "Авария": 716,
    "Ошибка в работе": 718,
    "Обучение":798,
    "Настройка Битрикс24": 720,
    "Нужна консультация": 722,
    "Разработка нового функционала": 724
}

# Вопросы теста
test_questions = [
    {
        "question": "Как обойти ограничение по задачам на бесплатном тарифе?",
        "answers": [
            "Приобрести коммерческий тариф",
            "Удалить часть задач, чтоб их снова стало 100 или меньше",
            "Попросить интегратора включить вам недостающий функционал"
        ],
        "correct": 1
    },
    {
        "question": "Сколько БЕСПЛАТНЫХ приложений можно установить на архивном тарифе «Компания»?",
        "answers": ["1", "2", "5", "10"],
        "correct": 3
    },
    {
        "question": "Сколько может быть промежуточных стадий по сделке?",
        "answers": [
            "Столько, сколько нужно компании",
            "Две, по умолчанию задана одна, компания может добавить еще одну, если это необходимо",
            "Одна, она уже задана в системе"
        ],
        "correct": 0
    },
    {
        "question": "Необходимо запустить другой бизнес-процесс по документу. Где настраиваются дополнительные поля?",
        "answers": [
            "В настройках документа, по которому запускается бизнес-процесс, опция  поля “Обязательно для заполнения при запуске бизнес-процесса”",
            "С помощью дизайнера бизнес-процесса, когда первым в шаблоне установлено действие \"Запрос дополнительной информации\"",
            "В настройках бизнес-процесса, меню \"Параметры шаблона\", в разделе \"Параметры\""
        ],
        "correct": 2
    },
    {
        "question": "Сотрудник ведет клиента, есть активная сделка. Это значит:",
        "answers": [
            "При получении очередного письма от этого клиента оно будет прикреплено к текущей сделке",
            "При получении очередного письма от этого клиента система спросит у сотрудника: создать новую сделку или прикрепить письмо к текущей?",
            "При получении очередного письма от этого клиента будет автоматически создана новая сделка"
        ],
        "correct": 0
    }
]


# Функция для удаления всех сообщений пользователя
def delete_user_messages(chat_id):
    if chat_id in user_messages:
        for msg_id in user_messages[chat_id]:
            try:
                bot.delete_message(chat_id, msg_id)
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Ошибка при удалении сообщения {msg_id} для чата {chat_id}: {e}")
        user_messages[chat_id] = []  # Очистка списка сообщений


# Функция для сбора данных
def request_next_part_of_data(message):
    chat_id = message.chat.id
    step = user_steps.get(chat_id, 0)

    if chat_id not in user_messages:
        user_messages[chat_id] = []

    if step == 0:
        user_data[chat_id] = {'chat_id': chat_id}  # Сохраните chat_id
        msg = bot.send_message(chat_id, "Давайте соберем нужную информацию.\n\nВведите название вашей организации:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 1

    elif step == 1:
        user_data[chat_id]['companyname'] = message.text
        markup = types.InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(
            types.InlineKeyboardButton(text="🔥Авария🔥", callback_data='Авария'),
            types.InlineKeyboardButton(text="❌Ошибка в работе❌", callback_data='Ошибка в работе'),
            types.InlineKeyboardButton(text="⚙️Настройка Битрикс24⚙️", callback_data='Настройка Битрикс24'),
            types.InlineKeyboardButton(text="🧑🏻‍🎓Обучение👩🏻‍🎓", callback_data='Обучение'),
            types.InlineKeyboardButton(text="📞Нужна консультация📞", callback_data='Нужна консультация'),
            types.InlineKeyboardButton(text="🔧Разработка нового функционала🔧", callback_data='Разработка нового функционала')
        )
        msg = bot.send_message(chat_id, "Выберите тип обращения:", reply_markup=markup)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 2

    elif step == 2:
        msg = bot.send_message(chat_id, "Пожалуйста, выберите тип обращения, используя кнопки ниже.")
        user_messages[chat_id].append(msg.message_id)

    # Авария
    elif step == 3 and user_data[chat_id]['request_type'] == 716:  # 716 — это ID для "Авария"
        user_data[chat_id]['issue'] = message.text
        msg = bot.send_message(chat_id, "Приложите, пожалуйста, скриншоты, если это необходимо.(Прикладывайте скриншоты файлом, без сжатия)")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 4

    elif step == 4 and user_data[chat_id]['request_type'] == 716:
        user_data[chat_id]['screenshots'] = message.document if message.document else None  # Обрабатываем скрины
        msg = bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 5

    elif step == 5 and user_data[chat_id]['request_type'] == 716:
        user_data[chat_id]['name'] = message.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        contact_button = types.KeyboardButton(text="Поделиться контактом", request_contact=True)
        markup.add(contact_button)
        msg = bot.send_message(chat_id, "Поделитесь вашим номером телефона:", reply_markup=markup)
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 6

    elif step == 6 and user_data[chat_id]['request_type'] == 716:
        if message.contact:
            user_data[chat_id]['phone'] = message.contact.phone_number
        else:
            user_data[chat_id]['phone'] = message.text
        add_lead_to_bitrix24_avaria(user_data[chat_id])  # Отправка данных в Bitrix24
        user_steps[chat_id] = 0

    # Ошибка в работе
    elif step == 3 and user_data[chat_id]['request_type'] == 718:  # 718 — это ID для "Ошибка в работе"
        user_data[chat_id]['error_description'] = message.text
        msg = bot.send_message(chat_id, "Приложите, пожалуйста, скриншоты файлом.(без сжатия)")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 4

    elif step == 4 and user_data[chat_id]['request_type'] == 718:
        user_data[chat_id]['screenshots'] = message.document if message.document else None  # Обрабатываем скрины
        msg = bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 5

    elif step == 5 and user_data[chat_id]['request_type'] == 718:
        user_data[chat_id]['name'] = message.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        contact_button = types.KeyboardButton(text="Поделиться контактом", request_contact=True)
        markup.add(contact_button)
        msg = bot.send_message(chat_id, "Поделитесь вашим номером телефона:", reply_markup=markup)
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 6

    elif step == 6 and user_data[chat_id]['request_type'] == 718:
        if message.contact:
            user_data[chat_id]['phone'] = message.contact.phone_number
        else:
            user_data[chat_id]['phone'] = message.text
        add_lead_to_bitrix24_error(user_data[chat_id])  # Отправка данных в Bitrix24
        user_steps[chat_id] = 0

    # Обучение
    elif step == 3 and user_data[chat_id]['request_type'] == 798:  # 798 — это ID для "Обучение"
        user_data[chat_id]['training_topic'] = message.text
        msg = bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 4

    elif step == 4 and user_data[chat_id]['request_type'] == 798:
        user_data[chat_id]['name'] = message.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        contact_button = types.KeyboardButton(text="Поделиться контактом", request_contact=True)
        markup.add(contact_button)
        msg = bot.send_message(chat_id, "Поделитесь вашим номером телефона:", reply_markup=markup)
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 5

    elif step == 5 and user_data[chat_id]['request_type'] == 798:
        if message.contact:
            user_data[chat_id]['phone'] = message.contact.phone_number
        else:
            user_data[chat_id]['phone'] = message.text
        add_lead_to_bitrix24_teach(user_data[chat_id])  # Отправка данных в Bitrix24
        user_steps[chat_id] = 0

    # Настройка Битрикс24
    elif step == 3 and user_data[chat_id]['request_type'] == 720:  # 720 — это ID для "Настройка Битрикс24"
        user_data[chat_id]['customization_request'] = message.text
        msg = bot.send_message(chat_id, "Приложите файлы с ТЗ / пожеланиями, если такие есть.")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 4

    elif step == 4 and user_data[chat_id]['request_type'] == 720:
        user_data[chat_id]['attachments'] = message.document if message.document else None  # Обрабатываем файлы
        msg = bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 5

    elif step == 5 and user_data[chat_id]['request_type'] == 720:
        user_data[chat_id]['name'] = message.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        contact_button = types.KeyboardButton(text="Поделиться контактом", request_contact=True)
        markup.add(contact_button)
        msg = bot.send_message(chat_id, "Поделитесь вашим номером телефона:", reply_markup=markup)
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 6

    elif step == 6 and user_data[chat_id]['request_type'] == 720:
        if message.contact:
            user_data[chat_id]['phone'] = message.contact.phone_number
        else:
            user_data[chat_id]['phone'] = message.text
        add_lead_to_bitrix24_settings(user_data[chat_id])  # Отправка данных в Bitrix24
        user_steps[chat_id] = 0

    # Разработка нового функционала
    elif step == 3 and user_data[chat_id]['request_type'] == 724:
        user_data[chat_id]['files'] = message.document if message.document else None
        msg = bot.send_message(chat_id, "Напишите, пожалуйста, ваши комментарии к файлам:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 4

    elif step == 4 and user_data[chat_id]['request_type'] == 724:
        user_data[chat_id]['comments'] = message.text
        msg = bot.send_message(chat_id, "Введите ваше имя:")
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 5


    elif step == 5 and user_data[chat_id]['request_type'] == 724:
        user_data[chat_id]['name'] = message.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        contact_button = types.KeyboardButton(text="Поделиться контактом", request_contact=True)
        markup.add(contact_button)
        msg = bot.send_message(chat_id, "Поделитесь вашим номером телефона:", reply_markup=markup)
        bot.register_next_step_handler(msg, request_next_part_of_data)
        user_messages[chat_id].append(msg.message_id)
        user_steps[chat_id] = 6

    elif step == 6 and user_data[chat_id]['request_type'] == 724:
        if message.contact:
            user_data[chat_id]['phone'] = message.contact.phone_number
        else:
            user_data[chat_id]['phone'] = message.text
        add_lead_to_bitrix24_dev(user_data[chat_id])  # Отправка данных в Bitrix24
        user_steps[chat_id] = 0

    elif step == 3 and user_data[chat_id]['request_type'] == 722: #нужна консультация
        user_data[chat_id]['name'] = message.text
        ask_for_contact(chat_id)
        user_steps[chat_id] = 0


def ask_for_contact(chat_id):
    # Создаем клавиатуру с кнопкой "Поделиться контактом"
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    # Кнопка для запроса номера телефона
    contact_button = KeyboardButton("📞 Поделиться контактом", request_contact=True)

    # Добавляем кнопку на клавиатуру
    markup.add(contact_button)

    # Отправляем сообщение с клавиатурой
    msg = bot.send_message(chat_id, "Пожалуйста, поделитесь вашим номером телефона:", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_contact)


def handle_contact(message):
    chat_id = message.chat.id

    # Если пользователь поделился контактом
    if message.contact:
        user_data[chat_id]['phone'] = message.contact.phone_number
    else:
        # Если пользователь не поделился контактом, берем текст из сообщения
        user_data[chat_id]['phone'] = message.text

    # Отправляем финальное сообщение и передаем данные в систему
    bot.send_message(chat_id, "Спасибо за обращение! Перевожу вас на сотрудника службы поддержки.")
    send_message_to_chat(
        user_data[chat_id]['companyname'],
        user_data[chat_id]['name'],
        user_data[chat_id]['phone']
    )  # Отправка данных в Bitrix24

    # Сбрасываем шаги
    user_steps[chat_id] = 0


# Основная функция для обработки всех шагов фидбека
def ask_feedback_question(message):
    chat_id = message.chat.id
    step = user_steps.get(chat_id, 1)  # Получаем текущий шаг или ставим 1 по умолчанию

    if step == 1:
        msg = bot.send_message(chat_id, "Представьтесь, пожалуйста:")
        user_steps[chat_id] = 2
        bot.register_next_step_handler(msg, ask_feedback_question)

    elif step == 2:
        user_data[chat_id]['name'] = message.text
        msg = bot.send_message(chat_id, "Напишите название компании:")
        user_steps[chat_id] = 3
        bot.register_next_step_handler(msg, ask_feedback_question)

    elif step == 3:
        user_data[chat_id]['company'] = message.text
        msg = bot.send_message(chat_id, "Что вам понравилось в нашем сотрудничестве?")
        user_steps[chat_id] = 4
        bot.register_next_step_handler(msg, ask_feedback_question)

    elif step == 4:
        user_data[chat_id]['liked'] = message.text
        msg = bot.send_message(chat_id, "Что превзошло ваши ожидания?")
        user_steps[chat_id] = 5
        bot.register_next_step_handler(msg, ask_feedback_question)

    elif step == 5:
        user_data[chat_id]['exceeded_expectations'] = message.text
        msg = bot.send_message(chat_id, "Можете ли рекомендовать нас?")
        user_steps[chat_id] = 6
        bot.register_next_step_handler(msg, ask_feedback_question)

    elif step == 6:
        user_data[chat_id]['recommend'] = message.text

        # Отправляем данные в Bitrix24
        add_feedback_to_bitrix24(user_data[chat_id])

        # Подтверждение пользователю
        bot.send_message(chat_id, "Спасибо за ваш отзыв!", reply_markup=types.ReplyKeyboardRemove())

        # Очистка данных после отправки
        user_data.pop(chat_id, None)
        user_steps.pop(chat_id, None)
        user_steps[chat_id] = 0

def ask_claim_question(message):
    chat_id = message.chat.id
    step = user_steps.get(chat_id, 1)  # Получаем текущий шаг или ставим 1 по умолчанию

    if step == 1:
        msg = bot.send_message(chat_id, "Представьтесь, пожалуйста:")
        user_steps[chat_id] = 2
        bot.register_next_step_handler(msg, ask_claim_question)

    elif step == 2:
        user_data[chat_id]['name'] = message.text
        msg = bot.send_message(chat_id, "Напишите название компании:")
        user_steps[chat_id] = 3
        bot.register_next_step_handler(msg, ask_claim_question)

    elif step == 3:
        user_data[chat_id]['company'] = message.text
        msg = bot.send_message(chat_id, "Укажите вашу должность")
        user_steps[chat_id] = 4
        bot.register_next_step_handler(msg, ask_claim_question)

    elif step == 4:
        user_data[chat_id]['position'] = message.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        contact_button = types.KeyboardButton(text="Поделиться контактом", request_contact=True)
        markup.add(contact_button)
        msg = bot.send_message(chat_id, "Поделитесь вашим номером телефона:", reply_markup=markup)
        user_steps[chat_id] = 5
        bot.register_next_step_handler(msg, ask_claim_question)

    elif step == 5:
        if message.contact:
            user_data[chat_id]['phone'] = message.contact.phone_number
        else:
            user_data[chat_id]['phone'] = message.text
        msg = bot.send_message(chat_id, "Укажите ваш Email")
        user_steps[chat_id] = 6
        bot.register_next_step_handler(msg, ask_claim_question)

    elif step == 6:
        user_data[chat_id]['email'] = message.text
        msg = bot.send_message(chat_id, "Опишите ситуацию")
        user_steps[chat_id] = 7
        bot.register_next_step_handler(msg, ask_claim_question)

    elif step == 7:
        user_data[chat_id]['description'] = message.text
        # Отправляем данные в Bitrix24
        add_claim_to_bitrix24(user_data[chat_id])

        # Подтверждение пользователю
        bot.send_message(chat_id, "Спасибо, что помогаете стать нам лучше!", reply_markup=types.ReplyKeyboardRemove())

        # Очистка данных после отправки
        user_data.pop(chat_id, None)
        user_steps.pop(chat_id, None)
        user_steps[chat_id] = 0

# Функция для отправки отзыва в Bitrix24
def add_claim_to_bitrix24(data):
    BITRIX24_WEBHOOK_URL = "https://tamplier.bitrix24.ru/rest/572/rebx9fxt0uas87fp/crm.item.add.json?entityTypeId=1040"

    payload = {
        "fields": {
            "TITLE": f"Замечание от {data['name']}",
            'ufCrm42_1727215586844': data['name'],
            'ufCrm42_1727215595862': data['company'],
            'ufCrm42_1727215605371': data['position'],
            'ufCrm42_1727215615528': data['phone'],
            'ufCrm42_1727215623763': data['email'],
            'ufCrm42_1727215669357': data['description']
        }
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(BITRIX24_WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
    except requests.exceptions.RequestException as e:
        print(f"Failed to send feedback to Bitrix24: {response.text}")

# Функция для отправки отзыва в Bitrix24
def add_feedback_to_bitrix24(data):
    BITRIX24_WEBHOOK_URL = "https://tamplier.bitrix24.ru/rest/572/rebx9fxt0uas87fp/crm.item.add.json?entityTypeId=1044"

    payload = {
        "fields": {
            "TITLE": f"Отзыв от {data['name']}",
            'ufCrm44_1727215941830': data['name'],
            'ufCrm44_1727215952066': data['company'],
            'ufCrm44_1727215969231': data['liked'],
            'ufCrm44_1727215983425': data['exceeded_expectations'],
            'ufCrm44_1727216001868': data['recommend']  # Рекомендация
        }
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(BITRIX24_WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
    except requests.exceptions.RequestException as e:
        print(f"Failed to send feedback to Bitrix24: {response.text}")

#Элемент смарт-процесса для Аварии
def add_lead_to_bitrix24_avaria(data):
    BITRIX24_WEBHOOK_URL = "https://tamplier.bitrix24.ru/rest/572/rebx9fxt0uas87fp/crm.item.add.json?entityTypeId=1036"
    payload = {
        "fields": {
            "TITLE": f"{data['name']} {data['phone']}",
            "NAME": data['name'],
            'ufCrm40_1724763200': data['request_type'],
            'ufCrm40_1724763274': data['issue'],
            'ufCrm40_1725624322023': data['companyname'],
            "PHONE": [{"VALUE": data['phone'], "VALUE_TYPE": "WORK"}]
        }
    }
    if 'screenshots' in data and data['screenshots']:
        file_id = data['screenshots'].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path

        # Загрузите файл с Telegram
        file_content = bot.download_file(file_path)
        # Кодируем файл в Base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')

        # Добавляем файл к запросу
        payload['fields']['ufCrm40_1724763290'] = [
            {
                "name": "filename.ext",
                "content": file_base64
            }
        ]

    # Отправляем запрос
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(BITRIX24_WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
    except requests.exceptions.RequestException as e:

        return

    if response.status_code == 200:
        lead_id = response.json().get("result", {}).get("item", {}).get("id")
        if lead_id:
            delete_user_messages(data['chat_id'])  # Удаление сообщений перед отправкой финального
            send_confirmation_message_avaria(data.get('chat_id'), lead_id, data['companyname'], data['issue'], data['name'],data['phone'])
    else:
        print(f"Failed to add lead to Bitrix24: {response.text}")

#Отправка заключительного сообщения для Аварии
def send_confirmation_message_avaria(chat_id, lead_id, companyname, issue, name, phone):
    if not chat_id:
        print("Chat ID is missing")
        return

    message_text = f"Спасибо, {name}!\n" \
                   f"Ваша заявка принята в работу. Ей присвоен номер - {lead_id}.\n" \
                   f"Состав заявки:\n1.Название компании: {companyname}\n" \
                   f"2.Задача: {issue}\n" \
                   f"3.Имя: {name}\n" \
                   f"4.Номер телефона: {phone}\n"

    try:
        bot.send_message(chat_id, message_text)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error sending message to chat {chat_id}: {e}")

#Элемент смарт-процесса для Ошибки в работе
def add_lead_to_bitrix24_error(data):
    BITRIX24_WEBHOOK_URL = "https://tamplier.bitrix24.ru/rest/572/rebx9fxt0uas87fp/crm.item.add.json?entityTypeId=1036"
    payload = {
        "fields": {
            "TITLE": f"{data['name']} {data['phone']}",
            "NAME": data['name'],
            'ufCrm40_1724763200': data['request_type'],
            'ufCrm40_1724763274': data['error_description'],
            'ufCrm40_1725624322023': data['companyname'],
            "PHONE": [{"VALUE": data['phone'], "VALUE_TYPE": "WORK"}]
        }
    }
    if 'screenshots' in data and data['screenshots']:
        file_id = data['screenshots'].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path

        # Загрузите файл с Telegram
        file_content = bot.download_file(file_path)
        # Кодируем файл в Base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')

        # Добавляем файл к запросу
        payload['fields']['ufCrm40_1724763290'] = [
            {
                "name": "filename.ext",
                "content": file_base64
            }
        ]

    # Отправляем запрос
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(BITRIX24_WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
    except requests.exceptions.RequestException as e:

        return

    if response.status_code == 200:
        lead_id = response.json().get("result", {}).get("item", {}).get("id")
        if lead_id:
            delete_user_messages(data['chat_id'])  # Удаление сообщений перед отправкой финального
            send_confirmation_message_teach(data.get('chat_id'), lead_id, data['companyname'], data['error_description'], data['name'],data['phone'])
    else:
        print(f"Failed to add lead to Bitrix24: {response.text}")

#Отправка заключительного сообщения для Ошибки в работе
def send_confirmation_message_error(chat_id, lead_id, companyname, error_description, name, phone):
    if not chat_id:
        print("Chat ID is missing")
        return

    message_text = f"Спасибо, {name}!\n" \
                   f"Ваша заявка принята в работу. Ей присвоен номер - {lead_id}.\n" \
                   f"Состав заявки:\n1.Название компании: {companyname}\n" \
                   f"2.Задача: {error_description}\n" \
                   f"3.Имя: {name}\n" \
                   f"4.Номер телефона: {phone}\n"

    try:
        bot.send_message(chat_id, message_text)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error sending message to chat {chat_id}: {e}")

#Элемент смарт-процесса для Обучение
def add_lead_to_bitrix24_teach(data):
    BITRIX24_WEBHOOK_URL = "https://tamplier.bitrix24.ru/rest/572/rebx9fxt0uas87fp/crm.item.add.json?entityTypeId=1036"
    payload = {
        "fields": {
            "TITLE": f"{data['name']} {data['phone']}",
            "NAME": data['name'],
            'ufCrm40_1724763200': data['request_type'],
            'ufCrm40_1724763274': data['training_topic'],
            'ufCrm40_1725624322023': data['companyname'],
            "PHONE": [{"VALUE": data['phone'], "VALUE_TYPE": "WORK"}]
        }
    }
    response = requests.post(BITRIX24_WEBHOOK_URL, json=payload)
    if response.status_code == 200:
        lead_id = response.json().get("result", {}).get("item", {}).get("id")
        if lead_id:
            delete_user_messages(data['chat_id'])  # Удаление сообщений перед отправкой финального
            send_confirmation_message_teach(data.get('chat_id'), lead_id, data['companyname'], data['training_topic'], data['name'],data['phone'])
    else:
        print(f"Failed to add lead to Bitrix24: {response.text}")

#Отправка заключительного сообщения для Обучение
def send_confirmation_message_teach(chat_id, lead_id, companyname, training_topic, name, phone):
    if not chat_id:
        print("Chat ID is missing")
        return

    message_text = f"Спасибо, {name}!\n" \
                   f"Ваша заявка принята в работу. Ей присвоен номер - {lead_id}.\n" \
                   f"Состав заявки:\n1.Название компании: {companyname}\n" \
                   f"2.Задача: {training_topic}\n" \
                   f"3.Имя: {name}\n" \
                   f"4.Номер телефона: {phone}\n"

    try:
        bot.send_message(chat_id, message_text)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error sending message to chat {chat_id}: {e}")

#Элемент смарт-процесса для Настройка Битрикс24
def add_lead_to_bitrix24_settings(data):
    BITRIX24_WEBHOOK_URL = "https://tamplier.bitrix24.ru/rest/572/rebx9fxt0uas87fp/crm.item.add.json?entityTypeId=1036"
    payload = {
        "fields": {
            "TITLE": f"{data['name']} {data['phone']}",
            "NAME": data['name'],
            'ufCrm40_1724763200': data['request_type'],
            'ufCrm40_1724763274': data['customization_request'],
            'ufCrm40_1725624322023': data['companyname'],
            "PHONE": [{"VALUE": data['phone'], "VALUE_TYPE": "WORK"}]
        }
    }
    # Если есть файлы, добавляем их в Base64
    if 'attachments' in data and data['attachments']:
        file_id = data['attachments'].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path

        # Загрузите файл с Telegram
        file_content = bot.download_file(file_path)
        # Кодируем файл в Base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')

        # Добавляем файл к запросу
        payload['fields']['ufCrm40_1724763290'] = [
            {
                "name": "filename.ext",
                "content": file_base64
            }
        ]

    # Отправляем запрос
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(BITRIX24_WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
    except requests.exceptions.RequestException as e:

        return

    if response.status_code == 200:
        lead_id = response.json().get("result", {}).get("item", {}).get("id")
        if lead_id:
            delete_user_messages(data['chat_id'])  # Удаление сообщений перед отправкой финального
            send_confirmation_message_settings(data.get('chat_id'), lead_id, data['companyname'], data['customization_request'], data['name'],data['phone'])
    else:
        print(f"Failed to add lead to Bitrix24: {response.text}")

#Отправка заключительного сообщения для Настройка Битрикс24
def send_confirmation_message_settings(chat_id, lead_id, companyname, customization_request, name, phone):
    if not chat_id:
        print("Chat ID is missing")
        return

    message_text = f"Спасибо, {name}!\n" \
                   f"Ваша заявка принята в работу. Ей присвоен номер - {lead_id}.\n" \
                   f"Состав заявки:\n1.Название компании: {companyname}\n" \
                   f"2.Задача: {customization_request}\n" \
                   f"3.Имя: {name}\n" \
                   f"4.Номер телефона: {phone}\n"

    try:
        bot.send_message(chat_id, message_text)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error sending message to chat {chat_id}: {e}")

#Элемент смарт-процесса для Разработка нового функционала
def add_lead_to_bitrix24_dev(data):
    BITRIX24_WEBHOOK_URL = "https://tamplier.bitrix24.ru/rest/572/rebx9fxt0uas87fp/crm.item.add.json"

    payload = {
        "entityTypeId": 1036,
        "fields": {
            "TITLE": f"{data['name']} {data['phone']}",
            "NAME": data['name'],
            'ufCrm40_1724763200': data['request_type'],
            'ufCrm40_1724763274': data['comments'],
            'ufCrm40_1725624322023': data['companyname'],
            "PHONE": [{"VALUE": data['phone'], "VALUE_TYPE": "WORK"}]
        }
    }

    # Если есть файлы, добавляем их в Base64
    if 'files' in data and data['files']:
        file_id = data['files'].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path

        # Загрузите файл с Telegram
        file_content = bot.download_file(file_path)
        # Кодируем файл в Base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')

        # Добавляем файл к запросу
        payload['fields']['ufCrm40_1724763290'] = [
            {
                "name": "filename.ext",
                "content": file_base64
            }
        ]

    # Отправляем запрос
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(BITRIX24_WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
    except requests.exceptions.RequestException as e:

        return

    if response.status_code == 200:
        lead_id = response.json().get("result", {}).get("item", {}).get("id")
        if lead_id:
            delete_user_messages(data['chat_id'])  # Удаление сообщений перед отправкой финального
            send_confirmation_message_dev(data.get('chat_id'), lead_id, data['companyname'], data['comments'], data['name'], data['phone'])
    else:
        print(f"Failed to add lead to Bitrix24: {response.text}")

#Открытая линия
def send_message_to_chat(companyname, name, phone):
    BITRIX24_WEBHOOK_URL = "https://tamplier.bitrix24.ru/rest/572/rebx9fxt0uas87fp/im.message.add.json"
    payload = {
        "CHAT_ID": 2,  # ID чата
        "MESSAGE": "Клиенту нужна консультация\n"\
                   f"Имя: {name}\n" \
                   f"Состав заявки:\n1. Название компании: {companyname}\n" \
                   f"2. Имя: {name}\n" \
                   f"3. Номер телефона: {phone}\n"  # Сообщение от клиента
    }
    response = requests.post(BITRIX24_WEBHOOK_URL, json=payload)
    result = response.json()

    if response.status_code == 200 and result.get('result'):
        print("Message sent successfully")
        return result['result']
    else:
        print(f"Failed to send message: {result}")
        return None

#Отправка заключительного сообщения для Разработка нового функционала
def send_confirmation_message_dev(chat_id, lead_id, companyname, comments, name, phone):
    if not chat_id:
        print("Chat ID is missing")
        return

    message_text = f"Спасибо, {name}!\n" \
                   f"Ваша заявка принята в работу. Ей присвоен номер - {lead_id}.\n" \
                   f"Состав заявки:\n1.Название компании: {companyname}\n" \
                   f"2.Задача: {comments}\n" \
                   f"3.Имя: {name}\n" \
                   f"4.Номер телефона: {phone}\n"

    try:
        bot.send_message(chat_id, message_text)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error sending message to chat {chat_id}: {e}")

# Функция для обработки команды /claim
@bot.message_handler(commands=['claim'])
def start_feedback(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    user_steps[chat_id] = 1  # Начальный шаг
    ask_claim_question(message)

# Функция для обработки команды /feedback
@bot.message_handler(commands=['feedback'])
def start_feedback(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    user_steps[chat_id] = 1  # Начальный шаг
    ask_feedback_question(message)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    welcome_text = (
        "👋🏻Добро пожаловать! Я бот Tamplier digital.\nСо мной Вы можете : \n\n❗️1.Подать заявку на неисправность ( авария, ошибка в работе портала)\n\n🛠2.Доработку и внедрение новых возможностей для вашей компании\n\n🔔3.Консультацию по функционалу Битрикс24\n\n📩4.Оставить обращение для специалиста нашей компании и пройти онлайн тестирование. \n\n" \
        "Вот список команд, которые я могу выполнить:\n" \
        "/start - Запустить бота\n" \
        "/service - Подать заявку\n" \
        "/help - Получить помощь по командам бота\n"\
        "/feedback - оставить отзыв о работе\n"\
        "/claim - оставить замечание по работе")
    bot.send_message(chat_id, welcome_text)


# Обработчик команды /service
@bot.message_handler(commands=['service'])
def service(message):
    chat_id = message.chat.id
    user_steps[chat_id] = 0
    request_next_part_of_data(message)


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    chat_id = message.chat.id
    help_text = "Я могу помочь вам с следующими действиями:\n" \
                "/start - Запустить бота\n" \
                "/service - Подать заявку\n" \
                "/feedback - Оставить отзыв о работе\n"\
                "/claim - Оставить замечание по работе"
    bot.send_message(chat_id, help_text)

#обработчик инлайн кнопок
@bot.callback_query_handler(func=lambda call: call.data in request_type_mapping)
def handle_request_type(call: CallbackQuery):
    chat_id = call.message.chat.id
    request_type_id = request_type_mapping[call.data]

    user_data[chat_id] = user_data.get(chat_id, {})
    user_data[chat_id]['request_type'] = request_type_id

    if request_type_id == 716:  # Авария
        msg = bot.send_message(chat_id, "Вы выбрали тип обращения: Авария.\nНапишите, пожалуйста, что именно не работает. Если не работает конкретный раздел – укажите название раздела.")
    elif request_type_id == 718:  # Ошибка в работе
        msg = bot.send_message(chat_id, "Вы выбрали тип обращения: Ошибка в работе.\nНапишите, пожалуйста, что именно не работает. Если не работает конкретный раздел – укажите название раздела..")
    elif request_type_id == 798:  # Обучение
        msg = bot.send_message(chat_id, "Вы выбрали тип обращения: Обучение.\nНапишите, пожалуйста, по какому функционалу Битрикс24 нужно обучение.")
    elif request_type_id == 720:  # Настройка Битрикс24
        msg = bot.send_message(chat_id, "Вы выбрали тип обращения: Настройка Битрикс24.\nНапишите, пожалуйста, что нужно настроить в вашем Битрикс24.")
    elif request_type_id == 724:  # Разработка нового функционала
        msg = bot.send_message(chat_id, "Вы выбрали тип обращения: Разработка нового функционала.\nПриложите файлы с ТЗ / пожеланиями.")
    elif request_type_id == 798:  # Обучение
        msg = bot.send_message(chat_id, "Вы выбрали тип обращения: Обучение.\nНапишите, пожалуйста, по какому функционалу Битрикс24 нужно обучение?.")
    elif request_type_id == 722:  # Открытая линия
        msg = bot.send_message(chat_id, "Вы выбрали тип обращения: Нужна консультация.\nНапишите, пожалуйста, ваше имя.")
    else:
        msg = bot.send_message(chat_id, f"Вы выбрали тип обращения: {call.data}. Опишите вашу проблему.")

    bot.register_next_step_handler(msg, request_next_part_of_data)
    user_messages[chat_id].append(msg.message_id)
    user_steps[chat_id] = 3


# Обработчик для сообщений с текстом (ответы на тест)
@bot.message_handler(func=lambda message: user_steps.get(message.chat.id, 0) == 7)
def handle_test_answer(message):
    chat_id = message.chat.id
    question_index = test_results[chat_id]["current_question"]

    if question_index >= len(test_questions):
        return

    question_data = test_questions[question_index]
    selected_answer = message.text

    if selected_answer in question_data["answers"]:
        selected_answer_index = question_data["answers"].index(selected_answer)
        correct_answer = question_data["correct"]

        if selected_answer_index == correct_answer:
            test_results[chat_id]["correct_answers"] += 1

    test_results[chat_id]["current_question"] += 1
    ask_test_question(message)


# Команда /test
# @bot.message_handler(commands=['test'])
# def start_test(message):
#     chat_id = message.chat.id
#     test_results[chat_id] = {"correct_answers": 0, "current_question": 0}
#     msg = bot.send_message(chat_id,
#                            "Тест состоит из 5-ти вопросов, которые помогут определить ваш уровень знания основного функционала Битрикс24. Введите ваше имя:")
#     bot.register_next_step_handler(msg, ask_test_question)
#
#
# def ask_test_question(message):
#     chat_id = message.chat.id
#     question_index = test_results[chat_id]["current_question"]
#
#     if question_index < len(test_questions):
#         question_data = test_questions[question_index]
#         markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
#
#         for answer in question_data["answers"]:
#             markup.add(KeyboardButton(answer))
#
#         bot.send_message(chat_id, question_data["question"], reply_markup=markup)
#         user_steps[chat_id] = 7  # Установим шаг для обработки ответов на вопросы
#
#     else:
#         correct_answers = test_results[chat_id]["correct_answers"]
#         bot.send_message(chat_id,
#                          f"Тест завершен! Вы ответили правильно на {correct_answers} из {len(test_questions)} вопросов.")
#         user_steps[chat_id] = 0


# Обработчик неизвестных команд и сообщений
@bot.message_handler(func=lambda message: True)
def handle_unknown_message(message):
    chat_id = message.chat.id
    help_text = ("Прошу прощения, не совсем вас понял. Вот команды, которые я могу выполнить:\n"
                 "/start - Запустить бота\n" \
                 "/service - Подать заявку\n" \
                 "/feedback - Оставить отзыв о работе\n"\
                 "/claim - Оставить замечание по работе")
    bot.send_message(chat_id, help_text)


# Запуск бота
bot.polling(none_stop=True)