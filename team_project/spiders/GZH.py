import scrapy
import json
import time
import redis
import requests
import asyncio
import sava2Hbase
from io import BytesIO
from pyppeteer import launch
from copy import deepcopy
from team_project.items import WeiXinItem
from scrapy_redis.spiders import RedisSpider

# 'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz=MjM5ODMzMDMyMw==&f=json&offset=10&count=10&is_ok=1&scene=124&uin=MTE2Mjg5NjE1Nw%3D%3D&key=&pass_ticket=AKFFJ0qmEBFvaKzTgriRLcfH628eBtWxsycgKS3aKT332xEW2zEwun2GSk%2FOhQXG&wxtoken=&appmsg_token=1166_yH27tA09YfZRk1MVSWKwYtng9sHe9rCRiRuXWg~~&x5=0&f=json'



class GzhSpider(RedisSpider):
    # 三个参数 __biz offset key
    content_url = 'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz={}&offset={}&f=json&uin=MTE2Mjg5NjE1Nw%3D%3D&key={}' # 大号 MjM4MzU3NjU0Mw%3D%3D  小号 MTE2Mjg5NjE1Nw%3D%3D
    NF_key = '3767ee28e6eacb643377f508429adcee8f5bf56fce3bf958bb2bd5cc9cf253589c02d914f152d07ba15ce23adfc6552c5db78b7afaab78373549c6826c48a508214c787747a125b1bb4a923db2312f3c858169d3e50a903f942497945c6b520c5883ed9a86050e6f084ca70cd759d79829b936738e1ce231a4a263b5a3081709'
    RW_KEY = '70329148eedbf977dc7bdfbe1b5f7051c8b331e2f579731988089dba4182b1cc924ebdaa5e0fc5d7c3dfff60258ae5e47fb83e96273d5f8e5529d78a262fce94a81e0eb282906f5c04dab522e5bb53918af6a1bd17153155f40b5b1120abd94a4e217e2f08b9bba2965a86af4742fddb7e97e1526905427d1d9bf5e9d6c8907e'
    XZK_KEY = '5d437e93ba2afc1f5bb4351cb954077a09be420a1742659db93863f7d491af9188c6d7909363176b0dcc3f6a890e087d4e6d439d98c0b25f40f13bd42d81dbe2f0a3e8b8d2159bf7d7a8ddb0ae46e44b13dff1caa4ef95e493cd93b4a1b8c5a16209e0af10588393f27976bb8a05768ad26527bf2a3bc4633892a97852fff63c'
    name = 'GZH'
    allowed_domains = ['weixin.com', 'mp.weixin.qq.com']
    start_urls = [content_url.format('Njk5MTE1', 0, NF_key)]
    # 设置爬取范围
    page_domain = 10

    # 负责截图的函数
    async def screenshot_main(self, url):
        browser = await launch()
        page = await browser.newPage()
        await page.goto(url)
        src = await page.screenshot(fullPage=True)
        await browser.close()
        return src

    def start_requests(self):
        # redis_serve = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
        # redis_serve.lpush('GZH:start_urls', self.content_url.format('Njk5MTE1', 0, self.NF_key))

        # NF翻页处理
        for i in range(self.page_domain):
            next_page = self.content_url.format('Njk5MTE1', str(i * 10), self.NF_key)
            yield scrapy.Request(next_page,callback=self.parse)
        # RW翻页处理
        for i in range(self.page_domain):
            next_page = self.content_url.format('MjEwMzA5NTcyMQ==', str(i * 10), self.RW_KEY)
            yield scrapy.Request(next_page,callback=self.parse)
        # XZK翻页处理
        for i in range(self.page_domain):
            next_page = self.content_url.format('MjM5ODMzMDMyMw==', str(i * 10), self.XZK_KEY)
            yield scrapy.Request(next_page,callback=self.parse)

    # 用于解析列表页
    def parse(self, response):
        # 解析新闻列表
        info_dic = json.loads(response.text)
        try:
            info_list = json.loads(info_dic['general_msg_list'])['list']
        except Exception:
            print('url失效，请重新获取')
        else:
            for info in info_list:
                # 解析第一级列表
                app_msg_ext_info = info['app_msg_ext_info']
                # 标题 (不一样)
                Title = app_msg_ext_info['title']
                # 新闻时间 (一样的)
                timeStamp = info['comm_msg_info']['datetime']
                timeArray = time.localtime(timeStamp)
                news_Time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                # 爬取时间 (一样的)
                curr_Time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
                # 新闻url (不一样)
                info_url = app_msg_ext_info['content_url']

                Item = WeiXinItem(Title=Title, News_Time=news_Time, Curr_Time=curr_Time, Info_url=info_url)
                try:
                    yield scrapy.Request(
                        url=info_url,
                        callback=self.info_parse,
                        meta={'Item': deepcopy(Item)},
                    )
                except Exception:
                    print('*'*80)
                    print('解析新闻页url失败！！！')
                    print(info_url)
                    print('*' * 80)

                # 解析第二级列表
                multi_app_msg_item_list = app_msg_ext_info['multi_app_msg_item_list']
                for muti_msg in multi_app_msg_item_list:
                    # 标题 (不一样)
                    Title = muti_msg['title']
                    # 新闻url
                    info_url = muti_msg['content_url']

                    Item = WeiXinItem(Title=Title, News_Time=news_Time, Curr_Time=curr_Time, Info_url=info_url)
                    # print(Item)
                    yield scrapy.Request(
                        url=info_url,
                        callback=self.info_parse,
                        meta={'Item': deepcopy(Item)},
                    )

    # 新闻内容页解析
    def info_parse(self, response):
        Item = response.meta['Item']
        # HTML
        Item['HTML'] = response.text
        # 新闻来源公众号
        page_source = response.xpath('//a[@class="wx_tap_link js_wx_tap_highlight weui-wa-hotarea"]/text()').get()
        if page_source:
            Item['Page_Source'] = page_source.strip()
        else:
            Item['Page_Source'] = ''
        # 图片url
        Item['Imag_Urls'] = response.xpath('//img/@data-src').getall()

        # 图片保存
        img_content = []
        for img_url in Item['Imag_Urls']:
            res = requests.get(img_url)
            # 转换为字节数组
            if res.status_code == 200:
                res.encoding = 'gbk'
            d = BytesIO(res.content)
            data = []
            while True:
                t = d.read(1)
                if not t:
                    break
                data.append(t)
            data = sava2Hbase.jb2jb(data)
            img_content.append(data)

        # 截图
        screenshot_src = asyncio.get_event_loop().run_until_complete(self.screenshot_main(Item['Info_url']))
        # 转换截图为字节数组
        d = BytesIO(screenshot_src)
        data = []
        while True:
            t = d.read(1)
            if not t:
                break
            data.append(t)
        data = sava2Hbase.jb2jb(data)
        img_content.append(data)

        Item['Imag_content'] = img_content

        yield Item
