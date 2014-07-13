# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Blackwave <blackwave-rt@hotmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cookielib
import urllib2, urllib
import json
import lxml.html
from lxml import etree
import sys
import requests

AUTH_URL = 'http://pikabu.ru/ajax/ajax_login.php'
ENDPOINT = "http://pikabu.ru/"
X_Csrf_Token = None
cookie = cookielib.CookieJar()
req = requests.Session()
default_headers = {
	"User-Agent"  : "Mozilla/5.0 (X11; Linux i686 (x86_64)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36",
	"Referer"	  : "http://pikabu.ru/",
	"Host"		  : "pikabu.ru",
	"Origin"	  : "pikabu.ru"
}
#req.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux i686 (x86_64)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36'), ]
#urllib2.install_opener(req)

def fetch_url(_url, settings=None, _data=None, __method="POST"):
	if len(req.cookies) == 0:		
		url 	= AUTH_URL
		__headers	= 	{ 
						'mode'		:	"login",
	                  	'username'	:	settings.get('login'),
	                   	'password'	:	settings.get('password'),
	                   	'remember'	:	0
					}
		resp 		= req.post(url, data=__headers, headers=default_headers)
		response 	= json.loads(resp.text)
		if int(response["logined"]) == 0:
			print 'Неверно указан логин или пароль'
			sys.exit(1)
		if int(response["logined"]) == -1:
			print response['error']
			sys.exit(1)

	if _url is not None:
		if _data != None and len(_data) >= 1:
			_resp = req.get(ENDPOINT, headers=default_headers)
			X_Csrf_Token = lxml.html.document_fromstring(_resp.text).xpath('/html/head/script[3]')[0].text.strip().split("\n")[2].strip().replace("'", "").split(": ")[1]
			_headers = default_headers
			if (__method == "POST"):
				_headers["Content-Type"] = "application/x-www-form-urlencoded"
				_headers["Accept"]	     = "application/json, text/javascript, */*; q=0.01"
				_headers["X-Csrf-Token"] = X_Csrf_Token				
				resp = req.post(ENDPOINT + _url, headers=_headers, data=_data)
			else:
				resp = req.get(ENDPOINT + _url, headers=_headers, params=_data)
		else:
			resp = req.get(ENDPOINT + _url, headers=default_headers)
		return resp.text
	else: return False

class PikaService:
	def __init__(self, **settings):
		if "login" not in settings or "password" not in settings:
			raise ValueError('Нужно указать логин и пароль')
		self.settings = settings

	def request(self, url, data=None, method='POST'):
		if url is not None:
			return fetch_url(url, self.settings, data, method)
		else: return False

class PikabuSearch(PikaService):
	def search_posts(self, query, page=1):
		return self.request('/search/posts/%s?page=%d' % (query, page))

class PikabuPosts(PikaService):
	def get(self, query, page=1):
		_page = self.request('%s?page=%s&twitmode=1' % (query, page))
		if _page is not None:
			posts_list = []	
			try:
				page_body = lxml.html.document_fromstring(json.loads(_page)["html"].replace("<br>", "\\n"))
			except:
				return False			
			for post_id in json.loads(_page)["news_arr"]:				
				post_title  	= page_body.xpath('//*[@id="num_dig3%s"]'%post_id)[0].text
				post_url		= page_body.xpath('//*[@id="num_dig3%s"]'%post_id)[0].get("href")
				post_text		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]'%post_id)[0].text
				post_image  	= page_body.cssselect('table#story_table_%s'%post_id)[0].get("lang")
				try:
					post_desc 	= " ".join(page_body.xpath('//*[@id="textDiv%s"]/text()'%post_id))
				except: post_desc = None
				try:
					post_author 	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[3]'%post_id)[0].text
					post_time 		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[4]'%post_id)[0].text
					post_comments	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[2]'%post_id)[0].text
				except:
					post_author 	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[3]'%post_id)[0].text
					post_time 		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[4]'%post_id)[0].text
					post_comments	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[2]'%post_id)[0].text			
				post_rating 		= page_body.xpath('//*[@id="num_digs%s"]'%post_id)[0].text				
				post_tags			= [result.text for result in page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/span'%post_id)]
				posts_list.append(ObjectPosts(post_id, post_title, post_url, post_text, post_image, post_desc, post_author, post_time, post_comments, post_rating, post_tags))
			return posts_list

	def search(self, query, cur_page=1, in_hot=True, in_pics=True, in_text=True, in_video=True):
		if query is not None:
			if in_hot: added_params = "&hot_search=on"
			if in_pics: added_params += "&pic_search=on"
			if in_text: added_params += "&text_search=on"
			if in_video: added_params += "&video_search=on"
			added_params += "&page=%s"%cur_page
			_page = self.request('search.php?q=%s%s' % (query, added_params))
			posts_list = []
			page_body = lxml.html.document_fromstring(_page)
			for story in page_body.xpath('//*[@id="stories_container"]/table'):
				try:
					post_id 		= int(story.get("attr"))
					post_title  	= page_body.xpath('//*[@id="num_dig3%s"]'%post_id)[0].text
					post_url		= page_body.xpath('//*[@id="num_dig3%s"]'%post_id)[0].get("href")
					post_desc 		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]'%post_id)[0].text
					post_image  	= page_body.cssselect('table#story_table_%s'%post_id)[0].get("lang")
					try:
						post_text 	= " ".join(page_body.xpath('//*[@id="textDiv%s"]/text()'%post_id))
					except: post_text = None
					try:
						post_author 	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[3]'%post_id)[0].text
						post_time 		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[4]'%post_id)[0].text
						post_comments	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[2]'%post_id)[0].text
					except:
						post_author 	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[3]'%post_id)[0].text
						post_time 		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[4]'%post_id)[0].text
						post_comments	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[2]'%post_id)[0].text			
					try:
						post_rating 	= page_body.xpath('//*[@id="num_digs%s"]'%post_id)[0].text
					except:
						post_rating		= None				
					post_tags			= [result.text for result in page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/span'%post_id)]
					posts_list.append(ObjectPosts(post_id, post_title, post_url, post_text, post_image, post_desc, post_author, post_time, post_comments, post_rating, post_tags))					
				except:
					pass
			return posts_list
		else: return False

	def tag(self, tag_name, page=1, category="new"):
		if tag_name and category is not None:
			_page = self.request('tag/%s/%s?page=%s&twitmode=1' % (tag_name, category, page))
			if _page is not None:
				posts_list = []
				try:
					page_body = lxml.html.document_fromstring(json.loads(_page)["html"].replace("<br>", "\\n"))
				except:
					return False
				for post_id in json.loads(_page)["news_arr"]:				
					post_title  	= page_body.xpath('//*[@id="num_dig3%s"]'%post_id)[0].text
					post_url		= page_body.xpath('//*[@id="num_dig3%s"]'%post_id)[0].get("href")
					post_text		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]'%post_id)[0].text
					post_image  	= page_body.cssselect('table#story_table_%s'%post_id)[0].get("lang")
					try:
						post_desc 	= " ".join(page_body.xpath('//*[@id="textDiv%s"]/text()'%post_id))
					except: post_desc = None
					try:
						post_author 	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[3]'%post_id)[0].text
						post_time 		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[4]'%post_id)[0].text
						post_comments	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/a[2]'%post_id)[0].text
					except:
						post_author 	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[3]'%post_id)[0].text
						post_time 		= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[4]'%post_id)[0].text
						post_comments	= page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[2]/span[1]/a[2]'%post_id)[0].text			
					try:
						post_rating 	= page_body.xpath('//*[@id="num_digs%s"]'%post_id)[0].text
					except:
						post_rating		= None		
					post_tags			= [result.text for result in page_body.xpath('//*[@id="story_table_%s"]//tr/td[2]/table[@id="story_main_t"]//tr/td/div[3]/span[1]/span'%post_id)]
					posts_list.append(ObjectPosts(post_id, post_title, post_url, post_text, post_image, post_desc, post_author, post_time, post_comments, post_rating, post_tags))
				return posts_list
			else: return False
		else: return False		




class PikabuComments(PikaService):
	def get(self, post_id, post_url):
		if post_url or post_id is not None:
			_page = self.request("story/" + post_url)
			if _page is not None:
				comment_list = []
				page_body = lxml.html.document_fromstring(_page)
				for cur_comment in page_body.xpath('//*[@class="comm_wrap_counter"]'):
					comment_id		= 	cur_comment.get("id")[3:]
					comment_rating	=	page_body.xpath('//*[@id="%s"]//tr[1]/td/noindex/span'%cur_comment.get("id"))[0].text
					comment_author	=	page_body.xpath('//*[@id="%s"]//tr[1]/td/noindex/a[3]'%cur_comment.get("id"))[0].text
					caret_avatar 	=	False
					if (comment_author == None):
						comment_author	=	page_body.xpath('//*[@id="%s"]//tr[1]/td/noindex/a[4]'%cur_comment.get("id"))[0].text
						caret_avatar	= 	True
					if (caret_avatar):
						comment_time	=	page_body.xpath('//*[@id="%s"]//tr[1]/td/noindex/a[5]'%cur_comment.get("id"))[0].text	
					else:
						comment_time	=	page_body.xpath('//*[@id="%s"]//tr[1]/td/noindex/a[4]'%cur_comment.get("id"))[0].text	
					comment_text	=	page_body.xpath('//*[@id="comment_desc_%s"]'%comment_id)[0].text
					comment_list.append( ObjectComments(comment_id, comment_rating, comment_author, comment_time, comment_text) )
				return comment_list
		else: return False

class PikabuTopTags(PikaService):
	def get(self, limit=10):
		if limit >= 1:
			_page = self.request("html.php?id=ad")
			if _page is not None:
				tag_list 	= {}
				page_body 	= lxml.html.document_fromstring(_page)
				caret 		= []
				for cur_tag in page_body.xpath('//*[@id="story_main_t"]//tr[2]/td/div/a/span'):
					print cur_tag.text
					if (len(caret) <= 1):
						caret.append(cur_tag.text)
					else:
						tag_list[len(tag_list) + 1]	=	caret
						caret       =	[]
						caret.append(cur_tag.text)
				return tag_list
			else: return False
		else: return False

class PikabuProfile(PikaService):
	def __init__(self, **settings):
		self._rating 	= None
		self._followers	= None
		self._messages	= None
		self._dor 		= None
		self._comments 	= None
		self._mynews	= []
		self._actions	= []
		self._awards 	= []
		self.settings 	= settings

	def dor(self):
		if (self._dor == None):
			_page = self.request("profile/" + self.settings.get('login'))
			if _page is not None:
				page_body 	= lxml.html.document_fromstring(_page)
				self._dor 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[2].strip()
		else: pass
		return self._dor

	def rating(self):
		if (self._rating == None):
			_page = self.request("profile/" + self.settings.get('login'))
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				self._rating 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[3].strip().split(": ")[1]
		else: pass
		return self._rating

	def followers(self):
		if (self._followers == None):
			_page = self.request("profile/" + self.settings.get('login'))
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				self._followers = page_body.xpath('//*[@id="subs_num"]')[0].text.strip()
		else: pass
		return self._followers

	def messages(self):
		if (self._messages == None):
			_page = self.request("profile/" + self.settings.get('login'))
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				self._messages 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[3].strip().split(": ")[1]
		else: pass
		return self._messages

	def comments(self):
		if (self._comments == None):
			_page = self.request("profile/" + self.settings.get('login'))
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				self._comments 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[4].strip().split(": ")[1]
		else: pass
		return self._comments

	def mynews(self):
		if (len(self._mynews) == 0):
			_page = self.request("profile/" + self.settings.get('login'))
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				pseudo_data 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[5].strip().split(", ")
				self._mynews.append(int(pseudo_data[0].split(": ")[1]))
				self._mynews.append(int(pseudo_data[1].split(": ")[1]))
		else: pass
		return self._mynews

	def actions(self):
		if (len(self._actions) == 0):
			_page = self.request("profile/" + self.settings.get('login'))
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				self._actions.append(int(page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/div/text()')[1].strip()[:-7]))
				self._actions.append(int(page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/div/text()')[2].strip()[:-8]))
		else: pass
		return self._actions

	def awards(self):
		if (len(self._awards) == 0):
			_page = self.request("profile/" + self.settings.get('login'))
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				for cur_award in page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[3]/div/a/img'):
					self._awards.append(cur_award.get("title"))
			else: pass
		else:pass
		return self._awards

	def set(self, arg, value):
		pass				

class PikabuUserInfo(PikaService):
	def __init__(self, **settings):
		self._rating 	= None
		self._followers	= None
		self._messages	= None
		self._dor 		= None
		self._comments 	= None
		self._mynews	= []
		self._actions	= []
		self._awards 	= []
		self._awards 	= []
		self.settings 	= settings

	def get(self, login, params=""):
		if (params != ""):
			if params == "dor": return self.dor(login)
			if params == "rating": return self.rating(login)
			if params == "comments": return self.comments(login)
			if params == "news": return self.news(login)
			if params == "actions": return self.actions(login)
			if params == "awards": return self.awards(login)
			return ObjectUserInfo(login, self.dor(login), self.rating(login), self.comments(login), self.news(login), self.actions(login), self.awards(login))

	def dor(self, login):
		if (self._dor == None):
			_page = self.request("profile/" + login)
			if _page is not None:
				page_body 	= lxml.html.document_fromstring(_page)
				self._dor 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[2].strip()
		else: pass
		return self._dor

	def rating(self, login):
		if (self._rating == None):
			_page = self.request("profile/" + login)
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				self._rating 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[3].strip().split(": ")[1]
		else: pass
		return self._rating

	def comments(self, login):
		if (self._comments == None):
			_page = self.request("profile/" + login)
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				self._comments 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[4].strip().split(": ")[1]
		else: pass
		return self._comments

	def news(self, login):
		if (len(self._mynews) == 0):
			_page = self.request("profile/" + login)
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				pseudo_data 	= page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/text()')[5].strip().split(", ")
				self._mynews.append(int(pseudo_data[0].split(": ")[1]))
				self._mynews.append(int(pseudo_data[1].split(": ")[1]))
		else: pass
		return self._mynews

	def actions(self, login):
		if (len(self._actions) == 0):
			_page = self.request("profile/" + login)
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				self._actions.append(int(page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/div/text()')[1].strip()[:-7]))
				self._actions.append(int(page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[2]/div/div/text()')[2].strip()[:-8]))
		else: pass
		return self._actions

	def awards(self, login):
		if (len(self._awards) == 0):
			_page = self.request("profile/" + login)
			if _page is not None:
				page_body 		= lxml.html.document_fromstring(_page)
				for cur_award in page_body.xpath('//*[@id="wrap"]/table//tr/td[1]/table[1]//tr/td[2]/div[1]/table//tr/td[3]/div/a/img'):
					self._awards.append(cur_award.get("title"))
			else: pass
		else:pass
		return self._awards

class PikabuSetRating(PikaService):
	def set(self, action, _type, post_id, comment_id=None):		
			if (_type == 1):
				if action: act = "+"
				else: act = "-" 				
				_page = self.request("ajax/dig.php", {"i":post_id, "type":act})
				if _page is not None:
					return _page
				else: return False
			else:
				if comment_id and post_id is not None:
					if action: act = 1
					else: act = 0		
					_page = self.request("dig.php", {'type':"comm", 'i':comment_id, 'story':post_id, 'dir':act}, "GET")
					if _page is not None:
						return _page				
				else: return False


class ObjectPosts():
	def __init__(self, _id, title, url, description, image, text, author, time, comment, rating, tags):
		self.id 			= _id
		self.title 			= title
		self.url   			= url
		self.description	= description
		self.tags 			= None
		self.image 			= image
		self.text 			= text
		self.author			= author
		self.time 			= time
		self.comments 		= comment
		self.rating			= rating
		self.tags 			= tags

	def tags(self, tags):
		self.tags = tags

class ObjectComments():
	def __init__(self, _id, rating, author, time, text):
		self.id 	= _id
		self.rating = rating
		self.author = author
		self.time 	= time
		self.text 	= text

class ObjectUserInfo():
	def __init__(self, login, dor, rating, comments, news, actions, awards):
		self.login 		= login
		self.dor 		= dor
		self.rating 	= rating
		self.comments 	= comments
		self.news 		= news
		self.actions 	= actions
		self.awards 	= awards

class Api:
	def __init__(self, **settings):
		self._settings 	= settings
		self.posts		= PikabuPosts(**self._settings)
		self.comments	= PikabuComments(**self._settings)
		self.top_tags	= PikabuTopTags(**self._settings)
		self.users	= PikabuUserInfo(**self._settings)
		#self.user_posts	= PikabuUserPosts(**self._settings)
		self.profile 	= PikabuProfile(**self._settings)
		self.rate		= PikabuSetRating(**self._settings)
		#self.settings 	= PikabuSettings(**self._settings)


