# -*- encoding: utf-8 -*-
"""
@File    : HFUTexchange.py
@Author  : MiracleShadow
@Time    : 2019-5-10 13:00
@Email   : zhangzhuheng2018@gmail.com
@Software: PyCharm
"""

import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
from retrying import retry
import multiprocessing
import csv


class NewsSpider:
    name = "HFUT"
    csv_file_path = "CSVFiles/HFUT_news.csv"
    News_Page_Url = "http://news.hfut.edu.cn/list-1-1.html"
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/69.0.3497.100 Safari/537.36'
    }
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))

    def start_requests(self, url=News_Page_Url):
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
            html = requests.get(url=url, headers=self.headers, timeout=6)
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
            html = requests.get(url=self.News_Page_Url, headers=self.headers, timeout=6)
            html.raise_for_status()
        except requests.exceptions.RequestException as e:
            return False, e
        return True

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def number_of_pages(self):
        soup = BeautifulSoup(self.start_requests(), 'lxml')
        pages_num = soup.select('#pages a')[-2:-1][0].string
        print("The number of pages is: ", pages_num)
        return pages_num

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def get_news_dic_list(self, url=News_Page_Url):
        """
        获取一个新闻页每条新闻的主要内容
        :param url:
        :return:
        """
        news_li = []
        soup = BeautifulSoup(self.start_requests(url=url), 'lxml')
        li_list = soup.select('.col-lg-8 li')
        for li in reversed(li_list):
            try:
                url = "http://news.hfut.edu.cn" + li.find(name='a')['href']
                title = li.find(name='a').string
                date = li.find(name='span').string
                content = self.get_news_content(news_url=url)
                news_dic = {
                    'Title': title,
                    'Date': date,
                    'Content': content,
                    'Url': url,
                }
                print(news_dic)
                news_li.append(news_dic)
            except TypeError:
                continue
        return news_li

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def get_news_content(self, news_url):
        """
        获取单个新闻内容
        :param news_url:
        :return:
        """
        soup = BeautifulSoup(self.start_requests(url=news_url), 'lxml')
        p_list = soup.select('#artibody p')
        content = "".join(p.get_text() for p in p_list)
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

    def work(self, page_num=None):
        """
        爬虫入口
        倒序遍历新闻页爬取
        :return: None
        """

        if self.link_test():
            print("合肥工业大学——工大要闻 Link successful! Start request...")
        else:
            print("合肥工业大学——工大要闻 Link failed!")
            exit()

        if page_num is None:
            # 若无参数，则获取总页数开始爬取
            page_num = int(self.number_of_pages())

        self.create_csv()

        for i in range(page_num, 0, -1):
            news_page_url = "http://news.hfut.edu.cn/list-1-{}.html".format(i)
            print("开始爬取第{}页".format(i))
            news_dic_list = self.get_news_dic_list(url=news_page_url)
            for news_dic in news_dic_list:
                self.save_to_csv(news_dic=news_dic)


if __name__ == '__main__':
    news = NewsSpider()
    news.work()
