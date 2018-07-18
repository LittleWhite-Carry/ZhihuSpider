# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst, Join
import datetime
from scrapy.loader import ItemLoader
import re
from ArticleSpider.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()


def date_convert(value):
    # 获取日期
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()
    return create_date


def get_nums(value):
    # 获取评论数和收藏数
    match_re = re.match(r".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums


def remove_comment_tags(value):
    # 去除tags中的 评论 字样
    if '评论' in value:
        return ''
    else:
        return value


def return_value(value):
    return value


class JobboleArticleItem(scrapy.Item):
    title = scrapy.Field(
        input_processor=MapCompose(return_value)
    )
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert)
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(',')
    )
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into jobbole_article(title, create_date, url, url_object_id, front_image_url, front_image_path, comment_nums, fav_nums, praise_nums, tags, content)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
        params = (self['title'], self['create_date'], self['url'],  self['url_object_id'], self['front_image_url'], self['front_image_path'], self['comment_nums'], self['fav_nums'], self['praise_nums'], self['tags'], self['content'])
        return insert_sql, params

class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题 item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num, 
                      watch_user_num, click_num, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                      ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
                      watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num), crawl_time=VALUES(crawl_time)
                """
        zhihu_id = self['zhihu_id'][0]
        topics = ','.join(self['topics'])
        url = self['url'][0]
        title = self['title'][0]
        content = self['content'][0]
        answer_num = int(self.get('answer_num', ['0'])[0].replace(',', ''))
        comments_num = int(self['comments_num'][0].split(' ')[0]) if self['comments_num'][0] != '添加评论' else 0
        watch_user_num = self['watch_user_num'][0]
        click_num = self['watch_user_num'][1]
        crawl_time = datetime.datetime.now().strftime(SQL_DATE_FORMAT)
        params = (zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, click_num, crawl_time)
        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    # 知乎的回答
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    parise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, praise_num, comments_num,
                     create_time, update_time, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                      ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num),
                      praise_num=VALUES(praise_num), update_time=VALUES(update_time), crawl_time=VALUES(crawl_time)
                """

        zhihu_id = self['zhihu_id']
        url = self['url']
        question_id = self['question_id']
        author_id = self['author_id']
        content = self['content']
        parise_num = self['parise_num']
        comments_num = self['comments_num']
        create_time = datetime.datetime.fromtimestamp(self['create_time']).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self['update_time']).strftime(SQL_DATETIME_FORMAT)
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, url, question_id,  author_id, content, parise_num, comments_num, create_time, update_time, crawl_time)
        return insert_sql, params
