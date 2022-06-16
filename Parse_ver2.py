import time
import pandas as pd
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from Settings import CHROME_DRIVER


def data_handler(data_frame):
    data_frame = pd.DataFrame(data_frame.loc[data_frame['genres'] != '(no genres listed)'])
    data_frame['year'] = data_frame['title'].apply(lambda x: get_year_title(x)[0])
    data_frame['title'] = data_frame['title'].apply(lambda x: get_year_title(x)[1])
    data_frame.dropna(inplace=True)
    return data_frame


def ru_name_handler(ru_name):
    extra = ['трейлеры,', 'даты премьер', chr(8212), 'смотреть онлайн', 'кассовые сборы', \
             'отзывы и рецензии', 'О фильме', 'фильмы', 'Форум на Кинопоиске', 'Кинопоиск', 'КиноПоиск', \
             'актеры и съемочная группа', 'связанные']
    for s in extra:
        if s in ru_name:
            ru_name = ru_name.replace(s, '')
    return ru_name.strip().strip('-').strip()


def get_name_from_string(string):
    name_eng, year = '', ''
    ind_1 = 0
    for i, el in enumerate(string):
        if el.isalpha():
            ind_1 = i
            break
    while string[ind_1].isalpha() or string[ind_1] != ',':
        name_eng = name_eng + string[ind_1]
        ind_1 += 1
    ind_2 = string.rfind(',')
    for el in string[ind_2 + 1:]:
        if el.isdigit():
            year = year + el
    return name_eng, year[:4]


def get_num_from_link(link):
    ind = link.rfind('/')
    return link[ind + 1:]


def get_page_source(movie, year):
    movie = movie.replace('&', 'and').replace("'ll", ' will').replace('/', ' ').replace("'", '').replace('+', 'plus')
    query = movie + ' фильм' + ' ' + str(int(year))
    query = query.replace(' ', '+')
    time.sleep(10)
    s = Service(CHROME_DRIVER)
    options = webdriver.ChromeOptions()
    options.add_argument('headless')  # для открытия headless-браузера
    browser = webdriver.Chrome(service=s, options=options)
    browser.get('https://yandex.ru/search/?text=' + query)
    source_data = browser.page_source
    parse = bs(source_data, "html.parser")
    return parse


def make_query_from_movie(movie, year):
    parse = get_page_source(movie, year)
    params = ['name_eng', 'rating', 'name_ru', 'age_limit']
    classes = [
        "serp-title serp-title_type_subtitle serp-title_black_yes typo typo_type_greenurl entity-search__subtitle",
        "rating-vendor rating-vendor_size_m rating-vendor_icon_kp typo typo_text_m typo_line_m entity-search__subtitle-rating",
        "serp-title serp-title_type_supertitle serp-title_font-weight_bold typo typo_text_xxl typo_line_m entity-search__title",
        "label label_color_white label_horizontal-padding_m label_font_own"]
    full_info = {}
    if parse.find_all('div', class_=classes[0]):
        full_info[params[0]] = get_name_from_string(parse.find_all('div', class_=classes[0])[0].get_text())[0]
        for p, cl in zip(params[1:], classes[1:]):
            if parse.find_all('div', class_=cl):
                full_info[p] = parse.find_all('div', class_=cl)[0].get_text()
            else:
                full_info[p] = '0'
        full_info['year'] = get_name_from_string(parse.find_all('div', class_=classes[0])[0].get_text())[1]
    else:
        full_info['name_eng'] = movie
        full_info['name_ru'] = parse.find('div', class_="serp-title serp-title_type_supertitle serp-title_font-weight_bold typo typo_text_xxl typo_line_m entity-search__title").get_text()
        full_info['rating'] = parse.find('span', class_="rating__value").get_text()
        full_info['age_limit'] = '0'
        full_info['year'] = str(year)

    full_info['link'] = get_num_from_link(parse.find_all('a',
                                                         class_="Button2 Button2_size_m Button2_view_clear Button2_type_link EntitySites-Button")[
                                              0]['href'])
    g = parse.find_all('li', class_="key-value__item")[0]
    genres_list = g.find('span', class_="text-cut2 typo typo_text_m typo_line_m").find_all('a',
                                                                                           class_="link link_theme_normal ajax i-bem")
    if not genres_list:
        genres_list = g.find('span', class_="text-cut2 typo typo_text_m typo_line_m")
    genres = [genre.get_text().title() for genre in genres_list]
    full_info['genres'] = ', '.join(genres)
    if full_info['name_eng'] != movie:
        full_info['name_eng'] = movie
    return full_info


def get_year_title(title):
    start = title.rfind('(')
    end = title.rfind(')')
    try:
        return int(title[start + 1:end]), title[:start - 1]
    except:
        return None, title[:start - 1]


def handle_data_from_file(year=None):
    if year is None:
        df = pd.read_csv('Информация о фильмах/movies.csv', sep=',')
        df = data_handler(df)
        file_name = 'Информация о фильмах/movies_ru_пример.txt'
    else:
        df = pd.read_csv('Информация о фильмах/films-' + str(year) + '_сырые.txt', sep=';', header=None,
                         index_col=None,
                         encoding='utf-8')
        df = pd.DataFrame(df)
        df.columns = ['title', 'genres', 'title_ru']
        df['title'] = df['title'].fillna(df['title_ru'])
        file_name = 'Информация о фильмах/films-' + str(year) + '_пример.txt'
    with open(file_name, 'a', encoding="utf-8") as f:
        for i in range(df.shape[0]):
            if year is None:
                movieId = str(df.loc[i, 'movieId'])
                year_new = int(df.loc[i, 'year'])
            else:
                movieId = str(year) + '-' + str(i)
                year_new = year
            title_eng = df.loc[i, 'title']
            year_new = str(year_new)
            full_info = make_query_from_movie(title_eng, year_new)
            print(movieId, full_info)
            f.write(';'.join([movieId, full_info['name_eng'], full_info['name_ru'],
                              full_info['year'], full_info['genres'],
                              full_info['rating'], full_info['link'],
                              full_info['age_limit']]) + '\n')


handle_data_from_file()
handle_data_from_file(2010)
handle_data_from_file(2020)