import telebot
from telebot import types
import sqlite3
import random
from Settings import TG_TOKEN


# Стандартный запрос к базе данных
def select_default():
    sel = 'SELECT DISTINCT title_ru, year, rating, num, genres, age_limit FROM Movies'
    return sel


# Запрос, позволяющий определить, относится ли фильм к данному жанру
def select_genre(genres):
    str_genres = 'genres ' + ' OR genres '.join(
        ['LIKE ' + '"%' + genre + '%"' for genre in genres])
    return '(' + str_genres + ')'


# Запрос, позволяющий определить, подходит ли фильм по данным параметрам
def select_params(params, column):
    params = sorted(params)
    params[:-1] = [(el[:el.find('-')], el[el.find('-') + 1:]) for el in params[:-1]]
    ind = params[-1].find('-')
    if params[-1] == full_info[2][-1] or params[-1] == full_info[3][-1]:
        params[-1] = (params[-1][:ind], str(int(params[-1][ind + 1:]) + 1))
    else:
        params[-1] = (params[-1][:ind], params[-1][ind + 1:])
    delim = ' OR (' + column
    str_params = '(' + column + delim.join(['>= ' + str(el[0]) + ' AND ' + column + ' < ' + str(el[1]) + ')'
                                            for el in params])
    return '(' + str_params + ')'


# Отбор фильмов по заданным параметрам
def selection(*args):
    connection = sqlite3.connect('Movies.db')
    cursor = connection.cursor()
    info = [i for i, x in enumerate(args[0]) if x]
    commands = [select_genre, select_params]
    sel = select_default()
    sels = []
    for i in info:
        if i == 0:
            sels.append(commands[i](args[0][i]))
        else:
            column = ('year', 'rating')[i - 1]
            sels.append(commands[1](args[0][i], column))
    if sels:
        sel = sel + ' WHERE ' + ' AND '.join(sels)
    cursor.execute(sel)
    rows = cursor.fetchall()
    if rows:
        row = random.sample(rows, 1)
    else:
        row = []
    return row


# Отбор уникальных значений в столбце
def sel_distinct_values(column):
    connection = sqlite3.connect('Movies.db')
    cursor = connection.cursor()
    sel = 'SELECT DISTINCT ' + column + ' FROM Movies'
    cursor.execute(sel)
    rows = cursor.fetchall()
    values = sorted(list(map(lambda x: x[0], rows)))
    if column == 'year':
        ind_st, ind_end = 0, 1
        periods = []
        for year in values[1:]:
            if year % 10 == 0:
                ind_end = values[ind_st:].index(year) + ind_st
                periods.append((str(values[ind_st]), str(year)))
                ind_st = ind_end
        if periods[-1][1] != str(values[-1]):
            periods.append((periods[-1][1], str(values[-1])))
        values = periods.copy()
    elif column == 'rating':
        values = [(1, 5), (5, 7), (7, 9), (9, 10)]
    connection.commit()
    connection.close()
    return values


# Поиск ключа по значению
def key_from_dict_value(dictionary, val):
    for key, value in dictionary.items():
        if val in value:
            return key


# Создание клавиатуры
def create_keyboard(values=None, given=None):
    buttons = []
    if not given:
        given = []
    if not values:
        values = []
    for value in values:
        if value in given:
            btn = types.InlineKeyboardButton(text='\u2705' + value, callback_data=value)
        else:
            btn = types.InlineKeyboardButton(text=value, callback_data=value)
        buttons.append(btn)
    kb = []
    if values == full_info[1]:
        for j in range(6, 15, 3):
            kb.append(buttons[j:j + 3])
            k = ((j - 6) // 3)
            kb.append(buttons[2 * k:2 * (k + 1)])
        kb.append(buttons[-4:])
    else:
        for i in range(len(buttons) // 3):
            kb.append(buttons[3 * i:3 * (i + 1)])
        if len(buttons) % 3 != 0:
            kb.append(buttons[3 * (i + 1):])
    for i in range(1, 4):
        if values == full_info[i]:
            text = ('Далее', 'Найти')[i == 3]
            btn = types.InlineKeyboardButton(text=text, callback_data='Далее-' + str(i))
            btn_1 = types.InlineKeyboardButton(text='Пропустить', callback_data='Пропустить-' + str(i))
    if values:
        kb.append([btn])
        kb.append([btn_1])
    menu = types.InlineKeyboardMarkup(keyboard=kb)
    return menu


# Функция возвращает текст сообщения и меню в зависимости от заданных параметров
def choose_film(values, values_need=None):
    menu = create_keyboard(values, values_need)
    texts = ['Выберите один или несколько жанров.\n', 'Выберите один или несколько периодов.\n',
             'Выберите рейтинг.\n']
    i = int(key_from_dict_value(full_info, values[0]))
    txt = texts[i - 1]
    sub_text = 'Если Вы сделали выбор, нажмите на кнопку ' + ('"Далее"', '"Найти"')[i == 3] + '.\n'
    txt = txt + '\n' * 2 + sub_text + 'Если вообще не хотите ничего выбирать, то нажмите на кнопку "Пропустить".'
    return txt, menu


bot = telebot.TeleBot(TG_TOKEN)
# Русские названия жанров
russian_version = ['Боевик', 'Приключения', 'Мультфильм', 'Детский', 'Комедия',
                   'Криминал', 'Документальный', 'Драма', 'Биографический',
                   'Фэнтези', 'Фильм-нуар', 'Ужасы', 'Мюзикл', 'Детектив',
                   'Романтический', 'Научно-фантастический', 'Триллер', 'Военный', 'Вестерн']
# Отсортируем их по убыванию длины названия
films = sorted(russian_version, key=len, reverse=True)
# Представим года в виде временных промежутков xxxx-xxxx
years = list(map(lambda x: '-'.join([str(x[0]), str(x[1])]), sel_distinct_values('year')))
# Представим рейтинг в виде промежутков
ratings = list(map(lambda x: '-'.join([str(x[0]), str(x[1])]), sel_distinct_values('rating')))
# Словарь значений
full_info = {1: films, 2: years, 3: ratings}
# Создадим пустой словарь, в котором будет храниться информация о запросе пользователя
global full_data
full_data = dict()


# Если пользователь дал одну из перечисленных команд, то
@bot.message_handler(commands=['find_movie', 'start'])
def start(message):
    # Выводит сообщение и клавиатуру
    txt, menu = choose_film(full_info[1])
    bot.send_message(chat_id=message.chat.id, text=txt, reply_markup=menu)
    # Заполняем информацию о запросе пользователя
    full_data[message.from_user.id] = [[] for i in range(3)]


# Если пользователь дал одну из перечисленных команд, то
@bot.message_handler(commands=['random_movie'])
def random_movie(message):
    # Выводит сообщение со смайлом
    bot.send_message(message.chat.id, '👇')
    # Выбирает случайный фильм из БД
    result = selection([[] for i in range(3)])
    # Выводит информацию о фильме в виде сообщения
    output(message.chat.id, result)


# Вывод результатов поиска в виде сообщения
def output(chat_id, result):
    if result:
        if result[0][5] != '0':
            film = result[0][0] + ' (' + result[0][5] + ')'
        else:
            film = result[0][0]
        link = 'http://kinopoisk.ru/film/' + str(result[0][3])
        if result[0][2]:
            text = 'Фильм: {}\nГод: {}\nРейтинг Кинопоиска: {}\nЖанр(-ы): {}\nСсылка на Кинопоиск: {}' \
                .format(film, result[0][1], result[0][2], result[0][4], link)
        else:
            text = 'Фильм: {}\nГод: {}\nЖанр(-ы): {}\nСсылка на Кинопоиск: {}' \
                .format(film, result[0][1], result[0][4], link)
    else:
        text = 'Увы! По Вашему запросу ничего не найдено. Попробуйте изменить параметры поиска.'
    bot.send_message(chat_id, text)


# Изменение текста сообщения
def edit_message_text(call, values=None, values_need=None):
    if values:
        txt, menu = choose_film(values, values_need)
    else:
        menu = create_keyboard()
        txt = '👇'
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=txt, reply_markup=menu)


# Определяет, была ли уже нажата данная кнопка
def get_values_need(call, values=None, values_need=None):
    for el in values:
        if call.data == el:
            if el not in values_need:
                values_need.append(el)
            else:
                values_need.remove(el)
            edit_message_text(call, values, values_need)
    return values_need


# Проверка отклика от пользователя
@bot.callback_query_handler(func=lambda call: True)
def check_callback_data(call):
    chat_id = call.message.chat.id
    if 'Далее' in call.data or 'Пропустить' in call.data:
        print(full_data[chat_id])
        i = int(call.data[-1])
        if 'Пропустить' in call.data:
            full_data[chat_id][i - 1].clear()
        if i != 3:
            edit_message_text(call, full_info[i + 1])
        if i == 3:
            edit_message_text(call)
            result = selection(full_data[chat_id])
            output(chat_id, result)
    else:
        i = int(key_from_dict_value(full_info, call.data))
        vals = get_values_need(call, full_info[i], full_data[chat_id][i - 1])
        full_data[chat_id][i - 1] = vals


bot.polling()
