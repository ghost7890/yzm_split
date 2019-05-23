import os
from PIL import Image

class Yzm_spilt(object):
    def __init__(self, yzm_path='yzm.gif', img_dir='./img/', threshold=165):
        self.yzm_path = yzm_path        # 验证码图片位置
        self.img_dir = img_dir          # 验证码切片存放目录
        self.threshold = threshold      # 二值化的阈值
        self.__dir_is_exist()           # 初始化验证码切片存放目录
        self.captcha_firstsplit_paths = []  # 存放纵向切片位置

    def __dir_is_exist(self):
        '''
        初始化img目录
        :return:
        '''
        if os.path.exists(self.img_dir):        # 如果存在img目录，则清空
            files = [self.img_dir + file for file in os.listdir(self.img_dir)]
            for file in files:
                os.remove(file)
        else:                                   # 如果不存在则创建img目录
            os.mkdir(self.img_dir)

    def preprocessing(self, yzm_path='yzm.gif', new_yzm_path='yzm.gif'):
        '''
        验证码预处理，灰度化，二值化
        :param captcha_path:    验证码图片路径
        :param new_captcha_path: 经过预处理后验证码图片保存路径
        '''
        image = Image.open(yzm_path)
        # 灰度化
        image = image.convert('L')
        # 二值化
        table = []
        for i in range(256):
            if i < self.threshold:
                table.append(0)
            else:
                table.append(1)
        image = image.point(table, '1')
        image.save(new_yzm_path)

    def split_col(self, image):
        '''
        寻找验证码纵向的切割边界
        :param image: 验证码对象
        :return: 每个字符的起始横坐标和结束横坐标的list
        '''
        inletter = False        # 标记当前列是否在字符内，False表示不在字符内，True表示在字符内
        foundletter = False     # 标记是否找到字符，False表示目前没找到字符，True表示已经找到字符
        start = 0
        end = image.size[0]
        letters = []            # 记录每个字符的起始坐标和结束坐标
        for x in range(image.size[0]):          # 按列查找
            for y in range(image.size[1]):
                pix = image.getpixel((x, y))
                if pix != 255:      # 不为白色，表示进入字符
                    inletter = True
            if foundletter == False and inletter == True:   # 刚进入字符，将foundletter标记为True
                foundletter = True
                start = x
            if foundletter == True and inletter == False:   # 当前列已经出了字符，并将起始位置
                foundletter = False                         # 将foundletter重置为False
                end = x
                if end - start >= 4:                        # 如果字符切片宽度大于等于4像素，则记录起始终止位置；
                    letters.append((start, end))            # 否则，认为当前切片为图片的噪点，或平躺的i、j首部（不具备唯一性，识别用不到，故剔除）
            inletter = False                                # 重置inletter为False
        # 最后一个字符贴边
        if start != letters[-1][0]:                         # 如果当前的start和letters中最后一个start不等，后面还有字符，即字符贴边
            letters.append((start, image.size[0]))          # 最后一个字符的结束位置，即图片的宽度
        return letters

    def is_row_have_black(self, image, row):
        '''
        判断该行是否有黑像素
        :param image: 图片对象
        :param column: 图片的行
        :return:
        '''
        for i in range(image.size[0]):
            pix = image.getpixel((i, row))  # 获取图片某点的像素值
            if pix != 1:    # 不为白
                return True
        return False

    def split_row(self, image, start, end):
        '''
        寻找验证码横向的切割边界
        :param image:
        :return:
        '''
        inletter = False        # 表示当前在字符内部
        if start >= end:        # 递归出口
            return None, None

        mid = int((end - start) / 2)    # 图片中间行

        inletter = self.is_row_have_black(image, mid)  # 中间一行出现黑像素表示进入字符中

        if inletter == True:  # 在字符中间

            outletter_up = False            # 是否出字符（上半部分），False表示没出字符，True表示已经出字符
            outletter_down = False          # 是否出字符（下半部分），False表示没出字符，True表示已经出字符

            for i in range(1, int(mid) + 2):  # 向两边发散，考虑到图片高度为偶数，从中间移动mid的距离不足以到达图片边界，
                                                # 特此将移动距离mid+2
                # 向上
                if outletter_up == False:

                    row_have_black = self.is_row_have_black(image, mid - i)  # 上i行是否有黑像素

                    if row_have_black is False:  # 向上第一次全白的行
                        top = mid - i + 1
                        outletter_up = True     # 已经出字符

                    if mid - i == 0:  # 贴顶
                        top = 0
                        outletter_up = True

                # 向下
                if outletter_down == False:

                    row_have_black = self.is_row_have_black(image, mid + i)  # 下i行是否有黑像素

                    if row_have_black is False:  # 向下的第一行全白，下到底
                        botton = mid + i
                        outletter_down = True

                    if mid + i + 1 == image.size[1]:  # 贴底
                        botton = mid + i + 1
                        outletter_down = True

                if outletter_up == True and outletter_down == True:
                    if botton - top >= 4:  # 如果宽度大于等于4像素，返回top,botton
                        return top, botton

            return None, None  # 如果宽度小于4像素，返回None，None（即i、j的首部的点）

        # 不在字符中间，即字符位于上半部分或下半部分，或是i、j首位分离
        else:
            top_up, botton_up = self.split_row(image, start, mid - 1)
            top_down, botton_down = self.split_row(image, mid + 1, end)

            if top_up != None and botton_up != None:  # 字符在上半部分或i、j尾部在上半部分
                return top_up, botton_up
            else:  # 字符在上半部分或i、j头部在上半部分，尾部在下半部分
                return top_down, botton_down
        pass

    def deal_col(self, img_path):
        '''
        验证码纵向处理
        :param img_path:
        :return:
        '''

        image = Image.open(img_path)
        # 纵向切
        letters = self.split_col(image)
        # 保存各个切片图片
        try:
            for j in range(len(letters)):
                im_spilt = image.crop((letters[j][0], 0, letters[j][1], image.size[1]))
                new_path = self.img_dir + '{0}.gif'.format(j)
                im_spilt.save(new_path)
                self.captcha_firstsplit_paths.append(new_path)
        except:
            pass

    def deal_row(self):
        '''
        单个字符横向处理
        :return:
        '''
        for captcha in self.captcha_firstsplit_paths:
            img = Image.open(captcha)
            # 横向切
            top, botton = self.split_row(img, 0, img.size[1]-1)
            # 切割，并保存文件
            try:
                im_spilt = img.crop((0, top, img.size[0], botton))
                new_path = '{0}split__{1}'.format(self.img_dir, captcha.split('/')[-1])
                im_spilt.save(new_path)
            except:
                pass

    def run(self, yzm_path='yzm.gif'):
        # 验证码预处理
        self.preprocessing(yzm_path, yzm_path)
        # 验证码纵向处理
        self.deal_col(yzm_path)
        # 验证码横向处理
        self.deal_row()



if __name__ == '__main__':
    yzm = Yzm_spilt()
    yzm.run()

