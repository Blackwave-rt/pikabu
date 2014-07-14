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
XPATH_PIKAUSER_ACT = '''//*[@id="wrap"]/table//tr/td[1]/
table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/div/text()'''
XPATH_PIKAUSER_NEWS = '''//*[@id="wrap"]/table//tr/td[1]/
table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()'''
XPATH_PIKAUSER_COM = '''//*[@id="wrap"]/table//tr/td[1]/
table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()'''
XPATH_PIKAUSER_RATE = '''//*[@id="wrap"]/table//tr/td[1]/
table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()'''
XPATH_PIKAUSER_DOR = '''//*[@id="wrap"]/table//tr/td[1]/
table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()'''
XPATH_PIKAUSER_MSG = '''//*[@id="right_menu"]/table[1]
//tr[2]/td/ul/li[5]/a/b'''
XPATH_PIKAUSER_LSMSG = '''//*[@id="com2"]//tr[2]/td/div/noindex/div/input'''


def fetch_url(_url, settings=None,
    _data=None, __method="POST"):
    """Выполняет запрос к сайту и возвращает результат в виде
    страницы
    В зависимости от типа запроса, авторизации и в каком доме находится
    сатурн - выполняет определенный запрос с подстановкой заголовков.

    """
    if len(SITE_REQUEST.cookies) == 0:
        url = AUTH_URL
        login_data = {
          "mode": "login",
          "username": settings.get('login'),
          "password": settings.get('password'),
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

    if _url is not None:
        if _data is not None and len(_data) >= 1:
            _headers = DEFAULT_HEADERS
            _resp = SITE_REQUEST.get(ENDPOINT, headers=DEFAULT_HEADERS)
            XCSRF_TOKEN = lxml.html.document_fromstring(_resp.text).xpath(
                XPATH_XCSRFTOKEN)[0].text.strip()
            XCSRF_TOKEN = XCSRF_TOKEN.split("\n")[2].strip()
            XCSRF_TOKEN = XCSRF_TOKEN.replace("'", "").split(": ")[1]
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
        return resp.text
    else:
        return False


class PikaService:
    """Абстрактный класс"""
    def __init__(self, **settings):
        if "login" not in settings or "password" not in settings:
            raise ValueError('Нужно указать логин и пароль')
        self.settings = settings

    def request(self, url, data=None, method='POST'):
        if url is not None:
            return fetch_url(url, self.settings, data, method)
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
            _page = self.request("generate_xml_comm.php?id=" + post_id)
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


class PikabuProfile(PikaService):
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


    def dor(self):
        """Возвращает дату регистрации юзера"""
        if self._dor is None:
            _page = self.request("profile/" + self.settings.get('login'))
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._dor = page_body.xpath(
                    XPATH_PIKAUSER_DOR)[2].strip()
        else:
            pass
        return self._dor

    def rating(self):
        """Возвращает рейтинг пользователя"""
        if self._rating is None:
            _page = self.request("profile/" + self.settings.get('login'))
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._rating = page_body.xpath(
                    XPATH_PIKAUSER_RATE)[3].strip().split(": ")[1]
        else:
            pass
        return self._rating

    def followers(self):
        """Возвращает количество подписчиков"""
        if self._followers is None:
            _page = self.request("profile/" + self.settings.get('login'))
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
            _page = self.request("profile/" + self.settings.get('login'))
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

    def comments(self):
        """Возвращает количество комментариев"""
        if self._comments is None:
            _page = self.request("profile/" + self.settings.get('login'))
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._comments = page_body.xpath(
                    XPATH_PIKAUSER_COM)[4].strip().split(": ")[1]
        else:
            pass
        return self._comments

    def mynews(self):
        """Возвращает количество новостей и их число в горячем"""
        if len(self._mynews) == 0:
            _page = self.request("profile/" + self.settings.get('login'))
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                pseudo_data = page_body.xpath(
                    XPATH_PIKAUSER_NEWS)[5].strip().split(", ")
                self._mynews.append(int(pseudo_data[0].split(": ")[1]))
                self._mynews.append(int(pseudo_data[1].split(": ")[1]))
        else:
            pass
        return self._mynews

    def actions(self):
        """Возвращает массив с плюсами и минусами юзера"""
        if len(self._actions) == 0:
            _page = self.request("profile/" + self.settings.get('login'))
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._actions.append(int(page_body.xpath(
                    XPATH_PIKAUSER_ACT)[1].strip()[:-7]))
                self._actions.append(int(page_body.xpath(
                    XPATH_PIKAUSER_ACT)[2].strip()[:-8]))
        else:
            pass
        return self._actions

    def awards(self):
        """Возвращает массив с наградами пользователя"""
        if len(self._awards) == 0:
            _page = self.request("profile/" + self.settings.get('login'))
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                for cur_award in page_body.xpath(XPATH_PIKAUSER_AWARDS):
                    self._awards.append(cur_award.get("title"))
            else:
                pass
        else:
            pass
        return self._awards

    def set(self, arg, value):
        pass


class PikabuUserInfo(PikaService):
    """Класс информации о пользователе"""
    def __init__(self, **settings):
        self._rating = None
        self._followers = None
        self._messages = None
        self._dor = None
        self._comments = None
        self._mynews = []
        self._actions = []
        self._awards = []
        self._awards = []
        self.settings = settings

    def get(self, login, params=""):
        """Возвращает информацию о пользователе"""
        if params != "":
            if params == "dor":
                return self.dor(login)
            if params == "rating":
                return self.rating(login)
            if params == "comments":
                return self.comments(login)
            if params == "news":
                return self.news(login)
            if params == "actions":
                return self.actions(login)
            if params == "awards":
                return self.awards(login)
        return ObjectUserInfo(login, self.dor(login),
            self.rating(login), self.comments(login),
            self.news(login), self.actions(login), self.awards(login))

    def dor(self, login):
        """Возвращает дату регистрации пользователя"""
        if self._dor is None:
            _page = self.request("profile/" + login)
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._dor = page_body.xpath(
                    XPATH_PIKAUSER_DOR)[2].strip()
        else:
            pass
        return self._dor

    def rating(self, login):
        """Возвращает рейтинг юзера"""
        if self._rating is None:
            _page = self.request("profile/" + login)
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._rating = page_body.xpath(
                    XPATH_PIKAUSER_RATE)[3].strip().split(": ")[1]
        else:
            pass
        return self._rating

    def comments(self, login):
        """Возвращает количество комментариев юзера"""
        if self._comments is None:
            _page = self.request("profile/" + login)
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._comments = page_body.xpath(
                    XPATH_PIKAUSER_COM)[4].strip().split(": ")[1]
        else:
            pass
        return self._comments

    def news(self, login):
        """Возвращает массив с количеством новостей"""
        if len(self._mynews) == 0:
            _page = self.request("profile/" + login)
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                pseudo_data = page_body.xpath(
                    XPATH_PIKAUSER_NEWS)[5].strip().split(", ")
                self._mynews.append(int(pseudo_data[0].split(": ")[1]))
                self._mynews.append(int(pseudo_data[1].split(": ")[1]))
        else:
            pass
        return self._mynews

    def actions(self, login):
        """Возвращает массив с количество + и - юзера"""
        if len(self._actions) == 0:
            _page = self.request("profile/" + login)
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                self._actions.append(int(page_body.xpath(
                    XPATH_PIKAUSER_ACT)[1].strip()[:-7]))
                self._actions.append(int(page_body.xpath(
                    XPATH_PIKAUSER_ACT)[2].strip()[:-8]))
        else:
            pass
        return self._actions

    def awards(self, login):
        """Возвращает список наград пользователя"""
        if len(self._awards) == 0:
            _page = self.request("profile/" + login)
            if _page is not None:
                page_body = lxml.html.document_fromstring(_page)
                for cur_award in page_body.xpath(XPATH_PIKAUSER_AWARDS):
                    self._awards.append(cur_award.get("title"))
            else:
                pass
        else:
            pass
        return self._awards


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
    def __init__(self, _id, rating, author, time, text, parent=0, post=None):
        self.id = _id
        self.rating = rating
        self.author = author
        self.time = time
        self.text = text
        self.post = post
        self.parent = parent


class ObjectUserInfo():
    """Объект информации о пользователе"""
    def __init__(self, login, dor, rating, comments, news, actions, awards):
        self.login = login
        self.dor = dor
        self.rating = rating
        self.comments = comments
        self.news = news
        self.actions = actions
        self.awards = awards


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
