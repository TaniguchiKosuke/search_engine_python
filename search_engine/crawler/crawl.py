from nltk import text
import requests
import time
import json
import re
from requests.api import request
from urllib.parse import urljoin
import concurrent.futures

from bs4 import BeautifulSoup
import ipadic
import MeCab
import nltk

from .analyze import analyze
from ..models import Index, Article, ToAnalyzePage


def get_page(page_url):
    """
    url取得
    """
    r = requests.get(page_url, timeout=(3.0, 7.5))
    time.sleep(3)
    if r.status_code == 200:
        return r.content


def extract_page_url_links(page_content):
    """
    クローリング先のページのaタグのhref属性を取得し、ToAnalyzePageに追加
    """
    soup = BeautifulSoup(page_content, 'html.parser')
    a_tags = soup.find_all('a')
    for a_tag in a_tags:
        a_tag_href = a_tag.get('href')
        if a_tag_href:
            if a_tag_href.startswith('http'):
                crawled = Article.objects.filter(url=a_tag_href)
                to_analyze = ToAnalyzePage.objects.filter(url=a_tag_href)
                if not crawled and not to_analyze:
                    ToAnalyzePage.objects.create(url=a_tag_href)
            else:
                continue


def crawl(max_depth, stop_flag):
    depth = 0
    seeds = ToAnalyzePage.objects.all()
    while seeds and depth <= max_depth and not stop_flag:
        page_url = seeds.order_by('?').first().url
        print(page_url)
        article_exist = Article.objects.filter(url=page_url)
        if not article_exist:
            page_content = get_page(page_url)
            if page_content:
                extract_page_url_links(page_content)
                print('here==========================')
                analyze(page_url, page_content)