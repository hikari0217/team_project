from io import BytesIO

import requests
import scrapy
from team_project.items import qqItem
from scrapy.linkextractors import LinkExtractor
from bs4 import BeautifulSoup
from scrapy_splash import SplashRequest
from team_project import sava2Hbase
import time
import base64
from scrapy_redis.spiders import RedisSpider
from pyppeteer import launch
import asyncio

#记录层数
global level
level = 1

#当前爬取层数
global now_level
now_level = 1

#外链解析中的链接采用键值对存储，链接作为key，层数作为values，可以通过控制values的上限控制其爬取层数
global url_dic
url_dic = {}



script = """
                function main(splash, args)
                  splash:go(args.url)
                  local scroll_to = splash:jsfunc("window.scrollTo")
                  scroll_to(0, 2800)
                  splash:set_viewport_full()
                  splash:wait(8)
                  return {html=splash:html()}
                end
                """
#截图脚本
# script_png = """
#                 function main(splash, args)
#                 splash:go(splash.args.url)
#                 splash:set_viewport_size(1500, 10000)
#                 local scroll_to = splash:jsfunc("window.scrollTo")
#                 scroll_to(0, 2800)
#                 splash:wait(8)
#                 return {png=splash:png()}
#                 end
#                 """
class QqSpider(RedisSpider):
    name = 'qq'

    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'team_project.middlewares.TeamProjectSpiderMiddleware': 543,
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'team_project.middlewares.TeamProjectDownloaderMiddleware': 543,
        },
        # Splash配置
        'SPLASH_URL': 'http://localhost:8050',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
    }

    #allowed_domains = ['news.qq.com']
    #start_urls = ['https://www.qq.com/']

    # 负责截图的函数
    async def screenshot_main(self, url):
        browser = await launch()
        page = await browser.newPage()
        await page.goto(url)
        src = await page.screenshot(fullPage=True)
        await browser.close()
        return src

    def start_requests(self):
        url = 'https://www.qq.com/'
        yield SplashRequest(url, self.parse,  endpoint='execute', args={'lua_source': script, 'url': url})
        #yield SplashRequest(url, self.pic_save, endpoint='execute', args={'lua_source': script_png, 'images': 0})


    # def pic_save(self, response):
    #     global num
    #     num = num + 1
    #     fname = 'qq' + str(num) + '.png'
    #     with open(fname, 'wb') as f:
    #          f.write(base64.b64decode(response.data['png']))

    def links_return(self, response):
        global level
        global url_dic
        link = LinkExtractor()
        links = link.extract_links(response)

        return links

    #找到所有img标签
    def pic_find(self,response):
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        pic_list = soup.find_all('img')
        return pic_list

    #加到待爬取列表里
    def link_add(self, links):
        global level
        global url_dic
        for link in links:
            key = link.url
            url_dic[key]= level
        level = level + 1
        return url_dic

    def url_edit(self, pic_src):
        head = 'http'
        if head in pic_src:
            pic_url = pic_src
        else:
            pic_url = 'http:' + pic_src
        return pic_url

    def parse(self, response):
        global level
        global now_level
        global url_dic
        img_content_list=[]
        img_src_list=[]

        pic_list = self.pic_find(response)

        item = qqItem()
        item['img_name'] = 'qq'
        item['img_url'] = response.url
        item['html'] = response

        for pic in pic_list:
            pic_src = pic['src']
            if pic_src == '':
                continue
            src = self.url_edit(pic_src)

            img_src_list.append(src)
            # 获取图片响应
            pic_res = requests.get(src)

            if pic_res.status_code == 200:
                pic_res.encoding = 'gbk'
            d = BytesIO(pic_res.content)
            data = []
            while True:
                t = d.read(1)
                if not t:
                    break
                data.append(t)
            data = sava2Hbase.jb2jb(data)
            img_content_list.append(data)

        # 截图
        screenshot_src = asyncio.get_event_loop().run_until_complete(self.screenshot_main(response.url))
        d = BytesIO(screenshot_src)
        data = []
        while True:
            t = d.read(1)
            if not t:
                break
            data.append(t)
        data = sava2Hbase.jb2jb(data)
        img_content_list.append(data)

        # 图片字节数组列表
        item['img_content'] = img_content_list
        # 图片url列表
        item['img_src'] = img_src_list

        print('*' * 80)
        print('qq_Spider')
        print('*' * 80)
        print(item['img_name'])

        yield item

        # 改变i的值来控制爬取层数
        if (now_level > 0 and level < 4):
            for key, values in url_dic.items():
                url = key
                if (values == now_level):
                    yield SplashRequest(url, self.parse, endpoint='execute', args={'lua_source': script, 'url': url})
                    # yield SplashRequest(url, self.pic_save, endpoint='execute', args={'lua_source': script_png, 'images': 0})
            now_level = now_level + 1