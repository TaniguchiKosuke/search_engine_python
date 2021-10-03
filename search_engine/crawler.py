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
    text = str(text).lower()
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
    if keyword:
        Index.objects.create(
            keyword = keyword,
            url =url
        )


def add_page_to_index(index, url, html):
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


def extract_page_url_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('a')


def crawler(seed, max_depth):    
    to_crawl = {seed}
    crawled = []
    next_depth = []
    index = []
    depth = 0
    while to_crawl and (depth <= max_depth):
        page = to_crawl.pop()
        if page not in crawled:
            content = get_page(page)
            add_page_to_index(index, page, content)
            # to_crawl.union(next_depth, extract_page_url_links(get_page(page)))
            new_url_links = extract_page_url_links(get_page(page))
            for new_url_link in new_url_links:
                if new_url_link not in to_crawl:
                    to_crawl.add(new_url_link)
            crawled.append(page)
        if not to_crawl:
            to_crawl, next_depth = next_depth, []
            depth = depth + 1
    print('to_crawl======================================')
    print(to_crawl)
    return crawled