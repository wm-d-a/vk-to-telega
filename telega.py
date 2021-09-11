import time
import telebot
from config import vk_token, token
import vk_api
import pickle
from vk_api.longpoll import VkLongPoll, VkEventType
import os
import datetime


def log(user, command, *args):  # Logging by template: <date and time> <chat id> <command> <other options>
    now = datetime.datetime.now()
    logs = open('log.txt', 'a')
    log_message = f'[{str(now)}] id: {user}, {command}, {"; ".join(args)}'
    logs.writelines(log_message + '\n')
    logs.close()
    print(log_message)


init = False  # Проверка на первый запуск

is_broadcast = False  # Включена ли трансляция


def main():
    bot = telebot.TeleBot(token)

    try:
        session = vk_api.VkApi(token=vk_token)
        vk = session.get_api()
    except Exception:
        log('before_the_start', 'CHECK ACCESS TOKEN')

    def is_empty():
        global init
        if os.stat("users.pickle").st_size == 0:
            init = True
        else:
            init = False
        return init

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        log(message.from_user.id, '/start')
        bot.reply_to(message,
                     "Привет! Это бот для трансляции сообщений из ВКонтакте в Телеграм.\n"
                     "Чтобы посмотреть список команд введи /help")

    @bot.message_handler(commands=['help'])
    def help(message):
        log(message.from_user.id, '/help')
        commands = {
            '/add': 'Добавить пользователя',
            '/delete': 'Удалить пользователя',
            '/check': 'Показать список пользователей',
            '/vk': 'Старт трансляции',
            '/exit': 'Отключение трансляции',
            '/lang': 'Настройки языка (Скоро будет!)',
        }
        buf = ''
        for key in commands:
            buf += f'{key} - {commands[key]}\n'
        bot.send_message(message.from_user.id, buf)

    @bot.message_handler(commands=['vk'])
    def vk_t(message):  # модуль запуска трансляции
        global is_broadcast
        log(message.from_user.id, '/vk')
        if is_empty():
            log(message.from_user.id, '/vk', 'the list of users is empty')
            bot.send_message(message.from_user.id,
                             'Ваш список отслеживаемых пользователей пуст.'
                             'Для добавления введите /add')
        else:
            bot.send_message(message.from_user.id, 'Вы запустили трансляцию сообщений, введите /exit для отключения')
            is_broadcast = True
            log(message.from_user.id, '/vk', 'starting broadcast')
            broadcast(message)

    @bot.message_handler(commands=['exit'])
    def exit(message):
        log(message.from_user.id, '/exit')
        global is_broadcast
        bot.send_message(message.from_user.id, 'Трансляция отключится через 10 секунд')
        time.sleep(10)
        bot.send_message(message.from_user.id, 'Трансляция отключена')
        is_broadcast = False
        log(message.from_user.id, '/exit', 'Broadcast stopped')

    def broadcast(message):
        global is_broadcast
        log(message.from_user.id, '/vk', 'broadcast', 'starting longpoll')
        longpoll = VkLongPoll(session)
        try:
            with open('users.pickle', 'rb') as f:
                data = pickle.load(f)
        except Exception:
            log(message.from_user.id, '/delete', 'ERROR', "Error opening the list of users")
            bot.send_message(message.from_user.id,
                             'Ошибка при открытии списка юзеров, проверьте наличие файла и повторите команду')
            return 1
        try:
            for event in longpoll.listen():
                if is_broadcast:
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text and event.from_user:
                        if str(event.user_id) in data:
                            id = str(event.user_id)
                            message_resend = f'Пользователь {data[id]} отправил:\n{event.text}'
                            log(message.from_user.id, '/vk', 'broadcast', 'resend message')
                            bot.send_message(message.from_user.id, message_resend)
                else:
                    log(message.from_user.id, '/vk', 'translation', 'stop translation')
                    return 0
        except Exception:
            log(message.from_user.id, '/vk', 'broadcast', 'ERROR', 'Error listening to messages')
            bot.send_message(message.from_user.id, 'Ошибка при отслеживании сообщений, перезапуск трансляции...')
            broadcast(message)

    @bot.message_handler(commands=['add'])
    def add_main(message):
        log(message.from_user.id, '/add')
        if is_empty():
            bot.send_message(message.from_user.id, 'Ваш список пуст')
        else:
            check(message)
        bot.send_message(message.from_user.id, 'Введите ссылку на пользователя')
        bot.register_next_step_handler(message, add)

    def add(message):
        data = {}
        # https://vk.com/delukaaa
        try:
            if is_empty:
                with open('users.pickle', 'rb') as f:
                    data = pickle.load(f)
        except Exception:
            log(message.from_user.id, '/add', 'Error reading a file')
            bot.send_message(message.from_user.id,
                             'Ошибка при открытии списка юзеров, проверьте наличие файла и повторите команду')
            return 1
        try:
            user = vk.users.get(user_ids=[message.text.split('/')[-1]])[0]
        except Exception:
            log(message.from_user.id, "/add", 'ERROR', 'User is not found')
            bot.send_message(message.from_user.id,
                             'Пользователь не найден, проверьте id пользователя и повторите команду /add')
            return 1
        data[user["id"]] = user['first_name'] + ' ' + user['last_name']
        try:
            with open('users.pickle', 'wb') as f:
                pickle.dump(data, f)
        except Exception:
            log(message.from_user.id, '/delete', 'ERROR', "Error while saving a new list")
            bot.send_message(message.from_user.id, 'Ошибка при сохранении исправленного списка, перезапустите команду')
            return 1
        log(message.from_user.id, '/add', 'add new user', f"{user['first_name']} {user['last_name']}")
        bot.send_message(message.from_user.id,
                         f'Пользователь {user["first_name"]} {user["last_name"]} успешно добавлен')

    @bot.message_handler(commands=['delete'])
    def delete_main(message):  # модуль запуска трансляции
        log(message.from_user.id, '/delete')
        if is_empty():
            bot.send_message(message.from_user.id, 'Ваш список уже пуст')
            return 0
        else:
            check(message)
        bot.send_message(message.from_user.id, 'Введите id пользователя')
        bot.register_next_step_handler(message, delete)

    def delete(message):
        try:
            with open('users.pickle', 'rb') as f:
                data = pickle.load(f)
        except Exception:
            log(message.from_user.id, '/delete', 'ERROR', "Error opening the list of users")
            bot.send_message(message.from_user.id,
                             'Ошибка при открытии списка юзеров, проверьте наличие файла и повторите команду')
            return 1
        try:
            user = data[message.text]
            del data[message.text]
        except Exception:
            log(message.from_user.id, '/delete', 'ERROR', 'The user is missing in the list')
            bot.send_message(message.from_user.id, 'Пользователь отсутствует в списке, повторите команду /delete')
            return 1
        try:
            with open('users.pickle', 'wb') as f:
                pickle.dump(data, f)
        except Exception:
            log(message.from_user.id, '/delete', 'ERROR', "Error while saving a new list")
            bot.send_message(message.from_user.id, 'Ошибка при сохранении исправленного списка, перезапустите команду')
            return 1
        log(message.from_user.id, '/delete', f'User {user}(id: {message.text}) removed')
        bot.send_message(message.from_user.id, f'Пользователь {user}(id: {message.text}) успешно удален')

    @bot.message_handler(commands=['check'])
    def check(message):
        log(message.from_user.id, '/check')
        if is_empty():
            bot.send_message(message.from_user.id,
                             'Вы запустили бота впервые, необходимо добавить'
                             'пользователей. Введите /add')
        else:
            try:
                with open('users.pickle', 'rb') as f:
                    data = pickle.load(f)
                    buf = ''
                    for item in data:
                        buf += f'{data[item]} (id: {item})\n'
                    bot.send_message(message.from_user.id, f'В вашем списке:\n' + buf)
            except Exception:
                log(message.from_user.id, '/check', 'Error reading a file')
                bot.send_message(message.from_user.id,
                                 'Ошибка при открытии списка юзеров, проверьте наличие файла и повторите команду')

    bot.polling()


try:
    main()
except Exception:
    log(user='--------', command='\nREBOOT\n')
    main()
