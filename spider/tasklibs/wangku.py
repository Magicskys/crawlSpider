import threading
from django.conf import settings
import logging
from lxml import etree
import datetime
from spider.utils import utils, city_code, crack_slider_verificationCode
from spider.models import Spider
from crawlSpider.app import app
from queue import Queue
import re
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager

fmt = '%(asctime)s - %(lineno)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
logger = logging.getLogger('wangku')
logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler("log/wangku.log", maxBytes=100 * 1024 * 1024, backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

downQueue = Queue(2000)
# thread=50

insertdate = datetime.datetime.now().date()
search_url = 'http://shop.99114.com/'

request = utils.Direquest2()


def SpiderArea(que):
    proxyname, pagehtml = request.request(url=search_url, project_name='wangku', method='get')
    if pagehtml is False:
        raise SystemExit("读取地址信息失败，请检查网络问题")

    select = etree.HTML(pagehtml.content.decode('utf-8'))
    for city in select.xpath('//div[@class="quer_div"]/table/tr'):
        city_name = city.xpath('td/strong/text()')[0]
        for i in city.xpath('td/a'):
            if len(i.xpath('text()')) == 0:
                continue
            area = i.xpath('text()')[0]
            url = i.xpath('@href')[0]
            SpiderURL(url, city_name, area, que)
            # downQueue.put((url,city_name,region))


def SpiderURL(url, city_name, area, que):
    nowpage = settings.RD.get('wangtong_%s_%s' % (city_name, area)).decode('utf-8') if settings.RD.exists('wangtong_%s_%s' % (city_name, area)) else '1'
    k = int(nowpage)
    while 1:
        proxyname, pagehtml = request.request(url=url.rsplit('_')[0] + '_%d' % k, method='get', project_name='wangku')
        if pagehtml is False:
            continue
        select = etree.HTML(pagehtml.content.decode('utf-8'))
        urllist = select.xpath('//ul[@class="cony_div"]/li/a/@href')
        if len(urllist) == 0:
            break
        logger.info("正在爬取 %s %s | %s 页 %s | %s条数据 | %d队列" % (city_name, area, k, url.rsplit('_')[0] + '_%d' % k, len(urllist), downQueue.qsize()))
        # [downQueue.put((url,city_name,area,nowpage)) for url in urllist]
        [que.put((url, city_name, area, nowpage)) for url in urllist]

        k += 1
        settings.RD.set('wangtong_%s_%s' % (city_name, area), k)
        if len(select.xpath('//div[@class="page_list"]')) == 0:
            break
        if re.search(r'\"disabled\"\>下一页', pagehtml.content.decode('utf-8')):
            if int(select.xpath('//div[@class="page_list"]/a/text()')[-1]) <= k:
                break
            elif '下一页' in select.xpath('//div[@class="page_list"]/a/text()')[-1]:
                continue


def getPageList(que):
    while 1:
        try:
            # url,city_name,area,page=downQueue.get(timeout=3600)
            url, city_name, area, page = que.get(timeout=3600)
        except:
            break
        proxyname, pagehtml = request.request(url=url + '/ch6', method='get', project_name='wangku')
        if pagehtml is False:
            continue
        select = etree.HTML(pagehtml.content.decode('utf-8'))
        phone = ';'.join(select.xpath('//span[@class="phoneNumber"]/text()')).strip()
        try:
            phone2 = select.xpath('//span[@class="addR telephoneShow"]/text()')[0].strip()
        except:
            phone2 = ''
        if phone2 == '暂未填写':
            phone2 = ''
        name = ';'.join(select.xpath('//span[@class="name"]/text()')).strip()
        try:
            corporate_name = select.xpath('//p[@class="companyname"]/span/a/text()')[0].strip()
            address = select.xpath('//span[@class="p_rzR"]/text()')[-1].strip()
            industry = select.xpath('//span[@class="p_rzR"]/text()')[-2].strip()
        except:
            continue
        try:
            email = select.xpath('//div[@class="addIntroL"]/ul/li/span[@class="addR"]/text()')[-2].strip()
        except:
            email = ''
        if industry == '暂未填写':
            industry = ''
        if email == '暂未填写':
            email = ''

        item = {}
        item['name'] = name
        item['phone'] = phone + ';' + phone2 if phone2 != '' else phone
        item['email'] = email
        item['corporate_name'] = corporate_name
        item['city'] = city_name
        item['region'] = address.split(' ')[-1]
        item['address'] = address
        item['url'] = url
        item['year'] = insertdate.year
        item['personnel_scale'] = ''
        item['industry'] = industry
        item['keyword'] = ''
        item['datetime'] = insertdate
        item['source'] = 'wangku'
        item['insertdate'] = insertdate
        item['source_corporate_name'] = item['source'] + '__' + item['corporate_name']
        try:
            Spider.objects.create(**item)
            # logger.info(item)
            logger.info("存入一条数据 %s 页/%d 队列" % (page, downQueue.qsize()))
        except:
            logger.info("存在数据 %s/%d 队列" % (corporate_name, downQueue.qsize()))
    logger.info("[!] 数据爬取组件退出！")


def Spideraction(*args, **kwargs):
    print(args, kwargs)
    i, que = args[0]
    if i == 'Down':
        SpiderArea(que)
    elif i == 'Spider':
        getPageList(que)
    else:
        pass


@app.task
def main(*args, **kwargs):
    thread = int(kwargs['thread'])
    listQue = Queue()
    threadlist = [('Down', listQue)]
    threadlist.extend([('Spider', listQue) for i in range(thread - 1)])
    # for t in range(thread):
    #     t=threading.Thread(target=getPageList,args=())
    #     threadlist.append(t)
    # for t in threadlist:
    #     t.start()

    logger.info("[*] 开始收集信息")
    # i=threading.Thread(target=SpiderArea(),args=())
    # i.start()
    # threadlist.append(i)

    # logger.info("开始...")
    # for t in threadlist:
    #     t.join()
    logger.info("[*] 开始爬取信息")
    with ProcessPoolExecutor(max_workers=5) as executer:
        res = executer.map(Spideraction, threadlist)

    # i.join()

    logger.info('Waiting for all subprocesses done...')
