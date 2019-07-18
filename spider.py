# usr/bin/env python3;
#-*-coding: utf-8-*-

'''
思路：
1 模拟登陆
2 通过模拟交互获取市级列表构造url字典
3 模拟切换页面索引并获取公司信息

待解决：
1 使用add_cookie()方法无效; Geetest的极滑验证未通过；模拟登陆功能需要解决
2 页面索引的切换功能未完善，selenium的优势未体现
3 模块可以转化为类便于调用和优化代码 
'''
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
# import requests
# import lxml
import pymongo
import time

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)

wait = WebDriverWait(browser, 10)
client = pymongo.MongoClient('localhost')
db = client['Weimao']

'''
def login():
    '''
    模拟登陆
    '''
    url = "https://www.weimao.com/search/category/12"
    driver.get(url)
    js="var q=document.documentElement.scrollTop=100000"
    driver.execute_script(js)
    login = driver.find_element(By.XPATH, '//div[@class="bottom-tip"]/a')
    login.click()
    for item in cookies:
        driver.add_cookie(item)
    time.sleep(6)
    text = driver.find_elements(By.XPATH, '//div[@class="table"]/div/ul/li')
    print(text)
'''

def get_cities():
    '''
    获取给定网页下的城市索引
    :return: 字典city: url
    ps. 可以使用selenium的Action Chains来实现城市索引的切换，因为没有实现模拟登陆，
        所以本方法虽然使用了selenium，但是属于静态爬取
    '''
    try:
        # login()
        url = "https://www.weimao.com/search/category/12"
        browser.get(url)
        time.sleep(2)
        html = browser.page_source
        doc = pq(html)
        items = doc('.menu-list .mini .item').items()
        city_index = {item.text(): "https://www.weimao.com" + item.attr('href') for item in items}
    except TimeoutException as e:
        get_cities()
    return city_index

def index_page(url):
    """
    抓取城市页所有公司信息
    :param url: 城市地址
    ps. 未登录状态下无法进行页面索引的换页操作，selenium的作用被弱化
    """
    try:
        browser.get(url)
        wait.until(EC.presence_of_element_located((By.ID, 'result_list')))
        get_company_info()
    except TimeoutException:
        index_page(url)

def get_company_info():\
    '''
    获取公司信息
    ps. pyquery比xpath更简洁易记，以往经验看获取节点的出错率也更小
    '''
    html = browser.page_source
    doc = pq(html)
    items = doc('.company-li').items()
    for item in items:
        company = {
            '公司名称': item('.search-left-content a').text(),
            '法定代表人': item('.info-li:first-child span:nth-child(2)').text(),
            '成立时间': item('.info-li:nth-child(2) span:nth-child(2)').text(),
            '注册资本': item('.info-li:nth-child(3) span:nth-child(2)').text(),
            '行业': item('.info-li:nth-child(4) span:nth-child(2)').text(),
            '企业地址': item('.company-adress span:nth-child(2)').text(),
            '企业状态': item('.status span').text()
        }
        print(company)
        save_to_mongo(company)

def save_to_mongo(result):
    '''
    保存至MongoDB
    :param result: 结果
    '''
    try:
        if db['company'].insert(result):
            print('存储到MongoDB成功')
    except Exception:
        print('存储到MongoDB失败')


def main():
    city_index = get_cities()
    for city in city_index.keys():
        print("开始爬取 ", city)
        index_page(city_index[city])

if __name__ == "__main__":
    main()
    browser.close()
