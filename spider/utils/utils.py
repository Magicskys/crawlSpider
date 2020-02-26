# coding:utf-8
import requests
from requests import adapters
from fake_useragent import UserAgent
from django.conf import settings
import urllib.request
import socket
import pickle
import logging
import random
from threading import Lock
import copy
from collections import Counter
import time

requests.adapters.DEFAULT_RETRIES = 2


# gif to png
def iter_frames(im):
    try:
        i = 0
        while 1:
            im.seek(i)
            imframe = im.copy()
            if i == 0:
                palette = imframe.getpalette()
            else:
                imframe.putpalette(palette)
            yield imframe
            i += 1
    except EOFError:
        pass


def getCookieDict(cookie):
    cookie = [item["name"] + ":" + item["value"] for item in cookie]
    cookMap = {}
    for elem in cookie:
        str = elem.split(':')
        cookMap[str[0]] = str[1]
    return cookMap


def get_ip(project_name):
    def judge_key(response):
        if len(response) == 0:
            return None
        proxy = random.choice(response)
        if settings.RD.exists("UseProxyPool_%s_lock" % proxy):
            response.remove(proxy)
            return judge_key(response)
        return proxy

    proxylist = settings.RD.keys("ProxyPool_*")
    i = 0
    proxies = {}
    if len(proxylist) == 0:
        logging.info("获取代理IP,添加进代理池中")
        while i < 3:
            #代理地址
            url = "http://***"
            try:
                response = urllib.request.urlopen(url, timeout=3).read().decode('utf-8').strip().split('\r\n')
                response2 = copy.deepcopy(response)
                for j in response2:
                    if not settings.RD.exists("UseProxyPool_%s_%s" % (j, project_name)) or settings.RD.exists("UseProxyPool_%s_lock" % j):
                        settings.RD.set("ProxyPool_%s" % j, 1, ex=15)
                    else:
                        response.remove(j)
                if len(response) == 0:
                    continue
                proxy = judge_key(response)
                if proxy is None:
                    continue
                ttl = settings.RD.ttl('ProxyPool_' + proxy)
                settings.RD.incr('ProxyPool_' + proxy)
                settings.RD.expire('ProxyPool_' + proxy, ttl if ttl > 0 else 15)
                settings.RD.delete('ProxyPool_' + proxy)
                proxyurl = "http://" + settings.PROXYUSER + ":" + settings.PROXYPASSWD + "@%s" % proxy
                proxies['http'] = proxyurl
                proxies['https'] = proxyurl
                return proxy, proxies
            except socket.timeout:
                logging.warning("重新获取代理IP ...")
                i += 1
                continue
            except:
                return False, False
        return False, False
    else:
        proxy = random.choice(proxylist).decode('utf-8').split("_", 1)[-1]
        ttl = settings.RD.ttl('ProxyPool_' + proxy)
        settings.RD.incr('ProxyPool_' + proxy, amount=1)
        settings.RD.expire('ProxyPool_' + proxy, ttl if ttl > 0 else 15)
        settings.RD.delete('ProxyPool_' + proxy)
        proxyurl = "http://" + settings.PROXYUSER + ":" + settings.PROXYPASSWD + "@%s" % proxy
        proxies['http'] = proxyurl
        proxies['https'] = proxyurl
        return proxy, proxies


class IP_Pool:
    def __init__(self):
        self.pool = Counter()
        self.ip_time = time.time()

    def pull_ip(self):
        #代理地址
        url = "http://**"
        response = urllib.request.urlopen(url, timeout=3).read().decode('utf-8').strip().split('\r\n')
        self.pool = Counter(response)
        self.ip_time = time.time()

    def get_ip(self):
        if self.ip_time - time.time() > 15 or len(self.pool) == 0:
            self.pull_ip()
        proxy = random.choice(self.pool.most_common(10))[0]
        self.pool.subtract(proxy)
        proxies = {}
        proxyurl = "http://" + settings.PROXYUSER + ":" + settings.PROXYPASSWD + "@%s" % proxy
        proxies['http'] = proxyurl
        proxies['https'] = proxyurl
        return proxy, proxies


# def timeout_retry(url,method,headers,timeout,**kwargs):
#     i = 0
#     while i < 4:
#         proxyname, proxies = get_ip()
#         if proxyname is False:
#             return False,False
#         try:
#             html =requests.request(method=method,url=url,headers=headers,proxies=proxies,timeout=timeout,**kwargs)
#             pagehtmlD=html.text
#             if '由于您的并发请求过高，导致服务器堵塞' in pagehtmlD or '您访问的太快了，请联系我们客服' in pagehtmlD:
#                 settings.RD.set("UseProxyPool_%s_lock"%proxyname, 1,ex=2)
#                 continue
#             return proxyname,html
#         except Exception as e:
#             print(e)
#             logging.warning("开始重试URL... %s | %s "%(url,proxies))
#             settings.RD.set("UseProxyPool_%s"%proxyname, 1)
#             settings.RD.delete('ProxyPool_'+proxyname)
#             timeout+=3
#             i+=1
#     return False,False

class Direquest2():
    def __init__(self):
        requests.adapters.DEFAULT_RETRIES = 5
        self.session = requests.session()
        self.session.keep_alive = False
        self.session.mount('https://', adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))
        self.session.mount('http://', adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))
        self.ua = UserAgent()
        self.pool = IP_Pool()
        self.pool.pull_ip()

    def request(self, url, method, project_name, headers=None, timeout=10, *args, **kwargs):
        headers = {'User-Agent': self.ua.chrome, 'Connection': 'close'}
        if headers is not None:
            headers = dict(headers, **headers)
        if 'cookies' in headers:
            del headers['cookies']
        if 'cookies' in kwargs:
            cook = []
            for k, v in kwargs['cookies'].items():
                cook.append('%s=%s' % (k, v))
            headers['Cookie'] = ';'.join(cook)

        proxyname, html = self.timeout_retry(url, project_name, method, headers, timeout=timeout, **kwargs)
        return proxyname, html

    def timeout_retry(self, url, project_name, method, headers, timeout, **kwargs):
        i = 0
        j = 0
        while i < 4:
            proxyname, proxies = self.pool.get_ip()
            # if proxyname is False:
            #     return False, False
            try:
                html = self.session.request(method=method, url=url, headers=headers, proxies=proxies, timeout=timeout, **kwargs)
                pagehtmlD = html.text
                if '由于您的并发请求过高，导致服务器堵塞' in pagehtmlD or '您访问的太快了，请联系我们客服' in pagehtmlD:
                    # settings.RD.set("UseProxyPool_%s_lock" % proxyname, 1, ex=2)
                    continue
                return proxyname, html
            except socket.timeout:
                logging.warning("开始重试URL... %s | %s " % (url, proxies))
                timeout += 3
                i += 1
            except requests.exceptions.ProxyError as e:
                logging.warning("%s %s" % (proxyname, e))
                i += 1
                j += 1
                if j > 3:
                    j = 0
                    self.pool.pull_ip()
                del self.pool.pool[proxyname]
                time.sleep(random.randint(1, 3))
            except Exception as e:
                logging.warning("%s %s" % (proxyname, e))
                del self.pool.pool[proxyname]
                i += 1
                time.sleep(random.randint(1, 3))
        return False, False


# tianyancha 用这个，上面那个会速度太快,需要手动 sleep 。否则会导致封号
class Direquest():
    def __init__(self):
        self.session = requests.session()
        self.session.keep_alive = False
        self.session.mount('https://', adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))
        self.session.mount('http://', adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))
        self.ua = UserAgent()

    def request(self, url, method, project_name, headers=None, timeout=10, *args, **kwargs):
        headers = {'User-Agent': self.ua.chrome, 'Connection': 'close'}
        if headers is not None:
            headers = dict(headers, **headers)
        if 'cookies' in headers:
            del headers['cookies']
        if 'cookies' in kwargs:
            cook = []
            for k, v in kwargs['cookies'].items():
                cook.append('%s=%s' % (k, v))
            headers['Cookie'] = ';'.join(cook)

        proxyname, html = self.timeout_retry(url, project_name, method, headers, timeout=timeout, **kwargs)
        return proxyname, html

    def timeout_retry(self, url, project_name, method, headers, timeout, **kwargs):
        i = 0
        while i < 4:
            proxyname, proxies = get_ip(project_name)
            if proxyname is False:
                return False, False
            try:
                html = self.session.request(method=method, url=url, headers=headers, proxies=proxies, timeout=timeout, **kwargs)
                pagehtmlD = html.text
                if '由于您的并发请求过高，导致服务器堵塞' in pagehtmlD or '您访问的太快了，请联系我们客服' in pagehtmlD:
                    settings.RD.set("UseProxyPool_%s_lock" % proxyname, 1, ex=2)
                    continue
                return proxyname, html
            except socket.timeout:
                logging.warning("开始重试URL... %s | %s " % (url, proxies))
                settings.RD.set("UseProxyPool_%s_%s" % (proxyname, project_name), 1, ex=18000)
                settings.RD.delete('ProxyPool_' + proxyname)
                timeout += 3
                i += 1
            except Exception as e:
                print(e, proxyname, proxies)
                settings.RD.set("UseProxyPool_%s_%s" % (proxyname, project_name), 1, ex=18000)
                settings.RD.delete('ProxyPool_' + proxyname)
                i += 1
        return False, False


class CookiePool():
    def __init__(self, name: str):
        self.rd = settings.RD
        self.name = name + 'Dict'
        self.count = self.rd.hlen(self.name)
        self.weight_data = self.get_weight_data()
        self.reverse_weight_data = self.compute_weight(self.weight_data)
        # self.ra=self.getra(self.compute_weight(self.weight_data))
        self.choice('tianyanchaCookieDict')
        self.lock = Lock()

    def get_weight_data(self):
        weight_data = {}
        for key, value in self.getAllCookie().items():
            cookDict = {}
            for j in self.getCookieDictName(key.decode('utf-8')):
                count = self.rd.get(j.decode('utf-8') + '_expire')
                cookDict[j.decode("utf-8")] = int(count if count else 0)
            weight_data[key.decode('utf-8')] = cookDict
        return weight_data

    def exists(self, name):
        return self.rd.exists(self.name + '_%s' % name)

    # 计算反向权重
    def compute_weight(self, weight_data):
        c = {}
        for key, value in weight_data.items():
            d = {}
            j = 10
            # for z,rev in value.items():
            for z, rev in sorted(value.items(), key=lambda x: x[1], reverse=True):
                while 1:
                    if j > rev:
                        d[z] = (1 - rev / j) * 100
                        break
                    else:
                        j *= 10
            c[key] = d
        return c

    # 获取权重
    def getra(self, weight_data):
        total = sum([i for i in weight_data.values()])
        ra = random.uniform(0, total)
        curr_sum = 0
        ret = None
        keys = weight_data.keys()
        for k in keys:
            curr_sum += (weight_data[k])
            if ra <= curr_sum:
                ret = k
                break
        return ret

    def choice(self, clname):
        clname = self.name + '_%s' % clname
        while 1:
            names = self.rd.hkeys(clname)
            if len(names) == 0:
                return False
            name = self.getra(self.reverse_weight_data[clname])
            if self.rd.exists(name + '_expire'):
                return name
            else:
                self.rd.hdel(clname, name)

    def getCookie(self, clname, di=True):
        result = self.rd.hgetall(self.name + '_%s' % clname)
        name = self.choice(clname)
        if isinstance(name, bool):
            return False, False
        self.setincr(name=clname, key=name)
        if di:
            return name, getCookieDict(pickle.loads(result[name.encode('utf-8')]))
        else:
            return name, pickle.loads(result[name.encode('utf-8')])

    def getCookieDictName(self, name):
        if self.name not in name:
            name = self.name + '_%s' % name
        return self.rd.hgetall(name)

    def getCookieName(self, name, key):
        return self.rd.hget(self.name + '_%s' % name, key)

    def getAllCookie(self):
        alldict = {}
        for i in self.rd.keys(self.name + '*'):
            alldict[i] = self.rd.hgetall(i)
        return alldict

    def getAllCookieKeys(self):
        return self.rd.hkeys(self.name)

    def setCookie(self, name, key, value, ex):
        self.rd.set(key + '_expire', 1, ex=ex)
        self.rd.hset(self.name + '_%s' % name, key, value)
        self.setincr(name, key)

    def setincr(self, name, key):
        name = self.name + '_%s' % name
        self.rd.incr(key + '_expire', amount=1)
        if name in self.weight_data and key in self.weight_data[name]:
            self.lock.acquire()
            self.weight_data[name][key] += 1
            self.weight_data = self.get_weight_data()
            self.reverse_weight_data = self.compute_weight(self.weight_data)
            self.lock.release()

    def getWeightData(self):
        return self.weight_data

    def delCookieName(self, name):
        self.rd.delete('tianyanchaCookieDict_%s' % name)
