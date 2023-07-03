import configparser
import os
import sys
from pathlib import Path
from time import sleep
from db import BotDB
import telebot
import random
from datetime import datetime
import time
from telebot import types

#Настройки
config_path = os.path.join(sys.path[0], 'settings.ini')
config = configparser.ConfigParser()
config.read(config_path)
#TELEGRAM
BOT_TOKEN = config.get('Telegram', 'listen_bot_token')
GROUP_FOR_LOGS = config.get('Telegram', 'group_for_logs')
IMPORTANT_LOGS = config.get('Telegram', 'important_logs')
PREVIEW_LINK = config.getboolean('Telegram', 'PREVIEW_LINK')
#SETTINGS
LOGS = config.getboolean('Settings', 'logs')


#Инициализируем бота и базу
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
BotDB = BotDB('tg-bot-database')



def telegram_bot():
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        try:
            name_stick_hello = list(Path('Stick').rglob('Hello_*'))
            number_stick_hello = random.randint(1, len(name_stick_hello))
            random_stick_hello = open(name_stick_hello[number_stick_hello], 'rb')
            #logging
            if LOGS:
                bot.forward_message(chat_id=GROUP_FOR_LOGS,
                                from_chat_id=message.chat.id,
                                message_id=message.message_id)
            bot.send_sticker(message.chat.id, random_stick_hello)
            sleep(0.3)
            #Сохраняем инфо о юзере в БД
            user_id = message.from_user.id
            first_name = message.from_user.first_name
            full_name = message.from_user.full_name
            username = message.from_user.username
            language_code = message.from_user.language_code
            time_UTC = int(time.time())
            date_added = datetime.fromtimestamp(time_UTC)
            BotDB.add_new_user_in_db(user_id, first_name, full_name, username, language_code, date_added)
            #Создаем папку для войсов
            folder_path = 'voice_users'
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            else:
                pass
        except:
            if LOGS:
                bot.send_message(IMPORTANT_LOGS, "Отправка приветственных стикеров лажает")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton("🎤Высказаться")
        item2 = types.KeyboardButton("🎧Послушать")
        markup.add(item1, item2)
        bot.send_message(message.chat.id, "<b>Привет.</b>", parse_mode='html', reply_markup=markup,
                         disable_web_page_preview=not PREVIEW_LINK)
        time.sleep(0.3)
        bot.send_message(message.chat.id, "<i>Здесь можно послушать голосовые сообщения от совершенно незнакомых людей</i>", parse_mode='html', reply_markup=markup,
                         disable_web_page_preview=not PREVIEW_LINK)
        time.sleep(1)
        bot.send_message(message.chat.id, "Это почти как написать письмо, положить его в бутылку и швырнуть в океан. Никогда не узнаешь, послушал его кто-то или нет и ответить тоже не получится..", parse_mode='html', reply_markup=markup,
                         disable_web_page_preview=not PREVIEW_LINK)
        time.sleep(0.8)
        bot.send_message(message.chat.id, "Если не знаешь, что сказать, можешь просто прочитать любое текстовое сообщение из недавно полученных или отправленных (или спеть, рассказать стихотворенье)", parse_mode='html', reply_markup=markup,
                         disable_web_page_preview=not PREVIEW_LINK)
        time.sleep(0.8)
        msg = bot.send_message(message.chat.id, "<b>ну всё, достаточно инструкций. записывайся! Микрофон твой - </b> 🎤", parse_mode='html', reply_markup=markup,
                         disable_web_page_preview=not PREVIEW_LINK)
        bot.register_next_step_handler(msg, standup)


    def last_message():
        # функция с отображением сообщения "Последнее сообщение было записано"
        date_from_db = BotDB.last_date_audio()
        parse_date = datetime.strptime(date_from_db, "%Y-%m-%d %H:%M:%S")
        last_voice_time_timestamp = time.mktime(parse_date.timetuple())
        time_now_timestamp = time.time()
        date_difference = time_now_timestamp - last_voice_time_timestamp
        # считаем минуты, часы, дни
        much_minutes_ago = round(date_difference / 60, 0)
        much_hour_ago = round(date_difference / 3600, 0)
        much_days_ago = int(round(much_hour_ago / 24, 0))
        message_with_date = ''
        if much_minutes_ago <= 60:
            word_minute = plural_time(1, much_minutes_ago)
            message_with_date = f'<b>Последнее сообщение было записано {word_minute} назад</b>'
        elif much_minutes_ago > 60 and much_hour_ago <= 24:
            word_hour = plural_time(2, much_hour_ago)
            message_with_date = f'<b>Последнее сообщение было записано {word_hour} назад</b>'
        elif much_hour_ago > 24:
            word_day = plural_time(3, much_days_ago)
            message_with_date = f'<b>Последнее сообщение было записано {word_day} назад</b>'
        return message_with_date

    def standup(message):
        # Клавиатуру добавляем
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton("🎤Высказаться")
        item2 = types.KeyboardButton("🎧Послушать")
        markup.add(item1, item2)
        if message.text == '🎤Высказаться':
            markup = types.ReplyKeyboardRemove()
            if LOGS:
                # logging
                bot.forward_message(chat_id=GROUP_FOR_LOGS,
                                    from_chat_id=message.chat.id,
                                    message_id=message.message_id)
            msg = bot.send_message(chat_id=message.chat.id, text='Хорошо, теперь пришли мне свое голосовое сообщение', reply_markup=markup)
            is_exists = BotDB.is_audio_exists()
            if is_exists == True:
                message_with_date = last_message()
                msg = bot.send_message(chat_id=message.chat.id, text=message_with_date, parse_mode="html")
                bot.register_next_step_handler(msg, save_voice_message)
            else:
                bot.register_next_step_handler(msg, save_voice_message)
        elif message.text == '🎧Послушать':
            check_audio = BotDB.check_listen_audio(user_id=message.from_user.id)
            list_audio = list(check_audio)
            if list_audio == []:
                msg = bot.send_message(message.chat.id, 'Прости, ты прослушал все аудио😔. Возвращайся позже, возможно наша база пополнится', reply_markup=markup)
                is_audio_exist = BotDB.is_audio_exists()
                if is_audio_exist == True:
                    message_with_date = last_message()
                    msg = bot.send_message(chat_id=message.chat.id, text=message_with_date, parse_mode="html")
                    bot.register_next_step_handler(msg, standup)
                else:
                    bot.register_next_step_handler(msg, standup)
            else:
                number_element = random.randint(0, len(list_audio) - 1)
                audio_for_user = check_audio[number_element]
                path = Path(f'voice_users/{audio_for_user}.ogg')
                voice = open(path, 'rb')
                #Маркируем сообщение как прослушанное
                BotDB.mark_listened_audio(audio_for_user, user_id=message.from_user.id)

                msg = bot.send_voice(message.chat.id, voice=voice, reply_markup=markup)
                bot.register_next_step_handler(msg, standup)

            if LOGS:
                # logging
                bot.forward_message(chat_id=GROUP_FOR_LOGS,
                                    from_chat_id=message.chat.id,
                                    message_id=message.message_id)
        elif message.text == '/restart':
            msg = bot.send_message(message.chat.id, 'Я перезапущен, и готов к работе🥳', reply_markup=markup)
            bot.forward_message(chat_id=GROUP_FOR_LOGS,
                                from_chat_id=message.chat.id,
                                message_id=message.message_id)
            bot.register_next_step_handler(msg, standup)
        else:
            msg = bot.send_message(chat_id=message.chat.id, text='Я тебя не понял, воспользуйся меню', reply_markup=markup)
            bot.register_next_step_handler(msg, standup)


    def plural_time(type, n):
        word = []
        if type == 1:
            word = ['минуту', 'минуты', 'минут']
        elif type == 2:
            word = ['час', 'часа', 'часов']
        elif type == 3:
            word = ['день', 'дня', 'дней']
        else:
            pass

        if n % 10 == 1 and n % 100 != 11:
            p = 0
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            p = 1
        else:
            p = 2
        new_number = int(n)
        return str(new_number) + ' ' + word[p]

    def save_voice_message(message):
        if message.content_type == 'voice':
            file_id = 1
            #Проверяем что запись о файле есть в базе данных
            is_having_audio_from_user = BotDB.get_last_user_audio_record(user_id=message.from_user.id)
            if is_having_audio_from_user is False:
                #Если нет, то генерируем имя файла
                file_name = f'message_from_{message.from_user.id}_number_{file_id}'
            else:
                #Иначе берем последнюю запись из БД, добавляем к ней 1, и создаем новую запись
                file_name = BotDB.get_path_for_audio_record(user_id=message.from_user.id)
                file_id = BotDB.get_id_for_audio_record(message.from_user.id) + 1
                path = Path(f'voice_users/{file_name}.ogg')
                if path.exists():
                    file_name = f'message_from_{message.from_user.id}_number_{file_id}'
                else:
                    pass
            #Собираем инфо о сообщении
            author_id = message.from_user.id
            time_UTC = int(time.time())
            date_added = datetime.fromtimestamp(time_UTC)
            #Сохраняем в базку
            BotDB.add_audio_record(file_name, author_id, date_added, 0, file_id)
            #Сохраняем файл на сервер
            file_info = bot.get_file(message.voice.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(f'voice_users/{file_name}.ogg', 'wb') as new_file:
                new_file.write(downloaded_file)
            #инициализируем кнопки
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1 = types.KeyboardButton("🎤Высказаться")
            item2 = types.KeyboardButton("🎧Послушать")
            markup.add(item1, item2)
            bot.send_message(chat_id=message.chat.id, text='Окей, сохранил!👌', reply_markup=markup)
            #menu_standup(message=message)
            bot.register_next_step_handler(message, standup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1 = types.KeyboardButton("🎤Высказаться")
            item2 = types.KeyboardButton("🎧Послушать")
            markup.add(item1, item2)
            msg = bot.send_message(chat_id=message.chat.id, text='Я тебя не понимаю🤷‍♀️ запиши голосовое', reply_markup=markup)
            bot.register_next_step_handler(msg, standup)

    @bot.message_handler(commands=['restart'])
    def restart_function(message):
        return standup(message)

if __name__ == '__main__':
    telegram_bot()
    try:
        bot.polling(none_stop=True)
        bot.enable_save_next_step_handlers(delay=2)
        bot.load_next_step_handlers()
    except ConnectionError as e:
        if LOGS:
            bot.send_message(IMPORTANT_LOGS, "Ошибка соединения, потерял войс бот связь")
    except Exception as r:
        if LOGS:
            bot.send_message(IMPORTANT_LOGS, "Произошло что-то непредвиденное, хелп. Войс бот болеет")
    finally:
        if LOGS:
            bot.send_message(IMPORTANT_LOGS, 'Я войс бот упал, помогите')