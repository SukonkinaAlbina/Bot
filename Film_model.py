class Film:
    params = ['title_ru', 'year', 'rating', 'num', 'genres', 'age_limit']

    def __init__(self, result):
        self.result = result
        if self.result:
            for i, p in enumerate(self.params):
                setattr(self, p, self.result[0][i])

    def output(self):
        if self.result:
            if getattr(self, 'age_limit') != '0':
                film = getattr(self, 'title_ru') + ' (' + getattr(self, 'age_limit') + ')'
                setattr(self, 'title_ru', film)
            link = 'http://kinopoisk.ru/film/' + str(getattr(self, 'num'))
            if getattr(self, 'rating'):
                text = 'Фильм: {}\nГод: {}\nРейтинг Кинопоиска: {}\nЖанр(-ы): {}\nСсылка на Кинопоиск: {}' \
                    .format(getattr(self, 'title_ru'),
                            getattr(self, 'year'),
                            getattr(self, 'rating'),
                            getattr(self, 'genres'),
                            link)
            else:
                text = 'Фильм: {}\nГод: {}\nЖанр(-ы): {}\nСсылка на Кинопоиск: {}' \
                    .format(getattr(self, 'title_ru'),
                            getattr(self, 'year'),
                            getattr(self, 'genres'),
                            link)
        else:
            text = 'Увы! По Вашему запросу ничего не найдено. Попробуйте изменить параметры поиска.'
        return text



