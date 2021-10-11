import time
import telebot

from config import vk_token, tele_token
import vk_api
import pickle
from vk_api.longpoll import VkLongPoll, VkEventType
import datetime
import lang


def log(user, command, *args):  # Logging by template: <date and time> <chat id> <command> <other options>
    '''
    :param user: Bot User ID.
    :param command: Current command (process)
    :param args: Other logging arguments

    The function is designed for the logging of processes occurring during the work of the bot
    '''
    """
    :param user: id пользователя бота
    :param command: текущая команда(процесс)
    :param args: Прочие аргументы для логирования

    Функция предназначена для логирования процессов происходящих во время работы бота
    """
    now = datetime.datetime.now()
    logs = open('log.txt', 'a')
    log_message = f'[{str(now)}] id: {user}, {command}, {"; ".join(args)}'
    logs.writelines(log_message + '\n')
    logs.close()
    print(log_message)


is_broadcast = False  # Включена ли трансляция
words_ru = lang.words_ru
words_eng = lang.words_eng
words = words_ru
language = 'ru'


def main():
    bot = telebot.TeleBot(tele_token)

    try:
        session = vk_api.VkApi(token=vk_token)
        vk = session.get_api()
    except Exception:
        log('before_the_start', 'CHECK ACCESS TOKEN')

    def save(message, data):
        try:
            with open('users.pickle', 'wb') as f:
                pickle.dump(data, f)
        except Exception:
            log(message.from_user.id, 'save', 'ERROR', "Error while saving a new list")
            bot.send_message(message.from_user.id, words['save'][0])
            return 1

    def open_users(message):
        try:
            with open('users.pickle', 'rb') as f:
                data = pickle.load(f)
        except Exception:
            log(message.from_user.id, 'open_users', 'ERROR', 'Error reading a file')
            bot.send_message(message.from_user.id, words['open_users'][0])
            return 1
        return data

    def reboot(message, func_name, for_user=''):
        global is_broadcast
        if is_broadcast:
            is_broadcast = False
            bot.send_message(message.from_user.id, words['reboot'][0])
            log(message.from_user.id, func_name, f'Reboot broadcast. {for_user}')
            time.sleep(10)
            is_broadcast = True
            bot.send_message(message.from_user.id, words['reboot'][1])
            broadcast(message)

    @bot.message_handler(commands=['start'])
    def start(message):
        log(message.from_user.id, '/start')
        bot.reply_to(message, words['start'][0])

    @bot.message_handler(commands=['lang'])
    def lang(message):
        global words
        global language
        global words_ru
        global words_eng
        log(message.from_user.id, '/lang')
        if language == 'ru':
            words = words_eng
            bot.send_message(message.from_user.id, words['lang'][0])
            language = 'eng'
        elif language == 'eng':
            words = words_ru
            bot.send_message(message.from_user.id, words['lang'][0])
            language = 'ru'

    @bot.message_handler(commands=['help'])
    def alt_help(message):
        log(message.from_user.id, '/help')
        commands = {
            '/add': words['help'][0],
            '/delete': words['help'][1],
            '/check': words['help'][2],
            '/vk': words['help'][3],
            '/exit': words['help'][4],
            '/delete_all': words['help'][5],
            '/add_all': words['help'][6],
            '/lang': words['help'][7],
        }
        buf = ''
        for key in commands:
            buf += f'{key} - {commands[key]}\n'
        bot.send_message(message.from_user.id, buf)

    @bot.message_handler(commands=['vk'])
    def _vk_(message):  # модуль запуска трансляции
        global is_broadcast
        if not is_broadcast:
            log(message.from_user.id, '/vk')
            if check(message) != 0:
                bot.send_message(message.from_user.id, words['vk'][0])
                is_broadcast = True
                log(message.from_user.id, '/vk', 'starting broadcast')
                broadcast(message)
        else:
            bot.send_message(message.from_user.id, words['vk'][1])

    @bot.message_handler(commands=['exit'])
    def alt_exit(message):
        '''
        The function is responsible for the output from the broadcast
        '''
        """
        Функция отвечает за выход из трансляции
        """
        log(message.from_user.id, '/exit')
        global is_broadcast
        bot.send_message(message.from_user.id, words['exit'][0])
        time.sleep(10)
        bot.send_message(message.from_user.id, words['exit'][1])
        is_broadcast = False
        log(message.from_user.id, '/exit', 'Broadcast stopped')

    def broadcast(message):
        '''
        The function is responsible for broadcast messages
        '''
        '''
        Функция отвечает за трансляцию сообщений
        '''
        global is_broadcast
        log(message.from_user.id, '/vk', 'broadcast', 'starting longpoll')
        longpoll = VkLongPoll(session)

        data = open_users(message)

        try:
            for event in longpoll.listen():
                if is_broadcast:
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.from_user:
                        if str(event.user_id) in data:
                            if event.text:
                                id = str(event.user_id)
                                message_resend = words['broadcast'][0].format(data[id][0], event.text)
                                log(message.from_user.id, '/vk', 'broadcast', 'resend message')
                                if len(event.attachments) != 0:
                                    bot.send_message(message.from_user.id, str(event.attachments))
                                    bot.send_message(message.from_user.id, words['broadcast'][1])
                            else:
                                if len(event.attachments) != 0:
                                    id = str(event.user_id)
                                    message_resend = words['broadcast'][2].format(data[id][0])
                                    log(message.from_user.id, '/vk', 'broadcast', 'resend message')
                                    # bot.send_message(message.from_user.id, str(event.attachments))
                                    bot.send_message(message.from_user.id, words['broadcast'][1])
                            bot.send_message(message.from_user.id, message_resend)
                else:
                    log(message.from_user.id, '/vk', 'broadcast', 'stop broadcast')
                    return 0
        except Exception:
            log(message.from_user.id, '/vk', 'broadcast', 'ERROR', 'Error listening to messages')
            # bot.send_message(message.from_user.id, 'Ошибка при отслеживании сообщений, перезапуск трансляции...')
            broadcast(message)

    @bot.message_handler(commands=['add'])
    def add_main(message):
        '''
        The function launches the user adding module to the list of monitored
        '''
        """
        Функция запускает модуль добавления пользователя в список отслеживаемых
        """
        log(message.from_user.id, '/add')
        check(message)
        bot.send_message(message.from_user.id, words['add_main'][0])
        bot.register_next_step_handler(message, add)

    def add(message):
        '''
        The function adds one user to the list of tracked users
        '''
        """
        Функция добавляет одного пользователя в список отслеживаемых пользователей
        """
        global is_broadcast
        data = open_users(message)
        if data != 1:
            try:
                user = vk.users.get(user_ids=[message.text.split('/')[-1]])[0]
            except Exception:
                log(message.from_user.id, "/add", 'ERROR', 'User is not found')
                bot.send_message(message.from_user.id, words['add'][0])
                return 1

            data[str(user["id"])] = [user['first_name'] + ' ' + user['last_name'], len(data) + 1]

            save(message, data)
            log(message.from_user.id, '/add', 'add new user', f"{user['first_name']} {user['last_name']}")
            bot.send_message(message.from_user.id, words['add'][1].format(user["first_name"], user["last_name"]))
            reboot(message, '/add', f'User {user["first_name"]} {user["last_name"]} add')

    @bot.message_handler(commands=['delete'])
    def delete_main(message):  # модуль запуска трансляции
        '''
        The function starts the user deletion module from the list of monitored
        '''
        """
        Функция запускает модуль удаления пользователя из списка отслеживаемых
        """
        log(message.from_user.id, '/delete')
        if check(message) == 0:
            bot.send_message(message.from_user.id, words['delete_main'][0])
            return 0

        bot.send_message(message.from_user.id, words['delete_main'][1])
        bot.register_next_step_handler(message, delete)

    def delete(message):
        '''
        The function deletes one user from the list of tracked users
        '''
        """
        Функция удаляет одного пользователя из списка отслеживаемых пользователей
        """

        def find_user_id(index, data):
            '''
            :param index: Serial user number from the list of tracked users
            :param data: List of tracked users
            :return: user key (ID in VK)
            The function finds the user's key in the dictionary by order number
            '''
            """
            :param index: порядковый номер пользователя из списка отслеживаемых пользователей
            :param data: список отслеживаемых пользователей
            :return: ключ пользователя (id в ВК)
            Функция находит ключ пользователя в словаре по порядковому номеру
            """
            for key in data:
                if data[key][1] == index:
                    return key

        def change_index(user_id, data):
            '''
            :param user_id: ID of the tracked user in VK
            :param data: List of tracked users
            :return: Returns a list of tracked users with corrected sequence numbers
            Function corrects sequence numbers after deleting a user
            '''
            """
            :param user_id: id отслеживаемого пользователя в ВК
            :param data: список отслеживаемых пользователей
            :return: возвращает список отслеживаемых пользователей с откорректированными порядковыми номерами
            Функция исправляет порядковые номера после удаления пользователя
            """
            change = False
            for key in data:
                if key == user_id:
                    change = True
                if change:
                    data[key][1] -= 1
            return data

        global is_broadcast
        try:
            with open('users.pickle', 'rb') as f:
                data = pickle.load(f)
        except Exception:
            log(message.from_user.id, '/delete', 'ERROR', "Error opening the list of users")
            bot.send_message(message.from_user.id, words['delete'][0])
            return 1
        try:
            user_id = find_user_id(int(message.text), data)
            data = change_index(user_id, data)
            user = data[user_id][0]
            del data[user_id]
        except Exception:
            log(message.from_user.id, '/delete', 'ERROR', 'The user is missing in the list')
            bot.send_message(message.from_user.id, words['delete'][1])
            return 1
        save(message, data)
        log(message.from_user.id, '/delete', f'User {user}(id: {user_id}) removed')
        bot.send_message(message.from_user.id, words['delete'][2].format(user, user_id))
        reboot(message, '/delete', f'User {user}(id: {user_id}) removed')

    @bot.message_handler(commands=['add_all'])
    def add_all(message):
        '''
        :param message:
        Function adds to the list of tracked users of all friends
        '''
        """
        :param message:
        :return:
        Функция добавляет в список отслеживаемых пользователей всех друзей
        """
        friends = vk.friends.get()['items']
        users = vk.users.get(user_ids=friends)
        data = open_users(message)
        if data != 1:
            for user in users:
                if user['id'] not in data:
                    data[str(user["id"])] = [user['first_name'] + ' ' + user['last_name'], len(data) + 1]
            save(message, data)
            log(message.from_user.id, '/add_all', 'add all friends')
            bot.send_message(message.from_user.id, words['add_all'][0])
            reboot(message, '/add_all')

    @bot.message_handler(commands=['delete_all'])
    def delete_all(message):  # модуль запуска трансляции
        '''
        Function Clears the list of tracked users
        '''
        """
        Функция очищает список отслеживаемых пользователей
        """
        global is_broadcast
        log(message.from_user.id, '/delete_all')
        check(message)
        data = {}
        save(message, data)
        log(message.from_user.id, '/delete_all', f'all users removed')
        bot.send_message(message.from_user.id, words['delete_all'][0])
        if is_broadcast:
            alt_exit(message)

    @bot.message_handler(commands=['check'])
    def check(message):
        '''
        The function sends the user list of monitored users to the user.
        '''
        """
        Функция отправляет пользователю список отслеживаемых пользователей
        """
        log(message.from_user.id, '/check')
        data = open_users(message)
        if data != 1:
            if len(data) == 0:
                bot.send_message(message.from_user.id, words['check'][0])
                log(message.from_user.id, '/check', 'the list of users is empty')
                return 0
            else:
                try:
                    buf = ['']
                    for item in data:
                        if len(buf[-1]) > 3000:
                            buf.append('')
                        buf[-1] += f'{data[item][1]}) {data[item][0]} (id: {item})\n'
                    bot.send_message(message.from_user.id, words['check'][1])
                    for item in buf:
                        bot.send_message(message.from_user.id, '\n' + item)
                except Exception:
                    log(message.from_user.id, '/check', 'Error reading a file')
                    bot.send_message(message.from_user.id,
                                     words['check'][2])

    bot.polling()


log('start', '')
while True:
    try:
        main()
    except Exception:
        log(user='--------', command='\nREBOOT\n')
        time.sleep(5)
        continue
