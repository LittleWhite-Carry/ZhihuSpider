# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import re
from urllib import parse
import datetime
from ArticleSpider.items import JobboleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5
from scrapy.loader import ItemLoader

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        """
        1. 获取文章列表页中的文章URL，并交给解析函数进行具体字段的解析。这个解析函数是Scrapy自带的
        2. 获取下一页URL，并交给Scrapy进行下载，下载完成后交给parse
        :param response:
        :return:
        """
        # 解析文章列表页中的文章URL
        post_nodes = response.css('#archive .floated-thumb .post-thumb a')
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            # 用yield交给Scrapy下载
            yield Request(url=parse.urljoin(response.url, post_url), meta={"front_image_url": image_url}, callback=self.parse_detail)

        # 提取下一页，并交给Scrapy下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, post_url), callback=self.parse)  # 用yield交给Scrapy下载

    def parse_detail(self, response):
        # 提取文章的具体字段
        # article_item = JobboleArticleItem()

        '''
        # xpath
        title = response.xpath('//*[@id="post-114159"]/div[1]/h1/text()').extract()[0]
        create_date = response.xpath("//p[@class='entry-meta-hide-on-mobile']/text()").extract()[0].strip().strip().replace("·", "").strip()
        praise_nums = int(response.xpath("//span[contains(@class, 'vote-post-up')]/h10/text()").extract()[0])
        fav_nums = response.xpath("//span[contains(@class, 'bookmark-btn')]/text()").extract()[0]
        match_re = re.match(r".*?(\d+).*", fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0
        comment_nums = response.xpath("//a[@href='#article-comment']/span/text()").extract()[0]
        match_re = re.match(r".*?(\d+).*", comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0
        content = response.xpath("//div[@class='entry']").extract()[0]
        tags_list = response.xpath("//p[@class='entry-meta-hide-on-mobile']/a/text()").extract()
        tags_list = [element for element in tags_list if not element.strip().endswith("评论")]
        tags = '，'.join(tags_list)
        '''

        '''
        # css
        front_image_url = response.meta.get("front_image_url", "") # 封面图，用get不会抛异常
        title = response.css(".entry-header h1::text").extract()[0]
        create_date = response.css("p.entry-meta-hide-on-mobile::text").extract()[0].strip().strip().replace("·", "").strip()
        try:
            create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        praise_nums = int(response.css(".vote-post-up h10::text").extract()[0])
        fav_nums = response.css(".bookmark-btn::text").extract()[0]
        match_re = re.match(r".*?(\d+).*", fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0
        comment_nums = response.css("a[href='#article-comment'] span::text").extract()[0]
        match_re = re.match(r".*?(\d+).*", comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0
        content = response.css("div.entry").extract()[0]
        tags_list = response.css("p.entry-meta-hide-on-mobile a::text").extract()
        tags_list = [element for element in tags_list if not element.strip().endswith("评论")]
        tags = '，'.join(tags_list)

        article_item["url_object_id"] = get_md5(response.url)
        article_item["title"] = title
        article_item["url"] = response.url
        article_item["create_date"] = create_date
        article_item["front_image_url"] = [front_image_url]
        article_item["praise_nums"] = praise_nums
        article_item["comment_nums"] = comment_nums
        article_item["fav_nums"] = fav_nums
        article_item["tags"] = tags
        article_item["content"] = content
        '''

        # Itemloader加载item
        front_image_url = response.meta.get("front_image_url", "")  # 封面图，用get不会抛异常
        item_loader = ArticleItemLoader(item=JobboleArticleItem(), response=response)
        item_loader.add_css('title', ".entry-header h1::text")
        item_loader.add_value('url_object_id', get_md5(response.url))
        item_loader.add_value('url', response.url)
        item_loader.add_css('create_date', "p.entry-meta-hide-on-mobile::text")
        item_loader.add_value('front_image_url', [front_image_url])
        item_loader.add_css('praise_nums', ".vote-post-up h10::text")
        item_loader.add_css('comment_nums', "a[href='#article-comment'] span::text")
        item_loader.add_css('fav_nums', ".bookmark-btn::text")
        item_loader.add_css('tags', "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css('content', "div.entry")

        article_item = item_loader.load_item()

        yield article_item
