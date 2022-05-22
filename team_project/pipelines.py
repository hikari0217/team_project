# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from team_project.items import WeiXinItem,SouhuItem,hzItem,qqItem,zjolItem

class TeamProjectPipeline:
    def process_item(self, item, spider):
        if isinstance(item,WeiXinItem):
            # 微信爬虫数据处理
            print('*'*80)
            print('WeiXin_Spider')
            print('*' * 80)
            print(item['Page_Source'])
            print(item['Title'])
            # print(item['Imag_content'])

        elif isinstance(item,SouhuItem):
            # 搜狐爬虫数据处理
            print('*' * 80)
            print('Souhu_Spider')
            print('*' * 80)
            print(item['img_name'])
            # print(item['img_content'])

        elif isinstance(item, hzItem):
            # 杭州爬虫数据处理
            print('*' * 80)
            print('hz_Spider')
            print('*' * 80)
            print(item['img_name'])
            # print(item['img_content'])

        elif isinstance(item, qqItem):
            # QQ爬虫数据处理
            print('*' * 80)
            print('qq_Spider')
            print('*' * 80)
            print(item['img_name'])
            # print(item['img_content'])

        elif isinstance(item, zjolItem):
            # zjol爬虫数据处理
            print('*' * 80)
            print('zjol_Spider')
            print('*' * 80)
            print(item['img_name'])
            # print(item['img_content'])

        return item
