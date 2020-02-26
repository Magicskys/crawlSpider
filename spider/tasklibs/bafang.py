import threading
from django.conf import settings
import logging
from lxml import etree
import datetime
from spider.utils import utils,city_code,crack_slider_verificationCode
from spider.models import Spider
from crawlSpider.app import app
from queue import Queue
from multiprocessing import Process
import re
import aiohttp,asyncio

fmt = '%(asctime)s - %(lineno)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
logger = logging.getLogger('wangku')
logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler("log/wangku.log", maxBytes = 100*1024*1024, backupCount = 5)
handler.setFormatter(formatter)
logger.addHandler(handler)
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)


# downQueue=queue.Queue()
downQueue=Queue()
downThread=50

insertdate = datetime.datetime.now().date()
domain_url = 'https://www.b2b168.com'
search_url = 'https://www.b2b168.com/page-company.html'


async def fetch_async():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.b2b168.com') as resp:
            print(resp.status)
            print(await resp.text())
def SpiderIndustry():

    import ipdb
    ipdb.set_trace()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fetch_async())
    loop.close()
    # pagehtml = utils.Direquest(url=search_url,method='get')
    # if pagehtml is False:
    #     raise SystemExit("读取地址信息失败，请检查网络问题")
    # select=etree.HTML(pagehtml.content.decode('utf-8'))
    # for i in select.xpath('//ul[@class="c-hangye"]/li/a/@href'):
    #     url=domain_url+i.xpath('@href')[0]
    #     pagehtml = utils.Direquest(url=url, method='get')
    #     if pagehtml is False:
    #         continue
    #     industryselect = etree.HTML(pagehtml.content.decode('utf-8'))
    #     for industryinfo in industryselect.xpath('//div[@class="mach_list clearfix"]/dl'):
    #         url=domain_url+industryinfo.xpath('dt[1]/a/@href')[0]
    #         industry = industryinfo.xpath('dt[1]/a/@title')[0].replace('黄页','')
            # SpiderURL(url,industry)
            # downQueue.put((url,city_name,region))



# def SpiderURL(url,industry):
#
#     nowpage=settings.RD.get('wangtong_%s_%s'%(city_name,area)).decode('utf-8') if settings.RD.exists('wangtong_%s_%s' % (city_name, area)) else '1'
#     k=int(nowpage)
#     while 1:
#         logger.info("正在爬取 %s %s | %s 页"%(city_name,area,k))
#         pagehtml = utils.Direquest(url=url.rsplit('_')[0]+'_%d'%k, method='get')
#         if pagehtml is False:
#             continue
#         select = etree.HTML(pagehtml.content.decode('utf-8'))
#         urllist = select.xpath('//ul[@class="cony_div"]/li/a/@href')
#         if urllist:
#             continue
#         [downQueue.put((url,city_name,area,nowpage)) for url in urllist]
#
#         threadlist=[]
#         for t in range(downThread):
#             t=threading.Thread(target=getPageList,args=())
#             threadlist.append(t)
#         for t in threadlist:
#             t.start()
#         for t in threadlist:
#             t.join()
#
#         k+=1
#         settings.RD.set('wangtong_%s_%s'%(city_name,area),k)
#         if len(select.xpath('//div[@class="page_list"]'))==0:
#             continue
#         if re.search(r'\"disabled\"\>下一页',pagehtml.content.decode('utf-8')):
#             if int(select.xpath('//div[@class="page_list"]/a/text()')[-1])<=k:
#                 break
#             elif '下一页' in select.xpath('//div[@class="page_list"]/a/text()')[-1]:
#                 continue
#
# def getPageList():
#     while 1:
#         if downQueue.empty():
#             break
#         url,city_name,area,page=downQueue.get()
#         pagehtml = utils.Direquest(url=url+'/ch6', method='get')
#         if pagehtml is False:
#             continue
#         select = etree.HTML(pagehtml.content.decode('utf-8'))
#         phone=';'.join(select.xpath('//span[@class="phoneNumber"]/text()')).strip()
#         try:
#             phone2=select.xpath('//span[@class="addR telephoneShow"]/text()')[0].strip()
#         except:
#             phone2=''
#         if phone2=='暂未填写':
#             phone2=''
#         name=';'.join(select.xpath('//span[@class="name"]/text()')).strip()
#         try:
#             corporate_name=select.xpath('//p[@class="companyname"]/span/a/text()')[0].strip()
#         except:
#             continue
#         address=select.xpath('//span[@class="p_rzR"]/text()')[-1].strip()
#         industry=select.xpath('//span[@class="p_rzR"]/text()')[-2].strip()
#         try:
#             email=select.xpath('//div[@class="addIntroL"]/ul/li/span[@class="addR"]/text()')[-2].strip()
#         except:
#             email=''
#         if industry=='暂未填写':
#             industry=''
#         if email=='暂未填写':
#             email=''
#
#         item={}
#         item['name'] = name
#         item['phone']=phone+';'+phone2 if phone2!='' else phone
#         item['email']=email
#         item['corporate_name'] = corporate_name
#         item['city']=city_name
#         item['region']=address.split(' ')[-1]
#         item['address']=address
#         item['url']=url
#         item['year']=insertdate.year
#         item['personnel_scale']=''
#         item['industry']=industry
#         item['keyword']=''
#         item['datetime']=insertdate
#         item['source']='wangku'
#         item['insertdate']=insertdate
#         item['source_corporate_name'] = item['source'] + '__' + item['corporate_name']
#         # if not Spider.objects.filter(corporate_name=corporate_name,source=item['source']).exists():
#         try:
#             Spider.objects.create(**item)
#             logger.info(item)
#             logger.info("存入一条数据 %s 页"%page)
#         except:
#             logger.info("存在数据 %s"%corporate_name)
#         # else:


@app.task
def main(*args,**kwargs):
    global key
    global downThread

    keyword=args
    key=keyword[0]
    downThread=int(kwargs['downloadthread'])

    logger.info("[*] 开始收集信息")
    # SpiderArea()

    p=Process(target=SpiderIndustry())
    p.start()
    p.join()

    # SpiderURL()

    # logger.info("[*] 开始爬取信息")
    # for i in range(thread):
    #     i = threading.Thread(target=GetPageInfo,args=())
    #     thList.append(i)
    #     i.start()
    #
    # logger.info("开启存入数据库组件")
    #
    # for i in range(DataThread):
    #     p=Process(target=InsertData,args=())
    #     p.start()
    #     thList.append(p)
    #
    # for i in thList:
    #     i.join()
    # logger.info('Waiting for all subprocesses done...')
