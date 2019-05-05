import requests
from bs4 import BeautifulSoup
import csv
import time


class NewsSpider:
    name = "HNNU"
    NewsPage_url = "http://www.hnnu.edu.cn/199/list1.htm"
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/69.0.3497.100 Safari/537.36'
    }

    def start_requests(self, url=NewsPage_url):
        try:
            html = requests.get(url=url, headers=self.headers)
            html.raise_for_status()
            html.encoding = html.apparent_encoding
            return html.text
        except:
            print('request error')
            pass

    def bs4_analysis(self, url=NewsPage_url):
        soup = BeautifulSoup(self.start_requests(url=url), 'lxml')
        title = soup.title.string
        td_table = soup.find(attrs={'portletmode': 'simpleList'}).find_all(name='td')
        for td in reversed(td_table):
            try:
                title = td.find(name='a').string
                news_url = "http://www.hnnu.edu.cn" + td.find(name='a')['href']
                date = td.find(style='white-space:nowrap').string
                # print(news_url, title, date)
                self.get_NewsDic(news_url=news_url, title=title, date=date)
            except:
                pass
        return

    def get_NewsDic(self, news_url, title, date):
        """
        获取单个新闻字典
        :return:
        """
        soup = BeautifulSoup(self.start_requests(url=news_url), 'lxml')
        content = ""
        p_list = soup.select('.Article_Content p')
        for p in p_list:
            content += p.get_text()

        news_dic = {
            'title': title,
            'date': date,
            'content': content.replace('\xa0', '')
        }
        self.save_to_csv(news_dic)
        return

    @staticmethod
    def save_to_csv(news_dic):
        """
        保存新闻，向尾部添加，字符编码 utf-8
        :param news_dic:
        :return:
        """
        with open('HNNU_news.csv', 'a', newline='', encoding='utf-8') as csvfile:
            # newline='' 解决空行
            fieldnames = ['title', 'date', 'content']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(news_dic)
            print("保存成功! Title:{} Date:{}".format(news_dic['title'], news_dic['date']))
            csvfile.close()

    def get_pagesnum(self):
        """
        获取新闻网页的总页数
        :return: number of pages
        """
        soup = BeautifulSoup(self.start_requests(), 'lxml')
        pagesnum = soup.find(attrs={'class': 'all_pages'}).string
        print("number of pages: ", pagesnum)
        return pagesnum

    def work(self, page_num=None):
        """
        爬虫入口
        倒序遍历新闻页爬取
        :return: None
        """
        if page_num is None:
            page_num = int(self.get_pagesnum())
        for i in range(page_num, 0, -1):
            page_url = "http://www.hnnu.edu.cn/199/list{}.htm".format(i)
            print("开始爬取第{}页".format(i))
            self.bs4_analysis(url=page_url)


if __name__ == '__main__':
    news = NewsSpider()
    news.work(page_num=184)
