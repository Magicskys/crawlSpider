#!/usr/bin/env python
# coding:utf-8

import requests
from hashlib import md5
from django.conf import settings

class Chaojiying_Client(object):

    def __init__(self, username, password, soft_id):
        self.username = username
        password =  password.encode('utf8')
        self.password = md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    def PostPic(self,filename,codetype=9004):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
        }
        with open(settings.BASE_DIR+'/img/verification/%s'%filename,'rb') as fp:
            im=fp.read()
        params.update(self.base_params)
        files = {'userfile': ('p2.png', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', data=params, files=files, headers=self.headers)
        return r.json()

    def ReportError(self, im_id):
        """
        im_id:报错题目的图片ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/ReportError.php', data=params, headers=self.headers)
        return r.json()


# if __name__ == '__main__':
#     chaojiying = Chaojiying_Client('', '', '')	#用户中心>>软件ID 生成一个替换 96001
#     im = open('/Users/haishun/project/p2.png', 'rb').read()													#本地图片文件路径 来替换 a.jpg 有时WIN系统须要//
#     print(chaojiying.PostPic(im, 9004))											#1902 验证码类型  官方网站>>价格体系 3.4+版 print 后要加()

    # print(chaojiying.ReportError(6063119312254100004))

    # {'err_no': 0, 'err_str': 'OK', 'pic_id': '6063119322254100005', 'pic_str': '184,246|302,222|524,226|470,193','md5': 'e7613d0d126af3cdc24c26eb951e326e'}
