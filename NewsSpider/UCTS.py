# -*- encoding: utf-8 -*-
"""
@File    : UCTS.py
@Author  : MiracleShadow
@Time    : 2019-5-22 17:00
@Email   : zhangzhuheng2018@gmail.com
@Software: PyCharm
"""

from ns import NewsSpider

ns = NewsSpider(name='UCTS', news_page_url='http://news.ustc.edu.cn/xwbl/list{}.htm',
                main_url='http://news.ustc.edu.cn', csv_file_path='CSVFiles/UCTS_news.csv',
                select_dic_list='#wp_news_w3 li', select_content='#articleShow p')
ns.run(291)
