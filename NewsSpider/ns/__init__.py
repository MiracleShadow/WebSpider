# -*- encoding: utf-8 -*-
"""
@File    : __init__.py.py
@Author  : MiracleShadow
@Time    : 2019-5-22 17:00
@Email   : zhangzhuheng2018@gmail.com
@Software: PyCharm
"""

__all__ = ['NewsSpider']

import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from retrying import retry
import multiprocessing
import csv


class NewsSpider:
    HEADERS = {
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/69.0.3497.100 Safari/537.36'
    }

    def __init__(self, name="", news_page_url="", main_url="", csv_file_path=None,
                 select_dic_list="", select_content=""):
        """

        :param name:
        :param news_page_url:
        :param main_url:
        :param csv_file_path:
        """
        self.name = name
        self.news_page_url = news_page_url
        self.main_url = main_url
        self.csv_file_path = csv_file_path
        self.select_dic_list = select_dic_list
        self.select_content = select_content

    def __str__(self):
        return '<ns: {name} {url}'.format(name=self.name, url=self.name)

    def start_requests(self, url):
        """
        max_retries 为最大重试次数，重试3次
        timeout=5   超时时间为5
        :param url: 需要requests的url
        :return:
        """
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=3))
        s.mount('https://', HTTPAdapter(max_retries=3))
        try:
            html = requests.get(url=url, headers=self.HEADERS, timeout=6)
            html.encoding = html.apparent_encoding
            html.raise_for_status()
            return html.text
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.HTTPError:
            pass
        except requests.exceptions.RequestException as e:
            print(e)
            raise e

    def link_test(self):
        try:
            html = requests.get(url=self.news_page_url.format(1), headers=self.HEADERS, timeout=6)
            html.raise_for_status()
        except requests.exceptions.RequestException as e:
            return False, e
        return True

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def total_news_pages(self, select):
        soup = BeautifulSoup(self.start_requests(url=self.news_page_url.format(1)), 'lxml')
        print(soup)
        pages_num = soup.select(select)
        print("The number of pages is: ", pages_num)
        return pages_num

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def get_news_dic_list(self, news_list_url):
        """
        获取一个新闻页每条新闻的主要内容
        :param news_list_url:
        :return:
        """
        soup = BeautifulSoup(self.start_requests(url=news_list_url), 'lxml')
        li_list = soup.select(self.select_dic_list)
        for li in reversed(li_list):
            try:
                url = self.main_url + li.find(name='a')['href']
                title = li.find(name='a').string
                date = li.find(name='span').string
                content = self.get_news_content(news_url=url, select=self.select_content)
                news_dic = {
                    'Title': title,
                    'Date': date,
                    'Content': content,
                    'Url': url,
                }
                yield news_dic
            except TypeError:
                continue

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def get_news_content(self, news_url, select):
        """
        获取单个新闻内容
        :param select:
        :param news_url:
        :return:
        """
        soup = BeautifulSoup(self.start_requests(url=news_url), 'lxml')
        p_list = soup.select(select)
        content = ""
        for p in p_list:
            content += p.get_text()
        content = content.replace('\xa0', '').replace('\n', '').replace('\r\t', '')
        return content

    def create_csv(self):
        """
        新建csv文件保存爬取的新闻信息
        :return:
        """
        csv_head = ["Title", "Date", "Content", "Url"]
        with open(self.csv_file_path, 'w', newline='') as csv_file:
            csv_write = csv.writer(csv_file)
            csv_write.writerow(csv_head)
            print("Create csv file successful! path:{}".format(self.csv_file_path))
            csv_file.close()

    def save_to_csv(self, news_dic):
        """
        保存新闻，向尾部添加，字符编码 utf-8
        :param news_dic:
        :return:
        """
        with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as csv_file:
            # newline='' 解决空行
            fieldnames = ["Title", "Date", "Content", "Url"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writerow(news_dic)
            print("Save to csv successful! Title:{} Date:{}".format(news_dic['Title'], news_dic['Date']))
            csv_file.close()

    def work(self, page):
        """

        :param page:
        :return:
        """
        for news_dic in self.get_news_dic_list(self.news_page_url.format(page)):
            self.save_to_csv(news_dic=news_dic)

    def run(self, page_num=None, multiprocess=False):
        """
        爬虫入口
        倒序遍历新闻页爬取
        :return: None
        """

        if self.link_test():
            print("{} Link successful! Start request...".format(self.name))
        else:
            print("{} Link failed!".format(self.name))
            exit()

        if page_num is None:
            # 若无参数，则获取总页数开始爬取
            page_num = int(self.total_news_pages())

        self.create_csv()

        # 多进程爬取，阻塞按顺序存储
        if multiprocess:
            pool = multiprocessing.Pool(multiprocessing.cpu_count())
            for i in range(page_num, 0, -1):
                print("开始多进程爬取第{}页".format(i))
                pool.apply_async(self.work, (i,))
            pool.close()
            pool.join()
        else:
            for i in range(page_num, 0, -1):
                print("开始爬取第{}页".format(i))
                self.work(i)


if __name__ == '__main__':
    ns = NewsSpider(name='UCTS', news_page_url='http://news.ustc.edu.cn/xwbl/list{}.htm',
                    main_url='http://news.ustc.edu.cn', csv_file_path='../CSVFiles/UCTS_news.csv',
                    select_dic_list='#wp_news_w3 li', select_content='#articleShow p')
    # ns.run(291)
    ns.run(291, multiprocess=True)
