import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(message)s, %(levelname)s, %(name)s')
handler = RotatingFileHandler('main.log', maxBytes=50000000, backupCount=5)
logging.getLogger(__name__).addHandler(handler)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name', 'Неизвестное имя')
    homework_statuses = {
        'approved': 'Ревьюеру всё понравилось, работа зачтена!',
        'rejected': 'К сожалению, в работе нашлись ошибки.',
        'reviewing': 'Работа проходит ревью'
    }
    homework_status = homework.get('status', 'Неизвестный статус')
    try:
        verdict = homework_statuses[homework_status]
    except Exception as e:
        logging.error(e)
        send_message(f'сервер не вернул статус работы {e}')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    if current_timestamp is None:
        current_timestamp = 0
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(url,
                                         headers=headers,
                                         params=payload)
        return homework_statuses.json()
    except Exception as e:
        logging.error(e)
        send_message('Не удалось получить домашнюю работу.')


def send_message(message):
    logging.info(message)
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    logging.debug('Бот запущен')
    bot_error = 'Бот упал с ошибкой:'

    while True:
        try:
            homeworks = get_homeworks(current_timestamp)
            homework = homeworks.get('homeworks')
            if homework[0] is not None:
                send_message(parse_homework_status(homework[0]))
            current_timestamp = homeworks.get('current_date')
            time.sleep(5 * 60)

        except Exception as e:
            logging.exception(f'{bot_error} {e}')
            send_message(f'{bot_error} {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
