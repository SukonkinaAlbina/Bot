import time
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests


# Извлечение даты из названия фильма
def get_year_title(title):
    start = title.rfind('(')
    end = title.rfind(')')
    try:
        return int(title[start + 1:end]), title[:start - 1]
    except:
        return None, title[:start - 1]


# Предварительная обработка данных
def data_handler(data_frame):
    data_frame = pd.DataFrame(data_frame.loc[data_frame['genres'] != '(no genres listed)'])
    data_frame['year'] = data_frame['title'].apply(lambda x: get_year_title(x)[0])
    data_frame['title'] = data_frame['title'].apply(lambda x: get_year_title(x)[1])
    data_frame.dropna(inplace=True)
    return data_frame


# Обработка названия фильма на русском
def ru_name_handler(ru_name):
    extra = ['трейлеры,', 'даты премьер', chr(8212), 'смотреть онлайн', 'кассовые сборы', \
             'отзывы и рецензии', 'О фильме', 'фильмы', 'Форум на Кинопоиске', 'Кинопоиск', 'КиноПоиск', \
             'актеры и съемочная группа', 'связанные']
    for s in extra:
        if s in ru_name:
            ru_name = ru_name.replace(s, '')
    return ru_name.strip().strip('-').strip()


# Обработка рейтинга
def rating_handler(rating):
    ind = rating.find('/')
    rating = rating[:ind]
    return rating


# Обработка Интернет-запросов
def make_query_from_movie(movie, year):
    movie = movie.replace('&', 'and').replace("'", '').replace('/', ' ')
    query = movie + ' фильм' + ' ' + str(int(year))
    query = query.replace(' ', '+')
    time.sleep(10)
    r = requests.get('https://www.google.ru/search?q=' + query)
    parse = bs(r.text, features="html.parser")
    all_divs = parse.find_all('div')
    selection_a = [i for i, x in enumerate(all_divs) if x.find('a')]
    selection_h3 = [i for i, x in enumerate(all_divs) if x.find('h3')]
    k_1 = [i for i in selection_a if 'kinopoisk.ru' in all_divs[i].find('a').get('href')]
    k_2 = [i for i in selection_h3 if i in k_1]
    if k_2:
        ind = k_2[0]
        links = all_divs[ind].find_all('a')
        try:
            link = [get_film_number_from_link(x.get('href')) for x in links if
                    x.get('href') and 'kinopoisk.ru' in x.get('href') \
                    and ('film' in x.get('href') or 'series' in x.get('href') or 'name' in x.get('href'))][0]
        except:
            link = '0'
        ru_name = ru_name_handler(all_divs[ind].find('h3').text)
        try:
            rating_found = [all_divs[x].find('span', class_="oqSTJd").text for x in k_2 if \
                            all_divs[x].find('span', class_="oqSTJd")]
            if rating_found:
                rating = rating_handler(rating_found[0])
            else:
                rating = '0'
        except:
            rating = '0'
    else:
        link = '0'
        ru_name = movie
        rating = '0'
    print(ru_name, rating, link)
    return ru_name, rating, link


# Извлечение номера фильма на Кинопоиске из ссылки
def get_film_number_from_link(link):
    ind_1 = link.find('film/')
    if ind_1 == -1:
        ind_1 = link.find('series/')
        ind_2 = link[ind_1 + 7:].find('/')
        return link[ind_1 + 7:ind_1 + 7 + ind_2]
    else:
        ind_2 = link[ind_1 + 5:].find('/')
        return link[ind_1 + 5:ind_1 + 5 + ind_2]


# Обработка информации о фильмах из исходной таблицы.
def from_eng_to_ru():
    df = pd.read_csv('Информация о фильмах/movies.csv', sep=',')
    movies_df = data_handler(df)
    for i in range(movies_df.shape[0]):
        with open('Информация о фильмах/movies_ru_пример.txt', 'a', encoding="utf-8") as f:
            movie_id = str(movies_df.loc[i, 'movieId'])
            movie, year = movies_df.loc[i, ['title', 'year']]
            f.write(movie_id + ';' + movie + ';' + ';'.join(make_query_from_movie(movie, year)) + '\n')
