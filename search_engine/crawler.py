from bs4.element import ContentMetaAttributeValue
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .models import Index
import ipadic
import MeCab
import time


def split_to_word(text):
    """
    MeCabにより、日本語を解析
    """
    words = []
    # m = MeCab.Tagger("-Ochasen")
    m = MeCab.Tagger(ipadic.MECAB_ARGS)
    #この処理をしないとエラーが出る
    text = str(text).lower()
    node = m.parseToNode(text)
    while node:
        words.append(node.surface)
        node = node.next
    return words


def get_page(page_url):
    """
    指定したurlのページを取得
    """
    r = requests.get(page_url)
    time.sleep(3)
    if r.status_code == 200:
        return r.content


def add_to_index(index, keyword, url):
    """
    キーワードとurlをDBに追加
    """
    for entry in index:
        if entry['keyword'] == keyword:
            if not url in entry['url']:
                entry['url'].append(url)
            return
    if keyword:
        Index.objects.create(
            keyword = keyword,
            url =url
        )


def add_page_to_index(index, url, html):
    """
    取得したページをインデックスに追加
    """
    print(type(index))
    print(type(url))
    print(type(html))
    body_soup = BeautifulSoup(html, "html.parser").find('body')
    for child_tag in body_soup.findChildren():
        #直下の処理でscritpタグを処理から外す
        if child_tag.name == 'script':
            continue
        #以下でh1, h2, h3といったその記事のキーワードになりそうなタグのテキストを取得
        if child_tag.name == 'h1' or child_tag.name == 'h2' or child_tag.name == 'h3':
            child_text = child_tag.text
            for line in child_text.split('\n'):
                line = line.rstrip().lstrip()
                for keyword in split_to_word(line):
                    add_to_index(index, keyword, url)


def union(to_crawl, new_url_links_list):
    """
    クローリングするURLに重複がないように
    するための関数
    """

    for new_url_link in new_url_links_list:
        if new_url_link not in to_crawl:
            to_crawl.append(new_url_link)


def extract_page_url_links(html):
    """
    クローリング先のページのaタグのhref属性を取得
    """
    soup = BeautifulSoup(html, 'html.parser')
    a_tags = soup.find_all('a')
    url_links_list = []
    for a_tag in a_tags:
        a_tag_href = a_tag.get('href')
        if a_tag_href:
            if a_tag_href.startswith('http'):
                url_links_list.append(a_tag_href)
            else:
                continue
    return url_links_list


def crawler(seed, max_depth):
    """
    クローラーのmain関数
    """
    to_crawl = [seed]
    crawled = []
    next_depth = []
    index = []
    depth = 0
    while to_crawl and depth <= max_depth:
        page = to_crawl.pop()
        if page not in crawled:
            content = get_page(page)
            if content:
                add_page_to_index(index, page, content)
                new_url_links = extract_page_url_links(content)
                new_url_links_list = []
                for new_url_link in new_url_links:
                    new_url_link = str(new_url_link)
                    new_url_links_list.append(new_url_link)
                union(to_crawl, new_url_links_list)
                crawled.append(page)
        if not to_crawl:
            to_crawl, next_depth = next_depth, []
            depth += 1
    return crawled