owner = 5673467820
__version__ = 0.8
tz_name = 'Europe/Kiev'

separator = '%'

about_message = '''
Триггербот %s
''' % __version__

help_message = '''Команды:
    Добавить триггеры:
        /add(context) <триггер> % <ответ>
        /add(context) <триггер> как ответ на сообщение        
    Удалить триггеры:
        /del(context) <триггер>
        /del(context) <триггер> как ответ на сообщение
    Информация о сообщении:
        /status
    Размер списка:
        /size
    Списки:
        /all
'''

admin_help_message = '''Команды:
    Добавить триггеры:
        /add(context) <триггер> % <ответ>
        /add(context) <триггер> как ответ на сообщение
    Удалить триггеры:
        /del(context) <триггер>
        /del(context) <триггер> как ответ на сообщение
    Информация о сообщении:
        /status
    Размер списка:
        /size
    Списки:
        /all        
Команды админа:
    Транслировать сообщение:
        /b <Сообщение>
    Добавить глобальные триггеры:
        /gadd <триггер> % <ответ>
        /gadd <триггер> как ответ на сообщение
    Удалить глобальные триггеры:
        /gdel <триггер>
        /gdel <триггер> как ответ на сообщение
    Добавить админа:
        /add_admin <ID>
        /add_admin как ответ на сообщение
    Удалить админа:
        /del_admin <ID>
        /del_admin как ответ на сообщение
    Найти триггер:
        /gsearch <триггер>
'''

trigger_created_message = '''
Триггер создан:
Триггер [{}]
Ответ [{}]
'''

context_trigger_created_message = '''
Контекст-триггер создан:
Триггер [{}]
Ответ [{}]
'''

global_trigger_created_message = '''
Глобальный триггер создан:
Триггер [{}]
Ответ [{}]
'''

global_trigger_deleted_message = '''
Триггер [{}] удален из {}
'''

invited_message = '''
Привет, я триггербот мятки.
Для списка команд введите /help
'''

changelog = '''
0.1:
    ...
0.2:
    Триггеры для медиа
    ---
    Исправление работы команд
    Исправление работы с исключениями
0.3:
    Были добавлены админы и все что с ними связано
    Добавлено логгирование
    ---
    Исправление работы команд
    Исправление опечаток
    Исправление работы статистики
    Исправление работы с большим количеством бесед    
0.4:
    Добавлена проверка статуса сообщения
    ---
    Исправление логгирования
0.5:
    Добавлены контекст-триггеры
0.6: 
    Все что можно переведено на инлайн-кнопки
    ---
    Исравление контекст-триггеров
0.7:
    Контекстные триггеры может добавлять только админ
0.8: 
    Полная переработка админки
    Увеличено количество инлайн-кнопок и уменьшено количество спама
    ---
    Фиксы админки    
'''


