import requests
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup


class NewsSpider:
    name = "HFUT"
    NewsPage_url = "http://news.hfut.edu.cn/list-1-161.html"
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/69.0.3497.100 Safari/537.36'
    }
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))

    def link_test(self):
        try:
            html = requests.get(url=self.NewsPage_url, headers=self.headers, timeout=6)
            html.raise_for_status()
        except requests.exceptions.RequestException as e:
            return False, e
        return True


if __name__ == '__main__':
    news = NewsSpider()
    print(news.link_test())

