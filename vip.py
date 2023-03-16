import time
from typing import Union, Tuple
from playwright.sync_api import Playwright, sync_playwright
import re
import math
import lxml.etree as etree
import pandas as pd
from pprint import  pprint
import datetime
from furl import furl
import urllib.parse
from typing import Dict, List
from parse import url_parse

def scrape_data(source):
    # 使用lxml解析源代码
    tree = etree.HTML(source)
    # 使用xpath提取表格数据
    table = tree.xpath('//table/tbody/tr')

    data = [[td.text.strip() if td.text is not None and td.text.strip() != '' else '空缺' for td in tr.xpath('./td')] for tr in table]

    #存储数据
    # data = []
    # for tr in table:
    #     td = tr.xpath('./td')
    #     td_value = []
    #     for single_value in td:
    #         if single_value.text is not None:
    #             if single_value.text.strip() == '':
    #                 td_value.append('空缺')
    #             else:
    #                 td_value.append(single_value.text.strip())
    #         else:
    #             td_value.append('空缺')
    #     data.append((td_value))
    return data


def get_date_range(date: str = None, month: bool = False) -> Union[str, Tuple[str, str]]:
    """
    Get date range based on input parameters.

    :param date: str, default None. If specified, return the previous day's date in "YYYY-MM-DD" format.
    :param month: bool, default False. If True, return the date range for the previous month from the current date.
    :return: str or tuple. If `date` is specified, return the previous day's date in "YYYY-MM-DD" format. If `month` is
             True, return a tuple of the start date and end date for the previous month in "YYYY-MM-DD" format.
    """
    if date:
        # calculate previous day's date
        prev_day = (datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        return prev_day
    elif month:
        # calculate previous month's date range
        today = datetime.date.today()
        last_month_end = today.replace(day=1) - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return last_month_start.strftime('%Y-%m-%d'), last_month_end.strftime('%Y-%m-%d')
    else:
        raise ValueError("Either 'date' or 'month' must be specified.")

# def url_parse(url):
#     url = urllib3.parse.unquote(url)  # type: ignore # decode url
#     url_querys = {}
#     if url == '':
#         url_querys['source'] = '专利通'
#         url_querys['name'] = '专利通'
#         url_querys['orgin_name'] = '专利通'
#         url_querys['back_type'] = '专利通'
#         return url_querys


#     url_obj = furl(url)

#     url_parmas = url_obj.query.params

#     if url_obj.path != '/login':
#         url_querys['source'] = url_parmas.get('ga_source','空缺')
#         url_querys['name'] = url_parmas.get('ga_name','空缺')
#         url_querys['orgin_name'] = url_parmas.get('back_url','空缺')
#         url_querys['back_type'] = url_parmas.get('type','空缺')

#         if url_parmas.get('back_url','空缺') != '空缺':
#             url_querys['orgin_name'] = url_parmas.get('back_url','空缺')
#             url_querys['name'] = url_querys['orgin_name']

#         if url_querys['orgin_name'] == 'prompt_popup':
#             url_querys['orgin_name'] = url_parmas.get('back_url','空缺')
#             url_querys['name'] = url_parmas.get('back_url','空缺')

#         if any(s in url_querys['orgin_name'] for s in {'_wuquanxian', '_fanyexianzhi', '_yanfalicheng', '_ercishaixuan', '_jingzhunfenxi', '_unique_link', '_shiguangzhou'}):
#             url_querys['orgin_name'] = url_querys['orgin_name'].split('_')[0]
        
#     else:
#         url_querys['source'] = '登录页'
#         url_querys['name'] = '登录页'
#         url_querys['orgin_name'] = '登录页'
#         url_querys['back_type'] = '登录页'

#     return url_querys

def analyse_url(df:pd.DataFrame):
    need_column = ['账户','时间','试用产品','来源','来源URL']
    need_data = df.loc[:,need_column]
    new_columns = need_data['来源URL'].apply(url_parse)
    new_df = pd.DataFrame(list(new_columns), columns=['source', 'orgin_name', 'name', 'back_type'])
    df = pd.concat([need_data, new_df], axis=1)
    

    df.to_excel('processed_urls.xlsx', index=False)






def run(playwright: Playwright):
    # 初始化 Playwright 并启动一个新的 Chromium 浏览器实例
    browser = playwright.chromium.launch(headless=False, channel='chrome', slow_mo=50)
    page = browser.new_page()

    # 访问登录页面
    page.goto('https://adminvip.yaozh.com/login/index.html')

    # 等待用户名和密码输入框出现，并输入用户名和密码
    page.wait_for_selector("input[name='username']")
    page.fill("input[name='username']", 'liumeng')
    page.fill("input[name='password']", 'liumeng123')

    # 定位鼠标
    page.mouse.move(490, 416)

    # 按下鼠标
    page.mouse.down()

    # 移动鼠标
    page.mouse.move(800, 416)

    # 放起鼠标
    page.mouse.up()

    time.sleep(1)

    # 点击登录
    page.mouse.click(500, 465)

    # 等待1秒

    #获取月
    starttime, endtime = "2023-03-15", "2023-03-15"
    # 跳转到里面
    page.goto(f'https://adminvip.yaozh.com/user/viptrial.html?starttime={starttime}&endtime={endtime}',timeout=5000)


    page.wait_for_load_state()

    #page.wait_for_selector('table')

    #获取共有多少页
    pages_content = page.query_selector('font').text_content()
    items = re.findall('(\d+)',pages_content)[0]
    pages = math.ceil(int(items) / 10)

    rows_list = []

    #翻页转圈所有
    for each_page in range(1, pages+1):
        page.goto(f'https://adminvip.yaozh.com/user/viptrial.html?starttime={starttime}&endtime={endtime}&page={each_page}')

        page.wait_for_load_state()
        page.wait_for_selector('table')
      #  print(page.content())
        content = page.content()
        rows_list.extend(scrape_data(content))

        time.sleep(2)

    pd_csv = pd.DataFrame(data=rows_list,columns=['序号','ID','账户','时间','试用产品','来源','负责人','状态','变更时间','来源URL','页面标题','操作'])
    
    analyse_url(pd_csv)


    time.sleep(5)

    # 关闭浏览器
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
