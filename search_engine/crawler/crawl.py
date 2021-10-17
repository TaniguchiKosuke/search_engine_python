from nltk import text
from nltk.util import filestring
import requests
import time
from requests.api import request
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import nltk

from .analyze import analyze
from ..models import Index, Article, ToAnalyzePage


def get_page(page_url):
    """
    url取得
    """
    try:
        proxies_dic = {
            "http": "http://proxy.example.co.jp:8080",
            "https": "http://proxy.example.co.jp:8080",}
        r = requests.get(page_url, timeout=(3.0, 7.5))
        time.sleep(3)
        if r.status_code == 200:
            return r.content
    except requests.ConnectionError as e:
        print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
        print(str(e))   


def extract_page_url_links(page_content):
    """
    クローリング先のページのaタグのhref属性を取得し、ToAnalyzePageに追加
    """
    soup = BeautifulSoup(page_content, 'html.parser')
    a_tags = soup.find_all('a')
    for a_tag in a_tags:
        a_tag_href = a_tag.get('href')
        if a_tag_href:
            url_jpg = a_tag_href.endswith('jpg')
            url_jpeg = a_tag_href.endswith('jpeg')
            url_png = a_tag_href.endswith('png')
            url_gif = a_tag_href.endswith('gif')
            url_tiff = a_tag_href.endswith('tiff')
            if a_tag_href.startswith('http') and not url_jpg and not url_jpeg and not url_png and not url_gif and not url_tiff:
                crawled = Article.objects.filter(url=a_tag_href)
                to_analyze = ToAnalyzePage.objects.filter(url=a_tag_href)
                if not crawled and not to_analyze:
                    ToAnalyzePage.objects.create(url=a_tag_href)
            else:
                continue


def crawl(max_depth, stop_flag):
    depth = 0
    seeds = ToAnalyzePage.objects.all().exists()
    while seeds and depth <= max_depth and not stop_flag:
        to_analyze_pages = ToAnalyzePage.objects.order_by('?')[:10]
        page_content_dict = dict()
        for page in to_analyze_pages:
            page_content = get_page(page.url)
            page_content_dict[page.url] = page_content
        if page_content_dict:
            page_content = list(page_content_dict.values())[0]
            extract_page_url_links(page_content)
            print('here==========================')
            analyze(page_content_dict)