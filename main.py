# -*- coding: utf-8 -*-

import json
import logging
import sys
import datetime
from time import time, asctime, sleep
from os.path import exists
from copy import copy

from config import *
import pytz
import telebot
from telebot import types
from telebot.apihelper import ApiException

triggers = {}
admins = {}

tz = pytz.timezone(tz_name)


# Логгер
def get_logger(name=__file__, file='log.txt', encoding='utf-8'):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-8s %(message)s')

    fh = logging.FileHandler(file, encoding=encoding)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    return log


# Костыль для записи всех принтов
log = get_logger()
print = log.debug


# Проверка на давность
def is_recent(m):
    return (time() - m.date) < 60


# Инициализация json файлов
if exists('triggers.json'):
    with open('triggers.json') as f1:
        triggers = json.load(f1)
    print('Загружен файл с триггерами')
else:
    with open('triggers.json', 'w') as f1:
        json.dump({}, f1)

if exists('context.json'):
    with open('context.json') as fc:
        context = json.load(fc)
    print('Загружен файл с контекст-триггерами')
else:
    with open('context.json', 'w') as fc:
        json.dump({}, fc)

if exists('admins.json'):
    with open('admins.json') as f2:
        admins = json.load(f2)
    print('Загружен файл с админами')
else:
    with open('admins.json', 'w') as f2:
        json.dump({}, f2)


def save_triggers():
    with open('triggers.json', 'w') as f1:
        json.dump(triggers, f1, indent=2)
    print('Файл с триггерами сохранен')


def save_context():
    with open('context.json', 'w') as fc:
        json.dump(context, fc, indent=2)
    print('Файл с контекст-триггерами сохранен')


def save_admins():
    with open('admins.json', 'w') as f2:
        json.dump(admins, f2, indent=2)
    print('Файл с админами сохранен')


def get_triggers(group_id):
    if str(group_id) in triggers.keys():
        return triggers[str(group_id)]
    else:
        return False


def get_context(group_id):
    if str(group_id) in context.keys():
        return context[str(group_id)]
    else:
        return False


def get_admins(group_id):
    if str(group_id) in admins.keys():
        return admins[str(group_id)]
    else:
        return False


result = []
path = []


def get_keys(d, target):
    for k, v in d.iteritems():
        path.append(k)
        if isinstance(v, dict):
            get_keys(v, target)
        if v == target:
            result.append(copy(path))
        path.pop()


token = ''

# Подгрузка токена
if exists('token.txt'):
    with open('token.txt') as f:
        token = f.readline().strip()
    print('Токен загружен')
else:
    msg = 'Файла с токенами не обнаружено, введите токен:\n> '
    token = input(msg)
    with open('token.txt', 'w') as f:
        f.write(token)
    print('Файл с токенами сохранен')

bot = telebot.TeleBot(token)

bot_id = int(token.split(':')[0])
print('Bot ID [%s]' % bot_id)


def listener(messages):
    for m in messages:
        print('%s[%s]:%s' % (m.from_user.first_name, m.chat.id, m.text if m.text else m.content_type))


bot.set_update_listener(listener)


# Системные сообщения находятся в файле config.py
# Инфо команды


@bot.message_handler(commands=['help', 'start'])
def bot_help(m):
    bot.send_message(m.chat.id, help_message, True, parse_mode="Markdown")


@bot.message_handler(commands=['about'])
def about(m):
    keyboard = types.InlineKeyboardMarkup()
    changelog = types.InlineKeyboardButton(text="Changelog", callback_data="changelog_call")
    keyboard.add(changelog)
    bot.send_message(m.chat.id, about_message, reply_markup=keyboard)


# Хендлеры с инлайн-кнопками
@bot.message_handler(commands=["all"])
def all(m):
    if m.chat.type in ['group', 'supergroup']:
        keyboard = types.InlineKeyboardMarkup()
        button_triggers = types.InlineKeyboardButton(text="Триггеры", callback_data="all_triggers")
        button_context = types.InlineKeyboardButton(text="Контекст", callback_data="all_context")
        button_admins = types.InlineKeyboardButton(text="Админы", callback_data="all_admins")
        keyboard.add(button_triggers, button_context, button_admins)
        bot.send_message(m.chat.id, "Список чего ты хочешь посмотреть?", reply_markup=keyboard)


@bot.message_handler(commands=["size"])
def size(m):
    if m.chat.type in ['group', 'supergroup']:
        keyboard = types.InlineKeyboardMarkup()
        button_size = types.InlineKeyboardButton(text="Размер Т", callback_data="size_triggers")
        button_size_context = types.InlineKeyboardButton(text="Размер К", callback_data="size_context")
        keyboard.add(button_size, button_size_context)
        bot.send_message(m.chat.id, "Список чего ты хочешь посмотреть?", reply_markup=keyboard)


@bot.message_handler(commands=["admin"])
def all(m):
    if m.from_user.id == owner:
        keyboard = types.InlineKeyboardMarkup()
        admin_help = types.InlineKeyboardButton(text="Админ-команды", callback_data="admin_help")
        stats = types.InlineKeyboardButton(text="Статистика", callback_data="stats")
        check = types.InlineKeyboardButton(text="Проверить группы", callback_data="check")
        download = types.InlineKeyboardButton(text="Скачать файлы", callback_data="download")
        clear = types.InlineKeyboardButton(text="Отчистка файлов", callback_data="clear")
        keyboard.add(admin_help, stats, check, download, clear)
        bot.send_message(m.chat.id, "Админ-панель Короля-Бога", reply_markup=keyboard)


# Обработка инлайн кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "admin_help":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="admin")
                keyboard.add(rturn)
                bot.send_message(owner, admin_help_message)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Сообщение отправлено Королю-Богу. Что-то еще?', reply_markup=keyboard)
        if call.data == "admin":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                admin_help = types.InlineKeyboardButton(text="Админ-команды", callback_data="admin_help")
                download = types.InlineKeyboardButton(text="Скачать файлы", callback_data="download")
                stats = types.InlineKeyboardButton(text="Статистика", callback_data="stats")
                check = types.InlineKeyboardButton(text="Проверить группы", callback_data="check")
                clear = types.InlineKeyboardButton(text="Отчистка файлов", callback_data="clear")
                keyboard.add(admin_help, stats, check, download, clear)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Админ-панель Короля-Бога", reply_markup=keyboard)
        if call.data == "download":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                t_json = types.InlineKeyboardButton(text="triggers.json", callback_data="t_json")
                c_json = types.InlineKeyboardButton(text="context.json", callback_data="c_json")
                a_json = types.InlineKeyboardButton(text="admins.json", callback_data="a_json")
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="admin")
                keyboard.add(t_json, c_json, a_json, rturn)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Какой файл отправить?", reply_markup=keyboard)
        if call.data == "t_json":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="download")
                bot.send_document(owner, open('triggers.json'))
                keyboard.add(rturn)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Сообщение отправлено Королю-Богу. Что-то еще?', reply_markup=keyboard)
        if call.data == "c_json":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="download")
                bot.send_document(owner, open('context.json'))
                keyboard.add(rturn)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Сообщение отправлено Королю-Богу. Что-то еще?', reply_markup=keyboard)
        if call.data == "a_json":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="download")
                bot.send_document(owner, open('admins.json'))
                keyboard.add(rturn)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Сообщение отправлено Королю-Богу. Что-то еще?', reply_markup=keyboard)
        if call.data == "clear":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                clean_t_json = types.InlineKeyboardButton(text="triggers.json", callback_data="clean_t_json")
                clean_c_json = types.InlineKeyboardButton(text="context.json", callback_data="clean_c_json")
                clean_a_json = types.InlineKeyboardButton(text="admins.json", callback_data="clean_a_json")
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="admin")
                keyboard.add(clean_t_json, clean_c_json, clean_a_json, rturn)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Что будем удалять?', reply_markup=keyboard)
        if call.data == "clean_t_json":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="clear")
                keyboard.add(rturn)
                total_triggers = 0
                for x in triggers.keys():
                    total_triggers += len(triggers[x].keys())

                triggers_count = 0
                for g in triggers.copy().keys():
                    try:
                        bot.send_chat_action(call.message.chat.id, 'typing')
                        triggers.pop(g)
                    except():
                        triggers_count += len(triggers.pop(g))
                final_triggers = len(triggers)
                msg_text = '''
Original trigger count : {}
Final trigger count : {}

Что-то еще?        
                '''.format(
                    total_triggers,
                    final_triggers)
                save_triggers()
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg_text,
                                      reply_markup=keyboard)
        if call.data == "clean_a_json":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="clear")
                keyboard.add(rturn)
                total_admins = 0
                for x in admins.keys():
                    total_admins += len(admins[x].keys())

                admins_count = 0
                for g in admins.copy().keys():
                    try:
                        bot.send_chat_action(call.message.chat.id, 'typing')
                        admins.pop(g)
                    except():
                        admins_count += len(admins.pop(g))
                final_admins = len(admins)
                msg_text = '''
Original admin count : {}
Final admin count : {}

Что-то еще?
                '''.format(
                    total_admins,
                    final_admins)
                save_admins()
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg_text,
                                      reply_markup=keyboard)
        if call.data == "clean_c_json":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="clear")
                keyboard.add(rturn)
                total_context = 0
                for x in context.keys():
                    total_context += len(context[x].keys())

                context_count = 0
                for g in context.copy().keys():
                    try:
                        bot.send_chat_action(call.message.chat.id, 'typing')
                        context.pop(g)
                    except():
                        context_count += len(context.pop(g))
                final_context = len(context)
                msg_text = '''
Original context count : {}
Final context count : {}

Что-то еще?
                '''.format(
                    total_context,
                    final_context)
                save_context()
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg_text,
                                      reply_markup=keyboard)
        if call.data == "stats":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="admin")
                keyboard.add(rturn)
                total_triggers = 0
                for x in triggers.keys():
                    total_triggers += len(triggers[x].keys())
                stats_text = 'Чатов : {}\nТриггеров : {}'.format(len(triggers.keys()), total_triggers)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=stats_text,
                                      reply_markup=keyboard)
        if call.data == "check":
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="admin")
                keyboard.add(rturn)
                group_count = 0
                for g in triggers.keys():
                    try:
                        bot.send_chat_action(g, 'typing')
                        group_count += 1
                    except():
                        pass
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Работает %s из %s чатов' % (group_count, len(triggers)),
                                      reply_markup=keyboard)

        if call.data == "all":
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                button_triggers = types.InlineKeyboardButton(text="Триггеры", callback_data="all_triggers")
                button_context = types.InlineKeyboardButton(text="Контекст", callback_data="all_context")
                button_admins = types.InlineKeyboardButton(text="Админы", callback_data="all_admins")
                keyboard.add(button_triggers, button_context, button_admins)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Список чего ты хочешь посмотреть?', reply_markup=keyboard)
        if call.data == "all_triggers":
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="all")
                keyboard.add(rturn)
                trg = get_triggers(call.message.chat.id)
                if trg:
                    if len(trg.keys()) == 0:
                        msg = 'Тут нет триггеров, пока что'
                    else:
                        msg = 'Триггеры:\n' + '\n'.join(trg)
                else:
                    msg = 'Тут нет триггеров, пока что'
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg,
                                  reply_markup=keyboard)
        if call.data == "all_context":
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="all")
                keyboard.add(rturn)
                ctx = get_context(call.message.chat.id)
                if ctx:
                    if len(ctx.keys()) == 0:
                        msg = 'Тут нет конекст-триггеров, пока что',
                    else:
                        msg = 'Триггеры:\n' + '\n'.join(ctx)
                else:
                    msg = 'Тут нет конекст-триггеров, пока что'
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg,
                                  reply_markup=keyboard)
        if call.data == "all_admins":
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="all")
                keyboard.add(rturn)
                adm = get_admins(call.message.chat.id)
                if adm:
                    if len(adm.keys()) == 0:
                        msg = 'Тут нет админов, пока что'
                    else:
                        admin_list = ''
                        for a in adm.keys():
                            admin_list = admin_list + '\n' + str(adm[a]) + ' - ' + str(a)
                        msg = 'Админы:' + admin_list
                else:
                    msg = 'Тут нет админов, пока что'
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg,
                                  reply_markup=keyboard)
        if call.data == "size":
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                button_size = types.InlineKeyboardButton(text="Размер Т", callback_data="size_triggers")
                button_size_context = types.InlineKeyboardButton(text="Размер К", callback_data="size_context")
                keyboard.add(button_size, button_size_context)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Список чего ты хочешь посмотреть?', reply_markup=keyboard)
        if call.data == "size_triggers":
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="size")
                keyboard.add(rturn)
                trg = get_triggers(call.message.chat.id)
                if trg:
                    msg = 'Количество триггеров = {}'.format(len(trg))
                else:
                    msg = 'Количество триггеров = 0'
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg,
                                  reply_markup=keyboard)
        if call.data == "size_context":
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="size")
                keyboard.add(rturn)
                ctx = get_context(call.message.chat.id)
                if ctx:
                    msg = 'Количество контекст-триггеров = {}'.format(len(ctx))
                else:
                    msg = 'Количество конекст-триггеров = 0'
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg,
                                  reply_markup=keyboard)
        if call.data == "changelog_call":
            keyboard = types.InlineKeyboardMarkup()
            about_key = types.InlineKeyboardButton(text="About", callback_data="about_call")
            keyboard.add(about_key)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=changelog,
                                  reply_markup=keyboard)
        if call.data == "about_call":
            keyboard = types.InlineKeyboardMarkup()
            changelog_key = types.InlineKeyboardButton(text="Changelog", callback_data="changelog_call")
            keyboard.add(changelog_key)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=about_message,
                                  reply_markup=keyboard)


# Работа с триггерами
@bot.message_handler(commands=['add'])
def add(m):
    adm = get_admins(m.chat.id)
    if adm:
        for t in adm.keys():
            if str(t) == str(m.from_user.id):
                if m.reply_to_message:
                    if m.reply_to_message.text:
                        if len(m.reply_to_message.text) < 2:
                            bot.reply_to(m, 'Неправильный аргумент')
                            return
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.text.strip()
                    elif m.reply_to_message.sticker:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.sticker.file_id + ' sti'
                    elif m.reply_to_message.photo:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.photo[0].file_id + ' pho'
                    elif m.reply_to_message.video:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.video.file_id + ' vid'
                    elif m.reply_to_message.voice:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.voice.file_id + ' voi'
                    elif m.reply_to_message.audio:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.audio.file_id + ' aud'
                    elif m.reply_to_message.document:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.document.file_id + ' doc'
                    elif m.reply_to_message.video_note:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.video_note.file_id + ' vnt'
                    else:
                        bot.reply_to(m, 'ЧТО ТЫ ТАКОЕ?')
                        return
                else:
                    if m.text.find(separator, 1) == -1:
                        bot.reply_to(m, 'Нет разделителя/Неправильный разделитель, используй %')
                        return
                    rest_text = m.text.split(' ', 1)[1]
                    trigger_word = u'' + rest_text.split(separator)[0].strip().lower()
                    trigger_response = u'' + rest_text.split(separator, 1)[1].strip()
                if m.chat.type in ['group', 'supergroup']:
                    if get_triggers(m.chat.id):
                        get_triggers(m.chat.id)[trigger_word] = trigger_response
                    else:
                        triggers[str(m.chat.id)] = {trigger_word: trigger_response}
                    msg = u'' + trigger_created_message.format(trigger_word, trigger_response)
                    bot.reply_to(m, msg)
                    save_triggers()
                else:
                    return


@bot.message_handler(commands=['add_context'])
def add_context(m):
    adm = get_admins(m.chat.id)
    if adm:
        for t in adm.keys():
            if str(t) == str(m.from_user.id):
                if m.reply_to_message:
                    if m.reply_to_message.text:
                        if len(m.reply_to_message.text) < 2:
                            bot.reply_to(m, 'Неправильный аргумент')
                            return
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.text.strip()
                    elif m.reply_to_message.sticker:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.sticker.file_id + ' sti'
                    elif m.reply_to_message.photo:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.photo[0].file_id + ' pho'
                    elif m.reply_to_message.video:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.video.file_id + ' vid'
                    elif m.reply_to_message.voice:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.voice.file_id + ' voi'
                    elif m.reply_to_message.audio:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.audio.file_id + ' aud'
                    elif m.reply_to_message.document:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.document.file_id + ' doc'
                    elif m.reply_to_message.video_note:
                        trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                        trigger_response = u'' + m.reply_to_message.video_note.file_id + ' vnt'
                    else:
                        bot.reply_to(m, 'ЧТО ТЫ ТАКОЕ?')
                        return
                else:
                    if m.text.find(separator, 1) == -1:
                        bot.reply_to(m, 'Нет разделителя/Неправильный разделитель, используй %')
                        return
                    rest_text = m.text.split(' ', 1)[1]
                    trigger_word = u'' + rest_text.split(separator)[0].strip().lower()
                    trigger_response = u'' + rest_text.split(separator, 1)[1].strip()
                if m.chat.type in ['group', 'supergroup']:
                    if get_context(m.chat.id):
                        get_context(m.chat.id)[trigger_word] = trigger_response
                    else:
                        context[str(m.chat.id)] = {trigger_word: trigger_response}
                    msg = u'' + context_trigger_created_message.format(trigger_word, trigger_response)
                    bot.reply_to(m, msg)
                    save_context()
                else:
                    return


@bot.message_handler(commands=['del'])
def delete(m):
    adm = get_admins(m.chat.id)
    if adm:
        for t in adm.keys():
            if str(t) == str(m.from_user.id):
                if len(m.text.split()) == 1 and m.reply_to_message and m.reply_to_message.text:
                    trg = get_triggers(m.chat.id)
                    if trg:
                        for x in trg.keys():
                            if trg[x].lower() == m.reply_to_message.text.lower():
                                trg.pop(x)
                                bot.reply_to(m, 'Триггер [%s] удален' % x)
                                return
                if len(m.text.split()) < 2:
                    bot.reply_to(m, 'Неправильный аргумент')
                    return
                del_text = m.text.split(' ', 1)[1].strip()
                if m.chat.type in ['group', 'supergroup']:
                    trg = get_triggers(m.chat.id)
                    if trg and del_text in trg.keys():
                        trg.pop(del_text)
                        bot.reply_to(m, 'Триггер [{}] удален'.format(del_text))
                        save_triggers()
                    else:
                        bot.reply_to(m, 'Триггер [{}] не найден'.format(del_text))


@bot.message_handler(commands=['del_context'])
def delete_context(m):
    adm = get_admins(m.chat.id)
    if adm:
        for t in adm.keys():
            if str(t) == str(m.from_user.id):
                if len(m.text.split()) == 1 and m.reply_to_message and m.reply_to_message.text:
                    ctx = get_context(m.chat.id)
                    if ctx:
                        for x in ctx.keys():
                            if ctx[x].lower() == m.reply_to_message.text.lower():
                                ctx.pop(x)
                                bot.reply_to(m, 'Контекст-триггер [%s] удален' % x)
                                return
                if len(m.text.split()) < 2:
                    bot.reply_to(m, 'Неправильный аргумент')
                    return
                del_text = m.text.split(' ', 1)[1].strip()
                if m.chat.type in ['group', 'supergroup']:
                    ctx = get_context(m.chat.id)
                    if ctx and del_text in ctx.keys():
                        ctx.pop(del_text)
                        bot.reply_to(m, 'Контекст-триггер [{}] удален'.format(del_text))
                        save_context()
                    else:
                        bot.reply_to(m, 'Контекст-триггер [{}] не найден'.format(del_text))


# Админ-панель
@bot.message_handler(commands=['solve'])
def solve(m):
    rp = m.reply_to_message
    rw = ''
    ts = 'Триггер не найден'
    if len(m.text.split()) >= 2:
        rw = m.text.split(' ', 1)[1]
    if rp and rp.from_user.id == bot_id and rp.text:
        rw = rp.text
    if m.chat.type in ['group', 'supergroup']:
        trg = get_triggers(m.chat.id)
        if trg:
            for x in trg.keys():
                if trg[x].lower() == rw.lower():
                    ts = 'Триггер = ' + x
        bot.reply_to(m, ts)


@bot.message_handler(commands=['b'])
def broadcast(m):
    if m.from_user.id != owner:
        return
    if len(m.text.split()) == 1:
        bot.send_message(m.chat.id, 'Нет текста')
        return
    count = 0
    for g in triggers.keys():
        try:
            bot.send_message(int(g), m.text.split(' ', 1)[1])
            count += 1
        except ApiException:
            continue
    bot.send_message(m.chat.id, 'Broadcast sent to {} groups of {}'.format(count, len(triggers.keys())))


@bot.message_handler(commands=['gadd'])
def add_global_trigger(m):
    if m.from_user.id == owner:
        if len(m.text.split()) == 1:
            bot.reply_to(m, 'Использоване:\n/gadd <триггер> % <ответ>\n[Ответ на сообщение]:\n/gadd <триггер>')
            return
        if m.reply_to_message:
            if m.reply_to_message.text:
                trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                trigger_response = u'' + m.reply_to_message.text.strip()
            elif m.reply_to_message.sticker:
                trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                trigger_response = u'' + m.reply_to_message.sticker.file_id + ' sti'
            elif m.reply_to_message.photo:
                trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                trigger_response = u'' + m.reply_to_message.photo.file_id + ' pho'
            elif m.reply_to_message.video:
                trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                trigger_response = u'' + m.reply_to_message.video.file_id + ' vid'
            elif m.reply_to_message.voice:
                trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                trigger_response = u'' + m.reply_to_message.voice.file_id + ' voi'
            elif m.reply_to_message.audio:
                trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                trigger_response = u'' + m.reply_to_message.audio.file_id + ' aud'
            elif m.reply_to_message.document:
                trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                trigger_response = u'' + m.reply_to_message.document.file_id + ' doc'
            elif m.reply_to_message.video_note:
                trigger_word = u'' + m.text.split(' ', 1)[1].strip().lower()
                trigger_response = u'' + m.reply_to_message.video_note.file_id + ' vnt'
            else:
                bot.reply_to(m, 'ЧТО ТЫ ТАКОЕ?')
                return
        else:
            if m.text.find(separator, 1) == -1:
                bot.reply_to(m, 'Нет разделителя/Неправильный разделитель, используй %')
                return
            rest_text = m.text.split(' ', 1)[1]
            trigger_word = u'' + rest_text.split(separator)[0].strip().lower()
            trigger_response = u'' + rest_text.split(separator, 1)[1].strip()
            if len(trigger_word) < 4:
                bot.reply_to(m, 'Слишком короткий [chars < 4]')
                return
            if len(trigger_response) < 1:
                bot.reply_to(m, 'Неправильный ответ')
                return
        for g in triggers.keys():
            triggers[g][trigger_word] = trigger_response
        bot.reply_to(m, global_trigger_created_message.format(trigger_word, trigger_response))
        save_triggers()


@bot.message_handler(commands=['gdel'])
def global_delete(m):
    if m.from_user.id == owner:
        if len(m.text.split()) == 1:
            bot.reply_to(m, 'Использование: /gdel <триггер>')
        else:
            trigger_word = m.text.split(' ', 1)[1]
            count = 0
            for g in triggers.keys():
                if trigger_word in triggers[g]:
                    triggers[g].pop(trigger_word)
                    count += 1
            bot.reply_to(m, global_trigger_deleted_message.format(trigger_word, count))
            save_triggers()


@bot.message_handler(commands=['gsearch'])
def global_search(m):
    if m.from_user.id == owner:
        if len(m.text.split()) == 1:
            bot.reply_to(m, 'Использование: /gsearch <триггер>')
        else:
            trigger_word = m.text.split(' ', 1)[1]
            results = []
            for g in triggers.keys():
                if trigger_word in triggers[g].keys():
                    txt = triggers[g][trigger_word]
                    results.append('[%s]:\n%s' % (g, txt if len(txt) < 30 else txt[:27] + '...'))
            if len(results) == 0:
                result_text = 'Триггер не найден'
            else:
                result_text = 'Триггер найден в таких группах как:\n%s' % '\n-----\n'.join(results)
            bot.reply_to(m, result_text)


@bot.message_handler(commands=['merge'])
def merge_triggers(m):
    if m.from_user.id == owner:
        success_text = 'Триггеры слиты с [%s], всего триггеров: [%s]'
        no_exists = 'Группы %s не существует. Как минимум в базе данных'
        if len(m.text.split()) == 2:
            merge_from = int(m.text.split()[1])
            if get_triggers(merge_from):
                get_triggers(m.chat.id).update(get_triggers(merge_from))
                save_triggers()
                bot.reply_to(m, success_text % (merge_from, len(get_triggers(m.chat.id))))
            else:
                bot.reply_to(m, no_exists % merge_from)
        else:
            bot.reply_to(m, 'Нет ID группы')


@bot.message_handler(commands=['add_admin'])
def add_admin(m):
    if m.from_user.id == owner:
        if m.reply_to_message:
            if m.reply_to_message.text:
                admin_id = m.reply_to_message.from_user.id
                admin_name = m.reply_to_message.from_user.username
            else:
                bot.reply_to(m, 'ЧТО ТЫ ТАКОЕ?')
                return
        else:
            if len(m.text.split()) == 1:
                bot.reply_to(m, 'Использование: /add_admin <userid> % <username>')
            else:
                rest_text = m.text.split(' ', 1)[1]
                admin_id = rest_text.split(separator)[0].strip().lower()
                admin_name = rest_text.split(separator, 1)[1].strip()
        if get_admins(m.chat.id):
            get_admins(m.chat.id)[admin_id] = str(admin_name)
        else:
            admins[str(m.chat.id)] = {admin_id: str(admin_name)}
        bot.reply_to(m, 'Админ добавлен')
        save_admins()


@bot.message_handler(commands=['del_admin'])
def delete_admin(m):
    if m.from_user.id == owner:
        adm = get_admins(m.chat.id)
        if len(m.text.split()) == 1:
            bot.reply_to(m, 'Использование: /del_admin <id / username> % <~>')
            return
        else:
            if m.reply_to_message:
                if m.reply_to_message.text:
                    del_admin = m.reply_to_message.from_user.id
                else:
                    bot.reply_to(m, 'ЧТО ТЫ ТАКОЕ?')
                    return
            else:
                rest_text = m.text.split(' ', 1)[1]
                deltype = rest_text.split(separator)[0].strip().lower()
                if deltype == 'id':
                    del_admin = rest_text.split(separator, 1)[1].strip()
                elif deltype == 'username':
                    del_admin_username = rest_text.split(separator, 1)[1].strip()
                    del_admin_all = (adm, del_admin_username)
                    del_admin_list = del_admin_all[0]
                    del_admin = list(del_admin_list.keys())[0]
                else:
                    bot.reply_to(m, 'Использование: /del_admin <id / username> % <~>')
                    return
            if adm and del_admin in adm.keys():
                adm.pop(del_admin)
                bot.reply_to(m, 'Админ [{}] удален'.format(del_admin))
                save_admins()
            else:
                bot.reply_to(m, 'Админ [{}] не найден'.format(del_admin))


@bot.message_handler(commands=['status'])
def check_message(m):
    try:
        if m.reply_to_message.forward_from is not None:
            from_user = m.reply_to_message.forward_from.id
            username = m.reply_to_message.forward_from.username
            is_bot = m.reply_to_message.forward_from.is_bot
            date = datetime.datetime.fromtimestamp(m.reply_to_message.forward_date, tz).strftime("%A, %B %d, "
                                                                                                 "%Y %H:%M:%S")

            msg_text = '''
От пользователя : {}
ID пользователя : {}
Бот: {}

Дата : {}
                    '''.format(
                from_user,
                username,
                is_bot,
                date)
            bot.reply_to(m, msg_text)
        else:
            message_id = m.reply_to_message.message_id
            from_user = m.reply_to_message.from_user.id
            username = m.reply_to_message.from_user.username
            date = datetime.datetime.fromtimestamp(m.reply_to_message.date, tz).strftime("%A, %B %d, %Y %H:%M:%S")

            msg_text = '''
ID сообщения : {}
ID пользователя : {}
Юзернейм : {}

Дата : {}    
                            '''.format(
                message_id,
                from_user,
                username,
                date)
            bot.reply_to(m, msg_text)
    except Exception as e:
        message_id = m.message_id
        from_user = m.from_user.id
        username = m.from_user.username
        date = datetime.datetime.fromtimestamp(m.date, tz).strftime("%A, %B %d, %Y %H:%M:%S")

        msg_text = '''
ID сообщения : {}
ID пользователя : {}
Юзернейм : {}

Дата : {}
                                '''.format(
            message_id,
            from_user,
            username,
            date)
        bot.reply_to(m, msg_text)


@bot.message_handler(content_types=['new_chat_member'])
def invited(m):
    if m.new_chat_member.id == bot_id:
        bot.send_message(m.chat.id, invited_message, parse_mode="Markdown")
        if not get_triggers(m.chat.id):
            save_triggers()
        bot.send_message(owner, 'Бот добавлен в %s[%s]' % (m.chat.title, m.chat.id))


@bot.message_handler(content_types=['left_chat_member'])
def expulsed(m):
    if m.left_chat_member.id == bot_id:
        bot.send_message(owner, 'Бот удален из %s[%s]' % (m.chat.title, m.chat.id))


# Проверка каждого сообщения
@bot.message_handler(func=lambda m: True)
def response(m):
    if not is_recent(m):
        return
    if m.chat.type in ['group', 'supergroup']:
        trg = get_triggers(m.chat.id)
        ctx = get_context(m.chat.id)
        if trg:
            for t in trg.keys():
                if t == m.text.lower():
                    if ' sti' in trg[t]:
                        bot.send_sticker(m.chat.id, (trg[t])[:-4])
                    elif ' pho' in trg[t]:
                        bot.send_photo(m.chat.id, (trg[t])[:-4])
                    elif ' vid' in trg[t]:
                        bot.send_video(m.chat.id, (trg[t])[:-4])
                    elif ' voi' in trg[t]:
                        bot.send_voice(m.chat.id, (trg[t])[:-4])
                    elif ' aud' in trg[t]:
                        bot.send_audio(m.chat.id, (trg[t])[:-4])
                    elif ' doc' in trg[t]:
                        bot.send_document(m.chat.id, (trg[t])[:-4])
                    elif ' vnt' in trg[t]:
                        bot.send_video_note(m.chat.id, (trg[t])[:-4])
                    else:
                        bot.send_message(m.chat.id, trg[t])
        if ctx:
            for t in ctx.keys():
                if t in m.text.lower():
                    if ' sti' in ctx[t]:
                        bot.send_sticker(m.chat.id, (ctx[t])[:-4])
                    elif ' pho' in ctx[t]:
                        bot.send_photo(m.chat.id, (ctx[t])[:-4])
                    elif ' vid' in ctx[t]:
                        bot.send_video(m.chat.id, (ctx[t])[:-4])
                    elif ' voi' in ctx[t]:
                        bot.send_voice(m.chat.id, (ctx[t])[:-4])
                    elif ' aud' in ctx[t]:
                        bot.send_audio(m.chat.id, (ctx[t])[:-4])
                    elif ' doc' in ctx[t]:
                        bot.send_document(m.chat.id, (ctx[t])[:-4])
                    elif ' vnt' in ctx[t]:
                        bot.send_video_note(m.chat.id, (ctx[t])[:-4])
                    else:
                        bot.send_message(m.chat.id, ctx[t])


def safepolling(bot):
    if bot.skip_pending:
        lid = bot.get_updates()[-1].update_id
    else:
        lid = 0
    while 1:
        try:
            updates = bot.get_updates(lid + 1, 50)
            if len(updates) > 0:
                lid = updates[-1].update_id
                bot.process_new_updates(updates)
        except ApiException as a:
            print(a)
        except Exception as e:
            print('Exception at %s \n%s' % (asctime(), e))
            now = int(time())
            while 1:
                error_text = 'Exception at %s:\n%s' % (asctime(), str(e) if len(str(e)) < 3600 else str(e)[:3600])
                try:
                    offline = int(time()) - now
                    bot.send_message(owner, error_text + '\nБот упал на %s секунд(у)' % offline)
                    break
                except():
                    sleep(0.25)


if __name__ == '__main__':
    print('Бот начал свою работу')
    try:
        print('Ник бота:[%s]' % bot.get_me().username)
    except ApiException:
        print('Токен [%s] неправильный')
        exit(1)
    try:
        bot.send_message(owner, 'Бот начал свою работу')
    except ApiException:
        print('''Бот https://telegram.me/%s нуждается в настройке''' % bot.get_me().username)
        exit(1)
    print('Safepolling начат')
    safepolling(bot)
