# -*- coding: utf-8 -*-
import scrapy
from selenium import webdriver
import requests
import http.cookiejar as cookielib
import json
from urllib import parse
import re
import pickle
import os
import datetime
from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuAnswerItem, ZhihuQuestionItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_urls = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,reshipment_settings,comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[*].mark_infos[*].url;data[*].author.follower_count,badge[?(type=best_answerer)].topics&limit={1}&offset={2}&sort_by=default'

    def parse(self, response):
        """
        提取页面中的所有url，并进一步爬取
        如果提取的url是 /question/xxx 就下载之后进入解析函数
        """
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls1 = filter(lambda x: True if x.startswith('https') else False, all_urls)
        for url in all_urls1:
            match_obj = re.match('(.*zhihu.com/question/(\d+))(/|$).*', url)
            if match_obj:
                # 页面提取到question相关的页面，则下载后交由提取函数提取
                request_url = match_obj.group(1)
                # question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_detail)
            else:
                # 如果不是question页面，就进一步跟踪
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_detail(self, response):
        # 处理question页面，从页面中提取quesiont item

        match_obj = re.match('(.*zhihu.com/question/(\d+))(/|$).*', response.url)
        question_id = int(match_obj.group(2))

        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_css('title', 'h1.QuestionHeader-title::text')
        item_loader.add_css('content', '.QuestionHeader-detail') # .QuestionHeader-detail span.RichText::text
        item_loader.add_value('url', response.url)
        item_loader.add_value('zhihu_id', question_id)
        item_loader.add_css('answer_num', '.List-headerText span::text')
        item_loader.add_css('comments_num', '.QuestionHeader-Comment button.Button--plain::text')
        item_loader.add_css('watch_user_num', '.NumberBoard-itemInner strong.NumberBoard-itemValue::attr("title")')
        item_loader.add_css('topics', '.QuestionHeader-topics .Popover div::text')

        question_item = item_loader.load_item()

        yield scrapy.Request(self.start_answer_urls.format(question_id, 3, 0), headers=self.headers, callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        # 处理question的answer
        answer_json = json.loads(response.text)
        is_end = answer_json["paging"]['is_end']
        # totals_answer = answer_json["paging"]['totals']
        next_url = answer_json["paging"]['next']

        # 提取answer的具体字段
        for answer in answer_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['zhihu_id'] = answer['id']
            answer_item['url'] = answer['url']
            answer_item['question_id'] = answer['question']['id']
            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None
            answer_item['content'] = answer['content'] if 'content' in answer else None
            answer_item['parise_num'] = answer['voteup_count']
            answer_item['comments_num'] = answer['comment_count']
            answer_item['update_time'] = answer['updated_time']
            answer_item['create_time'] = answer['created_time']
            answer_item['crawl_time'] = datetime.datetime.now()
            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

    def start_requests(self):
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        self.headers = {
            'Connection': 'keep - alive',
            'User-Agent': user_agent
        }
        zhihu_session = requests.session()
        if os.path.exists('zhihu_cookies.pkl'):
            with open('zhihu_cookies.pkl', 'rb') as f:
                cookies = pickle.load(f)
        else:
            cookies = {}
        if zhihu_session.get(url='https://www.zhihu.com/signin', headers=self.headers, cookies=cookies).url == 'https://www.zhihu.com/signin':
            chromePath = r'G:\PythonWork\ArticleSpider\chromedriver.exe'
            wd = webdriver.Chrome(executable_path=chromePath)
            loginUrl = 'https://www.zhihu.com/signin'
            wd.get(loginUrl)
            wd.find_element_by_xpath(
                '//*[@id="root"]/div/main/div/div/div/div[2]/div[1]/form/div[1]/div[2]/div[1]/input').send_keys(
                '15972126588')
            wd.find_element_by_xpath(
                '//*[@id="root"]/div/main/div/div/div/div[2]/div[1]/form/div[2]/div/div[1]/input').send_keys('wh85864908')
            # 通过url的变化判断是否登陆成功
            while wd.current_url == loginUrl:
                pass
            cookies = wd.get_cookies()
            wd.quit()
            for cookie in cookies:
                zhihu_session.cookies.set(cookie['name'], cookie['value'])
            with open('zhihu_cookies.pkl', 'wb') as f:
                pickle.dump(zhihu_session.cookies, f, 0)
        else:
            print(zhihu_session.get(url='https://www.zhihu.com/signin', headers=self.headers, cookies=cookies).url)

        # yield scrapy.Request(url='https://www.zhihu.com/signin', headers=self.headers, cookies=zhihu_session.cookies.get_dict(), callback=self.check_login)
        return [scrapy.FormRequest('https://www.zhihu.com/signin', headers=self.headers, cookies=zhihu_session.cookies.get_dict(), callback=self.check_login)]


    def check_login(self, response):
        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True, headers=self.headers)

