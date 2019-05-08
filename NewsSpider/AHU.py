import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
import csv
from retrying import retry
import multiprocessing
import os
import time


class NewsSpider:
    name = "AHU"
    NewsPage_url = "http://www.ahu.edu.cn/15129/list1.htm"
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/69.0.3497.100 Safari/537.36'
    }

    def start_requests(self, url=NewsPage_url):
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
            return html.text
        except requests.exceptions.RequestException as e:
            print(e)
        return ""

    @retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
    def bs4_analysis(self, url=NewsPage_url):
        """
        @retry
            stop_max_attempt_number: 在停止之前尝试的最大次数，最后一次如果还是有异常则会抛出异常，停止运行
            wait_random_min：在两次调用方法停留时长，停留最短时间，默认为0
            wait_random_max：在两次调用方法停留时长，停留最长时间，默认为1000毫秒
        :param url:
        :return:
        """
        soup = BeautifulSoup(self.start_requests(url=url), 'lxml')
        # title = soup.title.string   # 新闻资讯
        td_table = soup.select('#wp_news_w25 li')
        for td in reversed(td_table):
            try:
                title = td.find(name='a').string
                news_url = "http://www.ahu.edu.cn" + td.find(name='a')['href']
                date = td.find(attrs={'class': 'cols_meta'}).string
                # print(news_url, title, date)
                self.get_NewsDic(news_url=news_url, title=title, date=date)
            except AttributeError as e:
                print(e)
                raise e
        return

    def get_NewsDic(self, news_url, title, date):
        """
        获取单个新闻字典
        :param news_url:
        :param title:
        :param date:
        :return:
        :return:
        """
        soup = BeautifulSoup(self.start_requests(url=news_url), 'lxml')
        p_content, div_content = "", ""
        p_list = soup.select('.wp_articlecontent p')
        div_list = soup.select('.wp_articlecontent')
        for p in p_list:
            for p_child in p.descendants:
                # 遍历子孙节点，并过滤无用标签，如<style>
                if p_child.name is not None and p_child.name != 'style':
                    # print(p_child.name, p_child.string)
                    p_content += p_child.get_text()
        for div in div_list:
            div_content += div.get_text()
        if len(p_content) > 0 and len(div_content) > 0:
            content = p_content if len(p_content) < len(div_content) else div_content
        else:
            content = p_content if len(p_content) > len(div_content) else div_content
        news_dic = {
            'title': title,
            'date': date,
            'content': content.replace('\xa0', ''),
        }
        # print("{} {}\n{}\n\n".format(title, date, content))
        if len(content) > 0:
            self.save_to_csv(news_dic)
        else:
            print("保存失败！URL:{}".format(news_url))
            with open('fail.csv', 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['title', 'date', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(title, date, news_url)
                csvfile.close()
        return news_dic

    @staticmethod
    def save_to_csv(news_dic):
        """
        保存新闻，向尾部添加，字符编码 utf-8
        :param news_dic:
        :return:
        """
        with open('AH_news.csv', 'a', newline='', encoding='utf-8') as csvfile:
            # newline='' 解决空行
            fieldnames = ['title', 'date', 'content']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(news_dic)
            print("保存成功! Title:{} Date:{}".format(news_dic['title'], news_dic['date']))
            csvfile.close()

    def get_PagesNum(self):
        """
        获取新闻网页的总页数
        :return: number of pages
        """
        soup = BeautifulSoup(self.start_requests(), 'lxml')
        pages_num = soup.find(attrs={'class': 'all_pages'}).string
        print("number of pages: ", pages_num)
        return pages_num

    def work(self, page_num=None):
        """
        爬虫入口
        倒序遍历新闻页爬取
        :return: None
        """
        if page_num is None:
            # 若无参数，则获取总页数开始爬取
            page_num = int(self.get_PagesNum())

        # 多进程爬取，阻塞按顺序存储
        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        for i in range(page_num, 0, -1):
            page_url = "http://www.ahu.edu.cn/15129/list{}.htm".format(i)
            print("开始爬取第{}页".format(i))
            pool.apply(self.bs4_analysis, (page_url, ))
            # self.bs4_analysis(url=page_url)
        pool.close()
        pool.join()


if __name__ == '__main__':
    news = NewsSpider()
    news.work()
    os.system("shutdown -s -t  60 ")
