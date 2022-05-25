from io import BytesIO
import redis
import requests
import scrapy
from scrapy.linkextractors import LinkExtractor
from team_project.items import hzItem
from bs4 import BeautifulSoup
from scrapy_splash import SplashRequest
import time
from team_project import sava2Hbase
import base64
from scrapy_redis.spiders import RedisSpider
from pyppeteer import launch
import asyncio

start = time.time()


#记录层数
global level
level=1

#当前爬取层数
global now_level
now_level=1

#外链解析中的链接采用键值对存储，链接作为key，层数作为values，可以通过控制values的上限控制其爬取层数
global url_dic
url_dic={}






class HzSpider(RedisSpider):
    name = 'hz'

    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'team_project.middlewares.TeamProjectSpiderMiddleware': 543,
            'scrapy_splash.SplashDeduplicateArgsMiddleware':100,
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

    def start_requests(self):
        url = 'https://www.hangzhou.com.cn/'
        yield scrapy.Request(url, self.parse)
        #截图
        #yield SplashRequest(url, self.pic_save, endpoint='execute', args={'lua_source': script_png, 'images': 0})

    # 负责截图的函数
    async def screenshot_main(self, url):
        browser = await launch()
        page = await browser.newPage()
        await page.goto(url)
        src = await page.screenshot(fullPage=True)
        await browser.close()
        return src

    #保存截图
    # def pic_save(self, response):
    #     global num
    #     num=num+1
    #     #截图命名
    #     fname = 'hangzhouwang'+str(num) +'.png'
    #     with open(fname, 'wb') as f:
    #          f.write(base64.b64decode(response.data['png']))

    def links_return(self, response):
        link = LinkExtractor()
        links = link.extract_links(response)
        return links

    def link_add(self, links):
        global level
        global url_dic
        for link in links:
            key = link.url
            url_dic[key]= level
        level = level + 1
        return url_dic

    def pic_find(self, response):
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        pic_list = soup.find_all('img')
        return pic_list

    def url_edit(self,pic):
        url = pic
        head = 'http'
        if head in url:
            pic = url
        else:
            pic = 'http:' + url
        return pic

    def parse(self, response):
        global level
        global now_level
        global url_dic
        #当前页面图片字节数组列表
        img_content_list=[]
        #当前页面图片src
        img_src_list=[]

        pic_list = self.pic_find(response)

        item = hzItem()
        item['img_name'] = 'hz'
        item['img_url'] = response.url
        item['html'] = response

        for pic in pic_list:
            pic_src = pic['src']

            if pic_src == '':
                continue

            src = self.url_edit(pic_src)
            img_src_list.append(src)

            # 获取图片响应
            try:
                pic_res = requests.get(src,verify=False, headers={'Connection':'close'})
            except Exception:
                print('Error Url:',src)
                continue

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

        links = self.links_return(response)
        url_dic = self.link_add(links)

        # 图片字节数组列表
        item['img_content'] = img_content_list
        # 图片url列表
        item['img_src'] = img_src_list

        yield item

        if (now_level > 0 and level < 4):
            for key, values in url_dic.items():
                url = key
                if (values == now_level):
                    yield scrapy.Request(url, callback=self.parse)
                    #yield SplashRequest(url, self.pic_save, endpoint='execute',args={'lua_source': script_png, 'images': 0})
            now_level = now_level + 1