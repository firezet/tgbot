# -*- coding: utf-8 -*-

import logging
import datetime
from os.path import exists
from time import *
import shutil

import pytz
from config_sql import *
from peewee import *
import telebot
from telebot import types
from telebot.apihelper import ApiException


db = SqliteDatabase('bot.db')
tz = pytz.timezone(tz_name)


# Peewee database instance
class BaseModel(Model):
    class Meta:
        database = db


class Trigger(BaseModel):
    trigger_text = CharField()
    trigger_response = CharField()
    chat_id = DateField()
    trigger_type = CharField()
    added_by = DateField()
    is_locked = CharField()
    is_media = CharField()
    media_type = CharField()


class Admin(BaseModel):
    chat_id = DateField()
    username = CharField()
    user_id = DateField()
    time_of_addition = CharField()
    global_admin = CharField()
    added_by = DateField()
    added_by_username = CharField()


class Backup(BaseModel):
    backup_time = CharField()


def create_tables():
    with db:
        db.create_tables([Trigger, Admin, Backup])


# Create a database if none exists
if exists('bot.db'):
    pass
else:
    create_tables()


# Message time check
def is_recent(m):
    return (time() - m.date) < 60


def get_time():
    return datetime.datetime.now().strftime("%A, %B %d, %Y %H:%M:%S")


bot = telebot.TeleBot(token)
bot_id = int(token.split(':')[0])


def listener(messages):
    for m in messages:
        print('%s[%s]:%s' % (m.from_user.first_name, m.chat.id, m.text if m.text else m.content_type))
        with open('{}.txt'.format(m.chat.id), 'a', encoding='utf-8') as file:
            file.write('{}[{}] : {}'.format(m.from_user.first_name, m.from_user.id, m.text if m.text else m.content_type) + '\n')


bot.set_update_listener(listener)


@bot.message_handler(commands=['help', 'start'])
def bot_help(m):
    bot.send_message(m.chat.id, help_message)


@bot.message_handler(commands=['about'])
def about(m):
    keyboard = types.InlineKeyboardMarkup()
    changelog_key = types.InlineKeyboardButton(text='Changelog', callback_data='changelog_call')
    keyboard.add(changelog_key)
    bot.send_message(m.chat.id, about_message, reply_markup=keyboard)


@bot.message_handler(commands=['a_add'])
def add_admin(m):
    if m.from_user.id == owner:
        if m.reply_to_message:
            admin_id = m.reply_to_message.from_user.id
            admin_name = m.reply_to_message.from_user.username
        else:
            if m.text.find(separator, 1) == -1:
                bot.reply_to(m, add_admin_error_message)
                return
            rest_text = m.text.split(' ', 1)[1]

            admin_id = u'' + rest_text.split(separator)[0].strip()
            admin_name = u'' + rest_text.split(separator, 1)[1].strip()

        a_del = Admin.delete().where((Admin.chat_id == m.chat.id) & (Admin.username == admin_name) &
                                     (Admin.user_id == admin_id))
        a_del.execute()

        Admin.create(chat_id=m.chat.id, username=admin_name, user_id=admin_id, time_of_addition=get_time(),
                     global_admin='False', added_by=m.from_user.id, added_by_username=m.from_user.username)


@bot.message_handler(commands=['a_del'])
def del_admin(m):
    if m.from_user.id == owner:
        if m.reply_to_message:
            admin_id = m.reply_to_message.from_user.id
            admin_name = m.reply_to_message.from_user.username
        else:
            if m.text.find(separator, 1) == -1:
                bot.reply_to(m, del_admin_error_message)
                return
            rest_text = m.text.split(' ', 1)[1]

            admin_id = u'' + rest_text.split(separator)[0].strip()
            admin_name = u'' + rest_text.split(separator, 1)[1].strip()

        a_del = Admin.delete().where((Admin.chat_id == m.chat.id) & (Admin.username == admin_name) &
                                     (Admin.user_id == admin_id))
        a_del.execute()


@bot.message_handler(commands=['add'])
def add_trigger(m):
    admin_list = []
    for adm in Admin.select().where(Admin.chat_id == m.chat.id):
        admin_list.append(adm.user_id)
    if m.from_user.id in admin_list:
        if m.reply_to_message:
            trigger_word = m.text.split(' ', 1)[1].strip().lower()
            if m.reply_to_message.text:
                if len(m.reply_to_message.text) < 2:
                    bot.reply_to(m, error_len)
                    return
                trigger_response = m.reply_to_message.text.strip()
                is_media = 'False'
                media = 'text'
            elif m.reply_to_message.sticker:
                trigger_response = m.reply_to_message.sticker.file_id
                is_media = 'True'
                media = 'sticker'
            elif m.reply_to_message.photo:
                trigger_response = m.reply_to_message.photo[0].file_id
                is_media = 'True'
                media = 'photo'
            elif m.reply_to_message.video:
                trigger_response = m.reply_to_message.video.file_id
                is_media = 'True'
                media = 'video'
            elif m.reply_to_message.voice:
                trigger_response = m.reply_to_message.voice.file_id
                is_media = 'True'
                media = 'voice'
            elif m.reply_to_message.audio:
                trigger_response = m.reply_to_message.audio.file_id
                is_media = 'True'
                media = 'audio'
            elif m.reply_to_message.document:
                trigger_response = m.reply_to_message.document.file_id
                is_media = 'True'
                media = 'document'
            elif m.reply_to_message.video_note:
                trigger_response = m.reply_to_message.video_note.file_id
                is_media = 'True'
                media = 'video_note'
            else:
                bot.reply_to(m, error_message)
                return
        else:
            if m.text.find(separator, 1) == -1:
                bot.reply_to(m, error_message_separator)
                return
            rest_text = m.text.split(' ', 1)[1]
            trigger_word = rest_text.split(separator)[0].strip().lower()
            trigger_response = rest_text.split(separator, 1)[1].strip()
            is_media = 'False'
            media = 'text'
        if m.chat.type == 'group' or m.chat.type == 'supergroup':
            for trg in Trigger.select().where((Trigger.chat_id == m.chat.id) & (Trigger.trigger_text == trigger_word)
                                              & (Trigger.media_type == media) & (Trigger.trigger_type == 'local')):
                if trg.trigger_text == trigger_word and trg.is_locked == 'True':
                    bot.reply_to(m, locked_error.format(trg.added_by))
                    return
                elif trg.trigger_text == trigger_word and trg.is_locked == 'False':
                    t_del = Trigger.delete().where((Trigger.chat_id == m.chat.id)
                                                   & (Trigger.trigger_text == trigger_word)
                                                   & (Trigger.is_locked == 'False'))
                    t_del.execute()
            Trigger.create(trigger_text=trigger_word, trigger_response=trigger_response, chat_id=m.chat.id,
                           trigger_type='local', added_by=m.from_user.id, is_locked='False', is_media=is_media,
                           media_type=media)
            bot.reply_to(m, trigger_created_message.format(trigger_word, trigger_response))
        else:
            return


@bot.message_handler(commands=['del'])
def del_trigger(m):
    admin_list = []
    for adm in Admin.select().where(Admin.chat_id == m.chat.id):
        admin_list.append(adm.user_id)
    if m.from_user.id in admin_list:
        if m.reply_to_message:
            trigger_response = m.reply_to_message.text
            p = 0
        else:
            trigger_word = m.text.split(' ', 1)[1]
            p = 1
        if (m.chat.type == 'group' or m.chat.type == 'supergroup') and p == 1:
            for trg in Trigger.select().where((Trigger.chat_id == m.chat.id) & (Trigger.trigger_text == trigger_word)
                                              & (Trigger.trigger_type == 'local')):
                if trg.is_locked == 'True':
                    bot.reply_to(m, locked_error.format(trg.added_by))
                    return
                elif trg.is_locked == 'False':
                    bot.reply_to(m, trigger_del_message.format(trigger_word))
                    t_del = Trigger.delete().where((Trigger.chat_id == m.chat.id)
                                                   & (Trigger.trigger_text == trigger_word)
                                                   & (Trigger.is_locked == 'False'))
                    t_del.execute()
        elif (m.chat.type == 'group' or m.chat.type == 'supergroup') and p == 0:
            for trg in Trigger.select().where((Trigger.chat_id == m.chat.id)
                                              & (Trigger.trigger_response == trigger_response)
                                              & (Trigger.trigger_type == 'local')):
                if trg.is_locked == 'True':
                    bot.reply_to(m, locked_error.format(trg.added_by))
                    return
                elif trg.is_locked == 'False':
                    bot.reply_to(m, trigger_del_message.format(trigger_response))
                    t_del = Trigger.delete().where((Trigger.chat_id == m.chat.id)
                                                   & (Trigger.trigger_response == trigger_response)
                                                   & (Trigger.is_locked == 'False'))
                    t_del.execute()


@bot.message_handler(commands=['g_add'])
def add_global_trigger(m):
    admin_list = []
    for adm in Admin.select().where(Admin.chat_id == m.chat.id):
        admin_list.append(adm.user_id)
    if m.from_user.id in admin_list:
        if m.reply_to_message:
            trigger_word = m.text.split(' ', 1)[1].strip().lower()
            if m.reply_to_message.text:
                if len(m.reply_to_message.text) < 2:
                    bot.reply_to(m, error_len)
                    return
                trigger_response = m.reply_to_message.text.strip()
                is_media = 'False'
                media = 'text'
            elif m.reply_to_message.sticker:
                trigger_response = m.reply_to_message.sticker.file_id
                is_media = 'True'
                media = 'sticker'
            elif m.reply_to_message.photo:
                trigger_response = m.reply_to_message.photo[0].file_id
                is_media = 'True'
                media = 'photo'
            elif m.reply_to_message.video:
                trigger_response = m.reply_to_message.video.file_id
                is_media = 'True'
                media = 'video'
            elif m.reply_to_message.voice:
                trigger_response = m.reply_to_message.voice.file_id
                is_media = 'True'
                media = 'voice'
            elif m.reply_to_message.audio:
                trigger_response = m.reply_to_message.audio.file_id
                is_media = 'True'
                media = 'audio'
            elif m.reply_to_message.document:
                trigger_response = m.reply_to_message.document.file_id
                is_media = 'True'
                media = 'document'
            elif m.reply_to_message.video_note:
                trigger_response = m.reply_to_message.video_note.file_id
                is_media = 'True'
                media = 'video_note'
            else:
                bot.reply_to(m, error_message)
                return
        else:
            if m.text.find(separator, 1) == -1:
                bot.reply_to(m, error_message_separator)
                return
            rest_text = m.text.split(' ', 1)[1]
            trigger_word = rest_text.split(separator)[0].strip().lower()
            trigger_response = rest_text.split(separator, 1)[1].strip()
            is_media = 'False'
            media = 'text'
        if m.chat.type == 'group' or m.chat.type == 'supergroup':
            for trg in Trigger.select().where((Trigger.chat_id == m.chat.id) & (Trigger.trigger_text == trigger_word)
                                              & (Trigger.media_type == media) & (Trigger.trigger_type == 'global')):
                if trg.trigger_text == trigger_word and trg.is_locked == 'True':
                    bot.reply_to(m, locked_error.format(trg.added_by))
                    return
                elif trg.trigger_text == trigger_word and trg.is_locked == 'False':
                    t_del = Trigger.delete().where((Trigger.chat_id == m.chat.id)
                                                   & (Trigger.trigger_text == trigger_word)
                                                   & (Trigger.is_locked == 'False'))
                    t_del.execute()
            Trigger.create(trigger_text=trigger_word, trigger_response=trigger_response, chat_id=m.chat.id,
                           trigger_type='global', added_by=m.from_user.id, is_locked='True', is_media=is_media,
                           media_type=media)
            bot.reply_to(m, trigger_created_message.format(trigger_word, trigger_response))
        else:
            return


@bot.message_handler(commands=['g_del'])
def del_global_trigger(m):
    admin_list = []
    for adm in Admin.select().where(Admin.chat_id == m.chat.id):
        admin_list.append(adm.user_id)
    if m.from_user.id in admin_list:
        if m.reply_to_message:
            trigger_response = m.reply_to_message.text
            p = 0
        else:
            trigger_word = m.text.split(' ', 1)[1]
            p = 1
        if (m.chat.type == 'group' or m.chat.type == 'supergroup') and p == 1:
            for trg in Trigger.select().where((Trigger.chat_id == m.chat.id) & (Trigger.trigger_text == trigger_word)
                                              & (Trigger.trigger_type == 'global')):
                if trg.is_locked == 'True':
                    bot.reply_to(m, locked_error.format(trg.added_by))
                    return
                elif trg.is_locked == 'False':
                    bot.reply_to(m, trigger_del_message.format(trigger_word))
                    t_del = Trigger.delete().where((Trigger.chat_id == m.chat.id)
                                                   & (Trigger.trigger_text == trigger_word)
                                                   & (Trigger.is_locked == 'False'))
                    t_del.execute()
        elif (m.chat.type == 'group' or m.chat.type == 'supergroup') and p == 0:
            for trg in Trigger.select().where((Trigger.chat_id == m.chat.id)
                                              & (Trigger.trigger_response == trigger_response)
                                              & (Trigger.trigger_type == 'local')):
                if trg.is_locked == 'True':
                    bot.reply_to(m, locked_error.format(trg.added_by))
                    return
                elif trg.is_locked == 'False':
                    bot.reply_to(m, trigger_del_message.format(trigger_response))
                    t_del = Trigger.delete().where((Trigger.chat_id == m.chat.id)
                                                   & (Trigger.trigger_response == trigger_response)
                                                   & (Trigger.is_locked == 'False'))
                    t_del.execute()


@bot.message_handler(commands=['l'])
def lock(m):
    if m.reply_to_message:
        trigger_response = m.reply_to_message.text
        p = 0
    else:
        try:
            trigger_word = m.text.split(' ', 1)[1]
            p = 1
        except IndexError:
            bot.reply_to(m, error_message)
            return
    if (m.chat.type == 'group' or m.chat.type == 'supergroup') and p == 1:
        for trg in Trigger.select().where((Trigger.chat_id == m.chat.id) & (Trigger.trigger_text == trigger_word)):
            if trg.is_locked == 'True' and m.from_user.id == (trg.added_by or owner):
                update = Trigger.update(is_locked='False').where((Trigger.chat_id == m.chat.id)
                                                                            & (Trigger.trigger_text == trigger_word)
                                                                            & (Trigger.is_locked == 'True'))
                update.execute()
                bot.reply_to(m, trigger_unlocked.format(trg.trigger_text))
            elif trg.is_locked == 'False' and m.from_user.id == (trg.added_by or owner):
                update = Trigger.update(is_locked='True').where((Trigger.chat_id == m.chat.id)
                                                                           & (Trigger.trigger_text == trigger_word)
                                                                           & (Trigger.is_locked == 'False'))
                update.execute()
                bot.reply_to(m, trigger_locked.format(trigger_word))
    elif (m.chat.type == 'group' or m.chat.type == 'supergroup') and p == 0:
        for trg in Trigger.select().where((Trigger.chat_id == m.chat.id)
                                          & (Trigger.trigger_response == trigger_response)
                                          & (Trigger.trigger_type == 'local')):
            if trg.is_locked == 'True' and m.from_user.id == (trg.added_by or owner):
                update = Trigger.update(is_locked='False').where((Trigger.chat_id == m.chat.id)
                                                                        & (Trigger.trigger_response == trigger_response)
                                                                            & (Trigger.is_locked == 'True'))
                update.execute()
                bot.reply_to(m, trigger_unlocked.format(trg.trigger_response))
            elif trg.is_locked == 'False' and m.from_user.id == (trg.added_by or owner):
                update = Trigger.update(is_locked='True').where((Trigger.chat_id == m.chat.id)
                                                                        & (Trigger.trigger_response == trigger_response)
                                                                           & (Trigger.is_locked == 'False'))
                update.execute()
                bot.reply_to(m, trigger_unlocked.format(trg.trigger_response))


@bot.message_handler(commands=['s'])
def trigger_status(m):
    if m.reply_to_message:
        trigger_response = m.reply_to_message.text
        p = 0
    else:
        try:
            trigger_word = m.text.split(' ', 1)[1]
            p = 1
        except IndexError:
            bot.reply_to(m, error_message)
    if (m.chat.type == 'group' or m.chat.type == 'supergroup') and p == 1:
        for trg in Trigger.select().where((Trigger.chat_id == m.chat.id) & (Trigger.trigger_text == trigger_word)):
            bot.reply_to(m, trigger_status_message.format(trg.trigger_text, trg.trigger_response, trg.trigger_type,
                                                    trg.added_by, trg.is_locked, trg.media_type))
    elif (m.chat.type == 'group' or m.chat.type == 'supergroup') and p == 0:
        for trg in Trigger.select().where((Trigger.chat_id == m.chat.id)
                                          & (Trigger.trigger_response == trigger_response)):
            bot.reply_to(m, trigger_status_message.format(trg.trigger_text, trg.trigger_response, trg.trigger_type,
                                                          trg.added_by, trg.is_locked, trg.media_type))


@bot.message_handler(commands=['status'])
def check_message(m):
    try:
        if m.reply_to_message.forward_from is not None:
            from_user = m.reply_to_message.forward_from.id
            username = m.reply_to_message.forward_from.username
            is_bot = m.reply_to_message.forward_from.is_bot
            date = datetime.datetime.fromtimestamp(m.reply_to_message.forward_date, tz).strftime("%A, %B %d, "
                                                                                                 "%Y %H:%M:%S")
            bot.reply_to(m, status_text1.format(from_user, username, is_bot, date))
        else:
            message_id = m.reply_to_message.message_id
            from_user = m.reply_to_message.from_user.id
            username = m.reply_to_message.from_user.username
            date = datetime.datetime.fromtimestamp(m.reply_to_message.date, tz).strftime("%A, %B %d, %Y %H:%M:%S")
            bot.reply_to(m, status_text2.format(message_id, from_user, username, date))
    except Exception as e:
        logging.exception(e)
        message_id = m.message_id
        from_user = m.from_user.id
        username = m.from_user.username
        date = datetime.datetime.fromtimestamp(m.date, tz).strftime('%A, %B %d, %Y %H:%M:%S')
        bot.reply_to(m, status_text2.format(message_id, from_user, username, date))


@bot.message_handler(commands=['all'])
def all_list(m):
    if m.chat.type in ['group', 'supergroup']:
        keyboard = types.InlineKeyboardMarkup()
        button_triggers = types.InlineKeyboardButton(text=name_triggers, callback_data='all_triggers')
        button_admins = types.InlineKeyboardButton(text=name_admins, callback_data='all_admins')
        keyboard.add(button_triggers, button_admins)
        bot.send_message(m.chat.id, view_list, reply_markup=keyboard)
        
        
@bot.message_handler(commands=['admin'])
def admin(m):
    if m.from_user.id == owner:
        keyboard = types.InlineKeyboardMarkup()
        admin_help = types.InlineKeyboardButton(text=adm_commands, callback_data='admin_help')
        stats = types.InlineKeyboardButton(text=adm_stats, callback_data='stats')
        check = types.InlineKeyboardButton(text=adm_check, callback_data='check')
        download = types.InlineKeyboardButton(text=adm_backup_files, callback_data='backup')
        keyboard.add(admin_help, stats, check, download)
        bot.send_message(m.chat.id, adm_panel, reply_markup=keyboard)


# Stupid callback structure
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == 'changelog_call':
            keyboard = types.InlineKeyboardMarkup()
            about_key = types.InlineKeyboardButton(text='About', callback_data='about_call')
            keyboard.add(about_key)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=changelog,
                                  reply_markup=keyboard)

        if call.data == 'about_call':
            keyboard = types.InlineKeyboardMarkup()
            changelog_key = types.InlineKeyboardButton(text='Changelog', callback_data='changelog_call')
            keyboard.add(changelog_key)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=about_message,
                                  reply_markup=keyboard)

        if call.data == 'all':
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                button_triggers = types.InlineKeyboardButton(text=name_triggers, callback_data='all_triggers')
                button_admins = types.InlineKeyboardButton(text=name_admins, callback_data='all_admins')
                keyboard.add(button_triggers, button_admins)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=view_list, reply_markup=keyboard)

        if call.data == 'all_triggers':
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                back = types.InlineKeyboardButton(text=name_return, callback_data='all')
                keyboard.add(back)
                for trg in Trigger.select().where(Trigger.chat_id == call.message.chat.id):
                    msg = trigger_list + '\n'.join(trg.trigger_text) + ' [' + ''.join(str(trg.media_type)) + ']'
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=msg + '\n' + trigger_count.format(Trigger.select().count()),
                                  reply_markup=keyboard)

        if call.data == 'all_admins':
            if call.message.chat.type in ['group', 'supergroup']:
                keyboard = types.InlineKeyboardMarkup()
                back = types.InlineKeyboardButton(text=name_return, callback_data='all')
                keyboard.add(back)
                for adm in Admin.select().where(Admin.chat_id == call.message.chat.id):
                    msg = admin_list + ''.join(str(adm.username)) + ' [' + ''.join(str(adm.user_id)) + ']' + '\n'
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg,
                                  reply_markup=keyboard)

        if call.data == 'admin':
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                admin_help = types.InlineKeyboardButton(text=adm_commands, callback_data='admin_help')
                stats = types.InlineKeyboardButton(text=adm_stats, callback_data='stats')
                check = types.InlineKeyboardButton(text=adm_check, callback_data='check')
                download = types.InlineKeyboardButton(text=adm_backup_files, callback_data='backup')
                keyboard.add(admin_help, stats, check, download)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=adm_panel, reply_markup=keyboard)

        if call.data == 'backup':
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                back = types.InlineKeyboardButton(text=name_return, callback_data='admin')
                dt_now = datetime.datetime.now()
                Backup.create(backup_time=dt_now)
                shutil.copy2('bot.db', 'backup/backup{}.db'.format(Backup.select().count()))
                bot.send_document(owner, open('backup/backup{}.db'.format(Backup.select().count())))
                keyboard.add(back)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=admin_backup_complete + ' ' + name_return, reply_markup=keyboard)

        if call.data == 'check':
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                back = types.InlineKeyboardButton(text=name_return, callback_data='admin')
                delay = (time() - call.message.date) * 0.001
                keyboard.add(back)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=ping_message.format((str(delay)[:-12])) + ' ' + name_return,
                                      reply_markup=keyboard)

        if call.data == 'admin_help':
            if call.from_user.id == owner:
                keyboard = types.InlineKeyboardMarkup()
                rturn = types.InlineKeyboardButton(text="Назад", callback_data="admin")
                keyboard.add(rturn)
                bot.send_message(owner, admin_help_message)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=admin_message_complete + ' ' + name_return, reply_markup=keyboard)


@bot.message_handler(content_types=['new_chat_member'])
def invited(m):
    if m.new_chat_member.id == bot_id:
        bot.send_message(m.chat.id, invited_message)
        bot.send_message(owner, new_chat_member.format(m.chat.title, m.chat.id))


@bot.message_handler(content_types=['left_chat_member'])
def deleted(m):
    if m.left_chat_member.id == bot_id:
        bot.send_message(owner, left_chat_member.format(m.chat.title, m.chat.id))


@bot.message_handler(func=lambda m: True)
def response(m):
    if not is_recent(m):
        return
    if m.chat.type in ['group', 'supergroup']:
        for trg in Trigger.select().where(((Trigger.chat_id == m.chat.id) | (Trigger.trigger_type == 'global'))
                                          | ((Trigger.chat_id == m.chat.id) & (Trigger.trigger_type == 'context'))):
            if trg.trigger_text.lower() == m.text.lower():
                if trg.media_type == 'sticker':
                    bot.send_sticker(m.chat.id, trg.trigger_text)
                elif trg.media_type == 'photo':
                    bot.send_photo(m.chat.id, trg.trigger_text)
                elif trg.media_type == 'video':
                    bot.send_video(m.chat.id, trg.trigger_text)
                elif trg.media_type == 'voice':
                    bot.send_voice(m.chat.id, trg.trigger_text)
                elif trg.media_type == 'audio':
                    bot.send_audio(m.chat.id, trg.trigger_text)
                elif trg.media_type == 'document':
                    bot.send_document(m.chat.id, trg.trigger_text)
                elif trg.media_type == 'video_note':
                    bot.send_video_note(m.chat.id, trg.trigger_text)
                elif trg.media_type == 'text':
                    bot.send_message(m.chat.id, trg.trigger_text)
                else:
                    bot.send_message(owner, sql_error.format(trg.trigger_text))


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
    except:
        print('Токен [%s] неправильный')
        exit(1)
    try:
        bot.send_message(owner, 'Бот начал свою работу')
    except:
        print('''Бот https://telegram.me/%s нуждается в настройке''' % bot.get_me().username)
        exit(1)
    print('Safepolling начат')
    safepolling(bot)
