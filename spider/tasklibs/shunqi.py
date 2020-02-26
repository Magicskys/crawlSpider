import threading
from django.conf import settings
import logging
from lxml import etree
from bs4 import BeautifulSoup
import datetime
from spider.utils import utils,city_code,crack_slider_verificationCode

from spider.models import Spider
from crawlSpider.app import app
from queue import Queue
import re

fmt = '%(asctime)s - %(lineno)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
logger = logging.getLogger('shunqi')
logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler("log/shunqi.log", maxBytes = 100*1024*1024, backupCount = 5)
handler.setFormatter(formatter)
logger.addHandler(handler)
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

downQueue=Queue(1000)
thread=40

insertdate = datetime.datetime.now().date()
search_url = 'http://b2b.11467.com/'
# search_url = 'http://www.11467.com'
headers={'Referer':'http://www.11467.com','Accept-Language':'zh-cn','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Encoding':'gzip, deflate'}

request=utils.Direquest()

# def SpiderIndustry():
#     pagehtml = getRsponse(search_url)
#     if pagehtml is False:
#         raise SystemExit("读取分类失败，请检查网络问题")
#     import ipdb
#     ipdb.set_trace()
#     select = BeautifulSoup(pagehtml.content.decode('utf-8'), 'html5lib')
#     infos = select.find_all('div',class_='boxcontent')
#     for info in infos:
#         for i in info.find_all('a',attrs={"rel":"nofollow"}):
#             industry=i.string
#             pagehtml = getRsponse('http:'+i['href'])
#             if pagehtml is False:
#                 raise SystemExit("读取分类详情失败，请检查网络问题")
#             select2 = BeautifulSoup(pagehtml.content.decode('utf-8'), 'html5lib')
#             infos2 = select2.find_all('div',class_='boxcontent')
#             for info2 in infos2:
#                 for i2 in info2.find_all('a'):
#                     industry2 = i2.string
#                     pagehtml = getRsponse('http:' + i2['href'])
#                     if pagehtml is False:
#                         raise SystemExit("读取分类详情失败，请检查网络问题")
#                     select3 = BeautifulSoup(pagehtml.content.decode('utf-8'), 'html5lib')
#                     infos3 = select3.find_all('div', class_='boxcontent')
#                     for info3 in infos3:
#                         for i3 in info3.find_all('a'):
#                             industry3 = i3.string
#                             url='http:'+i['href']
#                             SpiderURL(url,industry,industry2,industry3)
                            # downQueue.put((url,'%s-%s-%s'%(industry,industry2,industry3)))





def SpiderArea():
    pagehtml = getRsponse(search_url)
    if pagehtml is False:
        raise SystemExit("读取地址信息失败，请检查网络问题")
    select=etree.HTML(pagehtml.content.decode('utf-8'))
    citys=select.xpath('//div[@class="box sidesubcat t5"][2]/div[@class="boxcontent"]/dl[@class="listtxt"]')
    citys.reverse()
    for city in citys:
        city_name=city.xpath('dt/text()')[0]
        for i in city.xpath('dd/a'):
            try:
                area=i.xpath('em/text()')[0]
            except:
                area = i.xpath('text()')[0]
            url = i.xpath('@href')[0][2:]
            SpiderIndustry(url,city_name,area)



def SpiderIndustry(url,city_name,area):
    pagehtml = getRsponse('http://' + url)
    if pagehtml is False:
        return
    select = etree.HTML(pagehtml.content.decode('utf-8'))
    for classifi in select.xpath('//div[@id="il"]/div[1]/div[2]/ul[@class="listtxt"]/li/dl/dt'):
        url=classifi.xpath('a/@href')[0]
        industry=classifi.xpath('a/text()')[0].replace('黄页','')
        logger.info('%s %s %s %s'%(city_name,area,industry,url))
        SpiderURL(url,city_name,area,industry)


def getRsponse(url):
    proxyname,pagehtml = request.request(url=url,project_name='shunqi', method='get', headers=headers, timeout=10)
    if pagehtml is False:
        return False
    return pagehtml


def SpiderURL(url,city_name,area,industry):
    listurl=url
    nowpage=settings.RD.get('shunqi_%s_%s_%s'%(city_name,area,industry)).decode('utf-8') if settings.RD.exists('shunqi_%s_%s_%s' % (city_name,area,industry)) else '1'
    k=int(nowpage)
    while 1:
        settings.RD.set('shunqi_%s_%s_%s' % (city_name,area,industry), k)
        if 'search' in listurl:
            listurl = listurl[:-4]+'-%d.htm'%k
        else:
            listurl=listurl[:listurl.index('-p')]+'-p%d.htm'%k if '-p' in listurl else listurl[:-4]+'-p%d.htm'%k
        pagehtml = getRsponse('http:'+listurl)
        if pagehtml is False or pagehtml.status_code==404:
            if pagehtml.status_code == 404 and k>1:
                settings.RD.set('shunqi_%s_%s_%s' % (city_name, area, industry),1)
            continue
        select = etree.HTML(pagehtml.text)
        urllist=select.xpath('//div[@class="f_l"]')
        logger.info("正在爬取 %s %s %s| %s 页/%d 条数据 %s | %d队列"%(city_name,area,industry,k,len(urllist),listurl,downQueue.qsize()))
        if len(urllist)==0:
            settings.RD.set('shunqi_%s_%s_%s'%(city_name,area,industry),k-1 if k>1 else 1)
            break
        for i in urllist:
            info=i.xpath('h4/a')[0]
            corporate_name=info.xpath('@title')[0]
            url = info.xpath('@href')[0]
            if url[:4]!='http':
                url='http:'+url
            downQueue.put((url,city_name,area,corporate_name))

        k+=1
        try:
            lastPage=select.xpath('//div[@class="pages"]/a')[-2]
        except:
            settings.RD.set('shunqi_%s_%s_%s'%(city_name,area,industry),k-1)
            break
        endPage=re.search('(?<=-p)\d+(?=\.htm)',select.xpath('//div[@class="pages"]/a/@href')[-1]).group()
        if int(endPage)<k:
            break
        if lastPage.xpath('text()')[0]=='下一页':
            if k<10:
                url=lastPage.xpath('@href')[0][:-5]+'%d.htm'%k
            else:
                url = lastPage.xpath('@href')[0][:-6] + '%d.htm' % k
        settings.RD.set('shunqi_%s_%s_%s'%(city_name,area,industry),k)


def getPageList():
    while 1:
        try:
            url,city_name,area,corporate_name=downQueue.get(timeout=600)
        except:
            break

        pagehtml = getRsponse(url)
        if pagehtml is False:
            continue
        select = etree.HTML(pagehtml.text)
        contact=select.xpath('//div[@id="contact"]/div/dl[@class="codl"]/dd')
        phones=[]
        try:
            phone1=''.join(contact[1].xpath('text()'))
        except:
            pagehtml = getRsponse(url)
            if pagehtml is False:
                continue
            select = etree.HTML(pagehtml.content.decode('utf-8'))
            try:
                contact = select.xpath('//div[@id="contact"]/div/dl[@class="codl"]/dd')
                phone1 = ''.join(contact[1].xpath('text()'))
            except:
                continue

        if phone1!='未提供':
            phones.append(phone1)
        phone2=''.join(contact[3].xpath('text()'))
        if phone2!='未提供':
            phones.append(phone2)

        if len(phones)==2 and phone1==phone2:
            phones.pop()

        try:
            name=';'.join(contact[2].xpath('text()')).strip()
            address=''.join(contact[0].xpath('text()'))
            email=';'.join(contact[4].xpath('text()'))
            industry=select.xpath('//div[@class="navleft"]/a/text()')[-2][:-2].replace(area,'')
        except:
            continue

        item={}
        item['name'] = name
        item['phone']=';'.join(phones)
        item['email']=email
        item['corporate_name'] = corporate_name
        item['city']=city_name
        item['region']=area
        item['address']=address
        item['url']=url
        item['year']=insertdate.year
        item['personnel_scale']=''
        item['industry']=industry
        item['keyword']=''
        item['datetime']=insertdate
        item['source']='shunqi'
        item['insertdate']=insertdate
        item['source_corporate_name'] = item['source'] + '__' + item['corporate_name']
        try:
            Spider.objects.create(**item)
            # logger.info(item)
        except:
            pass
            # logger.info("存在数据 %s"%corporate_name)

    logging.info("数据库存储组件退出")

@app.taskinsertdate
def main(*args,**kwargs):
    thread=int(kwargs['thread'])

    logger.info("[*] thead %s | DownloadThead %s | DataThread %s" % (kwargs['thread'], kwargs['downloadthread'], kwargs['datathread']))
    logger.info("[*] 开始收集信息")

    threadlist = []

    for t in range(thread):
        t = threading.Thread(target=getPageList, args=())
        threadlist.append(t)

    threadlist.append(threading.Thread(target=SpiderArea,args=()))

    for t in threadlist:
        t.start()

    for t in threadlist:
        t.join()

    logger.info('Waiting for all subprocesses done...')
