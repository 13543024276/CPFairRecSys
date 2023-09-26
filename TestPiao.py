# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
#
# # 创建一个Chrome浏览器实例
# driver = webdriver.Chrome()
#
# # 打开小程序网页
# driver.get("https://www.baidu.com/")
#
# # 查找表单元素并填写信息
# # driver.f
# driver.find_elements()
# input_element = driver.find_element(value="kw")  # 使用正确的元素ID
# input_element.send_keys("Wugusdas")  # 填写姓名

# 提交表单（如果有提交按钮的话）
# submit_button = driver.find_element_by_id("submit_button_id")  # 使用正确的按钮ID
# submit_button.click()
# print("sad")
# 关闭浏览器
# driver.quit()

import wxpy
from wxpy import *

bot = Bot()
mini_program = bot.search('参观北大')[0]
mini_program.click()
import pyautogui
import time

# 模拟点击输入框
x, y = 500, 600  # 请根据实际情况调整坐标
pyautogui.click(x, y)

# 输入信息
pyautogui.typewrite('要填写的信息')

# 模拟点击提交按钮
x, y = 600, 700  # 请根据实际情况调整坐标
pyautogui.click(x, y)

# 等待一段时间，以确保信息提交完成
time.sleep(2)