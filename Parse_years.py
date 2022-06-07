import time
from bs4 import BeautifulSoup as bs
import requests
from Settings import SITE


def parsing(year, site=SITE):
    site = site + str(year) + '/nojs?page='
    for j in range(100):
        time.sleep(10)
        r = requests.get(site + str(j))
        parse = bs(r.text, features="html.parser")
        all_divs = parse.find_all('div', class_="film_list")
        titles_ru = [x['title'] for x in all_divs]
        links = parse.find_all('a', class_="film_list_link")
        titles_eng = [link.find_all('span')[0].find('span')['title'] for link in links]
        genres = [link.find_all('span')[3].text.split(',')[0] for link in links]
        with open('Информация о фильмах/films-' + str(year) + '_сырые.txt', 'a', encoding="utf-8") as f:
            for i in range(len(titles_ru)):
                params = [titles_eng[i], genres[i], titles_ru[i]]
                print(params)
                f.write(";".join(params) + '\n')


parsing(2010)
parsing(2020)
