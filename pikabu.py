# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Blackwave <blackwave-rt@hotmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except Exception in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import lxml.html
from lxml import etree
import sys
import requests
import base64
import re

ENDPOINT = "http://pikabu.ru/"
AUTH_URL = ENDPOINT + 'ajax/ajax_login.php'
XCSRF_TOKEN = None
SITE_REQUEST = requests.Session()
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0;\ Windows NT 6.0)",
    "Referer": "http://pikabu.ru/",
    "Host": "pikabu.ru",
    "Origin": "pikabu.ru"
}
POST_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}
IS_LOGGED = False
USER_DATA = {"login":None, "password":None}
XPATH_XCSRFTOKEN = "/html/head/script[3]"
XPATH_PIKAPOSTS_TITLE = '//*[@id="num_dig3%s"]'
XPATH_PIKAPOSTS_TEXT = '''//*[@id="story_table_%s"]//tr/td[2]/
table[@id="story_main_t"]//tr/td/div[2]'''
XPATH_PIKAPOSTS_DESC = '//*[@id="textDiv%s"]/text()'
XPATH_PIKAPOSTS_ATC = '''//*[@id="story_table_%s"]//tr/td[2]/
table[@id="story_main_t"]//tr/td/div[%s]/span[1]/a[%s]'''
XPATH_PIKAPOSTS_RATE = '//*[@id="num_digs%s"]'
XPATH_PIKAPOSTS_TAGS = '''//*[@id="story_table_%s"]//tr/td[2]/
table[@id="story_main_t"]//tr/td/div[3]/span[1]/span'''
XPATH_PIKACOM_LIST = '/comments/comment'
XPATH_PIKACOM_RATE = '//*[@id="%s"]//tr[1]/td/noindex/span'
XPATH_PIKACOM_AUT = '//*[@id="%s"]//tr[1]/td/noindex/a[%s]'
XPATH_PIKATAG = '//*[@id="story_main_t"]//tr[2]/td/div/a/span'
XPATH_PIKAUSER_AWARDS = '''//*[@id="wrap"]/table//tr/td[1]/
table[1]//tr/td[2]/div[1]/table//tr/td[3]/div/a/img'''
XPATH_PIKAUSER = '''//*[@id="wrap"]/table//tr/td[1]/
table//tr/td[2]/div[1]/table//tr/td[2]/div/text()'''
XPATH_PIKAUSER_MSG = '''//*[@id="right_menu"]/table[1]
//tr[2]/td/ul/li[5]/a/b'''
XPATH_PIKAUSER_LSMSG = '''//*[@id="com2"]//tr[2]/td/div/noindex/div/input'''
RE_PUSER_DOR = re.compile(r'пикабушник\s+уже\s+(.*)')


def fetch_url(_url, settings=None,
    _data=None, __method="POST", need_auth=True):
    """Выполняет запрос к сайту и возвращает результат в виде
    страницы
    В зависимости от типа запроса, авторизации и в каком доме находится
    сатурн - выполняет определенный запрос с подстановкой заголовков.

    """
    global IS_LOGGED
    if need_auth and not IS_LOGGED:
        url = AUTH_URL
        SITE_REQUEST.get(ENDPOINT, headers=DEFAULT_HEADERS)
        DEFAULT_HEADERS['X-Csrf-Token'] = SITE_REQUEST.cookies.get_dict()['PHPSESS']
        if USER_DATA['login'] is None:
            USER_DATA['login'] = settings.get('login')
            USER_DATA['password'] = settings.get('password')
        login_data = {
          "mode": "login",
          "username": USER_DATA['login'],
          "password": USER_DATA['password'],
          "remember": 0
        }
        resp = SITE_REQUEST.post(url, data=login_data, headers=DEFAULT_HEADERS)
        response = json.loads(resp.text)
        if int(response["logined"]) == 0:
            print 'Неверно указан логин или пароль'
            sys.exit(1)
        if int(response["logined"]) == -1:
            print response['error']
            sys.exit(1)
        IS_LOGGED = True

    if _url is not None:
        if _data is not None and len(_data) >= 1:
            _headers = DEFAULT_HEADERS
            '''_resp = SITE_REQUEST.get(ENDPOINT, headers=DEFAULT_HEADERS)
            XCSRF_TOKEN = lxml.html.document_fromstring(_resp.text).xpath(
                XPATH_XCSRFTOKEN)[0].text.strip()
            XCSRF_TOKEN = XCSRF_TOKEN.split("\n")[2].strip()
            XCSRF_TOKEN = XCSRF_TOKEN.replace("'", "").split(": ")[1]'''
            XCSRF_TOKEN = SITE_REQUEST.cookies.get_dict()['PHPSESS']
            if __method == "POST":
                _headers["Content-Type"] = POST_HEADERS["Content-Type"]
                _headers["Access"] = POST_HEADERS["Accept"]
                _headers["X-Csrf-Token"] = XCSRF_TOKEN  # inject X csrf token
                resp = SITE_REQUEST.post(ENDPOINT + _url, 
                    headers=_headers, data=_data)
            else:
                resp = SITE_REQUEST.get(ENDPOINT + _url, 
                    headers=_headers, params=_data)
        else:
            resp = SITE_REQUEST.get(ENDPOINT + _url, headers=DEFAULT_HEADERS)
        if need_auth:
            return resp.text
        else:
            return resp.content
    else:
        return False


class PikaService(object):
    """Абстрактный класс"""
    def __init__(self, **settings):
        if "login" not in settings or "password" not in settings:
            raise ValueError('Нужно указать логин и пароль')
        self.settings = settings

    def request(self, url, data=None, method='POST', need_auth=True):
        if url is not None:
            return fetch_url(url, self.settings, data, method, need_auth)
        else:
            return False


class PikabuPosts(PikaService):
    """Вывод постов из горячего, свежего, лучшего"""
    def get(self, query, page=1):
        _page = self.request('%s?page=%s&twitmode=1' % (query, page))
        if _page is not None:
            posts_list = []
            try:
                page_body = lxml.html.document_fromstring(
                    json.loads(_page)["html"].replace("<br>", "\\n"))
            except Exception:
                return False
            for post_id in json.loads(_page)["news_arr"]:
                post_title = page_body.xpath(
                    XPATH_PIKAPOSTS_TITLE % post_id)[0].text
                post_url = page_body.xpath(
                    XPATH_PIKAPOSTS_TITLE % post_id)[0].get("href")
                post_text = page_body.xpath(
                    XPATH_PIKAPOSTS_TEXT % post_id)[0].text
                post_image = page_body.cssselect(
                    'table#story_table_%s' % post_id)[0].get("lang")
                try:
                    post_desc = " ".join(
                        page_body.xpath(XPATH_PIKAPOSTS_DESC % post_id))
                except Exception:
                    post_desc = None
                try:
                    post_author = page_body.xpath(
                        XPATH_PIKAPOSTS_ATC % (post_id, 3, 3))[0].text
                    post_time = page_body.xpath(
                        XPATH_PIKAPOSTS_ATC % (post_id, 3, 4))[0].text
                    post_comments = page_body.xpath(
                        XPATH_PIKAPOSTS_ATC % (post_id, 3, 2))[0].text
                except Exception:
                    post_author = page_body.xpath(
                        XPATH_PIKAPOSTS_ATC % (post_id, 2, 3))[0].text
                    post_time = page_body.xpath(
                        XPATH_PIKAPOSTS_ATC % (post_id, 2, 4))[0].text
                    post_comments = page_body.xpath(
                        XPATH_PIKAPOSTS_ATC % (post_id, 2, 2))[0].text
                post_rating = page_body.xpath(
                        XPATH_PIKAPOSTS_RATE % post_id)[0].text
                post_tags = [result.text for result in page_body.xpath(
                        XPATH_PIKAPOSTS_TAGS % post_id)]
                posts_list.append(ObjectPosts(post_id, post_title, post_url,
                        post_text, post_image, post_desc,
                        post_author, post_time, post_comments,
                        post_rating, post_tags))
            return posts_list
        else:
            return False

    def search(self, query, cur_page=1,
        in_hot=True, in_pics=True, in_text=True, in_video=True):
        """Поиск по сайту с указанием страницы и разделов"""
        if query is not None:
            if in_hot:
                added_params = "&hot_search=on"
            if in_pics:
                added_params += "&pic_search=on"
            if in_text:
                added_params += "&text_search=on"
            if in_video:
                added_params += "&video_search=on"
            added_params += "&page=%s" % cur_page
            _page = self.request(
                'search.php?q=%s%s' % (query, added_params))
            posts_list = []
            page_body = lxml.html.document_fromstring(_page)
            for story in page_body.xpath('//*[@id="stories_container"]/table'):
                try:
                    post_id = int(story.get("attr"))
                    post_title = page_body.xpath(
                        XPATH_PIKAPOSTS_TITLE % post_id)[0].text
                    post_url = page_body.xpath(
                        XPATH_PIKAPOSTS_TITLE % post_id)[0].get("href")
                    post_text = page_body.xpath(
                        XPATH_PIKAPOSTS_TEXT % post_id)[0].text
                    post_image = page_body.cssselect(
                        'table#story_table_%s' % post_id)[0].get("lang")
                    try:
                        post_desc = " ".join(
                            page_body.xpath(XPATH_PIKAPOSTS_DESC % post_id))
                    except Exception:
                        post_desc = None
                    try:
                        post_author = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 3, 3))[0].text
                        post_time = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 3, 4))[0].text
                        post_comments = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 3, 2))[0].text
                    except Exception:
                        post_author = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 2, 3))[0].text
                        post_time = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 2, 4))[0].text
                        post_comments = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 2, 2))[0].text
                    try:
                        post_rating = page_body.xpath(
                            XPATH_PIKAPOSTS_RATE % post_id)[0].text
                    except Exception:
                        post_rating = "NaN"
                    post_tags = [result.text for result in page_body.xpath(
                            XPATH_PIKAPOSTS_TAGS % post_id)]
                    posts_list.append(ObjectPosts(post_id, post_title, post_url,
                                        post_text, post_image, post_desc,
                                        post_author, post_time, post_comments,
                                        post_rating, post_tags))
                except Exception:
                    return False
            return posts_list
        else:
            return False

    def tag(self, tag_name, page=1, category="new"):
        """Вывод новостей по указанному тегу"""
        if tag_name and category is not None:
            _page = self.request(
                'tag/%s/%s?page=%s&twitmode=1' % (tag_name, category, page))
            if _page is not None:
                posts_list = []
                try:
                    __page = json.loads(_page)["html"].replace("<br>", "\\n")
                    page_body = lxml.html.document_fromstring(__page)
                except Exception:
                    return False
                for post_id in json.loads(_page)["news_arr"]:
                    post_title = page_body.xpath(
                        XPATH_PIKAPOSTS_TITLE % post_id)[0].text
                    post_url = page_body.xpath(
                        XPATH_PIKAPOSTS_TITLE % post_id)[0].get("href")
                    post_text = page_body.xpath(
                        XPATH_PIKAPOSTS_TEXT % post_id)[0].text
                    post_image = page_body.cssselect(
                        'table#story_table_%s' % post_id)[0].get("lang")
                    try:
                        post_desc = " ".join(
                            page_body.xpath(XPATH_PIKAPOSTS_DESC % post_id))
                    except Exception:
                        post_desc = None
                    try:
                        post_author = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 3, 3))[0].text
                        post_time = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 3, 4))[0].text
                        post_comments = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 3, 2))[0].text
                    except Exception:
                        post_author = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 2, 3))[0].text
                        post_time = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 2, 4))[0].text
                        post_comments = page_body.xpath(
                            XPATH_PIKAPOSTS_ATC % (post_id, 2, 2))[0].text
                    try:
                        post_rating = page_body.xpath(
                            XPATH_PIKAPOSTS_RATE % post_id)[0].text
                    except Exception:
                        post_rating = "NaN"
                    post_tags = [result.text for result in page_body.xpath(
                            XPATH_PIKAPOSTS_TAGS % post_id)]
                    posts_list.append(ObjectPosts(post_id, post_title, post_url,
                                        post_text, post_image, post_desc,
                                        post_author, post_time, post_comments,
                                        post_rating, post_tags))
                return posts_list
            else:
                return False
        else:
            return False

    def add_pic(self, header, description, image,
        tags, is_my=False, is_adult=False):
        """Постинг картинки на пикабу
        Изображение указывается в виде ссылки на компьютере
        Теги указываются списком

        """
        pass

    def add_text(self, header, text, tags, is_my=False, is_adult=False):
        """Постинг текстовой информации на пикабу"""
        pass


class PikabuComments(PikaService):
    """Вывод комментариев по указанному материалу"""
    def get(self, post_id, post_url=''):
        if post_id is not None:
            _page = self.request("generate_xml_comm.php?id=" + str(post_id))
            if _page is not None:
                comment_list = []
                page_body = etree.fromstring(_page.encode("utf-8"))
                for item in page_body.xpath(XPATH_PIKACOM_LIST):
                    comment_id = item.attrib['id']
                    comment_rating = item.attrib['rating']
                    comment_author = item.attrib['nick']
                    comment_parent = item.attrib['answer']
                    comment_time = item.attrib['date']
                    comment_text = item.text
                    comment_list.append(ObjectComments(comment_id,
                                comment_rating, comment_author,
                                comment_time, comment_text, comment_parent))
                return comment_list
            else:
                return False
        else:
            return False

    def add(self, text, post_id, comment_id=0):
        """Добавление комментария на пикабу"""
        if post_id and text is not None:
            _page = self.request("ajax.php", {
                'act': "addcom",
                'id': post_id,
                'comment': text,
                'parentid': comment_id,
                'include': 0,
                'comment_images': 'undefined'}, "POST")
            if _page is not None:
                try:
                    return json.loads(_page)["type"]
                except Exception:
                    return False
            else:
                return False
        else:
            return False

class PikabuTopTags(PikaService):
    """Список популярных за сутки тегов"""
    def get(self, limit=10):
        if limit >= 1:
            _page = self.request("html.php?id=ad")
            if _page is not None:
                tag_list = {}
                page_body = lxml.html.document_fromstring(_page)
                caret = []
                for cur_tag in page_body.xpath(XPATH_PIKATAG):
                    if len(caret) <= 1:
                        caret.append(cur_tag.text)
                    else:
                        tag_list[len(tag_list) + 1] = caret
                        caret = []
                        caret.append(cur_tag.text)
                return tag_list
            else:
                return False
        else:
            return False


class PikabuUserInfo(PikaService):
    """Класс информации о пользователе"""
    def __init__(self, **settings):
        self.rating     = None
        self.followers  = None
        self.messages   = None
        self.registered = None
        self.comments   = None
        self.news       = []
        self.actions    = {}
        self.awards     = []
        self.settings   = settings

    def get(self, login, params=""):
        """Возвращает информацию о пользователе"""
        _page = self.request("profile/" + login)
        page_body = lxml.html.document_fromstring(_page)
        for x in page_body.xpath( XPATH_PIKAUSER ):
            response = re.sub( "\s+", " ", x.encode("utf-8").strip() )
            if len(response) >= 3:        
                if response.startswith("пикабушник уже"):
                    parsed = re.search( RE_PUSER_DOR, response )
                    if parsed.group():self.registered = parsed.group(1)
                    else:self.registered = "None"                
                elif response.startswith("рейтинг"):
                    parsed = re.sub( "\s", "", response)
                    try:self.rating = parsed.split(":")[1]
                    except:self.rating = 0
                elif response.startswith("комментариев"):
                    parsed = re.sub( "\s", "", response)
                    try:self.comments = parsed.split(":")[1]
                    except:self.comments = 0              
                elif response.startswith("добавил постов"):
                    parsed = re.sub( "\s", "", response)
                    try:self.news = [x.split(":")[1] for x in parsed.split(",")]
                    except:self.news = 0
                elif response.endswith("минусов"):
                    self.actions["dislike"] = filter(lambda x: x.isdigit(), response)
                elif "плюсов" in response:
                    self.actions["like"] = filter(lambda x: x.isdigit(), response)                    

        return ObjectUserInfo(login, self.registered,
            self.rating, self.comments,
            self.news, self.actions, self.awards)


    def _awards(self, login):
        """Возвращает список наград пользователя"""
        if len(self._awards) == 0:
            _page = self.request("profile/" + login)
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._awards = map(
                    lambda x: x.get("title").encode('utf-8'), 
                    page_body.xpath(XPATH_PIKAUSER_AWARDS)
                )
            else:
                pass
        else:
            pass
        return self._awards


class PikabuProfile(PikabuUserInfo):
    """Профиль авторизованного пользователя"""
    def __init__(self, **settings):
        self._rating = None
        self._followers = None
        self._messages = None
        self._dor = None
        self._comments = None
        self._mynews = []
        self._actions = []
        self._awards = []
        self.settings = settings

    def get(self, params=""):
        """Возвращает информацию о пользователе"""
        if params != "":
            if params == "dor":
                return self.dor()
            if params == "rating":
                return self.rating()
            if params == "comments":
                return self.comments()
            if params == "news":
                return self.news()
            if params == "actions":
                return self.actions()
            if params == "awards":
                return self.awards()
            if params == "awards":
                return self.awards()
            if params == "followers":
                return self.followers()
            if params == "messages":
                return self.messages()
            if params == "last_msg":
                return self.last_msg()
        return ObjectUserInfo(self.settings["login"], self.dor(),
            self.rating(), self.comments(),
            self.news(), self.actions(), self.awards(), self.followers(), self.messages(), self.last_msg())

    def dor(self):
        """Возвращает дату регистрации пользователя"""
        return super(PikabuProfile, self).dor(self.settings["login"])

    def rating(self):
        """Возвращает рейтинг пользователя"""
        return super(PikabuProfile, self).rating(self.settings["login"])

    def comments(self):
        """Возвращает количество комментариев"""
        return super(PikabuProfile, self).comments(self.settings["login"])

    def news(self):
        """Возвращает количество новостей и их число в горячем"""
        return super(PikabuProfile, self).news(self.settings["login"])

    def actions(self):
        """Возвращает массив с плюсами и минусами юзера"""
        return super(PikabuProfile, self).actions(self.settings["login"])

    def awards(self):
        """Возвращает массив с наградами пользователя"""
        return super(PikabuProfile, self).awards(self.settings["login"])

    def followers(self):
        """Возвращает количество подписчиков"""
        if self._followers is None:
            _page = self.request("profile/" + self.settings["login"])
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._followers = page_body.xpath(
                    '//*[@id="subs_num"]')[0].text.strip()
        else:
            pass
        return self._followers

    def messages(self):
        """Возвращает количество сообщений пользователю"""
        if self._messages is None:
            _page = self.request("profile/" + self.settings["login"])
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                try:
                    self._messages = page_body.xpath(
                        XPATH_PIKAUSER_MSG)[0].text
                except Exception:
                    self._messages = 0
        else:
            pass
        return self._messages

    def last_msg(self):
        """Возвращает последнее сообщение пользователю"""
        _page = self.request("freshitems.php")
        if _page is not None:
            page_body = lxml.html.document_fromstring(_page)
            try:
                comment_text = page_body.xpath(
                    '//*[@id="com2"]//tr[2]/td/div/div')[0].text.strip()
            except Exception:
                comment_text = None
                return False
            if comment_text is not None:
                comment_id = page_body.xpath(
                    XPATH_PIKAUSER_LSMSG)[0].get("value")
                comment_author = page_body.xpath(
                    '//*[@id="com2"]//tr[1]/td/noindex/a[3]')[0].text
                comment_time = page_body.xpath(
                    '//*[@id="com2"]//tr[1]/td/noindex/a[4]')[0].text
                comment_rating = page_body.xpath(
                    '//*[@id="com2"]//tr[1]/td/noindex/h6')[0].text
                comment_post = page_body.xpath(
                    '//*[@id="com2"]//tr[1]/td/noindex/a[5]')[0].text
                return ObjectComments(comment_id, comment_rating,
                    comment_author, comment_time,
                    comment_text, comment_post)
            else:
                return False
        else:
            return False

    def set(self, arg, value):
        pass


class PikabuRegistration(PikaService):
    """Класс для регистрации пользователя
    После вызова api.register() она возвращает base64 капчи, код которой
    нужно указать последним параметром в функции add
    """
    def __init__(self, **settings):
        self.rv = None
        self.first_hidden = None
        self.pass_name = None
        self.settings = settings

    def __call__(self):
        """Возвращает капчу и секретные поля"""
        _page = self.request("index.php", None, "POST", False)
        page_body = lxml.html.document_fromstring(_page)        
        self.first_hidden = page_body.xpath(
            '//*[@id="form2"]/input[2]')[0].get("name")
        self.rv = re.search(
            '\$\("\#rv"\)\.val\(\'(\w+)\'\);', page_body.xpath(
            '/html/head/script[6]')[0].text).group(1)
        self.pass_name = page_body.xpath(
            '//*[@id="rm_pass"]')[0].get("name")
        _page = self.request(
            "kcaptcha/index.php?PHPSESS=%s"%SITE_REQUEST.cookies["PHPSESS"],
             None, "POST", False)
        return {"image":base64.encodestring(_page)}

    def add(self, login, password, email, captcha_code):
        global IS_LOGGED
        """Функция проверяет существование юзера, почты и капчу.
        Если все круто - регистрирует юзера, если нет - возвращает ошибку
        """
        if self.pass_name and self.rv and self.first_hidden is not None:
            """Проверяем свободен ли логин"""
            check_login = self.request(
                "signup.php?avail=" + login, None, "POST", False)
            if check_login.endswith("0"):
                return {"result":False, 
                "error":"Логин уже используется"}

            """Проверяем свободен ли ящик"""
            check_email = self.request(
                "ajax/ajax_login.php", {
                "mode": "test_email",
                "email": email
                }, "POST", False)
            if int(check_email) == 1:
                return {"result":False, 
                "error":"Почтовый ящик уже используется"}

            """Проверяем капчу"""
            check_captcha = self.request("signup.php", {
                "check_captcha": 1,
                "captcha": captcha_code
                }, "POST", False)
            if int(check_captcha) == 1:
                return {"result":False, 
                "error":"Неверно указана капча"}

            _page = self.request("signup.php", {
                'enter_type': "simple",
                'username': login,
                self.first_hidden:"",
                'email': email,
                'rv': self.rv,
                self.pass_name: password,
                'password2':password,
                'captcha': captcha_code,
                'agree': 1}, "POST", False)
            self.settings['login'] = login
            self.settings['password'] = password
            IS_LOGGED = True
            return True
        else:
            return {"result":False, 
            "error":"Произошла ошибка, попробуйте получить капчу еще раз!"}    


class PikabuSetRating(PikaService):
    """Смена рейтинга поста/комментария"""
    def set(self, action, _type, post_id, comment_id=None):
        if _type == 1:
            if action:
                act = "+"
            else:
                act = "-"
            _page = self.request("ajax/dig.php", {"i": post_id, "type": act})
            if _page is not None:
                return _page
            else:
                return False
        else:
            if comment_id and post_id is not None:
                if action:
                    act = 1
                else:
                    act = 0
                _page = self.request(
                    "dig.php", {
                    'type': "comm",
                    'i': comment_id,
                    'story': post_id,
                    'dir': act}, "GET")
                if _page is not None:
                    return _page
            else:
                return False


class ObjectPosts():
    """Объект с постами"""
    def __init__(self, _id, title, url, description,
        image, text, author, time, comment, rating, tags):
        self.id = _id
        self.title = title
        self.url = url
        self.description = description
        self.tags = None
        self.image = image
        self.text = text
        self.author = author
        self.time = time
        self.comments = comment
        self.rating = rating
        self.tags = tags

    def tags(self, tags):
        self.tags = tags


class ObjectComments():
    """Объект с комментариями"""
    def __init__(self, _id, rating, author, 
        time, text, parent=0, post=None):
        self.id = _id
        self.rating = rating
        self.author = author
        self.time = time
        self.text = text
        self.post = post
        self.parent = parent


class ObjectUserInfo():
    """Объект информации о пользователе"""
    def __init__(self, login, dor, rating, comments, news, actions, awards, followers=None, messages=None, last_msg=None):
        self.login = login
        self.dor = dor
        self.rating = rating
        self.comments = comments
        self.news = news
        self.actions = actions
        self.awards = awards
        self.followers = followers
        self.messages = messages
        self.last_msg = last_msg


class Api:
    """Основной класс инициализирующий сервисы пикабу"""
    def __init__(self, **settings):
        self._settings = settings
        self.posts = PikabuPosts(**self._settings)
        self.comments = PikabuComments(**self._settings)
        self.top_tags = PikabuTopTags(**self._settings)
        self.users = PikabuUserInfo(**self._settings)
        #self.user_posts  = PikabuUserPosts(**self._settings)
        self.profile = PikabuProfile(**self._settings)
        self.rate = PikabuSetRating(**self._settings)
        self.register = PikabuRegistration(**self._settings)