from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from django.conf import settings
import time
import logging
from lxml import etree
import threading
import datetime
from spider.utils import utils, city_code, crack_slider_verificationCode
from ast import literal_eval
from spider.models import Spider
from queue import Empty
from threading import RLock
from crawlSpider.app import app
from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Process, Queue as MQueue, Manager, Value
from multiprocessing.managers import BaseManager
import sys
import json
import requests.packages as packages

packages.urllib3.disable_warnings()

fmt = '%(asctime)s - %(lineno)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
logger = logging.getLogger('tianyancha')
logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler("log/tianyancha.log", maxBytes=100 * 1024 * 1024, backupCount=5)
handler.setFormatter(formatter)
logger.addHandler(handler)
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

thread = 30
DownloadThread = 3

insertdate = datetime.datetime.now().date()
# 关键字
key = '咨询'
# VIP账号
listinfouser = [('', ''), ('', '')]
# 普通账号
spideruser = [('', ''), ('', ''), ('', ''), ('', '')]

# 普通账号
downusername = ''
downpassword = ''

Downcookies = {}
login_url = 'https://www.tianyancha.com/login'
search_url = 'https://www.tianyancha.com/search/ola4/p{page}?key={key}&base=bj&areaCode=110105'

headers = {'Referer': 'https://www.tianyancha.com', 'Connection': 'close'}

request = utils.Direquest2()


class CookieManager(BaseManager):
    pass


def ManagerCookie():
    m = CookieManager()
    m.start()
    return m


CookieManager.register('CookiePool', utils.CookiePool)


def getRsponse(url, clname='', *args, **kwargs):
    proxyname, pagehtml = request.request(url=url, project_name='tianyancha', verify=False, *args, **kwargs)
    if pagehtml is False:
        return False
    return pagehtml


def get_browser(browsermod=True, stat=True):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    if browsermod and stat:
        if settings.OSX == 'linux':
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36"')
            browser = webdriver.Chrome(settings.CHROME_DRIVER, chrome_options=options)
            browser.maximize_window()
            return browser
    elif browsermod is True and stat is False:
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(
            'user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36"')
        browser = webdriver.Chrome(settings.CHROME_DRIVER, chrome_options=options)
        browser.maximize_window()
        return browser
    return webdriver.Chrome(settings.CHROME_DRIVER)


def crack_code(browser, username, password):
    k = 0
    while k < 3:
        cracker = crack_slider_verificationCode.IndustryAndCommerceGeetestCrack(browser)
        cracker.crack()
        if 'gt_popup_wrap' not in browser.page_source:
            break
        else:
            k += 1
            if browser.find_element_by_class_name('gt_info_type').text == '出现错误:':
                browser.get(login_url)
                browser.execute_script('changeCurrent(1);')
                usernameElement = browser.find_element_by_xpath(
                    '//div[@class="module module1 module2 loginmodule collapse in"]/div[@class="modulein modulein1 mobile_box  f-base collapse in"]/div[@class="pb30 position-rel"]/input')
                usernameElement.send_keys(username)
                passwordElement = browser.find_element_by_xpath(
                    '//div[@class="module module1 module2 loginmodule collapse in"]/div[@class="modulein modulein1 mobile_box  f-base collapse in"]/div[@class="input-warp -block"]/input')
                passwordElement.send_keys(password)
                browser.execute_script('loginByPhone(event);')
                time.sleep(2)
                cracker = crack_slider_verificationCode.IndustryAndCommerceGeetestCrack(browser)
                cracker.crack()
            else:
                browser.find_element_by_class_name('gt_refresh_button').click()
                time.sleep(4)
                cracker = crack_slider_verificationCode.IndustryAndCommerceGeetestCrack(browser)
                cracker.crack()


def get_cookie(cookiepool, mod='manual', browsermod=True, user='Spider'):
    global Downcookies
    global downusername
    global downpassword
    global listinfouser

    cookuser = None
    if user == 'Spider':
        cookuser = spideruser
    elif user == 'List':
        cookuser = listinfouser
    elif user == 'Down':
        cookuser = [(downusername, downpassword)]
    for username, password in cookuser:
        browser = get_browser(browsermod)
        browser.get(login_url)
        time.sleep(3)
        browser.execute_script('changeCurrent(1);')
        usernameElement = browser.find_element_by_xpath(
            '//div[@class="module module1 module2 loginmodule collapse in"]/div[@class="modulein modulein1 mobile_box  f-base collapse in"]/div[@class="pb30 position-rel"]/input')
        passwordElement = browser.find_element_by_xpath(
            '//div[@class="module module1 module2 loginmodule collapse in"]/div[@class="modulein modulein1 mobile_box  f-base collapse in"]/div[@class="input-warp -block"]/input')
        usernameElement.send_keys(username)
        passwordElement.send_keys(password)
        browser.execute_script('loginByPhone(event);')
        if mod == 'auto':
            time.sleep(3)
            crack_code(browser, username, password)
        elif browsermod is False:
            input("请手动输入回车")
        else:
            time.sleep(5)
        browser.get(search_url.format(page=1, key=key))
        time.sleep(2)
        select = etree.HTML(browser.page_source)
        pages = select.xpath('//ul[@class="pagination"]/li/a/text()')
        if 'captcha/verify' in browser.current_url:
            if browsermod:
                skip_click_verification(browser, username)
            else:
                logger.info("请输入任意文字并回车")
                input()
            browser.get(search_url.format(page=1, key=key))
            time.sleep(2)
            select = etree.HTML(browser.page_source)
            pages = select.xpath('//ul[@class="pagination"]/li/a/text()')
        try:
            if pages[-1] == ">":
                pages = pages[-2].replace('.', '')
            else:
                pages = pages[-1]
        except:
            pages = 2
        c = browser.get_cookies()
        browser.quit()
        if user != 'Down':
            cookiepool.setCookie(name=user, key=username, value=json.dumps(c), ex=604700)
        else:
            settings.RD.set('tianyanchaDownCookie', json.dumps(c), ex=604800)
            Downcookies = utils.getCookieDict(c)
    # return int(pages)


def getAllPages(url, cookiepool, user='Spider'):
    global Downcookies
    c = []
    if user == 'Spider':
        url = 'https://www.tianyancha.com/company/3307130126'
        for key, value in cookiepool.getCookieDictName('Spider').items():
            cookies = utils.getCookieDict(json.loads(value))
            c.append((key, cookies))
    elif user == 'List':
        for key, value in cookiepool.getCookieDictName('List').items():
            cookies = utils.getCookieDict(json.loads(value))
            c.append((key, cookies))
    elif user == 'Down':
        cookie = json.loads(settings.RD.get('tianyanchaDownCookie'))
        Downcookies = utils.getCookieDict(cookie)
        c.append(('tianyanchaDownCookie', Downcookies))
    else:
        raise SystemExit("未找到该用户组")
    for cook_name, cook in c:
        html = getRsponse(url, cookies=cook, method='get', headers=headers, clname=sys._getframe().f_code.co_name)
        if isinstance(html, bool):
            raise SystemExit("未找到页面")
        html = verification_url(html, cook_name, cook, user, cookiepool=cookiepool)
        select = etree.HTML(html.content.decode('utf-8'))
        pages = select.xpath('//ul[@class="pagination"]/li/a/text()')
        pagecount = select.xpath('//span[@class="tips-num"]')
        if user == 'Spider':
            info = select.xpath('//div[@class="content"]')[0]
            corporate_name = info.xpath('//div[@class="header"]/h1[@class="name"]/text()')
            if len(corporate_name) == 0:
                raise SystemExit("账号 %s %s 可能被封" % (user, cook_name))
        elif len(pages) == 0 and len(pagecount) == 0:
            raise SystemExit("账号 %s %s 可能被封" % (user, cook_name))


def get_count_page_infos(url, browser):
    browser.get(url)
    cookie = json.loads(settings.RD.get('tianyanchaDownCookie'))
    for i in cookie:
        browser.add_cookie(i)
    x = True
    browser2 = object
    while 1:
        browser.get(url)
        if 'captcha/verify' in browser.current_url:
            browser2 = get_browser(True)
            x = False
            browser2.get(browser.current_url)
            for i in cookie:
                browser2.add_cookie(i)
            browser2.get(browser.current_url)
            skip_click_verification(browser2, downusername, 'Down')
        elif x is False:
            browser2.quit()
            break
        else:
            break
    try:
        infosCount = int(browser.find_element_by_xpath('//span[@class="tips-num"]').text.replace('+', ''))
    except:
        return None
    if infosCount > 5000:
        return False
    return True


def get_all_code():
    allCode = []
    for i, citys in city_code.city_code.items():
        for j, city in citys.items():
            if len(city) == 0:
                allCode.append({"base": j})
            else:
                for k, areas in city.items():
                    for l, area in areas.items():
                        allCode.append({"base": j, "code": area, 'city': k, 'region': l})
    return allCode


# status
#    1 industry codeDict
#    2 industry capital codeDict
#    3 industry capital establish codeDict
#    4 industry capital establish codeDict la
def SpiderURL(filterQue):
    flag = False
    browser = get_browser(True, False)
    allCode = get_all_code()
    industryCode = city_code.industry_code
    for codeDict in allCode:
        # if codeDict['city'] in ['天津市', '重庆市']:
        #     continue

        if settings.RD.exists('tianyancha_%s_%s_Region_over' % (codeDict['city'], codeDict['code'] if 'code' in codeDict else codeDict['base'])):
            logger.info("[*] Down 跳过 %s %s" % (codeDict['city'], codeDict['code'] if 'code' in codeDict else codeDict['base']))
            continue

        for industry, industry_code in industryCode.items():
            if settings.RD.exists(
                    'tianyancha_%s_%s_%s_%s_%s_over' % (codeDict['city'], list(industry_code.keys())[0], None, None, codeDict['code'] if 'code' in codeDict else codeDict['base'])):
                logger.info("[*] Down跳过 %s " % industry + 'tianyancha_%s_%s_%s_%s_%s_over' % (
                    codeDict['city'], list(industry_code.keys())[0], None, None, codeDict['code'] if 'code' in codeDict else codeDict['base']))
                flag = False
                continue
            if flag:
                logger.info("Down 休眠 11 秒")
                time.sleep(11)
            url = 'https://www.tianyancha.com/search/{industry}-la4/p{page}?key={key}&base={base}&areaCode={code}'.format(key=key, page=1, industry=list(industry_code.keys())[0],
                                                                                                                          base=codeDict['base'], code=codeDict['code'])
            pgcount = get_count_page_infos(url, browser)
            logger.info("[*] Down %s %s %s %s" % (codeDict['city'], codeDict['region'], industry, pgcount))
            if pgcount is None:
                flag = False
                continue
            elif pgcount:
                flag = True
                filterQue.put(
                    {"status": 1, "industry": industry, "industry_code": list(industry_code.keys())[0], "codeDict": codeDict, 'la': 'la4', 'capital': None, 'establish': None})
                continue
            for indu, indu_code in industry_code[list(industry_code.keys())[0]].items():
                if settings.RD.exists('tianyancha_%s_%s_%s_%s_%s_over' % (codeDict['city'], indu_code, None, None, codeDict['code'] if 'code' in codeDict else codeDict['base'])):
                    logger.info("[*] Down跳过 %s " % industry + 'tianyancha_%s_%s_%s_%s_%s_over' % (
                        codeDict['city'], indu_code, None, None, codeDict['code'] if 'code' in codeDict else codeDict['base']))
                    flag = False
                    continue
                if flag:
                    logger.info("Down 休眠 15 秒")
                    time.sleep(15)
                url = 'https://www.tianyancha.com/search/{industry}-la4/p{page}?searchType=company&key={key}&base={base}&areaCode={code}'.format(key=key, page=1, industry=indu_code,
                                                                                                                                                 base=codeDict['base'], code=codeDict['code'])
                pgcount = get_count_page_infos(url, browser)
                if pgcount is None:
                    continue
                elif pgcount:
                    flag = True
                    filterQue.put({"status": 1, "industry": indu, "industry_code": indu_code, "codeDict": codeDict, 'la': 'la4', 'capital': None, 'establish': None})
                    continue
                for capital in ['r0100', 'r100200', 'r200500', 'r5001000', 'r1000']:
                    if settings.RD.exists(
                            'tianyancha_%s_%s_%s_%s_%s_over' % (codeDict['city'], indu_code, capital, None, codeDict['code'] if 'code' in codeDict else codeDict['base'])):
                        logger.info("[*] Down跳过 %s " % industry + 'tianyancha_%s_%s_%s_%s_%s_over' % (
                            codeDict['city'], indu_code, capital, None, codeDict['code'] if 'code' in codeDict else codeDict['base']))
                        flag = False
                        continue
                    if flag:
                        logger.info("Down 休眠 61 秒")
                        time.sleep(61)
                    url = 'https://www.tianyancha.com/search/{industry}-{capital}-la4/p{page}?searchType=company&key={key}&base={base}&areaCode={code}'.format(key=key, page=1, industry=indu_code,
                                                                                                                                                               capital=capital, base=codeDict['base'],
                                                                                                                                                               code=codeDict['code'])
                    pgcount = get_count_page_infos(url, browser)
                    if pgcount is None:
                        continue
                    elif pgcount:
                        flag = True
                        filterQue.put({"status": 2, "industry": indu, "industry_code": indu_code, 'capital': capital, "codeDict": codeDict, 'la': 'la4', 'establish': None})
                        continue
                    for establish in ['e01', 'e015', 'e510', 'e1015', 'e15']:
                        if flag:
                            logger.info("Down 休眠 21 秒")
                            time.sleep(21)
                        url = 'https://www.tianyancha.com/search/{industry}-{capital}-{establish}-la4/p{page}?searchType=company&key={key}&base={base}'.format(capital=capital, establish=establish,
                                                                                                                                                               key=key, page=1, industry=indu_code,
                                                                                                                                                               base=codeDict['base'])
                        pgcount = get_count_page_infos(url, browser)
                        if pgcount is None:
                            continue
                        elif pgcount:
                            for la in ['la3', 'la4']:
                                if la == "la4":
                                    if settings.RD.exists('tianyancha_%s_%s_%s_%s_%s_over' % (
                                            codeDict['city'], indu_code, capital, establish, codeDict['code'] if 'code' in codeDict else codeDict['base'])):
                                        logger.info("[*] Down跳过 %s " % industry + 'tianyancha_%s_%s_%s_%s_%s_over' % (
                                            codeDict['city'], indu_code, capital, establish, codeDict['code'] if 'code' in codeDict else codeDict['base']))
                                        flag = False
                                        continue
                                else:
                                    if settings.RD.exists('tianyancha_%s_%s_%s_%s_%s_%s_over' % (
                                            codeDict['city'], indu_code, capital, establish, codeDict['code'] if 'code' in codeDict else codeDict['base'], la)):
                                        logger.info("[*] Down跳过 %s " % industry + 'tianyancha_%s_%s_%s_%s_%s_%s_over' % (
                                            codeDict['city'], indu_code, capital, establish, codeDict['code'] if 'code' in codeDict else codeDict['base'], la))
                                        flag = False
                                        continue
                                filterQue.put(
                                    {"status": 4, "capital": capital, "industry": indu, 'industry_code': indu_code, 'establish': establish, "codeDict": codeDict, 'la': la})
                        else:
                            if settings.RD.exists('tianyancha_%s_%s_%s_%s_%s_over' % (
                                    codeDict['city'], indu_code, capital, establish, codeDict['code'] if 'code' in codeDict else codeDict['base'])):
                                logger.info("[*] Down跳过 %s " % industry + 'tianyancha_%s_%s_%s_%s_%s_over' % (
                                    codeDict['city'], indu_code, capital, establish, codeDict['code'] if 'code' in codeDict else codeDict['base']))
                                flag = False
                                continue
                            filterQue.put(
                                {"status": 3, "capital": capital, "industry": indu, 'industry_code': indu_code, 'establish': establish, "codeDict": codeDict, 'la': 'la4'})
        settings.RD.set('tianyancha_%s_%s_Region_over' % (codeDict['city'], codeDict['code'] if 'code' in codeDict else codeDict['base']), 1, ex=345600)


def getFilterurl(infoDict, codeDict, page=1):
    filterurl = ''
    if infoDict['status'] == 1:
        filterurl = 'https://www.tianyancha.com/search/{industry}-la4/p{page}?key={key}&base={base}&areaCode={code}'.format(
            key=key, page=page, industry=infoDict['industry_code'], base=codeDict['base'], code=codeDict['code'])
    elif infoDict['status'] == 2:
        filterurl = 'https://www.tianyancha.com/search/{industry}-{capital}-la4/p{page}?key={key}&base={base}&areaCode={code}'.format(
            key=key, page=page, industry=infoDict['industry_code'], capital=infoDict['capital'], base=codeDict['base'],
            code=codeDict['code'])
    elif infoDict['status'] == 3:
        filterurl = 'https://www.tianyancha.com/search/{industry}-{capital}-{establish}-la4/p{page}?key={key}&base={base}'.format(
            capital=infoDict['capital'], establish=infoDict['establish'], key=key, page=page,
            industry=infoDict['industry_code'], base=codeDict['base'])
    elif infoDict['status'] == 4:
        filterurl = 'https://www.tianyancha.com/search/{industry}-{capital}-{establish}-{la}/p{page}?key={key}&base={base}'.format(
            capital=infoDict['capital'], establish=infoDict['establish'], key=key, page=page,
            industry=infoDict['industry_code'], base=codeDict['base'], la=infoDict['la'])
    print(filterurl)
    return filterurl


def SpiderThreadPages(clname, filterQue, listQue, listinfolock, cookiepool, ThreadFlag):
    global key
    while 1:
        try:
            infoDict = filterQue.get(timeout=1800)
        except Empty as e:
            logger.info("[!]DownloadThead 队列超时，退出")
            break
        codeDict = infoDict['codeDict']
        filterurl = getFilterurl(infoDict, codeDict)

        city = codeDict['city']
        if 'code' in codeDict:
            code = codeDict['code']
        else:
            code = codeDict['base']

        cook_name, cook = cookiepool.getCookie(clname=clname, di=True)
        if isinstance(cook, bool):
            raise SystemExit("未找到Cookie")
        with listinfolock:
            pagehtml = getRsponse(filterurl, cookies=cook, method='get', headers=headers, clname=sys._getframe().f_code.co_name)
            if pagehtml is False:
                continue
            pagehtml = verification_url(pagehtml, cook_name, cook, clname, cookiepool=cookiepool)
            judge_login_url(pagehtml, user=clname, cookiepool=cookiepool)

        select = etree.HTML(pagehtml.content.decode('utf-8'))
        pages = select.xpath('//ul[@class="pagination"]/li/a/text()')
        if len(pages) == 0:
            pages = 2
        elif pages[-1] == ">":
            pages = int(pages[-2].replace('.', ''))
        else:
            pages = int(pages[-1])

        if infoDict['la'] == 'la3':
            pages = int(pages / 2)
            firstPage = int(settings.RD.get(
                'tianyancha_%s_%s_%s_%s_%s_%s' % (city, infoDict['industry_code'], infoDict['capital'], infoDict['establish'], code, infoDict['la']))) if settings.RD.exists(
                'tianyancha_%s_%s_%s_%s_%s_%s' % (city, infoDict['industry_code'], infoDict['capital'], infoDict['establish'], code, infoDict['la'])) else 1
        else:
            firstPage = int(
                settings.RD.get('tianyancha_%s_%s_%s_%s_%s' % (city, infoDict['industry_code'], infoDict['capital'], infoDict['establish'], code))) if settings.RD.exists(
                'tianyancha_%s_%s_%s_%s_%s' % (city, infoDict['industry_code'], infoDict['capital'], infoDict['establish'], code)) else 1
        infosCount = select.xpath('//span[@class="tips-num"]/text()')
        # for page in range(1,2):
        if len(infosCount) == 0:
            logger.info("[*] 爬取%s 省份 %s | %s 行业 %s 地区 注册资本%s 注册时间%s %s 页 | 关键字 %s 数据总数%s" % (
                city, codeDict['region'], infoDict['industry'], code, infoDict['capital'], infoDict['establish'], firstPage, key, 0))
            continue
        else:
            logger.info("[*] 爬取%s 省份 %s | %s 行业 %s 地区 注册资本%s 注册时间%s %s 页 | 关键字 %s %s 数据总数" % (
                city, codeDict['region'], infoDict['industry'], code, infoDict['capital'], infoDict['establish'], firstPage, key, infosCount))

        for page in range(firstPage, int(pages)):
            logger.info("[*] 正在抓取第%d / %d 页 | %s 条数据" % (page, pages, infosCount))
            cook_name, cook = cookiepool.getCookie(clname, di=True)
            if isinstance(cook, bool):
                raise SystemExit("未找到Cookie")
            with listinfolock:
                filterurl = getFilterurl(infoDict, codeDict, page)
                html = getRsponse(filterurl, cookies=cook, method='get', headers=headers, clname=sys._getframe().f_code.co_name)
                if html is False:
                    logger.warning("[!!] List 跳过 %s %s %s" % (city, page, filterurl))
                    continue
                html = verification_url(html, cook_name, cook, clname, cookiepool=cookiepool)
                judge_login_url(html, user=clname, cookiepool=cookiepool)

            select = etree.HTML(html.content.decode('utf-8'))
            infos = select.xpath('//div[@class="result-list sv-search-container"]')
            logger.info("[**] %d 页下有 %d 条带插入的数据" % (page, len(infos[0].xpath('//div[@class="search-result-single   "]//div[@class="header"]'))))
            if len(infos) == 0:
                continue
            continue_flag = True
            for info in infos[0].xpath('//div[@class="search-result-single   "]//div[@class="header"]'):
                url = info.xpath('a/@href')[0]
                name = info.xpath('string(a)')
                print(url, city, codeDict['region'], name + '__' + name)
                # if not settings.RD.exists('tianyancha_%s' % name):
                #     # print((url,info,name))
                #     listQue.put((url, city, codeDict['region']))
                # else:
                #     continue_flag = False
                #     print("存在数据", name, url)
            if settings.OSX == 'linux':
                logger.info("[*] 链接队列%d | 下载队列%d | %s" % (filterQue.qsize(), listQue.qsize(), cookiepool.getWeightData()))
            else:
                logger.info("[*] | %s" % (cookiepool.getWeightData()))
            if infoDict['la'] == 'la3':
                settings.RD.set('tianyancha_%s_%s_%s_%s_%s_%s' % (city, infoDict['industry_code'], infoDict['capital'], infoDict['establish'], code, infoDict['la']), page)
            else:
                settings.RD.set('tianyancha_%s_%s_%s_%s_%s' % (city, infoDict['industry_code'], infoDict['capital'], infoDict['establish'], code), page)
            if continue_flag:
                logger.info("[*] List sleep 10s")
                time.sleep(10)
        if infoDict['la'] == "la4":
            settings.RD.set('tianyancha_%s_%s_%s_%s_%s_over' % (city, infoDict['industry_code'], infoDict['capital'], infoDict['establish'], code), 1, ex=345600)
        else:
            settings.RD.set('tianyancha_%s_%s_%s_%s_%s_%s_over' % (city, infoDict['industry_code'], infoDict['capital'], infoDict['establish'], code, infoDict['la']), 1, ex=345600)

    logger.warning("[!] 信息搜集组件退出")


def skip_click_verification(browser, cookie_name, user='Spider'):
    time.sleep(3)
    logger.info("[*] %s正在进行验证码验证识别" % user)
    k = 0
    while k <= 5:
        browserImg = browser.find_element_by_class_name('new-box94')
        browserImg.screenshot(settings.BASE_DIR + '/img/verification/click_%s_%s.png' % (user, cookie_name))
        if settings.OSX == 'linux':
            img = Image.open(settings.BASE_DIR + '/img/verification/click_%s_%s.png' % (user, cookie_name))
            img2 = img.crop([45, 20, 370, 200])
            # img2 = img.crop([80, 50, 745, 410])
            draw = ImageDraw.Draw(img2)
            fon = './spider/drive/Arial Unicode.ttf'
            font = ImageFont.truetype(fon, 15)
            # font = ImageFont.truetype(settings.IMG_FONTS, 35)
            draw.rectangle((0, 0, img2.size[0], 30), fill=(255, 255, 255))
            draw.text((10, 5), '请你按照 上图 文字 顺序选中 下图 文字！', fill=(255, 0, 0), font=font)
            img2.save(settings.BASE_DIR + '/img/verification/click2_%s_%s.png' % (user, cookie_name))
            Imglocation = browserImg.size
            ikx, iky = img.size[0] / Imglocation['width'], img.size[1] / Imglocation['height']
            html = settings.TEXT_CLICK_CODE.PostPic('click2_%s_%s.png' % (user, cookie_name))
            logger.info("[*]开始写入验证码...")
            if 'pic_str' in html and '|' in html['pic_str']:
                locations = [[int(number) for number in group.split(',')] for group in html['pic_str'].split('|')]
                for location in locations:
                    # 线上测试
                    x = location[0] + 45
                    y = location[1] + 20

                    # 本地测试
                    # x=location[0]+80
                    # y=location[1]+50
                    # x = x / ikx
                    # y = y / iky
                    ActionChains(browser).move_to_element_with_offset(browserImg, x, y).click().perform()
                    time.sleep(0.8)
        else:
            Imglocation = browserImg.size
            img = Image.open(settings.BASE_DIR + '/img/verification/click_%s_%s.png' % (user, cookie_name))
            img2 = img.crop([90, 90, 735, 406])
            draw = ImageDraw.Draw(img2)
            font = ImageFont.truetype(settings.IMG_FONTS, 26)
            draw.rectangle((0, 0, img2.size[0], 20), fill=(255, 255, 255))
            draw.text((40, 5), '请你按照 上图 文字 顺序选中 下图 文字！', fill=(255, 0, 0), font=font)
            img3 = img2.resize((460, 310), Image.ANTIALIAS)
            img3.save(settings.BASE_DIR + '/img/verification/click2_%s_%s.png' % (user, cookie_name))
            kx, ky = img3.size[0] / img2.size[0], img3.size[1] / img2.size[1]
            ikx, iky = img.size[0] / Imglocation['width'], img.size[1] / Imglocation['height']
            html = settings.TEXT_CLICK_CODE.PostPic('click2_%s_%s.png' % (user, cookie_name))
            logger.info("[*]开始写入验证码...")
            if 'pic_str' in html and '|' in html['pic_str']:
                locations = [[int(number) for number in group.split(',')] for group in html['pic_str'].split('|')]
                for location in locations:
                    x = int(location[0] / kx + 90)
                    y = int(location[1] / ky + 90)
                    x = x / ikx
                    y = y / iky
                    ActionChains(browser).move_to_element_with_offset(browserImg, x, y).click().perform()
                    time.sleep(0.8)
        browser.find_element_by_id('submitie').click()
        time.sleep(2)
        if 'captcha/verify' in browser.current_url:
            logger.warning("[!]验证码识别失败，重新验证")
            k += 1
            settings.TEXT_CLICK_CODE.ReportError(html['pic_id'])
            browser.find_element_by_id('refeshie').click()
            time.sleep(2)
        else:
            break


def skip_verification(url, cook_name, user, cookiepool):
    browser = get_browser(True)
    browser.get(url)
    if user != 'Down':
        cookie = json.loads(cookiepool.getCookieName(user, cook_name))
    else:
        cookie = json.loads(settings.RD.get('tianyanchaDownCookie'))
    for i in cookie:
        browser.add_cookie(i)
    browser.get(url)
    skip_click_verification(browser, cook_name, user)
    # print("请进行验证,验证完成后输入回车")
    # input()
    url = browser.current_url
    browser.quit()
    return url


def verification_url(html, cook_name, cookies, user, cookiepool):
    if html is False or 'captcha/verify' in html.url:
        url = skip_verification(html.url, cook_name, user, cookiepool)
        i = 0
        while i < 2:
            html = getRsponse(url, cookies=cookies, method='get', headers=headers, clname=sys._getframe().f_code.co_name)
            if isinstance(html, bool):
                i += 1
                # return False
            else:
                break
        if i >= 2:
            return False
        if user == 'Down':
            logger.info(html.url)
        return verification_url(html, cook_name, cookies, user, cookiepool=cookiepool)
    return html


def judge_login_url(html, user, cookiepool):
    return html
    # k=0
    # while k<3:
    #     if html is False or 'www.tianyancha.com/login?from=' in html.url:
    #         get_cookie(cookiepool,'auto',user=user)
    #     else:
    #         return html
    #     k+=1
    # logger.warning('Cookie 无效，请手动重新登陆')
    # raise SystemExit


def GetPageInfo(clname, listQue, rlk_list, cookiepool, ThreadFlag):
    while True:
        try:
            url, city, region = listQue.get(timeout=1800)
        except:
            if ThreadFlag == 0:
                logger.info("[!]Thead 队列超时，退出")
                break
            else:
                time.sleep(20)
                logging.info("[^] 信息爬取组件重新启动")
                continue
        cook_name, cook = cookiepool.getCookie(clname, di=True)
        if isinstance(cook, bool):
            raise SystemExit("未找到Cookie")
        with rlk_list[cook_name]:
            html = getRsponse(url, cookies=cook, method='get', headers=headers, clname=sys._getframe().f_code.co_name)
            if html is False:
                continue
            html = verification_url(html, cook_name, cook, clname, cookiepool=cookiepool)
            judge_login_url(html, user=clname, cookiepool=cookiepool)
        select = etree.HTML(html.content)
        page404 = select.xpath('//div[@class="page404"]')
        if len(page404) != 0:
            continue
        try:
            info = select.xpath('//div[@class="content"]')[0]
        except:
            continue
        try:
            phone = info.xpath('//div[@class="detail "]/div[@class="f0"]/div[@class="in-block"]/span/span[@class="hidden"]/text()')[0]
        except:
            phone = ""
        try:
            email = info.xpath('//div[@class="detail "]/div[@class="f0"]/div[@class="in-block"][2]/span[2]/text()')[0]
            if email == '暂无信息':
                email = ''
        except:
            email = ''
        try:
            if isinstance(phone, str) and phone != "":
                phone = literal_eval(phone)
            phone = ';'.join(phone)
        except:
            pass
        try:
            corporate_name = info.xpath('//div[@class="header"]/h1[@class="name"]/text()')[0]
            history_name = ';'.join(select.xpath('//div[@class="history-content"]/div/text()'))
            address = ''.join(info.xpath('//div[@class="block-data"]/div[@id="_container_baseInfo"]/table[2]/tbody/tr[10]/td[2]/text()'))
            name = select.xpath('//div[@class="name"]/a/text()')
        except:
            logger.error("%s 未找到" % url)
            continue
        if len(name) == 0:
            name = ""
        else:
            name = name[0]
        try:
            industry = info.xpath('//div[@id="_container_baseInfo"]/table[2]/tbody/tr[5]/td[4]/text()')[0]
        except:
            industry = ''
        try:
            personnel_scale = info.xpath('//div[@id="_container_baseInfo"]/table[2]/tbody/tr[7]/td[4]/text()')[0].replace('-', '')
        except:
            personnel_scale = ''

        insertdate = datetime.datetime.now().date()

        item = {}
        item['corporate_name'] = corporate_name
        item['history_name'] = history_name
        item['city'] = city
        item['industry'] = industry
        item['keyword'] = key
        item['region'] = region
        item['address'] = address
        item['phone'] = phone
        item['email'] = email
        item['personnel_scale'] = personnel_scale
        item['name'] = name
        item['url'] = html.url
        item['year'] = insertdate.year
        item['datetime'] = insertdate
        item['source'] = 'tianyancha'
        item['insertdate'] = insertdate
        item['source_corporate_name'] = item['source'] + '__' + item['corporate_name']
        try:
            Spider.objects.create(**item)
            if settings.OSX == 'linux':
                logger.info("[*] %s 成功插入..... | %s 队列" % (threading.current_thread().name, listQue.qsize()))
            else:
                logger.info("[*] %s 成功插入....." % threading.current_thread().name)
        except:
            Spider.objects.filter(corporate_name=item['corporate_name'], source='tianyancha', source_corporate_name=item['source_corporate_name']).update(
                history_name=item['history_name'], email=item['email'], personnel_scale=item['personnel_scale'], url=item['url'], industry=item['industry'])
            if settings.OSX == 'linux':
                logger.info("[!] %s 存在数据..... %s | %s 队列" % (threading.current_thread().name, item['corporate_name'], listQue.qsize()))
            else:
                logger.info("[!] %s 存在数据..... %s" % (threading.current_thread().name, item['corporate_name']))
        settings.RD.set('tianyancha_%s' % item['corporate_name'], 1)

    logger.warning("[!] 信息抓取组件退出 %s" % threading.current_thread().name)


@app.task
def main(*args, **kwargs):
    global key
    global thread
    global DownloadThread

    keyword = args
    key = keyword[0]
    mod = kwargs['mod']
    thread = int(kwargs['thread'])
    DownloadThread = int(kwargs['downloadthread'])

    manage = Manager()
    manage2 = ManagerCookie()

    # cookiepool = utils.CookiePool('tianyanchaCookie')
    # lock = Lock()
    # listinfolock = MLock()
    # downlock = MLock()

    cookiepool = manage2.CookiePool('tianyanchaCookie')
    listinfolock = manage.Lock()
    rlk_list = {}
    for i in cookiepool.getWeightData()['tianyanchaCookieDict_Spider']:
        rlk_list[i] = RLock()

    logger.info("[*] thead %s | DownloadThead %s | DataThread %s" % (kwargs['thread'], kwargs['downloadthread'], kwargs['datathread']))

    logger.info("[*] 正在进行基线检测")
    if settings.RD.exists('tianyanchaDownCookie'):
        getAllPages(search_url.format(page=1, key=key), cookiepool=cookiepool, user='Down')
    else:
        get_cookie(mod, user='Down', browsermod=False)

    for k in ['Spider', 'List']:
        if cookiepool.exists(k):
            getAllPages(search_url.format(page=1, key=key), cookiepool=cookiepool, user=k)
        else:
            get_cookie(mod, browsermod=False)

    thList = []
    logger.info("[*] 开始收集信息")
    listQue = MQueue(1000)
    filterQue = MQueue(10)
    ThreadFlag = Value("d", 1)

    # for i in range(thread):
    #     i = threading.Thread(target=
    #     , args=('Spider', listQue, rlk_list, cookiepool, ThreadFlag))
    #     i.start()
    #     thList.append(i)

    p = Process(target=SpiderURL, args=(filterQue,))
    p.start()
    thList.append(p)

    time.sleep(2)

    logger.info("[*] 开始爬取信息")
    for i in range(DownloadThread):
        x = Process(target=SpiderThreadPages, args=('List', filterQue, listQue, listinfolock, cookiepool, ThreadFlag))
        x.start()
        thList.append(x)

    for i in thList:
        i.join()
    logger.info('Waiting for all subprocesses done...')


@app.task
def update(*args, **kwargs):
    cookiepool = utils.CookiePool('tianyanchaCookie')
    if kwargs['user'] == 'all':
        for user in ['List', 'Spider', 'Down']:
            cookiepool.delCookieName(user)
            get_cookie(browsermod=False, user=user, cookiepool=cookiepool)
    else:
        cookiepool.delCookieName(kwargs['user'])
        get_cookie(browsermod=False, user=kwargs['user'], cookiepool=cookiepool)
