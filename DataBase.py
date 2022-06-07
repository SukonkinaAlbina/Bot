import sqlite3
import pandas as pd
import pickle


# получить год из названия фильма
def get_year_title(title):
    start = title.rfind('(')
    end = title.rfind(')')
    try:
        return int(title[start + 1:end]), title[:start - 1]
    except:
        return None, title[:start - 1]


# обработка исходной таблицы данных
def data_handler(data_frame):
    data_frame = pd.DataFrame(data_frame.loc[data_frame['genres'] != '(no genres listed)'])
    data_frame['year'] = data_frame['title'].apply(lambda x: get_year_title(x)[0])
    data_frame['title'] = data_frame['title'].apply(lambda x: get_year_title(x)[1])
    data_frame.dropna(inplace=True)
    data_frame['genres'] = data_frame['genres'].apply(translate_genres_into_rus)
    return data_frame


# очистка русских названий от лишних слов и символов
def ru_name_handler(ru_name):
    extra = ['трейлеры,', 'даты премьер', chr(8212), 'смотреть онлайн', 'кассовые сборы', \
             'отзывы и рецензии', 'О фильме', 'фильмы', 'Кинопоиск', 'КиноПоиск', \
             'актеры и съемочная группа', 'связанные']
    for s in extra:
        if s in ru_name:
            ru_name = ru_name.replace(s, '')
    return ru_name.strip().strip('-').strip()


# обработка таблицы с русскими названиями
def ru_data_handler(data_frame):
    data_frame['film/serial'] = data_frame['title_ru'].apply(lambda x: 'сериал' not in x.lower())
    data_frame = data_frame[data_frame['film/serial'] == 1]
    data_frame = data_frame.drop(columns=['film/serial'])
    data_frame['title_ru'] = data_frame['title_ru'].apply(ru_name_handler)
    data_frame['rating'] = data_frame['rating'].apply(lambda x: float(x.replace(',', '.')))
    data_frame['num'] = data_frame['num'].astype(int)
    data_frame = data_frame[data_frame['num'] != 0]
    data_frame['genres'].replace('Война', 'Военный')
    data_frame['genres'].replace('Романтика', 'Романтический')
    return data_frame


# сохраняем словарь в файл .pkl
def save_obj(dict, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(dict, f, pickle.HIGHEST_PROTOCOL)


# считываем информацию из файла
def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


# создаём словарь типа {русское название жанра: английское} и сохраняем в файл
def get_eng_genre_name(data_frame):
    dict_movies, dict_genres = {}, {}
    for movie, genres in zip(data_frame['title'], data_frame['genres']):
        dict_movies.setdefault(movie, []).append(genres.split('|'))

    unique_genres = set()
    for val in dict_movies.values():
        for arr in val:
            for el in arr:
                unique_genres.add(el)
    unique_genres.discard('IMAX')
    unique_genres = sorted(unique_genres)
    russian_version = ['Боевик', 'Приключения', 'Мультфильм', 'Детский', 'Комедия', 'Криминал', \
                       'Документальный', 'Драма', 'Фэнтези', 'Фильм-нуар', 'Ужасы', \
                       'Мюзикл', 'Детектив', 'Романтический', 'Научно-фантастический', 'Триллер', \
                       'Военный', 'Вестерн']
    dict_genres = dict(zip(russian_version, unique_genres))
    save_obj(dict_genres, 'Информация о фильмах/genres_ru_eng')
    return dict_genres


# перевести названия жанров на русский
def translate_genres_into_rus(genres):
    genres_load = load_obj('genres_ru_eng')
    genres = genres.split('|')
    for i, genre in enumerate(genres):
        for key, value in genres_load.items():
            if value == genre:
                genres[i] = key
    return ', '.join(genres)


# создание базы данных
def create_db(data_frame):
    connection = sqlite3.connect('Movies.db')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Movies
    (movieId TEXT, title_eng TEXT, title_ru TEXT, year INT, genres TEXT, rating FLOAT, num INT)
    ''')
    data_frame.to_sql('Movies', connection, if_exists='append', index=False)
    connection.commit()
    connection.close()
    print('БД создана')


# Добавление записей в базу данных
def insert_into_db(rows):
    connection = sqlite3.connect('Movies.db')
    cursor = connection.cursor()
    rows.to_sql('Movies', connection, if_exists='append', index=False)
    connection.commit()
    connection.commit()
    cursor.close()
    print('Записи успешно добавлены в БД')


# Проверка количества записей в базе данных
def check_count():
    connection = sqlite3.connect('Movies.db')
    cursor = connection.cursor()
    query = """SELECT COUNT(*) FROM Movies"""
    cursor.execute(query)
    count = cursor.fetchone()
    print('Размер базы данных - {}'.format(count[0]))
    connection.commit()
    cursor.close()


# Объединение баз данных с данными на английском и на русском
def merge_eng_ru():
    df = pd.read_csv('Информация о фильмах/movies.csv')
    movies_eng = data_handler(df)
    df_1 = pd.read_csv('Информация о фильмах/movies_ru_пример.txt', sep=';', header=None, index_col=None, encoding='utf-8')
    df_1.columns = ['movieId', 'title_eng', 'title_ru', 'rating', 'num']
    res = df_1.merge(movies_eng, how='inner')
    res = res.loc[:, ['movieId', 'title_eng', 'title_ru', 'year', 'genres', 'rating', 'num']]
    return res


# Считывание файла и предоставление данных в виде таблицы
def read_file(file_name):
    df = pd.read_csv(file_name, sep=';', header=None, index_col=None,
                     encoding='utf-8')
    df = pd.DataFrame(df)
    df.columns = ['movieId', 'title_eng', 'title_ru', 'year', 'genres', 'rating', 'num']
    df['rating'] = df['rating'].astype('str')
    return df


# Функция для проверки повторяющихся строк
def check_duplicates():
    connection = sqlite3.connect('Movies.db')
    cursor = connection.cursor()
    query = """SELECT num, movieId FROM Movies group by num having count(*)>1"""
    cursor.execute(query)
    res = cursor.fetchall()
    print('Повторяющихся строк - {}'.format(len(res)))
    connection.commit()
    cursor.close()
    return res


# Удаление повторов
def delete_duplicates(ids):
    sqlite_connection = sqlite3.connect('Movies.db')
    cursor = sqlite_connection.cursor()
    query = """DELETE from Movies where movieId = ?"""
    cursor.executemany(query, ids)
    sqlite_connection.commit()
    print("Удалено записей:", cursor.rowcount)
    sqlite_connection.commit()
    cursor.close()


# Объединяем таблицы с английскими и русскими названиями
movies_all = merge_eng_ru()
# Считываем из файла информацию о фильмах 2010 года
movies_2010 = read_file('Информация о фильмах/films-2010_пример.txt')
# Считываем из файла информацию о фильмах 2020 года
movies_2020 = read_file('Информация о фильмах/films-2020_пример.txt')
# Добавляем фильмы 2010 года в таблицу
movies_all = pd.concat([movies_all, movies_2010], ignore_index=True)
# Обрабатываем данные, чтобы привести их к общему виду
movies_all = ru_data_handler(movies_all)
# Создаём базу данных на основе полученной таблицы
create_db(movies_all)
# Вставляем в БД строки с фильмами 2020 года
insert_into_db(ru_data_handler(movies_2020))
# Проверяем базу данных на наличие повторяющихся строк
dupl = check_duplicates()
# Извлекаем только movieId для каждой повторяющейся строки
all_dupls = [(el[1],) for el in dupl]
# Удаляем дубликаты
delete_duplicates(all_dupls)
