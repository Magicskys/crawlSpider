import json
import redis
import time
from spider.utils import text_click_verificationCode
import logging
from PIL import Image, ImageDraw, ImageFont
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import os
import platform

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OSX = ''
if platform.system() == 'Darwin':
    OSX = 'mac'
elif platform.system() == 'Linux':
    OSX = 'linux'
else:
    raise SystemExit('not found browser drive!')

logger = logging.getLogger('tianyancha')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
logger.addHandler(ch)

pool = redis.ConnectionPool(host='127.0.0.1', password='', db=0)
rd = redis.Redis(connection_pool=pool)

# 超级鹰账号
TEXT_CLICK_CODE = text_click_verificationCode.Chaojiying_Client('', '', '')
CHROME_DRIVER = BASE_DIR + '/crawlSpider/spider/drive/chromedriver_%s' % OSX
# CHROME_DRIVER=BASE_DIR+'/spider/drive/chromedriver_mac'
# PHANTOMJS=BASE_DIR+'/spider/drive/phantomjs_%s'%osx
IMG_FONTS = BASE_DIR + '/crawlSpider/spider/drive/Arial Unicode.ttf'


def get_browser(browsermod=True, stat=True):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    if browsermod and stat:
        if OSX == 'linux':
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36"')
            browser = webdriver.Chrome(CHROME_DRIVER, chrome_options=options)
            browser.maximize_window()
            return browser
    elif browsermod is True and stat is False:
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(
            'user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1664.3 Safari/537.36"')
        browser = webdriver.Chrome(CHROME_DRIVER, chrome_options=options)
        browser.maximize_window()
        return browser
    return webdriver.Chrome(CHROME_DRIVER)


def skip_click_verification(browser, cookie_name, user='Spider'):
    time.sleep(3)
    logger.info("[*] %s正在进行验证码验证识别" % user)
    k = 0
    while k <= 5:
        browserImg = browser.find_element_by_class_name('new-box94')
        browserImg.screenshot(BASE_DIR + '/img/verification/click_%s_%s.png' % (user, cookie_name))
        if OSX == 'linux':
            img = Image.open(BASE_DIR + '/img/verification/click_%s_%s.png' % (user, cookie_name))
            img2 = img.crop([45, 20, 370, 200])
            # img2 = img.crop([80, 50, 745, 410])
            draw = ImageDraw.Draw(img2)
            fon = './spider/drive/Arial Unicode.ttf'
            font = ImageFont.truetype(fon, 15)
            # font = ImageFont.truetype(IMG_FONTS, 35)
            draw.rectangle((0, 0, img2.size[0], 30), fill=(255, 255, 255))
            draw.text((10, 5), '请你按照 上图 文字 顺序选中 下图 文字！', fill=(255, 0, 0), font=font)
            img2.save(BASE_DIR + '/img/verification/click2_%s_%s.png' % (user, cookie_name))
            Imglocation = browserImg.size
            ikx, iky = img.size[0] / Imglocation['width'], img.size[1] / Imglocation['height']
            html = TEXT_CLICK_CODE.PostPic('click2_%s_%s.png' % (user, cookie_name))
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
            img = Image.open(BASE_DIR + '/img/verification/click_%s_%s.png' % (user, cookie_name))
            img2 = img.crop([90, 90, 735, 406])
            draw = ImageDraw.Draw(img2)
            font = ImageFont.truetype(IMG_FONTS, 26)
            draw.rectangle((0, 0, img2.size[0], 20), fill=(255, 255, 255))
            draw.text((40, 5), '请你按照 上图 文字 顺序选中 下图 文字！', fill=(255, 0, 0), font=font)
            img3 = img2.resize((460, 310), Image.ANTIALIAS)
            img3.save(BASE_DIR + '/img/verification/click2_%s_%s.png' % (user, cookie_name))
            kx, ky = img3.size[0] / img2.size[0], img3.size[1] / img2.size[1]
            ikx, iky = img.size[0] / Imglocation['width'], img.size[1] / Imglocation['height']
            html = TEXT_CLICK_CODE.PostPic('click2_%s_%s.png' % (user, cookie_name))
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
            TEXT_CLICK_CODE.ReportError(html['pic_id'])
            browser.find_element_by_id('refeshie').click()
            time.sleep(2)
        else:
            break


logger.info("开始监听")
ps = rd.pubsub()
ps.subscribe("colly")

for item in ps.listen():
    if item['type'] == 'message':
        browser = get_browser(True)
        print(item['data'])
        # cookie = json.loads(rd.hget('tianyanchaCookieDict_Spider', item['data']))
        cookie = json.loads(rd.get('tianyanchaDownCookie'))
        browser.get("https://www.tianyancha.com/company/9434757")
        for i in cookie:
            if 'expiry' in i:
                i['expiry'] = int(i['expiry'])
            print(i)
            browser.add_cookie(i)
        browser.get("https://www.tianyancha.com/company/9434757")
        # skip_click_verification(browser, "cook_name")
