# from scrapy.utils.project import get_project_settings
# from scrapy.crawler import CrawlerProcess
#
# # def main():
# #     setting = get_project_settings()
# #     process = CrawlerProcess(setting)
# #     didntWorkSpider = ['souhu', 'qq', 'zjol', 'hz']
# #
# #     for spider_name in process.spider_loader.list():
# #         if spider_name in didntWorkSpider :
# #             continue
# #         print("Running spider %s" % (spider_name))
# #         process.crawl(spider_name)
# #     process.start()
# #
# # main()
#
# setting = get_project_settings()
# process = CrawlerProcess(setting)
#
# # process.crawl('GZH')
# # process.crawl('souhu')
# # process.crawl('zjol')
# # process.crawl('qq')
# process.crawl('hz')
#
# process.start()

from scrapy import cmdline
cmdline.execute('scrapy crawl hz'.split())