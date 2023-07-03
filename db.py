import sqlite3
import configparser
import os
import sys

config_path = os.path.join(sys.path[0], 'settings.ini')
config = configparser.ConfigParser()
config.read(config_path)
LOGS = config.getboolean('Settings', 'logs')
IMPORTANT_LOGS = config.get('Telegram', 'important_logs')

class BotDB:

    def __init__(self, db_file):
        if os.path.exists(db_file):
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
        else:
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_new_tables()

    def create_new_tables(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS "our_users" (
                                "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                                "user_id"	INTEGER NOT NULL UNIQUE,
                                "first_name"	STRING,
                                "full_name"	STRING,
                                "username"	STRING,
                                "language_code"	STRING,
                                "date_added"	DATE NOT NULL
                            );""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS "listen_audio_users" (
                                "file_name"	TEXT NOT NULL,
                                "user_id"	INTEGER NOT NULL,
                                "is_listen"	BOOLEAN NOT NULL DEFAULT 0
                            );""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS "audio_message_reference" (
                                "id"	INTEGER NOT NULL UNIQUE,
                                "file_name"	TEXT NOT NULL UNIQUE,
                                "author_id"	INTEGER NOT NULL,
                                "date_added"	DATE NOT NULL,
                                "listen_count"	INTEGER NOT NULL,
                                "file_id"	INTEGER NOT NULL,
                                PRIMARY KEY("id")
                            );""")
        self.conn.commit()

    def add_new_user_in_db(self, user_id, first_name, full_name, username, language_code, date_added):
        """Добавляем юзера в базу"""
        self.cursor.execute("INSERT INTO 'our_users' ('user_id', 'first_name', 'full_name', 'username', "
                            "'language_code', 'date_added') VALUES (?, ?, ?, ?, ?, ?)",
                            (user_id, first_name, full_name,
                             username, language_code, date_added))
        return self.conn.commit()


    def add_audio_record(self, file_name, author_id, date_added, listen_count, file_id):
        """Добавляет информацию о войсе юзера в БД"""
        self.cursor.execute("INSERT INTO `audio_message_reference` (file_name, author_id, date_added, listen_count, file_id) VALUES (?, ?, ?, ?, ?)", (file_name, author_id, date_added, listen_count, file_id))
        return self.conn.commit()

    def is_audio_exists(self):
        """Проверяем, есть ли аудио в базе"""
        result = self.cursor.execute("SELECT `id` FROM `audio_message_reference`")
        return bool(len(result.fetchall()))

    def last_date_audio(self):
        """Получаем дату последнего войса"""
        result = self.cursor.execute(
            "SELECT `date_added` FROM `audio_message_reference` ORDER BY date_added DESC LIMIT 1")
        return result.fetchone()[0]

    def get_last_user_audio_record(self, user_id):
        """Получает данные о количестве записей пользователя"""
        result = self.cursor.execute("SELECT `file_id` FROM `audio_message_reference` WHERE `author_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def get_id_for_audio_record(self, user_id):
        """Получает ID аудио сообщения пользователя"""
        result = self.cursor.execute("SELECT `file_id` FROM `audio_message_reference` WHERE `author_id` = ? ORDER BY date_added DESC LIMIT 1",
                                     (user_id,))
        return result.fetchone()[0]

    def get_path_for_audio_record(self, user_id):
        """Получает данные о названии файла"""
        result = self.cursor.execute("SELECT `file_name` FROM `audio_message_reference` WHERE `author_id` = ? ORDER BY date_added DESC LIMIT 1", (user_id,))
        return result.fetchone()[0]

    def check_listen_audio(self, user_id):
        """Проверяет прослушано ли аудио пользователем"""
        query_listen_audio = self.cursor.execute(
            """SELECT l.file_name
            FROM audio_message_reference a
            LEFT JOIN listen_audio_users l ON l.file_name = a.file_name
            WHERE l.user_id = ?
            AND l.file_name IS NOT NULL""" , (user_id,))
        check_sign = query_listen_audio.fetchall()
        query_all_audio = self.cursor.execute('SELECT file_name FROM audio_message_reference WHERE author_id <> ?', (user_id,))
        sign_all_audio = query_all_audio.fetchall()
        new_sign1 = list(set(sign_all_audio) - set(check_sign))
        new_sign = []
        for i in new_sign1:
            new_sign.append(i[0])
        return new_sign

    def mark_listened_audio(self, file_name, user_id):
        """Отмечает аудио прослушанным для конкретного пользователя."""
        result = self.cursor.execute("INSERT INTO `listen_audio_users` (file_name, user_id, is_listen) VALUES (?, ?, ?)", (file_name, user_id, 1))
        return self.conn.commit()

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()

