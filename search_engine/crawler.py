import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .models import Index
import ipadic
import MeCab


def split_to_word(text):
    words = []
    # m = MeCab.Tagger("-Ochasen")
    m = MeCab.Tagger(ipadic.MECAB_ARGS)
    # text = text.encode("utf-8")
    print(text)
    node = m.parseToNode(text)
    while node:
        words.append(node.surface)
        node = node.next
    return words


def get_page(page_url):
    r = requests.get(page_url)
    if r.status_code == 200:
        return r.content


def add_to_index(index, keyword, url):
    for entry in index:
        if entry['keyword'] == keyword:
            if not url in entry['url']:
                entry['url'].append(url)
            return
    # not found, add new keyword to index
    print(index)
    print(keyword)
    print(url)
    url = [url]
    Index.objects.create(
        keyword = keyword,
        url =url
    )


def add_page_to_index(index,url,content):
    """contentを形態素解析してindexにurl登録"""
    for keyword in split_to_word(content):
        add_to_index(index, keyword, url)


def extract_page_url_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('a')


# def extract_page_url_and_text(html):
#     """
#     return:
#         {'title': 'url'}
#     """
#     soup = BeautifulSoup(html, 'html.parser')
#     a_tags = soup.find_all('a')
#     url_title_dict = dict() 
#     for a_tag in a_tags:
#         a_tag_title = a_tag.text
#         a_tag_url = a_tag.get('href')
#         url_title_dict[a_tag_title] = a_tag_url
#     print(url_title_dict)
#     return url_title_dict


def crawler(seed,max_depth):    
    to_crawl = {seed}
    crawled = []
    next_depth = []
    index = []
    depth = 0
    while to_crawl and depth <= max_depth:
        page = to_crawl.pop()
        if page not in crawled:
            content = get_page(page)
            add_page_to_index(index, page, content)
            to_crawl.union(next_depth, extract_page_url_links(get_page(page)))
            crawled.append(page)
        if not to_crawl:
            to_crawl, next_depth = next_depth, []
            depth = depth + 1
    return crawled


# def crawler(seed, max_depth):
#     to_crawl = {seed}
#     crawled = []
#     next_depth = []
#     depth = 0
#     while to_crawl and depth <= max_depth:
#         page_url = to_crawl.pop()
#         if page_url not in crawled:
#             html = get_page(page_url)
#             url_title_dict = extract_page_url_and_text(html)
#             add_page(url_title_dict)
#             crawled.append(page_url)
#         if not to_crawl:
#             to_crawl, next_depth = next_depth, []
#             depth += 1