pikabu
======

Неофициальный клиент на Python для pikabu.ru

pikabu - это источник интересных статей, фотографий и видео, добавляемых пользователями. Вы добавляете пост: фото, видео или историю.
Данная библиотека была создана от безысходности из-за отсутствия официального Апи на сайте pikabu.ru. Автором библиотеки является [Blackwave](http://pikabu.ru/profile/blackwave).

В ближайшее время планирую добавить публикацию поста/комментария, изменение рейтинга у постов/комментариев и настройки.

## Установка

Из pip:
```bash
$ sudo pip install pikabu
```
Из исходников:
```bash
$ git clone https://github.com/Blackwave-rt/pikabu && cd pikabu
$ sudo python setup.py install
```
Готово!

## Быстрый старт

Все до ужаса просто.
   ```python
   import pikabu
   pika_api = pikabu.Api(login='ваш логин', password='ваш пароль')
```
Все дальнейшие операции будут происходить через pika_api.

Например, получим заоблачный рейтинг пользователя [Admin](http://pikabu.ru/profile/admin):
```python
   import pikabu
   pika_api = pikabu.Api(login='ваш логин', password='ваш пароль')
   pika_api.users.get("admin", "rating")
```

## Документация по возможностям

###api.posts.get( (string)category, (int)page )
Возвращает массив постов по выборке: горячее, популярные, свежее.

Аргументы: [hot|best|new], страница

Результат: А в результате возвращается массив с объектом "ObjectPosts", который обладает аргументами:

	title    - вернет название поста
	url      - вернет название ссылки
	text     - вернет текст поста (в случае, если это изображение - вернет None)
	image    - вернет изображение поста (в случае, если пост текстовый - вернет None)
	time     - вернет дату создания (два часа назад, etc)
	author   - вернет ник автора
	comments - вернет количество комментариев
	rating   - вернет рейтинг поста
	tags     - вернет массив тегов поста

	
###api.users.get( (string)login, (string)param )

Возвращает объект "ObjectUserInfo" в случае, если параметр не был указан. Или (если он все же был указан, лол) возвращает значение запрашиваемого параметра.

####Параметры:

	dor 	 - дата регистрации
	rating   - рейтинг юзера
	comments - количество комментариев
	news     - возвращает массив вида [количество новостей, в горячем]
	actions  - возвращает массив вида [поставил плюсов, поставил минусов]
	avatar   - возвращает ссылку на аватарку юзера
	awards   - возвращает список наград


####Пример:
    api.users("Blackwave", dor) - вернет дату регистрации

    api.users("Blackwave") - вернет объект "ObjectUserInfo", который имеет аргументы:
Аргументы:

		dor 	   - дата регистрации
		rating   - рейтинг юзера
		comments - количество комментариев
		news     - возвращает массив вида [количество новостей, в горячем]
		actions  - возвращает массив вида [поставил плюсов, поставил минусов]
		avatar   - возвращает ссылку на аватарку юзера
		awards   - возвращает список наград


###api.profile
Возвращает информацию по Вашему пользователю. Доступные методы:

		api.profile.dor()
		api.profile.rating()
		api.profile.comments()
		etc


###api.comments.get( (string)alias, (int)post_id )
Возвращает комментарии к выбранному посту (алиас вида: nazvanie_temy_1234567)

    api.comments(nazvanie_temy_1234567, 1234567) - вернет объект "ObjectComments"
    
Аргументы:

    	id     - id комментария
    	rating - рейтинг комментария
    	author - логин автора
    	time   - время добавления
    	text   - текст комментария


###api.top_tags.get()
Возвращает популярные за сутки теги. Вид: [название тега, количество]

###api.posts.search( (string)query, (int)cur_page, (bool)in_hot, (bool)in_pics, (bool)in_text, (bool)in_video )
Возвращает результаты поиска в виде объекта ObjectPosts. Аргументы соответствуют api.posts.get

###api.posts.tag( (string)tag_name, (int)page, (string)category )
Возвращает отфильтрованные по тегам посты в виде объекта ObjectPosts. Аргументы соответствуют api.posts.get

###api.rate.set( (bool)action, (int)type, (int)post_id, (int or None)comment_id )
Позволяет ставить рейтинг постам и комментариям.
Параметры:
action - True/False +/-, соответственно.
type   - 1 - пост, 2 - комментарий
post_id - ид поста
comment_id - ид комментария. Не указывается при type=1

###api.comments.add( (string)text, (int)post_id, (int)comment_id )
Позволяет добавлять комментарии к посту post_id или к комментарию comment_id (обязательно указывайте post_id)
## Лицензия

Библиотека доступна на условиях лицензии Apache версии 2.0

http://www.apache.org/licenses/LICENSE-2.0
