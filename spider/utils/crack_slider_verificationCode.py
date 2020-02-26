#coding:utf-8
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import time,random
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from django.conf import settings
from selenium.webdriver.common.action_chains import ActionChains


class BaseGeetestCrack(object):

    def __init__(self, driver):
        self.driver = driver

    def calculate_slider_offset(self):
        """计算滑块偏移位置，必须在点击查询按钮之后调用
        :returns: Number
        """
        img1,captcha_el_width = self.crop_captcha_image(1)
        self.drag_and_drop(x_offset=random.randint(140,180))
        img2,captcha_el_width = self.crop_captcha_image(2)
        w1, h1 = img1.size
        w2, h2 = img2.size
        if w1 != w2 or h1 != h2:
            return False
        left = 0
        flag = False
        for i in range(120, w1):
            for j in range(20,h1):
                # print(i,j)
                if not self.is_pixel_equal(img1, img2, i, j):
                    left = i
                    flag = True
                    break
            if flag:
                break
        if left==120:
            left=40
        else:
            left=captcha_el_width/w1*(left-11)
        return left

    def is_pixel_equal(self, img1, img2, x, y):
        pix1 = img1.load()[x, y]
        pix2 = img2.load()[x, y]
        if (abs(pix1[0] - pix2[0] < 60) and abs(pix1[1] - pix2[1] < 60) and abs(pix1[2] - pix2[2] < 60)):
            return True
        else:
            return False

    def crop_captcha_image(self,x, element_id="gt_box"):
        """截取验证码图片
        :element_id: 验证码图片网页元素id
        """
        captcha_el = self.driver.find_element_by_class_name(element_id)
        captcha_el.screenshot('%s/img/verification/%dxxx.png'%(settings.BASE_DIR,x))
        captcha=Image.open('%s/img/verification/%dxxx.png'%(settings.BASE_DIR,x))
        return captcha,captcha_el.size['width']

    def get_track(self,distance):
        '''
        拿到移动轨迹，模仿人的滑动行为，先匀加速后匀减速
        匀变速运动基本公式：
        ①v=v0+at
        ②s=v0t+(1/2)at²
        ③v²-v0²=2as

        :param distance: 需要移动的距离
        :return: 存放每0.2秒移动的距离
        '''
        # 初速度
        v = 0
        # 单位时间为0.2s来统计轨迹，轨迹即0.2内的位移
        t = 0.1
        # 位移/轨迹列表，列表内的一个元素代表0.2s的位移
        tracks = []
        # 当前的位移
        current = 0
        # 到达mid值开始减速
        mid = distance * 4 / 5

        distance += 10  # 先滑过一点，最后再反着滑动回来

        while current < distance:
            if current < mid:
                # 加速度越小，单位时间的位移越小,模拟的轨迹就越多越详细
                a = 2  # 加速运动
            else:
                a = -3  # 减速运动

            # 初速度
            v0 = v
            # 0.2秒时间内的位移
            s = v0 * t + 0.5 * a * (t ** 2)
            # 当前的位置
            current += s
            # 添加到轨迹列表
            tracks.append(round(s))

            # 速度已经达到v,该速度作为下次的初速度
            v = v0 + a * t

        # 反着滑动到大概准确位置
        for i in range(3):
            tracks.append(-2)
        for i in range(4):
            tracks.append(-1)
        return {'forward_tracks':tracks}

    # def get_track(self,distance):
    #     distance += 20  # 20
    #     # distance += 0  # 11
    #     v = 0
    #     t = 0.2
    #     forward_tracks = []
    #
    #     current = 0
    #     mid = distance * 3 / 5
    #     while current < distance:
    #         if current < mid:
    #             a = 2
    #         else:
    #             a = -3
    #
    #         s = v * t + 0.5 * a * (t ** 2)
    #         v = v + a * t
    #         current += s
    #         forward_tracks.append(round(s))
    #
    #     # 反着滑动到准确位置
    #     back_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]  # 20
    #     # back_tracks=[-1, -1, -1, -2]     # 11
    #     # forward_tracks.append(distance - sum(forward_tracks[:-2]))
    #     return {'forward_tracks': forward_tracks[:-2], 'back_tracks': back_tracks}

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        slider = EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_slider_button'))
        return slider


    def move_to_gap(self,slider,tracks):
        ActionChains(self.driver).click_and_hold(slider).perform()

        for track in tracks['forward_tracks']:
            # t=round(random.uniform(0.01,0.03),2)
            # time.sleep(t)
            # time.sleep(0.08)
            ActionChains(self.driver).move_by_offset(xoffset=track, yoffset=0).perform()
        time.sleep(0.5)
        # for back_track in tracks['back_tracks']:
            # time.sleep(0.05)
            # ActionChains(self.driver).move_by_offset(xoffset=back_track, yoffset=0).perform()

        ActionChains(self.driver).move_by_offset(xoffset=-3, yoffset=0).perform()
        ActionChains(self.driver).move_by_offset(xoffset=3, yoffset=0).perform()
        ActionChains(self.driver).release().perform()


    def drag_and_drop(self, x_offset=0, y_offset=0, element_class="gt_slider_knob"):
        """拖拽滑块
        :x_offset: 相对滑块x坐标偏移
        :y_offset: 相对滑块y坐标偏移
        :element_class: 滑块网页元素CSS类名
        """
        x_offset = self.get_track(x_offset)
        dragger = self.driver.find_element_by_class_name(element_class)
        ActionChains(self.driver).click_and_hold(dragger).perform()
        for track in x_offset['forward_tracks']:
            time.sleep(0.02)
            ActionChains(self.driver).move_by_offset(xoffset=track, yoffset=0).perform()
        ActionChains(self.driver).release().perform()
        # action = ActionChains(self.driver)
        # action.drag_and_drop_by_offset(dragger, x_offset, y_offset).perform()
        time.sleep(3)

    def crack(self):
        """执行破解程序
        """
        raise NotImplementedError

class IndustryAndCommerceGeetestCrack(BaseGeetestCrack):
    def __init__(self, driver):
        super(IndustryAndCommerceGeetestCrack, self).__init__(driver)

    def crack(self):
        x_offset = self.calculate_slider_offset()
        track=self.get_track(x_offset)
        element = self.driver.find_element_by_class_name('gt_slider_knob')
        self.move_to_gap(element, track)

#
# def main():
#     driver = webdriver.Chrome('./spider/drive/chromedriver')
#     driver.get("https://www.tianyancha.com")
#     cracker = IndustryAndCommerceGeetestCrack(driver)
#     cracker.crack()
#     input()
#
# if __name__ == "__main__":
#     main()