import threading
from django.conf import settings
import logging
import datetime
from spider.utils import utils, city_code, crack_slider_verificationCode
from spider.models import Spider
from crawlSpider.app import app
from queue import Queue
from bs4 import BeautifulSoup
import re
from threading import Lock
import time

fmt = '%(asctime)s - %(lineno)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
logger = logging.getLogger('shangwu1024')
logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler("log/shangwu1024.log", maxBytes=100 * 1024 * 1024, backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

downQueue = Queue(1000)
thread = 50
lock = Lock()

insertdate = datetime.datetime.now().date()
domain_url = 'http://www.1024sj.com'
search_url = 'http://www.1024sj.com/com/'

request = utils.Direquest()


def getRsponse(url):
    proxyname, pagehtml = request.request(url=url, project_name='shangwu1024', method='get', timeout=6)
    if pagehtml is False:
        return False
    return pagehtml


def SpiderArea():
    pagehtml = getRsponse(search_url)
    if pagehtml is False:
        raise SystemExit("读取地址信息失败，请检查网络问题")
    select = BeautifulSoup(pagehtml.text, 'html5lib')
    info = select.find_all('table', class_="news_1222")[1]
    info_as = info.find_all('a')
    info_as.reverse()
    for i in info_as:
        url = i.attrs['href']
        city = i.string
        pagehtml = getRsponse(url)
        if pagehtml is False:
            continue
        infoselect = BeautifulSoup(pagehtml.text, 'html5lib')
        if len(infoselect.find_all('table', class_='news_1222')) == 0:
            continue
        for u in infoselect.find_all('table', class_='news_1222')[0].find_all('a'):
            url = u.attrs['href']
            area = u.string.replace('黄页', '')
            pagehtml = getRsponse(url)
            if pagehtml is False:
                continue
            areaselect = BeautifulSoup(pagehtml.text, 'html5lib')
            try:
                areaselect = areaselect.find_all('table', class_='tb_1')[1]
            except:
                continue
            for k in areaselect.find_all('a'):
                url = k.attrs['href']
                industry = k.string.replace('企业名录', '').replace(area, '')
                pagehtml = getRsponse(url)
                if pagehtml is False:
                    continue
                logger.info("%s %s %s" % (city, area, industry))
                SpiderURLs(url, industry, city, area)


def SpiderURLs(url, industry, city, area):
    nowpage = settings.RD.get('shangwu1024_%s_%s_%s' % (city, area, industry)).decode('utf-8') if settings.RD.exists('shangwu1024_%s_%s_%s' % (city, area, industry)) else '1'
    page = int(nowpage)
    pageflat = True
    if page == 1:
        pageurl = url[:-5] + '-%d.html' % page if page != 1 else url
    else:
        pageurl = url.split('-', 2)[0] + '-' + url.split('-', 2)[1] + '-s0-' + url.split('-', 2)[2]
        pageurl = pageurl[:-5] + '-%d.html' % page if page != 1 else url
    while 1:
        if 'http' not in pageurl:
            break
        pagehtml = getRsponse(url)
        if pagehtml is False:
            break
        if pagehtml.url.count('-') < 2:
            break
        select = BeautifulSoup(pagehtml.text, 'html5lib')
        if len(select.find_all('table', class_="basic_14")) == 0:
            continue
        corporate_name = ''
        for i in select.find_all('table', class_="basic_14"):
            info = i.find_all('a')[0]
            if corporate_name == info.string:
                continue
            corporate_name = info.string
            if corporate_name == '上一页':
                pageurl = i.find_all('a')[1].attrs
                if 'disabled' in pageurl:
                    print(pageurl, ' break')
                    pageflat = False
                    break
                pageurl = pageurl['href']
                break
            url = info.attrs['href']
            downQueue.put((url, industry, city, area, corporate_name))
        if pageflat:
            pageurl, page = pageurl.rsplit('-', 1)
            page = page.split('.')[0]
            pageurl = domain_url + '/com/' + pageurl + '-%s.html' % page if page != 1 else pageurl
            logger.info("正在爬取 %s %s %s %s 页/%s 队列 | %s" % (city, area, industry, page, downQueue.qsize(), pageurl))
            settings.RD.set('shangwu1024_%s_%s_%s' % (city, area, industry), page)


def getPage():
    while 1:
        try:
            url, industry, city, area, corporate_name = downQueue.get(timeout=1200)
        except:
            break
        pagehtml = getRsponse(url)
        if pagehtml is False:
            continue
        select = BeautifulSoup(pagehtml.text, 'html5lib')
        try:
            info = select.find_all('table', class_="tb_1 tb_qiye")[1].find_all('td')
        except:
            continue
        try:
            name = info[0].find_all('td')[2].string.strip().replace('联系人：', '')
            phone = info[0].find_all('td')[4].string.strip().replace('电话：', '')
            phone2 = info[0].find_all('td')[7].string.strip().replace('手机：', '')
            email = info[0].find_all('td')[8].string.strip().replace('email：', '')
            address = re.search(r'(?<=地址：).+', info[0].text).group(0).strip()
            personnel_scal = re.search(r'(?<=员工人数：)(.*)\s+</td>', pagehtml.content.decode('gbk')).group(1).strip()
        except:
            continue
        phones = []
        if phone != "":
            phones.append(phone)
        if phone2 != "":
            phones.append(phone2)

        if corporate_name is None:
            continue

        item = {}
        item['name'] = name
        item['phone'] = ';'.join(phones)
        item['email'] = email
        item['corporate_name'] = corporate_name
        item['city'] = city
        item['region'] = area
        item['address'] = address
        item['url'] = url
        item['year'] = insertdate.year
        item['personnel_scale'] = personnel_scal
        item['industry'] = industry
        item['keyword'] = ''
        item['datetime'] = insertdate
        item['source'] = 'shangwu1024'
        item['insertdate'] = insertdate
        item['source_corporate_name'] = item['source'] + '__' + item['corporate_name']
        try:
            Spider.objects.create(**item)
            # logger.info(item)
            logger.info("存入一条数据")
        except:
            logger.info("存在数据 %s" % corporate_name)
    logger.warning("[!]信息抓取组件退出")


@app.task
def main(*args, **kwargs):
    thread = int(kwargs['thread'])
    logger.info("[*] thead %s | DownloadThead %s | DataThread %s" % (kwargs['thread'], kwargs['downloadthread'], kwargs['datathread']))

    tdlist = []

    logger.info("[*] 开始爬取信息")
    for _ in range(thread):
        i = threading.Thread(target=getPage, args=())
        tdlist.append(i)
    for i in tdlist:
        i.start()

    logger.info("[*] 开始收集信息")
    i = threading.Thread(target=SpiderArea, args=())
    i.start()
    tdlist.append(i)

    for i in tdlist:
        i.join()

    logger.info('Waiting for all subprocesses done...')
